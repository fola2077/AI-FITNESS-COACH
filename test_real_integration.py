#!/usr/bin/env python3
"""
Test Real Video Analysis Integration - Test actual PoseProcessor with DataLogger
"""

import cv2
import sys
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_real_video_analysis(video_path):
    """Test the actual PoseProcessor with integrated DataLogger"""
    
    print("🔄 Testing Real Video Analysis Integration")
    
    try:
        # Import the actual integrated PoseProcessor
        from src.processing.pose_processor import PoseProcessor
        from src.grading.advanced_form_grader import UserProfile, UserLevel
        
        # Check if video exists
        if not Path(video_path).exists():
            print(f"❌ Video file not found: {video_path}")
            return False
        
        # Create user profile
        user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.INTERMEDIATE)
        
        # Create pose processor with data logging
        processor = PoseProcessor(user_profile=user_profile)
        print("✅ PoseProcessor created with integrated DataLogger")
        
        # Start session
        print("🚀 Starting analysis session...")
        processor.start_session('video')
        print("✅ Session started")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            print(f"❌ Cannot open video file: {video_path}")
            return False
        
        print(f"📹 Video opened successfully")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        print(f"   📊 FPS: {fps:.2f}")
        print(f"   📊 Frames: {frame_count:,}")
        print(f"   📊 Duration: {duration:.1f} seconds")
        
        # Process frames
        frame_num = 0
        frames_processed = 0
        frames_with_data = 0
        max_frames = 60  # Process first 2 seconds
        
        print(f"\n🔄 Processing frames...")
        
        while frame_num < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_num += 1
            
            # Process frame using the actual processor
            result = processor.process_frame(frame)
            
            if result and result.get('landmarks_detected'):
                frames_processed += 1
                
                # Check if the result contains expected data
                if result.get('rep_count') is not None:
                    frames_with_data += 1
                
                if frame_num % 20 == 0:
                    print(f"   🔄 Frame {frame_num}: Pose detected, Rep count: {result.get('rep_count', 0)}")
        
        # End session
        print(f"\n🛑 Ending session...")
        session_summary = processor.end_session()
        
        cap.release()
        
        print(f"✅ Session completed!")
        print(f"   📊 Frames processed: {frames_processed}/{frame_num}")
        print(f"   📊 Frames with data: {frames_with_data}")
        
        # Check CSV files
        print(f"\n📄 Checking CSV Files...")
        check_csv_results()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in real integration test: {e}")
        print(f"📍 Error details: {traceback.format_exc()}")
        return False

def check_csv_results():
    """Check if CSV files have new data"""
    
    csv_files = [
        "data/logs/sessions/session_202508.csv",
        "data/logs/reps/rep_data_202508.csv", 
        "data/logs/biomechanics/biomech_202508.csv",
        "data/logs/ml_training/ml_dataset_202508.csv"
    ]
    
    for file_path in csv_files:
        full_path = Path(file_path)
        
        if full_path.exists():
            try:
                import pandas as pd
                df = pd.read_csv(full_path)
                row_count = len(df)
                
                if row_count > 0:
                    print(f"   ✅ {full_path.name}: {row_count} rows")
                    
                    # Show sample of recent data
                    if row_count > 0 and file_path.endswith('biomech_202508.csv'):
                        recent_data = df.tail(3)
                        if len(recent_data) > 0:
                            print(f"      📊 Recent biomech data sample:")
                            for idx, row in recent_data.iterrows():
                                print(f"         Row {idx}: depth={row.get('depth_percentage', 'N/A')}%, phase={row.get('movement_phase', 'N/A')}")
                else:
                    print(f"   ⚠️ {full_path.name}: Empty (headers only)")
                    
            except Exception as e:
                print(f"   ❌ {full_path.name}: Error reading - {e}")
        else:
            print(f"   ❌ {full_path.name}: Not found")

def main():
    """Main test function"""
    
    # Use the sample video
    video_path = "0918_squat_000064.mp4"
    
    print("🧪 Real Integration Test - PoseProcessor + DataLogger")
    print("=" * 60)
    
    try:
        success = test_real_video_analysis(video_path)
        
        if success:
            print(f"\n🎉 Real integration test completed successfully!")
            print(f"Data should now be logged in CSV files.")
        else:
            print(f"\n❌ Real integration test failed")
            
    except KeyboardInterrupt:
        print(f"\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error during test: {e}")
        print(f"Traceback: {traceback.format_exc()}")
    
    input(f"\nPress Enter to exit...")

if __name__ == "__main__":
    main()
