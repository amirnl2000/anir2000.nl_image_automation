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

# Create the review_queue table with a dedicated Review_Status field
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
    QR INTEGER,
    QC_Status TEXT,
    Review_Status TEXT,
    Original_File_Name TEXT
)
""")

conn.commit()
conn.close()
"✅ Database initialized with review_queue including Review_Status and untouched QC_Status."
