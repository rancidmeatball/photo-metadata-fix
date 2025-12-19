#!/usr/bin/env python3
"""
Create HEIC-only recovery plan from main recovery plan.

Filters for HEIC files that need metadata updates.
"""

import sys
import csv
from pathlib import Path

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create HEIC-only recovery plan'
    )
    parser.add_argument('--input', default='recovery_plan.csv',
                       help='Input recovery plan CSV')
    parser.add_argument('--output', default='recovery_plan_heic_only.csv',
                       help='Output HEIC-only CSV')
    parser.add_argument('--confidence', default='HIGH',
                       choices=['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW'],
                       help='Minimum confidence level (default: HIGH)')
    parser.add_argument('--needs-update', action='store_true', default=True,
                       help='Only include files that need updates (date_differs=YES)')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print(f"HEIC RECOVERY PLAN CREATOR")
    print(f"{'='*80}")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Min Confidence: {args.confidence}")
    print(f"Only needs update: {args.needs_update}")
    print(f"{'='*80}\n")
    
    # Load recovery plan
    print("Loading recovery plan...")
    heic_entries = []
    total_heic = 0
    confidence_levels = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'VERY_LOW': 3}
    min_level = confidence_levels[args.confidence]
    
    with open(args.input, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check if HEIC file
            filename = row.get('current_filename', '')
            if filename.lower().endswith('.heic'):
                total_heic += 1
                
                # Filter by confidence
                conf = row.get('confidence', 'VERY_LOW')
                if confidence_levels.get(conf, 99) > min_level:
                    continue
                
                # Filter by needs update
                if args.needs_update and row.get('date_differs') != 'YES':
                    continue
                
                heic_entries.append(row)
    
    print(f"  Total HEIC files in plan: {total_heic}")
    print(f"  HEIC files matching criteria: {len(heic_entries)}")
    
    # Write filtered CSV
    if heic_entries:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = heic_entries[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(heic_entries)
        
        # Statistics
        by_confidence = {}
        by_update_reason = {}
        no_exif = 0
        
        for entry in heic_entries:
            conf = entry.get('confidence', 'UNKNOWN')
            by_confidence[conf] = by_confidence.get(conf, 0) + 1
            
            reason = entry.get('update_reason', 'UNKNOWN')
            by_update_reason[reason] = by_update_reason.get(reason, 0) + 1
            
            if entry.get('current_exif_date') == 'NONE':
                no_exif += 1
        
        print(f"\n✅ Created {args.output}")
        print(f"\n📊 Statistics:")
        print(f"   Total HEIC entries: {len(heic_entries)}")
        print(f"\n   By confidence:")
        for conf in ['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']:
            if conf in by_confidence:
                print(f"     {conf}: {by_confidence[conf]}")
        
        print(f"\n   By update reason:")
        for reason, count in sorted(by_update_reason.items(), key=lambda x: -x[1]):
            print(f"     {reason}: {count}")
        
        print(f"\n   Files with no EXIF: {no_exif}")
        print(f"   Files with existing EXIF: {len(heic_entries) - no_exif}")
        
    else:
        print(f"\n❌ No HEIC files found matching criteria")
        return 1
    
    print(f"\n{'='*80}")
    print(f"✅ Next step: Use apply_heic_recovery_plan.py to update HEIC files")
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
