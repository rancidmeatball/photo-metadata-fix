#!/bin/bash
# Diagnostic script to find what recovery runs happened
# Run this on your Synology: bash diagnose_recovery_status.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        RECOVERY STATUS DIAGNOSTIC                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

LOG_DIR="/volume1/photo/logs"

echo "=== 1. CHECKING OUTPUT LOGS FOR PROCESSING INFO ==="
echo ""

# Check recovery_output.log (likely HIGH confidence)
if [ -f "$LOG_DIR/recovery_output.log" ]; then
    echo "recovery_output.log:"
    echo "  Size: $(ls -lh $LOG_DIR/recovery_output.log | awk '{print $5}')"
    echo "  Last 5 lines:"
    tail -5 $LOG_DIR/recovery_output.log | sed 's/^/    /'
    echo ""
fi

# Check recovery_low_output.log
if [ -f "$LOG_DIR/recovery_low_output.log" ]; then
    echo "recovery_low_output.log:"
    echo "  Size: $(ls -lh $LOG_DIR/recovery_low_output.log | awk '{print $5}')"
    echo "  Last 5 lines:"
    tail -5 $LOG_DIR/recovery_low_output.log | sed 's/^/    /'
    echo ""
fi

# Check recovery_very_low_no_exif_output.log
if [ -f "$LOG_DIR/recovery_very_low_no_exif_output.log" ]; then
    echo "recovery_very_low_no_exif_output.log:"
    echo "  Size: $(ls -lh $LOG_DIR/recovery_very_low_no_exif_output.log | awk '{print $5}')"
    echo "  Last 5 lines:"
    tail -5 $LOG_DIR/recovery_very_low_no_exif_output.log | sed 's/^/    /'
    echo ""
fi

# Check recovery_very_low_full_output.log
if [ -f "$LOG_DIR/recovery_very_low_full_output.log" ]; then
    echo "recovery_very_low_full_output.log:"
    echo "  Size: $(ls -lh $LOG_DIR/recovery_very_low_full_output.log | awk '{print $5}')"
    echo "  Last 5 lines:"
    tail -5 $LOG_DIR/recovery_very_low_full_output.log | sed 's/^/    /'
    echo ""
fi

echo "=== 2. SEARCHING OUTPUT LOGS FOR SUMMARY INFO ==="
echo ""

# Look for summary sections in output logs
for log in $LOG_DIR/recovery*_output.log; do
    if [ -f "$log" ]; then
        echo "$(basename $log):"
        # Look for summary section
        if grep -q "SUMMARY" "$log"; then
            grep -A 10 "SUMMARY" "$log" | head -15 | sed 's/^/    /'
        else
            echo "    No SUMMARY section found"
        fi
        echo ""
    fi
done

echo "=== 3. CHECKING FOR MISSING APPLY LOGS ==="
echo ""

# Check if apply logs exist for each output log
for output_log in $LOG_DIR/recovery*_output.log; do
    if [ -f "$output_log" ]; then
        BASE=$(basename "$output_log" _output.log)
        APPLY_LOG="$LOG_DIR/${BASE}_apply.log"
        if [ -f "$APPLY_LOG" ]; then
            COUNT=$(grep "✓ Updated" "$APPLY_LOG" 2>/dev/null | wc -l)
            echo "✅ $(basename $output_log) → $(basename $APPLY_LOG) ($COUNT files)"
        else
            echo "❌ $(basename $output_log) → NO APPLY LOG FOUND"
            echo "   (Processing may have used default log name: recovery_apply.log)"
        fi
    fi
done
echo ""

echo "=== 4. CHECKING DEFAULT LOG FILE ==="
if [ -f "$LOG_DIR/recovery_apply.log" ]; then
    COUNT=$(grep "✓ Updated" "$LOG_DIR/recovery_apply.log" 2>/dev/null | wc -l)
    ERRORS=$(grep "✗ Error" "$LOG_DIR/recovery_apply.log" 2>/dev/null | wc -l)
    echo "recovery_apply.log:"
    echo "  Files updated: $COUNT"
    echo "  Errors: $ERRORS"
    echo "  Last 3 entries:"
    grep "✓ Updated\|✗ Error" "$LOG_DIR/recovery_apply.log" 2>/dev/null | tail -3 | sed 's/^/    /'
fi
echo ""

echo "=== 5. WHAT'S MISSING ==="
echo ""
echo "Expected processing:"
echo "  HIGH confidence:    ~248 JPG files"
echo "  LOW confidence:     ~744 JPG files"
echo "  VERY_LOW confidence: ~290 JPG files"
echo "  Total expected:     ~1,282 JPG files"
echo ""
echo "Actual processing:"
echo "  recovery_apply.log:  $(grep '✓ Updated' $LOG_DIR/recovery_apply.log 2>/dev/null | wc -l) files"
echo "  recovery_very_low_full_apply.log: $(grep '✓ Updated' $LOG_DIR/recovery_very_low_full_apply.log 2>/dev/null | wc -l) files"
echo "  Total found:        $(grep -h '✓ Updated' $LOG_DIR/recovery*_apply.log 2>/dev/null | wc -l) files"
echo ""

echo "=== 6. RECOMMENDATIONS ==="
echo ""
if [ ! -f "$LOG_DIR/recovery_high_apply.log" ] && [ ! -f "$LOG_DIR/recovery_low_apply.log" ]; then
    echo "⚠️  HIGH and LOW confidence runs may not have completed or used different log names."
    echo "   Check if HIGH and LOW confidence scripts were run."
    echo ""
fi

echo "To find all updates, search output logs:"
echo "  grep -h '✓ Updated' $LOG_DIR/recovery*_output.log | wc -l"
echo ""
