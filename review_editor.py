import os
import sys
import shutil
import sqlite3
import subprocess
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox, Frame, Text, END, DISABLED
from PIL import Image, ImageTk

# --- CONFIGURATION ---
DB_PATH = 'data/review.db'
TABLE_NAME = 'review_queue'
INCOMING_DIR = r"C:\Users\YOUR_USERNAME\incoming"
REJECTED_FOLDER = r'C:\Users\YOUR_USERNAME\Desktop\rejected'
LOCAL_BASE = r"C:\Users\YOUR_USERNAME\images"
DESKTOP_ROOT = r"C:\Users\YOUR_USERNAME\Desktop\photos"
ARCHIVE_ROOT = r"C:\Users\YOUR_USERNAME\Pictures"
FONT_PATH = "fonts/Montserrat-Light.ttf"
WATERMARK_TEXT = "your_watermark_here"
# --- END CONFIGURATION --- 

from utils.image_processor import resize_and_watermark
from utils.file_namer import generate_unique_filename

QR_EXPLANATION = (
    "QR (Quality Rating) Guide:\n"
    "  • Top (≥7.3): Outstanding. Publish or license with confidence.\n"
    "  • Good (6.5–7.3): Strong image for web/stock/blog.\n"
    "  • Average (5.5–6.5): Acceptable, but may need improvement (sharpness, exposure, composition).\n"
    "  • Low (<5.5): Major issues (blur, noise, exposure, poor subject). Consider removing or retouching.\n"
    "\nTips: High QR = sharp, well-exposed, visually appealing, strong subject/focus. Use 'Blur', 'Brightness', 'Contrast' fields for more details."
)

def qc_status(qr):
    if qr is None or qr == "":
        return "NA"
    try:
        qr = float(qr)
    except:
        return "NA"
    if qr >= 7.3:
        return "Top"
    elif qr >= 6.5:
        return "Good"
    elif qr >= 5.5:
        return "Average"
    else:
        return "Low"

class ReviewApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Amir2000 Image Review & Publish")
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        self.images = self.get_images_to_review()
        self.idx = 0
        self.field_vars = {}
        self.text_widgets = {}
        self.build_layout()
        if self.images:
            self.load_image()
        else:
            messagebox.showinfo("No Images", "No images found to review.")
            self.master.quit()

    def build_layout(self):
        self.left_frame = Frame(self.master)
        self.left_frame.grid(row=0, column=0, padx=8, pady=8, sticky="n")
        self.right_frame = Frame(self.master)
        self.right_frame.grid(row=0, column=1, padx=8, pady=8, sticky="n")

        self.image_label = Label(self.left_frame)
        self.image_label.pack()

        self.qr_info = Text(self.left_frame, height=9, width=44, wrap='word', fg='#144', font=('Arial', 9))
        self.qr_info.insert(END, QR_EXPLANATION)
        self.qr_info.config(state=DISABLED)
        self.qr_info.pack(pady=(10, 0))

        labels = [
            'id', 'Folder', 'File_Name', 'Path', 'Thumb_Path', 'DateTime',
            'Camera', 'Lens_model', 'Width', 'Height', 'Exposure', 'Aperture',
            'ISO', 'Focal_length', 'Keywords', 'Caption', 'Location',
            'Subject', 'nima_score', 'blur_score', 'brightness_score', 'contrast_score',
            'QR', 'QC_Status', 'Review_Status', 'Original_File_Name'
        ]
        for i, label in enumerate(labels):
            Label(self.right_frame, text=label).grid(row=i, column=0, sticky='e')
            if label in ['Keywords', 'Caption']:
                txt = Text(self.right_frame, height=3, width=60, wrap='word')
                txt.grid(row=i, column=1, sticky='w')
                self.text_widgets[label] = txt
            else:
                var = StringVar()
                entry = Entry(self.right_frame, textvariable=var, width=60)
                entry.grid(row=i, column=1, sticky='w')
                self.field_vars[label] = var
                if label in ['id', 'Path', 'Thumb_Path', 'Original_File_Name']:
                    entry.config(state='readonly')

        Button(self.right_frame, text="Back", command=self.back).grid(row=99, column=0)
        Button(self.right_frame, text="Approve", command=self.approve).grid(row=99, column=1)
        Button(self.right_frame, text="Reject", command=self.reject).grid(row=99, column=2)
        Button(self.right_frame, text="Pending", command=self.pending).grid(row=99, column=3)
        Button(self.right_frame, text="Publish", command=self.publish).grid(row=99, column=4)

    def get_images_to_review(self):
        self.cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE Review_Status IS NULL OR Review_Status != 'Uploaded' ORDER BY id")
        rows = self.cur.fetchall()
        colnames = [x[0] for x in self.cur.description]
        return [dict(zip(colnames, row)) for row in rows]

    def load_image(self):
        img_info = self.images[self.idx]
        for k, v in img_info.items():
            if k in self.field_vars:
                self.field_vars[k].set(str(v) if v is not None else "")
            if k in self.text_widgets:
                self.text_widgets[k].delete(1.0, END)
                if v:
                    self.text_widgets[k].insert(END, str(v))
        # Show image (local or url)
        orig_path = img_info.get("Path")
        try:
            im = Image.open(orig_path)
            im.thumbnail((600, 600))
            img = ImageTk.PhotoImage(im)
            self.image_label.config(image=img)
            self.image_label.image = img
            self.image_label.config(text="")
        except Exception:
            self.image_label.config(text="Image not found", image=None)
        try:
            qr_val = float(self.field_vars['QR'].get()) if self.field_vars['QR'].get() else None
        except:
            qr_val = None
        qc = qc_status(qr_val)
        self.field_vars['QC_Status'].set(qc)

    def get_field_values(self):
        values = {k: v.get() for k, v in self.field_vars.items()}
        for k, txt in self.text_widgets.items():
            values[k] = txt.get("1.0", END).strip()
        return values

    def save_current(self, status):
        img_info = self.images[self.idx]
        values = self.get_field_values()
        values['QC_Status'] = qc_status(values.get('QR'))
        set_clause = ", ".join([f"{k} = ?" for k in values if k != 'id'])
        sql = f"UPDATE {TABLE_NAME} SET {set_clause}, Review_Status=? WHERE id=?"
        args = [values[k] for k in values if k != 'id'] + [status, img_info['id']]
        self.cur.execute(sql, args)
        self.conn.commit()

    def approve(self):
        img_info = self.images[self.idx]
        values = self.get_field_values()
        folder = values['Folder']
        suggested_name = values['File_Name']
        year = img_info['DateTime'][:4] if img_info.get('DateTime') else "unknown"
        orig_path = img_info['Path']

        web_dir = os.path.join(LOCAL_BASE, year, folder)
        thumb_dir = os.path.join(LOCAL_BASE, year, "thumbs", folder)
        desk_dir = os.path.join(DESKTOP_ROOT, folder)
        archive_dir = os.path.join(ARCHIVE_ROOT, year, folder)
        for d in (web_dir, thumb_dir, desk_dir, archive_dir):
            os.makedirs(d, exist_ok=True)
        web_path = os.path.join(web_dir, suggested_name)
        thumb_path = os.path.join(thumb_dir, suggested_name)
        desk_path = os.path.join(desk_dir, suggested_name)
        archive_path = os.path.join(archive_dir, suggested_name)

        # Copy original to archive before any modification!
        shutil.copy2(orig_path, archive_path)

        # Move working file to web_dir (for resizing and publishing)
        shutil.move(orig_path, web_path)

        # Resize/watermark/copy to all targets
        resize_and_watermark(
            web_path, web_path, thumb_path, desk_path,
            WATERMARK_TEXT,
            FONT_PATH
        )

        # *** UPDATE width and height after resizing ***
        try:
            im = Image.open(web_path)
            width, height = im.size
            self.field_vars['Width'].set(str(width))
            self.field_vars['Height'].set(str(height))
        except Exception as e:
            print(f"Error reading new width/height: {e}")

        # Save public URLs to local DB
        web_url = f"https://your_domain.com/images/{year}/{folder}/{suggested_name}"
        thumb_url = f"https://your_domain.com/images/{year}/thumbs/{folder}/{suggested_name}"
        self.field_vars['Path'].set(web_url)
        self.field_vars['Thumb_Path'].set(thumb_url)
        self.save_current('Approved')
        self.next_image()

    def reject(self):
        img_info = self.images[self.idx]
        orig_path = img_info.get("Path")
        if orig_path and os.path.exists(orig_path):
            shutil.move(orig_path, os.path.join(REJECTED_FOLDER, os.path.basename(orig_path)))
        self.cur.execute(f"DELETE FROM {TABLE_NAME} WHERE id=?", (img_info['id'],))
        self.conn.commit()
        self.next_image()

    def pending(self):
        self.save_current('Pending')
        self.next_image()

    def publish(self):
        self.save_current('Published')
        messagebox.showinfo("Publish", "Marked as Published. You can upload to MySQL & FTP now.")
        self.next_image()

    def next_image(self):
        self.idx += 1
        if self.idx < len(self.images):
            self.load_image()
        else:
            answer = messagebox.askyesno(
                "Done!", "All images reviewed and renamed! Would you like to upload now?"
            )
            if answer:
                

                result = subprocess.run(
                    [sys.executable, "db_uploader.py"],
                    capture_output=True, text=True
                )

                messagebox.showinfo("Upload Complete", result.stdout)
                # Clean review_queue from uploaded rows for tidiness:
                self.cur.execute(f"DELETE FROM {TABLE_NAME} WHERE Review_Status='Uploaded'")
                self.conn.commit()
                messagebox.showinfo("Done", "All images uploaded and queue cleaned!")
            else:
                messagebox.showinfo("Done", "You may close this window now.")
            self.master.destroy()
            self.master.quit()  # Sometimes helps on Windows
            sys.exit(0)



    def back(self):
        if self.idx > 0:
            self.idx -= 1
            self.load_image()
        else:
            messagebox.showinfo("Back", "This is the first image.")


def next_image(self):
    # ... your review logic ...
    self.master.quit()
    self.master.destroy()
    print("Exited cleanly!")
    os._exit(0)  # <- This will force exit, guaranteed to return to prompt.

if __name__ == "__main__":
    root = Tk()
    app = ReviewApp(root)
    root.mainloop()
    # (The below code will not normally be reached, but just in case)
    print("Exited cleanly!")
    os._exit(0)



