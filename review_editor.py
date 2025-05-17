import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import os

DB_PATH =  "data/review.db"
TABLE = "review_queue"

class ReviewEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Review & Publish")
        self.conn = sqlite3.connect(DB_PATH)
        self.c = self.conn.cursor()
        self._load_rows()

        if not self.rows:
            messagebox.showinfo("Done", "✅ Nothing left to review.")
            self.conn.close()
            self.master.destroy()
            return

        self._build_ui()
        self._show()


    def _load_rows(self):
        # Only show rows not yet reviewed (Review_Status is NULL)
        self.c.execute(f"SELECT * FROM {TABLE} WHERE Review_Status = 'Pending'")
        cols = [d[0] for d in self.c.description]
        self.rows = [dict(zip(cols, r)) for r in self.c.fetchall()]
        self.idx = 0

    def _build_ui(self):
        self.frame = ttk.Frame(self.master)
        self.frame.pack(padx=10, pady=10)
        self.widgets = {}

        if not self.rows:
            messagebox.showinfo("Empty", "Nothing to review!")
            self.master.destroy()
            return

        for i, key in enumerate(self.rows[0].keys()):
            ttk.Label(self.frame, text=key).grid(row=i, column=0, sticky="w")
            if key in ("Keywords", "Caption"):
                widget = tk.Text(self.frame, height=4, width=60)
            else:
                widget = ttk.Entry(self.frame, width=60)
            widget.grid(row=i, column=1)
            self.widgets[key] = widget

        btns = ttk.Frame(self.master)
        btns.pack(pady=10)

        for txt, cmd in [("Approve", self._approve), ("Reject", self._reject),
                         ("Pending", self._pending), ("Publish", self._publish)]:
            ttk.Button(btns, text=txt, command=cmd).pack(side="left", padx=5)

    def _show(self):
        if self.idx >= len(self.rows):
            answer = messagebox.askyesno("Done", "✅ All reviewed. Upload to DB & FTP now?")
            if answer:
                subprocess.run(["python", "db_uploader.py"], check=False)
            self.master.destroy()

            return
        self.current = self.rows[self.idx]
        for k, widget in self.widgets.items():
            val = self.current[k] or ""
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                widget.insert("1.0", val)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, val)

    def _save_status(self, status):
        rid = self.current["id"]
        self.c.execute(f"UPDATE {TABLE} SET Review_Status=? WHERE id=?", (status, rid))
        self.conn.commit()
        self.idx += 1
        self._show()

    def _approve(self): self._save_status("Approved")
    def _reject(self):  self._save_status("Rejected")
    def _pending(self): self._save_status("Pending")

    def _publish(self):
        subprocess.run(["python", "db_uploader.py"], shell=True)
        messagebox.showinfo("Publish", "✅ Uploaded approved rows to DB/FTP.")
        self.conn.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    ReviewEditor(root)
    root.mainloop()
