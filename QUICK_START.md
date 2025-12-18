# Quick Start Guide

## Install Dependencies

```bash
pip install Pillow exifread
brew install exiftool  # Optional but recommended for videos
```

## Common Tasks

### 1. Find Files with Wrong Dates

```bash
# Show files with suspicious/mismatched dates
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious
```

### 2. Rename Files Based on Original Metadata

```bash
# Preview what will happen (safe, no changes)
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run

# Actually rename the files
./find_and_rename_by_original_date.py /Volumes/photo-1/2016

# Process entire drive recursively
./find_and_rename_by_original_date.py /Volumes/photo-1 --recursive --yes
```

### 3. Check What Dates Are in Files

```bash
# Scan a directory
./scan_metadata_dates.py /Volumes/photo-1/2016

# Show only files with 2025 dates
./scan_metadata_dates.py /Volumes/photo-1/2016 --filter-year 2025

# Show only files with 2018 dates
./scan_metadata_dates.py /Volumes/photo-1/2016 --filter-year 2018
```

### 4. Recover Corrupted Metadata (Advanced)

```bash
# See what dates are in filenames
./extract_date_from_filename.py /Volumes/photo-1/2016 --show-all

# Preview metadata restoration from filenames
./extract_date_from_filename.py /Volumes/photo-1/2016 --update --dry-run

# Actually restore metadata (USE WITH CAUTION - have backups!)
./extract_date_from_filename.py /Volumes/photo-1/2016 --update
```

## Typical Workflow

```bash
# 1. Identify the problem
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious

# 2. Preview the fix
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run

# 3. Apply the fix
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --yes

# 4. Verify results
./scan_metadata_dates.py /Volumes/photo-1/2016
```

## Safety Tips

1. ✅ **Always use `--dry-run` first** to preview changes
2. ✅ **Make backups** before modifying anything
3. ✅ **Start with a small test directory** to verify behavior
4. ⚠️ **Never use `--update`** on `extract_date_from_filename.py` unless you're certain
5. ⚠️ **The old scripts (`fix_2025_files.py`, etc.) are DANGEROUS** - they overwrite metadata

## What Each Script Does

| Script | Purpose | Safe? |
|--------|---------|-------|
| `scan_metadata_dates.py` | Show all dates in files | ✅ Read-only |
| `find_and_rename_by_original_date.py` | Rename based on original dates | ✅ Only renames, doesn't modify metadata |
| `extract_date_from_filename.py` | Extract dates from filenames | ✅ Read-only (unless --update) |
| `extract_date_from_filename.py --update` | Restore metadata from filenames | ⚠️ Overwrites metadata |
| ~~`fix_2025_files.py`~~ | OLD - Corrupts metadata | ❌ DO NOT USE |
| ~~`update_and_rename.py`~~ | OLD - Corrupts metadata | ❌ DO NOT USE |

## Examples

### Example 1: Fix files in 2016 folder that were mislabeled

```bash
# Check what's wrong
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious

# Preview fix
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run

# Apply fix
./find_and_rename_by_original_date.py /Volumes/photo-1/2016
```

### Example 2: Process all photos on a drive

```bash
# Dry run on entire drive
./find_and_rename_by_original_date.py /Volumes/photo-1 --recursive --dry-run

# If looks good, apply
./find_and_rename_by_original_date.py /Volumes/photo-1 --recursive --yes
```

### Example 3: Find all files with 2025 dates (likely corrupted)

```bash
./scan_metadata_dates.py /Volumes/photo-1 --recursive --filter-year 2025
```

## Help

```bash
# Get help for any script
./scan_metadata_dates.py --help
./find_and_rename_by_original_date.py --help
./extract_date_from_filename.py --help
```
