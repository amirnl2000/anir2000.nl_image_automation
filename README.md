# amir2000_image_automation

A modular, GUI-driven workflow for reviewing, scoring, and uploading photography, with local + MySQL/FTP sync.

---

## Features

- Batch ingestion of images via GUI (Tkinter)
- Smart filename generator based on subject/location/camera/year
- EXIF extraction and automatic metadata builder
- ML-based image quality scoring (NIMA, sharpness, etc.)
- Review/editor interface for manual override and approval
- Automatic sync to MySQL database & FTP upload to web host
- Local-first workflow, cross-platform compatible (Windows tested)
- One-click batch launch: double-click a single `.bat` file

---

## Workflow Overview

1. **Prepare new images** in the `incoming/` folder.
2. **Launch the GUI** with `run_upload.bat` (recommended) or `python main.py`.
3. **Select images, enter subject/location/folder** (category).
4. **System auto-extracts EXIF, builds filenames, moves files to processing folder.**
5. **ML scoring** (NIMA/technical quality) is run on images.
6. **Manual review/editor UI:** approve/reject/edit captions/keywords if needed.
7. **On approval:** upload metadata to MySQL and images to FTP.
8. **Session completes:** terminal returns to ready-to-run.

---

## Project Structure

```

amir2000\_image\_automation/
│
├── main.py                    # Entry point for GUI and ingestion pipeline
├── batch\_image\_quality\_score.py # ML scoring (NIMA, sharpness, etc.)
├── review\_editor.py           # Manual approval/override interface
├── db\_uploader.py             # Syncs reviewed images to MySQL/FTP
├── utils/                     # Helper modules: EXIF, renaming, metadata, etc.
├── data/                      # SQLite DB, JSON location/folder mappings
├── run\_upload.bat             # Preferred way to launch the pipeline
└── README.md                  # (This file)

````

---

## First-Time Setup

1. **Clone this repo and extract it to your preferred folder.**

2. **Set up Anaconda environment** (one-time):

    ```sh
    conda create -n imgquality python=3.11
    conda activate imgquality
    pip install pyiqa Pillow ftplib mysql-connector-python tqdm
    ```

    _Install any other required libraries if prompted._

3. **Edit config variables** in `db_uploader.py` and other config files for your local paths and credentials.  
   **DO NOT upload your real credentials or private info to GitHub!**

4. **Edit `run_upload.bat`** with your local username and full paths if needed.

5. **Launch with `run_upload.bat`** — no need to manually activate environments each time.

---

## Example `run_upload.bat`

```bat
@echo off
echo ==== Activating imgquality environment ====
call "C:\ProgramData\anaconda3\Scripts\activate.bat" imgquality

echo ==== Changing to image automation project directory ====
cd /d "C:\Users\YOUR_USERNAME\amir2000_image_automation"

echo ==== Running Main Pipeline ====
python main.py

echo.
echo ==== Process finished. Press any key to close. ====
pause >nul
````

**Change the paths to match your system!**

---

## Notes

* **Windows/Anaconda/Python 3.11+ required**
* All local/external paths, database and FTP credentials are in `db_uploader.py` — **Edit these before using!**
* For security, never commit credentials or personal paths to public repos.
* If you have issues with environment activation, try running via Anaconda Prompt or adjust `run_upload.bat`.

---

## Credits

Project by Amir Darzi ([amir2000.nl](https://www.amir2000.nl)), modularized for full-automation photo workflows.

---

## License

MIT License (or specify your own)


