import cv2
import numpy as np
from src.pose.pose_detector import PoseDetector
from src.utils.math_utils import joint_angle

class PoseProcessor:
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.phase = "START"
        self.phase_tracker = "START"

    def process_frame(self, frame):
        # 1. Detect Pose
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # --- FIX: Changed find_pose to process_frame ---
        self.pose_detector.process_frame(frame_rgb)

        # 2. Analyze Pose (if landmarks are found)
        results = {}
        # The results are now stored in self.pose_detector.results, so we check that
        if self.pose_detector.results.pose_landmarks:
            # Get coordinate tuples
            right_hip = self.pose_detector.get_landmark_coords('RIGHT_HIP')
            right_knee = self.pose_detector.get_landmark_coords('RIGHT_KNEE')
            right_ankle = self.pose_detector.get_landmark_coords('RIGHT_ANKLE')

            # Calculate knee angle using your 'joint_angle' function
            knee_angle = joint_angle(
                right_hip[0], right_hip[1],
                right_knee[0], right_knee[1],
                right_ankle[0], right_ankle[1]
            )

            # --- Squat Phase Logic ---
            if knee_angle > 160:
                self.phase_tracker = "TOP"
            elif knee_angle < 90 and self.phase_tracker == "TOP":
                self.phase_tracker = "BOTTOM"
            
            results['knee_angle'] = knee_angle
            results['phase'] = self.phase_tracker

        # 3. Draw Overlays
        # --- FIX: Pass the original BGR frame to draw on ---
        annotated_frame = self.draw_overlays(frame.copy(), results)
        return annotated_frame, results

    def draw_overlays(self, frame, results):
        # --- FEATURE: Ensure landmarks are drawn on the frame ---
        # This was correct before, but confirming it's here.
        self.pose_detector.draw_landmarks(frame)
        
        # Display Info
        info_text = ""
        if 'knee_angle' in results:
            info_text += f"Knee Angle: {int(results['knee_angle'])} | "
        if 'phase' in results:
            info_text += f"Phase: {results['phase']}"

        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        return frame