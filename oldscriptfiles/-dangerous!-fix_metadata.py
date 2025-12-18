#!/usr/bin/env python3
"""
Analyze image metadata and find alternative dates for files in missing_metadata.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

def get_all_dates_from_exif(image_path):
    """Extract all date-related fields from EXIF metadata using multiple methods."""
    dates = {}
    
    # Method 1: Using PIL/Pillow
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)
                    tag_name = str(tag)
                    if isinstance(value, (str, int, float)) and value:
                        # Check if it's a date-related tag
                        if any(keyword in tag_name.lower() for keyword in ['date', 'time', 'datetime']):
                            dates[f'EXIF_{tag_name}'] = str(value)
    except Exception as e:
        pass
    
    # Method 2: Using exifread (more comprehensive, reads raw EXIF)
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
            for tag in tags.keys():
                tag_lower = tag.lower()
                if any(keyword in tag_lower for keyword in ['date', 'time', 'datetime']):
                    tag_value = str(tags[tag])
                    if tag_value and tag_value != 'None':
                        dates[f'EXIFREAD_{tag}'] = tag_value
    except Exception as e:
        pass
    
    return dates

def get_file_dates(image_path):
    """Get file system dates."""
    try:
        stat = os.stat(image_path)
        file_dates = {}
        
        # macOS birthtime (creation date)
        if hasattr(stat, 'st_birthtime'):
            file_dates['File Created (birthtime)'] = datetime.fromtimestamp(stat.st_birthtime)
        
        # Modification time
        file_dates['File Modified'] = datetime.fromtimestamp(stat.st_mtime)
        
        # Access time
        file_dates['File Accessed'] = datetime.fromtimestamp(stat.st_atime)
        
        return file_dates
    except Exception as e:
        return {}

def extract_date_from_filename(filename):
    """Try to extract date from filename patterns like IMG_YYYYMMDD_HHMMSS."""
    import re
    
    # Pattern for IMG_YYYYMMDD_HHMMSS
    pattern1 = r'IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
    match = re.search(pattern1, filename)
    if match:
        year, month, day, hour, minute, second = match.groups()
        try:
            return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        except:
            pass
    
    return None

def parse_date_string(date_str):
    """Try to parse various date string formats."""
    if not date_str or date_str == 'None':
        return None
    
    # Common EXIF date formats
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

def is_placeholder_date(date_obj):
    """Check if a date is likely a placeholder (like 2000-01-01)."""
    if date_obj.year == 2000 and date_obj.month == 1 and date_obj.day == 1:
        return True
    if date_obj.year < 1990:  # Very old dates are likely placeholders
        return True
    return False

def auto_select_best_date(date_options):
    """Automatically select the best date from available options.
    Prefers real dates over placeholder dates (2000-01-01).
    Prefers EXIF DateTime over DateTimeOriginal when DateTimeOriginal is a placeholder.
    Prefers Filename dates when available.
    """
    if not date_options:
        return None
    
    # Filter out placeholder dates
    real_dates = [(cat, key, val, parsed) for cat, key, val, parsed in date_options 
                  if not is_placeholder_date(parsed)]
    
    if not real_dates:
        # If all dates are placeholders, return None (user should choose)
        return None
    
    # Prefer Filename dates (most reliable)
    filename_dates = [d for d in real_dates if d[0] == 'Filename']
    if filename_dates:
        return filename_dates[0]
    
    # Prefer EXIF DateTime over DateTimeOriginal
    exif_datetime = [d for d in real_dates if 'DateTime' in d[1] and 'DateTimeOriginal' not in d[1]]
    if exif_datetime:
        return exif_datetime[0]
    
    # Prefer EXIF dates over file system dates
    exif_dates = [d for d in real_dates if 'EXIF' in d[0]]
    if exif_dates:
        return exif_dates[0]
    
    # Return the first real date
    return real_dates[0]

def analyze_image(image_path):
    """Analyze a single image and return all available dates."""
    all_dates = {}
    
    # Get EXIF dates
    exif_dates = get_all_dates_from_exif(image_path)
    if exif_dates:
        all_dates['EXIF Metadata'] = exif_dates
    
    # Get file system dates
    file_dates = get_file_dates(image_path)
    if file_dates:
        all_dates['File System'] = {k: v.isoformat() for k, v in file_dates.items()}
    
    # Try to extract date from filename
    filename_date = extract_date_from_filename(image_path.name)
    if filename_date:
        all_dates['Filename'] = {'Extracted Date': filename_date.isoformat()}
    
    return all_dates

def format_dates_for_display(dates_dict):
    """Format dates dictionary for readable display."""
    output = []
    for category, dates in dates_dict.items():
        output.append(f"\n{category}:")
        for key, value in dates.items():
            output.append(f"  {key}: {value}")
    return "\n".join(output)

def update_exif_date(image_path, new_date):
    """Update EXIF DateTimeOriginal, DateTime, and DateTimeDigitized with the chosen date."""
    try:
        # Format date for EXIF (standard format: YYYY:MM:DD HH:MM:SS)
        date_str = new_date.strftime("%Y:%m:%d %H:%M:%S")
        
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
        return True, date_str
    except Exception as e:
        return False, str(e)

def process_file_batch(image_path, dates, date_options):
    """Process a file in batch mode - auto-select best date."""
    auto_selected = auto_select_best_date(date_options)
    
    if auto_selected:
        category, key, value, parsed_date = auto_selected
        return parsed_date, f"Auto-selected: {category} - {key}"
    else:
        # If no good date found, use file modification date as fallback
        stat = os.stat(image_path)
        return datetime.fromtimestamp(stat.st_mtime), "Using file modification date (no good dates found)"

def main():
    import sys
    
    # Check for batch mode flag
    batch_mode = '--batch' in sys.argv or '-b' in sys.argv
    
    source_dir = Path("/Users/john/missing_metadata")
    dest_dir = Path("/Users/john/fixed_metadata")
    
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all image files (including videos for metadata analysis)
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.raw', '.cr2', '.nef', '.dng', '.arw', '.orf', '.raf', '.rw2',
                       '.mp4', '.mov', '.avi', '.mkv'}  # Added video formats
    
    print(f"Scanning {source_dir} for image files...")
    
    # First, list all items in the directory
    all_items = list(source_dir.iterdir())
    print(f"Found {len(all_items)} total items in directory")
    
    # Show first few items for debugging
    if all_items:
        print("Sample items:")
        for item in all_items[:5]:
            print(f"  - {item.name} (is_file: {item.is_file()}, suffix: {item.suffix})")
    
    image_files = [f for f in all_items 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    # If no files match extensions, try all files
    if not image_files and all_items:
        print("\nNo files matched standard image extensions. Trying all files...")
        image_files = [f for f in all_items if f.is_file()]
        print(f"Found {len(image_files)} files to process")
    
    if not image_files:
        print(f"\nNo image/video files found in {source_dir}")
        print("Supported formats: JPG, JPEG, PNG, TIFF, HEIC, RAW, CR2, NEF, DNG, MP4, MOV, etc.")
        print(f"Total items in directory: {len(all_items)}")
        return
    
    print(f"\nFound {len(image_files)} image/video file(s) to analyze\n")
    
    fixed_count = 0
    skipped_count = 0
    
    for idx, image_path in enumerate(image_files, 1):
        print(f"\n{'='*70}")
        print(f"[{idx}/{len(image_files)}] {image_path.name}")
        print(f"{'='*70}")
        
        dates = analyze_image(image_path)
        
        if not dates:
            print("⚠ No date information found in this file.")
            choice = input("Skip this file? (y/n, default=y): ").strip().lower()
            if choice != 'n':
                skipped_count += 1
                continue
        
        print(format_dates_for_display(dates))
        
        # Collect all date options
        date_options = []
        chosen_date = None  # Initialize
        print("\nAvailable date sources:")
        option_idx = 1
        
        for category, date_dict in dates.items():
            for key, value in date_dict.items():
                # Try to parse the date
                parsed_date = parse_date_string(value)
                if parsed_date:
                    date_display = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                    is_placeholder = is_placeholder_date(parsed_date)
                    placeholder_marker = " ⚠ PLACEHOLDER" if is_placeholder else ""
                    print(f"  {option_idx}. {category} - {key}: {date_display}{placeholder_marker}")
                    date_options.append((category, key, value, parsed_date))
                    option_idx += 1
        
        print(f"\n  {option_idx}. Skip this file")
        option_idx += 1
        print(f"  {option_idx}. Use file modification date")
        
        if batch_mode:
            # Batch mode: auto-select best date
            chosen_date, reason = process_file_batch(image_path, dates, date_options)
            print(f"\n💡 {reason}: {chosen_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            # Interactive mode: Try to auto-select the best date
            auto_selected = auto_select_best_date(date_options)
            if auto_selected:
                auto_idx = date_options.index(auto_selected) + 1
                category, key, value, parsed_date = auto_selected
                print(f"\n💡 Auto-selected: Option {auto_idx} - {category} - {key}: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print("   (Press Enter to accept, or enter a number to choose differently)")
                choice = input("\nWhich date would you like to use? (enter number or press Enter): ").strip()
                
                if not choice:
                    # User accepted auto-selection
                    chosen_date = parsed_date
                else:
                    try:
                        choice_num = int(choice)
                        if choice_num == option_idx - 1:
                            print("Skipping this file.\n")
                            skipped_count += 1
                            continue
                        elif choice_num == option_idx:
                            stat = os.stat(image_path)
                            chosen_date = datetime.fromtimestamp(stat.st_mtime)
                        elif 1 <= choice_num <= len(date_options):
                            category, key, date_str, parsed_date = date_options[choice_num - 1]
                            chosen_date = parsed_date
                        else:
                            print("Invalid choice. Skipping.\n")
                            skipped_count += 1
                            continue
                    except ValueError:
                        print("Invalid input. Skipping.\n")
                        skipped_count += 1
                        continue
            else:
                # No auto-selection possible, require user input
                choice = input("\nWhich date would you like to use? (enter number): ").strip()
                
                try:
                    choice_num = int(choice)
                    chosen_date = None
                    
                    if choice_num == option_idx - 1:
                        print("Skipping this file.\n")
                        skipped_count += 1
                        continue
                    elif choice_num == option_idx:
                        # Use file modification date
                        stat = os.stat(image_path)
                        chosen_date = datetime.fromtimestamp(stat.st_mtime)
                    elif 1 <= choice_num <= len(date_options):
                        # Use selected date
                        category, key, date_str, parsed_date = date_options[choice_num - 1]
                        chosen_date = parsed_date
                    else:
                        print("Invalid choice. Skipping.\n")
                        skipped_count += 1
                        continue
                except ValueError:
                    print("Invalid input. Skipping.\n")
                    skipped_count += 1
                    continue
        
        # Process the file (for both batch and interactive modes)
        try:
            if chosen_date:
                # Update EXIF with chosen date (only for image files)
                if image_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif'}:
                    success, result = update_exif_date(image_path, chosen_date)
                    
                    if success:
                        print(f"✓ EXIF metadata updated to: {result}")
                    else:
                        print(f"✗ Error updating metadata: {result}")
                        print("File will still be moved if you proceed.")
                
                # Move file to fixed_metadata directory
                dest_path = dest_dir / image_path.name
                shutil.move(str(image_path), str(dest_path))
                print(f"✓ File moved to: {dest_path}")
                fixed_count += 1
        except (ValueError, IndexError, Exception) as e:
            print(f"Error processing file: {e}. Skipping file.\n")
            skipped_count += 1
            continue
    
    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  Fixed and moved: {fixed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total processed: {len(image_files)}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

