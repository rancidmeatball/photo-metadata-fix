#!/usr/bin/env python3
"""
Photo/video renamer WITH CHECKPOINT/RESUME support (macOS/Linux version).
NEVER modifies metadata - only renames files based on existing dates.

NEW FEATURES:
- Checkpoint system: saves progress every 100 files
- Resume support: --resume to continue from last checkpoint
- Crash recovery: automatically resumes if interrupted
- Compatible with nohup, screen, tmux for background execution
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

# ============================================================================
# CHECKPOINT SYSTEM (Same as Synology version)
# ============================================================================

class CheckpointManager:
    """Manages checkpoint files for resume capability."""
    
    def __init__(self, checkpoint_path):
        self.checkpoint_path = Path(checkpoint_path)
        self.data = {
            'version': '2.0',
            'created_at': datetime.now().isoformat(),
            'last_update': None,
            'processed_files': [],
            'current_index': 0,
            'total_files': 0,
            'stats': {
                'renamed': 0,
                'already_correct': 0,
                'errors': 0
            }
        }
        
    def load(self):
        """Load existing checkpoint."""
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, 'r') as f:
                self.data = json.load(f)
            return True
        return False
    
    def save(self):
        """Save checkpoint to disk."""
        self.data['last_update'] = datetime.now().isoformat()
        
        temp_path = self.checkpoint_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        temp_path.replace(self.checkpoint_path)
    
    def mark_processed(self, file_path, result):
        """Mark a file as processed."""
        self.data['processed_files'].append({
            'path': str(file_path),
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        self.data['current_index'] += 1
        
        if result == 'renamed':
            self.data['stats']['renamed'] += 1
        elif result == 'already_correct':
            self.data['stats']['already_correct'] += 1
        elif result == 'error':
            self.data['stats']['errors'] += 1
    
    def is_processed(self, file_path):
        """Check if file was already processed."""
        file_str = str(file_path)
        return any(p['path'] == file_str for p in self.data['processed_files'])
    
    def should_save(self):
        """Check if we should save checkpoint (every 100 files)."""
        return self.data['current_index'] % 100 == 0
    
    def get_resume_index(self):
        """Get index to resume from."""
        return self.data['current_index']
    
    def delete(self):
        """Delete checkpoint file after successful completion."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()

# ============================================================================
# METADATA READING FUNCTIONS (Same as other scripts)
# ============================================================================

def get_best_date_from_exif(image_path):
    dates_found = {}
    
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            if exifdata:
                if 36867 in exifdata and exifdata[36867]:
                    dates_found['DateTimeOriginal'] = str(exifdata[36867])
                if 36868 in exifdata and exifdata[36868]:
                    dates_found['DateTimeDigitized'] = str(exifdata[36868])
                if 306 in exifdata and exifdata[306]:
                    dates_found['DateTime'] = str(exifdata[306])
    except Exception as e:
        pass
    
    if not dates_found:
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                if 'EXIF DateTimeOriginal' in tags:
                    dates_found['DateTimeOriginal'] = str(tags['EXIF DateTimeOriginal'])
                if 'EXIF DateTimeDigitized' in tags:
                    dates_found['DateTimeDigitized'] = str(tags['EXIF DateTimeDigitized'])
                if 'Image DateTime' in tags:
                    dates_found['DateTime'] = str(tags['Image DateTime'])
        except Exception as e:
            pass
    
    priority_order = ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']
    
    for date_type in priority_order:
        if date_type in dates_found:
            parsed_date = parse_exif_date(dates_found[date_type])
            if parsed_date and is_valid_date(parsed_date):
                return parsed_date, date_type
    
    return None, None

def get_artist_from_exif(image_path):
    try:
        with Image.open(image_path) as img:
            exifdata = img.getexif()
            if exifdata and 315 in exifdata and exifdata[315]:
                return str(exifdata[315]).strip()
    except Exception as e:
        pass
    
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            if 'Image Artist' in tags:
                return str(tags['Image Artist']).strip()
    except Exception as e:
        pass
    
    return None

def get_video_creation_date(video_path):
    try:
        result = subprocess.run(
            ['exiftool', '-CreateDate', '-DateTimeOriginal', '-MediaCreateDate', 
             '-CreationDate', '-TrackCreateDate', '-s', '-s', '-s', str(video_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line:
                    parsed_date = parse_exif_date(line.strip())
                    if parsed_date and is_valid_date(parsed_date):
                        return parsed_date, 'Video CreateDate'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None, None

def parse_exif_date(date_str):
    if not date_str or date_str.lower() == 'none':
        return None
    
    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y:%m:%d",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    
    return None

def is_valid_date(date_obj):
    if not date_obj:
        return False
    
    if date_obj.year < 2001 or date_obj.year > 2025:
        return False
    
    if date_obj.year == 2000 and date_obj.month == 1 and date_obj.day == 1:
        return False
    
    return True

def get_file_creation_date(file_path):
    try:
        stat = os.stat(file_path)
        
        if hasattr(stat, 'st_birthtime'):
            date_obj = datetime.fromtimestamp(stat.st_birthtime)
            if is_valid_date(date_obj):
                return date_obj, 'File Creation Date (birthtime)'
        
        date_obj = datetime.fromtimestamp(stat.st_mtime)
        if is_valid_date(date_obj):
            return date_obj, 'File Modification Date'
    except Exception as e:
        pass
    
    return None, None

def format_artist_name(artist_name):
    if not artist_name:
        return None
    
    import re
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', artist_name)
    
    words = cleaned.split()
    if not words:
        return None
    
    if len(words) == 1:
        return words[0][0].upper() + words[0][1:].lower() if len(words[0]) > 1 else words[0].upper()
    
    formatted_parts = []
    formatted_parts.append(words[0][0].upper())
    formatted_parts.append(words[1][0].upper() + words[1][1:].lower() if len(words[1]) > 1 else words[1].upper())
    
    for word in words[2:]:
        formatted_parts.append(word.lower())
    
    return ''.join(formatted_parts)

def generate_new_filename(file_path, date_obj, artist_name=None):
    ext = file_path.suffix.lower()
    
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    prefix = 'MOV' if ext in video_extensions else 'IMG'
    
    date_part = date_obj.strftime('%Y%m%d_%H%M%S')
    
    if artist_name:
        formatted_artist = format_artist_name(artist_name)
        if formatted_artist:
            new_name = f"{prefix}_{date_part}({formatted_artist}){file_path.suffix}"
        else:
            new_name = f"{prefix}_{date_part}{file_path.suffix}"
    else:
        new_name = f"{prefix}_{date_part}{file_path.suffix}"
    
    return new_name

def rename_file(file_path, new_filename):
    new_path = file_path.parent / new_filename
    
    counter = 1
    while new_path.exists() and new_path != file_path:
        name_parts = new_filename.rsplit('.', 1)
        if len(name_parts) == 2:
            base_name, ext = name_parts
            if ')' in base_name:
                parts = base_name.split('(')
                new_filename = f"{parts[0]}_{counter:02d}({parts[1]}.{ext}"
            else:
                new_filename = f"{base_name}_{counter:02d}.{ext}"
        else:
            new_filename = f"{new_filename}_{counter:02d}"
        
        new_path = file_path.parent / new_filename
        counter += 1
    
    try:
        file_path.rename(new_path)
        return True, new_path
    except Exception as e:
        return False, str(e)

def process_file(file_path, dry_run=False):
    ext = file_path.suffix.lower()
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    
    date_obj = None
    date_source = None
    artist = None
    
    if ext in image_extensions:
        date_obj, date_source = get_best_date_from_exif(file_path)
        artist = get_artist_from_exif(file_path)
    elif ext in video_extensions:
        date_obj, date_source = get_video_creation_date(file_path)
    
    if not date_obj:
        date_obj, date_source = get_file_creation_date(file_path)
    
    if not date_obj:
        return False, file_path.name, None, None, "No valid date found", None
    
    new_filename = generate_new_filename(file_path, date_obj, artist)
    
    if file_path.name == new_filename:
        return True, file_path.name, file_path.name, date_obj, date_source, artist
    
    if not dry_run:
        success, result = rename_file(file_path, new_filename)
        if success:
            return True, file_path.name, result.name, date_obj, date_source, artist
        else:
            return False, file_path.name, None, date_obj, date_source, f"Error: {result}"
    else:
        return True, file_path.name, new_filename, date_obj, date_source, artist

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Photo renamer WITH CHECKPOINT/RESUME support (macOS/Linux)'
    )
    parser.add_argument('directory', nargs='?', default=None,
                       help='Directory to process (default: current directory)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be done without renaming')
    parser.add_argument('--recursive', '-r', action='store_true', default=True,
                       help='Process subdirectories recursively (default: True)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm without prompting')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last checkpoint')
    parser.add_argument('--checkpoint-file', default=None,
                       help='Custom checkpoint file path')
    parser.add_argument('--no-checkpoint', action='store_true',
                       help='Disable checkpoint system')
    
    args = parser.parse_args()
    
    if args.directory:
        source_dir = Path(args.directory).expanduser().resolve()
    else:
        source_dir = Path.cwd()
    
    if not source_dir.exists():
        print(f"ERROR: Directory {source_dir} does not exist!")
        return 1
    
    # Setup checkpoint
    checkpoint = None
    if not args.no_checkpoint:
        if args.checkpoint_file:
            checkpoint_path = Path(args.checkpoint_file)
        else:
            checkpoint_path = source_dir / '.photo_rename_checkpoint.json'
        
        checkpoint = CheckpointManager(checkpoint_path)
        
        if args.resume or checkpoint.load():
            print(f"{'='*80}")
            print(f"RESUMING FROM CHECKPOINT")
            print(f"{'='*80}")
            print(f"Checkpoint: {checkpoint_path}")
            print(f"Processed: {checkpoint.data['current_index']} files")
            print(f"Renamed: {checkpoint.data['stats']['renamed']}")
            print(f"Already correct: {checkpoint.data['stats']['already_correct']}")
            print(f"Errors: {checkpoint.data['stats']['errors']}")
            print(f"{'='*80}\n")
    
    if not args.resume:
        print(f"{'='*80}")
        print(f"PHOTO RENAMER (WITH CHECKPOINT)")
        print(f"{'='*80}")
        print(f"Directory: {source_dir}")
        print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
        print(f"Recursive: {args.recursive}")
        print(f"Checkpoint: {'Enabled' if checkpoint else 'Disabled'}")
        if checkpoint:
            print(f"Checkpoint file: {checkpoint.checkpoint_path}")
        print(f"{'='*80}\n")
    
    # Find files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', 
                       '.gif', '.bmp', '.webp', '.raw', '.cr2', '.nef', '.dng', 
                       '.arw', '.orf', '.raf', '.rw2'}
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.m4v', '.mpeg', '.mpg', '.wmv'}
    all_extensions = image_extensions | video_extensions
    
    print("Scanning...")
    
    if args.recursive:
        files = [f for f in source_dir.rglob('*') 
                if f.is_file() and f.suffix.lower() in all_extensions]
    else:
        files = [f for f in source_dir.iterdir() 
                if f.is_file() and f.suffix.lower() in all_extensions]
    
    if checkpoint:
        checkpoint.data['total_files'] = len(files)
    
    print(f"Found {len(files)} file(s)\n")
    
    if not files:
        return 0
    
    start_idx = checkpoint.get_resume_index() if checkpoint else 0
    
    if start_idx > 0:
        print(f"Resuming from file {start_idx + 1}/{len(files)}\n")
    
    if not args.yes and not args.dry_run and not args.resume:
        response = input(f"Process {len(files)} files? (y/n): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return 0
    
    print(f"\n{'='*80}")
    print("Processing...")
    print(f"{'='*80}\n")
    
    success_count = checkpoint.data['stats']['renamed'] if checkpoint else 0
    already_named_count = checkpoint.data['stats']['already_correct'] if checkpoint else 0
    error_count = checkpoint.data['stats']['errors'] if checkpoint else 0
    errors = []
    
    for idx in range(start_idx, len(files)):
        file_path = files[idx]
        
        if checkpoint and checkpoint.is_processed(file_path):
            continue
        
        success, old_name, new_name, date_obj, date_source, artist_or_error = process_file(
            file_path, dry_run=args.dry_run
        )
        
        if success:
            if old_name == new_name:
                print(f"[{idx+1}/{len(files)}] ✓ Already correct: {old_name}")
                already_named_count += 1
                result_type = 'already_correct'
            else:
                date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S') if date_obj else 'N/A'
                print(f"[{idx+1}/{len(files)}] ✓ {old_name} → {new_name}")
                print(f"  Date: {date_str} (from {date_source})")
                success_count += 1
                result_type = 'renamed'
        else:
            print(f"[{idx+1}/{len(files)}] ✗ {old_name}: {artist_or_error}")
            error_count += 1
            errors.append((old_name, artist_or_error))
            result_type = 'error'
        
        if checkpoint:
            checkpoint.mark_processed(file_path, result_type)
            if checkpoint.should_save():
                checkpoint.save()
                print(f"  → Checkpoint saved ({idx+1}/{len(files)})")
    
    if checkpoint and not args.dry_run:
        checkpoint.save()
        print(f"\n✓ Final checkpoint saved")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total: {len(files)}")
    print(f"Renamed: {success_count}")
    print(f"Already correct: {already_named_count}")
    print(f"Errors: {error_count}")
    
    if args.dry_run:
        print(f"\n⚠ DRY RUN - No changes made")
    
    if checkpoint and not args.dry_run and error_count == 0:
        checkpoint.delete()
        print(f"\n✓ Checkpoint deleted (completed)")
    
    print(f"{'='*80}")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
