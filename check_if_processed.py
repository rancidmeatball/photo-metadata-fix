#!/usr/bin/env python3
"""Check if a file has been processed by the checkpoint system."""

import sys
import json
from pathlib import Path

def check_if_processed(checkpoint_path, file_path):
    """Check if a file is in the checkpoint."""
    checkpoint_path = Path(checkpoint_path)
    file_path = Path(file_path).resolve()
    
    if not checkpoint_path.exists():
        print(f"Checkpoint file not found: {checkpoint_path}")
        return False
    
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)
    
    file_str = str(file_path)
    for entry in data.get('processed_files', []):
        if Path(entry['path']).resolve() == file_path:
            print(f"File found in checkpoint:")
            print(f"  Path: {entry['path']}")
            print(f"  Result: {entry.get('result', 'unknown')}")
            print(f"  Timestamp: {entry.get('timestamp', 'unknown')}")
            if 'exif_date' in entry:
                print(f"  EXIF Date: {entry['exif_date']}")
            return True
    
    print(f"File NOT found in checkpoint (hasn't been processed yet)")
    return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 check_if_processed.py <checkpoint_file> <file_path>")
        print("Example: python3 check_if_processed.py /volume1/photo/.filesystem_dates_checkpoint.json /volume1/photo/2013/IMG_20130109_011419.jpg")
        return 1
    
    checkpoint_path = sys.argv[1]
    file_path = sys.argv[2]
    
    check_if_processed(checkpoint_path, file_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
