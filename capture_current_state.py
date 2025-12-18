#!/usr/bin/env python3
"""
Capture current state of all files BEFORE renaming.
Records: filename, full path, directory, file system dates, EXIF dates.
This preserves directory structure so files can be put back correctly.
"""

import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

def get_exif_dates(file_path):
    """Extract EXIF dates from a file."""
    dates = {}
    
    try:
        with Image.open(file_path) as img:
            exifdata = img.getexif()
            if exifdata:
                # Extract key date fields
                if 36867 in exifdata:  # DateTimeOriginal
                    dates['DateTimeOriginal'] = str(exifdata[36867])
                if 36868 in exifdata:  # DateTimeDigitized
                    dates['DateTimeDigitized'] = str(exifdata[36868])
                if 306 in exifdata:  # DateTime
                    dates['DateTime'] = str(exifdata[306])
    except:
        pass
    
    return dates

def get_file_dates(file_path):
    """Get file system dates."""
    dates = {}
    
    try:
        stat = os.stat(file_path)
        
        if hasattr(stat, 'st_birthtime'):
            dates['birthtime'] = datetime.fromtimestamp(stat.st_birthtime).isoformat()
        dates['mtime'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        dates['atime'] = datetime.fromtimestamp(stat.st_atime).isoformat()
    except:
        pass
    
    return dates

def capture_file_state(file_path, base_dir):
    """Capture complete state of a single file."""
    rel_path = file_path.relative_to(base_dir)
    
    state = {
        'filename': file_path.name,
        'full_path': str(file_path),
        'relative_path': str(rel_path),
        'directory': str(file_path.parent),
        'relative_directory': str(rel_path.parent),
        'extension': file_path.suffix.lower(),
        'size_bytes': file_path.stat().st_size,
        'file_dates': get_file_dates(file_path),
        'exif_dates': {},
        'captured_at': datetime.now().isoformat()
    }
    
    # Get EXIF dates for image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif'}
    if file_path.suffix.lower() in image_extensions:
        state['exif_dates'] = get_exif_dates(file_path)
    
    return state

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Capture current state of all files before renaming'
    )
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--output-dir', default='/Users/john/Cursor/fix_metadata/STATE_BACKUPS',
                       help='Output directory for state files')
    parser.add_argument('--recursive', '-r', action='store_true', default=True,
                       help='Scan recursively (default: True)')
    parser.add_argument('--include-thumbnails', action='store_true',
                       help='Include Synology thumbnail files')
    
    args = parser.parse_args()
    
    source_dir = Path(args.directory).resolve()
    
    if not source_dir.exists():
        print(f"ERROR: Directory {source_dir} does not exist!")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"{'='*80}")
    print(f"CAPTURE CURRENT FILE STATE")
    print(f"{'='*80}")
    print(f"Directory: {source_dir}")
    print(f"Recursive: {args.recursive}")
    print(f"Output: {output_dir}")
    print(f"{'='*80}\n")
    
    # Find all media files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    all_extensions = image_extensions | video_extensions
    
    print("Scanning for files...")
    
    if args.recursive:
        files = [f for f in source_dir.rglob('*') 
                if f.is_file() and f.suffix.lower() in all_extensions]
    else:
        files = [f for f in source_dir.iterdir() 
                if f.is_file() and f.suffix.lower() in all_extensions]
    
    # Filter out thumbnail files unless requested
    if not args.include_thumbnails:
        files = [f for f in files if 'SYNOPHOTO' not in f.name and '@eaDir' not in str(f)]
    
    print(f"Found {len(files)} files to capture\n")
    
    if not files:
        print("No files found!")
        return 0
    
    # Capture state of all files
    print("Capturing file states...")
    
    all_states = []
    errors = []
    
    for idx, file_path in enumerate(files, 1):
        if idx % 1000 == 0:
            print(f"  Progress: {idx}/{len(files)} ({idx*100//len(files)}%)")
        
        try:
            state = capture_file_state(file_path, source_dir)
            all_states.append(state)
        except Exception as e:
            errors.append((str(file_path), str(e)))
    
    print(f"  Captured: {len(all_states)} files")
    if errors:
        print(f"  Errors: {len(errors)} files")
    
    # Save as JSON (for scripts)
    json_path = output_dir / f"file_state_{timestamp}.json"
    print(f"\nSaving JSON database: {json_path.name}")
    with open(json_path, 'w') as f:
        json.dump({
            'captured_at': datetime.now().isoformat(),
            'source_directory': str(source_dir),
            'total_files': len(all_states),
            'files': all_states
        }, f, indent=2)
    print(f"  ✓ Saved {len(all_states)} file states")
    
    # Save as CSV (for viewing in Excel)
    csv_path = output_dir / f"file_state_{timestamp}.csv"
    print(f"Saving CSV file: {csv_path.name}")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Filename', 'Full Path', 'Relative Path', 'Directory', 
            'Relative Directory', 'Extension', 'Size (bytes)',
            'File Created', 'File Modified', 'EXIF DateTimeOriginal',
            'EXIF DateTimeDigitized', 'EXIF DateTime', 'Captured At'
        ])
        
        for state in all_states:
            writer.writerow([
                state['filename'],
                state['full_path'],
                state['relative_path'],
                state['directory'],
                state['relative_directory'],
                state['extension'],
                state['size_bytes'],
                state['file_dates'].get('birthtime', ''),
                state['file_dates'].get('mtime', ''),
                state['exif_dates'].get('DateTimeOriginal', ''),
                state['exif_dates'].get('DateTimeDigitized', ''),
                state['exif_dates'].get('DateTime', ''),
                state['captured_at']
            ])
    print(f"  ✓ Saved CSV with {len(all_states)} rows")
    
    # Create directory structure summary
    dir_summary_path = output_dir / f"directory_structure_{timestamp}.txt"
    print(f"Creating directory summary: {dir_summary_path.name}")
    
    # Group files by directory
    by_directory = {}
    for state in all_states:
        dir_path = state['relative_directory']
        if dir_path not in by_directory:
            by_directory[dir_path] = []
        by_directory[dir_path].append(state['filename'])
    
    with open(dir_summary_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("DIRECTORY STRUCTURE\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Captured: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {source_dir}\n")
        f.write(f"Total files: {len(all_states)}\n")
        f.write(f"Total directories: {len(by_directory)}\n\n")
        f.write("=" * 80 + "\n\n")
        
        for dir_path in sorted(by_directory.keys()):
            files_in_dir = by_directory[dir_path]
            f.write(f"{dir_path}/ ({len(files_in_dir)} files)\n")
            for filename in sorted(files_in_dir)[:10]:  # Show first 10
                f.write(f"  - {filename}\n")
            if len(files_in_dir) > 10:
                f.write(f"  ... and {len(files_in_dir) - 10} more files\n")
            f.write("\n")
    
    print(f"  ✓ Saved directory structure")
    
    # Save error log if any
    if errors:
        error_path = output_dir / f"capture_errors_{timestamp}.txt"
        print(f"\nSaving error log: {error_path.name}")
        with open(error_path, 'w') as f:
            f.write("ERRORS DURING CAPTURE\n")
            f.write("=" * 80 + "\n\n")
            for file_path, error in errors:
                f.write(f"File: {file_path}\n")
                f.write(f"Error: {error}\n\n")
        print(f"  ✓ Saved {len(errors)} errors")
    
    print(f"\n{'='*80}")
    print(f"SUCCESS!")
    print(f"{'='*80}")
    print(f"\nState captured for {len(all_states)} files")
    print(f"\nFiles created:")
    print(f"  1. {json_path.name} - JSON database")
    print(f"  2. {csv_path.name} - CSV for Excel")
    print(f"  3. {dir_summary_path.name} - Directory structure")
    if errors:
        print(f"  4. {error_path.name} - Error log")
    
    print(f"\nThis captures:")
    print(f"  ✓ Current filename and full path")
    print(f"  ✓ Directory structure (relative and absolute)")
    print(f"  ✓ File system dates (creation, modification)")
    print(f"  ✓ EXIF dates (DateTimeOriginal, etc.)")
    print(f"  ✓ File size and extension")
    
    print(f"\nYou can use this to:")
    print(f"  - Restore original directory structure")
    print(f"  - Find files by their old location")
    print(f"  - Verify file system dates (likely true creation dates)")
    print(f"  - Compare with rename logs")
    
    print(f"\n⚠️  KEEP THESE FILES SAFE - They're your backup!")
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
