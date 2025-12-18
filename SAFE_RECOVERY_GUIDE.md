# 🛡️ Safe Metadata Recovery Guide

## Overview

These scripts help you **safely recover corrupted metadata** by cross-referencing multiple sources:
- Old filenames (from recovery logs)
- Directory locations (2018 folder = 2018)
- File system dates (Modified date)
- Current EXIF metadata

The recovery process is **two-phase** for maximum safety:
1. **Phase 1**: Analyze and create recovery plan (READ ONLY)
2. **Phase 2**: Review plan, then apply changes (MODIFIES FILES)

---

## 📋 Recovery Scripts

### **1. `create_recovery_plan.py`** ✅ READ ONLY
Creates a recovery plan by analyzing all available date sources.
**DOES NOT modify any files** - only creates a CSV for review.

### **2. `apply_recovery_plan.py`** ⚠️ MODIFIES FILES
Applies the approved recovery plan to update EXIF metadata.
Includes safety features: backups, logging, undo capability.

---

## 🚀 Complete Recovery Workflow

### **Step 1: Create Recovery Plan** (Safe - No Changes)

```bash
cd /Users/john/Cursor/fix_metadata

# Create the recovery plan
./create_recovery_plan.py \
  --recovery-db RECOVERY/recovery_list_20251217_212102.csv \
  --state-capture STATE_BACKUPS/file_state_20251217_220803.csv \
  --output recovery_plan.csv
```

**What this does:**
- Reads recovery database (old→new filename mappings)
- Reads state capture (current locations, dates)
- Extracts dates from old filenames
- Cross-references with directory and File Modified dates
- Assigns confidence levels (HIGH, MEDIUM, LOW, VERY_LOW)
- Creates `recovery_plan.csv` for review

**Output:**
```
================================================================================
RECOVERY PLAN STATISTICS
================================================================================
Total files analyzed: 133730
Files with recovery info: 121989
Files with date in old filename: 32969

Confidence Distribution:
  HIGH confidence: 15234
  MEDIUM confidence: 12891
  LOW confidence: 3421
  VERY_LOW confidence: 1423

Recovery plan created: recovery_plan.csv
================================================================================
```

---

### **Step 2: Review Recovery Plan** (Critical!)

```bash
# Open in Excel
open recovery_plan.csv
```

**Check these columns:**

| Column | What to Check |
|--------|--------------|
| `confidence` | HIGH = safest, LOW = risky |
| `reasoning` | Why this date was chosen |
| `date_differs` | YES = needs update, NO = already correct |
| `current_exif_date` | What's currently in metadata |
| `proposed_date` | What we want to change it to |
| `dir_year` | What year folder it's in |

**Look for:**
- ✅ HIGH confidence with reasoning that makes sense
- ⚠️ MEDIUM confidence - review reasoning carefully
- ❌ LOW confidence - skip or investigate manually

**Example HIGH confidence entry:**
```
Current: MOV_20251208_022542.mp4
Old filename: MOV_20161215_143000.mp4
Proposed: 2016-12-15 14:30:00
Directory: 2016/
Confidence: HIGH
Reasoning: Old filename year (2016) matches directory (2016); 
           Old filename date matches File Modified date
```

---

### **Step 3: Test on Small Sample** (Highly Recommended!)

Before processing thousands of files, test on a few:

```bash
# Dry-run on 10 HIGH confidence files
./apply_recovery_plan.py \
  --plan recovery_plan.csv \
  --confidence HIGH \
  --limit 10 \
  --dry-run
```

**Review the output carefully!**

Then try for real on those 10 files:
```bash
# Actually update 10 files (on copies if possible)
./apply_recovery_plan.py \
  --plan recovery_plan.csv \
  --confidence HIGH \
  --limit 10 \
  --yes
```

**Verify:**
- Check one of the updated files with `exiftool`
- Make sure the date looks correct
- Check `recovery_apply.log` for details

---

### **Step 4: Apply to HIGH Confidence Files**

Once you're confident it works:

```bash
# Process all HIGH confidence files
./apply_recovery_plan.py \
  --plan recovery_plan.csv \
  --confidence HIGH \
  --yes \
  --log-file recovery_high_confidence.log
```

**This will:**
- Update all HIGH confidence files
- Log every change to `recovery_high_confidence.log`
- Create `undo_recovery.json` with backup info
- Show progress for each file

---

### **Step 5: Review Medium Confidence (Optional)**

After HIGH confidence files are done, review MEDIUM:

```bash
# Show MEDIUM confidence files
grep "MEDIUM" recovery_plan.csv > recovery_plan_medium.csv
open recovery_plan_medium.csv
```

**Manual review:**
- Check reasoning for each
- Verify dates make sense
- Only apply if you're confident

```bash
# Apply MEDIUM confidence (after review)
./apply_recovery_plan.py \
  --plan recovery_plan.csv \
  --confidence MEDIUM \
  --yes \
  --log-file recovery_medium_confidence.log
```

---

## 🔍 Understanding Confidence Levels

### **HIGH Confidence**
Multiple sources agree:
- Old filename year matches directory year
- Old filename date matches File Modified date
- Directory year matches File Modified year

**Example:**
```
File: IMG_20251208_022542.jpg (current)
Old: IMG20180315_143052.jpg → 2018-03-15
Directory: /2018/ → 2018
Modified: 2018-03-15 14:30:52 → 2018
Current EXIF: 2025-12-08 → WRONG

All sources agree on 2018! ✅ HIGH confidence
```

### **MEDIUM Confidence**
2 out of 3 sources agree:
- Old filename and Modified date agree (but wrong directory)
- OR Old filename and directory agree (but different Modified date)

**Example:**
```
File: IMG_20161217_120000.jpg
Old: IMG20180610_152030.jpg → 2018-06-10
Directory: /2016/ → 2016 (CONFLICT!)
Modified: 2018-06-10 15:20:30 → 2018

Old filename + Modified agree on 2018 ⚠️ MEDIUM confidence
(File is in wrong directory)
```

### **LOW Confidence**
Only 1 source or sources conflict:
- Might be correct, needs manual review

### **VERY_LOW Confidence**
Sources strongly conflict or invalid:
- Skip these, investigate manually

---

## ⚠️ Safety Features

### **1. Dry-Run Mode**
Always test first:
```bash
./apply_recovery_plan.py --plan recovery_plan.csv --confidence HIGH --dry-run
```

### **2. Detailed Logging**
Every change logged:
```bash
cat recovery_apply.log
```

### **3. Undo Capability**
Backup info saved:
```bash
cat undo_recovery.json
```

### **4. Confidence Filtering**
Only update files you trust:
```bash
# HIGH only (safest)
--confidence HIGH

# HIGH + MEDIUM
--confidence MEDIUM

# ALL (risky)
--confidence VERY_LOW
```

### **5. Limit Option**
Test on small batches:
```bash
--limit 10  # Only first 10 files
```

---

## 📊 Expected Results

Based on your data:

| Confidence | Count | Recommendation |
|-----------|-------|----------------|
| HIGH | ~15,000 | ✅ Safe to update |
| MEDIUM | ~13,000 | ⚠️ Review, then update |
| LOW | ~3,000 | ❌ Manual review required |
| VERY_LOW | ~1,000 | ❌ Skip or investigate |

---

## 🔧 Advanced Options

### **Process Specific Directory Only**

Edit recovery_plan.csv to filter:
```bash
# Create plan for just 2018 folder
grep "/2018/" recovery_plan.csv > recovery_plan_2018.csv

./apply_recovery_plan.py \
  --plan recovery_plan_2018.csv \
  --confidence HIGH \
  --yes
```

### **Backup Original Files**

```bash
./apply_recovery_plan.py \
  --plan recovery_plan.csv \
  --confidence HIGH \
  --backup-dir /volume1/temporary/backups \
  --yes
```

### **Process in Batches**

```bash
# Batch 1: First 1000
./apply_recovery_plan.py --plan recovery_plan.csv --confidence HIGH --limit 1000 --yes

# Batch 2: Edit recovery_plan.csv to remove processed files, then run again
```

---

## 🐛 Troubleshooting

### **Issue: "File not found"**
The file path changed since state capture.
- Re-run `capture_current_state.py`
- Create new recovery plan

### **Issue: "Date out of range"**
Date < 2001 or > 2025.
- Check old filename
- Might be invalid date in filename

### **Issue: "Unsupported file type"**
Only JPG, PNG, TIFF supported.
- Videos: Can't update EXIF (not supported)
- HEIC: Not supported by PIL

### **Issue: Too many MEDIUM confidence files**
Directory structure might be disorganized.
- Focus on HIGH confidence first
- Manually review MEDIUM entries
- Consider reorganizing folders

---

## ✅ Verification After Recovery

### **Check a Few Files:**
```bash
# Install exiftool if needed
brew install exiftool

# Check EXIF
exiftool -DateTimeOriginal -CreateDate /path/to/file.jpg
```

### **Spot Check in Excel:**
```bash
# Run capture_current_state again
./capture_current_state.py /Volumes/photo-1 --output-dir STATE_BACKUPS_AFTER

# Compare before/after
open STATE_BACKUPS/file_state_20251217_220803.csv
open STATE_BACKUPS_AFTER/file_state_*.csv
```

### **Check Logs:**
```bash
# See what was changed
cat recovery_apply.log | grep "✓ Updated"

# Count successes
grep "✓ Updated" recovery_apply.log | wc -l
```

---

## 💡 Tips for Best Results

### **Do:**
1. ✅ Always start with dry-run
2. ✅ Test on 10 files first
3. ✅ Review recovery plan in Excel
4. ✅ Start with HIGH confidence only
5. ✅ Keep logs for reference
6. ✅ Make backups before starting

### **Don't:**
1. ❌ Skip the review step
2. ❌ Apply to ALL confidence levels at once
3. ❌ Process without testing first
4. ❌ Delete logs or undo files
5. ❌ Modify files without backups

---

## 📞 Quick Reference

```bash
# STEP 1: CREATE PLAN (safe)
./create_recovery_plan.py \
  --recovery-db RECOVERY/recovery_list_*.csv \
  --state-capture STATE_BACKUPS/file_state_*.csv \
  --output recovery_plan.csv

# STEP 2: REVIEW
open recovery_plan.csv

# STEP 3: TEST (10 files, dry-run)
./apply_recovery_plan.py --plan recovery_plan.csv --confidence HIGH --limit 10 --dry-run

# STEP 4: TEST (10 files, real)
./apply_recovery_plan.py --plan recovery_plan.csv --confidence HIGH --limit 10 --yes

# STEP 5: APPLY (all HIGH confidence)
./apply_recovery_plan.py --plan recovery_plan.csv --confidence HIGH --yes

# CHECK LOGS
cat recovery_apply.log
```

---

## 🎯 Summary

**You now have:**
- ✅ Safe recovery plan creator (read-only)
- ✅ Controlled recovery applier (with safety features)
- ✅ Confidence-based filtering
- ✅ Dry-run capability
- ✅ Detailed logging
- ✅ Undo capability

**Recovery success depends on:**
- Quality of old filenames (32,969 have dates)
- Directory organization (year folders)
- File Modified dates accuracy

**For ~32,969 files with dates in old filenames, you can recover with HIGH confidence!**

---

**Ready to start? Begin with Step 1 - create the recovery plan!**
