# ai_fitness_coach/src/gui/widgets/video_widget.py
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
import cv2


class VideoWidget(QLabel):
    """
    Simplest possible viewer: a QLabel that we keep
    stuffing with a fresh QPixmap every 33 ms.
    Later you can switch to QOpenGLWidget for shaders,
    but this is perfect for FPS ≤ 60.
    """

    def update_frame(self, frame_bgr):
        if frame_bgr is None:
            return

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        qimg = QImage(frame_rgb.data, w, h, QImage.Format_RGB888)

        # Qt copies the data only when necessary; keeping this short avoids
        # touch-by-touch memory churn.
        self.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
