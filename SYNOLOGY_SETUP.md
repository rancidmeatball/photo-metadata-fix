# Synology Setup Guide

## Quick Start

The script is pre-configured to run on `/volume1/photo` recursively.

### Basic Usage

```bash
# SSH into your Synology
ssh admin@your-synology-ip

# Navigate to where you uploaded the script
cd /volume1/scripts  # or wherever you put it

# Make executable (if not already)
chmod +x synology_rename_photos.py

# DRY RUN (preview changes, safe)
./synology_rename_photos.py --dry-run

# Actually rename files
./synology_rename_photos.py

# Or auto-confirm
./synology_rename_photos.py --yes
```

---

## Installation Steps

### 1. Install Dependencies on Synology

SSH into your Synology and run:

```bash
# Install pip if not already installed
sudo python3 -m ensurepip

# Install required packages
sudo python3 -m pip install Pillow exifread

# Optional: Install exiftool for better video support
# (May require enabling Community packages)
```

### 2. Upload the Script

Option A: Using SCP from your Mac:
```bash
scp synology_rename_photos.py admin@your-synology:/volume1/scripts/
```

Option B: Using Synology File Station:
1. Open File Station
2. Navigate to a shared folder (e.g., create `/scripts`)
3. Upload `synology_rename_photos.py`
4. SSH in and make executable: `chmod +x /volume1/scripts/synology_rename_photos.py`

### 3. Run the Script

```bash
# SSH into Synology
ssh admin@your-synology-ip

# Navigate to script location
cd /volume1/scripts

# Preview what will happen (ALWAYS DO THIS FIRST)
./synology_rename_photos.py --dry-run

# Review the output, then run for real
./synology_rename_photos.py
```

---

## Command Options

### Default Behavior
```bash
./synology_rename_photos.py
```
- Processes `/volume1/photo` (default)
- Recursive (processes all subdirectories)
- Asks for confirmation

### Dry Run (Safe Preview)
```bash
./synology_rename_photos.py --dry-run
```
Shows what would happen without making changes

### Auto-Confirm (No Prompt)
```bash
./synology_rename_photos.py --yes
```
Useful for scheduled tasks

### Quiet Mode (Minimal Output)
```bash
./synology_rename_photos.py --yes --quiet
```
Only shows summary, good for cron jobs

### Different Directory
```bash
./synology_rename_photos.py /volume1/photo/2016
```
Process a specific subdirectory

### Non-Recursive
```bash
./synology_rename_photos.py --no-recursive
```
Only process files in the specified directory (not subdirectories)

### Combined Examples
```bash
# Dry run on specific folder
./synology_rename_photos.py /volume1/photo/2016 --dry-run

# Process entire photo library quietly
./synology_rename_photos.py --yes --quiet

# Process specific folder without subdirectories
./synology_rename_photos.py /volume1/photo/2016 --no-recursive --yes
```

---

## Scheduling with Task Scheduler

You can set up the script to run automatically using Synology Task Scheduler:

1. Open **Control Panel** → **Task Scheduler**
2. Create → **Scheduled Task** → **User-defined script**
3. General tab:
   - Task: "Rename photos by date"
   - User: root (or admin)
   - Enabled: ✓
4. Schedule tab:
   - Run on the following days: (choose your schedule)
   - Time: (choose a time, e.g., 2:00 AM)
5. Task Settings tab:
   - User-defined script:
   ```bash
   /volume1/scripts/synology_rename_photos.py --yes --quiet >> /volume1/logs/photo_rename.log 2>&1
   ```

This will run automatically and log results to `/volume1/logs/photo_rename.log`

---

## Common Synology Paths

| Description | Path |
|-------------|------|
| Default photo location | `/volume1/photo` |
| Scripts folder | `/volume1/scripts` |
| Home folder | `/volume1/homes/username` |
| Shared folder | `/volume1/shared` |
| Logs | `/volume1/logs` |

---

## Troubleshooting

### "Command not found"
```bash
# Make sure it's executable
chmod +x synology_rename_photos.py

# Run with explicit python3
python3 ./synology_rename_photos.py --dry-run
```

### "PIL not installed"
```bash
# Install Pillow
sudo python3 -m pip install Pillow exifread
```

### "Permission denied"
```bash
# Run as root or use sudo
sudo ./synology_rename_photos.py --dry-run

# Or change ownership
sudo chown admin:administrators synology_rename_photos.py
```

### "Directory does not exist"
```bash
# Check your volume name (might be volume2, etc.)
ls -la /volume*/

# Or specify the correct path
./synology_rename_photos.py /volume2/photo --dry-run
```

---

## What the Script Does

1. ✅ **Scans** `/volume1/photo` recursively by default
2. ✅ **Reads** EXIF metadata without modifying it
3. ✅ **Prioritizes** DateTimeOriginal > DateTimeDigitized > DateTime
4. ✅ **Validates** dates (must be 2001-2025)
5. ✅ **Renames** files to `IMG_yyyyMMdd_HHmmss.ext` format
6. ✅ **Includes** artist name if present: `IMG_yyyyMMdd_HHmmss(ArtistName).ext`
7. ✅ **Handles** duplicates automatically
8. ✅ **Never** modifies EXIF metadata

---

## Safety Features

- 🔒 **Read-only for metadata** - Never overwrites EXIF data
- 🔍 **Dry-run mode** - Preview before making changes
- ✅ **Validation** - Only uses dates between 2001-2025
- 🚫 **Rejects placeholders** - Ignores dates like 2000-01-01
- 📋 **Detailed logging** - See exactly what happens

---

## Example Output

```
================================================================================
SYNOLOGY PHOTO RENAMER
================================================================================
Directory: /volume1/photo
Mode: LIVE (will rename)
Recursive: Yes
================================================================================

Found 1547 file(s) to process

Process 1547 files? (y/n): y

================================================================================
Processing files...
================================================================================

[1/1547] ✓ DSC_0001.jpg
         → IMG_20180610_152030.jpg
         Date: 2018-06-10 15:20:30 (from DateTimeOriginal)

[2/1547] ✓ Already correctly named: IMG_20180610_152035.jpg

[3/1547] ✓ photo.jpg
         → IMG_20190315_103045(JBobphotography).jpg
         Date: 2019-03-15 10:30:45 (from DateTimeOriginal) | Artist: John Bob Photography

...

================================================================================
SUMMARY
================================================================================
Total files: 1547
Successfully renamed: 1423
Already correctly named: 98
Errors: 26
================================================================================
```

---

## Tips

1. **Always test first**: Use `--dry-run` on a small folder before running on your entire library
2. **Check logs**: Review the output to ensure dates look correct
3. **Backup**: Consider taking a snapshot before large operations
4. **Start small**: Test on one folder (e.g., `/volume1/photo/2016`) before processing everything
5. **Monitor**: First time, run without `--quiet` to see what's happening

---

## Help

```bash
./synology_rename_photos.py --help
```

Shows all available options.
