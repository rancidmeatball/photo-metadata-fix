#!/bin/bash
# Find all updates from both apply logs AND output logs
# Run this on your Synology: bash find_all_updates.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        FINDING ALL RECOVERY UPDATES                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

LOG_DIR="/volume1/photo/logs"

echo "=== SEARCHING ALL LOG FILES ==="
echo ""

# Search apply logs
echo "From apply logs (*_apply.log):"
APPLY_COUNT=$(grep -h "✓ Updated" $LOG_DIR/recovery*_apply.log 2>/dev/null | wc -l)
echo "  Found: $APPLY_COUNT files"
echo ""

# Search output logs (they might contain the actual updates)
echo "From output logs (*_output.log):"
OUTPUT_COUNT=$(grep -h "✓ Updated" $LOG_DIR/recovery*_output.log 2>/dev/null | wc -l)
echo "  Found: $OUTPUT_COUNT files"
echo ""

# Search all logs
echo "From ALL logs (*.log):"
ALL_COUNT=$(grep -h "✓ Updated" $LOG_DIR/recovery*.log 2>/dev/null | wc -l)
echo "  Found: $ALL_COUNT files"
echo ""

# Show breakdown by file
echo "=== BREAKDOWN BY LOG FILE ==="
for log in $LOG_DIR/recovery*.log; do
    if [ -f "$log" ]; then
        COUNT=$(grep "✓ Updated" "$log" 2>/dev/null | wc -l)
        if [ $COUNT -gt 0 ]; then
            echo "$(basename $log): $COUNT files"
        fi
    fi
done
echo ""

# Show what confidence levels were processed
echo "=== CHECKING OUTPUT LOGS FOR CONFIDENCE LEVELS ==="
for log in $LOG_DIR/recovery*_output.log; do
    if [ -f "$log" ]; then
        echo "$(basename $log):"
        if grep -q "Min Confidence" "$log"; then
            grep "Min Confidence" "$log" | head -1 | sed 's/^/    /'
        fi
        if grep -q "confidence" "$log" -i; then
            grep -i "confidence" "$log" | head -3 | sed 's/^/    /'
        fi
    fi
done
echo ""

echo "=== SUMMARY ==="
echo "Total unique updates found: $ALL_COUNT"
echo "Expected: ~1,282 JPG files"
echo ""

if [ $ALL_COUNT -lt 500 ]; then
    echo "⚠️  MISSING: Only $ALL_COUNT files updated out of ~1,282 expected"
    echo ""
    echo "Likely missing runs:"
    echo "  - HIGH confidence (expected ~248 JPG files)"
    echo "  - LOW confidence (expected ~744 JPG files)"
    echo "  - VERY_LOW no_exif (expected ~290 JPG files)"
    echo ""
    echo "Check if these scripts were run:"
    echo "  - HIGH: recovery_plan.csv with --confidence HIGH"
    echo "  - LOW: recovery_plan_low_only.csv with --confidence LOW"
    echo "  - VERY_LOW no_exif: recovery_plan_very_low_no_exif.csv"
fi
