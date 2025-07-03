# ai_fitness_coach/src/pose/pose_detector.py
import mediapipe as mp
import cv2

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self._pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.results = None

    def process_frame(self, frame_rgb):
        """Processes a frame and stores the results."""
        self.results = self._pose.process(frame_rgb)
        return self.results

    def draw_landmarks(self, frame):
        """Draws the pose landmarks on a given BGR frame."""
        if self.results and self.results.pose_landmarks:
            # Draw landmarks with better visibility
            self.mp_drawing.draw_landmarks(
                frame,
                self.results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                # Landmarks (joints) style - bright cyan circles
                self.mp_drawing.DrawingSpec(
                    color=(255, 255, 0),  # Bright cyan (BGR format)
                    thickness=3, 
                    circle_radius=4
                ),
                # Connections (bones) style - bright green lines
                self.mp_drawing.DrawingSpec(
                    color=(0, 255, 0),  # Bright green (BGR format)
                    thickness=3, 
                    circle_radius=2
                )
            )
            return True
        return False