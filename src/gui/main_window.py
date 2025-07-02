import sys
import cv2
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QFileDialog
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
from src.capture.camera import CameraManager
from src.processing.pose_processor import PoseProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Fitness Coach")
        self.resize(1280, 720) # Set a good default size

        self.video_label = QLabel("Press 'Webcam' or 'Open Video' to start")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(False)

        self.webcam_button = QPushButton("Webcam")
        self.video_button = QPushButton("Open Video")

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.webcam_button)
        layout.addWidget(self.video_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.camera_manager = None
        self.pose_processor = PoseProcessor()
        self.timer = QTimer()

        self.webcam_button.clicked.connect(self.start_webcam)
        self.video_button.clicked.connect(self.open_video_file)
        self.timer.timeout.connect(self.update_frame)

    def start_webcam(self):
        self.setup_camera(source=0)

    def open_video_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi)")
        if filepath:
            self.setup_camera(source=filepath)

    def setup_camera(self, source):
        if self.timer.isActive():
            self.timer.stop()
        if self.camera_manager:
            self.camera_manager.release()

        try:
            self.camera_manager = CameraManager(source)
            if not self.camera_manager.isOpened():
                raise RuntimeError(f"Could not open source '{source}'")
            
            # Reset the processor for the new video/session
            self.pose_processor.reset()
            self.timer.start(30) # ~33 FPS

        except RuntimeError as e:
            self.video_label.setText(f"Error: {e}")

    def update_frame(self):
        if not self.camera_manager:
            return

        frame = self.camera_manager.get_frame()
        # Gracefully handle the end of the video
        if frame is None:
            self.timer.stop()
            self.video_label.setText("Video finished or stream ended.")
            return

        processed_frame = self.pose_processor.process_frame(frame)
        self.display_frame(processed_frame)

    def display_frame(self, frame):
        # The frame from the processor is already annotated (BGR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale pixmap to fit the label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        self.timer.stop()
        if self.camera_manager:
            self.camera_manager.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())