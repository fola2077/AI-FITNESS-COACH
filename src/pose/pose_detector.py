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

    def draw_landmarks(self, frame):
        """Draws the pose landmarks on a given BGR frame."""
        if self.results and self.results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                self.results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
            )