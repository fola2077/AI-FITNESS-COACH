#!/usr/bin/env python3
"""
Simple test script to verify video loading functionality
"""
import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.capture.camera import CameraManager
from src.processing.pose_processor import PoseProcessor
from src.grading.advanced_form_grader import UserProfile, UserLevel
import cv2

def test_video_loading():
    """Test video loading functionality"""
    print("🧪 Testing Video Loading Functionality")
    print("=" * 50)
    
    # Test 1: Check if we can create camera manager for webcam
    print("1. Testing CameraManager for webcam...")
    try:
        cam = CameraManager(0)
        if cam.isOpened():
            print("   ✅ Webcam CameraManager created successfully")
            cam.release()
        else:
            print("   ⚠️  Webcam not available or permission denied")
    except Exception as e:
        print(f"   ❌ Webcam test failed: {e}")
    
    # Test 2: Check if we can create PoseProcessor
    print("\n2. Testing PoseProcessor initialization...")
    try:
        user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.INTERMEDIATE)
        processor = PoseProcessor(user_profile)
        print("   ✅ PoseProcessor created successfully")
        
        # Test session start for different source types
        processor.start_session('webcam')
        print(f"   ✅ Webcam session started: {processor.session_state}")
        
        processor.start_session('video')
        print(f"   ✅ Video session started: {processor.session_state}")
        
    except Exception as e:
        print(f"   ❌ PoseProcessor test failed: {e}")
    
    # Test 3: Test with a sample video file if available
    print("\n3. Testing video file loading...")
    test_video_paths = [
        "test_video.mp4",
        "sample_video.mp4",
        "data/test_video.mp4"
    ]
    
    video_found = False
    for test_path in test_video_paths:
        if os.path.exists(test_path):
            print(f"   Found test video: {test_path}")
            try:
                cam = CameraManager(test_path)
                if cam.isOpened():
                    info = cam.get_video_info()
                    print(f"   ✅ Video loaded successfully!")
                    print(f"      Video info: {info}")
                    
                    # Test reading a frame
                    frame = cam.get_frame()
                    if frame is not None:
                        print(f"      ✅ Frame read successfully: {frame.shape}")
                    else:
                        print("      ⚠️  Could not read frame")
                    
                    cam.release()
                    video_found = True
                    break
                else:
                    print(f"   ❌ Could not open video: {test_path}")
            except Exception as e:
                print(f"   ❌ Video test failed for {test_path}: {e}")
    
    if not video_found:
        print("   ℹ️  No test video files found. To test with your own video:")
        print("      - Place a video file in the project directory")
        print("      - Run: python test_video_loading.py your_video.mp4")
    
    print("\n" + "=" * 50)
    print("✅ Video loading test completed!")
    print("\n💡 Tips for video loading issues:")
    print("   • Ensure video file exists and is readable")
    print("   • Supported formats: MP4, AVI, MOV, MKV, WMV")
    print("   • Check that OpenCV is properly installed")
    print("   • For GUI issues, run the main app: python run_app.py")

def test_specific_video(video_path):
    """Test a specific video file"""
    print(f"🧪 Testing specific video: {video_path}")
    print("=" * 50)
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    try:
        # Test CameraManager
        cam = CameraManager(video_path)
        if not cam.isOpened():
            print(f"❌ Cannot open video file: {video_path}")
            return
        
        info = cam.get_video_info()
        print(f"✅ Video opened successfully!")
        print(f"Video information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Test frame reading
        frame_count = 0
        while frame_count < 10:  # Test first 10 frames
            frame = cam.get_frame()
            if frame is None:
                break
            frame_count += 1
        
        print(f"✅ Successfully read {frame_count} frames")
        cam.release()
        
        # Test with PoseProcessor
        print("\nTesting with PoseProcessor...")
        user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.INTERMEDIATE)
        processor = PoseProcessor(user_profile)
        processor.start_session('video')
        
        # Process one frame
        cam = CameraManager(video_path)
        frame = cam.get_frame()
        if frame is not None:
            result = processor.process_frame(frame)
            print(f"✅ Frame processed successfully!")
            print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        cam.release()
        
    except Exception as e:
        print(f"❌ Error testing video: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific video file
        test_specific_video(sys.argv[1])
    else:
        # Run general tests
        test_video_loading()
