#!/usr/bin/env python3
"""
AI Fitness Coach - Data Log Cleanup Script

This script safely clears all CSV log files and session reports while preserving
directory structure and important configuration files.

Usage:
    python clear_data_logs.py

Options:
    --dry-run    : Show what would be deleted without actually deleting
    --backup     : Create backup before deletion
    --all        : Include calibration and demo data (normally preserved)
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path
import glob

class DataLogCleaner:
    """Comprehensive data log cleanup utility"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.logs_dir = os.path.join(self.data_dir, "logs")
        
        # Define what gets cleaned by default
        self.csv_patterns = [
            "data/logs/sessions/*.csv",
            "data/logs/reps/*.csv", 
            "data/logs/biomechanics/*.csv",
            "data/logs/ml_training/*.csv",
            "data/logs/evaluation/*.csv"
        ]
        
        self.report_patterns = [
            "data/logs/session_report_*.txt",
            "data/logs/data_summary_report_*.json"
        ]
        
        # Files/patterns to preserve (unless --all specified)
        self.preserve_patterns = [
            "data/calibration_history.json",
            "data/validation_dataset.json",
            "data/demo_user_progress.txt",
            "data/models/**/*"
        ]
        
    def find_files_to_clean(self, include_preserved: bool = False) -> dict:
        """Find all files that will be cleaned"""
        files_to_clean = {
            'csv_files': [],
            'report_files': [],
            'preserved_files': []
        }
        
        # Find CSV files
        for pattern in self.csv_patterns:
            full_pattern = os.path.join(self.base_dir, pattern)
            files_to_clean['csv_files'].extend(glob.glob(full_pattern, recursive=True))
        
        # Find report files
        for pattern in self.report_patterns:
            full_pattern = os.path.join(self.base_dir, pattern)
            files_to_clean['report_files'].extend(glob.glob(full_pattern, recursive=True))
            
        # Find preserved files (for --all option)
        if include_preserved:
            for pattern in self.preserve_patterns:
                full_pattern = os.path.join(self.base_dir, pattern)
                files_to_clean['preserved_files'].extend(glob.glob(full_pattern, recursive=True))
        
        return files_to_clean
    
    def calculate_total_size(self, files: list) -> int:
        """Calculate total size of files to be deleted"""
        total_size = 0
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
            except (OSError, IOError):
                pass
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def create_backup(self, files: dict, backup_dir: str) -> bool:
        """Create backup of files before deletion"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            print(f"📦 Creating backup in: {backup_dir}")
            
            backup_count = 0
            for category, file_list in files.items():
                if not file_list:
                    continue
                    
                category_backup_dir = os.path.join(backup_dir, category)
                os.makedirs(category_backup_dir, exist_ok=True)
                
                for file_path in file_list:
                    if os.path.isfile(file_path):
                        filename = os.path.basename(file_path)
                        backup_path = os.path.join(category_backup_dir, filename)
                        shutil.copy2(file_path, backup_path)
                        backup_count += 1
            
            print(f"✅ Backed up {backup_count} files")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def delete_files(self, files: dict, dry_run: bool = False) -> dict:
        """Delete files and return statistics"""
        stats = {
            'deleted_count': 0,
            'failed_count': 0,
            'total_size_freed': 0,
            'errors': []
        }
        
        all_files = []
        for file_list in files.values():
            all_files.extend(file_list)
        
        for file_path in all_files:
            try:
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    
                    if dry_run:
                        print(f"🔍 Would delete: {file_path} ({self.format_size(file_size)})")
                        stats['deleted_count'] += 1
                        stats['total_size_freed'] += file_size
                    else:
                        os.remove(file_path)
                        print(f"🗑️  Deleted: {file_path} ({self.format_size(file_size)})")
                        stats['deleted_count'] += 1
                        stats['total_size_freed'] += file_size
                        
            except Exception as e:
                error_msg = f"Failed to delete {file_path}: {e}"
                stats['errors'].append(error_msg)
                stats['failed_count'] += 1
                print(f"❌ {error_msg}")
        
        return stats
    
    def clean_empty_directories(self, dry_run: bool = False):
        """Remove empty directories (but preserve structure)"""
        dirs_to_check = [
            os.path.join(self.logs_dir, "sessions"),
            os.path.join(self.logs_dir, "reps"),
            os.path.join(self.logs_dir, "biomechanics"),
            os.path.join(self.logs_dir, "ml_training"),
            os.path.join(self.logs_dir, "evaluation")
        ]
        
        for dir_path in dirs_to_check:
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                if dry_run:
                    print(f"🔍 Would remove empty directory: {dir_path}")
                else:
                    # Don't actually remove - preserve directory structure
                    print(f"📁 Preserving empty directory structure: {dir_path}")
    
    def run_cleanup(self, dry_run: bool = False, create_backup: bool = False, 
                   include_preserved: bool = False) -> bool:
        """Run the complete cleanup process"""
        
        print("🧹 AI Fitness Coach - Data Log Cleanup")
        print("=" * 50)
        
        # Check if data directory exists
        if not os.path.exists(self.data_dir):
            print(f"❌ Data directory not found: {self.data_dir}")
            return False
        
        # Find files to clean
        files_to_clean = self.find_files_to_clean(include_preserved)
        
        # Calculate statistics
        all_files = []
        for file_list in files_to_clean.values():
            all_files.extend(file_list)
        
        if not all_files:
            print("✅ No data files found to clean!")
            return True
        
        total_size = self.calculate_total_size(all_files)
        
        print(f"📊 Found files to clean:")
        print(f"   CSV Files: {len(files_to_clean['csv_files'])}")
        print(f"   Report Files: {len(files_to_clean['report_files'])}")
        if include_preserved:
            print(f"   Preserved Files: {len(files_to_clean['preserved_files'])}")
        print(f"   Total Files: {len(all_files)}")
        print(f"   Total Size: {self.format_size(total_size)}")
        
        if dry_run:
            print(f"\n🔍 DRY RUN MODE - No files will be deleted")
        
        # Create backup if requested
        if create_backup and not dry_run:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.base_dir, f"data_backup_{timestamp}")
            if not self.create_backup(files_to_clean, backup_dir):
                print("❌ Backup failed, aborting cleanup")
                return False
        
        # Confirm deletion (unless dry run)
        if not dry_run:
            response = input(f"\n⚠️  Are you sure you want to delete {len(all_files)} files? (y/N): ")
            if response.lower() != 'y':
                print("❌ Cleanup cancelled")
                return False
        
        print(f"\n🗑️  {'Simulating' if dry_run else 'Starting'} cleanup...")
        
        # Delete files
        stats = self.delete_files(files_to_clean, dry_run)
        
        # Clean empty directories
        self.clean_empty_directories(dry_run)
        
        # Print final statistics
        print(f"\n📈 Cleanup Statistics:")
        print(f"   Files {'would be ' if dry_run else ''}deleted: {stats['deleted_count']}")
        print(f"   Failed deletions: {stats['failed_count']}")
        print(f"   Space {'would be ' if dry_run else ''}freed: {self.format_size(stats['total_size_freed'])}")
        
        if stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in stats['errors']:
                print(f"   {error}")
        
        if stats['failed_count'] == 0:
            print(f"\n✅ Cleanup {'simulation ' if dry_run else ''}completed successfully!")
        else:
            print(f"\n⚠️  Cleanup completed with {stats['failed_count']} errors")
        
        return stats['failed_count'] == 0

def main():
    parser = argparse.ArgumentParser(
        description="Clear AI Fitness Coach CSV log files and session reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clear_data_logs.py                    # Interactive cleanup
  python clear_data_logs.py --dry-run          # Preview what will be deleted
  python clear_data_logs.py --backup           # Create backup before deletion
  python clear_data_logs.py --all              # Include calibration data
  python clear_data_logs.py --dry-run --all    # Preview full cleanup
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--backup', action='store_true',
                       help='Create backup before deletion')
    parser.add_argument('--all', action='store_true',
                       help='Include calibration and demo data (normally preserved)')
    
    args = parser.parse_args()
    
    try:
        cleaner = DataLogCleaner()
        success = cleaner.run_cleanup(
            dry_run=args.dry_run,
            create_backup=args.backup,
            include_preserved=args.all
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
