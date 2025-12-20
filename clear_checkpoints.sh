#!/bin/bash
# Clear checkpoints and logs to start fresh

echo "This will clear all checkpoints and logs for filesystem dates fix."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Backup checkpoint first
if [ -f /volume1/photo/.filesystem_dates_checkpoint.json ]; then
    echo "Backing up checkpoint..."
    cp /volume1/photo/.filesystem_dates_checkpoint.json /volume1/photo/.filesystem_dates_checkpoint.json.backup_$(date +%Y%m%d_%H%M%S)
fi

# Remove checkpoint
echo "Removing checkpoint..."
rm -f /volume1/photo/.filesystem_dates_checkpoint.json
rm -f /volume1/photo/.filesystem_dates_checkpoint.json.tmp

# Backup and clear log
if [ -f /volume1/photo/logs/filesystem_dates_fix.log ]; then
    echo "Backing up log..."
    mv /volume1/photo/logs/filesystem_dates_fix.log /volume1/photo/logs/filesystem_dates_fix.log.backup_$(date +%Y%m%d_%H%M%S)
fi

# Backup and clear skipped log
if [ -f /volume1/photo/logs/filesystem_dates_skipped.log ]; then
    echo "Backing up skipped log..."
    mv /volume1/photo/logs/filesystem_dates_skipped.log /volume1/photo/logs/filesystem_dates_skipped.log.backup_$(date +%Y%m%d_%H%M%S)
fi

# Backup and clear all log
if [ -f /volume1/photo/logs/filesystem_dates_all.log ]; then
    echo "Backing up all log..."
    mv /volume1/photo/logs/filesystem_dates_all.log /volume1/photo/logs/filesystem_dates_all.log.backup_$(date +%Y%m%d_%H%M%S)
fi

echo "✅ Checkpoints and logs cleared (backups created)"
echo "You can now start fresh with the updated script."
