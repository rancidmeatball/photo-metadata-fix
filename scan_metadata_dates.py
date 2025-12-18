#!/usr/bin/env python3
"""
Scan files and show all available dates in their metadata.
This helps identify which files have incorrect dates before renaming.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

def get_all_dates_from_image(image_path):
    """Extract ALL date-related fields from EXIF metadata."""
    dates = {}
    
    # Method 1: Using PIL/Pillow
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            if exifdata:
                # Common date tags
                date_tags = {
                    36867: 'DateTimeOriginal',
                    36868: 'DateTimeDigitized',
                    306: 'DateTime',
                    50971: 'SubSecTimeOriginal',
                    50972: 'SubSecTimeDigitized',
                }
                
                for tag_id, tag_name in date_tags.items():
                    if tag_id in exifdata and exifdata[tag_id]:
                        dates[f'EXIF_{tag_name}'] = str(exifdata[tag_id])
    except Exception as e:
        pass
    
    # Method 2: Using exifread for additional tags
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
            for tag_name in tags.keys():
                if any(keyword in tag_name.lower() for keyword in ['date', 'time']):
                    tag_value = str(tags[tag_name])
                    if tag_value and tag_value.lower() != 'none':
                        dates[f'EXIFREAD_{tag_name}'] = tag_value
    except Exception as e:
        pass
    
    return dates

def get_all_dates_from_video(video_path):
    """Extract ALL date-related fields from video metadata."""
    dates = {}
    
    # Try exiftool
    try:
        result = subprocess.run(
            ['exiftool', '-time:all', '-s', '-s', '-s', str(video_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip():
                    dates[f'ExifTool_Date_{i}'] = line.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        dates['ExifTool'] = 'Not available (install exiftool for video metadata)'
    
    # Try mdls (macOS)
    try:
        result = subprocess.run(
            ['mdls', '-name', 'kMDItemContentCreationDate', '-name', 
             'kMDItemDateAdded', '-name', 'kMDItemFSCreationDate', str(video_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if '=' in line and '(null)' not in line:
                    key, value = line.split('=', 1)
                    dates[f'macOS_{key.strip()}'] = value.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return dates

def get_file_system_dates(file_path):
    """Get file system dates."""
    dates = {}
    
    try:
        stat = os.stat(file_path)
        
        # macOS birthtime
        if hasattr(stat, 'st_birthtime'):
            dates['FS_Birthtime'] = datetime.fromtimestamp(stat.st_birthtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Modification time
        dates['FS_Modified'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Access time
        dates['FS_Accessed'] = datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        dates['FS_Error'] = str(e)
    
    return dates

def parse_date(date_str):
    """Parse various date formats and return year."""
    if not date_str:
        return None
    
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
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.year
        except:
            continue
    
    # Try to extract just the year
    import re
    match = re.search(r'(20\d{2}|19\d{2})', date_str)
    if match:
        return int(match.group(1))
    
    return None

def scan_file(file_path):
    """Scan a file and return all dates found."""
    ext = file_path.suffix.lower()
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    
    all_dates = {}
    
    # Get metadata dates
    if ext in image_extensions:
        metadata_dates = get_all_dates_from_image(file_path)
        if metadata_dates:
            all_dates['Metadata'] = metadata_dates
    elif ext in video_extensions:
        metadata_dates = get_all_dates_from_video(file_path)
        if metadata_dates:
            all_dates['Metadata'] = metadata_dates
    
    # Get file system dates
    fs_dates = get_file_system_dates(file_path)
    if fs_dates:
        all_dates['FileSystem'] = fs_dates
    
    return all_dates

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scan files and show all dates in metadata'
    )
    parser.add_argument('directory', nargs='?', default=None,
                       help='Directory to scan (default: current directory)')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Scan subdirectories recursively')
    parser.add_argument('--filter-year', type=int,
                       help='Only show files with dates matching this year')
    parser.add_argument('--suspicious', action='store_true',
                       help='Only show files with suspicious dates (mismatched years)')
    
    args = parser.parse_args()
    
    # Determine directory
    if args.directory:
        source_dir = Path(args.directory).expanduser().resolve()
    else:
        source_dir = Path.cwd()
    
    if not source_dir.exists():
        print(f"Error: Directory {source_dir} does not exist!")
        return 1
    
    print(f"{'='*80}")
    print(f"METADATA DATE SCANNER")
    print(f"{'='*80}")
    print(f"Directory: {source_dir}")
    print(f"Recursive: {'Yes' if args.recursive else 'No'}")
    if args.filter_year:
        print(f"Filter: Only showing files with {args.filter_year} dates")
    if args.suspicious:
        print(f"Filter: Only showing files with suspicious/mismatched dates")
    print(f"{'='*80}\n")
    
    # Find all media files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    all_extensions = image_extensions | video_extensions
    
    if args.recursive:
        files = [f for f in source_dir.rglob('*') 
                if f.is_file() and f.suffix.lower() in all_extensions]
    else:
        files = [f for f in source_dir.iterdir() 
                if f.is_file() and f.suffix.lower() in all_extensions]
    
    if not files:
        print(f"No image or video files found in {source_dir}")
        return 0
    
    print(f"Scanning {len(files)} file(s)...\n")
    
    # Scan files
    displayed_count = 0
    
    for idx, file_path in enumerate(files, 1):
        dates = scan_file(file_path)
        
        # Extract years from all dates
        years_found = set()
        all_date_strings = []
        
        for category, date_dict in dates.items():
            for key, value in date_dict.items():
                all_date_strings.append((category, key, value))
                year = parse_date(value)
                if year:
                    years_found.add(year)
        
        # Apply filters
        should_display = True
        
        if args.filter_year:
            if args.filter_year not in years_found:
                should_display = False
        
        if args.suspicious:
            # Suspicious if:
            # 1. Multiple different years found (more than 1)
            # 2. Contains both 2018 and 2025
            # 3. Contains very old dates (< 2001) and recent dates
            if len(years_found) <= 1:
                should_display = False
            elif 2018 in years_found and 2025 in years_found:
                should_display = True
            elif any(y < 2001 for y in years_found) and any(y >= 2015 for y in years_found):
                should_display = True
            elif len(years_found) == 2 and max(years_found) - min(years_found) <= 1:
                # Adjacent years are probably fine
                should_display = False
        
        if not should_display:
            continue
        
        # Display file info
        displayed_count += 1
        print(f"{'='*80}")
        print(f"[{idx}/{len(files)}] {file_path.name}")
        
        if len(years_found) > 1:
            print(f"⚠ WARNING: Multiple years found: {sorted(years_found)}")
        elif len(years_found) == 1:
            print(f"Year found: {list(years_found)[0]}")
        else:
            print(f"⚠ No parseable dates found")
        
        print(f"{'-'*80}")
        
        # Display all dates
        for category, key, value in all_date_strings:
            year = parse_date(value)
            year_str = f" [{year}]" if year else ""
            print(f"  {category:20s} | {key:30s} | {value}{year_str}")
        
        print()
    
    print(f"{'='*80}")
    print(f"Displayed {displayed_count} file(s) out of {len(files)} total")
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
