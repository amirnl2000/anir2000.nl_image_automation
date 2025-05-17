# amir2000.nl | Image Automation Pipeline

This project powers the complete automation pipeline for managing high-quality images on [amir2000.nl](https://www.amir2000.nl). It enables a streamlined process from local image import and metadata generation to FTP uploads and remote MySQL insertion. The workflow is optimized for professional photography publication and scalability.

---

## 📸 Key Features

- **Manual image selection** via UI with Subject, Location, and Folder categorization
- **Automatic EXIF extraction** and smart renaming based on metadata
- **Smart filename generation** with collision checks using `used_filenames.json`
- **Web-optimized image resizing** (1500px) + thumbnail (548x365px)
- **Watermarking** with custom font and layout
- **Metadata enrichment** (EXIF + random caption/keywords based on folder)
- **Review UI** for manual curation + correction
- **Automatic DB + FTP upload** upon approval
- **Dual database management**: local (SQLite) + remote (MySQL)
- **Logging and error tracking** for DB/FTP failures

---

## 📂 Folder Structure

```
├── main.py                  # Main entry: UI for processing selected images
├── review_editor.py         # Manual review interface for metadata edits
├── db_uploader.py           # Final step: uploads to MySQL & FTP
├── clear_review.py          # Utility to reset review.db
├── data/
│   ├── review.db            # SQLite metadata store
│   ├── used_filenames.json  # Tracks used filenames to avoid collisions
│   ├── caption_templates.json # Captions + keywords per folder
│   ├── folder_map.json      # Folder key to display name mapping
│   └── location_list.json   # All used Locations for dropdowns
├── utils/
│   ├── metadata_builder.py  # Build metadata (EXIF, caption, keywords)
│   ├── file_namer.py        # Handle EXIF read, filename generation
│   └── image_processor.py   # Resize, watermark, thumbnail creation
├── fonts/
│   └── Montserrat-Light.ttf # Watermark font
└── README.md                # You're reading this
```

---

## 🧠 Process Flow

### Step 1: Image Selection
- UI in `main.py` allows user to select files and define Subject, Location, Folder.
- The dropdowns for Location and Folder auto-update using `location_list.json` and `folder_map.json`.

### Step 2: Rename & Process
- Files are **moved** to the local archive: `path here/{year}/{folder}`
- Each file is renamed using a unique, SEO-friendly format:  
  `Subject_Location_Folder_Camera_Year_###.JPG`
- Resized, watermarked, and thumbnails are generated for:
  - Live site: `path here/...`
  - Review copy: `path here/...`
- EXIF + AI-enhanced metadata (caption/keywords) is created
- Final records are stored in SQLite `review.db`

### Step 3: Review & Approve
- Launches `review_editor.py` to:
  - Edit metadata (caption, keywords, etc.)
  - Approve, reject, or leave Pending
  - Rejected files are moved to: `path here/rejected/`
  - Approved ones trigger next step: auto-launch `db_uploader.py`

### Step 4: Upload to Web
- `db_uploader.py`:
  - Verifies **no duplicate filename** exists in remote MySQL
  - Inserts data into `photos_info_revamp1` (or live `photos_info_revamp`)
  - Uploads web + thumb images via FTP to `path here/...`
  - Marks local `review.db` row as `Uploaded`

---

## 💾 Data Fields (SQLite + MySQL)
- `Folder`
- `File_Name`
- `Original_File_Name`
- `Path`
- `Thumb_Path`
- `DateTime`
- `Camera`
- `Lens_model`
- `Width`, `Height`
- `Exposure`, `Aperture`, `ISO`, `Focal_length`
- `Keywords`, `Caption`, `Location`, `Subject`
- `QR` (nullable)
- `QC_Status` ('NA' by default)
- `Review_Status` ('Pending', 'Approved', 'Rejected', 'Uploaded')

---

## 🔮 Future Enhancements

- Integrate image quality model (NIMA, CLIP) to auto-suggest `QR` (quality rating)
- Train LLM/embedding model for dynamic caption & keyword generation
- Admin page for dashboard statistics & AI fine-tuning
- Slack or Email webhook alerts for upload success/failure

---

## 📸 Credits
Developed by [Amir Darzi](https://www.amir2000.nl/about.php) to automate high-quality image publishing, speed up website updates, and prepare for AI-driven photo metadata generation.

---

📁 Live Website: [amir2000.nl](https://www.amir2000.nl)  
🛠️ Latest Working UI: See `/screenshots/` for sample images

---

Feel free to fork, adapt, or extend for your own creative workflow!

MIT License.