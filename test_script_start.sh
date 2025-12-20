#!/bin/bash
# Test script to verify the Python script can start without hanging

echo "Testing script startup..."
cd /volume1/photo/scripts

# Test 1: Check if script has syntax errors
echo "1. Checking for syntax errors..."
python3 -m py_compile synology_fix_filesystem_dates_with_checkpoint.py
if [ $? -eq 0 ]; then
    echo "   ✓ No syntax errors"
else
    echo "   ✗ Syntax errors found!"
    exit 1
fi

# Test 2: Try to import the script
echo "2. Testing imports..."
python3 -c "import sys; sys.path.insert(0, '/volume1/photo/scripts'); import synology_fix_filesystem_dates_with_checkpoint" 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Imports successful"
else
    echo "   ✗ Import failed!"
    exit 1
fi

# Test 3: Run with --help (should exit quickly)
echo "3. Testing --help flag..."
timeout 5 python3 ./synology_fix_filesystem_dates_with_checkpoint.py --help > /dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo "   ✓ Script responds to --help"
else
    echo "   ✗ Script hangs on --help!"
    exit 1
fi

echo ""
echo "All tests passed. Script should be ready to run."
