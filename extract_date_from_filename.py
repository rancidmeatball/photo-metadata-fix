#!/usr/bin/env python3
"""
Extract dates from filenames when EXIF metadata has been corrupted.
Useful for files that were already renamed with dates in their names.
"""

import re
import sys
from pathlib import Path
from datetime import datetime

def extract_date_from_filename(filename):
    """
    Try to extract date from various filename patterns.
    Returns: (datetime_object, pattern_matched) or (None, None)
    """
    
    # Pattern 1: IMG_yyyyMMdd_HHmmss or MOV_yyyyMMdd_HHmmss
    pattern1 = r'(?:IMG|MOV)_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
    match = re.search(pattern1, filename, re.IGNORECASE)
    if match:
        try:
            year, month, day, hour, minute, second = map(int, match.groups())
            dt = datetime(year, month, day, hour, minute, second)
            if 2001 <= dt.year <= 2025:
                return dt, 'IMG/MOV_yyyyMMdd_HHmmss'
        except ValueError:
            pass
    
    # Pattern 2: yyyyMMdd_HHmmss (without prefix)
    pattern2 = r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
    match = re.search(pattern2, filename)
    if match:
        try:
            year, month, day, hour, minute, second = map(int, match.groups())
            dt = datetime(year, month, day, hour, minute, second)
            if 2001 <= dt.year <= 2025:
                return dt, 'yyyyMMdd_HHmmss'
        except ValueError:
            pass
    
    # Pattern 3: yyyy-MM-dd HH-mm-ss or yyyy_MM_dd HH_mm_ss
    pattern3 = r'(\d{4})[-_](\d{2})[-_](\d{2})[\s_-](\d{2})[-_](\d{2})[-_](\d{2})'
    match = re.search(pattern3, filename)
    if match:
        try:
            year, month, day, hour, minute, second = map(int, match.groups())
            dt = datetime(year, month, day, hour, minute, second)
            if 2001 <= dt.year <= 2025:
                return dt, 'yyyy-MM-dd HH-mm-ss'
        except ValueError:
            pass
    
    # Pattern 4: yyyyMMdd (date only, no time)
    pattern4 = r'(\d{4})(\d{2})(\d{2})'
    match = re.search(pattern4, filename)
    if match:
        try:
            year, month, day = map(int, match.groups())
            dt = datetime(year, month, day, 12, 0, 0)  # Default to noon
            if 2001 <= dt.year <= 2025:
                return dt, 'yyyyMMdd'
        except ValueError:
            pass
    
    # Pattern 5: yyyy-MM-dd or yyyy_MM_dd (date only)
    pattern5 = r'(\d{4})[-_](\d{2})[-_](\d{2})'
    match = re.search(pattern5, filename)
    if match:
        try:
            year, month, day = map(int, match.groups())
            dt = datetime(year, month, day, 12, 0, 0)  # Default to noon
            if 2001 <= dt.year <= 2025:
                return dt, 'yyyy-MM-dd'
        except ValueError:
            pass
    
    # Pattern 6: Screenshot patterns (Screenshot YYYY-MM-DD at HH.MM.SS)
    pattern6 = r'screenshot[\s_-](\d{4})[-_](\d{2})[-_](\d{2})[\s_-]at[\s_-](\d{1,2})[.\-_](\d{2})[.\-_](\d{2})'
    match = re.search(pattern6, filename, re.IGNORECASE)
    if match:
        try:
            year, month, day, hour, minute, second = map(int, match.groups())
            dt = datetime(year, month, day, hour, minute, second)
            if 2001 <= dt.year <= 2025:
                return dt, 'Screenshot pattern'
        except ValueError:
            pass
    
    # Pattern 7: Just year somewhere in filename (very loose, use with caution)
    pattern7 = r'(20[0-2][0-9])'
    match = re.search(pattern7, filename)
    if match:
        try:
            year = int(match.group(1))
            if 2001 <= year <= 2025:
                dt = datetime(year, 1, 1, 12, 0, 0)  # Default to Jan 1, noon
                return dt, 'Year only (approximate)'
        except ValueError:
            pass
    
    return None, None

def scan_directory(directory, show_all=False):
    """Scan directory and show what dates can be extracted from filenames."""
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    all_extensions = image_extensions | video_extensions
    
    files = [f for f in directory.iterdir() 
            if f.is_file() and f.suffix.lower() in all_extensions]
    
    if not files:
        print(f"No media files found in {directory}")
        return
    
    print(f"{'='*80}")
    print(f"Scanning {len(files)} file(s) for dates in filenames...")
    print(f"{'='*80}\n")
    
    found_count = 0
    not_found_count = 0
    
    for file_path in sorted(files):
        date_obj, pattern = extract_date_from_filename(file_path.name)
        
        if date_obj:
            found_count += 1
            date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            print(f"✓ {file_path.name}")
            print(f"  → Date: {date_str} (pattern: {pattern})")
            print()
        elif show_all:
            not_found_count += 1
            print(f"✗ {file_path.name}")
            print(f"  → No date pattern found")
            print()
    
    print(f"{'='*80}")
    print(f"Summary:")
    print(f"  Files with dates in filename: {found_count}")
    print(f"  Files without dates: {not_found_count}")
    print(f"  Total: {len(files)}")
    print(f"{'='*80}")

def update_metadata_from_filename(file_path, dry_run=True):
    """
    Update EXIF metadata based on date extracted from filename.
    Use ONLY when you're sure the filename date is correct!
    """
    from PIL import Image
    
    date_obj, pattern = extract_date_from_filename(file_path.name)
    
    if not date_obj:
        return False, "No date found in filename"
    
    if dry_run:
        return True, f"Would update to: {date_obj.strftime('%Y-%m-%d %H:%M:%S')} (pattern: {pattern})"
    
    # Actually update the EXIF
    ext = file_path.suffix.lower()
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    
    if ext not in image_extensions:
        return False, "Not a supported image format for EXIF update"
    
    try:
        date_str = date_obj.strftime("%Y:%m:%d %H:%M:%S")
        
        img = Image.open(file_path)
        exif_dict = img.getexif()
        
        # Update date fields
        exif_dict[306] = date_str  # DateTime
        exif_dict[36867] = date_str  # DateTimeOriginal
        exif_dict[36868] = date_str  # DateTimeDigitized
        
        # Save with updated EXIF
        img.save(file_path, exif=exif_dict)
        return True, f"Updated to: {date_str}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract dates from filenames and optionally update EXIF metadata'
    )
    parser.add_argument('directory', nargs='?', default=None,
                       help='Directory to process (default: current directory)')
    parser.add_argument('--update', action='store_true',
                       help='Update EXIF metadata based on filename dates (USE WITH CAUTION!)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without actually changing files')
    parser.add_argument('--show-all', action='store_true',
                       help='Show all files, including those without dates in filename')
    
    args = parser.parse_args()
    
    # Determine directory
    if args.directory:
        source_dir = Path(args.directory).expanduser().resolve()
    else:
        source_dir = Path.cwd()
    
    if not source_dir.exists():
        print(f"Error: Directory {source_dir} does not exist!")
        return 1
    
    if not source_dir.is_dir():
        print(f"Error: {source_dir} is not a directory!")
        return 1
    
    print(f"{'='*80}")
    print(f"FILENAME DATE EXTRACTOR")
    print(f"{'='*80}")
    print(f"Directory: {source_dir}")
    
    if args.update:
        if args.dry_run:
            print(f"Mode: DRY RUN - Preview metadata updates")
        else:
            print(f"Mode: LIVE - Will update EXIF metadata")
            print(f"\n⚠️  WARNING: This will OVERWRITE existing EXIF dates!")
            print(f"⚠️  Only use this if you're SURE the filename dates are correct!")
            print(f"⚠️  Consider making a backup first!")
            
            response = input("\nAre you ABSOLUTELY sure you want to proceed? (type 'yes' to continue): ").strip()
            if response != 'yes':
                print("Aborted.")
                return 0
    else:
        print(f"Mode: SCAN ONLY - No changes will be made")
    
    print(f"{'='*80}\n")
    
    if not args.update:
        # Just scan and show what dates can be extracted
        scan_directory(source_dir, show_all=args.show_all)
    else:
        # Update metadata based on filenames
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                           '.gif', '.bmp', '.webp'}
        
        files = [f for f in source_dir.iterdir() 
                if f.is_file() and f.suffix.lower() in image_extensions]
        
        if not files:
            print(f"No image files found in {source_dir}")
            return 0
        
        print(f"Processing {len(files)} file(s)...\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for idx, file_path in enumerate(files, 1):
            success, message = update_metadata_from_filename(file_path, dry_run=args.dry_run)
            
            if success:
                print(f"[{idx}/{len(files)}] ✓ {file_path.name}")
                print(f"            {message}")
                success_count += 1
            else:
                if "No date found" in message:
                    print(f"[{idx}/{len(files)}] - {file_path.name}")
                    print(f"            {message}")
                    skip_count += 1
                else:
                    print(f"[{idx}/{len(files)}] ✗ {file_path.name}")
                    print(f"            {message}")
                    error_count += 1
        
        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Successful: {success_count}")
        print(f"  Skipped (no date): {skip_count}")
        print(f"  Errors: {error_count}")
        if args.dry_run:
            print(f"\n⚠ DRY RUN MODE - No files were actually modified")
            print(f"Run with --update (without --dry-run) to apply changes")
        print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
