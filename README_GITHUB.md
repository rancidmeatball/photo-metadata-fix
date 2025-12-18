# Photo Metadata Fix & Recovery Tools

🔧 **Complete solution for fixing photo metadata corruption and safely renaming files based on original creation dates**

## 🎯 Purpose

This toolkit helps you:
- **Find and fix corrupted photo metadata** (dates that were accidentally overwritten)
- **Safely rename photos** based on TRUE original creation dates
- **Recover from metadata damage** caused by batch processing scripts
- **Never overwrite metadata** - only reads it to find correct dates

## ⚠️ The Problem It Solves

Photo management scripts sometimes **overwrite EXIF DateTimeOriginal** with arbitrary dates, destroying the record of when photos were actually taken. This toolkit:
1. **Reads** original dates from metadata (DateTimeOriginal → DateTimeDigitized → DateTime)
2. **Validates** dates (2001-2025, rejects placeholders)
3. **Renames** files accordingly
4. **Never modifies** EXIF data

## ✨ Key Features

### Safe Renaming Scripts
- ✅ **Never modify metadata** - read-only approach
- ✅ **Prioritize original dates** - DateTimeOriginal first
- ✅ **Validate dates** - only 2001-2025
- ✅ **Include artist names** - formatted per specification
- ✅ **Handle duplicates** - automatic counter suffix

### Checkpoint & Resume System
- ✅ **Saves progress every 100 files** - minimal overhead
- ✅ **Auto-resume** - continue after interruption
- ✅ **Crash recovery** - atomic file writes
- ✅ **Background compatible** - works with nohup, screen, tmux
- ✅ **Progress tracking** - real-time stats in checkpoint file

### Recovery Tools
- ✅ **Log parsing** - extract rename history
- ✅ **State capture** - snapshot current file locations
- ✅ **Date extraction** - from filenames when metadata lost
- ✅ **Diagnostic scanning** - identify corrupted files

## 📂 Main Scripts

### For Synology NAS

#### `synology_rename_photos_with_checkpoint.py` ⭐ **RECOMMENDED**
```bash
# With checkpoints (can resume if interrupted)
./synology_rename_photos_with_checkpoint.py --yes

# Resume after interruption
./synology_rename_photos_with_checkpoint.py --resume

# Dry run (preview)
./synology_rename_photos_with_checkpoint.py --dry-run
```

**Features:**
- Defaults to `/volume1/photo` recursive
- Checkpoint system built-in
- Background execution ready

#### `synology_rename_photos.py`
Basic version without checkpoints (simpler, faster for small jobs)

### For macOS/Linux

#### `find_and_rename_with_checkpoint.py` ⭐ **RECOMMENDED**
```bash
# With checkpoints
./find_and_rename_with_checkpoint.py /path/to/photos --yes

# Resume
./find_and_rename_with_checkpoint.py /path/to/photos --resume
```

#### `find_and_rename_by_original_date.py`
Basic version without checkpoints

### Diagnostic & Recovery

#### `scan_metadata_dates.py`
Find files with suspicious/corrupted dates
```bash
./scan_metadata_dates.py /path/to/photos --suspicious
./scan_metadata_dates.py /path/to/photos --filter-year 2025
```

#### `capture_current_state.py`
Snapshot current file locations and dates (critical for recovery)
```bash
./capture_current_state.py /path/to/photos
```

#### `parse_rename_logs.py`
Extract rename history from logs
```bash
./parse_rename_logs.py logs/*.log
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install Pillow exifread

# Optional (for video files)
brew install exiftool  # macOS
```

### 2. Test on Small Directory
```bash
# Preview what would happen
./synology_rename_photos_with_checkpoint.py /volume1/photo/test --dry-run

# If looks good, run for real
./synology_rename_photos_with_checkpoint.py /volume1/photo/test --yes
```

### 3. Run on Full Library (Background)
```bash
# Use screen to survive SSH disconnects
screen -S photo_rename
./synology_rename_photos_with_checkpoint.py --yes
# Press Ctrl+A then D to detach

# Reconnect later
screen -r photo_rename
```

## 📊 File Naming Format

### Photos
- Basic: `IMG_20231225_143052.jpg`
- With artist: `IMG_20231225_143052(JBobphotography).jpg`

### Videos
- Basic: `MOV_20220704_101530.mov`

### Artist Name Format
- Input: "John Bob Photography"
- Output: `JBobphotography`
- Rules: First word (first letter only), second word (capitalized), rest (lowercase)

## 🔄 Background Execution

### Method 1: screen (Recommended)
```bash
screen -S photo_rename
./synology_rename_photos_with_checkpoint.py --yes
# Ctrl+A, D to detach
# screen -r photo_rename to reconnect
```

### Method 2: nohup
```bash
nohup ./synology_rename_photos_with_checkpoint.py --yes > rename.log 2>&1 &
tail -f rename.log  # Monitor progress
```

### Method 3: tmux
```bash
tmux new -s photo_rename
./synology_rename_photos_with_checkpoint.py --yes
# Ctrl+B, D to detach
```

## 💾 Checkpoint System

### How It Works
- Saves progress every 100 files to `.photo_rename_checkpoint.json`
- Tracks: current index, renamed count, errors
- Auto-resumes from last checkpoint

### Checking Progress
```bash
# View checkpoint
cat /volume1/photo/.photo_rename_checkpoint.json

# Extract stats
grep -E "(current_index|stats)" .photo_rename_checkpoint.json
```

### Resume After Interruption
```bash
# Just run again - auto-detects checkpoint
./synology_rename_photos_with_checkpoint.py --yes

# Or explicitly
./synology_rename_photos_with_checkpoint.py --resume
```

## 🔍 Recovery from Metadata Corruption

If your metadata was already corrupted by other scripts:

### 1. Capture Current State
```bash
./capture_current_state.py /Volumes/photo-1
```
Creates CSV/JSON with:
- Current filenames and locations
- File system dates (birthtime = likely TRUE date!)
- Directory structure
- EXIF dates (may be corrupted)

### 2. Check File System Dates
**Key insight:** File birthtime is often the TRUE creation date because bad scripts only changed EXIF, not filesystem!

```bash
./scan_metadata_dates.py /path --show-all
# Look for "FS_Birthtime" - this is reliable!
```

### 3. Use Directory Structure
Files in `/2018/vacation/` are probably from 2018. Directory location is a strong clue!

### 4. Parse Old Logs
If you have rename logs:
```bash
./parse_rename_logs.py /path/to/*.log
# Creates recovery database with old→new filename mappings
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `START_HERE.md` | Main entry point |
| `CHECKPOINT_AND_BACKGROUND_GUIDE.md` | Complete checkpoint guide |
| `RECOVERY_GUIDE.md` | Detailed recovery instructions |
| `COMPLETE_SOLUTION_SUMMARY.md` | Full overview |
| `SYNOLOGY_SETUP.md` | Synology-specific setup |

## ⚠️ What NOT to Use

The `oldscriptfiles/` directory contains **dangerous scripts** that overwrite metadata:
- ❌ `-dangerous!-fix_2025_files.py` - DO NOT USE
- ❌ `-dangerous!-update_and_rename.py` - DO NOT USE
- ❌ `-dangerous!-fix_metadata.py` - DO NOT USE

These are kept for reference only.

## 🎯 Best Practices

### ✅ Do:
- Always use `--dry-run` first
- Run `capture_current_state.py` before major operations
- Use checkpoint versions for large libraries
- Trust file birthtime over EXIF if they conflict
- Process one directory at a time for testing

### ❌ Don't:
- Never run scripts that overwrite metadata
- Don't trust EXIF dates that seem wrong
- Don't delete checkpoint files while running
- Don't process same directory twice simultaneously

## 🆘 Support & Issues

If metadata is corrupted:
1. **Stop immediately** - don't run more scripts
2. **Capture state** - run `capture_current_state.py`
3. **Check backups** - restore from Time Machine if possible
4. **Check birthtime** - file system dates are often correct
5. **Use directory** - location is a strong date clue

## 📜 License

MIT License - Use freely, modify as needed

## 🙏 Credits

Created to solve real-world photo metadata corruption problems. Built with safety as top priority - reads metadata, never writes.

---

**Status:** Production ready | **Version:** 2.0 (with checkpoints)

**Keywords:** photo metadata, EXIF recovery, DateTimeOriginal, safe rename, checkpoint resume, Synology NAS, photo organization
