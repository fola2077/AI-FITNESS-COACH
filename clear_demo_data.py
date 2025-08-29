#!/usr/bin/env python3
"""
Clear Demo Data - Remove synthetic test data while preserving file structure
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from datetime import datetime

def create_backup():
    """Create backup of current data before cleaning"""
    
    project_root = Path(__file__).parent.absolute()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = project_root / "data_backup" / f"backup_{timestamp}"
    
    print(f"📁 Creating backup...")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Directories to backup
    data_dirs = [
        "data/logs/sessions",
        "data/logs/reps", 
        "data/logs/biomechanics",
        "data/logs/ml_training",
        "data/demo_analytics",
        "test_data_output"
    ]
    
    total_backed_up = 0
    
    for data_dir in data_dirs:
        source_dir = project_root / data_dir
        if source_dir.exists():
            dest_dir = backup_dir / data_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all files
            for file_path in source_dir.glob("*"):
                if file_path.is_file():
                    shutil.copy2(file_path, dest_dir / file_path.name)
                    total_backed_up += 1
                    print(f"   ✅ Backed up: {file_path.name}")
    
    print(f"✅ Backup complete: {total_backed_up} files backed up to {backup_dir}")
    return backup_dir

def identify_demo_patterns():
    """Identify patterns that indicate demo/test data"""
    
    return {
        'session_patterns': [
            'demo_user_001',
            'test_user',
            'session_20250829_174454_demo_user_001',
            'session_20250829_173855_test_user_001',
            'session_20250829_173956_test_user_001',
            'session_20250829_174034_test_user_001'
        ],
        'user_patterns': [
            'demo_user_001',
            'test_user_001',
            'test_user',
            'mock_user'
        ],
        # Perfect synthetic data indicators
        'synthetic_indicators': {
            'perfect_symmetry': [1.0],  # Knee/ankle symmetry always 1.0
            'perfect_stability': [0.05, 0.08],  # Only 2 postural sway values
            'perfect_progression': [20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0],  # Movement velocity
            'constant_acceleration': [3.0, 0.0, -2.0],  # Only 3 acceleration values
            'perfect_visibility': [0.95, 0.88],  # Landmark visibility too consistent
        }
    }

def is_synthetic_data(df, patterns):
    """Check if DataFrame contains synthetic/demo data patterns"""
    
    if len(df) == 0:
        return False
    
    # Check for demo session/user patterns
    if 'session_id' in df.columns:
        for pattern in patterns['session_patterns']:
            if df['session_id'].str.contains(pattern, na=False).any():
                return True
    
    if 'user_id' in df.columns:
        for pattern in patterns['user_patterns']:
            if df['user_id'].str.contains(pattern, na=False).any():
                return True
    
    # Check for synthetic data patterns
    synthetic_score = 0
    total_checks = 0
    
    # Check knee symmetry (real humans have variation)
    if 'knee_symmetry_ratio' in df.columns:
        unique_values = df['knee_symmetry_ratio'].nunique()
        if unique_values <= 2:  # Too few unique values
            synthetic_score += 1
        total_checks += 1
    
    # Check movement velocity (real movement has more variation)
    if 'movement_velocity' in df.columns:
        velocities = df['movement_velocity'].unique()
        perfect_progression = patterns['synthetic_indicators']['perfect_progression']
        overlap = len(set(velocities) & set(perfect_progression))
        if overlap >= 6:  # High overlap with demo pattern
            synthetic_score += 1
        total_checks += 1
    
    # Check acceleration consistency
    if 'acceleration' in df.columns:
        unique_accel = df['acceleration'].nunique()
        if unique_accel <= 3:  # Too few acceleration values
            synthetic_score += 1
        total_checks += 1
    
    # Check postural sway
    if 'postural_sway' in df.columns:
        unique_sway = df['postural_sway'].nunique()
        if unique_sway <= 2:  # Only 2 values (0.05, 0.08)
            synthetic_score += 1
        total_checks += 1
    
    # If more than 50% of checks indicate synthetic data
    if total_checks > 0 and (synthetic_score / total_checks) > 0.5:
        return True
    
    return False

def clean_csv_file(file_path, patterns):
    """Clean demo/synthetic data from a CSV file"""
    
    if not file_path.exists():
        return False, "File doesn't exist"
    
    try:
        df = pd.read_csv(file_path)
        original_rows = len(df)
        
        if original_rows == 0:
            return False, "File is empty"
        
        print(f"\n📄 Cleaning: {file_path.name}")
        print(f"   Original rows: {original_rows:,}")
        
        cleaned_df = df.copy()
        
        # Remove by session ID patterns
        if 'session_id' in cleaned_df.columns:
            for pattern in patterns['session_patterns']:
                mask = cleaned_df['session_id'].str.contains(pattern, na=False)
                removed_count = mask.sum()
                if removed_count > 0:
                    cleaned_df = cleaned_df[~mask]
                    print(f"   🗑️ Removed {removed_count:,} rows matching session: {pattern}")
        
        # Remove by user ID patterns  
        if 'user_id' in cleaned_df.columns:
            for pattern in patterns['user_patterns']:
                mask = cleaned_df['user_id'].str.contains(pattern, na=False)
                removed_count = mask.sum()
                if removed_count > 0:
                    cleaned_df = cleaned_df[~mask]
                    print(f"   🗑️ Removed {removed_count:,} rows matching user: {pattern}")
        
        # Check remaining sessions for synthetic patterns
        if 'session_id' in cleaned_df.columns and len(cleaned_df) > 0:
            synthetic_sessions = []
            
            for session_id in cleaned_df['session_id'].unique():
                session_data = cleaned_df[cleaned_df['session_id'] == session_id]
                
                if is_synthetic_data(session_data, patterns):
                    synthetic_sessions.append(session_id)
            
            # Remove synthetic sessions
            for session_id in synthetic_sessions:
                mask = cleaned_df['session_id'] == session_id
                removed_count = mask.sum()
                cleaned_df = cleaned_df[~mask]
                print(f"   🗑️ Removed {removed_count:,} rows from synthetic session: {session_id}")
        
        # Save cleaned data
        final_rows = len(cleaned_df)
        rows_removed = original_rows - final_rows
        
        if rows_removed > 0:
            cleaned_df.to_csv(file_path, index=False)
            print(f"   ✅ Cleaned: {rows_removed:,} rows removed, {final_rows:,} rows remain")
            return True, f"{rows_removed:,} rows removed"
        else:
            print(f"   ✅ No demo data found")
            return False, "No demo data found"
            
    except Exception as e:
        print(f"   ❌ Error cleaning {file_path.name}: {e}")
        return False, str(e)

def remove_demo_directories():
    """Remove entire demo directories"""
    
    project_root = Path(__file__).parent.absolute()
    
    demo_dirs = [
        "data/demo_analytics",
        "test_data_output"
    ]
    
    removed_dirs = 0
    
    for demo_dir in demo_dirs:
        dir_path = project_root / demo_dir
        
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"   🗑️ Removed directory: {demo_dir}")
                removed_dirs += 1
            except Exception as e:
                print(f"   ❌ Error removing {demo_dir}: {e}")
    
    return removed_dirs

def analyze_remaining_data():
    """Analyze what data remains after cleaning"""
    
    project_root = Path(__file__).parent.absolute()
    
    print(f"\n📊 Analyzing Remaining Data")
    print("=" * 30)
    
    csv_files = [
        "data/logs/sessions/session_202508.csv",
        "data/logs/reps/rep_data_202508.csv",
        "data/logs/biomechanics/biomech_202508.csv", 
        "data/logs/ml_training/ml_dataset_202508.csv"
    ]
    
    total_rows = 0
    total_sessions = 0
    total_users = 0
    
    for csv_file in csv_files:
        file_path = project_root / csv_file
        
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                rows = len(df)
                total_rows += rows
                
                print(f"📄 {file_path.name}: {rows:,} rows")
                
                if 'session_id' in df.columns and rows > 0:
                    unique_sessions = df['session_id'].nunique()
                    total_sessions += unique_sessions
                    print(f"   📊 Unique sessions: {unique_sessions}")
                
                if 'user_id' in df.columns and rows > 0:
                    unique_users = df['user_id'].nunique()
                    print(f"   👤 Unique users: {unique_users}")
                    
                if rows > 0:
                    # Show sample data to verify it's not synthetic
                    sample_data = df.head(1)
                    if 'session_id' in sample_data.columns:
                        session_sample = sample_data['session_id'].iloc[0]
                        print(f"   📋 Sample session: {session_sample}")
                
            except Exception as e:
                print(f"❌ Error reading {file_path.name}: {e}")
        else:
            print(f"📄 {csv_file}: File doesn't exist")
    
    print(f"\n🎯 Summary:")
    print(f"   Total data rows: {total_rows:,}")
    print(f"   Total sessions: {total_sessions}")
    
    if total_rows == 0:
        print(f"✅ All demo/test data successfully removed!")
        print(f"🚀 Ready for production - next workout will create clean data")
        return True
    else:
        print(f"⚠️ Some data remains - please verify it's real workout data")
        return False

def main():
    """Main cleanup function"""
    
    print("🧹 AI Fitness Coach - Demo Data Cleanup")
    print("=" * 50)
    print("This will remove all demo/test data from CSV files.")
    print("A backup will be created before cleaning.")
    
    # Confirm with user
    confirm = input("\nProceed with cleanup? (y/n): ").lower().strip()
    
    if confirm != 'y':
        print("❌ Cleanup cancelled")
        return
    
    project_root = Path(__file__).parent.absolute()
    
    # Step 1: Create backup
    backup_dir = create_backup()
    
    # Step 2: Get demo patterns
    patterns = identify_demo_patterns()
    
    # Step 3: Clean CSV files
    print(f"\n🧹 Cleaning CSV Files")
    print("-" * 25)
    
    csv_files = [
        "data/logs/sessions/session_202508.csv",
        "data/logs/reps/rep_data_202508.csv",
        "data/logs/biomechanics/biomech_202508.csv",
        "data/logs/ml_training/ml_dataset_202508.csv"
    ]
    
    cleaning_results = {}
    
    for csv_file in csv_files:
        file_path = project_root / csv_file
        success, message = clean_csv_file(file_path, patterns)
        cleaning_results[csv_file] = (success, message)
    
    # Step 4: Remove demo directories
    print(f"\n🗑️ Removing Demo Directories")
    print("-" * 30)
    
    removed_dirs = remove_demo_directories()
    print(f"✅ Removed {removed_dirs} demo directories")
    
    # Step 5: Analyze results
    is_clean = analyze_remaining_data()
    
    # Step 6: Summary
    print(f"\n🎯 Cleanup Summary")
    print("=" * 20)
    
    for file_path, (success, message) in cleaning_results.items():
        status = "✅" if success else "ℹ️"
        file_name = Path(file_path).name
        print(f"{status} {file_name}: {message}")
    
    print(f"\n💾 Backup saved to: {backup_dir}")
    
    if is_clean:
        print(f"\n🎉 SUCCESS! All demo data removed.")
        print(f"🚀 AI Fitness Coach is ready for real workout data!")
        print(f"\nNext workout session will create fresh, clean CSV files.")
    else:
        print(f"\n⚠️ Please verify remaining data is legitimate workout data.")
        print(f"If you see any demo patterns, run this script again.")
    
    print(f"\n📁 File structure preserved:")
    print(f"   📂 data/logs/sessions/")
    print(f"   📂 data/logs/reps/") 
    print(f"   📂 data/logs/biomechanics/")
    print(f"   📂 data/logs/ml_training/")

if __name__ == "__main__":
    main()
