#!/usr/bin/env python3
"""
Synology-optimized script to rename photos based on original metadata dates.
Default: Processes /volume1/photo recursively
NEVER modifies metadata - only renames files based on existing dates.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Try to import PIL and exifread, provide helpful error if missing
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("ERROR: PIL (Pillow) not installed!")
    print("Install with: python3 -m pip install Pillow")
    sys.exit(1)

try:
    import exifread
except ImportError:
    print("ERROR: exifread not installed!")
    print("Install with: python3 -m pip install exifread")
    sys.exit(1)

def get_best_date_from_exif(image_path):
    """
    Extract the BEST original date from EXIF metadata.
    Priority: DateTimeOriginal > DateTimeDigitized > DateTime
    Returns: (datetime_object, source_name) or (None, None)
    """
    dates_found = {}
    
    # Method 1: Using PIL/Pillow
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            if exifdata:
                # Tag IDs for dates:
                # 36867 = DateTimeOriginal (when photo was taken)
                # 36868 = DateTimeDigitized (when digitized)
                # 306 = DateTime (last modification)
                
                if 36867 in exifdata and exifdata[36867]:
                    dates_found['DateTimeOriginal'] = str(exifdata[36867])
                if 36868 in exifdata and exifdata[36868]:
                    dates_found['DateTimeDigitized'] = str(exifdata[36868])
                if 306 in exifdata and exifdata[306]:
                    dates_found['DateTime'] = str(exifdata[306])
    except Exception as e:
        pass
    
    # Method 2: Using exifread (backup method)
    if not dates_found:
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                
                if 'EXIF DateTimeOriginal' in tags:
                    dates_found['DateTimeOriginal'] = str(tags['EXIF DateTimeOriginal'])
                if 'EXIF DateTimeDigitized' in tags:
                    dates_found['DateTimeDigitized'] = str(tags['EXIF DateTimeDigitized'])
                if 'Image DateTime' in tags:
                    dates_found['DateTime'] = str(tags['Image DateTime'])
        except Exception as e:
            pass
    
    # Parse and validate dates in priority order
    priority_order = ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']
    
    for date_type in priority_order:
        if date_type in dates_found:
            parsed_date = parse_exif_date(dates_found[date_type])
            if parsed_date and is_valid_date(parsed_date):
                return parsed_date, date_type
    
    return None, None

def get_artist_from_exif(image_path):
    """Extract artist/photographer name from EXIF metadata."""
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            if exifdata:
                # Tag ID 315 = Artist
                if 315 in exifdata and exifdata[315]:
                    return str(exifdata[315]).strip()
    except Exception as e:
        pass
    
    # Backup method with exifread
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            if 'Image Artist' in tags:
                return str(tags['Image Artist']).strip()
    except Exception as e:
        pass
    
    return None

def get_video_creation_date(video_path):
    """
    Get creation date from video file using exiftool.
    Returns: (datetime_object, source_name) or (None, None)
    """
    # Try exiftool (if available)
    try:
        result = subprocess.run(
            ['exiftool', '-CreateDate', '-DateTimeOriginal', '-MediaCreateDate', 
             '-CreationDate', '-TrackCreateDate', '-s', '-s', '-s', str(video_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line:
                    parsed_date = parse_exif_date(line.strip())
                    if parsed_date and is_valid_date(parsed_date):
                        return parsed_date, 'Video CreateDate'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None, None

def parse_exif_date(date_str):
    """Parse EXIF date string to datetime object."""
    if not date_str or date_str.lower() == 'none':
        return None
    
    # Common EXIF formats
    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y:%m:%d",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    
    return None

def is_valid_date(date_obj):
    """Check if date is within valid range (2001-2025) and not a placeholder."""
    if not date_obj:
        return False
    
    # Check year range
    if date_obj.year < 2001 or date_obj.year > 2025:
        return False
    
    # Check for common placeholder dates
    if date_obj.year == 2000 and date_obj.month == 1 and date_obj.day == 1:
        return False
    
    return True

def get_file_creation_date(file_path):
    """Get file system creation date as last resort."""
    try:
        stat = os.stat(file_path)
        
        # Try birthtime first (if available)
        if hasattr(stat, 'st_birthtime'):
            date_obj = datetime.fromtimestamp(stat.st_birthtime)
            if is_valid_date(date_obj):
                return date_obj, 'File Creation Date (birthtime)'
        
        # Fallback to modification time
        date_obj = datetime.fromtimestamp(stat.st_mtime)
        if is_valid_date(date_obj):
            return date_obj, 'File Modification Date'
    except Exception as e:
        pass
    
    return None, None

def format_artist_name(artist_name):
    """
    Format artist name according to specification:
    - First word: First letter only (uppercase)
    - Second word: Whole word with capitalized first letter
    - Remaining words: Whole word (lowercase)
    - Remove non-alphanumeric characters
    """
    if not artist_name:
        return None
    
    # Remove non-alphanumeric characters (except spaces)
    import re
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', artist_name)
    
    # Split into words
    words = cleaned.split()
    if not words:
        return None
    
    if len(words) == 1:
        # Single word: capitalize first letter
        return words[0][0].upper() + words[0][1:].lower() if len(words[0]) > 1 else words[0].upper()
    
    # Format according to rules
    formatted_parts = []
    
    # First word: first letter only (uppercase)
    formatted_parts.append(words[0][0].upper())
    
    # Second word: whole word with capitalized first letter
    formatted_parts.append(words[1][0].upper() + words[1][1:].lower() if len(words[1]) > 1 else words[1].upper())
    
    # Remaining words: whole word (lowercase)
    for word in words[2:]:
        formatted_parts.append(word.lower())
    
    return ''.join(formatted_parts)

def generate_new_filename(file_path, date_obj, artist_name=None):
    """
    Generate new filename according to specification:
    - Photos: IMG_yyyyMMdd_HHmmss.ext or IMG_yyyyMMdd_HHmmss(NameIdentifier).ext
    - Videos: MOV_yyyyMMdd_HHmmss.ext or MOV_yyyyMMdd_HHmmss(NameIdentifier).ext
    """
    ext = file_path.suffix.lower()
    
    # Determine prefix
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    prefix = 'MOV' if ext in video_extensions else 'IMG'
    
    # Format date part
    date_part = date_obj.strftime('%Y%m%d_%H%M%S')
    
    # Format artist part if present
    if artist_name:
        formatted_artist = format_artist_name(artist_name)
        if formatted_artist:
            new_name = f"{prefix}_{date_part}({formatted_artist}){file_path.suffix}"
        else:
            new_name = f"{prefix}_{date_part}{file_path.suffix}"
    else:
        new_name = f"{prefix}_{date_part}{file_path.suffix}"
    
    return new_name

def rename_file(file_path, new_filename):
    """Rename file, handling duplicates by adding counter."""
    new_path = file_path.parent / new_filename
    
    # Handle duplicates
    counter = 1
    while new_path.exists() and new_path != file_path:
        name_parts = new_filename.rsplit('.', 1)
        if len(name_parts) == 2:
            # Has extension
            base_name, ext = name_parts
            # Check if there's an artist name in parentheses
            if ')' in base_name:
                # Insert counter before the artist name
                parts = base_name.split('(')
                new_filename = f"{parts[0]}_{counter:02d}({parts[1]}.{ext}"
            else:
                new_filename = f"{base_name}_{counter:02d}.{ext}"
        else:
            # No extension
            new_filename = f"{new_filename}_{counter:02d}"
        
        new_path = file_path.parent / new_filename
        counter += 1
    
    try:
        file_path.rename(new_path)
        return True, new_path
    except Exception as e:
        return False, str(e)

def process_file(file_path, dry_run=False):
    """
    Process a single file: find original date and rename.
    Returns: (success, old_name, new_name, date_found, date_source, artist)
    """
    ext = file_path.suffix.lower()
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    
    date_obj = None
    date_source = None
    artist = None
    
    # Try to get date from metadata
    if ext in image_extensions:
        date_obj, date_source = get_best_date_from_exif(file_path)
        artist = get_artist_from_exif(file_path)
    elif ext in video_extensions:
        date_obj, date_source = get_video_creation_date(file_path)
    
    # Fallback to file creation date if no metadata date found
    if not date_obj:
        date_obj, date_source = get_file_creation_date(file_path)
    
    if not date_obj:
        return False, file_path.name, None, None, "No valid date found", None
    
    # Generate new filename
    new_filename = generate_new_filename(file_path, date_obj, artist)
    
    # Check if already correctly named
    if file_path.name == new_filename:
        return True, file_path.name, file_path.name, date_obj, date_source, artist
    
    # Rename file (unless dry run)
    if not dry_run:
        success, result = rename_file(file_path, new_filename)
        if success:
            return True, file_path.name, result.name, date_obj, date_source, artist
        else:
            return False, file_path.name, None, date_obj, date_source, f"Error: {result}"
    else:
        return True, file_path.name, new_filename, date_obj, date_source, artist

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Synology photo renamer - Default: /volume1/photo recursive'
    )
    parser.add_argument('directory', nargs='?', default='/volume1/photo',
                       help='Directory to process (default: /volume1/photo)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be done without actually renaming files')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do NOT process subdirectories (default is recursive)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm without prompting')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output (only show summary)')
    
    args = parser.parse_args()
    
    # Determine directory
    source_dir = Path(args.directory).resolve()
    
    if not source_dir.exists():
        print(f"ERROR: Directory {source_dir} does not exist!")
        return 1
    
    if not source_dir.is_dir():
        print(f"ERROR: {source_dir} is not a directory!")
        return 1
    
    recursive = not args.no_recursive
    
    if not args.quiet:
        print(f"{'='*80}")
        print(f"SYNOLOGY PHOTO RENAMER")
        print(f"{'='*80}")
        print(f"Directory: {source_dir}")
        print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE (will rename)'}")
        print(f"Recursive: {'Yes' if recursive else 'No'}")
        print(f"\nThis script will:")
        print(f"  1. Find TRUE original date from metadata")
        print(f"  2. Prioritize: DateTimeOriginal > DateTimeDigitized > DateTime")
        print(f"  3. Only use dates between 2001-2025")
        print(f"  4. NEVER modify metadata")
        print(f"  5. Rename files based on original date")
        print(f"{'='*80}\n")
    
    # Find all media files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    all_extensions = image_extensions | video_extensions
    
    if not args.quiet:
        print("Scanning for files...")
    
    if recursive:
        files = [f for f in source_dir.rglob('*') 
                if f.is_file() and f.suffix.lower() in all_extensions]
    else:
        files = [f for f in source_dir.iterdir() 
                if f.is_file() and f.suffix.lower() in all_extensions]
    
    if not files:
        print(f"No image or video files found in {source_dir}")
        return 0
    
    if not args.quiet:
        print(f"Found {len(files)} file(s) to process\n")
        
        # Show sample
        if len(files) <= 20:
            print("Files to process:")
            for f in files:
                print(f"  - {f.relative_to(source_dir)}")
        else:
            print("Sample of files to process:")
            for f in files[:10]:
                print(f"  - {f.relative_to(source_dir)}")
            print(f"  ... and {len(files) - 10} more files")
        
        print()
    
    # Confirm unless auto-confirmed or dry run
    if not args.yes and not args.dry_run:
        response = input(f"Process {len(files)} files? (y/n): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return 0
    
    # Process files
    if not args.quiet:
        print(f"\n{'='*80}")
        print("Processing files...")
        print(f"{'='*80}\n")
    
    success_count = 0
    already_named_count = 0
    error_count = 0
    errors = []
    
    for idx, file_path in enumerate(files, 1):
        success, old_name, new_name, date_obj, date_source, artist_or_error = process_file(
            file_path, dry_run=args.dry_run
        )
        
        if not args.quiet:
            if success:
                if old_name == new_name:
                    print(f"[{idx}/{len(files)}] ✓ Already correctly named: {old_name}")
                    already_named_count += 1
                else:
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S') if date_obj else 'N/A'
                    artist_str = f" | Artist: {artist_or_error}" if artist_or_error else ""
                    print(f"[{idx}/{len(files)}] ✓ {old_name}")
                    print(f"               → {new_name}")
                    print(f"               Date: {date_str} (from {date_source}){artist_str}")
                    success_count += 1
            else:
                print(f"[{idx}/{len(files)}] ✗ Error: {old_name}")
                print(f"               {artist_or_error}")
                error_count += 1
                errors.append((old_name, artist_or_error))
        else:
            # Quiet mode - just count
            if success:
                if old_name == new_name:
                    already_named_count += 1
                else:
                    success_count += 1
            else:
                error_count += 1
                errors.append((old_name, artist_or_error))
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total files: {len(files)}")
    print(f"Successfully renamed: {success_count}")
    print(f"Already correctly named: {already_named_count}")
    print(f"Errors: {error_count}")
    
    if args.dry_run:
        print(f"\n⚠ DRY RUN MODE - No files were actually renamed")
        print(f"Run without --dry-run to apply changes")
    
    if errors and not args.quiet:
        print(f"\nFiles with errors:")
        for filename, error in errors[:20]:  # Show first 20 errors
            print(f"  - {filename}: {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
    
    print(f"{'='*80}")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
