# ai_fitness_coach/src/pose/pose_detector.py
import mediapipe as mp
import cv2
import numpy as np
import math
from typing import Optional, Dict, Any

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Optimized settings for better performance and fewer warnings
        self._pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # Fastest model
            smooth_landmarks=True,
            enable_segmentation=False,  # Disable segmentation for better performance
            min_detection_confidence=0.5,  # Increased for better stability
            min_tracking_confidence=0.5   # Increased for better stability
        )
        self.debug_mode = False  # Disable debug by default for performance
        self.results = None

    def process_frame(self, frame_rgb):
        """Processes a frame and stores the results."""
        try:
            # Check if the frame is valid
            if frame_rgb is None or frame_rgb.size == 0:
                if self.debug_mode:
                    print("❌ Invalid frame provided to pose detector")
                return None
                
            # Process the frame
            self.results = self._pose.process(frame_rgb)
            
            # Optional debug logging
            if self.debug_mode:
                if self.results and self.results.pose_landmarks:
                    print("✅ Pose detected successfully!")
                else:
                    print("❌ No pose detected in frame")
                    
            return self.results
        except Exception as e:
            print(f"❌ Error in pose detection: {e}")
            import traceback
            traceback.print_exc()
            return None

    def draw_landmarks(self, frame):
        """Draws the pose landmarks on a given BGR frame."""
        if self.results and self.results.pose_landmarks:
            try:
                # Make a copy of the frame for drawing
                height, width = frame.shape[:2]
                
                # First, add a slight darkening effect to make landmarks more visible
                overlay = frame.copy()
                cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
                
                # Draw landmarks with enhanced visibility
                self.mp_drawing.draw_landmarks(
                    frame,
                    self.results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    # Landmarks (joints) style - bright yellow larger circles
                    self.mp_drawing.DrawingSpec(
                        color=(0, 255, 255),  # Bright yellow (BGR format)
                        thickness=8, 
                        circle_radius=8
                    ),
                    # Connections (bones) style - bright green thicker lines
                    self.mp_drawing.DrawingSpec(
                        color=(0, 255, 0),  # Bright green (BGR format)
                        thickness=6, 
                        circle_radius=3
                    )
                )
                
                # Draw additional large markers for key points to make them more visible
                landmark_list = self.results.pose_landmarks.landmark
                for idx, landmark in enumerate(landmark_list):
                    # Only draw key landmarks bigger
                    if idx in [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]:  # Head, shoulders, elbows, wrists, hips, knees, ankles
                        x, y = int(landmark.x * width), int(landmark.y * height)
                        # Draw a larger circle around important landmarks
                        cv2.circle(frame, (x, y), 10, (255, 0, 255), -1)  # Filled magenta circle
                
                # Draw a message indicating pose detected
                cv2.putText(
                    frame,
                    "POSE DETECTED ✓",
                    (10, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),  # Green
                    2
                )
                
                if self.debug_mode:
                    print("✅ Landmarks drawn successfully!")
                
                return True
            except Exception as e:
                print(f"Error drawing landmarks: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        if self.debug_mode:
            print("⚠️ No pose landmarks available to draw")
        return False
    
    def calculate_angle(self, point1, point2, point3):
        """
        Calculate angle between three points using vector mathematics.
        
        Args:
            point1, point2, point3: MediaPipe landmark objects
            
        Returns:
            Angle in degrees
        """
        try:
            # Get coordinates
            a = np.array([point1.x, point1.y])
            b = np.array([point2.x, point2.y])
            c = np.array([point3.x, point3.y])
            
            # Calculate vectors
            ba = a - b
            bc = c - b
            
            # Calculate angle
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
            
            return np.degrees(angle)
        except:
            return 0.0
    
    def calculate_joint_angles(self, landmarks):
        """
        Calculate all relevant joint angles for squat analysis.
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            Dictionary containing all calculated angles
        """
        if not landmarks:
            return {}
        
        try:
            # Key landmark indices for MediaPipe pose
            LEFT_HIP = 23
            RIGHT_HIP = 24
            LEFT_KNEE = 25
            RIGHT_KNEE = 26
            LEFT_ANKLE = 27
            RIGHT_ANKLE = 28
            LEFT_SHOULDER = 11
            RIGHT_SHOULDER = 12
            LEFT_HEEL = 29
            RIGHT_HEEL = 30
            
            angles = {}
            
            # Left knee angle (hip-knee-ankle)
            angles['knee_left'] = self.calculate_angle(
                landmarks[LEFT_HIP], landmarks[LEFT_KNEE], landmarks[LEFT_ANKLE]
            )
            
            # Right knee angle (hip-knee-ankle)
            angles['knee_right'] = self.calculate_angle(
                landmarks[RIGHT_HIP], landmarks[RIGHT_KNEE], landmarks[RIGHT_ANKLE]
            )
            
            # Hip angle (average of left and right)
            left_hip_angle = self.calculate_angle(
                landmarks[LEFT_SHOULDER], landmarks[LEFT_HIP], landmarks[LEFT_KNEE]
            )
            right_hip_angle = self.calculate_angle(
                landmarks[RIGHT_SHOULDER], landmarks[RIGHT_HIP], landmarks[RIGHT_KNEE]
            )
            angles['hip'] = (left_hip_angle + right_hip_angle) / 2
            
            # Back angle (shoulder-hip-knee, indicates forward lean)
            angles['back'] = self.calculate_angle(
                landmarks[LEFT_SHOULDER], landmarks[LEFT_HIP], landmarks[LEFT_KNEE]
            )
            
            # Ankle angles
            angles['ankle_left'] = self.calculate_angle(
                landmarks[LEFT_KNEE], landmarks[LEFT_ANKLE], landmarks[LEFT_HEEL]
            )
            angles['ankle_right'] = self.calculate_angle(
                landmarks[RIGHT_KNEE], landmarks[RIGHT_ANKLE], landmarks[RIGHT_HEEL]
            )
            
            return angles
            
        except Exception as e:
            return {}
    
    def calculate_center_of_mass(self, landmarks):
        """
        Estimate center of mass position.
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            Tuple of (x, y) coordinates
        """
        if not landmarks:
            return (0.0, 0.0)
        
        try:
            # Use key body points to estimate COM
            key_points = [
                landmarks[11],  # Left shoulder
                landmarks[12],  # Right shoulder
                landmarks[23],  # Left hip
                landmarks[24],  # Right hip
            ]
            
            avg_x = sum(point.x for point in key_points) / len(key_points)
            avg_y = sum(point.y for point in key_points) / len(key_points)
            
            return (avg_x, avg_y)
            
        except:
            return (0.0, 0.0)
    
    def calculate_landmark_visibility(self, landmarks):
        """
        Calculate average visibility of key landmarks.
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            Average visibility score (0-1)
        """
        if not landmarks:
            return 0.0
        
        try:
            key_landmarks = [11, 12, 23, 24, 25, 26, 27, 28]  # Key points for squat
            visibilities = [landmarks[i].visibility for i in key_landmarks if i < len(landmarks)]
            
            return sum(visibilities) / len(visibilities) if visibilities else 0.0
            
        except:
            return 0.0