╔══════════════════════════════════════════════════════════════════════════════╗
║                     ⚠️  OLD/DANGEROUS FILES - QUARANTINED                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

This directory contains OLD and DANGEROUS scripts that have been moved here
to prevent accidental use during recovery.

═══════════════════════════════════════════════════════════════════════════════

DANGEROUS SCRIPTS (DO NOT USE!)
═══════════════════════════════════════════════════════════════════════════════

❌ -dangerous!-fix_2025_files.py
   • Overwrites EXIF DateTimeOriginal with arbitrary dates
   • Forces files to have incorrect dates
   • Destroys original creation dates

❌ -dangerous!-update_and_rename.py
   • Overwrites all EXIF date fields
   • Uses arbitrary dates
   • No validation

❌ -dangerous!-fix_metadata.py
   • Can overwrite metadata
   • Interactive but still risky
   • Better alternatives exist

═══════════════════════════════════════════════════════════════════════════════

OLD CHECKPOINT FILES (Backed Up)
═══════════════════════════════════════════════════════════════════════════════

These are checkpoint files from previous rename operations.
Kept for reference and potential data recovery.

• old-checkpoint-photo1.json (7.7 MB)
  - From /Volumes/photo-1/rename_photos_checkpoint.json
  - Original rename operation checkpoint

• old-checkpoint-recycle.json (79 KB)
  - From /Volumes/photo-1/#recycle/rename_photos_checkpoint.json
  - Recycle bin operation checkpoint

• old-checkpoint-metadata.json (128 B)
  - From /Volumes/photo-1/#recycle/metadata/checkpoint.json
  - Metadata operation checkpoint

═══════════════════════════════════════════════════════════════════════════════

USE THESE INSTEAD (Safe Scripts)
═══════════════════════════════════════════════════════════════════════════════

✅ synology_rename_photos_with_checkpoint.py
   • WITH checkpoint/resume support
   • NEVER modifies metadata
   • Safe for production use

✅ find_and_rename_with_checkpoint.py
   • macOS/Linux version with checkpoints
   • NEVER modifies metadata
   • Safe for production use

✅ scan_metadata_dates.py
   • Diagnostic tool
   • Read-only
   • Identifies problems

✅ capture_current_state.py
   • Records current state
   • Essential for recovery
   • Creates backup snapshots

═══════════════════════════════════════════════════════════════════════════════

WHY THESE ARE DANGEROUS
═══════════════════════════════════════════════════════════════════════════════

Problem: DateTimeOriginal is PRECIOUS
• It records when the photo was actually taken
• Once overwritten, it's gone forever (unless you have backups)
• The dangerous scripts overwrite it with made-up dates

Example of Damage:
  Before:  Photo taken June 10, 2018
           EXIF DateTimeOriginal: 2018:06:10 15:20:30 ✓
  
  After running dangerous script:
           EXIF DateTimeOriginal: 2016:12:17 12:00:00 ✗
           
  Result:  Original date DESTROYED!

═══════════════════════════════════════════════════════════════════════════════

IF YOU ACCIDENTALLY RUN A DANGEROUS SCRIPT
═══════════════════════════════════════════════════════════════════════════════

STOP IMMEDIATELY!

1. Press Ctrl+C to kill the script
2. Check what files were changed (check logs)
3. Restore from backup if you have one
4. Use recovery tools:
   • capture_current_state.py - snapshot current state
   • Check file birthtime (likely still correct)
   • Check directory structure (files in 2018/ are from 2018)
   • Use RECOVERY/ database to find original names

═══════════════════════════════════════════════════════════════════════════════

DO NOT DELETE THIS DIRECTORY
═══════════════════════════════════════════════════════════════════════════════

Keep these files for:
• Reference (to understand what went wrong)
• Old checkpoints (may contain useful data)
• Historical record

But NEVER use the dangerous scripts again!

═══════════════════════════════════════════════════════════════════════════════

Questions? Read:
• CHECKPOINT_AND_BACKGROUND_GUIDE.md
• RECOVERY_GUIDE.md
• COMPLETE_SOLUTION_SUMMARY.md

═══════════════════════════════════════════════════════════════════════════════
