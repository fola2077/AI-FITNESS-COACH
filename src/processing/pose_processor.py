# ai_fitness_coach/src/processing/pose_processor.py
import cv2
import numpy as np
import time
from src.pose.pose_detector import PoseDetector
from src.utils.math_utils import joint_angle

class PoseProcessor:
    def __init__(self):
        self.pose_detector = PoseDetector()
        
        # State Management
        self.rep_counter = 0
        self.phase = "TOP"
        self.feedback_log = []

        # FPS calculation
        self.start_time = time.time()
        self.frame_counter = 0
        self.fps = 0

    def reset(self):
        """Resets the processor for a new session."""
        self.rep_counter = 0
        self.phase = "TOP"
        self.feedback_log = []
        self.start_time = time.time()
        self.frame_counter = 0
        self.fps = 0

    def process_frame(self, frame):
        # 1. FPS Calculation
        self.frame_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            self.fps = self.frame_counter / elapsed_time
            self.frame_counter = 0
            self.start_time = time.time()

        # 2. Pose Detection
        self.pose_detector.process_frame(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 3. Form Analysis
        metrics, faults = {}, []
        if self.pose_detector.results and self.pose_detector.results.pose_landmarks:
            landmarks = self.pose_detector.results.pose_landmarks.landmark
            
            # --- Biomechanical Calculations ---
            try:
                # Get landmarks for calculations
                left_shoulder = landmarks[11].x, landmarks[11].y
                left_hip = landmarks[23].x, landmarks[23].y
                left_knee = landmarks[25].x, landmarks[25].y
                left_ankle = landmarks[27].x, landmarks[27].y
                
                right_knee_x = landmarks[26].x
                right_ankle_x = landmarks[28].x

                # Calculate metrics
                metrics['knee_angle'] = joint_angle(left_hip[0], left_hip[1], left_knee[0], left_knee[1], left_ankle[0], left_ankle[1])
                metrics['back_angle'] = joint_angle(left_shoulder[0], left_shoulder[1], left_hip[0], left_hip[1], left_knee[0], left_knee[1])
                
                # --- Phase Detection ---
                previous_phase = self.phase
                if metrics['knee_angle'] > 160:
                    self.phase = "TOP"
                elif previous_phase == "TOP" and metrics['knee_angle'] < 160:
                    self.phase = "DOWN"
                elif metrics['knee_angle'] < 90:
                    self.phase = "BOTTOM"
                elif previous_phase == "BOTTOM" and metrics['knee_angle'] > 90:
                    self.phase = "UP"

                # --- Repetition Counting ---
                if self.phase == "TOP" and previous_phase in ["UP", "BOTTOM"]:
                    self.rep_counter += 1
                    # Log the feedback for the completed rep here if you have a scorecard
                
                # --- Real-time Fault Detection ---
                if metrics['back_angle'] < 150:
                    faults.append("BACK ROUNDING")
                
                # Add more fault checks here...

            except Exception as e:
                # This block prevents crashes if a landmark is not visible
                pass 

        metrics['fps'] = self.fps

        # 4. Draw Overlays
        annotated_frame = self.draw_overlays(frame.copy(), metrics, faults)
        return annotated_frame

    def draw_overlays(self, frame, metrics, faults):
        # Draw the pose skeleton
        self.pose_detector.draw_landmarks(frame)
        
        # Draw the horizontal metrics bar
        bar_height = 60
        cv2.rectangle(frame, (0, 0), (frame.shape[1], bar_height), (0, 0, 0, 128), -1)

        # Display Reps, Phase, and FPS
        info_text = f"Reps: {self.rep_counter}   |   Phase: {self.phase}   |   FPS: {int(metrics.get('fps', 0))}"
        cv2.putText(frame, info_text, (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Display Real-time Faults
        if faults:
            fault_text = "WARNING: " + ", ".join(faults)
            (w, h), _ = cv2.getTextSize(fault_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            cv2.putText(frame, fault_text, (frame.shape[1] - w - 15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        return frame