import sys
import cv2
import time
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QLabel, QFileDialog,
                             QTextEdit, QSplitter, QGridLayout,
                             QGroupBox, QMenuBar, QMessageBox, QComboBox)
from PySide6.QtGui import QImage, QPixmap, QAction
from PySide6.QtCore import Qt, QTimer
from src.capture.camera import CameraManager
from src.processing.pose_processor import PoseProcessor
from src.grading.advanced_form_grader import UserProfile, UserLevel, IntelligentFormGrader
from src.pose.pose_detector import PoseDetector
from src.utils.rep_counter import RepCounter
from src.gui.widgets.settings_dialog import SettingsDialog
from src.gui.widgets.session_report import SessionReportDialog
from src.config.config_manager import ConfigManager
from src.gui.widgets.session_report import SessionManager

class MainWindow(QMainWindow):
    """
    The main application window for the AI Fitness Coach.

    This class is responsible for setting up the user interface, managing
    user interactions, and orchestrating the flow of data from the camera
    to the pose processor and back to the UI.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Fitness Coach - Squat Form Analyzer")

        # --- Core Component Initialization ---
        self.config_manager = ConfigManager()
        self.camera_manager = None
        self.session_manager = SessionManager()

        # Load settings first, as they are needed by other components
        self.current_settings = self.config_manager.get_analysis_settings()
        ui_settings = self.config_manager.get_ui_settings()
        self.resize(ui_settings.get('window_width', 1600), ui_settings.get('window_height', 1000))

        # Create user profile
        self.user_profile = UserProfile(user_id="main_user", skill_level=UserLevel.INTERMEDIATE)
        
        # Create PoseProcessor with correct constructor (it creates its own internal components)
        self.pose_processor = PoseProcessor(user_profile=self.user_profile)

        # Timers
        self.timer = QTimer(self)
        self.rep_analysis_display_timer = QTimer(self)
        self.rep_analysis_display_timer.setSingleShot(True)

        # Initialize the timestamp for the last displayed report
        self._last_report_ts = 0

        # UI Setup
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_connections()

    def setup_ui(self):
        """Sets up the main UI layout, styles, and widgets."""
        self.setStyleSheet("""
            QMainWindow { background-color: #2e2e2e; }
            QGroupBox {
                color: #e0e0e0; font-weight: bold; border: 1px solid #444;
                border-radius: 8px; margin-top: 1ex; background-color: #3c3c3c;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLabel { color: #e0e0e0; font-size: 14px; }
            QPushButton {
                background-color: #0078d4; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1e90ff; }
            QPushButton:disabled { background-color: #555; color: #aaa; }
            QTextEdit { background-color: #252525; color: #e0e0e0; border: 1px solid #444; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = self._create_video_panel()
        right_panel = self._create_info_panel()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([1200, 400])

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Select a source to start a session")

    def setup_menu_bar(self):
        """Creates the main application menu bar."""
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        open_video_action = QAction('Open Video...', self, triggered=self.open_video_file)
        start_webcam_action = QAction('Start Webcam', self, triggered=self.start_webcam)
        exit_action = QAction('Exit', self, triggered=self.close)
        file_menu.addActions([open_video_action, start_webcam_action, exit_action])

        view_menu = menubar.addMenu('View')
        show_report_action = QAction('Session Report...', self, triggered=self.show_session_report)
        view_menu.addAction(show_report_action)
        
        # Debug menu for validation
        debug_menu = menubar.addMenu('Debug')
        self.validation_action = QAction('Enable Validation Mode', self, checkable=True)
        self.validation_action.setChecked(False)
        self.validation_action.triggered.connect(self.toggle_validation_mode)
        debug_menu.addAction(self.validation_action)

    def _create_video_panel(self):
        """Creates the left panel containing the video feed and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        video_group = QGroupBox("Video Feed")
        video_layout = QVBoxLayout(video_group)
        self.video_label = QLabel("Press 'Start Webcam' or 'Load Video'")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("border: 2px dashed #555; background-color: #222;")
        video_layout.addWidget(self.video_label)
        layout.addWidget(video_group)

        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)
        self.webcam_button = QPushButton("🎥 Start Webcam")
        self.video_button = QPushButton("📁 Load Video")
        self.stop_button = QPushButton("⏹️ Stop Session")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #d32f2f;")
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner", "Casual", "Professional"])
        self.difficulty_combo.setCurrentText("Casual")
        controls_layout.addWidget(self.webcam_button)
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Difficulty:"))
        controls_layout.addWidget(self.difficulty_combo)
        layout.addWidget(controls_group)
        return panel

    def _create_info_panel(self):
        """Creates the right panel for displaying metrics and feedback."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        stats_group = QGroupBox("Live Statistics")
        stats_layout = QGridLayout(stats_group)
        self.rep_label = QLabel("0")
        self.form_score_label = QLabel("N/A")
        self.phase_label = QLabel("Ready")
        stats_layout.addWidget(QLabel("Rep Count:"), 0, 0)
        stats_layout.addWidget(self.rep_label, 0, 1)
        stats_layout.addWidget(QLabel("Form Score:"), 1, 0)
        stats_layout.addWidget(self.form_score_label, 1, 1)
        stats_layout.addWidget(QLabel("Phase:"), 2, 0)
        stats_layout.addWidget(self.phase_label, 2, 1)
        layout.addWidget(stats_group)

        feedback_group = QGroupBox("Analysis & Feedback")
        feedback_layout = QVBoxLayout(feedback_group)
        self.feedback_display = QTextEdit()
        self.feedback_display.setReadOnly(True)
        self.feedback_display.setPlaceholderText("Detailed analysis will appear here after each rep.")
        feedback_layout.addWidget(self.feedback_display)
        layout.addWidget(feedback_group)

        return panel

    def setup_connections(self):
        """Connects widget signals to their corresponding slots."""
        self.webcam_button.clicked.connect(self.start_webcam)
        self.video_button.clicked.connect(self.open_video_file)
        self.stop_button.clicked.connect(self.stop_session)
        self.timer.timeout.connect(self.update_frame)
        self.difficulty_combo.currentTextChanged.connect(self.on_difficulty_changed)
        self.rep_analysis_display_timer.timeout.connect(self.clear_rep_analysis_display)

    def start_webcam(self):
        self._start_session(0)

    def open_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self._start_session(file_path)

    def _start_session(self, source):
        """Initializes a new session with the given video source."""
        try:
            if self.camera_manager:
                self.camera_manager.release()
            
            self.camera_manager = CameraManager(source)
            if not self.camera_manager.isOpened():
                raise RuntimeError(f"Failed to open source: {source}")

            source_type = 'video' if isinstance(source, str) else 'webcam'
            self.pose_processor.start_session(source_type)

            self.webcam_button.setEnabled(False)
            self.video_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.timer.start(30)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start session:\n{e}")

    def stop_session(self):
        """Stops the current session and resets the UI."""
        # Prevent multiple calls
        if not self.stop_button.isEnabled():
            return
            
        self.timer.stop()
        if self.camera_manager:
            self.camera_manager.release()
            self.camera_manager = None

        self.pose_processor.end_session()

        self.webcam_button.setEnabled(True)
        self.video_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.video_label.setText("Session stopped. Select a source to begin.")
        
        # FIX: Use the correct session manager and check for any activity
        from PySide6.QtCore import QTimer
        
        # Delay the report slightly to ensure all data is processed
        def show_delayed_report():
            report = self.session_manager.get_session_summary()
            print(f"DEBUG: Session summary: {report}")  # Debug line
            
            # Show report if there was any meaningful activity
            total_reps = report.get('total_reps', 0)
            form_scores = report.get('form_scores', [])
            feedback_count = len(report.get('feedback_history', []))
            
            if total_reps > 0 or len(form_scores) > 0 or feedback_count > 0:
                print("Showing session report...")  # Debug line
                self.show_session_report()
            else:
                print("No activity detected - no report to show")  # Debug line
        
        # Use QTimer to delay the report display
        QTimer.singleShot(500, show_delayed_report)  # 500ms delay

    def update_frame(self):
        """The main loop called by the QTimer to process and display video frames."""
        frame = self.camera_manager.get_frame()
        if frame is None:
            self.stop_session()
            return

        live_metrics = self.pose_processor.process_frame(frame)
        
        self.rep_label.setText(str(live_metrics.get('rep_count', 0)))
        self.phase_label.setText(live_metrics.get('phase', '...'))

        processed_frame = live_metrics.get('processed_frame')
        if processed_frame is not None:
            self.display_frame(processed_frame)

        # FIX: Better form score display and session manager integration
        report = live_metrics.get('last_rep_analysis')
        if report and report.get('timestamp', 0) > getattr(self, '_last_report_ts', 0):
            self._last_report_ts = report['timestamp']
            self.display_rep_analysis(report)
            
            # UPDATE SESSION MANAGER with the analysis
            self.session_manager.update_session(
                rep_count=live_metrics.get('rep_count', 0),
                form_score=report.get('score', 0),
                phase=live_metrics.get('phase', 'STANDING'),
                fault_data=report.get('faults', [])
            )

        status_msg = (f"FPS: {live_metrics.get('fps', 0):.0f} | "
                      f"State: {live_metrics.get('session_state', 'N/A')} | "
                      f"Pose: {'✅' if live_metrics.get('landmarks_detected') else '❌'}")
        self.status_bar.showMessage(status_msg)

    def display_frame(self, frame):
        """Converts a CV2 frame to QPixmap and displays it."""
        try:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            if ch == 3:
                q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
                pixmap = QPixmap.fromImage(q_image)
                self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            print(f"Error displaying frame: {e}")

    def display_rep_analysis(self, analysis: dict):
        """Displays the detailed analysis of a completed rep in the feedback box."""
        if not analysis: 
            return

        score = analysis.get('score', 0)
        feedback = analysis.get('feedback', [])
        
        # DEBUG: Print to console as well
        print(f"DEBUG: Displaying rep analysis - Score: {score}%, Feedback: {feedback}")
        
        self.form_score_label.setText(f"{score}%")
        
        # Display feedback with better formatting
        if feedback:
            feedback_html = "<br>".join(f"• {item}" for item in feedback[:5])  # Limit to 5 items
            self.feedback_display.setHtml(feedback_html)
        else:
            self.feedback_display.setPlainText("Analysis complete - no specific feedback.")

        # Color-code the score with font weight
        if score >= 85: 
            self.form_score_label.setStyleSheet("color: #4CAF50; font-weight: bold;")  # Green
        elif score >= 60: 
            self.form_score_label.setStyleSheet("color: #FFC107; font-weight: bold;")  # Amber
        else: 
            self.form_score_label.setStyleSheet("color: #F44336; font-weight: bold;")  # Red
        
        self.rep_analysis_display_timer.start(7000)

    def clear_rep_analysis_display(self):
        """Clears the post-rep feedback."""
        self.feedback_display.setPlaceholderText("Complete another rep for analysis.")
        self.feedback_display.clear()
        self.form_score_label.setText("N/A")
        self.form_score_label.setStyleSheet("color: #e0e0e0;")

    def on_difficulty_changed(self, text: str):
        """Updates the form grader's difficulty setting."""
        difficulty = text.lower()
        self.pose_processor.form_grader.set_difficulty(difficulty)
        print(f"Difficulty changed to: {difficulty}")

    def show_session_report(self):
        """Shows the end-of-session report dialog."""
        report_data = self.session_manager.get_session_summary()
        if not report_data or report_data.get('total_reps', 0) == 0:
            QMessageBox.information(self, "Session Report", "No reps were completed in the session.")
            return
        
        dialog = SessionReportDialog(report_data, self)
        dialog.exec()
    
    def toggle_validation_mode(self, enabled):
        """Toggle validation mode for debugging pose analysis"""
        try:
            # Recreate PoseProcessor with validation enabled/disabled
            self.pose_processor = PoseProcessor(
                user_profile=self.user_profile,
                enable_validation=enabled
            )
            
            status_text = "Validation mode enabled - Debug output will be shown in console" if enabled else "Validation mode disabled"
            self.status_bar.showMessage(status_text, 3000)
            
            print(f"🔧 Validation mode {'enabled' if enabled else 'disabled'}")
            
        except Exception as e:
            print(f"Error toggling validation mode: {e}")
            self.validation_action.setChecked(not enabled)  # Revert checkbox state

    def closeEvent(self, event):
        """Handles the application close event."""
        self.stop_session()
        self.config_manager.save_ui_settings({'window_width': self.width(), 'window_height': self.height()})
        event.accept()
    
    def toggle_validation_mode(self, enabled: bool):
        """Toggle validation mode on/off"""
        print(f"🔍 Validation mode {'enabled' if enabled else 'disabled'}")
        
        # Recreate PoseProcessor with validation enabled/disabled
        self.pose_processor = PoseProcessor(
            user_profile=self.user_profile, 
            enable_validation=enabled
        )
        
        # Update UI to show validation status
        if enabled:
            self.status_bar.showMessage("🔍 VALIDATION MODE ACTIVE - Debug output enabled")
        else:
            self.status_bar.showMessage("Ready - Select a source to start a session")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
