#!/usr/bin/env python3
"""
Check file system and EXIF metadata for a specific file.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def check_file_metadata(file_path):
    """Check both file system dates and EXIF dates for a file."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"{'='*80}")
    print(f"METADATA CHECK: {file_path.name}")
    print(f"{'='*80}")
    print(f"Full path: {file_path}")
    print()
    
    # Get file system dates using stat
    try:
        import os
        stat_info = os.stat(file_path)
        print(f"FILE SYSTEM DATES (from os.stat):")
        print(f"  Creation time (st_birthtime): {datetime.fromtimestamp(stat_info.st_birthtime)}")
        print(f"  Modification time (st_mtime): {datetime.fromtimestamp(stat_info.st_mtime)}")
        print(f"  Access time (st_atime): {datetime.fromtimestamp(stat_info.st_atime)}")
        print()
    except Exception as e:
        print(f"  Error getting file system dates: {e}")
        print()
    
    # Get EXIF dates using exiftool
    print(f"EXIF METADATA (from exiftool):")
    try:
        result = subprocess.run(
            ['exiftool', '-s', '-s', '-s', 
             '-DateTimeOriginal', '-DateTimeDigitized', '-CreateDate', '-ModifyDate',
             '-FileModifyDate', '-FileCreateDate',
             str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if ':' in line:
                    tag, value = line.split(':', 1)
                    print(f"  {tag.strip()}: {value.strip()}")
        else:
            print(f"  Error: {result.stderr}")
    except Exception as e:
        print(f"  Error running exiftool: {e}")
    
    print()
    
    # Get detailed exiftool output
    print(f"DETAILED EXIFTOOL OUTPUT:")
    try:
        result = subprocess.run(
            ['exiftool', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Filter for date-related tags
            for line in result.stdout.split('\n'):
                if any(tag in line for tag in ['Date', 'Time', 'Create', 'Modify']):
                    print(f"  {line}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print(f"{'='*80}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_file_metadata.py <file_path>")
        print("Example: python3 check_file_metadata.py /volume1/photo/2013/IMG_20130109_011419.jpg")
        return 1
    
    file_path = sys.argv[1]
    check_file_metadata(file_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
