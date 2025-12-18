# The Problem and Solution - Photo Metadata Corruption

## The Problem 🔴

### What Went Wrong?

The previous scripts (`fix_2025_files.py`, `update_and_rename.py`) were **destroying precious photo metadata** by:

1. **Overwriting DateTimeOriginal** - The most important EXIF field that records when a photo was actually taken
2. **Ignoring actual creation dates** - Using arbitrary dates or file modification dates instead
3. **Forcing incorrect dates** - Making all files in a folder have the same date (e.g., December 17, 2016)
4. **No validation** - Not checking if the date being written makes sense

### Real-World Impact

**Example 1**: Photo taken in June 2018
- **Original metadata**: DateTimeOriginal = `2018:06:10 15:20:30` ✓
- **After bad script**: DateTimeOriginal = `2016:12:17 12:00:00` ❌
- **Filename**: `IMG_20251217_120000.jpg` ❌❌

**Result**: A 2018 photo is now incorrectly labeled as 2016 in metadata AND 2025 in filename!

### Why This Happened

The old scripts had this logic:
```python
# BAD: Forces a specific date
target_date = datetime(2016, 12, 17, 12, 0, 0)  # Arbitrary!

# BAD: Overwrites the original creation date
exif_dict[36867] = target_date  # DateTimeOriginal destroyed!
```

They were designed to "fix" files that were in the wrong folder, but instead of:
- Reading the actual date → renaming/moving the file

They did:
- Forcing a date based on folder name → overwriting metadata → renaming

This is **backwards** and **destructive**!

## The Solution ✅

### New Approach

The new scripts follow this **correct** workflow:

1. **READ** metadata without touching it
2. **PRIORITIZE** the most reliable date sources:
   - DateTimeOriginal (when photo was taken) - **PRIMARY**
   - DateTimeDigitized (when scanned/imported)
   - DateTime (last modification in camera)
   - File system creation date (last resort)
3. **VALIDATE** dates (must be 2001-2025, not placeholder dates)
4. **RENAME** files based on what we found
5. **NEVER** overwrite metadata

### New Scripts

#### 1. `scan_metadata_dates.py` - Detective Tool 🔍

```bash
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious
```

**What it does:**
- Shows ALL dates found in each file
- Highlights files with mismatched dates (e.g., metadata says 2018, filename says 2025)
- Helps identify which files were corrupted

**Output example:**
```
IMG_20251217_120000.jpg
⚠ WARNING: Multiple years found: [2016, 2025]
--------------------------------------------------------------------------------
  Metadata            | EXIF_DateTimeOriginal          | 2016:12:17 12:00:00 [2016]
  Metadata            | EXIF_DateTime                  | 2016:12:17 12:00:00 [2016]
  FileSystem          | FS_Birthtime                   | 2018-06-10 15:20:30 [2018]
  FileSystem          | FS_Modified                    | 2025-12-17 10:15:00 [2025]
```

This immediately shows the corruption: metadata was overwritten with 2016, but file system still has 2018!

#### 2. `find_and_rename_by_original_date.py` - Renaming Tool 📝

```bash
# Safe preview
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run

# Actually rename
./find_and_rename_by_original_date.py /Volumes/photo-1/2016
```

**What it does:**
- Finds the TRUE original date from metadata
- Renames files to match: `IMG_20180610_152030.jpg`
- Includes artist name if present: `IMG_20180610_152030(JBobphotography).jpg`
- Handles duplicates automatically
- **NEVER touches the metadata itself**

**Key features:**
- ✅ Read-only for metadata
- ✅ Smart date prioritization
- ✅ Validates date ranges (2001-2025)
- ✅ Rejects placeholder dates
- ✅ Supports photos AND videos
- ✅ Dry-run mode for safety

#### 3. `extract_date_from_filename.py` - Recovery Tool 🔧

For files where metadata is already corrupted beyond repair:

```bash
# See what can be extracted from filenames
./extract_date_from_filename.py /Volumes/photo-1/2016

# Restore metadata from filenames (USE WITH CAUTION)
./extract_date_from_filename.py /Volumes/photo-1/2016 --update --dry-run
```

**Use cases:**
- Files were correctly renamed BEFORE metadata was corrupted
- You need to restore EXIF from correct filenames
- Last resort recovery

**⚠️ Warning**: The `--update` flag WILL overwrite metadata. Only use if:
- You have backups
- The filename date is definitely correct
- The metadata is already wrong anyway

## How to Fix Your Files

### Step 1: Assess the Damage

```bash
# Find all files with suspicious dates
./scan_metadata_dates.py /Volumes/photo-1 --recursive --suspicious > problem_files.txt

# Check specific years
./scan_metadata_dates.py /Volumes/photo-1/2016 --filter-year 2025
```

### Step 2: Preview the Fix

```bash
# See what would happen (safe, no changes)
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run
```

Review the output carefully. Look for:
- ✅ Dates that make sense (match the folder/timeframe)
- ❌ Dates that seem wrong
- ⚠️ Files using "File Creation Date" instead of EXIF (metadata might be missing)

### Step 3: Apply the Fix

```bash
# Rename files based on original metadata
./find_and_rename_by_original_date.py /Volumes/photo-1/2016

# Or process entire drive
./find_and_rename_by_original_date.py /Volumes/photo-1 --recursive --yes
```

### Step 4: Verify

```bash
# Check results
./scan_metadata_dates.py /Volumes/photo-1/2016
```

Files should now have consistent dates between filename and metadata.

## Recovery Strategies

### If Metadata is Already Corrupted

**Best option**: Restore from backup (Time Machine, etc.)

**If no backup**:

1. **Check file system dates** - Often still accurate:
   ```bash
   ./scan_metadata_dates.py /path --show-all
   ```
   Look for `FS_Birthtime` - this is often the real creation date

2. **Extract from filename** - If files were correctly named first:
   ```bash
   ./extract_date_from_filename.py /path --update --dry-run
   ```

3. **Manual correction** - For important photos, check:
   - Email attachments (original date in email)
   - Social media uploads (date posted)
   - Related photos in same session
   - GPS coordinates (can help pinpoint when/where)

### Prevention

❌ **Never use these scripts again:**
- `fix_2025_files.py` - Overwrites metadata
- `update_and_rename.py` - Overwrites metadata
- Any script that calls `update_exif_to_date()` with arbitrary dates

✅ **Safe practices:**
- Always use `--dry-run` first
- Make backups before batch operations
- Use `scan_metadata_dates.py` to verify before/after
- Only use `find_and_rename_by_original_date.py` (read-only for metadata)

## Technical Details

### Date Priority Logic

```
Priority 1: EXIF DateTimeOriginal (tag 36867)
   ↓ If not found or invalid
Priority 2: EXIF DateTimeDigitized (tag 36868)
   ↓ If not found or invalid
Priority 3: EXIF DateTime (tag 306)
   ↓ If not found or invalid
Priority 4: File system creation date (st_birthtime)
   ↓ If not found or invalid
Priority 5: File system modification date (st_mtime)
```

### Validation Rules

- ✅ Year must be 2001-2025
- ❌ Reject 2000-01-01 (common placeholder)
- ❌ Reject dates before 1990 (likely corrupted)
- ✅ Date must be parseable
- ✅ Date must be valid (no Feb 30, etc.)

### Filename Format

Photos: `IMG_yyyyMMdd_HHmmss.ext`
Videos: `MOV_yyyyMMdd_HHmmss.ext`
With artist: `IMG_yyyyMMdd_HHmmss(ArtistName).ext`

Artist name formatting:
- "John Bob Photography" → `JBobphotography`
- First word: first letter only (uppercase)
- Second word: whole word (capitalize first letter)
- Remaining words: whole word (lowercase)
- Non-alphanumeric characters removed

## Summary

| Old Approach ❌ | New Approach ✅ |
|----------------|-----------------|
| Overwrites DateTimeOriginal | Never touches metadata |
| Uses arbitrary dates | Uses actual original dates |
| Destroys creation dates | Preserves all dates |
| Forces dates by folder | Validates date makes sense |
| No undo | Safe (only renames) |
| Dangerous | Safe |

**Bottom line**: The old scripts were metadata **destroyers**. The new scripts are metadata **readers** and filename **fixers**.

Your photo dates are precious historical records. Never let software overwrite them arbitrarily!
