#!/usr/bin/env python3
"""
Synology-optimized script to fix file system dates to match EXIF DateTimeOriginal.

Default: Processes /volume1/photo recursively
"""

import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime

def translate_mac_path_to_synology(mac_path):
    """Translate Mac paths to Synology paths."""
    if mac_path.startswith('/Volumes/photo-1/'):
        return mac_path.replace('/Volumes/photo-1/', '/volume1/photo/')
    return mac_path

def get_datetime_original(file_path):
    """Get DateTimeOriginal from file using exiftool."""
    try:
        result = subprocess.run(
            ['exiftool', '-s', '-s', '-s', '-DateTimeOriginal', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            try:
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except:
                pass
    except:
        pass
    return None

def update_filesystem_date(file_path, exif_date, dry_run=False):
    """Update file system modification date to match EXIF date."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    if not exif_date:
        return False, "No EXIF DateTimeOriginal found"
    
    if dry_run:
        return True, f"[DRY RUN] Would set file date to {exif_date.strftime('%Y:%m:%d %H:%M:%S')}"
    
    try:
        # Use exiftool to set file system dates
        date_str = exif_date.strftime("%Y:%m:%d %H:%M:%S")
        
        result = subprocess.run(
            ['exiftool', '-overwrite_original',
             f'-FileModifyDate={date_str}',
             f'-FileCreateDate={date_str}',
             str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, f"✓ Set file date to {date_str}"
        else:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            return False, f"✗ Error: {error_msg}"
            
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix file system dates to match EXIF DateTimeOriginal on Synology'
    )
    parser.add_argument('directory', nargs='?', default='/volume1/photo',
                       help='Directory to process (default: /volume1/photo)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int,
                       help='Limit number of files (for testing)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm without prompting')
    parser.add_argument('--log-file', default='/volume1/photo/logs/filesystem_dates_fix.log',
                       help='Log file for changes')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"SYNOLOGY FIX FILESYSTEM DATES")
    print(f"{'='*80}")
    print(f"Directory: {args.directory}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    if args.limit:
        print(f"Limit: {args.limit} files")
    print(f"Log: {args.log_file}")
    print(f"{'='*80}\n")
    
    # Check exiftool
    try:
        result = subprocess.run(['exiftool', '-ver'], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("❌ ERROR: exiftool not found!")
            print("Install with: opkg install perl-image-exiftool")
            return 1
    except:
        print("❌ ERROR: exiftool not found!")
        print("Install with: opkg install perl-image-exiftool")
        return 1
    
    print("✅ exiftool found\n")
    
    # Find image files
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Directory not found: {args.directory}")
        return 1
    
    image_extensions = ['.jpg', '.jpeg', '.heic', '.png', '.tiff', '.tif', '.JPG', '.JPEG', '.HEIC']
    files = []
    for ext in image_extensions:
        files.extend(directory.rglob(f'*{ext}'))
    
    if not files:
        print(f"❌ No image files found in {args.directory}")
        return 1
    
    print(f"Found {len(files)} image files")
    
    if args.limit:
        files = files[:args.limit]
        print(f"Limited to: {len(files)} files\n")
    
    # Confirm
    if not args.yes and not args.dry_run:
        print(f"\n⚠️  WARNING: This will modify file system dates for {len(files)} files!")
        print(f"Make sure you have backups!")
        response = input(f"\nProceed? Type 'yes' to continue: ").strip().lower()
        if response != 'yes':
            print("Aborted.")
            return 0
    
    # Initialize log
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, 'w', encoding='utf-8')
    log_file.write(f"File System Dates Fix - Started: {datetime.now().isoformat()}\n")
    log_file.write("="*80 + "\n\n")
    
    # Process files
    print(f"\n{'='*80}")
    print(f"Processing files...")
    print(f"{'='*80}\n")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for idx, file_path in enumerate(files, 1):
        exif_date = get_datetime_original(file_path)
        
        if not exif_date:
            skipped_count += 1
            continue
        
        success, message = update_filesystem_date(file_path, exif_date, dry_run=args.dry_run)
        
        if success:
            log_file.write(f"{file_path}: {message}\n")
            if idx <= 20 or idx % 100 == 0:
                print(f"[{idx}/{len(files)}] {message}")
            success_count += 1
        else:
            log_file.write(f"{file_path}: {message}\n")
            if error_count < 10:  # Show first 10 errors
                print(f"[{idx}/{len(files)}] {message}")
            error_count += 1
        
        if idx % 100 == 0:
            log_file.flush()
            print(f"  → Progress: {idx}/{len(files)} (Updated: {success_count}, Skipped: {skipped_count})")
    
    log_file.write("\n" + "="*80 + "\n")
    log_file.write(f"File System Dates Fix - Ended: {datetime.now().isoformat()}\n")
    log_file.write(f"Total: {len(files)}, Updated: {success_count}, Errors: {error_count}, Skipped: {skipped_count}\n")
    log_file.close()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total files: {len(files)}")
    print(f"Updated: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped (no EXIF): {skipped_count}")
    
    if args.dry_run:
        print(f"\n⚠️  DRY RUN - No files modified")
    else:
        print(f"\n✅ File system dates updated!")
        print(f"   Log: {args.log_file}")
        print(f"   Next step: Re-index Synology Photos (Settings → Rebuild Index)")
    
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
