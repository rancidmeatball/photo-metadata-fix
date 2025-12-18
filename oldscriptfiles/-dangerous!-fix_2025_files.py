#!/usr/bin/env python3
"""
Fix files in /Volumes/photo-1/2016 that have 2025 in their filename.
Update their EXIF metadata and rename them with 2016 dates, staggered by a few seconds.
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image

def update_exif_to_date(image_path, target_date):
    """Update EXIF DateTimeOriginal, DateTime, and DateTimeDigitized with the target date."""
    try:
        # Format date for EXIF (standard format: YYYY:MM:DD HH:MM:SS)
        date_str = target_date.strftime("%Y:%m:%d %H:%M:%S")
        
        # Read image
        img = Image.open(image_path)
        exif_dict = img.getexif()
        
        # Update date fields
        # Tag IDs: DateTime = 306, DateTimeOriginal = 36867, DateTimeDigitized = 36868
        exif_dict[306] = date_str  # DateTime
        exif_dict[36867] = date_str  # DateTimeOriginal
        exif_dict[36868] = date_str  # DateTimeDigitized
        
        # Save with updated EXIF
        img.save(image_path, exif=exif_dict)
        return True, target_date
    except Exception as e:
        return False, str(e)

def update_video_metadata(video_path, target_date):
    """Update video file metadata using SetFile (macOS)."""
    try:
        # Format date for SetFile: MM/DD/YYYY HH:MM:SS
        date_str = target_date.strftime("%m/%d/%Y %H:%M:%S")
        
        # Use SetFile to update creation date
        subprocess.run(['SetFile', '-d', date_str, str(video_path)], check=True)
        return True, target_date
    except Exception as e:
        return False, str(e)

def rename_file_to_format(file_path, target_date):
    """Rename file to IMG_yyyyMMdd_HHmmss or MOV_yyyyMMdd_HHmmss format."""
    try:
        # Get file extension
        ext = file_path.suffix.lower()
        if ext in ['.mov', '.mp4', '.avi', '.mkv']:
            prefix = 'MOV'
        else:
            prefix = 'IMG'
        
        # Format: IMG_yyyyMMdd_HHmmss or MOV_yyyyMMdd_HHmmss
        new_name = f"{prefix}_{target_date.strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"
        new_path = file_path.parent / new_name
        
        # Handle duplicates by adding a number
        counter = 1
        while new_path.exists():
            new_name = f"{prefix}_{target_date.strftime('%Y%m%d_%H%M%S')}_{counter:02d}{file_path.suffix}"
            new_path = file_path.parent / new_name
            counter += 1
        
        file_path.rename(new_path)
        return True, new_path
    except Exception as e:
        return False, str(e)

def main():
    import sys
    
    # Check for --yes flag
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    source_dir = Path("/Volumes/photo-1/2016")
    
    if not source_dir.exists():
        print(f"Error: Directory {source_dir} does not exist!")
        return
    
    # Find all files with "2025" in their name
    print(f"Scanning {source_dir} for files with 2025 in their name...")
    files_2025 = sorted([f for f in source_dir.iterdir() 
                         if f.is_file() and "2025" in f.name])
    
    if not files_2025:
        print(f"No files with '2025' found in {source_dir}")
        return
    
    print(f"Found {len(files_2025)} file(s) to process\n")
    
    # Show the files
    print("Files to be updated:")
    for f in files_2025[:10]:
        print(f"  - {f.name}")
    if len(files_2025) > 10:
        print(f"  ... and {len(files_2025) - 10} more")
    
    # Ask for confirmation unless auto-confirmed
    if not auto_confirm:
        response = input(f"\nProcess {len(files_2025)} files? (y/n): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return
    else:
        print(f"\nAuto-confirming processing of {len(files_2025)} files...")
    
    # Target date: December 17, 2016 at 12:00:00
    # Use current year but in 2016, staggered by 3 seconds each
    base_date = datetime(2016, 12, 17, 12, 0, 0)
    
    # Image and video extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}
    
    updated_count = 0
    renamed_count = 0
    error_count = 0
    
    print(f"\nProcessing files...\n")
    
    for idx, file_path in enumerate(files_2025):
        print(f"[{idx+1}/{len(files_2025)}] Processing: {file_path.name}")
        
        # Calculate staggered date (3 seconds between each file)
        target_date = base_date + timedelta(seconds=idx * 3)
        
        # Update metadata based on file type
        if file_path.suffix.lower() in image_extensions:
            success, result = update_exif_to_date(file_path, target_date)
            if success:
                print(f"  ✓ EXIF metadata updated to: {result.strftime('%Y-%m-%d %H:%M:%S')}")
                updated_count += 1
            else:
                print(f"  ✗ Error updating EXIF: {result}")
                error_count += 1
        elif file_path.suffix.lower() in video_extensions:
            success, result = update_video_metadata(file_path, target_date)
            if success:
                print(f"  ✓ Video metadata updated to: {result.strftime('%Y-%m-%d %H:%M:%S')}")
                updated_count += 1
            else:
                print(f"  ✗ Error updating video metadata: {result}")
                error_count += 1
        
        # Rename file
        success, result = rename_file_to_format(file_path, target_date)
        if success:
            print(f"  ✓ Renamed to: {result.name}")
            renamed_count += 1
        else:
            print(f"  ✗ Error renaming: {result}")
            error_count += 1
        
        print()
    
    print(f"{'='*70}")
    print(f"Summary:")
    print(f"  Files processed: {len(files_2025)}")
    print(f"  Metadata updated: {updated_count}")
    print(f"  Files renamed: {renamed_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

