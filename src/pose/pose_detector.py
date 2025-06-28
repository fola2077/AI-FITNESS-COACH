"""
2-D MediaPipe pose wrapper — minimal, no rules, no smoothing.
"""

from dataclasses import dataclass
import mediapipe as mp
import cv2


@dataclass
class Landmark2D:
    x: int
    y: int
    visibility: float


class PoseDetector:
    _mp_pose = mp.solutions.pose

    def __init__(
        self,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
    ):
        self._pose = self._mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            smooth_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.results = None  # Store latest results

    def detect(self, frame_bgr):
        """
        Returns a list[Landmark2D] in pixel coords,
        or None when no person is detected.
        """
        h, w, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._pose.process(frame_rgb)
        self.results = results  # Store results for external access
        if not results.pose_landmarks:
            return None
        pixel_list = []
        for lm in results.pose_landmarks.landmark:
            pixel_list.append(
                Landmark2D(int(lm.x * w), int(lm.y * h), lm.visibility)
            )
        return pixel_list, results.pose_landmarks

    def process_frame(self, frame_rgb):
        """
        Processes an RGB frame and returns the frame with pose landmarks drawn and the results object.
        """
        self.results = self._pose.process(frame_rgb)
        output_frame = frame_rgb.copy()
        if self.results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                output_frame,
                self.results.pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS
            )
        return output_frame, self.results

    def draw_landmarks(self, frame):
        """Draw pose landmarks on the given frame if available."""
        if hasattr(self, 'results') and self.results and self.results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                self.results.pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS
            )

    def get_landmark_coords(self, landmark_name):
        """Return (x, y) tuple for a given landmark name."""
        if not (hasattr(self, 'results') and self.results and self.results.pose_landmarks):
            return (0, 0)
        idx = self._mp_pose.PoseLandmark[landmark_name].value
        lm = self.results.pose_landmarks.landmark[idx]
        return (lm.x, lm.y)

    def close(self):
        self._pose.close()