import os
import sqlite3
import mysql.connector
from ftplib import FTP
from datetime import datetime
import json

# Config

# Load sensitive configs from external files
with open('config/db_config.json') as f:
    MYSQL = json.load(f)
with open('config/ftp_config.json') as f:
    FTP_CONFIG = json.load(f)

DB_PATH = "data/review.db"
TABLE_NAME = "table name"
REMOTE_BASE = "path here"
LOCAL_BASE = r"path here"
LOG_FILE = r"path here\upload_errors.log"

with open("data/folder_map.json", encoding="utf-8") as f:
    folder_map = json.load(f)

def format_datetime(raw):
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except:
        return None

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
    c.execute("SELECT * FROM review_queue WHERE Review_Status='Approved'")
    rows = c.fetchall()
    cols = [d[0] for d in c.description]

    if not rows:
        print("Nothing approved for upload.")
        return

    conn_remote = mysql.connector.connect(**MYSQL)
    cursor = conn_remote.cursor()

    ftp = FTP()
    ftp.connect(FTP_CONFIG["host"], FTP_CONFIG["port"])
    ftp.login(FTP_CONFIG["user"], FTP_CONFIG["passwd"])

    success, fail = 0, 0

    for row in rows:
        record = dict(zip(cols, row))
        year = record["DateTime"][:4]
        file_name = record["File_Name"]

        folder_key = next((k for k, v in folder_map.items() if v == record["Folder"]), record["Folder"])

        local_img = os.path.join(LOCAL_BASE, year, folder_key, file_name)
        local_thumb = os.path.join(LOCAL_BASE, year, "thumbs", folder_key, file_name)

        remote_img_dir = f"{REMOTE_BASE}/{year}/{folder_key}"
        remote_thumb_dir = f"{REMOTE_BASE}/{year}/thumbs/{folder_key}"

        try:
            has_original = "Original_File_Name" in record

            sql = f"""INSERT INTO {TABLE_NAME} (
                id, Folder, File_Name, Path, Thumb_Path, DateTime, Camera, Lens_model,
                Width, Height, Exposure, Aperture, ISO, Focal_length,
                Keywords, Caption, Location, QR, QC_Status
                {', Original_File_Name' if has_original else ''}
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
                {', %s' if has_original else ''}
            )"""

            data = [
                "*",
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
                record["QC_Status"]
            ]

            if has_original:
                data.append(record["Original_File_Name"])

            cursor.execute(sql, tuple(data))

            mkdir_p(ftp, remote_img_dir)
            with open(local_img, "rb") as f:
                ftp.storbinary(f"STOR " + file_name, f)

            mkdir_p(ftp, remote_thumb_dir)
            with open(local_thumb, "rb") as f:
                ftp.storbinary(f"STOR " + file_name, f)

            c.execute("UPDATE review_queue SET Review_Status = 'Uploaded' WHERE id = ?", (record["id"],))
            conn_local.commit()
            success += 1

        except Exception as e:
            msg = f"❌ Failed: {file_name} → {e}"
            print(msg)
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(msg + "\n")
            fail += 1

    cursor.close()
    conn_remote.commit()
    conn_remote.close()
    conn_local.close()
    ftp.quit()

    print(f"✅ Done. Uploaded {success}, Failed {fail}")
    if fail:
        print(f"Check: {LOG_FILE}")

if __name__ == "__main__":
    upload()
