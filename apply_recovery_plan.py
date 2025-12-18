#!/usr/bin/env python3
"""
Safe Recovery Plan Applier - Phase 2

Applies a pre-approved recovery plan to update file metadata.
Includes multiple safety features:
- Backup original EXIF before changes
- Dry-run mode
- Confidence level filtering
- Detailed logging
- Undo capability

WARNING: This DOES modify files. Always test on copies first!
"""

import sys
import csv
import json
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

class SafeEXIFUpdater:
    """Safely updates EXIF metadata with backup and logging."""
    
    def __init__(self, log_file, backup_dir=None):
        self.log_file = Path(log_file)
        self.backup_dir = Path(backup_dir) if backup_dir else None
        self.changes = []
        
        if self.backup_dir:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Open log file
        self.log = open(self.log_file, 'w', encoding='utf-8')
        self.log.write(f"Recovery Log - Started: {datetime.now().isoformat()}\n")
        self.log.write("="*80 + "\n\n")
    
    def backup_exif(self, file_path):
        """Backup current EXIF data before changes."""
        try:
            img = Image.open(file_path)
            exif = img.getexif()
            
            backup_data = {
                'file': str(file_path),
                'timestamp': datetime.now().isoformat(),
                'exif': {}
            }
            
            # Save key date fields
            for tag_id in [306, 36867, 36868]:  # DateTime, DateTimeOriginal, DateTimeDigitized
                if tag_id in exif:
                    tag_name = TAGS.get(tag_id, tag_id)
                    backup_data['exif'][tag_name] = str(exif[tag_id])
            
            return backup_data
        except Exception as e:
            return {'error': str(e)}
    
    def update_exif(self, file_path, new_date, dry_run=False):
        """
        Update EXIF metadata with new date.
        Returns: (success, message, backup_data)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, f"File not found: {file_path}", None
        
        # Check file extension
        if file_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
            return False, f"Unsupported file type: {file_path.suffix}", None
        
        # Backup current EXIF
        backup_data = self.backup_exif(file_path)
        
        if dry_run:
            message = f"[DRY RUN] Would update {file_path.name} to {new_date}"
            self.log.write(f"{message}\n")
            self.log.write(f"  Current EXIF: {backup_data.get('exif', {})}\n")
            self.log.write(f"  New date: {new_date}\n\n")
            return True, message, backup_data
        
        try:
            # Format date for EXIF
            date_str = new_date.strftime("%Y:%m:%d %H:%M:%S")
            
            # Update EXIF
            img = Image.open(file_path)
            exif_dict = img.getexif()
            
            # Update date fields
            exif_dict[306] = date_str      # DateTime
            exif_dict[36867] = date_str    # DateTimeOriginal
            exif_dict[36868] = date_str    # DateTimeDigitized
            
            # Save with updated EXIF
            img.save(file_path, exif=exif_dict)
            
            # Log success
            message = f"✓ Updated {file_path.name} to {date_str}"
            self.log.write(f"{message}\n")
            self.log.write(f"  Old EXIF: {backup_data.get('exif', {})}\n")
            self.log.write(f"  New date: {date_str}\n\n")
            self.log.flush()
            
            # Save change record
            self.changes.append({
                'file': str(file_path),
                'old_exif': backup_data.get('exif', {}),
                'new_date': date_str,
                'timestamp': datetime.now().isoformat()
            })
            
            return True, message, backup_data
            
        except Exception as e:
            message = f"✗ Error updating {file_path.name}: {str(e)}"
            self.log.write(f"{message}\n\n")
            self.log.flush()
            return False, message, backup_data
    
    def save_undo_script(self, undo_file='undo_recovery.json'):
        """Save undo information."""
        with open(undo_file, 'w') as f:
            json.dump({
                'created': datetime.now().isoformat(),
                'changes': self.changes
            }, f, indent=2)
    
    def close(self):
        """Close log file."""
        self.log.write("\n" + "="*80 + "\n")
        self.log.write(f"Recovery Log - Ended: {datetime.now().isoformat()}\n")
        self.log.close()

def parse_date(date_str):
    """Parse date string to datetime."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        pass
    
    return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Apply recovery plan to update file metadata (MODIFIES FILES!)'
    )
    parser.add_argument('--plan', required=True,
                       help='Path to recovery_plan.csv')
    parser.add_argument('--confidence', default='HIGH',
                       choices=['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW'],
                       help='Minimum confidence level to apply (default: HIGH)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int,
                       help='Limit number of files to process (for testing)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm without prompting')
    parser.add_argument('--log-file', default='recovery_apply.log',
                       help='Log file for changes (default: recovery_apply.log)')
    parser.add_argument('--backup-dir',
                       help='Directory to backup original files (optional)')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"SAFE RECOVERY PLAN APPLIER")
    print(f"{'='*80}")
    print(f"Plan: {args.plan}")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE (will modify files)'}")
    print(f"Min Confidence: {args.confidence}")
    if args.limit:
        print(f"Limit: {args.limit} files")
    print(f"Log: {args.log_file}")
    if args.backup_dir:
        print(f"Backup: {args.backup_dir}")
    print(f"{'='*80}\n")
    
    # Load recovery plan
    print("Loading recovery plan...")
    recovery_plan = []
    
    with open(args.plan, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recovery_plan.append(row)
    
    print(f"  Loaded {len(recovery_plan)} entries")
    
    # Filter by confidence
    confidence_levels = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'VERY_LOW': 3}
    min_level = confidence_levels[args.confidence]
    
    filtered_plan = [
        entry for entry in recovery_plan
        if confidence_levels.get(entry['confidence'], 99) <= min_level
        and entry.get('date_differs') == 'YES'  # Only update if date actually differs
    ]
    
    print(f"  After filtering ({args.confidence}+ confidence, dates differ): {len(filtered_plan)} entries")
    
    if args.limit:
        filtered_plan = filtered_plan[:args.limit]
        print(f"  Limited to: {args.limit} entries")
    
    if not filtered_plan:
        print("\nNo files to process!")
        return 0
    
    # Show summary
    print(f"\nFiles to update:")
    confidence_counts = {}
    for entry in filtered_plan:
        conf = entry['confidence']
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
    
    for conf, count in sorted(confidence_counts.items()):
        print(f"  {conf}: {count} files")
    
    # Show sample
    print(f"\nSample entries:")
    for entry in filtered_plan[:5]:
        print(f"  {entry['current_filename']}")
        print(f"    Current EXIF: {entry['current_exif_date']}")
        print(f"    Proposed: {entry['proposed_date']}")
        print(f"    Confidence: {entry['confidence']}")
        print(f"    Reason: {entry['reasoning'][:80]}...")
        print()
    
    if len(filtered_plan) > 5:
        print(f"  ... and {len(filtered_plan) - 5} more")
    
    # Confirm
    if not args.yes and not args.dry_run:
        print(f"\n⚠️  WARNING: This will MODIFY {len(filtered_plan)} files!")
        print(f"Make sure you have backups before proceeding.")
        response = input(f"\nProceed with updating {len(filtered_plan)} files? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Aborted.")
            return 0
    
    # Initialize updater
    updater = SafeEXIFUpdater(args.log_file, args.backup_dir)
    
    # Process files
    print(f"\n{'='*80}")
    print(f"Processing files...")
    print(f"{'='*80}\n")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for idx, entry in enumerate(filtered_plan, 1):
        file_path = entry['full_path']
        proposed_date_str = entry['proposed_date']
        
        # Parse date
        new_date = parse_date(proposed_date_str)
        if not new_date:
            print(f"[{idx}/{len(filtered_plan)}] ✗ Invalid date: {proposed_date_str}")
            error_count += 1
            continue
        
        # Validate date range
        if new_date.year < 2001 or new_date.year > 2025:
            print(f"[{idx}/{len(filtered_plan)}] ✗ Date out of range: {new_date.year}")
            skipped_count += 1
            continue
        
        # Update EXIF
        success, message, backup = updater.update_exif(file_path, new_date, dry_run=args.dry_run)
        
        print(f"[{idx}/{len(filtered_plan)}] {message}")
        
        if success:
            success_count += 1
        else:
            error_count += 1
        
        # Save progress every 100 files
        if idx % 100 == 0:
            updater.save_undo_script()
            print(f"  → Progress saved (processed {idx}/{len(filtered_plan)})")
    
    # Save final undo script
    if not args.dry_run:
        updater.save_undo_script()
    
    updater.close()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total processed: {len(filtered_plan)}")
    print(f"Successfully updated: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped: {skipped_count}")
    
    if args.dry_run:
        print(f"\n⚠️  DRY RUN MODE - No files were modified")
        print(f"Run without --dry-run to apply changes")
    else:
        print(f"\n✅ Files updated successfully!")
        print(f"Log file: {args.log_file}")
        print(f"Undo info: undo_recovery.json")
    
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
