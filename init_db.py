import sqlite3

DB_PATH = "data/review.db"

schema = """
DROP TABLE IF EXISTS review_queue;
CREATE TABLE review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Folder TEXT,
    File_Name TEXT,
    Path TEXT,
    Thumb_Path TEXT,
    DateTime TEXT,
    Camera TEXT,
    Lens_model TEXT,
    Width INTEGER,
    Height INTEGER,
    Exposure TEXT,
    Aperture TEXT,
    ISO INTEGER,
    Focal_length INTEGER,
    Keywords TEXT,
    Caption TEXT,
    Location TEXT,
    Subject TEXT,
    QR INTEGER,
    QC_Status TEXT
);
"""

def reset_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript(schema)
    conn.commit()
    conn.close()
    print("✅ review_queue table recreated successfully.")

if __name__ == "__main__":
    reset_table()
