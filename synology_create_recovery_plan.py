#!/usr/bin/env python3
"""
Synology-optimized Safe Recovery Plan Creator - Phase 1 (READ ONLY)

Creates recovery plan for Synology NAS.
Default paths: /volume1/photo

DOES NOT modify any files - only creates a plan for review.
"""

import sys
import csv
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def extract_date_from_filename(filename):
    """Extract date from various filename patterns."""
    # Pattern 1: IMG_yyyyMMdd_HHmmss or MOV_yyyyMMdd_HHmmss
    pattern1 = r'(?:IMG|MOV)_?(\d{4})(\d{2})(\d{2})_?(\d{2})(\d{2})(\d{2})'
    match = re.search(pattern1, filename, re.IGNORECASE)
    if match:
        try:
            year, month, day, hour, minute, second = map(int, match.groups())
            if 2001 <= year <= 2025:
                return datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass
    
    # Pattern 2: IMGyyyyMMdd_HHmmss (no underscore after IMG)
    pattern2 = r'(?:IMG|MOV)(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
    match = re.search(pattern2, filename, re.IGNORECASE)
    if match:
        try:
            year, month, day, hour, minute, second = map(int, match.groups())
            if 2001 <= year <= 2025:
                return datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass
    
    # Pattern 3: Date only
    pattern3 = r'(?:IMG|MOV)_?(\d{4})(\d{2})(\d{2})'
    match = re.search(pattern3, filename, re.IGNORECASE)
    if match:
        try:
            year, month, day = map(int, match.groups())
            if 2001 <= year <= 2025:
                return datetime(year, month, day, 12, 0, 0)
        except ValueError:
            pass
    
    return None

def extract_year_from_path(directory):
    """Extract year from directory path."""
    match = re.search(r'/(201[0-9]|202[0-5])/?', directory)
    if match:
        return int(match.group(1))
    return None

def parse_date_string(date_str):
    """Parse ISO date string."""
    if not date_str or date_str == '':
        return None
    
    try:
        return datetime.fromisoformat(date_str)
    except:
        pass
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def calculate_confidence(old_date, dir_year, modified_date, exif_date):
    """Calculate confidence level based on agreement between sources."""
    reasons = []
    agreements = 0
    
    if old_date and dir_year:
        if old_date.year == dir_year:
            agreements += 1
            reasons.append(f"Old filename year ({old_date.year}) matches directory ({dir_year})")
        else:
            reasons.append(f"WARNING: Old filename year ({old_date.year}) ≠ directory ({dir_year})")
    
    if old_date and modified_date:
        if old_date.date() == modified_date.date():
            agreements += 1
            reasons.append(f"Old filename date matches File Modified date")
        elif old_date.year == modified_date.year and old_date.month == modified_date.month:
            agreements += 0.5
            reasons.append(f"Old filename year+month matches File Modified")
    
    if dir_year and modified_date:
        if dir_year == modified_date.year:
            agreements += 1
            reasons.append(f"Directory year ({dir_year}) matches File Modified year")
    
    if exif_date:
        if exif_date.year > 2025 or exif_date.year < 2001:
            reasons.append(f"Current EXIF date ({exif_date.year}) is invalid")
        elif old_date and abs((exif_date - old_date).days) > 365:
            reasons.append(f"Current EXIF differs from old filename by {abs((exif_date - old_date).days)} days")
    
    if agreements >= 2.5:
        confidence = "HIGH"
    elif agreements >= 1.5:
        confidence = "MEDIUM"
    elif agreements >= 0.5:
        confidence = "LOW"
    else:
        confidence = "VERY_LOW"
    
    return confidence, "; ".join(reasons)

def translate_mac_path_to_synology(mac_path):
    """
    Translate Mac paths to Synology paths.
    /Volumes/photo-1/... -> /volume1/photo/...
    """
    if mac_path.startswith('/Volumes/photo-1/'):
        return mac_path.replace('/Volumes/photo-1/', '/volume1/photo/')
    return mac_path

def load_recovery_database(csv_path):
    """Load the recovery database."""
    recovery_map = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            old_name = row['Original Filename']
            new_name = row['New Filename']
            recovery_map[new_name] = {
                'old_name': old_name,
                'timestamp': row.get('Timestamp', ''),
                'directory': row.get('Directory', '')
            }
    
    return recovery_map

def load_state_capture(csv_path):
    """Load the current state capture."""
    state_map = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['Filename']
            # Translate Mac paths to Synology paths
            full_path = translate_mac_path_to_synology(row['Full Path'])
            directory = translate_mac_path_to_synology(row['Directory'])
            
            state_map[filename] = {
                'full_path': full_path,
                'directory': directory,
                'relative_directory': row['Relative Directory'],
                'file_created': row.get('File Created', ''),
                'file_modified': row.get('File Modified', ''),
                'exif_original': row.get('EXIF DateTimeOriginal', ''),
                'exif_digitized': row.get('EXIF DateTimeDigitized', ''),
                'exif_datetime': row.get('EXIF DateTime', ''),
                'extension': Path(filename).suffix.lower()
            }
    
    return state_map

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create safe recovery plan for Synology NAS (READ ONLY)'
    )
    parser.add_argument('--recovery-db', default='/volume1/photo/RECOVERY/recovery_list.csv',
                       help='Path to recovery_list_*.csv')
    parser.add_argument('--state-capture', default='/volume1/photo/STATE_BACKUPS/file_state.csv',
                       help='Path to file_state_*.csv')
    parser.add_argument('--output', default='/volume1/photo/recovery_plan.csv',
                       help='Output recovery plan CSV')
    parser.add_argument('--jpg-only', action='store_true',
                       help='Only include JPG files (skip HEIC and MOV)')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"SYNOLOGY SAFE RECOVERY PLAN CREATOR (READ ONLY)")
    print(f"{'='*80}")
    print(f"Recovery DB: {args.recovery_db}")
    print(f"State Capture: {args.state_capture}")
    print(f"Output: {args.output}")
    if args.jpg_only:
        print(f"Filter: JPG files only")
    print(f"{'='*80}\n")
    
    # Load data
    print("Loading recovery database...")
    recovery_map = load_recovery_database(args.recovery_db)
    print(f"  Loaded {len(recovery_map)} old→new mappings")
    
    print("Loading state capture...")
    state_map = load_state_capture(args.state_capture)
    print(f"  Loaded {len(state_map)} current file states")
    
    # Check if Mac paths were translated
    with open(args.state_capture, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        sample = f.readline()
        if '/Volumes/photo-1/' in sample:
            print(f"  ℹ️  Mac paths detected - auto-translated to Synology paths")
    
    # Build recovery plan
    print("\nAnalyzing and building recovery plan...")
    recovery_plan = []
    stats = defaultdict(int)
    
    for current_filename, state in state_map.items():
        # Check if we have recovery info
        if current_filename not in recovery_map:
            continue
        
        # JPG only filter
        if args.jpg_only and state.get('extension') not in ['.jpg', '.jpeg']:
            stats['skipped_non_jpg'] += 1
            continue
        
        recovery_info = recovery_map[current_filename]
        old_filename = recovery_info['old_name']
        
        # Extract date from old filename
        old_date = extract_date_from_filename(old_filename)
        if not old_date:
            stats['no_date_in_old_filename'] += 1
            continue
        
        # Extract year from directory
        dir_year = extract_year_from_path(state['relative_directory'])
        
        # Parse File Modified date
        modified_date = parse_date_string(state['file_modified'])
        
        # Parse current EXIF date
        exif_date = None
        for exif_field in ['exif_original', 'exif_digitized', 'exif_datetime']:
            exif_date = parse_date_string(state.get(exif_field, ''))
            if exif_date:
                break
        
        # Calculate confidence
        confidence, reasoning = calculate_confidence(old_date, dir_year, modified_date, exif_date)
        
        stats[f'confidence_{confidence}'] += 1
        
        # Determine if needs updating
        needs_update = False
        if not exif_date:
            needs_update = True
            update_reason = 'No EXIF data'
        elif abs((exif_date - old_date).days) > 1:
            needs_update = True
            update_reason = f'EXIF differs by {abs((exif_date - old_date).days)} days'
        else:
            update_reason = 'EXIF already correct'
        
        # Create recovery plan entry
        plan_entry = {
            'current_filename': current_filename,
            'full_path': state['full_path'],
            'old_filename': old_filename,
            'proposed_date': old_date.strftime('%Y-%m-%d %H:%M:%S'),
            'current_exif_date': exif_date.strftime('%Y-%m-%d %H:%M:%S') if exif_date else 'NONE',
            'directory': state['relative_directory'],
            'dir_year': dir_year if dir_year else 'N/A',
            'file_modified': state['file_modified'],
            'confidence': confidence,
            'reasoning': reasoning,
            'date_differs': 'YES' if needs_update else 'NO',
            'update_reason': update_reason,
            'file_extension': state.get('extension', '')
        }
        
        recovery_plan.append(plan_entry)
    
    # Sort by confidence
    confidence_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'VERY_LOW': 3}
    recovery_plan.sort(key=lambda x: (confidence_order.get(x['confidence'], 99), x['current_filename']))
    
    # Write recovery plan
    print(f"\nWriting recovery plan to: {args.output}")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if recovery_plan:
            fieldnames = recovery_plan[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(recovery_plan)
    
    # Print statistics
    print(f"\n{'='*80}")
    print(f"RECOVERY PLAN STATISTICS")
    print(f"{'='*80}")
    print(f"Total files analyzed: {len(state_map)}")
    print(f"Files with recovery info: {len(recovery_map)}")
    print(f"Files with date in old filename: {len(recovery_plan)}")
    print(f"Files without date in old filename: {stats['no_date_in_old_filename']}")
    if args.jpg_only:
        print(f"Skipped non-JPG files: {stats['skipped_non_jpg']}")
    
    print(f"\nConfidence Distribution:")
    print(f"  HIGH confidence: {stats['confidence_HIGH']}")
    print(f"  MEDIUM confidence: {stats['confidence_MEDIUM']}")
    print(f"  LOW confidence: {stats['confidence_LOW']}")
    print(f"  VERY_LOW confidence: {stats['confidence_VERY_LOW']}")
    
    # Count files needing updates
    need_update = sum(1 for entry in recovery_plan if entry['date_differs'] == 'YES')
    need_update_high = sum(1 for entry in recovery_plan if entry['date_differs'] == 'YES' and entry['confidence'] == 'HIGH')
    
    print(f"\nFiles Needing Updates:")
    print(f"  Total: {need_update}")
    print(f"  HIGH confidence: {need_update_high} (SAFE TO UPDATE!)")
    
    print(f"\nRecovery plan created: {args.output}")
    print(f"{'='*80}")
    print(f"\n✅ NEXT STEPS:")
    print(f"1. Download {args.output} and open in Excel")
    print(f"2. Review HIGH confidence entries with date_differs=YES")
    print(f"3. Edit/filter as needed")
    print(f"4. Upload edited CSV back to Synology")
    print(f"5. Use synology_apply_recovery_plan.py to update metadata")
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
