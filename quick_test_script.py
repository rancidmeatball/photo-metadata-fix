#!/usr/bin/env python3
"""Quick test to see if script can start without hanging."""

import sys
import time

print("Testing script import...")
start = time.time()

try:
    sys.path.insert(0, '/volume1/photo/scripts')
    import synology_fix_filesystem_dates_with_checkpoint
    elapsed = time.time() - start
    print(f"✓ Import successful in {elapsed:.2f} seconds")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Import failed after {elapsed:.2f} seconds: {e}")
    sys.exit(1)

print("\nTesting checkpoint loading...")
start = time.time()

try:
    checkpoint_path = '/volume1/photo/.filesystem_dates_checkpoint.json'
    import json
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)
    elapsed = time.time() - start
    print(f"✓ Checkpoint loaded in {elapsed:.2f} seconds")
    print(f"  Processed files: {len(data.get('processed_files', []))}")
    print(f"  Current index: {data.get('current_index', 0)}")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Checkpoint load failed after {elapsed:.2f} seconds: {e}")
    sys.exit(1)

print("\nTesting exiftool check...")
start = time.time()

try:
    import subprocess
    result = subprocess.run(['exiftool', '-ver'], capture_output=True, timeout=5)
    elapsed = time.time() - start
    if result.returncode == 0:
        print(f"✓ exiftool found in {elapsed:.2f} seconds")
    else:
        print(f"✗ exiftool check failed: {result.stderr.decode()}")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ exiftool check failed after {elapsed:.2f} seconds: {e}")

print("\nAll basic tests passed!")
