# Photo/Video Metadata Fix and Rename Tools

## Problem Summary

The previous scripts (`fix_2025_files.py`, `update_and_rename.py`) were **destroying original metadata** by:
- Overwriting DateTimeOriginal, DateTimeDigitized, and DateTime fields with arbitrary dates
- Using the most recent modification date instead of the true creation date
- Forcing all files to have incorrect dates (e.g., forcing everything to December 17, 2016)

This resulted in photos from 2018 being incorrectly renamed to 2025, and potentially destroying the true original creation dates stored in the metadata.

## Solution

Three new scripts to diagnose and fix the issues:

### 1. `scan_metadata_dates.py` - Diagnostic Tool

Scans files and shows ALL dates found in metadata to help identify problems.

**Usage:**
```bash
# Scan current directory
./scan_metadata_dates.py

# Scan specific directory
./scan_metadata_dates.py /Volumes/photo-1/2016

# Show only suspicious files (mismatched dates)
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious

# Show only files with 2025 dates
./scan_metadata_dates.py /Volumes/photo-1/2016 --filter-year 2025

# Recursive scan
./scan_metadata_dates.py /Volumes/photo-1 --recursive
```

**What it shows:**
- All EXIF date fields (DateTimeOriginal, DateTimeDigitized, DateTime)
- File system dates (creation, modification)
- Video metadata dates
- Highlights files with mismatched years

### 2. `find_and_rename_by_original_date.py` - Renaming Tool

Finds the TRUE original date and renames files accordingly. **NEVER modifies metadata.**

**Usage:**
```bash
# Dry run (preview changes without making them)
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run

# Actually rename files (with confirmation)
./find_and_rename_by_original_date.py /Volumes/photo-1/2016

# Auto-confirm (no prompt)
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --yes

# Recursive processing
./find_and_rename_by_original_date.py /Volumes/photo-1 --recursive --yes
```

**How it works:**
1. **Reads** metadata without changing it
2. **Prioritizes** dates in this order:
   - DateTimeOriginal (when photo was actually taken) - **PRIMARY**
   - DateTimeDigitized (when digitized/scanned)
   - DateTime (last modification in camera)
   - File system creation date (last resort)
3. **Validates** dates are between 2001-2025
4. **Rejects** placeholder dates (e.g., 2000-01-01)
5. **Renames** files based on the original date found

**Naming format:**
- Photos: `IMG_yyyyMMdd_HHmmss.ext`
- Videos: `MOV_yyyyMMdd_HHmmss.ext`
- With artist: `IMG_yyyyMMdd_HHmmss(NameIdentifier).ext`

**Artist name formatting:**
- "John Bob Photography" → `JBobphotography`
- First word: first letter only (uppercase)
- Second word: whole word capitalized
- Remaining words: lowercase
- Non-alphanumeric removed

### 3. `extract_date_from_filename.py` - Recovery Tool

For files where metadata was already corrupted, this script can extract dates from filenames and optionally restore them to EXIF.

**Usage:**
```bash
# Scan to see what dates can be extracted from filenames
./extract_date_from_filename.py /Volumes/photo-1/2016

# Show all files (including those without dates in filename)
./extract_date_from_filename.py /Volumes/photo-1/2016 --show-all

# Preview metadata updates (dry run)
./extract_date_from_filename.py /Volumes/photo-1/2016 --update --dry-run

# Actually update metadata (USE WITH CAUTION!)
./extract_date_from_filename.py /Volumes/photo-1/2016 --update
```

**⚠️ WARNING**: The `--update` flag will OVERWRITE existing EXIF metadata. Only use this if:
- You're CERTAIN the filename dates are correct
- The metadata is already corrupted beyond repair
- You have a backup

**Supported filename patterns:**
- `IMG_20231225_143052.jpg` (standard format)
- `20231225_143052.jpg` (without prefix)
- `2023-12-25 14-30-52.jpg` (with separators)
- `20231225.jpg` (date only)
- `Screenshot 2023-12-25 at 14.30.52.jpg` (screenshot format)

## Recommended Workflow

### Step 1: Scan for problems
```bash
# Find files with suspicious dates
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious
```

This shows files where the metadata dates don't match, indicating previous corruption.

### Step 2: Preview the fixes
```bash
# See what would be changed (dry run)
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run
```

Review the output to ensure dates look correct.

### Step 3: Apply the fixes
```bash
# Actually rename the files
./find_and_rename_by_original_date.py /Volumes/photo-1/2016
```

Or use `--yes` to skip confirmation.

### Step 4: Verify
```bash
# Scan again to verify dates are consistent
./scan_metadata_dates.py /Volumes/photo-1/2016
```

## Key Differences from Old Scripts

| Old Scripts | New Scripts |
|-------------|-------------|
| ❌ Overwrote DateTimeOriginal | ✅ Never touches metadata |
| ❌ Used arbitrary dates | ✅ Uses actual original dates |
| ❌ Forced dates to match folder name | ✅ Finds true creation date |
| ❌ Could destroy old dates | ✅ Preserves all metadata |
| ❌ Used file modification time | ✅ Prioritizes EXIF DateTimeOriginal |
| ❌ No validation | ✅ Validates 2001-2025 range |

## Important Notes

1. **No Metadata Modification**: These scripts ONLY rename files, they never modify EXIF data
2. **Safe to Run**: Always use `--dry-run` first to preview changes
3. **Handles Duplicates**: Automatically adds counters for duplicate filenames
4. **Artist Names**: Automatically included if present in metadata
5. **Video Support**: Works with photos AND videos

## Dependencies

```bash
# Install required Python packages
pip install Pillow exifread

# Optional but recommended for video metadata
brew install exiftool  # macOS
```

## Examples

### Example 1: Photo with correct metadata
```
Original: DSC_12345.jpg
Metadata DateTimeOriginal: 2018:03:15 14:30:45
Result: IMG_20180315_143045.jpg
```

### Example 2: Photo with artist
```
Original: photo.jpg
Metadata DateTimeOriginal: 2023:12:25 14:30:52
Artist: John Bob Photography
Result: IMG_20231225_143052(JBobphotography).jpg
```

### Example 3: Video file
```
Original: MVI_0001.mov
Video CreateDate: 2022:07:04 10:15:30
Result: MOV_20220704_101530.mov
```

### Example 4: File with corrupted metadata
```
Original: IMG_20251217_120000.jpg (wrong date in filename)
Metadata DateTimeOriginal: 2018:06:10 15:20:30 (true original)
Result: IMG_20180610_152030.jpg (corrected!)
```

## Recovering from Previous Script Damage

If you've already run the old scripts that overwrote metadata, here's a recovery strategy:

### Option 1: Restore from Backup (BEST)
1. Check Time Machine or other backups
2. Restore files from before the metadata was corrupted
3. Run `find_and_rename_by_original_date.py` to rename based on correct metadata

### Option 2: Extract from Filenames (If files were renamed correctly first)
If the files were renamed with the correct date BEFORE metadata was corrupted:

```bash
# Step 1: See what dates can be extracted from current filenames
./extract_date_from_filename.py /Volumes/photo-1/2016 --show-all

# Step 2: Preview metadata restoration
./extract_date_from_filename.py /Volumes/photo-1/2016 --update --dry-run

# Step 3: If dates look correct, apply the update
./extract_date_from_filename.py /Volumes/photo-1/2016 --update
```

### Option 3: Manual Investigation
1. Use `scan_metadata_dates.py --suspicious` to find files with mismatched dates
2. Compare file system dates, metadata dates, and filename dates
3. Determine which is most likely to be correct
4. Use `extract_date_from_filename.py --update` selectively

### Example Recovery Scenario

You have a file named `IMG_20251217_120000.jpg` but you know it was taken in 2018:

```bash
# Step 1: Check all dates
./scan_metadata_dates.py /path/to/file --show-all

# If metadata shows 2016 (corrupted):
# EXIF_DateTimeOriginal: 2016:12:17 12:00:00  ❌ Wrong (overwritten)
# FS_Birthtime: 2018:06:10 15:20:30  ✓ Might be correct
# Filename: IMG_20251217_120000.jpg  ❌ Wrong

# Step 2: Check if there's a backup or compare with similar files
# If you determine the file system date is correct, manually rename:
# mv IMG_20251217_120000.jpg IMG_20180610_152030.jpg

# Step 3: Update metadata from corrected filename
./extract_date_from_filename.py /path/to/file --update
```

## Questions?

- **Q: Will this change my files?**
  - A: Only filenames are changed. Metadata is NEVER modified.

- **Q: What if I'm not sure?**
  - A: Always use `--dry-run` first to preview changes.

- **Q: Can I undo the rename?**
  - A: No automatic undo, but the old filename is shown in the output. Back up first!

- **Q: What about files without EXIF data?**
  - A: Falls back to file system creation date.

- **Q: Why not fix the corrupted metadata?**
  - A: Once DateTimeOriginal is overwritten, the original date is lost unless you have backups.
