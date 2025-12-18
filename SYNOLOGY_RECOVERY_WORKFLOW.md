# 🔧 Synology Metadata Recovery Workflow

## Complete guide for recovering corrupted metadata on Synology NAS

---

## 📋 Prerequisites

### **1. Upload Files to Synology**

Upload these files to `/volume1/temporary/scripts/`:
- `synology_create_recovery_plan.py`
- `synology_apply_recovery_plan.py`
- `synology_rename_photos_with_checkpoint.py` (if not already uploaded)

### **2. Upload Recovery Data**

Upload to `/volume1/temporary/RECOVERY/`:
- `recovery_list_20251217_212102.csv` (from your Mac's RECOVERY folder)

Upload to `/volume1/temporary/STATE_BACKUPS/`:
- `file_state_20251217_220803.csv` (from your Mac's STATE_BACKUPS folder)

### **3. Make Scripts Executable**

```bash
ssh admin@your-synology
chmod +x /volume1/temporary/scripts/*.py
```

---

## 🚀 Complete Recovery Workflow

### **Phase 1: Create Recovery Plan** (Safe - No Changes)

```bash
ssh admin@your-synology
cd /volume1/temporary/scripts

# Create recovery plan
python3 ./synology_create_recovery_plan.py \
  --recovery-db /volume1/temporary/RECOVERY/recovery_list_20251217_212102.csv \
  --state-capture /volume1/temporary/STATE_BACKUPS/file_state_20251217_220803.csv \
  --output /volume1/temporary/recovery_plan.csv

# Optional: JPG files only (skip HEIC/MOV)
python3 ./synology_create_recovery_plan.py \
  --recovery-db /volume1/temporary/RECOVERY/recovery_list_20251217_212102.csv \
  --state-capture /volume1/temporary/STATE_BACKUPS/file_state_20251217_220803.csv \
  --output /volume1/temporary/recovery_plan_jpg.csv \
  --jpg-only
```

**Output:**
```
Files with date in old filename: 49,054
HIGH confidence: 9,575 files
Files needing updates: 6,774 HIGH confidence
```

---

### **Phase 2: Download and Review** (Critical!)

```bash
# From your Mac terminal
scp admin@your-synology:/volume1/temporary/recovery_plan.csv ~/Desktop/

# Open in Excel
open ~/Desktop/recovery_plan.csv
```

**Review in Excel:**
- Filter: `confidence` = `HIGH`
- Filter: `date_differs` = `YES`
- Filter: `file_extension` = `.jpg` (safest to update)
- Check `reasoning` column - does it make sense?
- Delete rows you're not confident about

**Save edited CSV**, then upload back:
```bash
scp ~/Desktop/recovery_plan.csv admin@your-synology:/volume1/temporary/
```

---

### **Phase 3: Test on 10 Files** (Dry Run)

```bash
ssh admin@your-synology
cd /volume1/temporary/scripts

# Dry run on 10 files
python3 ./synology_apply_recovery_plan.py \
  --plan /volume1/temporary/recovery_plan.csv \
  --confidence HIGH \
  --limit 10 \
  --dry-run
```

**Review the output** - does it look correct?

---

### **Phase 4: Test on 10 Files** (For Real)

```bash
# Actually update 10 files
python3 ./synology_apply_recovery_plan.py \
  --plan /volume1/temporary/recovery_plan.csv \
  --confidence HIGH \
  --limit 10 \
  --yes
```

**Verify:** Check one updated file:
```bash
# If exiftool installed
exiftool -DateTimeOriginal /volume1/photo/2015/IMG_20150128_113046.jpg

# Or check log
cat /volume1/temporary/logs/recovery_apply.log
```

---

### **Phase 5: Apply to All HIGH Confidence** (Background)

```bash
# Run in background with nohup
cd /volume1/temporary/scripts

nohup python3 ./synology_apply_recovery_plan.py \
  --plan /volume1/temporary/recovery_plan.csv \
  --confidence HIGH \
  --yes \
  --log-file /volume1/temporary/logs/recovery_high.log \
  --undo-file /volume1/temporary/undo_recovery_high.json \
  > /volume1/temporary/logs/recovery_output.log 2>&1 &

echo $! > /volume1/temporary/logs/recovery.pid

# Can disconnect SSH - it keeps running!
```

**Monitor progress:**
```bash
# Check if running
ps aux | grep synology_apply_recovery

# View log
tail -f /volume1/temporary/logs/recovery_output.log

# Count completed
grep "✓ Updated" /volume1/temporary/logs/recovery_high.log | wc -l
```

---

## 📊 What Gets Updated

### **HIGH Confidence Files (6,774 total)**

**Category 1: Missing EXIF (6,699 files)**
- Current EXIF: NONE
- Will be populated with date from old filename
- Safest update!

Example:
```
File: IMG_20150221_194221.jpg
Old filename: IMG_20150221_194221.JPG
Current EXIF: NONE
Will set to: 2015-02-21 19:42:21
Reasoning: Old filename matches directory (2015) and modified date
```

**Category 2: Corrupted EXIF (75 files)**
- Current EXIF: Wrong date (differs by 365+ days)
- Will be fixed to match old filename

Example:
```
File: IMG_20150128_113046.jpg
Old filename: IMG_20150128_113046.JPG
Current EXIF: 2017-06-27 (WRONG!)
Will change to: 2015-01-28 11:30:46
Reasoning: Old filename matches directory and modified date
```

---

## ⚠️ Important Limitations

### **HEIC Files**
- PIL/Pillow **cannot update HEIC EXIF** easily
- Options:
  1. Skip HEIC files for now
  2. Convert to JPG first
  3. Use exiftool instead (more complex)

**Recommended:** Use `--jpg-only` flag when creating plan

### **Video Files (MOV, MP4)**
- Don't have standard EXIF like photos
- Need different tools (exiftool)
- Skip videos for this recovery

---

## 🛡️ Safety Features

### **1. Dry-Run Testing**
```bash
--dry-run  # Shows what would happen, makes no changes
```

### **2. Limit Testing**
```bash
--limit 10  # Only process first 10 files
```

### **3. Detailed Logging**
```bash
cat /volume1/temporary/logs/recovery_apply.log
```

### **4. Undo Information**
```bash
cat /volume1/temporary/undo_recovery.json
# Contains backup of old EXIF values
```

### **5. Confidence Filtering**
```bash
--confidence HIGH  # Only safest files
```

---

## 📁 Synology Directory Structure

```
/volume1/
├── temporary/
│   ├── scripts/
│   │   ├── synology_create_recovery_plan.py
│   │   ├── synology_apply_recovery_plan.py
│   │   └── synology_rename_photos_with_checkpoint.py
│   ├── RECOVERY/
│   │   └── recovery_list_20251217_212102.csv
│   ├── STATE_BACKUPS/
│   │   └── file_state_20251217_220803.csv
│   ├── logs/
│   │   ├── recovery_apply.log
│   │   └── recovery_output.log
│   ├── recovery_plan.csv (created by script)
│   └── undo_recovery.json (created when applying)
└── photo/
    └── (your photos here)
```

---

## 🔍 Verification After Recovery

### **Check Sample Files**
```bash
# Check a file that was updated
exiftool -DateTimeOriginal /volume1/photo/2015/IMG_20150221_194221.jpg

# Should show: 2015:02:21 19:42:21
```

### **Count Successes**
```bash
grep "✓ Updated" /volume1/temporary/logs/recovery_high.log | wc -l
```

### **Check for Errors**
```bash
grep "✗ Error" /volume1/temporary/logs/recovery_high.log
```

---

## 📞 Quick Command Reference

```bash
# CREATE PLAN (read-only, safe)
python3 synology_create_recovery_plan.py \
  --recovery-db /volume1/temporary/RECOVERY/recovery_list_20251217_212102.csv \
  --state-capture /volume1/temporary/STATE_BACKUPS/file_state_20251217_220803.csv \
  --output /volume1/temporary/recovery_plan.csv

# DOWNLOAD & REVIEW
scp admin@your-synology:/volume1/temporary/recovery_plan.csv ~/Desktop/
open ~/Desktop/recovery_plan.csv

# UPLOAD AFTER EDITING
scp ~/Desktop/recovery_plan.csv admin@your-synology:/volume1/temporary/

# TEST (10 files, dry-run)
python3 synology_apply_recovery_plan.py \
  --plan /volume1/temporary/recovery_plan.csv \
  --confidence HIGH \
  --limit 10 \
  --dry-run

# APPLY (all HIGH confidence, background)
nohup python3 synology_apply_recovery_plan.py \
  --plan /volume1/temporary/recovery_plan.csv \
  --confidence HIGH \
  --yes \
  > /volume1/temporary/logs/recovery_output.log 2>&1 &
```

---

## 💡 Tips

1. **Start with JPG files only** - easiest to update
2. **Always test on 10 files first** before full run
3. **Review HIGH confidence entries** in Excel
4. **Keep logs** for troubleshooting
5. **Make backups** before large batches
6. **Process in background** with nohup for large jobs

---

## ✅ Success Metrics

After recovery, you should have:
- ✅ 6,774 files with corrected EXIF metadata
- ✅ Files match: Old filename date = Directory = Modified date = EXIF
- ✅ All changes logged
- ✅ Undo information preserved

---

**Status:** Ready for production use on Synology NAS
