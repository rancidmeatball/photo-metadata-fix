#!/usr/bin/env python3
"""
Update all files in fixed_metadata to December 17, 2016 and rename them.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

def update_exif_to_date(image_path, target_date, time_offset=0):
    """Update EXIF DateTimeOriginal, DateTime, and DateTimeDigitized with the target date."""
    try:
        # Format date for EXIF (standard format: YYYY:MM:DD HH:MM:SS)
        # Add time offset in seconds to create unique timestamps
        file_date = target_date + timedelta(seconds=time_offset)
        date_str = file_date.strftime("%Y:%m:%d %H:%M:%S")
        
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
        return True, file_date
    except Exception as e:
        return False, str(e)

def rename_file_to_format(file_path, target_date, time_offset=0):
    """Rename file to IMG_yyyyMMdd_HHmmss or MOV_yyyyMMdd_HHmmss format."""
    try:
        # Calculate the file date with offset
        file_date = target_date + timedelta(seconds=time_offset)
        
        # Get file extension
        ext = file_path.suffix.upper()
        if ext in ['.MOV', '.MP4', '.AVI', '.MKV']:
            prefix = 'MOV'
        else:
            prefix = 'IMG'
        
        # Format: IMG_yyyyMMdd_HHmmss or MOV_yyyyMMdd_HHmmss
        new_name = f"{prefix}_{file_date.strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"
        new_path = file_path.parent / new_name
        
        # Handle duplicates by adding a number
        counter = 1
        while new_path.exists():
            new_name = f"{prefix}_{file_date.strftime('%Y%m%d_%H%M%S')}_{counter:02d}{file_path.suffix}"
            new_path = file_path.parent / new_name
            counter += 1
        
        file_path.rename(new_path)
        return True, new_path
    except Exception as e:
        return False, str(e)

def main():
    source_dir = Path("/Users/john/fixed_metadata")
    
    if not source_dir.exists():
        print(f"Error: Directory {source_dir} does not exist!")
        return
    
    # Target date: December 17, 2016 at 12:00:00
    target_date = datetime(2016, 12, 17, 12, 0, 0)
    
    # Find all image and video files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}
    all_extensions = image_extensions | video_extensions
    
    print(f"Scanning {source_dir} for files...")
    
    files = [f for f in source_dir.iterdir() 
             if f.is_file() and f.suffix.lower() in all_extensions]
    
    if not files:
        print(f"No image/video files found in {source_dir}")
        return
    
    print(f"Found {len(files)} file(s) to process\n")
    
    # Sort files by name for consistent ordering
    files.sort(key=lambda x: x.name)
    
    updated_count = 0
    renamed_count = 0
    error_count = 0
    
    for idx, file_path in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Processing: {file_path.name}")
        
        # Use index as time offset (in seconds) to create unique timestamps
        # This ensures each file gets a slightly different time
        time_offset = idx * 2  # 2 seconds between each file
        
        # Update EXIF metadata for image files
        if file_path.suffix.lower() in image_extensions:
            success, result = update_exif_to_date(file_path, target_date, time_offset)
            if success:
                print(f"  ✓ EXIF metadata updated to: {result.strftime('%Y-%m-%d %H:%M:%S')}")
                updated_count += 1
            else:
                print(f"  ✗ Error updating EXIF: {result}")
                error_count += 1
        
        # Rename file
        success, result = rename_file_to_format(file_path, target_date, time_offset)
        if success:
            print(f"  ✓ Renamed to: {result.name}")
            renamed_count += 1
        else:
            print(f"  ✗ Error renaming: {result}")
            error_count += 1
        
        print()
    
    print(f"{'='*70}")
    print(f"Summary:")
    print(f"  Files processed: {len(files)}")
    print(f"  Metadata updated: {updated_count}")
    print(f"  Files renamed: {renamed_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

