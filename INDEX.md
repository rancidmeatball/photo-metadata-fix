# Metadata Fix Tools - File Index

## ✅ Safe Scripts (Use These)

### `synology_rename_photos.py` ⭐ SYNOLOGY VERSION (NEW!)
**Purpose**: Synology-optimized version - defaults to `/volume1/photo` recursive

**Safe**: ✅ Yes - Only renames files, NEVER modifies metadata

**Usage**:
```bash
# On Synology NAS (defaults to /volume1/photo, recursive)
./synology_rename_photos.py --dry-run
./synology_rename_photos.py --yes
```

**When to use**: Running on Synology NAS to batch process your entire photo library

**Setup**: See `SYNOLOGY_SETUP.md` for installation instructions

---

### `find_and_rename_by_original_date.py` ⭐ PRIMARY TOOL (macOS/Linux)
**Purpose**: Rename files based on their TRUE original creation date from metadata

**Safe**: ✅ Yes - Only renames files, NEVER modifies metadata

**Usage**:
```bash
./find_and_rename_by_original_date.py /path/to/photos --dry-run
./find_and_rename_by_original_date.py /path/to/photos
```

**When to use**: This is your main tool for correctly naming photos based on when they were actually taken.

---

### `scan_metadata_dates.py` ⭐ DIAGNOSTIC TOOL
**Purpose**: Scan files and show all dates in their metadata

**Safe**: ✅ Yes - Read-only, shows information

**Usage**:
```bash
./scan_metadata_dates.py /path/to/photos --suspicious
./scan_metadata_dates.py /path/to/photos --filter-year 2025
```

**When to use**: 
- Before running other scripts to see what dates exist
- To identify files with corrupted/mismatched dates
- To verify results after renaming

---

### `extract_date_from_filename.py` - RECOVERY TOOL
**Purpose**: Extract dates from filenames and optionally restore to EXIF

**Safe**: ⚠️ Conditionally
- Without `--update`: ✅ Safe (read-only)
- With `--update`: ⚠️ Overwrites metadata (use with caution)

**Usage**:
```bash
# Safe: just scan
./extract_date_from_filename.py /path/to/photos

# Caution: modifies metadata
./extract_date_from_filename.py /path/to/photos --update --dry-run
./extract_date_from_filename.py /path/to/photos --update
```

**When to use**:
- When metadata is already corrupted beyond repair
- When filenames have correct dates but EXIF doesn't
- As a last resort recovery option

---

## ❌ Dangerous Scripts (DO NOT USE)

### `fix_2025_files.py` ⛔ DANGEROUS
**Purpose**: (Original intent) Fix files with 2025 in name in 2016 folder

**Safe**: ❌ NO - Overwrites DateTimeOriginal with arbitrary dates

**Problem**: 
- Forces all files to December 17, 2016 regardless of true date
- Destroys original creation dates
- Makes up dates instead of reading real metadata

**Status**: ⛔ **DO NOT USE** - Kept for reference only

---

### `update_and_rename.py` ⛔ DANGEROUS
**Purpose**: (Original intent) Update files in fixed_metadata folder

**Safe**: ❌ NO - Overwrites all EXIF dates with arbitrary dates

**Problem**:
- Forces specific date (December 17, 2016)
- Destroys DateTimeOriginal
- No validation of existing dates

**Status**: ⛔ **DO NOT USE** - Kept for reference only

---

### `fix_metadata.py` ⚠️ PROBLEMATIC
**Purpose**: Analyze and update metadata interactively

**Safe**: ⚠️ Partially - Allows user to choose dates but still overwrites metadata

**Problem**:
- Still overwrites EXIF data (though with user choice)
- Could accidentally destroy original dates
- Better to just rename files, not modify metadata

**Status**: ⚠️ **Use with caution** - Prefer `find_and_rename_by_original_date.py` instead

---

## 📄 Documentation Files

### `README.md` - Full Documentation
Complete guide covering:
- Problem explanation
- All scripts and their usage
- Recovery strategies
- Examples

### `QUICK_START.md` - Quick Reference
Fast reference for common commands and workflows

### `PROBLEM_AND_SOLUTION.md` - Detailed Explanation
In-depth explanation of:
- What went wrong
- Why it happened
- How to fix it
- Technical details

### `INDEX.md` - This File
Overview of all files in the project

---

## Workflow Summary

```
┌─────────────────────────────────────┐
│  1. Diagnose                        │
│  ./scan_metadata_dates.py           │
│  --suspicious                       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  2. Preview Fix                     │
│  ./find_and_rename_by_original_date │
│  --dry-run                          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  3. Apply Fix                       │
│  ./find_and_rename_by_original_date │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  4. Verify                          │
│  ./scan_metadata_dates.py           │
└─────────────────────────────────────┘
```

---

## Quick Command Reference

```bash
# Most common workflow
cd /Users/john/Cursor/fix_metadata

# 1. Check what's wrong
./scan_metadata_dates.py /Volumes/photo-1/2016 --suspicious

# 2. Preview fix
./find_and_rename_by_original_date.py /Volumes/photo-1/2016 --dry-run

# 3. Apply fix
./find_and_rename_by_original_date.py /Volumes/photo-1/2016

# 4. Verify
./scan_metadata_dates.py /Volumes/photo-1/2016
```

---

## File Status Summary

| File | Type | Safe? | Use? |
|------|------|-------|------|
| `synology_rename_photos.py` | Tool | ✅ Yes | ⭐ SYNOLOGY |
| `find_and_rename_by_original_date.py` | Tool | ✅ Yes | ⭐ PRIMARY |
| `scan_metadata_dates.py` | Tool | ✅ Yes | ⭐ DIAGNOSTIC |
| `extract_date_from_filename.py` | Tool | ⚠️ Conditional | Recovery only |
| `fix_2025_files.py` | Tool | ❌ NO | ⛔ NEVER |
| `update_and_rename.py` | Tool | ❌ NO | ⛔ NEVER |
| `fix_metadata.py` | Tool | ⚠️ Risky | Avoid |
| `README.md` | Docs | - | Read first |
| `SYNOLOGY_SETUP.md` | Docs | - | Synology guide |
| `SYNOLOGY_QUICK_REF.txt` | Docs | - | Quick ref card |
| `QUICK_START.md` | Docs | - | Quick ref |
| `PROBLEM_AND_SOLUTION.md` | Docs | - | Detailed guide |
| `INDEX.md` | Docs | - | This file |

---

## Need Help?

1. **Read the docs**: Start with `README.md`
2. **Quick reference**: Check `QUICK_START.md`
3. **Understand the problem**: Read `PROBLEM_AND_SOLUTION.md`
4. **Get command help**: Run any script with `--help`
5. **Always test first**: Use `--dry-run` before making changes

---

## Remember

🎯 **Goal**: Rename files based on their TRUE original creation date

✅ **Safe approach**: Read metadata → Validate → Rename file

❌ **Wrong approach**: Make up date → Overwrite metadata → Rename

💡 **Key principle**: Metadata is precious. Never overwrite DateTimeOriginal!
