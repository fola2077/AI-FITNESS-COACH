#!/usr/bin/env python3
"""
Console-only debug test script for webcam rep detection
This script runs with extensive debugging to identify rep detection issues.
"""

import os
import sys
import cv2
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_webcam_rep_detection_console():
    """Test webcam rep detection with comprehensive debugging (console only)."""
    print("=" * 60)
    print("🔍 WEBCAM REP DETECTION DEBUG TEST (CONSOLE ONLY)")
    print("=" * 60)
    
    try:
        # Import after path setup
        from src.processing.pose_processor import PoseProcessor
        from src.grading.advanced_form_grader import UserProfile, UserLevel, ThresholdConfig
        
        # Create a user profile for testing
        user_profile = UserProfile(
            user_id="debug_test_user",
            skill_level=UserLevel.BEGINNER,  # Use beginner for more lenient thresholds
            height_cm=175
        )
        
        # Use emergency calibrated thresholds for testing
        threshold_config = ThresholdConfig.emergency_calibrated()
        
        # Create processor with debug settings
        processor = PoseProcessor(
            user_profile=user_profile,
            threshold_config=threshold_config,
            enable_validation=False  # Disable validation for cleaner debug output
        )
        
        print("✅ Processor initialized successfully")
        
        # Try to open webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Failed to open webcam")
            return
            
        print("✅ Webcam opened successfully")
        
        # Set webcam properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Start session with calibration skipped for immediate testing
        processor.start_session(source_type='webcam', skip_calibration=True)
        print("✅ Session started (calibration skipped)")
        
        frame_count = 0
        last_rep_count = 0
        start_time = time.time()
        
        print("\n" + "=" * 60)
        print("🎥 LIVE WEBCAM ANALYSIS - Run for 30 seconds")
        print("📝 Watch console for debug output")
        print("🏃‍♂️ Perform squats to test rep detection")
        print("=" * 60)
        
        # Run for 30 seconds to test
        while time.time() - start_time < 30:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame from webcam")
                break
                
            frame_count += 1
            
            # Process frame with debugging
            try:
                result = processor.process_frame(frame)
                
                # Check for new reps
                if result:
                    current_rep_count = result.get('rep_count', 0)
                    if current_rep_count > last_rep_count:
                        print(f"\n🎉 NEW REP DETECTED! Total: {current_rep_count}")
                        print(f"   Last analysis: {result.get('last_rep_analysis', {})}")
                        last_rep_count = current_rep_count
                
                # Print debug summary every 30 frames (1 second at 30fps)
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    print(f"\n📊 Status Summary (Frame {frame_count}, {elapsed:.1f}s elapsed):")
                    if result:
                        print(f"  Session State: {result.get('session_state', 'Unknown')}")
                        print(f"  Movement Phase: {result.get('phase', 'Unknown')}")
                        print(f"  Rep Count: {result.get('rep_count', 0)}")
                        print(f"  Landmarks Detected: {result.get('landmarks_detected', False)}")
                        print(f"  FPS: {result.get('fps', 0):.1f}")
                    else:
                        print("  No result from processor")
                
            except Exception as e:
                print(f"❌ Error processing frame {frame_count}: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"\n⏰ Test completed after 30 seconds ({frame_count} frames processed)")
        print(f"📊 Final rep count: {last_rep_count}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            cap.release()
            session_summary = processor.end_session()
            print("✅ Cleanup completed")
            print(f"📋 Session summary: {session_summary}")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

if __name__ == "__main__":
    test_webcam_rep_detection_console()
