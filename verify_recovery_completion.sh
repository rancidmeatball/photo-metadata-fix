#!/bin/bash
# Verification script for recovery completion
# Run this on your Synology: bash verify_recovery_completion.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        RECOVERY COMPLETION VERIFICATION                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

LOG_DIR="/volume1/photo/logs"

echo "=== 1. RECOVERY LOG FILES ==="
ls -lh $LOG_DIR/recovery*_apply.log 2>/dev/null | awk '{print $9, "(" $5 ")"}'
echo ""

echo "=== 2. FILES UPDATED BY CONFIDENCE LEVEL ==="

# HIGH confidence
HIGH_COUNT=$(grep "✓ Updated" $LOG_DIR/recovery_high_apply.log 2>/dev/null | wc -l)
echo "HIGH confidence:    $HIGH_COUNT files"

# LOW confidence  
LOW_COUNT=$(grep "✓ Updated" $LOG_DIR/recovery_low_apply.log 2>/dev/null | wc -l)
echo "LOW confidence:     $LOW_COUNT files"

# VERY_LOW confidence (no exif)
VERY_LOW_COUNT=$(grep "✓ Updated" $LOG_DIR/recovery_very_low_no_exif_apply.log 2>/dev/null | wc -l)
echo "VERY_LOW (no EXIF): $VERY_LOW_COUNT files"

# Total
TOTAL=$(($HIGH_COUNT + $LOW_COUNT + $VERY_LOW_COUNT))
echo "────────────────────────────────"
echo "TOTAL UPDATED:      $TOTAL files"
echo ""

echo "=== 3. ERRORS ==="
HIGH_ERRORS=$(grep "✗ Error" $LOG_DIR/recovery_high_apply.log 2>/dev/null | wc -l)
LOW_ERRORS=$(grep "✗ Error" $LOG_DIR/recovery_low_apply.log 2>/dev/null | wc -l)
VERY_LOW_ERRORS=$(grep "✗ Error" $LOG_DIR/recovery_very_low_no_exif_apply.log 2>/dev/null | wc -l)
TOTAL_ERRORS=$(($HIGH_ERRORS + $LOW_ERRORS + $VERY_LOW_ERRORS))

echo "HIGH errors:        $HIGH_ERRORS"
echo "LOW errors:         $LOW_ERRORS"
echo "VERY_LOW errors:    $VERY_LOW_ERRORS"
echo "────────────────────────────────"
echo "TOTAL ERRORS:       $TOTAL_ERRORS"
echo ""

echo "=== 4. UNSUPPORTED FILES (HEIC, etc.) ==="
HIGH_UNSUPPORTED=$(grep "Unsupported file type" $LOG_DIR/recovery_high_apply.log 2>/dev/null | wc -l)
LOW_UNSUPPORTED=$(grep "Unsupported file type" $LOG_DIR/recovery_low_apply.log 2>/dev/null | wc -l)
VERY_LOW_UNSUPPORTED=$(grep "Unsupported file type" $LOG_DIR/recovery_very_low_no_exif_apply.log 2>/dev/null | wc -l)
TOTAL_UNSUPPORTED=$(($HIGH_UNSUPPORTED + $LOW_UNSUPPORTED + $VERY_LOW_UNSUPPORTED))

echo "HIGH unsupported:   $HIGH_UNSUPPORTED"
echo "LOW unsupported:    $LOW_UNSUPPORTED"
echo "VERY_LOW unsupported: $VERY_LOW_UNSUPPORTED"
echo "────────────────────────────────"
echo "TOTAL UNSUPPORTED:  $TOTAL_UNSUPPORTED"
echo ""

echo "=== 5. EXPECTED VS ACTUAL ==="
echo "Expected JPG updates from recovery plan: ~1,282 files"
echo "Actual files updated:                    $TOTAL files"
echo ""

if [ $TOTAL_ERRORS -gt 0 ]; then
    echo "⚠️  WARNING: There are $TOTAL_ERRORS errors. Review logs for details."
    echo ""
fi

if [ $TOTAL_UNSUPPORTED -gt 0 ]; then
    echo "ℹ️  NOTE: $TOTAL_UNSUPPORTED files were unsupported (likely HEIC)."
    echo "   These need exiftool for processing."
    echo ""
fi

echo "=== 6. COMPLETION STATUS ==="
if [ $TOTAL -ge 1200 ]; then
    echo "✅ SUCCESS: Most JPG files appear to have been processed!"
    echo "   ($TOTAL files updated)"
else
    echo "⚠️  INCOMPLETE: Only $TOTAL files updated (expected ~1,282 JPG files)"
    echo "   Check logs for issues."
fi
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  To see recent activity, run:                                  ║"
echo "║  tail -20 /volume1/photo/logs/recovery*_apply.log              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
