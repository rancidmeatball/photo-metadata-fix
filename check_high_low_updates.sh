#!/bin/bash
# Check HIGH and LOW confidence updates in output logs
# Run this on your Synology: bash check_high_low_updates.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        CHECKING HIGH & LOW CONFIDENCE UPDATES                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

LOG_DIR="/volume1/photo/logs"

echo "=== HIGH CONFIDENCE (recovery_output.log) ==="
if [ -f "$LOG_DIR/recovery_output.log" ]; then
    HIGH_UPDATES=$(grep "✓ Updated" "$LOG_DIR/recovery_output.log" 2>/dev/null | wc -l)
    HIGH_ERRORS=$(grep "✗ Error" "$LOG_DIR/recovery_output.log" 2>/dev/null | wc -l)
    HIGH_UNSUPPORTED=$(grep "Unsupported file type" "$LOG_DIR/recovery_output.log" 2>/dev/null | wc -l)
    
    echo "Files updated: $HIGH_UPDATES"
    echo "Errors: $HIGH_ERRORS"
    echo "Unsupported: $HIGH_UNSUPPORTED"
    echo ""
    
    # Check if it completed
    if grep -q "SUMMARY" "$LOG_DIR/recovery_output.log"; then
        echo "Summary section found:"
        grep -A 10 "SUMMARY" "$LOG_DIR/recovery_output.log" | head -15 | sed 's/^/  /'
    else
        echo "⚠️  No SUMMARY section - run may not have completed"
        echo "Last 10 lines:"
        tail -10 "$LOG_DIR/recovery_output.log" | sed 's/^/  /'
    fi
else
    echo "❌ recovery_output.log not found"
fi
echo ""

echo "=== LOW CONFIDENCE (recovery_low_output.log) ==="
if [ -f "$LOG_DIR/recovery_low_output.log" ]; then
    LOW_UPDATES=$(grep "✓ Updated" "$LOG_DIR/recovery_low_output.log" 2>/dev/null | wc -l)
    LOW_ERRORS=$(grep "✗ Error" "$LOG_DIR/recovery_low_output.log" 2>/dev/null | wc -l)
    LOW_UNSUPPORTED=$(grep "Unsupported file type" "$LOG_DIR/recovery_low_output.log" 2>/dev/null | wc -l)
    
    echo "Files updated: $LOW_UPDATES"
    echo "Errors: $LOW_ERRORS"
    echo "Unsupported: $LOW_UNSUPPORTED"
    echo ""
    
    # Check if it completed
    if grep -q "SUMMARY" "$LOG_DIR/recovery_low_output.log"; then
        echo "Summary section found:"
        grep -A 10 "SUMMARY" "$LOG_DIR/recovery_low_output.log" | head -15 | sed 's/^/  /'
    else
        echo "⚠️  No SUMMARY section - run may not have completed"
        echo "Last 10 lines:"
        tail -10 "$LOG_DIR/recovery_low_output.log" | sed 's/^/  /'
    fi
else
    echo "❌ recovery_low_output.log not found"
fi
echo ""

echo "=== VERY_LOW NO_EXIF (recovery_very_low_no_exif_output.log) ==="
if [ -f "$LOG_DIR/recovery_very_low_no_exif_output.log" ]; then
    VL_NOEXIF_UPDATES=$(grep "✓ Updated" "$LOG_DIR/recovery_very_low_no_exif_output.log" 2>/dev/null | wc -l)
    VL_NOEXIF_ERRORS=$(grep "✗ Error" "$LOG_DIR/recovery_very_low_no_exif_output.log" 2>/dev/null | wc -l)
    VL_NOEXIF_UNSUPPORTED=$(grep "Unsupported file type" "$LOG_DIR/recovery_very_low_no_exif_output.log" 2>/dev/null | wc -l)
    
    echo "Files updated: $VL_NOEXIF_UPDATES"
    echo "Errors: $VL_NOEXIF_ERRORS"
    echo "Unsupported: $VL_NOEXIF_UNSUPPORTED"
    echo ""
    
    # Check if it completed
    if grep -q "SUMMARY" "$LOG_DIR/recovery_very_low_no_exif_output.log"; then
        echo "Summary section found:"
        grep -A 10 "SUMMARY" "$LOG_DIR/recovery_very_low_no_exif_output.log" | head -15 | sed 's/^/  /'
    else
        echo "⚠️  No SUMMARY section - run may not have completed"
        echo "Last 10 lines:"
        tail -10 "$LOG_DIR/recovery_very_low_no_exif_output.log" | sed 's/^/  /'
    fi
else
    echo "❌ recovery_very_low_no_exif_output.log not found"
fi
echo ""

echo "=== TOTAL FROM ALL OUTPUT LOGS ==="
TOTAL_OUTPUT=$(grep -h "✓ Updated" $LOG_DIR/recovery*_output.log 2>/dev/null | wc -l)
TOTAL_APPLY=$(grep -h "✓ Updated" $LOG_DIR/recovery*_apply.log 2>/dev/null | wc -l)
TOTAL_ALL=$(grep -h "✓ Updated" $LOG_DIR/recovery*.log 2>/dev/null | wc -l)

echo "From output logs: $TOTAL_OUTPUT files"
echo "From apply logs:  $TOTAL_APPLY files"
echo "From ALL logs:    $TOTAL_ALL files"
echo ""

echo "=== EXPECTED ==="
echo "HIGH JPG:        ~248 files"
echo "LOW JPG:         ~744 files"
echo "VERY_LOW JPG:    ~290 files"
echo "VERY_LOW full:   ~388 files (already done)"
echo "────────────────────────────────"
echo "Total expected:  ~1,282 JPG files"
echo ""
