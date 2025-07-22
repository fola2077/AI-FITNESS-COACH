#!/usr/bin/env python3
"""
Pose Detection Diagnostic Tool
Diagnoses pose detection issues in the AI Fitness Coach
"""
import sys
import cv2
import numpy as np
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_pose_detection():
    """Test pose detection with webcam"""
    print("🔬 Testing Pose Detection with Webcam")
    print("=" * 50)
    
    try:
        from src.pose.pose_detector import PoseDetector
        from src.capture.camera import CameraManager
        
        print("✅ Imports successful")
        
        # Initialize pose detector
        detector = PoseDetector()
        print("✅ PoseDetector initialized")
        
        # Initialize camera
        camera = CameraManager(0)  # Webcam
        if not camera.isOpened():
            print("❌ Cannot open webcam")
            return False
        
        print("✅ Webcam opened")
        print("\n🎥 Starting live pose detection test...")
        print("Press 'q' to quit, 's' to save screenshot")
        
        frame_count = 0
        detection_count = 0
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("❌ Failed to get frame")
                break
            
            frame_count += 1
            
            # Convert BGR to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = detector.process_frame(frame_rgb)
            
            # Check if pose detected
            landmarks_detected = results and results.pose_landmarks
            
            if landmarks_detected:
                detection_count += 1
                # Draw landmarks
                detector.draw_landmarks(frame)
                
                # Add detection indicator
                cv2.putText(frame, f"POSE DETECTED! ({detection_count}/{frame_count})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Show confidence
                if hasattr(results.pose_landmarks, 'visibility'):
                    avg_visibility = np.mean([lm.visibility for lm in results.pose_landmarks.landmark])
                    cv2.putText(frame, f"Avg Visibility: {avg_visibility:.2f}", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            else:
                cv2.putText(frame, f"NO POSE DETECTED ({detection_count}/{frame_count})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Show frame info
            cv2.putText(frame, f"Frame: {frame_count}", 
                       (10, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Size: {frame.shape[1]}x{frame.shape[0]}", 
                       (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Pose Detection Test', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"pose_test_frame_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"💾 Screenshot saved: {filename}")
            
            # Stop after 300 frames for automatic testing
            if frame_count >= 300:
                break
        
        camera.release()
        cv2.destroyAllWindows()
        
        # Results
        detection_rate = (detection_count / frame_count) * 100 if frame_count > 0 else 0
        print(f"\n📊 Test Results:")
        print(f"   Total frames: {frame_count}")
        print(f"   Poses detected: {detection_count}")
        print(f"   Detection rate: {detection_rate:.1f}%")
        
        if detection_rate > 50:
            print("✅ Pose detection working well!")
            return True
        elif detection_rate > 10:
            print("⚠️  Pose detection working but low rate. Check lighting and positioning.")
            return True
        else:
            print("❌ Pose detection not working properly.")
            return False
        
    except Exception as e:
        print(f"❌ Error in pose detection test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_pose_detection(video_path):
    """Test pose detection with a video file"""
    print(f"🔬 Testing Pose Detection with Video: {video_path}")
    print("=" * 50)
    
    try:
        from src.pose.pose_detector import PoseDetector
        from src.capture.camera import CameraManager
        
        if not Path(video_path).exists():
            print(f"❌ Video file not found: {video_path}")
            return False
        
        # Initialize
        detector = PoseDetector()
        camera = CameraManager(video_path)
        
        if not camera.isOpened():
            print(f"❌ Cannot open video: {video_path}")
            return False
        
        print("✅ Video opened successfully")
        
        frame_count = 0
        detection_count = 0
        
        print("🎥 Processing video frames...")
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                break
            
            frame_count += 1
            
            # Convert BGR to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = detector.process_frame(frame_rgb)
            
            # Check if pose detected
            if results and results.pose_landmarks:
                detection_count += 1
                # Draw landmarks
                detector.draw_landmarks(frame)
            
            # Show every 30th frame
            if frame_count % 30 == 0:
                cv2.putText(frame, f"Frame {frame_count}: {'POSE' if results and results.pose_landmarks else 'NO POSE'}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, 
                           (0, 255, 0) if results and results.pose_landmarks else (0, 0, 255), 2)
                cv2.imshow('Video Pose Detection Test', frame)
                cv2.waitKey(1)
        
        camera.release()
        cv2.destroyAllWindows()
        
        # Results
        detection_rate = (detection_count / frame_count) * 100 if frame_count > 0 else 0
        print(f"\n📊 Video Test Results:")
        print(f"   Total frames: {frame_count}")
        print(f"   Poses detected: {detection_count}")
        print(f"   Detection rate: {detection_rate:.1f}%")
        
        return detection_rate > 10
        
    except Exception as e:
        print(f"❌ Error in video pose detection test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mediapipe_directly():
    """Test MediaPipe directly without our wrapper"""
    print("🔬 Testing MediaPipe Directly")
    print("=" * 50)
    
    try:
        import mediapipe as mp
        import cv2
        
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        
        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open webcam for direct test")
            return False
        
        print("✅ Direct MediaPipe test starting...")
        print("Press 'q' to quit")
        
        frame_count = 0
        detection_count = 0
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
            
            frame_count += 1
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # To improve performance
            image_rgb.flags.writeable = False
            
            # Make detection
            results = pose.process(image_rgb)
            
            # Draw the pose annotation on the image
            image_rgb.flags.writeable = True
            image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            
            if results.pose_landmarks:
                detection_count += 1
                mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                cv2.putText(image, f"POSE DETECTED! ({detection_count}/{frame_count})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(image, f"NO POSE ({detection_count}/{frame_count})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow('Direct MediaPipe Test', image)
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
            
            # Auto-stop after 100 frames
            if frame_count >= 100:
                break
        
        cap.release()
        cv2.destroyAllWindows()
        pose.close()
        
        detection_rate = (detection_count / frame_count) * 100 if frame_count > 0 else 0
        print(f"\n📊 Direct MediaPipe Results:")
        print(f"   Detection rate: {detection_rate:.1f}%")
        
        return detection_rate > 10
        
    except Exception as e:
        print(f"❌ Direct MediaPipe test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🩺 AI Fitness Coach - Pose Detection Diagnostics")
    print("=" * 60)
    
    # Test 1: Direct MediaPipe test
    print("\n1️⃣ Testing MediaPipe directly...")
    mediapipe_works = test_mediapipe_directly()
    
    # Test 2: Our pose detector with webcam
    if mediapipe_works:
        print("\n2️⃣ Testing our PoseDetector with webcam...")
        our_detector_works = test_pose_detection()
    else:
        print("\n❌ Skipping our detector test due to MediaPipe issues")
        our_detector_works = False
    
    # Test 3: Video file if provided
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        print(f"\n3️⃣ Testing with video file: {video_path}")
        video_works = test_video_pose_detection(video_path)
    else:
        video_works = None
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"MediaPipe Direct:     {'✅ WORKING' if mediapipe_works else '❌ FAILED'}")
    print(f"Our PoseDetector:     {'✅ WORKING' if our_detector_works else '❌ FAILED'}")
    if video_works is not None:
        print(f"Video Processing:     {'✅ WORKING' if video_works else '❌ FAILED'}")
    
    if not mediapipe_works:
        print("\n🔧 RECOMMENDATIONS:")
        print("   • Check if webcam is working")
        print("   • Ensure good lighting")
        print("   • Position yourself fully in frame")
        print("   • Try: pip install --upgrade mediapipe")
        print("   • Try: pip install --upgrade opencv-python")
    elif not our_detector_works:
        print("\n🔧 RECOMMENDATIONS:")
        print("   • Check PoseDetector class implementation")
        print("   • Verify frame color conversion")
        print("   • Check confidence thresholds")
