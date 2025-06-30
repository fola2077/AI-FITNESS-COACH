import cv2
import numpy as np
import time
from src.pose.pose_detector import PoseDetector
from src.grading.form_grader import FormGrader # Import the new class

class PoseProcessor:
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.form_grader = FormGrader() # Create an instance of the grader
        
        # FPS calculation attributes
        self.start_time = time.time()
        self.frame_counter = 0
        self.fps = 0

    def process_frame(self, frame):
        # FPS Calculation
        self.frame_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            self.fps = self.frame_counter / elapsed_time
            self.frame_counter = 0
            self.start_time = time.time()
        
        # Pose Detection
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.pose_detector.process_frame(frame_rgb)

        # Form Grading
        metrics, faults = {}, []
        if self.pose_detector.results.pose_landmarks:
            metrics, faults = self.form_grader.grade_frame(self.pose_detector.results.pose_landmarks.landmark)

        # Add FPS to metrics for display
        metrics['fps'] = self.fps
        
        # Drawing Overlays
        annotated_frame = self.draw_overlays(frame.copy(), metrics, faults)
        return annotated_frame, metrics

    def draw_overlays(self, frame, metrics, faults):
        # Draw the pose skeleton
        self.pose_detector.draw_landmarks(frame)
        
        # --- Draw the Horizontal Metrics Bar ---
        bar_height = 50
        cv2.rectangle(frame, (0, 0), (frame.shape[1], bar_height), (0, 0, 0), -1)
        
        # --- Display Reps and Phase ---
        info_text = f"Reps: {self.form_grader.rep_counter} | Phase: {self.form_grader.phase}"
        cv2.putText(frame, info_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # --- Display Real-time Faults ---
        if faults:
            fault_text = "WARNING: " + ", ".join(faults)
            cv2.putText(frame, fault_text, (250, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        # --- Display FPS ---
        fps_text = f"FPS: {int(metrics.get('fps', 0))}"
        cv2.putText(frame, fps_text, (frame.shape[1] - 150, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        return frame