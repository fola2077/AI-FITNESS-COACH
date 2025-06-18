from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication
from PySide6.QtCore     import QTimer, Qt
import sys
import cv2

from capture.camera        import CameraManager
from gui.widgets.video_widget import VideoWidget
from pose.pose_detector    import PoseDetector, Landmark2D



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize camera and pose detector
        self.camera = CameraManager()
        self.pose_detector = PoseDetector()
        
        # Create the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Create video widget
        self.video_widget = VideoWidget()
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
        frame = self.camera.get_frame()
        if frame is None:
            return

        landmarks = self.pose_detector.detect(frame)

        # ----- rudimentary overlay: hips & knees -----
        if landmarks:
            # MediaPipe indices: 23 L-hip, 24 R-hip, 25 L-knee, 26 R-knee
            key_ids = (23, 24, 25, 26)
            for idx in key_ids:
                lm: Landmark2D = landmarks[idx]
                if lm.visibility > 0.5:               # ignore occluded pts
                    cv2.circle(frame, (lm.x, lm.y), 6, (0, 255, 0), -1)

        self.video_widget.update_frame(frame)

    def closeEvent(self, event):
        self.pose_detector.close()
        self.camera.release()
        super().closeEvent(event)


def run():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())