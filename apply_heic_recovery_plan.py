#!/usr/bin/env python3
"""
Apply recovery plan to update HEIC file metadata using exiftool.

WARNING: This DOES modify files. Always test on copies first!
"""

import sys
import csv
import json
import subprocess
from pathlib import Path
from datetime import datetime

def translate_mac_path_to_synology(mac_path):
    """
    Translate Mac paths to Synology paths.
    /Volumes/photo-1/... -> /volume1/photo/...
    """
    if mac_path.startswith('/Volumes/photo-1/'):
        return mac_path.replace('/Volumes/photo-1/', '/volume1/photo/')
    return mac_path

def check_exiftool():
    """Check if exiftool is installed."""
    try:
        result = subprocess.run(['exiftool', '-ver'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False

def parse_date(date_str):
    """Parse date string to datetime."""
    if not date_str or date_str == '':
        return None
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        pass
    
    return None

def update_heic_exif(file_path, new_date, dry_run=False, log_file=None):
    """Update HEIC EXIF metadata using exiftool."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, f"File not found: {file_path}", None
    
    if not file_path.suffix.lower() == '.heic':
        return False, f"Not a HEIC file: {file_path.suffix}", None
    
    # Format date for exiftool (YYYY:MM:DD HH:MM:SS)
    date_str = new_date.strftime("%Y:%m:%d %H:%M:%S")
    
    if dry_run:
        message = f"[DRY RUN] Would update {file_path.name} to {date_str}"
        if log_file:
            log_file.write(f"{message}\n")
        return True, message, None
    
    try:
        # Backup current EXIF first
        backup_result = subprocess.run(
            ['exiftool', '-s', '-j', str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        backup_data = None
        if backup_result.returncode == 0:
            try:
                backup_data = json.loads(backup_result.stdout)[0] if backup_result.stdout else None
            except:
                pass
        
        # Update EXIF tags
        # DateTimeOriginal, DateTimeDigitized, CreateDate, ModifyDate
        exiftool_cmd = [
            'exiftool',
            '-overwrite_original',
            f'-DateTimeOriginal={date_str}',
            f'-DateTimeDigitized={date_str}',
            f'-CreateDate={date_str}',
            f'-ModifyDate={date_str}',
            str(file_path)
        ]
        
        result = subprocess.run(
            exiftool_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            message = f"✓ Updated {file_path.name} to {date_str}"
            if log_file:
                log_file.write(f"{message}\n")
                log_file.write(f"  Old EXIF: {backup_data.get('DateTimeOriginal', 'N/A') if backup_data else 'N/A'}\n")
                log_file.write(f"  New date: {date_str}\n\n")
                log_file.flush()
            
            return True, message, backup_data
        else:
            error_msg = f"✗ Error updating {file_path.name}: {result.stderr.strip()}"
            if log_file:
                log_file.write(f"{error_msg}\n\n")
                log_file.flush()
            return False, error_msg, backup_data
            
    except subprocess.TimeoutExpired:
        error_msg = f"✗ Timeout updating {file_path.name}"
        if log_file:
            log_file.write(f"{error_msg}\n\n")
            log_file.flush()
        return False, error_msg, None
    except Exception as e:
        error_msg = f"✗ Error updating {file_path.name}: {str(e)}"
        if log_file:
            log_file.write(f"{error_msg}\n\n")
            log_file.flush()
        return False, error_msg, None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Apply recovery plan to update HEIC metadata (MODIFIES FILES!)'
    )
    parser.add_argument('--plan', default='recovery_plan_heic_only.csv',
                       help='Path to HEIC recovery plan CSV')
    parser.add_argument('--confidence', default='HIGH',
                       choices=['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW'],
                       help='Minimum confidence level (default: HIGH)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int,
                       help='Limit number of files (for testing)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm without prompting')
    parser.add_argument('--log-file', default='logs/heic_recovery_apply.log',
                       help='Log file for changes')
    parser.add_argument('--undo-file', default='undo_heic_recovery.json',
                       help='Undo information file')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"HEIC RECOVERY PLAN APPLIER")
    print(f"{'='*80}")
    print(f"Plan: {args.plan}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Min Confidence: {args.confidence}")
    if args.limit:
        print(f"Limit: {args.limit} files")
    print(f"Log: {args.log_file}")
    print(f"Undo: {args.undo_file}")
    print(f"{'='*80}\n")
    
    # Check exiftool
    if not check_exiftool():
        print("❌ ERROR: exiftool not found!")
        print("Install exiftool:")
        print("  macOS: brew install exiftool")
        print("  Synology: See SYNOLOGY_HEIC_GUIDE.md")
        return 1
    
    print("✅ exiftool found\n")
    
    # Load recovery plan
    print("Loading recovery plan...")
    recovery_plan = []
    
    with open(args.plan, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recovery_plan.append(row)
    
    print(f"  Loaded {len(recovery_plan)} entries")
    
    # Check if Mac paths need translation
    mac_paths_found = any('/Volumes/photo-1/' in entry.get('full_path', '') for entry in recovery_plan[:100])
    if mac_paths_found:
        print(f"  ℹ️  Mac paths detected - will auto-translate to Synology paths")
    
    # Filter
    confidence_levels = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'VERY_LOW': 3}
    min_level = confidence_levels[args.confidence]
    
    filtered_plan = [
        entry for entry in recovery_plan
        if confidence_levels.get(entry['confidence'], 99) <= min_level
        and entry.get('date_differs') == 'YES'
    ]
    
    print(f"  After filtering ({args.confidence}+ confidence, needs update): {len(filtered_plan)} entries")
    
    if args.limit:
        filtered_plan = filtered_plan[:args.limit]
        print(f"  Limited to: {args.limit} entries")
    
    if not filtered_plan:
        print("\nNo files to process!")
        return 0
    
    # Show summary
    print(f"\nFiles to update:")
    for conf in ['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']:
        count = sum(1 for e in filtered_plan if e['confidence'] == conf)
        if count > 0:
            print(f"  {conf}: {count} files")
    
    # Show sample
    print(f"\nSample entries (first 5):")
    for entry in filtered_plan[:5]:
        print(f"  {entry['current_filename']}")
        print(f"    Current EXIF: {entry['current_exif_date']}")
        print(f"    Proposed: {entry['proposed_date']}")
        print(f"    Confidence: {entry['confidence']}")
        print()
    
    if len(filtered_plan) > 5:
        print(f"  ... and {len(filtered_plan) - 5} more")
    
    # Confirm
    if not args.yes and not args.dry_run:
        print(f"\n⚠️  WARNING: This will MODIFY {len(filtered_plan)} HEIC files!")
        print(f"Make sure you have backups!")
        response = input(f"\nProceed? Type 'yes' to continue: ").strip().lower()
        if response != 'yes':
            print("Aborted.")
            return 0
    
    # Initialize log
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, 'w', encoding='utf-8')
    log_file.write(f"HEIC Recovery Log - Started: {datetime.now().isoformat()}\n")
    log_file.write("="*80 + "\n\n")
    
    changes = []
    
    # Process files
    print(f"\n{'='*80}")
    print(f"Processing files...")
    print(f"{'='*80}\n")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for idx, entry in enumerate(filtered_plan, 1):
        file_path = entry['full_path']
        # Translate Mac paths to Synology paths
        file_path = translate_mac_path_to_synology(file_path)
        proposed_date_str = entry['proposed_date']
        
        new_date = parse_date(proposed_date_str)
        if not new_date:
            print(f"[{idx}/{len(filtered_plan)}] ✗ Invalid date: {proposed_date_str}")
            error_count += 1
            continue
        
        if new_date.year < 2001 or new_date.year > 2025:
            print(f"[{idx}/{len(filtered_plan)}] ✗ Date out of range: {new_date.year}")
            skipped_count += 1
            continue
        
        success, message, backup = update_heic_exif(file_path, new_date, dry_run=args.dry_run, log_file=log_file)
        
        print(f"[{idx}/{len(filtered_plan)}] {message}")
        
        if success:
            success_count += 1
            if backup:
                changes.append({
                    'file': str(file_path),
                    'old_exif': backup,
                    'new_date': new_date.strftime("%Y:%m:%d %H:%M:%S"),
                    'timestamp': datetime.now().isoformat()
                })
        else:
            error_count += 1
        
        if idx % 100 == 0 and not args.dry_run:
            # Save undo info periodically
            with open(args.undo_file, 'w') as f:
                json.dump({
                    'created': datetime.now().isoformat(),
                    'changes': changes
                }, f, indent=2)
            print(f"  → Progress saved ({idx}/{len(filtered_plan)})")
    
    # Final save
    if not args.dry_run:
        with open(args.undo_file, 'w') as f:
            json.dump({
                'created': datetime.now().isoformat(),
                'changes': changes
            }, f, indent=2)
    
    log_file.write("\n" + "="*80 + "\n")
    log_file.write(f"HEIC Recovery Log - Ended: {datetime.now().isoformat()}\n")
    log_file.close()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total: {len(filtered_plan)}")
    print(f"Updated: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped: {skipped_count}")
    
    if args.dry_run:
        print(f"\n⚠️  DRY RUN - No files modified")
    else:
        print(f"\n✅ HEIC files updated!")
        print(f"Log: {args.log_file}")
        print(f"Undo: {args.undo_file}")
    
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
