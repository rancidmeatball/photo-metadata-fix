# 📍 Checkpoint & Background Execution Guide

## 🎉 New Features Added!

### ✅ **Checkpoint/Resume System**
- Saves progress every 100 files
- Automatically resumes if interrupted
- Tracks: renamed, already correct, errors
- Crash-safe: atomic file writes

### ✅ **Background Execution Ready**
- Works with `nohup`, `screen`, `tmux`
- Survives SSH disconnects
- Can run for hours/days unattended
- Progress tracked in checkpoint file

---

## 📁 New Scripts with Checkpoints

### 1. **`synology_rename_photos_with_checkpoint.py`** (Synology NAS)
- All features of original + checkpoints
- Defaults to `/volume1/photo`
- Optimized for Synology

### 2. **`find_and_rename_with_checkpoint.py`** (macOS/Linux)
- All features of original + checkpoints
- For local machines
- Same safe approach

---

## 🚀 Basic Usage

### **Standard Run (With Checkpoints)**
```bash
# Synology
./synology_rename_photos_with_checkpoint.py --yes

# macOS
./find_and_rename_with_checkpoint.py /path/to/photos --yes
```

### **Resume After Interruption**
```bash
# Automatically resumes from last checkpoint
./synology_rename_photos_with_checkpoint.py --resume

# Or just run normally - it auto-detects checkpoint
./synology_rename_photos_with_checkpoint.py --yes
```

### **Dry Run (No Checkpoints Created)**
```bash
./synology_rename_photos_with_checkpoint.py --dry-run
```

### **Disable Checkpoints**
```bash
./synology_rename_photos_with_checkpoint.py --no-checkpoint --yes
```

---

## 💾 Checkpoint Files

### **Default Locations**
- **Synology**: `/volume1/photo/.photo_rename_checkpoint.json`
- **macOS**: `<directory>/.photo_rename_checkpoint.json`

### **Custom Location**
```bash
./synology_rename_photos_with_checkpoint.py \
  --checkpoint-file /volume1/backups/my_checkpoint.json \
  --yes
```

### **What's Saved in Checkpoint**
```json
{
  "version": "2.0",
  "created_at": "2025-12-17T21:50:00",
  "last_update": "2025-12-17T22:30:00",
  "current_index": 5432,
  "total_files": 386356,
  "stats": {
    "renamed": 4821,
    "already_correct": 489,
    "errors": 122
  },
  "processed_files": [...]
}
```

---

## 🔄 Background Execution Methods

### **Method 1: `nohup` (Simplest)**

Runs in background, survives SSH disconnect:

```bash
# Synology
nohup ./synology_rename_photos_with_checkpoint.py --yes \
  > /volume1/logs/rename_$(date +%Y%m%d).log 2>&1 &

# Save the process ID
echo $! > /volume1/logs/rename.pid

# Check if still running
ps aux | grep synology_rename_photos_with_checkpoint

# View progress in real-time
tail -f /volume1/logs/rename_20251217.log

# Check checkpoint status
cat /volume1/photo/.photo_rename_checkpoint.json | grep current_index
```

**To kill if needed:**
```bash
kill $(cat /volume1/logs/rename.pid)
```

---

### **Method 2: `screen` (Recommended - Can Reconnect)**

Best option for long-running tasks:

```bash
# Start a screen session
screen -S photo_rename

# Run the script
./synology_rename_photos_with_checkpoint.py --yes

# Detach: Press Ctrl+A then D
# You can now disconnect SSH safely!

# Later: Reconnect to see progress
screen -r photo_rename

# List all active screens
screen -ls

# Kill a screen session
screen -X -S photo_rename quit
```

---

### **Method 3: `tmux` (Modern Alternative)**

Similar to screen, more features:

```bash
# Create new tmux session
tmux new -s photo_rename

# Run script
./synology_rename_photos_with_checkpoint.py --yes

# Detach: Press Ctrl+B then D

# Reconnect
tmux attach -t photo_rename

# List sessions
tmux ls

# Kill session
tmux kill-session -t photo_rename
```

---

### **Method 4: Synology Task Scheduler (Automated)**

For scheduled/automated runs:

1. **Control Panel** → **Task Scheduler**
2. **Create** → **Scheduled Task** → **User-defined script**
3. **General**:
   - Task: "Photo Rename with Checkpoint"
   - User: root
   - Enabled: ✓

4. **Schedule**:
   - Run on boot (if you want it to auto-resume)
   - Or specific time: Daily at 2:00 AM

5. **Task Settings**:
```bash
#!/bin/bash
cd /volume1/scripts
./synology_rename_photos_with_checkpoint.py --yes \
  >> /volume1/logs/photo_rename_$(date +%Y%m%d).log 2>&1
```

**Benefits:**
- Runs automatically
- Restarts on NAS reboot
- Can resume from checkpoint
- Logs everything

---

## 📊 Monitoring Progress

### **Check Checkpoint Status**
```bash
# View checkpoint (formatted)
cat /volume1/photo/.photo_rename_checkpoint.json | python3 -m json.tool

# Quick stats
grep -E "(current_index|total_files|stats)" \
  /volume1/photo/.photo_rename_checkpoint.json
```

### **Calculate Progress**
```bash
# Extract numbers and calculate
CURRENT=$(grep current_index /volume1/photo/.photo_rename_checkpoint.json | grep -o '[0-9]*')
TOTAL=$(grep total_files /volume1/photo/.photo_rename_checkpoint.json | grep -o '[0-9]*')
PERCENT=$((CURRENT * 100 / TOTAL))
echo "Progress: $CURRENT / $TOTAL ($PERCENT%)"
```

### **Watch Progress in Real-Time**
```bash
# Update every 10 seconds
watch -n 10 'grep -E "(current_index|stats)" /volume1/photo/.photo_rename_checkpoint.json'
```

---

## 🛠️ Common Workflows

### **Workflow 1: Long-Running Background Job**

```bash
# SSH into Synology
ssh admin@your-synology

# Start screen session
screen -S photo_rename

# Run with checkpoints
./synology_rename_photos_with_checkpoint.py --yes

# Detach: Ctrl+A, D
# Disconnect SSH

# Later: Check progress
ssh admin@your-synology
screen -r photo_rename
```

---

### **Workflow 2: Overnight Processing**

```bash
# Start in evening
nohup ./synology_rename_photos_with_checkpoint.py --yes \
  > /volume1/logs/rename_overnight.log 2>&1 &

# Next morning: Check results
tail -100 /volume1/logs/rename_overnight.log

# If still running, reconnect with screen
screen -r photo_rename
```

---

### **Workflow 3: Process by Directory with Checkpoints**

For better control and smaller checkpoints:

```bash
#!/bin/bash
# process_all_years.sh

for year in 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
  echo "Processing $year..."
  
  ./synology_rename_photos_with_checkpoint.py \
    /volume1/photo/$year \
    --yes \
    --checkpoint-file /volume1/photo/$year/.checkpoint.json \
    >> /volume1/logs/rename_$year.log 2>&1
  
  if [ $? -eq 0 ]; then
    echo "✓ $year completed successfully"
    # Checkpoint auto-deleted on success
  else
    echo "✗ $year had errors - checkpoint saved for resume"
  fi
done

echo "All years processed!"
```

Run in background:
```bash
chmod +x process_all_years.sh
nohup ./process_all_years.sh > /volume1/logs/all_years.log 2>&1 &
```

---

## 🔧 Recovery Scenarios

### **Scenario 1: Script Crashes**

```bash
# Simply run again - it auto-resumes
./synology_rename_photos_with_checkpoint.py --yes

# Or explicitly
./synology_rename_photos_with_checkpoint.py --resume
```

### **Scenario 2: NAS Reboots**

```bash
# After reboot, navigate to directory
cd /volume1/scripts

# Resume from checkpoint
./synology_rename_photos_with_checkpoint.py --resume
```

### **Scenario 3: Want to Start Over**

```bash
# Delete checkpoint
rm /volume1/photo/.photo_rename_checkpoint.json

# Start fresh
./synology_rename_photos_with_checkpoint.py --yes
```

### **Scenario 4: Checkpoint Corrupted**

```bash
# Backup corrupt checkpoint
mv /volume1/photo/.photo_rename_checkpoint.json \
   /volume1/photo/.photo_rename_checkpoint.json.corrupt

# Start fresh (will skip already-renamed files anyway)
./synology_rename_photos_with_checkpoint.py --yes
```

---

## 📋 Comparison: Old vs New Scripts

| Feature | Old Scripts | New Checkpoint Scripts |
|---------|-------------|----------------------|
| **Survives crashes** | ❌ No | ✅ Yes - auto-resume |
| **Saves progress** | ❌ No | ✅ Every 100 files |
| **Resume support** | ❌ No | ✅ `--resume` flag |
| **Background ready** | ⚠️ Partial | ✅ Fully compatible |
| **Progress tracking** | ⚠️ Logs only | ✅ Checkpoint file + logs |
| **Atomic saves** | ❌ No | ✅ Yes (temp file → rename) |
| **Stats tracking** | ⚠️ End only | ✅ Real-time in checkpoint |
| **Duplicate detection** | ⚠️ No | ✅ Checks if already processed |

---

## ⚙️ Advanced Options

### **Custom Checkpoint Frequency**

To save more/less frequently, edit the script:

```python
# In CheckpointManager class
def should_save(self):
    # Change 100 to desired number
    return self.data['current_index'] % 50 == 0  # Save every 50 files
```

### **Multiple Parallel Jobs**

Process different directories in parallel:

```bash
# Terminal 1
screen -S photos_2020
./synology_rename_photos_with_checkpoint.py /volume1/photo/2020 --yes
# Ctrl+A, D

# Terminal 2
screen -S photos_2021
./synology_rename_photos_with_checkpoint.py /volume1/photo/2021 --yes
# Ctrl+A, D

# Each has its own checkpoint!
```

---

## 🎯 Best Practices

### ✅ **Do:**
1. **Use `screen` or `tmux`** for long jobs
2. **Check checkpoint location** before starting
3. **Monitor initial progress** (first 100 files) before detaching
4. **Keep checkpoint files** until job completes
5. **Use `--dry-run` first** to test
6. **Process by directory** for better control

### ❌ **Don't:**
1. **Don't delete checkpoint** while running
2. **Don't run multiple jobs** on same directory (same checkpoint file)
3. **Don't modify checkpoint** manually
4. **Don't assume success** without checking logs
5. **Don't forget to resume** after interruption

---

## 📞 Quick Reference

```bash
# START WITH CHECKPOINT
./synology_rename_photos_with_checkpoint.py --yes

# RESUME AFTER INTERRUPTION
./synology_rename_photos_with_checkpoint.py --resume

# BACKGROUND (survives SSH disconnect)
screen -S rename
./synology_rename_photos_with_checkpoint.py --yes
# Ctrl+A, D

# CHECK PROGRESS
grep current_index /volume1/photo/.photo_rename_checkpoint.json

# RECONNECT TO SCREEN
screen -r rename

# VIEW LOGS
tail -f /volume1/logs/rename.log

# START OVER (delete checkpoint)
rm /volume1/photo/.photo_rename_checkpoint.json
```

---

## 🎉 Summary

**You now have:**
- ✅ Checkpoint system (saves every 100 files)
- ✅ Auto-resume capability
- ✅ Background execution ready
- ✅ Crash recovery
- ✅ Progress tracking
- ✅ SSH disconnect protection

**For your 386K files:**
- Process will save checkpoints regularly
- Can disconnect and reconnect anytime
- If interrupted, just run again to resume
- All progress preserved!

**Dangerous scripts:**
- ✅ Moved to `oldscriptfiles/`
- ✅ Renamed with `-dangerous!-` prefix
- ✅ Old checkpoints backed up
- ✅ Clean workspace!

---

**Ready to run!** Start with a test directory first:

```bash
# Test on small directory first
./synology_rename_photos_with_checkpoint.py /volume1/photo/test --dry-run

# If looks good
./synology_rename_photos_with_checkpoint.py /volume1/photo/test --yes

# Then full library in background
screen -S photo_rename
./synology_rename_photos_with_checkpoint.py --yes
```
