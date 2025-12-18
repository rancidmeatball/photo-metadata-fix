# 🔧 RECOVERY GUIDE - Undoing Rename Damage

## ✅ GOOD NEWS!

Your rename operations **WERE LOGGED!** I've already:

1. ✅ **Backed up your logs** to `LOG_BACKUPS/` (326,054 lines!)
2. ✅ **Parsed the logs** and created recovery database
3. ✅ **Found 133,151 rename operations** with old→new mappings
4. ✅ **Created recovery tools** to help restore files

---

## 📊 What Was Logged

Your rename logs contain:
- **Original filename** (before rename)
- **New filename** (after rename)
- **Timestamp** of when renamed
- **Directory** location
- **Action type** (RENAMED or MOVED)

Example from your log:
```
[2025-12-16 19:29:26] Processing: SYNOPHOTO_THUMB_M.jpg
[2025-12-16 19:29:26]   RENAMED: SYNOPHOTO_THUMB_M.jpg -> IMG_20240921_051446.jpg
```

---

## 📁 Recovery Files Created

Located in `/Users/john/Cursor/fix_metadata/RECOVERY/`:

### 1. `recovery_database_*.json`
- **Purpose**: Machine-readable database for scripts
- **Contains**: 121,989 filename mappings (new → original)
- **Use**: Can be used to programmatically rename files back

### 2. `recovery_list_*.csv`
- **Purpose**: Human-readable spreadsheet
- **Contains**: All 133,151 operations
- **Use**: Open in Excel to search for specific files
- **Columns**: Timestamp, Original Filename, New Filename, Directory, Action

### 3. `recovery_summary_*.txt`
- **Purpose**: Quick overview
- **Contains**: Statistics and sample entries
- **Use**: Review what happened

---

## 🔍 Finding File's Original Name

### Option 1: Using Excel/CSV (Easiest)

1. Open `recovery_list_*.csv` in Excel
2. Search (Cmd+F) for the current filename
3. Look at "Original Filename" column

### Option 2: Using Terminal

```bash
# Search for a file's original name
grep "current_filename.jpg" /Users/john/Cursor/fix_metadata/RECOVERY/recovery_list_*.csv
```

---

## 💾 Capturing Current State (CRITICAL!)

**BEFORE renaming anything else**, capture the current state:

```bash
cd /Users/john/Cursor/fix_metadata

# Capture state of /Volumes/photo-1
./capture_current_state.py /Volumes/photo-1

# This creates:
# - file_state_*.json - Complete database
# - file_state_*.csv - Spreadsheet view
# - directory_structure_*.txt - Directory tree
```

This captures:
- ✅ Current filename and location
- ✅ Directory structure (can restore files to correct folders!)
- ✅ File system dates (birthtime = likely true creation date!)
- ✅ EXIF dates from metadata
- ✅ File size, extension

**Why this is important**: The directory a file is in is often the correct date/location! If a file is in `/Volumes/photo-1/2018/vacation/`, that's probably when it was taken.

---

## 🔄 Recovery Strategies

### Strategy 1: Use File System Dates (RECOMMENDED)

The file system's `birthtime` (creation date) is often the TRUE original date because:
- It's set when the file is first created
- It doesn't get overwritten by metadata tools
- It's been preserved through your renames

**Check file system dates**:
```bash
./scan_metadata_dates.py /Volumes/photo-1/2016
```

Look for `FS_Birthtime` - this is likely the real creation date!

### Strategy 2: Use Directory as Clue

Files in `/Volumes/photo-1/2018/` were probably taken in 2018!

The `capture_current_state.py` script records the directory for every file so you can:
1. Find files currently in 2018 folder
2. Assume they were taken in 2018
3. Use directory name as date source

### Strategy 3: Manual Lookup

For important photos:
1. Open `recovery_list_*.csv` in Excel
2. Find the current filename
3. See what the original name was
4. Original name might have the correct date!

For example:
- Original: `IMG20180610_152030.jpg` (has date!)
- Current: `IMG_20161217_120000.jpg` (wrong date)
- **Recovery**: Extract date from original filename = June 10, 2018

---

## 🛠️ Recovery Scripts

### 1. Parse Rename Logs

Already done! But you can re-run:

```bash
./parse_rename_logs.py /Users/john/Cursor/fix_metadata/LOG_BACKUPS/*.log
```

### 2. Capture Current State

**DO THIS NOW before making any more changes!**

```bash
# Capture entire /Volumes/photo-1
./capture_current_state.py /Volumes/photo-1 --output-dir STATE_BACKUPS

# Or just a specific folder
./capture_current_state.py /Volumes/photo-1/2016 --output-dir STATE_BACKUPS
```

### 3. Analyze What Went Wrong

```bash
# Show files with suspicious dates
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious

# Show files with specific year
./scan_metadata_dates.py /Volumes/photo-1 --recursive --filter-year 2018
```

---

## 📋 Step-by-Step Recovery Plan

### Phase 1: Assessment (DO NOW)

```bash
cd /Users/john/Cursor/fix_metadata

# 1. Capture current state of ALL files
./capture_current_state.py /Volumes/photo-1 --output-dir STATE_BACKUPS

# 2. Scan for suspicious dates
./scan_metadata_dates.py /Volumes/photo-1 --recursive --suspicious > suspicious_files.txt

# 3. Review recovery database
open RECOVERY/recovery_list_*.csv  # Opens in Excel
```

### Phase 2: Analysis

1. **Open** `STATE_BACKUPS/file_state_*.csv` in Excel
2. **Look at columns**:
   - `Relative Directory` - Where file currently lives (e.g., "2018/vacation")
   - `File Created` - File system birthtime (likely true date!)
   - `EXIF DateTimeOriginal` - Current metadata date
3. **Compare**:
   - If `File Created` = 2018 but `EXIF DateTimeOriginal` = 2016, the EXIF was corrupted
   - If file is in `2018/` folder, it's probably from 2018

### Phase 3: Prioritize

Focus on:
1. **Files in wrong folders**: Photo from 2018 in `/2016/` folder
2. **Files with mismatched dates**: birthtime ≠ EXIF date
3. **Important photos**: Family events, vacations, etc.

### Phase 4: Selective Recovery

For files you want to fix:

```bash
# Extract date from original filename (if it had one)
./extract_date_from_filename.py /path/to/folder --show-all

# Use file system date as source
# (Look at STATE_BACKUPS CSV for birthtime)

# Manually rename important files
```

---

## ⚠️ Important: Don't Make It Worse!

**BEFORE running any more rename scripts:**

1. ✅ **Capture current state** (see Phase 1 above)
2. ✅ **Review what you have** (open CSV files)
3. ✅ **Make a backup** (copy important folders)
4. ✅ **Test on small folder first**
5. ✅ **Always use `--dry-run` first**

**DON'T:**
- ❌ Run batch rename scripts without `--dry-run`
- ❌ Trust EXIF dates that seem wrong
- ❌ Overwrite metadata again
- ❌ Delete the recovery files!

---

## 🎯 Example: Recovering a Specific File

Let's say you have: `IMG_20161217_120000.jpg`

**Step 1**: Find original name
```bash
grep "IMG_20161217_120000.jpg" RECOVERY/recovery_list_*.csv
```

Output shows:
```
2025-12-10 21:07:16,IMG20180610_152030.jpg,IMG_20161217_120000.jpg,/Volumes/photo-1,RENAMED
```

**Step 2**: Original name was `IMG20180610_152030.jpg` - has date June 10, 2018!

**Step 3**: Check current location
```bash
# Look in STATE_BACKUPS CSV for this file
grep "IMG_20161217_120000.jpg" STATE_BACKUPS/file_state_*.csv
```

Shows it's in `/Volumes/photo-1/2018/vacation/`

**Step 4**: Confirm - probably taken June 10, 2018!

**Step 5**: Rename back or update metadata
```bash
# Option A: Rename to correct date
mv IMG_20161217_120000.jpg IMG_20180610_152030.jpg

# Option B: Update metadata (if you're SURE)
# exiftool -DateTimeOriginal='2018:06:10 15:20:30' IMG_20161217_120000.jpg
```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Capture current state | `./capture_current_state.py /Volumes/photo-1` |
| Find suspicious files | `./scan_metadata_dates.py /path --suspicious` |
| Parse logs | `./parse_rename_logs.py LOG_BACKUPS/*.log` |
| Search for file | `grep "filename" RECOVERY/*.csv` |
| Open in Excel | `open RECOVERY/recovery_list_*.csv` |

---

## 🔑 Key Files to Protect

**NEVER delete these:**
- `LOG_BACKUPS/` - Original rename logs
- `RECOVERY/` - Parsed recovery database
- `STATE_BACKUPS/` - Current file state captures

These are your insurance policy!

---

## 💡 Tips for Future

1. **Always log before changing**: Use `capture_current_state.py` first
2. **Always dry-run**: Use `--dry-run` flag
3. **Never overwrite metadata**: Only rename files
4. **Trust file system dates**: birthtime is often correct
5. **Use directory structure**: Files in 2018/ folder are probably from 2018
6. **Keep backups**: Logs, state captures, recovery databases

---

## ✅ Summary

**You have:**
- ✅ 133,151 logged rename operations
- ✅ Recovery database with old→new mappings
- ✅ CSV files to search in Excel
- ✅ Tools to capture current state
- ✅ Scripts to analyze and fix

**Next steps:**
1. Run `./capture_current_state.py /Volumes/photo-1` **NOW**
2. Review `STATE_BACKUPS/*.csv` in Excel
3. Check file system dates (birthtime) as true dates
4. Use directory structure as date clue
5. Fix important files first

**You can recover!** The information is there, it just needs to be pieced together.
