import os
import cv2
import numpy as np
from PIL import Image
import pyiqa
from tqdm import tqdm
import sqlite3

# --- DB path and table should match your main workflow ---
DB_PATH = "data/review.db"
TABLE_NAME = "review_queue"

# --- Load the NIMA model (CPU for best compatibility) ---
model = pyiqa.create_metric('nima').cpu()

def calculate_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return lap_var

def calculate_brightness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

def calculate_contrast(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return np.std(gray)

def qc_status(qr):
    if qr is None:
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

# --- Get images from the review_queue table ---
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(f"SELECT id, Path, Folder, File_Name FROM {TABLE_NAME} WHERE QR IS NULL OR QC_Status IS NULL")
rows = c.fetchall()
print(f"Scoring {len(rows)} images pending quality...")

for row in tqdm(rows, desc="Scoring images"):
    img_id, img_path, folder, fname = row
    try:
        pil_img = Image.open(img_path).convert("RGB")
        nima_score = float(model(pil_img).item())
        cv_img = cv2.imread(img_path)
        blur = calculate_blur(cv_img)
        brightness = calculate_brightness(cv_img)
        contrast = calculate_contrast(cv_img)

        blur_score = min(blur / 200.0, 1.0) * 10
        brightness_score = max(0, min(1 - abs((brightness - 128) / 128), 1.0)) * 10
        contrast_score = min(contrast / 64.0, 1.0) * 10

        quality_score = (
            nima_score * 0.6 +
            blur_score * 0.2 +
            brightness_score * 0.1 +
            contrast_score * 0.1
        )
        quality_score = round(quality_score, 2)
        qc = qc_status(quality_score)

        # Update the DB with scores
        c.execute(f"""
            UPDATE {TABLE_NAME}
            SET nima_score=?, blur_score=?, brightness_score=?, contrast_score=?, QR=?, QC_Status=?
            WHERE id=?
        """, (
            round(nima_score, 2),
            round(blur_score, 2),
            round(brightness_score, 2),
            round(contrast_score, 2),
            quality_score,
            qc,
            img_id,
        ))
        conn.commit()
    except Exception as e:
        print(f"❌ Error processing {img_path}: {e}")

conn.close()
print("\n✅ All done! Scores written to your review queue.")
