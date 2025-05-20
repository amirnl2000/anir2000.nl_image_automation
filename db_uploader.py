import os
import sqlite3
import mysql.connector
from ftplib import FTP
from datetime import datetime
import json

# Config
DB_PATH = "data/review.db"
LOCAL_MIRROR_DB = "data/photos_info.db"
TABLE_NAME = "photos_info"
REVIEW_QUEUE = "review_queue"
REMOTE_BASE = "public_html/images/"
LOCAL_BASE = r"C:\Users\YOUR_USERNAME\Pictures\Photos"
# Adjust the path to your local base directory
LOG_FILE = r"C:\Users\YOUR_USERNAME\Desktop\logs\upload_errors.log"

MYSQL = {
    "host": "your_mysql_host",
    "user": "your_mysql_user",
    "password": "your_mysql_password",
    "database": "your_mysql_database",
}

FTP_CONFIG = {
    "host": "ftp.your_ftp_host",
    # Example: "ftp.example.com"    
    "port": 21,
    "user": "your_ftp_user",
    "passwd": "your_ftp_password"
}

with open("data/folder_map.json", encoding="utf-8") as f:
    folder_map = json.load(f)

def mkdir_p(ftp, remote_dir):
    ftp.cwd("/")
    for part in remote_dir.strip("/").split("/"):
        if not part:
            continue
        try:
            ftp.cwd(part)
        except:
            ftp.mkd(part)
            ftp.cwd(part)

def upload():
    conn_local = sqlite3.connect(DB_PATH)
    c = conn_local.cursor()
    c.execute(f"SELECT * FROM {REVIEW_QUEUE} WHERE Review_Status='Approved'")
    rows = c.fetchall()
    cols = [d[0] for d in c.description]

    if not rows:
        print("Nothing approved for upload.")
        return

    # Connect to MySQL, FTP, and local mirror DB
    conn_remote = mysql.connector.connect(**MYSQL)
    cursor = conn_remote.cursor()
    ftp = FTP()
    ftp.connect(FTP_CONFIG["host"], FTP_CONFIG["port"])
    ftp.login(FTP_CONFIG["user"], FTP_CONFIG["passwd"])

    mirror_conn = sqlite3.connect(LOCAL_MIRROR_DB)
    mirror_cur = mirror_conn.cursor()
    mirror_cur.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Folder TEXT, File_Name TEXT, Path TEXT, Thumb_Path TEXT, DateTime TEXT, Camera TEXT, Lens_model TEXT,
        Width INTEGER, Height INTEGER, Exposure TEXT, Aperture TEXT, ISO INTEGER, Focal_length INTEGER,
        Keywords TEXT, Caption TEXT, Location TEXT, QR REAL, QC_Status TEXT, Original_File_Name TEXT
    )""")
    mirror_conn.commit()

    success, fail = 0, 0

    for row in rows:
        record = dict(zip(cols, row))
        year = str(record["DateTime"])[:4]
        file_name = record["File_Name"]
        # For folder_key, prefer original key if in folder_map, else fall back to value.
        folder_key = next((k for k, v in folder_map.items() if v == record["Folder"]), record["Folder"])

        local_img = os.path.join(LOCAL_BASE, year, folder_key, file_name)
        local_thumb = os.path.join(LOCAL_BASE, year, "thumbs", folder_key, file_name)

        remote_img_dir = f"{REMOTE_BASE}/{year}/{folder_key}"
        remote_thumb_dir = f"{REMOTE_BASE}/{year}/thumbs/{folder_key}"

        try:
            # --- MySQL Upload ---
            sql = f"""INSERT INTO {TABLE_NAME} (
                Folder, File_Name, Path, Thumb_Path, DateTime, Camera, Lens_model,
                Width, Height, Exposure, Aperture, ISO, Focal_length,
                Keywords, Caption, Location, QR, QC_Status, Original_File_Name
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )"""
            data = [
                record["Folder"],
                record["File_Name"],
                record["Path"],
                record["Thumb_Path"],
                record["DateTime"],
                record["Camera"],
                record["Lens_model"],
                int(record["Width"]),
                int(record["Height"]),
                record["Exposure"],
                record["Aperture"],
                int(record["ISO"]),
                int(record["Focal_length"]),
                record["Keywords"],
                record["Caption"],
                record["Location"],
                record["QR"],
                record["QC_Status"],
                record.get("Original_File_Name", ""),
            ]
            cursor.execute(sql, tuple(data))

            # --- FTP Upload ---
            mkdir_p(ftp, remote_img_dir)
            with open(local_img, "rb") as f:
                ftp.storbinary(f"STOR " + file_name, f)
            mkdir_p(ftp, remote_thumb_dir)
            with open(local_thumb, "rb") as f:
                ftp.storbinary(f"STOR " + file_name, f)

            # --- Local Mirror Insert ---
            mirror_sql = f"""INSERT OR REPLACE INTO {TABLE_NAME} (
                Folder, File_Name, Path, Thumb_Path, DateTime, Camera, Lens_model,
                Width, Height, Exposure, Aperture, ISO, Focal_length,
                Keywords, Caption, Location, QR, QC_Status, Original_File_Name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            mirror_data = [
                record["Folder"],
                record["File_Name"],
                record["Path"],
                record["Thumb_Path"],
                record["DateTime"],
                record["Camera"],
                record["Lens_model"],
                int(record["Width"]),
                int(record["Height"]),
                record["Exposure"],
                record["Aperture"],
                int(record["ISO"]),
                int(record["Focal_length"]),
                record["Keywords"],
                record["Caption"],
                record["Location"],
                record["QR"],
                record["QC_Status"],
                record.get("Original_File_Name", ""),
            ]
            mirror_cur.execute(mirror_sql, tuple(mirror_data))
            mirror_conn.commit()

            # --- Mark as uploaded locally ---
            c.execute(f"UPDATE {REVIEW_QUEUE} SET Review_Status = 'Uploaded' WHERE id = ?", (record["id"],))
            conn_local.commit()
            success += 1

        except Exception as e:
            msg = f"❌ Failed: {file_name} → {e}"
            print(msg)
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(msg + "\n")
            fail += 1

    # Finalize and close connections
    try:
        conn_remote.commit()
    except Exception:
        pass
    cursor.close()
    conn_remote.close()
    conn_local.close()
    mirror_conn.close()
    ftp.quit()

    print(f"✅ Done. Uploaded {success}, Failed {fail}")
    if fail:
        print(f"Check: {LOG_FILE}")

if __name__ == "__main__":
    upload()
