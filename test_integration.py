#!/usr/bin/env python3
"""
Simple Integration Test for AI Fitness Coach
Tests basic functionality to identify where the issue is
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_basic_integration():
    """Test basic component integration"""
    print("🧪 Basic Integration Test")
    print("=" * 40)
    
    # Test 1: Import all components
    print("1. Testing imports...")
    try:
        from src.pose.pose_detector import PoseDetector
        from src.processing.pose_processor import PoseProcessor
        from src.grading.advanced_form_grader import UserProfile, UserLevel
        from src.capture.camera import CameraManager
        print("   ✅ All imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Create instances
    print("\n2. Testing component creation...")
    try:
        detector = PoseDetector()
        print("   ✅ PoseDetector created")
        
        user_profile = UserProfile(user_id="test", skill_level=UserLevel.INTERMEDIATE)
        processor = PoseProcessor(user_profile)
        print("   ✅ PoseProcessor created")
        
        # Test camera creation (don't fail if camera not available)
        try:
            camera = CameraManager(0)
            if camera.isOpened():
                print("   ✅ CameraManager created and camera opened")
                camera.release()
            else:
                print("   ⚠️  CameraManager created but camera not available")
        except Exception as cam_error:
            print(f"   ⚠️  Camera not available: {cam_error}")
        
    except Exception as e:
        print(f"   ❌ Component creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test pose detector directly
    print("\n3. Testing pose detector with dummy frame...")
    try:
        import cv2
        import numpy as np
        
        # Create a dummy frame (black image)
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Convert to RGB
        frame_rgb = cv2.cvtColor(dummy_frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = detector.process_frame(frame_rgb)
        print(f"   ✅ Pose detector processed frame, results: {type(results)}")
        print(f"       Has landmarks: {results and results.pose_landmarks is not None}")
        
    except Exception as e:
        print(f"   ❌ Pose detector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test processor with dummy frame
    print("\n4. Testing pose processor with dummy frame...")
    try:
        processor.start_session('webcam')
        result = processor.process_frame(dummy_frame)
        print(f"   ✅ Pose processor worked, result type: {type(result)}")
        if isinstance(result, dict):
            print(f"       Result keys: {list(result.keys())}")
            print(f"       Landmarks detected: {result.get('landmarks_detected', False)}")
        
    except Exception as e:
        print(f"   ❌ Pose processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ Basic integration test completed successfully!")
    print("\n💡 Next steps:")
    print("   • Run: python diagnose_pose.py - to test with live camera")
    print("   • Run: python run_app.py - to start the full application")
    
    return True

if __name__ == "__main__":
    success = test_basic_integration()
    if not success:
        print("\n❌ Integration test failed!")
        print("Please fix the errors above before running the main application.")
        sys.exit(1)
    else:
        print("\n🎉 All basic tests passed!")
        sys.exit(0)
