import sys
import cv2
import time
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QLabel, QFileDialog, QFrame,
                             QProgressBar, QTextEdit, QSplitter, QGridLayout,
                             QGroupBox, QMenuBar, QMenu, QMessageBox)
from PySide6.QtGui import QImage, QPixmap, QFont, QAction
from PySide6.QtCore import Qt, QTimer
from src.capture.camera import CameraManager
from src.processing.pose_processor import PoseProcessor
from src.grading.advanced_form_grader import UserProfile, UserLevel
from src.gui.widgets.settings_dialog import SettingsDialog
from src.gui.widgets.session_report import SessionReportDialog
from src.config.config_manager import ConfigManager
from src.feedback.feedback_manager import FeedbackManager
from src.gui.widgets.session_report import SessionReportDialog, SessionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Fitness Coach - Squat Form Analyzer")

        # Initialize managers using your existing classes
        self.config_manager = ConfigManager()
        self.current_settings = self.config_manager.get_analysis_settings()

        ui_settings = self.config_manager.get_ui_settings()
        self.resize(ui_settings.get('window_width', 1600), ui_settings.get('window_height', 1000))

        self.camera_manager = None

        # Create user profile for advanced form grader
        self.user_profile = UserProfile(
            user_id="main_user",
            skill_level=UserLevel.INTERMEDIATE,  # Could be configurable
            coaching_style="balanced"
        )

        # Initialize pose processor with user profile
        self.pose_processor = PoseProcessor(self.user_profile)
        self.feedback_manager = FeedbackManager()
        self.session_manager = SessionManager()

        self.timer = QTimer()
        self.is_session_active = False

        # Timer for displaying post-rep analysis
        self.rep_analysis_timer = QTimer(self)
        self.rep_analysis_timer.setSingleShot(True)
        self.rep_analysis_timer.timeout.connect(self.clear_rep_analysis_display)

        # Performance monitoring
        self._last_fps_time = time.time()
        self._frame_count = 0
        self._fps = 0
        self.frame_counter = 0  # For reducing debug output

        self.setup_ui()
        self.setup_menu_bar()  # Add the missing method
        self.setup_connections()

        self.pose_processor.update_settings(self.current_settings)

    def setup_ui(self):
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
                padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #1e90ff; }
            QPushButton:disabled { background-color: #555; color: #aaa; }
            QTextEdit { background-color: #2e2e2e; color: #e0e0e0; border: 1px solid #444; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = self.create_video_panel()
        right_panel = self.create_info_panel()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([1100, 500])

        # Add status bar for performance monitoring
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - No active session")

    def setup_menu_bar(self):
        """Setup the application menu bar"""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('File')

        open_video_action = QAction('Open Video...', self)
        open_video_action.setShortcut('Ctrl+O')
        open_video_action.triggered.connect(self.open_video_file)
        file_menu.addAction(open_video_action)

        start_webcam_action = QAction('Start Webcam', self)
        start_webcam_action.setShortcut('Ctrl+W')
        start_webcam_action.triggered.connect(self.start_webcam)
        file_menu.addAction(start_webcam_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings Menu
        settings_menu = menubar.addMenu('Settings')

        preferences_action = QAction('Preferences...', self)
        preferences_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(preferences_action)

        # View Menu
        view_menu = menubar.addMenu('View')

        show_report_action = QAction('Session Report...', self)
        show_report_action.triggered.connect(self.show_session_report)
        view_menu.addAction(show_report_action)

        # Help Menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def create_video_panel(self):
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

        controls_layout.addWidget(self.webcam_button)
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.stop_button)
        layout.addWidget(controls_group)
        return panel

    def create_info_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Basic stats
        stats_group = QGroupBox("Live Statistics")
        stats_layout = QGridLayout(stats_group)
        self.rep_label = QLabel("0")
        self.form_score_label = QLabel("100%")
        self.phase_label = QLabel("Ready")

        stats_layout.addWidget(QLabel("Rep Count:"), 0, 0)
        stats_layout.addWidget(self.rep_label, 0, 1)
        stats_layout.addWidget(QLabel("Form Score:"), 1, 0)
        stats_layout.addWidget(self.form_score_label, 1, 1)
        stats_layout.addWidget(QLabel("Phase:"), 2, 0)
        stats_layout.addWidget(self.phase_label, 2, 1)
        layout.addWidget(stats_group)

        # Advanced metrics from form grader
        advanced_group = QGroupBox("Advanced Metrics")
        advanced_layout = QGridLayout(advanced_group)
        self.depth_label = QLabel("0°")
        self.stability_label = QLabel("0.0")
        self.tempo_label = QLabel("0.0s")
        self.balance_label = QLabel("0.0")

        advanced_layout.addWidget(QLabel("Knee Depth:"), 0, 0)
        advanced_layout.addWidget(self.depth_label, 0, 1)
        advanced_layout.addWidget(QLabel("Stability:"), 1, 0)
        advanced_layout.addWidget(self.stability_label, 1, 1)
        advanced_layout.addWidget(QLabel("Tempo:"), 2, 0)
        advanced_layout.addWidget(self.tempo_label, 2, 1)
        advanced_layout.addWidget(QLabel("Balance:"), 3, 0)
        advanced_layout.addWidget(self.balance_label, 3, 1)
        layout.addWidget(advanced_group)

        feedback_group = QGroupBox("Real-time Feedback")
        feedback_layout = QVBoxLayout(feedback_group)
        self.feedback_display = QTextEdit()
        self.feedback_display.setReadOnly(True)
        self.feedback_display.setMaximumHeight(120)
        feedback_layout.addWidget(self.feedback_display)
        layout.addWidget(feedback_group)

        # Export buttons
        export_group = QGroupBox("Session Export")
        export_layout = QHBoxLayout(export_group)
        self.export_csv_button = QPushButton("📊 Export CSV")
        self.export_json_button = QPushButton("📄 Export JSON")
        self.export_csv_button.clicked.connect(self.export_session_csv)
        self.export_json_button.clicked.connect(self.export_session_json)
        export_layout.addWidget(self.export_csv_button)
        export_layout.addWidget(self.export_json_button)
        layout.addWidget(export_group)

        return panel

    def export_session_csv(self):
        """Export session data to CSV format"""
        if not hasattr(self.session_manager, 'get_session_data'):
            QMessageBox.warning(self, "Export Error", "Session data not available for export.")
            return

        try:
            session_data = self.session_manager.get_session_data()
            if not session_data:
                QMessageBox.warning(self, "Export Error", "No session data to export.")
                return

            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Session Data", f"session_{int(time.time())}.csv", "CSV Files (*.csv)"
            )

            if filename:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    # Write basic session info
                    writer = csv.writer(csvfile)
                    writer.writerow(['Metric', 'Value'])
                    writer.writerow(['Total Reps', session_data.get('rep_count', 0)])
                    writer.writerow(['Average Form Score', session_data.get('form_score', 100)])
                    writer.writerow(['Session Duration', f"{session_data.get('duration', 0):.1f}s"])
                    writer.writerow([''])  # Empty row

                    # Write biomechanical metrics if available
                    bio_metrics = session_data.get('biomechanical_metrics', {})
                    if bio_metrics:
                        writer.writerow(['Biomechanical Metrics'])
                        writer.writerow(['Knee Depth (degrees)', bio_metrics.get('knee_depth', 0)])
                        writer.writerow(['Stability Score', bio_metrics.get('stability_score', 0)])
                        writer.writerow(['Tempo (seconds)', bio_metrics.get('tempo', 0)])
                        writer.writerow(['Balance Score', bio_metrics.get('balance_score', 0)])
                        writer.writerow([''])

                    # Write feedback history
                    feedback_history = session_data.get('feedback_history', [])
                    if feedback_history:
                        writer.writerow(['Feedback History'])
                        writer.writerow(['Timestamp', 'Message', 'Category'])
                        for feedback in feedback_history:
                            timestamp = feedback.get('timestamp', time.time())
                            formatted_time = time.strftime('%H:%M:%S', time.localtime(timestamp))
                            writer.writerow([
                                formatted_time,
                                feedback.get('message', ''),
                                feedback.get('category', 'general')
                            ])

                QMessageBox.information(self, "Export Success", f"Session data exported to:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {str(e)}")

    def export_session_json(self):
        """Export session data to JSON format"""
        if not hasattr(self.session_manager, 'get_session_data'):
            QMessageBox.warning(self, "Export Error", "Session data not available for export.")
            return

        try:
            session_data = self.session_manager.get_session_data()
            if not session_data:
                QMessageBox.warning(self, "Export Error", "No session data to export.")
                return

            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Session Data", f"session_{int(time.time())}.json", "JSON Files (*.json)"
            )

            if filename:
                import json

                # Prepare comprehensive session export
                export_data = {
                    'session_info': {
                        'timestamp': time.time(),
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'duration': session_data.get('duration', 0),
                        'total_reps': session_data.get('rep_count', 0),
                        'average_form_score': session_data.get('form_score', 100)
                    },
                    'biomechanical_metrics': session_data.get('biomechanical_metrics', {}),
                    'angle_data': session_data.get('angles', {}),
                    'feedback_history': session_data.get('feedback_history', []),
                    'fault_data': session_data.get('fault_data', []),
                    'performance_metrics': {
                        'fps': session_data.get('fps', 0),
                        'phase_transitions': session_data.get('phase_transitions', [])
                    }
                }

                with open(filename, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, indent=2, default=str)

                QMessageBox.information(self, "Export Success", f"Session data exported to:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export JSON: {str(e)}")

    def setup_connections(self):
        """Setup signal connections"""
        self.webcam_button.clicked.connect(self.start_webcam)
        self.video_button.clicked.connect(self.open_video_file)
        self.stop_button.clicked.connect(self.stop_session)
        self.timer.timeout.connect(self.update_frame)

    def start_webcam(self):
        """Start webcam capture"""
        try:
            self.setup_camera(0)  # 0 for default webcam
            self.video_label.setText("Webcam Active - Position yourself and start exercising")
            QMessageBox.information(self, "Webcam Started", "Webcam started successfully!\nPosition yourself 6-8 feet from camera.")
        except Exception as e:
            QMessageBox.critical(self, "Webcam Error", f"Failed to start webcam:\n{str(e)}")

    def open_video_file(self):
        """Open video file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"
        )
        if file_path:
            try:
                self.setup_camera(file_path)

                # Get video info for confirmation
                if self.camera_manager:
                    video_info = self.camera_manager.get_video_info()
                    print(f"Video loaded: {video_info}")

                self.video_label.setText(f"Video Loaded: {Path(file_path).name}")
                QMessageBox.information(self, "Video Loaded", f"Video loaded successfully!\nFile: {Path(file_path).name}")
            except Exception as e:
                print(f"Video loading error: {str(e)}")
                QMessageBox.critical(self, "Video Error", f"Failed to load video:\n{str(e)}")

    def setup_camera(self, source):
        """Setup camera or video source"""
        try:
            if self.camera_manager:
                self.camera_manager.release()

            self.camera_manager = CameraManager(source)
            if not self.camera_manager.isOpened():
                raise RuntimeError("Failed to open video source")

            # Determine source type
            source_type = 'video' if isinstance(source, str) else 'webcam'

            # Reset and start session with proper source type
            self.pose_processor.reset()
            self.pose_processor.start_session(source_type)  # Pass the source type
            self.session_manager.reset_session()  # Reset before starting
            self.session_manager.start_session()
            self.is_session_active = True

            # DEBUG: Force session state to ACTIVE for troubleshooting
            from src.processing.pose_processor import SessionState
            self.pose_processor.session_state = SessionState.ACTIVE
            print("[DEBUG] Forced session state to ACTIVE after camera setup.")

            # Update UI
            self.webcam_button.setEnabled(False)
            self.video_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            # Start frame updates
            self.timer.start(33)  # ~30 FPS

        except Exception as e:
            raise e

    def stop_session(self):
        """Stop current session"""
        if self.timer.isActive():
            self.timer.stop()

        if self.camera_manager:
            self.camera_manager.release()
            self.camera_manager = None

        self.session_manager.end_session()
        self.is_session_active = False

        # Reset UI
        self.webcam_button.setEnabled(True)
        self.video_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.video_label.setText("Session stopped\n\nClick 'Start Webcam' or 'Load Video' to begin new session")

        # Show session report if there were reps
        if self.session_manager.session_data.get('total_reps', 0) > 0:
            self.show_session_report()

    def update_frame(self):
        """Update frame with pose analysis and handle new data flow."""
        if not self.is_session_active:
            return

        frame = self.camera_manager.get_frame()
        if frame is None:
            self.stop_session()
            return

        try:
            # Process frame - returns lightweight, real-time data
            live_results = self.pose_processor.process_frame(frame)

            if live_results:
                # Display the processed frame with skeleton
                self.display_frame(live_results.get('processed_frame', frame))

                # Update the live UI elements (rep count, phase)
                self.update_ui(live_results)

                # Check if a new rep analysis is available
                if live_results.get('last_rep_analysis'):
                    self.display_rep_analysis(live_results['last_rep_analysis'])

        except Exception as e:
            print(f"Frame processing error: {e}")
            self.display_frame(frame) # Display raw frame on error

    def update_ui(self, live_metrics: dict):
        """
        Updates the UI with live, real-time data. Robust error handling and fallback for missing metrics.
        """
        try:
            self.rep_label.setText(str(live_metrics.get('rep_count', 0)))
            self.phase_label.setText(live_metrics.get('phase', '...'))

            # Update advanced metrics if available in live data
            angles = live_metrics.get('angles', {})
            knee_angle = angles.get('knee', angles.get('left_knee', 0))
            if isinstance(knee_angle, (int, float)) and knee_angle > 0:
                self.depth_label.setText(f"{knee_angle:.0f}°")
            else:
                self.depth_label.setText("-")

            # Advanced metrics: stability, tempo, balance
            stability = live_metrics.get('stability', None)
            if stability is not None:
                self.stability_label.setText(f"{stability:.3f}")
            else:
                self.stability_label.setText("0.0")

            tempo = live_metrics.get('tempo', None)
            if tempo is not None:
                self.tempo_label.setText(f"{tempo:.2f}s")
            else:
                self.tempo_label.setText("0.0s")

            balance = live_metrics.get('balance', None)
            if balance is not None:
                self.balance_label.setText(f"{balance:.3f}")
            else:
                self.balance_label.setText("0.0")

            # Update form score from current metrics
            current_score = live_metrics.get('form_score', None)
            if isinstance(current_score, (int, float)) and current_score != 100:
                self.form_score_label.setText(f"{current_score}%")
            else:
                self.form_score_label.setText("-")

            # Update FPS display in status bar
            fps = live_metrics.get('fps', 0)
            session_state = live_metrics.get('session_state', 'UNKNOWN')
            landmarks_detected = live_metrics.get('landmarks_detected', False)
            status_msg = f"FPS: {fps:.0f} | State: {session_state} | Pose: {'✅' if landmarks_detected else '❌'}"
            self.status_bar.showMessage(status_msg)
        except Exception as e:
            print(f"UI update error: {e}")
            self.status_bar.showMessage("UI update error. Check logs.")

    def display_rep_analysis(self, analysis: dict):
        """Displays the detailed analysis of the last completed rep."""
        if not analysis:
            return

        score = analysis.get('score', 0)
        faults = analysis.get('faults', [])

        # Update the main form score label with the result of the last rep
        self.form_score_label.setText(f"{score}%")

        # Format the feedback text
        feedback_text = f"Rep Score: {score}%\n\nDetected Issues:\n"
        if faults:
            for fault in faults:
                feedback_text += f"• {fault.replace('_', ' ').title()}\n"
        else:
            feedback_text += "• None - Great form!\n"

        self.feedback_display.setPlainText(feedback_text)

        # Show the feedback for 5 seconds
        self.rep_analysis_timer.start(5000)

    def clear_rep_analysis_display(self):
        """Clears the post-rep analysis from the feedback box."""
        self.feedback_display.setPlainText("Complete another rep for analysis.")
        # Optionally, reset the score display to a neutral state
        # self.form_score_label.setText("N/A")

    def display_frame(self, frame):
        """Display frame in video label"""
        try:
            if frame is not None:
                # Convert frame to Qt format
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

                # Scale to fit label while maintaining aspect ratio
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                self.video_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Display error: {e}")

    def show_settings_dialog(self):
        """Show settings dialog using your existing SettingsDialog"""
        try:
            dialog = SettingsDialog(self)
            if dialog.exec() == dialog.Accepted:
                # Get updated settings and apply them
                if hasattr(dialog, 'get_settings'):
                    new_settings = dialog.get_settings()
                    self.current_settings.update(new_settings)
                    self.pose_processor.update_settings(self.current_settings)
                    self.config_manager.save_analysis_settings(self.current_settings)
        except Exception as e:
            QMessageBox.warning(self, "Settings Error", f"Could not open settings dialog:\n{str(e)}")

    def show_session_report(self):
        """Show session report using your existing SessionReportDialog"""
        try:
            session_data = self.session_manager.get_session_summary()
            dialog = SessionReportDialog(session_data, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Report Error", f"Could not generate session report:\n{str(e)}")

    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(self, "About AI Fitness Coach",
                        "AI Fitness Coach v1.0\n\n"
                        "Real-time squat form analysis using computer vision.\n"
                        "Built with MediaPipe and PySide6.")

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Stop session if active
            if self.is_session_active:
                self.stop_session()

            # Stop camera and processing
            if hasattr(self, 'camera_manager') and self.camera_manager is not None:
                try:
                    self.camera_manager.release()
                except AttributeError:
                    # Handle case where camera_manager doesn't have release method
                    if hasattr(self.camera_manager, 'cap') and self.camera_manager.cap is not None:
                        self.camera_manager.cap.release()

            if hasattr(self, 'timer'):
                self.timer.stop()

            # Save UI settings if the method exists
            if hasattr(self.config_manager, 'save_ui_settings'):
                ui_settings = {
                    'window_width': self.width(),
                    'window_height': self.height(),
                    'window_geometry': self.saveGeometry(),
                    'window_state': self.saveState(),
                    'splitter_state': getattr(self, 'splitter', None) and self.splitter.saveState()
                }
                self.config_manager.save_ui_settings(ui_settings)

            # End session if active
            if hasattr(self, 'pose_processor') and self.pose_processor:
                self.pose_processor.end_session()

        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())