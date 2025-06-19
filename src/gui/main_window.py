import time
from collections import deque

from utils.math_utils import joint_angle

import mediapipe as mp
_MP_DRAW = mp.solutions.drawing_utils
_MP_STYLE = mp.solutions.drawing_styles

from PySide6.QtWidgets import (QMainWindow, QWidget, QPushButton, QVBoxLayout, 
                               QHBoxLayout, QApplication, QFileDialog, QLabel, 
                               QSlider, QComboBox)
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
        
        # Initialize
        self.setWindowTitle("AI Fitness Coach – Video/Live Testing")
        self.camera = None
        self.pose_detector = PoseDetector(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # One-Euro filters
        self._filters = {
            idx: (OneEuroFilter(), OneEuroFilter())
            for idx in range(33)
        }

        # UI State
        self.is_playing = False
        self.is_video_mode = False
        
        # Performance tracking
        self._frame_times = deque(maxlen=30)
        self._last_ts = time.perf_counter()
        self.phase = "TOP"
        self.knee_ang = 0.0

        self._setup_ui()
        self._setup_timer()
        
        # Start with live camera by default
        self._switch_to_live()

    def _setup_ui(self):
        """Setup the user interface."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Video widget
        self.video_widget = VideoWidget()
        layout.addWidget(self.video_widget)
        
        # Control panel
        control_panel = QHBoxLayout()
        
        # Source selection
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Live Camera", "Video File"])
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        control_panel.addWidget(QLabel("Source:"))
        control_panel.addWidget(self.source_combo)
        
        # File selection button
        self.file_button = QPushButton("Select Video File")
        self.file_button.clicked.connect(self._select_video_file)
        self.file_button.setEnabled(False)
        control_panel.addWidget(self.file_button)
        
        # Play/Pause button
        self.play_button = QPushButton("Pause")
        self.play_button.clicked.connect(self._toggle_playback)
        control_panel.addWidget(self.play_button)
        
        # Restart button (for videos)
        self.restart_button = QPushButton("Restart")
        self.restart_button.clicked.connect(self._restart_video)
        self.restart_button.setEnabled(False)
        control_panel.addWidget(self.restart_button)
        
        layout.addLayout(control_panel)
        
        # Video progress slider (for video files)
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.progress_slider)
        
        # Info labels
        self.info_label = QLabel("Live Camera Mode")
        layout.addWidget(self.info_label)
        
    def _setup_timer(self):
        """Setup the frame update timer."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        
    def _on_source_changed(self, source_text):
        """Handle source selection change."""
        if source_text == "Video File":
            self.file_button.setEnabled(True)
            self.restart_button.setEnabled(True)
            self.progress_slider.setEnabled(True)
        else:
            self.file_button.setEnabled(False)
            self.restart_button.setEnabled(False)
            self.progress_slider.setEnabled(False)
            self._switch_to_live()
    
    def _select_video_file(self):
        """Open file dialog to select video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Video File", 
            "", 
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;All Files (*)"
        )
        
        if file_path:
            self._switch_to_video(file_path)
    
    def _switch_to_live(self):
        """Switch to live camera mode."""
        self._stop_playback()
        
        if self.camera:
            self.camera.release()
        
        try:
            self.camera = CameraManager(source=0)  # Camera ID 0
            self.is_video_mode = False
            self.info_label.setText("Live Camera Mode")
            self.source_combo.setCurrentText("Live Camera")
            self._start_playback()
        except RuntimeError as e:
            self.info_label.setText(f"Camera Error: {e}")
    
    def _switch_to_video(self, video_path):
        """Switch to video file mode."""
        self._stop_playback()
        
        if self.camera:
            self.camera.release()
        
        try:
            self.camera = CameraManager(source=video_path)
            self.is_video_mode = True
            
            # Setup progress slider
            self.progress_slider.setMaximum(self.camera.total_frames - 1)
            self.progress_slider.setValue(0)
            
            # Update info
            current_time, total_time = self.camera.get_time_info()
            self.info_label.setText(
                f"Video: {video_path.split('/')[-1]} | "
                f"Duration: {total_time:.1f}s | "
                f"FPS: {self.camera.video_fps:.1f}"
            )
            
            self._start_playback()
            
        except RuntimeError as e:
            self.info_label.setText(f"Video Error: {e}")
    
    def _start_playback(self):
        """Start video playback."""
        if self.camera:
            # Use different timer intervals based on source
            if self.is_video_mode:
                # Match video FPS, but cap at 30 FPS for performance
                interval = max(33, int(1000 / self.camera.video_fps))
            else:
                interval = 30  # 30ms for live camera (30+ FPS)
            
            self.timer.start(interval)
            self.is_playing = True
            self.play_button.setText("Pause")
    
    def _stop_playback(self):
        """Stop video playback."""
        self.timer.stop()
        self.is_playing = False
        self.play_button.setText("Play")
    
    def _toggle_playback(self):
        """Toggle play/pause."""
        if self.is_playing:
            self._stop_playback()
        else:
            self._start_playback()
    
    def _restart_video(self):
        """Restart video from beginning."""
        if self.camera and self.is_video_mode:
            self.camera.restart_video()
            self.progress_slider.setValue(0)
    
    def _on_slider_changed(self, value):
        """Handle progress slider changes."""
        if self.camera and self.is_video_mode and not self.is_playing:
            self.camera.seek_to_frame(value)

    def _update_frame(self):
        """Main frame update loop."""
        if not self.camera:
            return
            
        # FPS timing
        now = time.perf_counter()
        if self._frame_times:
            self._frame_times.append(now - self._last_ts)
        else:
            self._frame_times.append(0.033)
        self._last_ts = now
        fps = 1.0 / (sum(self._frame_times) / len(self._frame_times)) if self._frame_times else 30

        # Get frame
        frame = self.camera.get_frame()
        if frame is None:
            return

        # Pose detection
        detected = self.pose_detector.detect(frame)

        if detected:
            lm_pixel, mp_landmarks = detected

            # One-Euro smoothing
            for idx, lm in enumerate(lm_pixel):
                fx, fy = self._filters[idx]
                lm.x = int(fx.filter(lm.x, now))
                lm.y = int(fy.filter(lm.y, now))

            # Right-knee angle
            hip, knee, ankle = lm_pixel[24], lm_pixel[26], lm_pixel[28]
            if hip.visibility > 0.5 and knee.visibility > 0.5 and ankle.visibility > 0.5:
                self.knee_ang = joint_angle(hip.x, hip.y, knee.x, knee.y, ankle.x, ankle.y)

            # Phase detection
            prev_phase = self.phase
            if self.knee_ang > 140:
                self.phase = "TOP"
            elif self.knee_ang < 95:
                self.phase = "BOTTOM"
            elif self.knee_ang < 120 and prev_phase in ("TOP", "DESC"):
                self.phase = "DESC"
            elif self.knee_ang > 120 and prev_phase in ("BOTTOM", "ASC"):
                self.phase = "ASC"

            # Draw skeleton
            _MP_DRAW.draw_landmarks(
                frame,
                mp_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
            )

        # Draw text overlay
        cv2.putText(frame, f"FPS: {fps:5.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.putText(frame, f"Knee: {self.knee_ang:5.1f}°", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.putText(frame, f"Phase: {self.phase}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2, cv2.LINE_AA)

        # Video-specific info
        if self.is_video_mode:
            progress = self.camera.get_progress()
            current_time, total_time = self.camera.get_time_info()
            
            cv2.putText(frame, f"Progress: {progress:.1f}%", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            
            cv2.putText(frame, f"Time: {current_time:.1f}s / {total_time:.1f}s", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            
            # Update progress slider
            if self.is_playing:
                self.progress_slider.setValue(self.camera.frame_count)

        # Update display
        self.video_widget.update_frame(frame)

    def closeEvent(self, event):
        """Handle window close event."""
        self.pose_detector.close()
        if self.camera:
            self.camera.release()
        super().closeEvent(event)


def run():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 900)
    w.show()
    sys.exit(app.exec())