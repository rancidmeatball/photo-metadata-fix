#!/usr/bin/env python3
"""
Parse rename logs to create a recovery database.
Extracts old filename -> new filename mappings and directory locations.
"""

import sys
import re
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def parse_log_file(log_path):
    """
    Parse a rename log and extract all rename operations.
    Returns list of dicts with: {timestamp, old_name, new_name, directory, action}
    """
    renames = []
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        current_dir = None
        current_timestamp = None
        
        for line in f:
            line = line.strip()
            
            # Extract timestamp
            timestamp_match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
            if timestamp_match:
                current_timestamp = timestamp_match.group(1)
            
            # Extract source directory
            if 'Source directory:' in line:
                dir_match = re.search(r'Source directory: (.+)', line)
                if dir_match:
                    current_dir = dir_match.group(1).strip()
            
            # Extract directory from Processing line (for full path)
            if 'Processing:' in line:
                # The next RENAMED line will have the mapping
                pass
            
            # Extract rename operations
            if 'RENAMED:' in line:
                # Format: "RENAMED: old_file.jpg -> new_file.jpg"
                match = re.search(r'RENAMED:\s+(.+?)\s+->\s+(.+)', line)
                if match:
                    old_name = match.group(1).strip()
                    new_name = match.group(2).strip()
                    
                    renames.append({
                        'timestamp': current_timestamp,
                        'old_name': old_name,
                        'new_name': new_name,
                        'directory': current_dir,
                        'action': 'RENAMED'
                    })
            
            # Extract move operations
            if 'MOVED:' in line:
                # Format: "MOVED: file.jpg -> destination/"
                match = re.search(r'MOVED:\s+(.+?)\s+->\s+(.+)', line)
                if match:
                    old_name = match.group(1).strip()
                    destination = match.group(2).strip()
                    
                    renames.append({
                        'timestamp': current_timestamp,
                        'old_name': old_name,
                        'new_name': old_name,  # Filename didn't change, just moved
                        'directory': current_dir,
                        'destination': destination,
                        'action': 'MOVED'
                    })
    
    return renames

def create_recovery_database(renames, output_path):
    """Create a JSON database for recovery."""
    # Group by new filename to handle duplicates
    by_new_name = defaultdict(list)
    
    for r in renames:
        by_new_name[r['new_name']].append(r)
    
    # Create recovery map: new_name -> most recent old_name
    recovery_map = {}
    
    for new_name, rename_list in by_new_name.items():
        # Sort by timestamp (most recent first)
        sorted_renames = sorted(rename_list, key=lambda x: x['timestamp'] or '', reverse=True)
        most_recent = sorted_renames[0]
        
        recovery_map[new_name] = {
            'original_name': most_recent['old_name'],
            'timestamp': most_recent['timestamp'],
            'directory': most_recent['directory'],
            'action': most_recent['action'],
            'history': sorted_renames  # Full history
        }
    
    with open(output_path, 'w') as f:
        json.dump(recovery_map, f, indent=2)
    
    return recovery_map

def create_recovery_csv(renames, output_path):
    """Create a CSV file for easy viewing/editing."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Original Filename', 'New Filename', 'Directory', 'Action'])
        
        for r in renames:
            writer.writerow([
                r['timestamp'],
                r['old_name'],
                r['new_name'],
                r['directory'],
                r['action']
            ])

def analyze_renames(renames):
    """Analyze rename patterns."""
    stats = {
        'total_renames': len(renames),
        'unique_old_names': len(set(r['old_name'] for r in renames)),
        'unique_new_names': len(set(r['new_name'] for r in renames)),
        'directories': len(set(r['directory'] for r in renames if r['directory'])),
        'actions': defaultdict(int)
    }
    
    for r in renames:
        stats['actions'][r['action']] += 1
    
    return stats

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Parse rename logs and create recovery database'
    )
    parser.add_argument('log_files', nargs='+', help='Log files to parse')
    parser.add_argument('--output-dir', default='/Users/john/Cursor/fix_metadata/RECOVERY',
                       help='Output directory for recovery files')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"{'='*80}")
    print(f"RENAME LOG PARSER & RECOVERY DATABASE BUILDER")
    print(f"{'='*80}\n")
    
    all_renames = []
    
    # Parse all log files
    for log_file in args.log_files:
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"WARNING: Log file not found: {log_file}")
            continue
        
        print(f"Parsing: {log_path.name}")
        renames = parse_log_file(log_path)
        print(f"  Found {len(renames)} operations")
        all_renames.extend(renames)
    
    if not all_renames:
        print("\nNo rename operations found in log files!")
        return 1
    
    print(f"\nTotal operations found: {len(all_renames)}")
    
    # Analyze
    print(f"\nAnalyzing...")
    stats = analyze_renames(all_renames)
    
    print(f"\n{'='*80}")
    print(f"STATISTICS")
    print(f"{'='*80}")
    print(f"Total operations: {stats['total_renames']}")
    print(f"Unique original names: {stats['unique_old_names']}")
    print(f"Unique new names: {stats['unique_new_names']}")
    print(f"Directories affected: {stats['directories']}")
    print(f"\nOperations by type:")
    for action, count in stats['actions'].items():
        print(f"  {action}: {count}")
    
    # Create recovery files
    print(f"\n{'='*80}")
    print(f"Creating recovery files...")
    print(f"{'='*80}")
    
    # JSON database
    json_path = output_dir / f"recovery_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"Creating JSON database: {json_path.name}")
    recovery_map = create_recovery_database(all_renames, json_path)
    print(f"  ✓ {len(recovery_map)} filename mappings")
    
    # CSV file
    csv_path = output_dir / f"recovery_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"Creating CSV file: {csv_path.name}")
    create_recovery_csv(all_renames, csv_path)
    print(f"  ✓ {len(all_renames)} operations")
    
    # Create human-readable summary
    summary_path = output_dir / f"recovery_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    print(f"Creating summary: {summary_path.name}")
    
    with open(summary_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("RECOVERY DATABASE SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total operations: {stats['total_renames']}\n")
        f.write(f"Unique files affected: {stats['unique_old_names']}\n")
        f.write(f"Directories: {stats['directories']}\n\n")
        f.write("Operations by type:\n")
        for action, count in stats['actions'].items():
            f.write(f"  {action}: {count}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        f.write("SAMPLE ENTRIES (first 50):\n\n")
        
        for i, r in enumerate(all_renames[:50], 1):
            f.write(f"{i}. [{r['timestamp']}]\n")
            f.write(f"   Original: {r['old_name']}\n")
            f.write(f"   New:      {r['new_name']}\n")
            f.write(f"   Dir:      {r['directory']}\n")
            f.write(f"   Action:   {r['action']}\n\n")
    
    print(f"\n{'='*80}")
    print(f"SUCCESS!")
    print(f"{'='*80}")
    print(f"\nRecovery files created in: {output_dir}")
    print(f"\nFiles created:")
    print(f"  1. {json_path.name} - JSON database for scripts")
    print(f"  2. {csv_path.name} - CSV for Excel/spreadsheet")
    print(f"  3. {summary_path.name} - Human-readable summary")
    print(f"\nYou can now:")
    print(f"  - Open CSV in Excel to search for specific files")
    print(f"  - Use JSON database with recovery scripts")
    print(f"  - Review summary for overview")
    print(f"{'='*80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
