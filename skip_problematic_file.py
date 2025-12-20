#!/usr/bin/env python3
"""
Manually skip a problematic file by adding it to the checkpoint.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def skip_file(checkpoint_path, file_path):
    """Add a file to checkpoint as skipped_problematic."""
    checkpoint_path = Path(checkpoint_path)
    
    # Load checkpoint
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)
    
    # Check if already processed
    file_str = str(Path(file_path).resolve())
    if any(Path(p['path']).resolve() == Path(file_str) for p in data['processed_files']):
        print(f"⚠️  File already in checkpoint: {file_path}")
        return False
    
    # Add as skipped_problematic
    data['processed_files'].append({
        'path': file_str,
        'result': 'skipped_problematic',
        'timestamp': datetime.now().isoformat()
    })
    data['current_index'] += 1
    data['stats']['skipped_problematic'] = data['stats'].get('skipped_problematic', 0) + 1
    
    # Save
    temp_path = checkpoint_path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=2)
    temp_path.replace(checkpoint_path)
    
    print(f"✅ Added {file_path} to checkpoint as skipped_problematic")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 skip_problematic_file.py <checkpoint_file> <file_path>")
        print("Example: python3 skip_problematic_file.py /volume1/photo/.filesystem_dates_checkpoint.json /volume1/photo/2021/IMG_20211231_230338.heic")
        return 1
    
    checkpoint_path = sys.argv[1]
    file_path = sys.argv[2]
    
    skip_file(checkpoint_path, file_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
