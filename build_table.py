import sqlite3
import os

# Define the database path
db_path = "data/review.db"

# Remove existing DB if it exists
if os.path.exists(db_path):
    os.remove(db_path)

# Connect and create schema
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create the review_queue table with all needed scoring/review fields
c.execute("""
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
    nima_score REAL,
    blur_score REAL,
    brightness_score REAL,
    contrast_score REAL,
    QR REAL,
    QC_Status TEXT,
    Review_Status TEXT,
    Original_File_Name TEXT
)
""")

conn.commit()
conn.close()
print("✅ Database initialized with review_queue (incl. all scoring/quality fields, Review_Status, QC_Status).")
