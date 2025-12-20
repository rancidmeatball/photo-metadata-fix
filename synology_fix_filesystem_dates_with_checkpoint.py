#!/usr/bin/env python3
"""
Synology file system date fixer WITH CHECKPOINT/RESUME support.

Updates file system dates (FileModifyDate, FileCreateDate) to match EXIF DateTimeOriginal.
NEVER modifies EXIF metadata - only updates file system dates.

Default: Processes /volume1/photo recursively

FEATURES:
- Checkpoint system: saves progress every 100 files
- Resume support: --resume to continue from last checkpoint
- Crash recovery: automatically resumes if interrupted
- Detailed logging
- Background execution ready
"""

import os
import sys
import json
import subprocess
import threading
import signal
from pathlib import Path
from datetime import datetime

# ============================================================================
# CHECKPOINT SYSTEM
# ============================================================================

class CheckpointManager:
    """Manages checkpoint files for resume capability."""
    
    def __init__(self, checkpoint_path):
        self.checkpoint_path = Path(checkpoint_path)
        self.data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'last_update': None,
            'processed_files': [],
            'current_index': 0,
            'total_files': 0,
            'stats': {
                'updated': 0,
                'skipped_no_exif': 0,
                'skipped_problematic': 0,
                'errors': 0
            }
        }
        
    def load(self):
        """Load existing checkpoint."""
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, 'r') as f:
                    self.data = json.load(f)
                return True
            except:
                return False
        return False
    
    def save(self):
        """Save checkpoint to disk (atomic write)."""
        self.data['last_update'] = datetime.now().isoformat()
        
        # Write to temp file first, then rename (atomic operation)
        temp_path = self.checkpoint_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        temp_path.replace(self.checkpoint_path)
    
    def mark_processed(self, file_path, result, exif_date=None):
        """Mark a file as processed."""
        # Normalize path before storing
        normalized_path = str(Path(file_path).resolve())
        entry = {
            'path': normalized_path,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        if exif_date:
            entry['exif_date'] = exif_date.isoformat()
        
        # Don't add duplicates
        if not any(Path(p['path']).resolve() == Path(normalized_path) for p in self.data['processed_files']):
            self.data['processed_files'].append(entry)
            self.data['current_index'] += 1
        
        # Update stats
        if result == 'updated':
            self.data['stats']['updated'] += 1
        elif result == 'skipped_no_exif':
            self.data['stats']['skipped_no_exif'] += 1
        elif result == 'skipped_problematic':
            self.data['stats']['skipped_problematic'] = self.data['stats'].get('skipped_problematic', 0) + 1
        elif result == 'error':
            self.data['stats']['errors'] += 1
    
    def is_processed(self, file_path):
        """Check if file was already processed."""
        # Normalize path for comparison
        file_str = str(Path(file_path).resolve())
        return any(Path(p['path']).resolve() == Path(file_str) for p in self.data['processed_files'])
    
    def should_save(self):
        """Check if we should save checkpoint (every 100 files)."""
        return len(self.data['processed_files']) % 100 == 0
    
    def get_resume_index(self):
        """Get the index to resume from."""
        return self.data['current_index']
    
    def delete(self):
        """Delete checkpoint file."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()

# ============================================================================
# FILE SYSTEM DATE FIXING
# ============================================================================

def translate_mac_path_to_synology(mac_path):
    """Translate Mac paths to Synology paths."""
    if mac_path.startswith('/Volumes/photo-1/'):
        return mac_path.replace('/Volumes/photo-1/', '/volume1/photo/')
    return mac_path

def get_datetime_original(file_path):
    """Get DateTimeOriginal from file using exiftool."""
    try:
        result = subprocess.run(
            ['exiftool', '-s', '-s', '-s', '-DateTimeOriginal', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            try:
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except:
                pass
    except:
        pass
    return None

def run_exiftool_with_timeout(cmd, timeout_seconds=30):
    """Run exiftool with a hard timeout that actually kills the process."""
    process = None
    timed_out = threading.Event()
    
    def kill_process():
        if process and process.poll() is None:
            try:
                timed_out.set()
                process.kill()
                # Also try to kill any child processes
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except:
                    pass
            except:
                pass
    
    # Try to use setsid if available (Unix only)
    preexec_fn = None
    try:
        if hasattr(os, 'setsid'):
            preexec_fn = os.setsid
    except:
        pass
    
    try:
        popen_kwargs = {
            'cmd': cmd,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True
        }
        if preexec_fn:
            popen_kwargs['preexec_fn'] = preexec_fn
        
        process = subprocess.Popen(**popen_kwargs)
        
        # Set up timeout
        timer = threading.Timer(timeout_seconds, kill_process)
        timer.start()
        
        try:
            # Use communicate with timeout if available (Python 3.3+)
            if hasattr(subprocess.Popen, 'communicate'):
                try:
                    stdout, stderr = process.communicate(timeout=timeout_seconds+5)
                except TypeError:
                    # Python < 3.3 doesn't support timeout in communicate
                    stdout, stderr = process.communicate()
            else:
                stdout, stderr = process.communicate()
        except subprocess.TimeoutExpired:
            # Force kill if communicate times out
            kill_process()
            try:
                process.wait(timeout=2)
            except:
                pass
            raise subprocess.TimeoutExpired(cmd, timeout_seconds)
        finally:
            timer.cancel()
        
        if timed_out.is_set():
            raise subprocess.TimeoutExpired(cmd, timeout_seconds)
        
        return process.returncode, stdout, stderr
        
    except subprocess.TimeoutExpired:
        # Make sure process is dead
        if process and process.poll() is None:
            try:
                process.kill()
                try:
                    process.wait(timeout=2)
                except:
                    pass
            except:
                pass
        raise
    except Exception as e:
        if process:
            try:
                process.kill()
                try:
                    process.wait(timeout=2)
                except:
                    pass
            except:
                pass
        raise e

def update_filesystem_date(file_path, exif_date, dry_run=False, log_file=None):
    """Update file system dates to match EXIF DateTimeOriginal.
    
    ONLY updates file system dates - NEVER touches EXIF metadata.
    Uses robust timeout mechanism to prevent hanging.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, "File not found", None
    
    if not exif_date:
        return False, "No EXIF DateTimeOriginal found", None
    
    if dry_run:
        message = f"[DRY RUN] Would set file system date to {exif_date.strftime('%Y:%m:%d %H:%M:%S')}"
        if log_file:
            log_file.write(f"{message}\n")
            log_file.flush()
        return True, message, exif_date
    
    try:
        # Format date for exiftool: YYYY:mm:dd HH:MM:SS
        date_str = exif_date.strftime("%Y:%m:%d %H:%M:%S")
        
        # Use exiftool to set ONLY file system dates
        # -FileModifyDate: file system modification date
        # -FileCreateDate: file system creation date (if supported)
        # This does NOT modify any EXIF metadata
        # Use robust timeout that actually kills the process
        cmd = [
            'exiftool', '-overwrite_original',
            f'-FileModifyDate={date_str}',
            f'-FileCreateDate={date_str}',
            str(file_path)
        ]
        
        returncode, stdout, stderr = run_exiftool_with_timeout(cmd, timeout_seconds=30)
        
        if returncode == 0:
            message = f"✓ Updated file system date to {date_str}"
            if log_file:
                log_file.write(f"{file_path}: {message}\n")
                log_file.write(f"  EXIF DateTimeOriginal: {date_str}\n")
                log_file.flush()
            return True, message, exif_date
        else:
            error_msg = stderr.strip() if stderr else stdout.strip()
            if "killed" in error_msg.lower() or returncode == -9:
                message = "⚠️  Timeout (30s) - process killed, skipping problematic file"
            else:
                message = f"✗ Error: {error_msg}"
            if log_file:
                log_file.write(f"{file_path}: {message}\n")
                log_file.flush()
            return False, message, None
            
    except subprocess.TimeoutExpired:
        message = "⚠️  Timeout (30s) - skipping problematic file"
        if log_file:
            log_file.write(f"{file_path}: {message}\n")
            log_file.flush()
        return False, message, None
    except Exception as e:
        message = f"⚠️  Exception - skipping problematic file: {str(e)}"
        if log_file:
            log_file.write(f"{file_path}: {message}\n")
            log_file.flush()
        return False, message, None

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix file system dates to match EXIF DateTimeOriginal (with checkpoint)'
    )
    parser.add_argument('directory', nargs='?', default='/volume1/photo',
                       help='Directory containing year-named folders (default: /volume1/photo)')
    parser.add_argument('--checkpoint', default='/volume1/photo/.filesystem_dates_checkpoint.json',
                       help='Checkpoint file path')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last checkpoint')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int,
                       help='Limit number of files (for testing)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm without prompting')
    parser.add_argument('--log-file', default='/volume1/photo/logs/filesystem_dates_fix.log',
                       help='Log file for changes')
    parser.add_argument('--skipped-log', default='/volume1/photo/logs/filesystem_dates_skipped.log',
                       help='Log file for skipped problematic files')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"SYNOLOGY FIX FILESYSTEM DATES (WITH CHECKPOINT)")
    print(f"{'='*80}")
    print(f"Base directory: {args.directory}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Log: {args.log_file}")
    print(f"Note: Only processes year-named folders (2000-2025)")
    if args.limit:
        print(f"Limit: {args.limit} files")
    print(f"{'='*80}\n")
    
    # Check exiftool
    try:
        result = subprocess.run(['exiftool', '-ver'], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("❌ ERROR: exiftool not found!")
            print("Install with: opkg install perl-image-exiftool")
            return 1
    except:
        print("❌ ERROR: exiftool not found!")
        print("Install with: opkg install perl-image-exiftool")
        return 1
    
    print("✅ exiftool found\n")
    
    # Initialize checkpoint manager
    checkpoint = CheckpointManager(args.checkpoint)
    resume_mode = args.resume
    
    if resume_mode:
        if checkpoint.load():
            print(f"✅ Resuming from checkpoint")
            print(f"   Processed: {checkpoint.data['current_index']} files")
            print(f"   Stats: {checkpoint.data['stats']}\n")
        else:
            print("⚠️  No checkpoint found, starting fresh\n")
            resume_mode = False
    
    # Find image files - only in year-named folders
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Directory not found: {args.directory}")
        return 1
    
    # Find year-named folders (2000-2025)
    import re
    year_pattern = re.compile(r'^(200[0-9]|201[0-9]|202[0-5])$')
    year_folders = []
    
    for item in directory.iterdir():
        if item.is_dir() and year_pattern.match(item.name):
            year_folders.append(item)
    
    if not year_folders:
        print(f"❌ No year-named folders found in {args.directory}")
        print(f"   Looking for folders named: 2000-2025")
        return 1
    
    print(f"Found {len(year_folders)} year-named folders:")
    for yf in sorted(year_folders):
        print(f"  - {yf.name}")
    print()
    
    # Find image files only in year-named folders
    # Use find command for faster discovery (avoids Python rglob on huge directories)
    image_extensions = ['.jpg', '.jpeg', '.heic', '.png', '.tiff', '.tif', '.JPG', '.JPEG', '.HEIC']
    all_files = []
    
    print("Discovering files (this may take a while for large directories)...")
    sys.stdout.flush()
    
    # Use find command for faster file discovery
    import tempfile
    find_cmd = ['find']
    for year_folder in year_folders:
        find_cmd.append(str(year_folder))
    find_cmd.extend(['-type', 'f', '-name', '*.jpg', '-o', '-name', '*.jpeg', '-o', 
                     '-name', '*.heic', '-o', '-name', '*.png', '-o', '-name', '*.tiff', 
                     '-o', '-name', '*.tif', '-o', '-name', '*.JPG', '-o', '-name', '*.JPEG', 
                     '-o', '-name', '*.HEIC'])
    
    try:
        result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
        if result.returncode == 0:
            all_files = [Path(f.strip()) for f in result.stdout.split('\n') if f.strip()]
            print(f"Found {len(all_files)} files using find command")
        else:
            # Fallback to Python rglob if find fails
            print("find command failed, using Python rglob (slower)...")
            sys.stdout.flush()
            for year_folder in year_folders:
                for ext in image_extensions:
                    files = list(year_folder.rglob(f'*{ext}'))
                    all_files.extend(files)
                    if len(all_files) % 10000 == 0:
                        print(f"  Discovered {len(all_files)} files so far...")
                        sys.stdout.flush()
    except subprocess.TimeoutExpired:
        print("⚠️  File discovery timed out after 5 minutes")
        print("   Using checkpoint to resume from last known position...")
        if resume_mode and checkpoint.data.get('processed_files'):
            # Use files from checkpoint to continue
            processed_paths = {Path(p['path']) for p in checkpoint.data['processed_files']}
            # Try to discover files incrementally
            print("   Attempting incremental file discovery...")
            sys.stdout.flush()
            # Just use the checkpoint's file list if available
            if checkpoint.data.get('all_files'):
                all_files = [Path(f) for f in checkpoint.data['all_files']]
            else:
                print("❌ Cannot continue without file list")
                return 1
    except Exception as e:
        print(f"⚠️  Error during file discovery: {e}")
        print("   Falling back to Python rglob...")
        sys.stdout.flush()
        for year_folder in year_folders:
            for ext in image_extensions:
                files = list(year_folder.rglob(f'*{ext}'))
                all_files.extend(files)
                if len(all_files) % 10000 == 0:
                    print(f"  Discovered {len(all_files)} files so far...")
                    sys.stdout.flush()
    
    if not all_files:
        print(f"❌ No image files found in {args.directory}")
        return 1
    
    # Save file list to checkpoint for faster resume
    if not resume_mode:
        checkpoint.data['all_files'] = [str(f) for f in all_files]
    
    # Filter out already processed files if resuming
    if resume_mode:
        files_to_process = [f for f in all_files if not checkpoint.is_processed(f)]
        print(f"Found {len(all_files)} total files")
        print(f"Already processed: {len(all_files) - len(files_to_process)}")
        print(f"Remaining: {len(files_to_process)} files\n")
    else:
        files_to_process = all_files
        checkpoint.data['total_files'] = len(files_to_process)
        print(f"Found {len(files_to_process)} image files\n")
    
    if args.limit:
        files_to_process = files_to_process[:args.limit]
        print(f"Limited to: {len(files_to_process)} files\n")
    
    if not files_to_process:
        print("✅ All files already processed!")
        return 0
    
    # Confirm
    if not args.yes and not args.dry_run:
        print(f"\n⚠️  WARNING: This will modify file system dates for {len(files_to_process)} files!")
        print(f"EXIF metadata will NOT be modified - only file system dates.")
        print(f"Make sure you have backups!")
        response = input(f"\nProceed? Type 'yes' to continue: ").strip().lower()
        if response != 'yes':
            print("Aborted.")
            return 0
    
    # Initialize log
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, 'a', encoding='utf-8')  # Append mode for resume
    log_file.write(f"\n{'='*80}\n")
    log_file.write(f"File System Dates Fix - Started: {datetime.now().isoformat()}\n")
    if resume_mode:
        log_file.write(f"Resuming from checkpoint: {checkpoint.data['current_index']} files processed\n")
    log_file.write("="*80 + "\n\n")
    
    # Initialize skipped files log
    skipped_log_path = Path(args.skipped_log)
    skipped_log_path.parent.mkdir(parents=True, exist_ok=True)
    skipped_log_file = open(skipped_log_path, 'a', encoding='utf-8')  # Append mode
    skipped_log_file.write(f"\n{'='*80}\n")
    skipped_log_file.write(f"Skipped Problematic Files - Started: {datetime.now().isoformat()}\n")
    skipped_log_file.write("="*80 + "\n\n")
    
    # Process files
    print(f"\n{'='*80}")
    print(f"Processing files...")
    print(f"{'='*80}\n")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    skipped_problematic_count = 0
    
    try:
        for idx, file_path in enumerate(files_to_process, 1):
            # Skip if already processed (safety check)
            if checkpoint.is_processed(file_path):
                continue
            
            # Log which file we're processing (ALWAYS log for stuck file detection)
            log_file.write(f"Processing [{idx}/{len(files_to_process)}]: {file_path}\n")
            log_file.flush()
            
            try:
                # Get EXIF date (with timeout protection)
                exif_date = get_datetime_original(file_path)
                
                if not exif_date:
                    checkpoint.mark_processed(file_path, 'skipped_no_exif')
                    skipped_count += 1
                    if idx <= 10:  # Show first 10 skipped
                        print(f"[{idx}/{len(files_to_process)}] ⚠️  {file_path.name}: No EXIF DateTimeOriginal")
                    continue
                
                # Update file system date (has 30 second timeout)
                success, message, date_used = update_filesystem_date(
                    file_path, exif_date, dry_run=args.dry_run, log_file=log_file
                )
                
                if success:
                    checkpoint.mark_processed(file_path, 'updated', exif_date)
                    if idx <= 20 or idx % 100 == 0:
                        print(f"[{idx}/{len(files_to_process)}] {message}")
                    success_count += 1
                else:
                    # Check if it's a timeout or problematic file
                    if "Timeout" in message or "Exception" in message or "skipping problematic" in message:
                        # Mark as skipped_problematic and log to skipped file
                        checkpoint.mark_processed(file_path, 'skipped_problematic')
                        skipped_problematic_count += 1
                        skipped_log_file.write(f"{file_path}\n")
                        skipped_log_file.write(f"  Reason: {message}\n")
                        skipped_log_file.write(f"  Timestamp: {datetime.now().isoformat()}\n\n")
                        skipped_log_file.flush()
                        log_file.write(f"SKIPPED [{idx}/{len(files_to_process)}]: {file_path} - {message}\n")
                        log_file.flush()
                        if skipped_problematic_count <= 10:  # Show first 10 skipped
                            print(f"[{idx}/{len(files_to_process)}] ⚠️  SKIPPED: {file_path.name} - {message}")
                    else:
                        # Regular error
                        checkpoint.mark_processed(file_path, 'error')
                        log_file.write(f"ERROR [{idx}/{len(files_to_process)}]: {file_path} - {message}\n")
                        log_file.flush()
                        if error_count < 10:  # Show first 10 errors
                            print(f"[{idx}/{len(files_to_process)}] {message}")
                        error_count += 1
                        
            except Exception as e:
                # Catch any unexpected exceptions and skip the file
                error_msg = f"Exception processing {file_path}: {str(e)}"
                log_file.write(f"EXCEPTION [{idx}/{len(files_to_process)}]: {error_msg}\n")
                log_file.flush()
                checkpoint.mark_processed(file_path, 'skipped_problematic')
                skipped_problematic_count += 1
                skipped_log_file.write(f"{file_path}\n")
                skipped_log_file.write(f"  Reason: Exception - {str(e)}\n")
                skipped_log_file.write(f"  Timestamp: {datetime.now().isoformat()}\n\n")
                skipped_log_file.flush()
                if skipped_problematic_count <= 10:
                    print(f"[{idx}/{len(files_to_process)}] ⚠️  SKIPPED (Exception): {file_path.name}")
            
            # Save checkpoint periodically
            if checkpoint.should_save() and not args.dry_run:
                checkpoint.save()
                print(f"  → Checkpoint saved ({idx}/{len(files_to_process)})")
        
        # Final checkpoint save
        if not args.dry_run:
            checkpoint.save()
            print(f"\n✅ Final checkpoint saved")
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted by user")
        if not args.dry_run:
            checkpoint.save()
            print(f"✅ Checkpoint saved - use --resume to continue")
        log_file.write(f"\nInterrupted at: {datetime.now().isoformat()}\n")
        log_file.close()
        return 1
    
    log_file.write("\n" + "="*80 + "\n")
    log_file.write(f"File System Dates Fix - Ended: {datetime.now().isoformat()}\n")
    log_file.write(f"Total: {len(files_to_process)}, Updated: {success_count}, Errors: {error_count}, Skipped (no EXIF): {skipped_count}, Skipped (problematic): {skipped_problematic_count}\n")
    log_file.close()
    
    skipped_log_file.write("\n" + "="*80 + "\n")
    skipped_log_file.write(f"Skipped Problematic Files - Ended: {datetime.now().isoformat()}\n")
    skipped_log_file.write(f"Total skipped: {skipped_problematic_count} files\n")
    skipped_log_file.close()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total files: {len(files_to_process)}")
    print(f"Updated: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped (no EXIF): {skipped_count}")
    print(f"Skipped (problematic): {skipped_problematic_count}")
    print(f"Skipped files log: {args.skipped_log}")
    
    if args.dry_run:
        print(f"\n⚠️  DRY RUN - No files modified")
    else:
        print(f"\n✅ File system dates updated!")
        print(f"   Checkpoint: {args.checkpoint}")
        print(f"   Log: {args.log_file}")
        print(f"   Next step: Re-index Synology Photos (Settings → Rebuild Index)")
    
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
