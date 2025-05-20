import os
import sys
import sqlite3
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading

from utils.file_namer import get_exif_data, get_camera_model, get_exif_year, generate_unique_filename
from utils.metadata_builder import build_metadata

DB_PATH = "data/review.db"
TABLE_NAME = "review_queue"
INCOMING_DIR = r"C:\Users\YOUR_USERNAME\incoming"
LOCATION_FILE = os.path.join("data", "location_list.json")
FOLDER_MAP_FILE = os.path.join("data", "folder_map.json")

class ImageAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Amir2000 Image Automation")
        self.images = []
        self.subject_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.build_ui()

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Subject:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.subject_var, width=50).grid(row=0, column=1, sticky="ew")
        ttk.Label(frm, text="Location:").grid(row=1, column=0, sticky="w")
        locs = self.load_json(LOCATION_FILE)
        locs.sort()
        self.loc_combo = ttk.Combobox(frm, values=locs, textvariable=self.location_var, width=48)
        self.loc_combo.grid(row=1, column=1, sticky="ew")
        self.loc_combo.bind("<FocusOut>", lambda e: self.save_new(self.location_var.get(), LOCATION_FILE))
        ttk.Label(frm, text="Folder (category):").grid(row=2, column=0, sticky="w")
        fmap = self.load_json(FOLDER_MAP_FILE)
        self.folder_key_lookup = {v: k for k, v in fmap.items()}
        folder_names = sorted(fmap.values())
        self.folder_combo = ttk.Combobox(frm, values=folder_names, textvariable=self.folder_var, width=48)
        self.folder_combo.grid(row=2, column=1, sticky="ew")
        ttk.Button(frm, text="Select Images", command=self.select_images).grid(row=3, column=0, columnspan=2, pady=5)
        self.file_list = tk.Listbox(frm, width=80, height=8)
        self.file_list.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(frm, text="Start Batch", command=lambda: threading.Thread(target=self.proceed).start()).grid(row=5, column=0, columnspan=2, pady=10)
        frm.columnconfigure(1, weight=1)

    def load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_new(self, val, path):
        val = val.strip()
        if not val: return
        arr = self.load_json(path)
        if val not in arr:
            arr.append(val)
            arr.sort()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(arr, f, indent=2)

    def select_images(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("JPEG files", "*.jpg *.jpeg"), ("All files", "*.*")]
        )
        if files:
            self.images = list(files)
            self.file_list.delete(0, tk.END)
            for f in self.images:
                self.file_list.insert(tk.END, os.path.basename(f))

    def proceed(self):
        print("\n[STAGE 1] Input validation and collecting files...")
        subj = self.subject_var.get().strip()
        loc = self.location_var.get().strip()
        fld_readable = self.folder_var.get().strip()
        fld = self.folder_key_lookup.get(fld_readable, fld_readable)

        if not (subj and loc and fld):
            messagebox.showwarning("Missing fields", "Fill in Subject, Location, and Folder.")
            print("[ERROR] Missing required fields.")
            return
        if not self.images:
            messagebox.showwarning("No images", "No images selected.")
            print("[ERROR] No images selected.")
            return

        print("[STAGE 2] Preparing database and moving images to incoming folder...")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'")
        exists = c.fetchone()
        if not exists:
            c.execute(f"""CREATE TABLE {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Folder TEXT, File_Name TEXT, Path TEXT, Thumb_Path TEXT,
                DateTime TEXT, Camera TEXT, Lens_model TEXT, Width INTEGER,
                Height INTEGER, Exposure TEXT, Aperture TEXT, ISO INTEGER,
                Focal_length INTEGER, Keywords TEXT, Caption TEXT, Location TEXT,
                Subject TEXT, QR INTEGER, QC_Status TEXT, Review_Status TEXT,
                Original_File_Name TEXT
            )""")
            conn.commit()

        os.makedirs(INCOMING_DIR, exist_ok=True)
        for src in self.images:
            original_name = os.path.basename(src)
            incoming_path = os.path.join(INCOMING_DIR, original_name)
            if not os.path.exists(incoming_path):
                shutil.move(src, incoming_path)

            exif = get_exif_data(incoming_path)
            cam = get_camera_model(exif)
            year = get_exif_year(exif)
            suggested_name = generate_unique_filename(subj, loc, fld, cam, year)
            meta = build_metadata(incoming_path, "", suggested_name, fld, year, loc, subj)
            meta["Review_Status"] = "Pending"
            meta["Original_File_Name"] = original_name
            meta["Path"] = incoming_path
            meta["Thumb_Path"] = ""

            fields = ",".join(meta.keys())
            placeholders = ",".join(["?"] * len(meta))
            sql = f"INSERT INTO {TABLE_NAME} ({fields}) VALUES ({placeholders})"
            c.execute(sql, tuple(meta.values()))

        conn.commit()
        conn.close()
        print(f"[STAGE 3] Inserted {len(self.images)} images to DB. Moving to scoring...")

        messagebox.showinfo("Batch Ready", f"✅ {len(self.images)} images ready for scoring & review.")

        # Score images using external script
        print("[STAGE 4] Starting image scoring (this can take a moment)...")
        subprocess.run([sys.executable, "batch_image_quality_score.py"], check=True)
        print("[STAGE 5] Scoring done. Launching review/approval interface...")

        subprocess.run([sys.executable, "review_editor.py"], check=False)
        print("[STAGE 6] Review/editor closed. Exiting main UI.")
        self.root.destroy()

if __name__ == '__main__':
    print("\n========= Amir2000 Image Automation: MAIN START =========")
    root = tk.Tk()
    app = ImageAutomationApp(root)
    root.mainloop()
    print("========= Amir2000 Image Automation: MAIN END =========")
