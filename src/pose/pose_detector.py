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

    def detect(self, frame_bgr):
        """
        Returns a list[Landmark2D] in pixel coords,
        or None when no person is detected.
        """
        h, w, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._pose.process(frame_rgb)

        if not results.pose_landmarks:
            return None

        landmarks = []
        for lm in results.pose_landmarks.landmark:
            landmarks.append(
                Landmark2D(
                    x=int(lm.x * w),
                    y=int(lm.y * h),
                    visibility=lm.visibility,
                )
            )
        return landmarks

    def close(self):
        self._pose.close()