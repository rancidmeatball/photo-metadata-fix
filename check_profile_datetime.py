#!/usr/bin/env python3
"""
Check Profile Date Time metadata in /2013 folder and compare to filenames.
"""

import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

def extract_date_from_filename(filename):
    """Extract date from filename patterns."""
    # Pattern: IMG_yyyyMMdd_HHmmss or IMGyyyyMMdd_HHmmss
    patterns = [
        r'(?:IMG|MOV)_?(\d{4})(\d{2})(\d{2})_?(\d{2})(\d{2})(\d{2})',
        r'(?:IMG|MOV)(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            try:
                year, month, day, hour, minute, second = map(int, match.groups())
                if 2001 <= year <= 2025:
                    return datetime(year, month, day, hour, minute, second)
            except ValueError:
                pass
    
    return None

def get_profile_datetime(file_path):
    """Get Profile Date Time from file using exiftool."""
    try:
        result = subprocess.run(
            ['exiftool', '-s', '-s', '-s', '-ProfileDateTime', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            # Try to parse
            formats = [
                "%Y:%m:%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y:%m:%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
    except:
        pass
    return None

def get_datetime_original(file_path):
    """Get DateTimeOriginal from file."""
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

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check Profile Date Time in 2013 folder')
    # Auto-detect Mac vs Synology path
    import os
    if os.path.exists('/Volumes/photo-1'):
        default_dir = '/Volumes/photo-1/2013'
    elif os.path.exists('/volume1/photo/2013'):
        default_dir = '/volume1/photo/2013'
    else:
        default_dir = './2013'
    
    parser.add_argument('--directory', default=default_dir,
                       help=f'Directory to check (default: {default_dir})')
    parser.add_argument('--limit', type=int, default=20,
                       help='Limit number of files to check (default: 20)')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"PROFILE DATE TIME CHECK - {args.directory}")
    print(f"{'='*80}\n")
    
    # Find image files
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Directory not found: {args.directory}")
        return 1
    
    # Find image files
    image_extensions = ['.jpg', '.jpeg', '.heic', '.png', '.tiff', '.tif']
    files = []
    for ext in image_extensions:
        files.extend(directory.rglob(f'*{ext}'))
        files.extend(directory.rglob(f'*{ext.upper()}'))
    
    if not files:
        print(f"❌ No image files found in {args.directory}")
        return 1
    
    print(f"Found {len(files)} image files")
    if args.limit:
        files = files[:args.limit]
        print(f"Checking first {len(files)} files\n")
    
    print(f"{'Filename':<50} {'Filename Date':<20} {'ProfileDateTime':<25} {'DateTimeOriginal':<25} {'Match'}")
    print("="*140)
    
    matches = 0
    mismatches = 0
    no_profile = 0
    
    for file_path in files:
        filename = file_path.name
        filename_date = extract_date_from_filename(filename)
        
        profile_dt = get_profile_datetime(file_path)
        exif_dt = get_datetime_original(file_path)
        
        # Check if ProfileDateTime matches filename
        match_status = "?"
        if filename_date:
            if profile_dt:
                if abs((profile_dt - filename_date).total_seconds()) < 60:  # Within 1 minute
                    match_status = "✅ MATCH"
                    matches += 1
                else:
                    match_status = f"❌ DIFF ({abs((profile_dt - filename_date).days)} days)"
                    mismatches += 1
            else:
                match_status = "⚠️  NO PROFILE"
                no_profile += 1
        else:
            match_status = "⚠️  NO DATE IN NAME"
        
        filename_date_str = filename_date.strftime('%Y-%m-%d %H:%M:%S') if filename_date else 'N/A'
        profile_str = profile_dt.strftime('%Y-%m-%d %H:%M:%S') if profile_dt else 'NONE'
        exif_str = exif_dt.strftime('%Y-%m-%d %H:%M:%S') if exif_dt else 'NONE'
        
        print(f"{filename:<50} {filename_date_str:<20} {profile_str:<25} {exif_str:<25} {match_status}")
    
    print("\n" + "="*140)
    print(f"\nSummary:")
    print(f"  Files checked: {len(files)}")
    print(f"  ProfileDateTime matches filename: {matches}")
    print(f"  ProfileDateTime differs: {mismatches}")
    print(f"  No ProfileDateTime found: {no_profile}")
    
    if mismatches > 0:
        print(f"\n⚠️  {mismatches} files have ProfileDateTime that doesn't match filename!")
        print(f"   This might be why Synology Photos is showing wrong dates.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
