#!/bin/bash
# Verification script for recovery completion - checks ALL log files
# Run this on your Synology: bash verify_recovery_completion_fixed.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        RECOVERY COMPLETION VERIFICATION (FIXED)                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

LOG_DIR="/volume1/photo/logs"

echo "=== 1. ALL RECOVERY LOG FILES ==="
ls -lh $LOG_DIR/recovery*.log 2>/dev/null | awk '{print $9, "(" $5 ")"}'
echo ""

echo "=== 2. FILES UPDATED (from ALL log files) ==="

# Check ALL recovery apply logs for "✓ Updated"
ALL_UPDATES=$(grep -h "✓ Updated" $LOG_DIR/recovery*_apply.log 2>/dev/null | wc -l)
echo "Total files updated: $ALL_UPDATES"
echo ""

# Show breakdown by log file
echo "Breakdown by log file:"
for log in $LOG_DIR/recovery*_apply.log; do
    if [ -f "$log" ]; then
        COUNT=$(grep "✓ Updated" "$log" 2>/dev/null | wc -l)
        if [ $COUNT -gt 0 ]; then
            echo "  $(basename $log): $COUNT files"
        fi
    fi
done
echo ""

echo "=== 3. ERRORS (from ALL log files) ==="
ALL_ERRORS=$(grep -h "✗ Error" $LOG_DIR/recovery*_apply.log 2>/dev/null | wc -l)
echo "Total errors: $ALL_ERRORS"

if [ $ALL_ERRORS -gt 0 ]; then
    echo ""
    echo "Error breakdown:"
    for log in $LOG_DIR/recovery*_apply.log; do
        if [ -f "$log" ]; then
            COUNT=$(grep "✗ Error" "$log" 2>/dev/null | wc -l)
            if [ $COUNT -gt 0 ]; then
                echo "  $(basename $log): $COUNT errors"
            fi
        fi
    done
fi
echo ""

echo "=== 4. UNSUPPORTED FILES (HEIC, etc.) ==="
ALL_UNSUPPORTED=$(grep -h "Unsupported file type" $LOG_DIR/recovery*_apply.log 2>/dev/null | wc -l)
echo "Total unsupported: $ALL_UNSUPPORTED"

if [ $ALL_UNSUPPORTED -gt 0 ]; then
    echo ""
    echo "Unsupported breakdown:"
    for log in $LOG_DIR/recovery*_apply.log; do
        if [ -f "$log" ]; then
            COUNT=$(grep "Unsupported file type" "$log" 2>/dev/null | wc -l)
            if [ $COUNT -gt 0 ]; then
                echo "  $(basename $log): $COUNT files"
            fi
        fi
    done
fi
echo ""

echo "=== 5. EXPECTED VS ACTUAL ==="
echo "Expected JPG updates from recovery plan: ~1,282 files"
echo "Actual files updated:                    $ALL_UPDATES files"
echo ""

echo "=== 6. RECENT ACTIVITY (last 10 entries) ==="
echo "Most recent updates:"
grep -h "✓ Updated" $LOG_DIR/recovery*_apply.log 2>/dev/null | tail -10
echo ""

if [ $ALL_ERRORS -gt 0 ]; then
    echo "Most recent errors:"
    grep -h "✗ Error" $LOG_DIR/recovery*_apply.log 2>/dev/null | tail -5
    echo ""
fi

echo "=== 7. COMPLETION STATUS ==="
if [ $ALL_UPDATES -ge 1200 ]; then
    echo "✅ SUCCESS: Most JPG files appear to have been processed!"
    echo "   ($ALL_UPDATES files updated)"
elif [ $ALL_UPDATES -gt 0 ]; then
    echo "⚠️  PARTIAL: $ALL_UPDATES files updated (expected ~1,282 JPG files)"
    echo "   Some files may still need processing."
else
    echo "❌ NO FILES UPDATED: Check logs for issues."
    echo "   Run: tail -50 /volume1/photo/logs/recovery*_apply.log"
fi
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  To see full log details, run:                               ║"
echo "║  tail -50 /volume1/photo/logs/recovery*_apply.log             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
