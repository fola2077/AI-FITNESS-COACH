import time
from collections import deque

import mediapipe as mp                              #  add this
_MP_DRAW = mp.solutions.drawing_utils               #  add this
_MP_STYLE = mp.solutions.drawing_styles             #  add this


from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication
from PySide6.QtCore     import QTimer, Qt
import sys
import cv2

from capture.camera        import CameraManager
from gui.widgets.video_widget import VideoWidget
from pose.pose_detector    import PoseDetector, Landmark2D

from preprocess.one_euro import OneEuroFilter
import time



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize camera and pose detector
        self.camera = CameraManager()
        self.pose_detector = PoseDetector()

        # One-Euro filters – one (x,y) pair for each of the 33 pose landmarks
        self._filters = {
            idx: (OneEuroFilter(), OneEuroFilter())   # (filter_x, filter_y)
            for idx in range(33)
        }

        
        # Create the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Create video widget
        self.video_widget = VideoWidget()
        self._frame_times = deque(maxlen=30)   # store last 30 frame durations
        self._last_ts = time.perf_counter()
        layout.addWidget(self.video_widget)
        
        # Create control buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        
        # Setup timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        
        # Connect buttons
        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        
        # Start capture automatically
        self.start_capture()

    def start_capture(self):
        self.timer.start(33)  # ~30 FPS
        
    def stop_capture(self):
        self.timer.stop()

    def _update_frame(self):
        # --- timing section ---
        now = time.perf_counter()
        self._frame_times.append(now - self._last_ts)
        self._last_ts = now
        fps = 1.0 / (sum(self._frame_times) / len(self._frame_times)) if self._frame_times else 0


        frame = self.camera.get_frame()
        if frame is None:
            return

        detected = self.pose_detector.detect(frame)

        if detected:
            # unpack tuple: pixel landmarks list, and original mp_landmarks proto
            lm_pixel, mp_landmarks = detected

            # ------------ One-Euro smoothing ------------
            now = time.perf_counter()
            for idx, lm in enumerate(lm_pixel):
                fx, fy = self._filters[idx]
                lm.x = int(fx.filter(lm.x, now))
                lm.y = int(fy.filter(lm.y, now))
            # --------------------------------------------

            _MP_DRAW.draw_landmarks(
                frame,
                mp_landmarks,                         # still raw proto used for colours
                mp.solutions.pose.POSE_CONNECTIONS,
                landmark_drawing_spec=_MP_STYLE.get_default_pose_landmarks_style()
            )

        cv2.putText(
            frame,
            f"FPS: {fps:5.1f}",
            (10, 30),                    # x,y position
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,                         # font scale
            (0, 0, 255),               # text colour (B,G,R)
            2,                           # thickness
            cv2.LINE_AA,
        )
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