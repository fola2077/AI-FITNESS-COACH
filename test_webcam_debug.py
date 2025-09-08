#!/usr/bin/env python3
"""
Debug test script for webcam rep detection
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

def test_webcam_rep_detection():
    """Test webcam rep detection with comprehensive debugging."""
    print("=" * 60)
    print("🔍 WEBCAM REP DETECTION DEBUG TEST")
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
        
        print("\n" + "=" * 60)
        print("🎥 LIVE WEBCAM ANALYSIS - Press 'q' to quit")
        print("📝 Watch console for debug output")
        print("🏃‍♂️ Perform squats to test rep detection")
        print("=" * 60)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame from webcam")
                break
                
            frame_count += 1
            
            # Process frame with debugging
            try:
                result = processor.process_frame(frame)
                
                # Display current status on frame
                if result:
                    cv2.putText(frame, f"State: {result.get('session_state', 'Unknown')}", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Phase: {result.get('phase', 'Unknown')}", 
                              (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Reps: {result.get('rep_count', 0)}", 
                              (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Frame: {frame_count}", 
                              (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Check for new reps
                    current_rep_count = result.get('rep_count', 0)
                    if current_rep_count > last_rep_count:
                        print(f"\n🎉 NEW REP DETECTED! Total: {current_rep_count}")
                        last_rep_count = current_rep_count
                
                # Show frame
                cv2.imshow('Webcam Debug Test', frame)
                
                # Print debug summary every 30 frames (1 second at 30fps)
                if frame_count % 30 == 0:
                    print(f"\n📊 Status Summary (Frame {frame_count}):")
                    if result:
                        print(f"  Session State: {result.get('session_state', 'Unknown')}")
                        print(f"  Movement Phase: {result.get('phase', 'Unknown')}")
                        print(f"  Rep Count: {result.get('rep_count', 0)}")
                        print(f"  Landmarks Detected: {result.get('landmarks_detected', False)}")
                    else:
                        print("  No result from processor")
                
            except Exception as e:
                print(f"❌ Error processing frame {frame_count}: {e}")
                import traceback
                traceback.print_exc()
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n🛑 Quit requested by user")
                break
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            cap.release()
            cv2.destroyAllWindows()
            processor.end_session()
            print("✅ Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    test_webcam_rep_detection()
