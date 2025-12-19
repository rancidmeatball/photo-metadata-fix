# 🔧 HEIC File Recovery Guide

## Complete guide for recovering HEIC file metadata using exiftool

---

## 📋 Prerequisites

### **1. Install exiftool**

**On macOS:**
```bash
brew install exiftool
```

**On Synology:**
```bash
# Option 1: Via Synology Package Manager (if available)
# Check Package Center for "exiftool"

# Option 2: Manual installation
# Download from: https://exiftool.org/install.html
# Or use: sudo synopkg install exiftool
```

**Verify installation:**
```bash
exiftool -ver
```

Should show version number (e.g., `12.70`).

---

## 🚀 Complete HEIC Recovery Workflow

### **Phase 1: Create HEIC Recovery Plan** (Safe - No Changes)

**On your Mac:**
```bash
cd ~/Cursor/fix_metadata

# Create HEIC-only recovery plan
python3 create_heic_recovery_plan.py \
  --input recovery_plan.csv \
  --output recovery_plan_heic_only.csv \
  --confidence HIGH
```

**Output:**
- Creates `recovery_plan_heic_only.csv` with HEIC files only
- Shows statistics: confidence levels, update reasons

---

### **Phase 2: Upload to Synology**

**Via FileZilla:**
1. Upload `recovery_plan_heic_only.csv` → `/volume1/photo/`
2. Upload `synology_apply_heic_recovery_plan.py` → `/volume1/photo/scripts/`

**Make executable:**
```bash
ssh john@chipnas.lan
chmod +x /volume1/photo/scripts/synology_apply_heic_recovery_plan.py
```

---

### **Phase 3: Test on 10 Files** (Dry Run)

```bash
cd /volume1/photo/scripts

# Dry run on 10 files
python3 ./synology_apply_heic_recovery_plan.py \
  --plan /volume1/photo/recovery_plan_heic_only.csv \
  --confidence HIGH \
  --limit 10 \
  --dry-run
```

**Review the output** - does it look correct?

---

### **Phase 4: Test on 10 Files** (For Real)

```bash
# Actually update 10 files
python3 ./synology_apply_heic_recovery_plan.py \
  --plan /volume1/photo/recovery_plan_heic_only.csv \
  --confidence HIGH \
  --limit 10 \
  --yes
```

**Verify:** Check one updated file:
```bash
exiftool -DateTimeOriginal /volume1/photo/2023/2023/IMG_20230101_000125.heic
```

---

### **Phase 5: Apply to All HIGH Confidence** (Background)

```bash
# Run in background with nohup
cd /volume1/photo/scripts

nohup python3 ./synology_apply_heic_recovery_plan.py \
  --plan /volume1/photo/recovery_plan_heic_only.csv \
  --confidence HIGH \
  --yes \
  --log-file /volume1/photo/logs/heic_recovery_high.log \
  --undo-file /volume1/photo/undo_heic_recovery_high.json \
  > /volume1/photo/logs/heic_recovery_high_output.log 2>&1 &

echo $! > /volume1/photo/logs/heic_recovery_high.pid

# Can disconnect SSH - it keeps running!
```

**Monitor progress:**
```bash
# Check if running
ps aux | grep synology_apply_heic_recovery

# View log
tail -f /volume1/photo/logs/heic_recovery_high_output.log

# Count completed
grep "✓ Updated" /volume1/photo/logs/heic_recovery_high.log | wc -l
```

---

## 📊 What Gets Updated

### **HEIC Files (5,515 HIGH confidence)**

**Category: Missing EXIF (5,515 files)**
- Current EXIF: NONE
- Will be populated with date from old filename
- Safest update!

Example:
```
File: IMG_20230101_000125.heic
Old filename: IMG20230101_000125.heic
Current EXIF: NONE
Will set to: 2023-01-01 00:01:25
```

---

## ⚠️ Important Notes

### **exiftool Requirements**
- Must be installed on Synology
- May require manual installation if not in Package Center
- Check with: `exiftool -ver`

### **Processing Time**
- HEIC files take longer than JPG
- Expect ~1-2 seconds per file
- 5,515 files ≈ 1.5-3 hours

### **Safety Features**
- ✅ Dry-run testing
- ✅ Limit testing
- ✅ Detailed logging
- ✅ Undo information
- ✅ Confidence filtering

---

## 📁 Synology Directory Structure

```
/volume1/photo/
├── scripts/
│   └── synology_apply_heic_recovery_plan.py
├── logs/
│   ├── heic_recovery_high.log
│   └── heic_recovery_high_output.log
├── recovery_plan_heic_only.csv
└── undo_heic_recovery_high.json
```

---

## 🔍 Verification After Recovery

### **Check Sample Files**
```bash
# Check a file that was updated
exiftool -DateTimeOriginal /volume1/photo/2023/2023/IMG_20230101_000125.heic

# Should show: 2023:01:01 00:01:25
```

### **Count Successes**
```bash
grep "✓ Updated" /volume1/photo/logs/heic_recovery_high.log | wc -l
```

### **Check for Errors**
```bash
grep "✗ Error" /volume1/photo/logs/heic_recovery_high.log
```

---

## 📞 Quick Command Reference

```bash
# CREATE PLAN (on Mac)
python3 create_heic_recovery_plan.py \
  --input recovery_plan.csv \
  --output recovery_plan_heic_only.csv \
  --confidence HIGH

# TEST (10 files, dry-run)
python3 synology_apply_heic_recovery_plan.py \
  --plan /volume1/photo/recovery_plan_heic_only.csv \
  --confidence HIGH --limit 10 --dry-run

# APPLY (all HIGH confidence, background)
nohup python3 synology_apply_heic_recovery_plan.py \
  --plan /volume1/photo/recovery_plan_heic_only.csv \
  --confidence HIGH --yes \
  > /volume1/photo/logs/heic_recovery_high_output.log 2>&1 &
```

---

## 💡 Tips

1. **Install exiftool first** - required for HEIC processing
2. **Test on 10 files first** before full run
3. **Process in background** with nohup for large jobs
4. **Monitor progress** regularly
5. **Keep logs** for troubleshooting

---

## ✅ Success Metrics

After recovery, you should have:
- ✅ 5,515 HEIC files with corrected EXIF metadata
- ✅ Files match: Old filename date = Directory = Modified date = EXIF
- ✅ All changes logged
- ✅ Undo information preserved

---

**Status:** Ready for production use on Synology NAS (after exiftool installation)
