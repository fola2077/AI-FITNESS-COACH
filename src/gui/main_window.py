import time
from collections import deque

from utils.math_utils import joint_angle

import mediapipe as mp
_MP_DRAW = mp.solutions.drawing_utils
_MP_STYLE = mp.solutions.drawing_styles

from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication
from PySide6.QtCore import QTimer, Qt
import sys
import cv2

from capture.camera import CameraManager
from gui.widgets.video_widget import VideoWidget
from pose.pose_detector import PoseDetector, Landmark2D

from preprocess.one_euro import OneEuroFilter
import time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize camera and pose detector
        self.setWindowTitle("AI Fitness Coach – Early Slice")
        
        # OPTIMIZATION 1: Use faster camera settings
        self.camera = CameraManager(width=640, height=480, fps=30)
        
        # OPTIMIZATION 2: Use lowest model complexity for speed
        self.pose_detector = PoseDetector(
            model_complexity=0,  # Keep this at 0 for speed
            min_detection_confidence=0.7,  # Lower threshold for faster detection
            min_tracking_confidence=0.5
        )

        # One-Euro filters – one (x,y) pair for each of the 33 pose landmarks
        self._filters = {
            idx: (OneEuroFilter(), OneEuroFilter())
            for idx in range(33)
        }

        # Create the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Create video widget
        self.video_widget = VideoWidget()
        self._frame_times = deque(maxlen=30)
        self._last_ts = time.perf_counter()

        self.phase = "TOP"
        self.knee_ang = 0.0  # Cache knee angle to avoid recalculation

        layout.addWidget(self.video_widget)
        
        # Create control buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        
        # OPTIMIZATION 3: Use more aggressive timer for 30 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        
        # Connect buttons
        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        
        # Start capture automatically
        self.start_capture()

    def start_capture(self):
        # OPTIMIZATION 4: 30 FPS = 33.33ms, but use 30ms for buffer
        self.timer.start(30)  # More aggressive timing for 30+ FPS
        
    def stop_capture(self):
        self.timer.stop()

    def _update_frame(self):
        # ---------- FPS timing ----------
        now = time.perf_counter()
        if self._frame_times:
            self._frame_times.append(now - self._last_ts)
        else:
            self._frame_times.append(0.033)  # Initialize with target frame time
        self._last_ts = now
        fps = 1.0 / (sum(self._frame_times) / len(self._frame_times)) if self._frame_times else 30

        # ---------- grab frame ----------
        frame = self.camera.get_frame()
        if frame is None:
            return

        detected = self.pose_detector.detect(frame)

        if detected:
            # unpack tuple: (pixel-coords list, raw MediaPipe proto)
            lm_pixel, mp_landmarks = detected

            # ---------- One-Euro smoothing ----------
            for idx, lm in enumerate(lm_pixel):
                fx, fy = self._filters[idx]
                lm.x = int(fx.filter(lm.x, now))
                lm.y = int(fy.filter(lm.y, now))

            # ---------- right-knee angle ----------
            hip, knee, ankle = lm_pixel[24], lm_pixel[26], lm_pixel[28]
            if hip.visibility > 0.5 and knee.visibility > 0.5 and ankle.visibility > 0.5:
                self.knee_ang = joint_angle(hip.x, hip.y, knee.x, knee.y, ankle.x, ankle.y)
            # Don't reset to 0.0 if visibility is low - keep last valid angle

            # ---------- phase detector ----------
            prev_phase = self.phase
            if self.knee_ang > 140:
                self.phase = "TOP"
            elif self.knee_ang < 95:
                self.phase = "BOTTOM"
            elif self.knee_ang < 120 and prev_phase in ("TOP", "DESC"):
                self.phase = "DESC"
            elif self.knee_ang > 120 and prev_phase in ("BOTTOM", "ASC"):
                self.phase = "ASC"

            # OPTIMIZATION 5: Draw skeleton only - remove style for speed
            _MP_DRAW.draw_landmarks(
                frame,
                mp_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
                # Remove the style parameter for faster drawing
            )

        # OPTIMIZATION 6: Always draw text (even without detection) but use cached values
        cv2.putText(frame, f"FPS: {fps:5.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.putText(frame, f"Knee: {self.knee_ang:5.1f}°", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.putText(frame, f"Phase: {self.phase}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2, cv2.LINE_AA)

        # ---------- push to widget ----------
        self.video_widget.update_frame(frame)

    def closeEvent(self, event):
        self.pose_detector.close()
        self.camera.release()
        super().closeEvent(event)


def run():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())