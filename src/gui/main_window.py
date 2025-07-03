import sys
import cv2
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                               QHBoxLayout, QWidget, QLabel, QFileDialog, QFrame,
                               QProgressBar, QTextEdit, QSplitter, QGridLayout,
                               QGroupBox, QScrollArea, QSizePolicy, QMenuBar, QMenu)
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPalette, QAction
from PySide6.QtCore import Qt, QTimer, Signal
from src.capture.camera import CameraManager
from src.processing.pose_processor import PoseProcessor
from src.gui.widgets.settings_dialog import SettingsDialog
from src.gui.widgets.session_report import SessionReportDialog, SessionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Fitness Coach - Squat Form Analyzer")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # Apply modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                color: #333333;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

        # Initialize components
        self.setup_menu_bar()
        self.setup_ui()
        self.setup_connections()
        
        # Initialize processing components
        self.camera_manager = None
        self.pose_processor = PoseProcessor()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # Session management
        self.session_manager = SessionManager()
        self.session_start_time = None
        self.total_reps = 0
        self.best_form_score = 0
        self.session_feedback_history = []
        
        # Settings
        self.current_settings = {
            'confidence_threshold': 0.7,
            'back_angle_threshold': 25,
            'knee_depth_threshold': 90,
            'symmetry_threshold': 15,
            'feedback_frequency': 'Medium',
            'show_angles': True,
            'show_skeleton': True,
            'smoothing_frames': 5,
            'min_frames_for_fault': 3
        }

    def setup_ui(self):
        """Setup the enhanced UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with splitter
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Video and controls
        left_panel = self.create_video_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Stats and feedback
        right_panel = self.create_info_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (70% video, 30% info)
        splitter.setSizes([1100, 500])
        
    def create_video_panel(self):
        """Create the video display and control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Video display group
        video_group = QGroupBox("Video Feed")
        video_layout = QVBoxLayout(video_group)
        
        # Video label with minimum size
        self.video_label = QLabel("Press 'Start Webcam' or 'Load Video' to begin")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 8px;
                background-color: #fafafa;
                color: #666666;
                font-size: 16px;
            }
        """)
        self.video_label.setScaledContents(False)
        video_layout.addWidget(self.video_label)
        
        layout.addWidget(video_group)
        
        # Control buttons
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.webcam_button = QPushButton("🎥 Start Webcam")
        self.video_button = QPushButton("📁 Load Video")
        self.stop_button = QPushButton("⏹️ Stop")
        self.reset_button = QPushButton("🔄 Reset Session")
        
        # Session tracking button
        session_report_button = QPushButton("📊 Session Report")
        session_report_button.setStyleSheet("QPushButton { background-color: #2196F3; }")
        session_report_button.clicked.connect(self.show_session_report)
        
        # Settings button
        settings_button = QPushButton("⚙️ Settings")
        settings_button.setStyleSheet("QPushButton { background-color: #9C27B0; }")
        settings_button.clicked.connect(self.show_settings_dialog)
        
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: #f44336; }")
        self.reset_button.setStyleSheet("QPushButton { background-color: #ff9800; }")
        
        controls_layout.addWidget(self.webcam_button)
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(session_report_button)
        controls_layout.addWidget(settings_button)
        
        layout.addWidget(controls_group)
        
        return panel
        
    def create_info_panel(self):
        """Create the information and feedback panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Session stats group
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QGridLayout(stats_group)
        
        # Rep counter
        self.rep_label = QLabel("Reps: 0")
        self.rep_label.setFont(QFont("Arial", 16, QFont.Bold))
        stats_layout.addWidget(QLabel("Rep Count:"), 0, 0)
        stats_layout.addWidget(self.rep_label, 0, 1)
        
        # Form score
        self.form_score_label = QLabel("100%")
        self.form_score_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.form_score_label.setStyleSheet("color: #4CAF50;")
        stats_layout.addWidget(QLabel("Form Score:"), 1, 0)
        stats_layout.addWidget(self.form_score_label, 1, 1)
        
        # Current phase
        self.phase_label = QLabel("Ready")
        self.phase_label.setFont(QFont("Arial", 14))
        stats_layout.addWidget(QLabel("Phase:"), 2, 0)
        stats_layout.addWidget(self.phase_label, 2, 1)
        
        # FPS
        self.fps_label = QLabel("0 FPS")
        stats_layout.addWidget(QLabel("Performance:"), 3, 0)
        stats_layout.addWidget(self.fps_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        # Progress tracking
        progress_group = QGroupBox("Progress Tracking")
        progress_layout = QVBoxLayout(progress_group)
        
        # Form quality progress bar
        progress_layout.addWidget(QLabel("Form Quality:"))
        self.form_progress = QProgressBar()
        self.form_progress.setRange(0, 100)
        self.form_progress.setValue(100)
        progress_layout.addWidget(self.form_progress)
        
        # Session best score
        self.best_score_label = QLabel("Best Score: --")
        progress_layout.addWidget(self.best_score_label)
        
        # Total reps this session
        self.total_reps_label = QLabel("Total Reps: 0")
        progress_layout.addWidget(self.total_reps_label)
        
        layout.addWidget(progress_group)
        
        # Live feedback group
        feedback_group = QGroupBox("Live Feedback")
        feedback_layout = QVBoxLayout(feedback_group)
        
        # Current feedback display
        self.feedback_display = QTextEdit()
        self.feedback_display.setMaximumHeight(120)
        self.feedback_display.setReadOnly(True)
        self.feedback_display.setPlainText("Ready to analyze your squat form...")
        feedback_layout.addWidget(self.feedback_display)
        
        layout.addWidget(feedback_group)
        
        # Feedback history
        history_group = QGroupBox("Feedback History")
        history_layout = QVBoxLayout(history_group)
        
        self.feedback_history = QTextEdit()
        self.feedback_history.setReadOnly(True)
        self.feedback_history.setMaximumHeight(200)
        history_layout.addWidget(self.feedback_history)
        
        # Clear history button
        clear_button = QPushButton("Clear History")
        clear_button.setStyleSheet("QPushButton { background-color: #757575; }")
        clear_button.clicked.connect(self.clear_feedback_history)
        history_layout.addWidget(clear_button)
        
        layout.addWidget(history_group)
        
        # Real-time tips section
        tips_group = QGroupBox("💡 Real-time Tips")
        tips_layout = QVBoxLayout(tips_group)
        
        self.tips_display = QLabel("Position yourself 6-8 feet from camera for best results")
        self.tips_display.setWordWrap(True)
        self.tips_display.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 8px;
                color: #1976D2;
            }
        """)
        tips_layout.addWidget(self.tips_display)
        
        layout.addWidget(tips_group)
        
        return panel

    def setup_menu_bar(self):
        """Setup the menu bar with additional options"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_video_action = QAction('Open Video...', self)
        open_video_action.setShortcut('Ctrl+O')
        open_video_action.triggered.connect(self.open_video_file)
        file_menu.addAction(open_video_action)
        
        file_menu.addSeparator()
        
        export_session_action = QAction('Export Session Report...', self)
        export_session_action.triggered.connect(self.show_session_report)
        file_menu.addAction(export_session_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Session menu
        session_menu = menubar.addMenu('Session')
        
        start_webcam_action = QAction('Start Webcam', self)
        start_webcam_action.setShortcut('Ctrl+W')
        start_webcam_action.triggered.connect(self.start_webcam)
        session_menu.addAction(start_webcam_action)
        
        stop_session_action = QAction('Stop Session', self)
        stop_session_action.setShortcut('Ctrl+S')
        stop_session_action.triggered.connect(self.stop_session)
        session_menu.addAction(stop_session_action)
        
        reset_session_action = QAction('Reset Session', self)
        reset_session_action.setShortcut('Ctrl+R')
        reset_session_action.triggered.connect(self.reset_session)
        session_menu.addAction(reset_session_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        analysis_settings_action = QAction('Analysis Settings...', self)
        analysis_settings_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(analysis_settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        instructions_action = QAction('Instructions', self)
        instructions_action.triggered.connect(self.show_instructions_dialog)
        help_menu.addAction(instructions_action)

    def setup_connections(self):
        """Setup signal connections"""
        self.webcam_button.clicked.connect(self.start_webcam)
        self.video_button.clicked.connect(self.open_video_file)
        self.stop_button.clicked.connect(self.stop_session)
        self.reset_button.clicked.connect(self.reset_session)

    def start_webcam(self):
        """Start webcam capture"""
        self.setup_camera(source=0)

    def open_video_file(self):
        """Open video file dialog and start processing"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", 
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        if filepath:
            self.setup_camera(source=filepath)
    
    def stop_session(self):
        """Stop the current session"""
        if self.timer.isActive():
            self.timer.stop()
        if self.camera_manager:
            self.camera_manager.release()
            self.camera_manager = None
        
        self.webcam_button.setEnabled(True)
        self.video_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.video_label.setText("Session stopped. Ready to start a new session.")
        
    def reset_session(self):
        """Reset the current session data"""
        self.stop_session()
        self.pose_processor.reset()
        
        # Reset UI elements
        self.rep_label.setText("Reps: 0")
        self.form_score_label.setText("100%")
        self.form_score_label.setStyleSheet("color: #4CAF50;")
        self.phase_label.setText("Ready")
        self.fps_label.setText("0 FPS")
        self.form_progress.setValue(100)
        self.best_score_label.setText("Best Score: --")
        self.total_reps_label.setText("Total Reps: 0")
        self.feedback_display.setPlainText("Ready to analyze your squat form...")
        
        # Reset session tracking
        self.session_start_time = None
        self.total_reps = 0
        self.best_form_score = 0
        self.session_feedback_history = []
        
    def clear_feedback_history(self):
        """Clear the feedback history display"""
        self.feedback_history.clear()
        self.session_feedback_history = []

    def setup_camera(self, source):
        """Setup camera/video source with enhanced error handling"""
        self.stop_session()  # Stop any existing session
        
        try:
            self.camera_manager = CameraManager(source)
            if not self.camera_manager.isOpened():
                raise RuntimeError(f"Could not open source '{source}'")
            
            # Reset the processor for the new video/session
            self.pose_processor.reset()
            
            # Update UI state
            self.webcam_button.setEnabled(False)
            self.video_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Start session tracking
            import time
            self.session_start_time = time.time()
            self.session_manager.start_session()
            
            # Apply current settings to processor
            if hasattr(self.pose_processor, 'update_settings'):
                self.pose_processor.update_settings(self.current_settings)
            
            # Start processing
            self.timer.start(30)  # ~33 FPS
            
            source_text = "Webcam" if source == 0 else "Video File"
            self.video_label.setText(f"Starting {source_text}...")

        except RuntimeError as e:
            self.video_label.setText(f"Error: {e}")
            self.webcam_button.setEnabled(True)
            self.video_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def update_frame(self):
        """Update frame with enhanced feedback integration"""
        if not self.camera_manager:
            return

        frame = self.camera_manager.get_frame()
        # Gracefully handle the end of the video
        if frame is None:
            self.timer.stop()
            self.video_label.setText("Video finished or stream ended.")
            self.stop_button.setEnabled(False)
            self.webcam_button.setEnabled(True)
            self.video_button.setEnabled(True)
            return

        # Process frame and get results
        processed_frame = self.pose_processor.process_frame(frame)
        
        # Update UI with current stats
        self.update_statistics()
        
        # Update feedback display
        self.update_feedback_display()
        
        # Display the processed frame
        self.display_frame(processed_frame)

    def update_statistics(self):
        """Update the statistics panel with current data"""
        # Update rep count
        current_reps = self.pose_processor.rep_counter
        self.rep_label.setText(f"Reps: {current_reps}")
        
        # Track total reps
        if current_reps > self.total_reps:
            self.total_reps = current_reps
            self.total_reps_label.setText(f"Total Reps: {self.total_reps}")
        
        # Update form score with color coding
        form_score = getattr(self.pose_processor, 'form_score', 100)
        self.form_score_label.setText(f"{form_score}%")
        self.form_progress.setValue(form_score)
        
        # Color coding for form score
        if form_score >= 90:
            color = "#4CAF50"  # Green
        elif form_score >= 70:
            color = "#FF9800"  # Orange
        else:
            color = "#f44336"  # Red
            
        self.form_score_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        # Track best score
        if form_score > self.best_form_score:
            self.best_form_score = form_score
            self.best_score_label.setText(f"Best Score: {self.best_form_score}%")
        
        # Update phase
        phase = getattr(self.pose_processor, 'phase', 'READY')
        phase_display = {
            'STANDING': '🧍 Standing',
            'DESCENT': '⬇️ Descending', 
            'BOTTOM': '🔄 Bottom',
            'ASCENT': '⬆️ Ascending',
            'READY': '⏸️ Ready'
        }.get(phase, phase)
        self.phase_label.setText(phase_display)
        
        # Update FPS
        fps = getattr(self.pose_processor, 'fps', 0)
        self.fps_label.setText(f"{fps:.1f} FPS")
        
        # Update session manager
        if self.session_start_time:
            # Get current faults for tracking
            current_faults = []
            current_feedback = self.pose_processor.feedback_manager.get_current_feedback()
            for feedback in current_feedback:
                if feedback.category == 'safety' or feedback.category == 'form':
                    # Extract fault type from feedback message (simplified)
                    if 'chest up' in feedback.message.lower():
                        current_faults.append('BACK_ROUNDING')
                    elif 'knees out' in feedback.message.lower():
                        current_faults.append('KNEE_VALGUS')
                    elif 'deeper' in feedback.message.lower():
                        current_faults.append('INSUFFICIENT_DEPTH')
                    elif 'upright' in feedback.message.lower():
                        current_faults.append('FORWARD_LEAN')
                    elif 'balanced' in feedback.message.lower():
                        current_faults.append('ASYMMETRIC_MOVEMENT')
                    elif 'heels' in feedback.message.lower():
                        current_faults.append('HEEL_RISE')
            
            self.session_manager.update_session(
                self.total_reps, 
                form_score, 
                self.session_feedback_history[-5:],  # Last 5 feedback items
                current_faults
            )
            
        # Update tips display based on current state
        self.update_tips_display()

    def update_feedback_display(self):
        """Update the live feedback display"""
        # Get current feedback from the feedback manager
        current_feedback = self.pose_processor.feedback_manager.get_current_feedback()
        
        if current_feedback:
            # Show the most important feedback messages
            feedback_text = []
            for msg in current_feedback[:2]:  # Show top 2 messages
                category_icon = {
                    'safety': '⚠️',
                    'form': '💡', 
                    'encouragement': '👍'
                }.get(msg.category, '📋')
                
                feedback_text.append(f"{category_icon} {msg.message}")
            
            self.feedback_display.setPlainText('\n'.join(feedback_text))
            
            # Add to history (avoid duplicates)
            for msg in current_feedback:
                if msg.message not in [h['message'] for h in self.session_feedback_history[-5:]]:
                    import time
                    timestamp = time.strftime("%H:%M:%S")
                    history_entry = {
                        'message': msg.message,
                        'timestamp': timestamp,
                        'category': msg.category
                    }
                    self.session_feedback_history.append(history_entry)
                    
                    # Update history display
                    category_icon = {
                        'safety': '⚠️',
                        'form': '💡',
                        'encouragement': '👍'
                    }.get(msg.category, '📋')
                    
                    history_text = f"[{timestamp}] {category_icon} {msg.message}"
                    self.feedback_history.append(history_text)
                    
                    # Auto-scroll to bottom
                    scrollbar = self.feedback_history.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
        else:
            # Show ready state when no active feedback
            if self.pose_processor.phase == "STANDING":
                self.feedback_display.setPlainText("✅ Good form! Keep it up!")
            else:
                self.feedback_display.setPlainText("👀 Analyzing your movement...")

    def update_tips_display(self):
        """Update the tips display based on current analysis"""
        tips = [
            "Keep your chest up and core engaged",
            "Squat down by pushing your hips back", 
            "Keep knees aligned over your toes",
            "Descend until hip crease is below knee",
            "Drive through your heels to stand up",
            "Maintain steady, controlled movement",
            "Focus on form over speed"
        ]
        
        # Get context-aware tips based on current phase and issues
        current_feedback = self.pose_processor.feedback_manager.get_current_feedback()
        
        if current_feedback:
            # Show specific tip based on active feedback
            for feedback in current_feedback:
                if feedback.category == 'safety':
                    self.tips_display.setText(f"⚠️ {feedback.message}")
                    self.tips_display.setStyleSheet("""
                        QLabel {
                            background-color: #FFEBEE;
                            border: 1px solid #F44336;
                            border-radius: 4px;
                            padding: 8px;
                            color: #C62828;
                        }
                    """)
                    return
                elif feedback.category == 'form':
                    self.tips_display.setText(f"💡 {feedback.message}")
                    self.tips_display.setStyleSheet("""
                        QLabel {
                            background-color: #FFF3E0;
                            border: 1px solid #FF9800;
                            border-radius: 4px;
                            padding: 8px;
                            color: #F57C00;
                        }
                    """)
                    return
        
        # Show general tips when no active feedback
        phase = getattr(self.pose_processor, 'phase', 'STANDING')
        if phase == 'DESCENT':
            tip = "Continue descending slowly - control the movement"
        elif phase == 'BOTTOM':
            tip = "Hold briefly at bottom, then drive up through heels"
        elif phase == 'ASCENT':
            tip = "Push the floor away and squeeze glutes at the top"
        else:
            import random
            tip = random.choice(tips)
            
        self.tips_display.setText(f"💡 {tip}")
        self.tips_display.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 8px;
                color: #1976D2;
            }
        """)

    def display_frame(self, frame):
        """Display the processed frame with proper scaling"""
        # The frame from the processor is already annotated (BGR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale pixmap to fit the label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        """Handle application close with cleanup"""
        self.timer.stop()
        if self.camera_manager:
            self.camera_manager.release()
        event.accept()

    def show_settings_dialog(self):
        """Show the settings configuration dialog"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.update_settings)
        
        # Set current settings in dialog
        dialog.confidence_threshold.setValue(self.current_settings['confidence_threshold'])
        dialog.back_angle_threshold.setValue(self.current_settings['back_angle_threshold'])
        dialog.knee_depth_threshold.setValue(self.current_settings['knee_depth_threshold'])
        dialog.symmetry_threshold.setValue(self.current_settings['symmetry_threshold'])
        dialog.feedback_frequency.setCurrentText(self.current_settings['feedback_frequency'])
        dialog.show_angles.setChecked(self.current_settings['show_angles'])
        dialog.show_skeleton.setChecked(self.current_settings['show_skeleton'])
        dialog.smoothing_frames.setValue(self.current_settings['smoothing_frames'])
        dialog.min_frames_for_fault.setValue(self.current_settings['min_frames_for_fault'])
        
        dialog.exec()
        
    def update_settings(self, new_settings):
        """Update application settings"""
        self.current_settings.update(new_settings)
        
        # Apply settings to pose processor if active
        if hasattr(self.pose_processor, 'update_settings'):
            self.pose_processor.update_settings(self.current_settings)
            
    def show_session_report(self):
        """Show comprehensive session report"""
        session_data = self.session_manager.get_session_summary()
        
        # Add current session data
        session_data.update({
            'feedback_history': self.session_feedback_history,
            'total_reps': self.total_reps,
            'best_form_score': self.best_form_score
        })
        
        dialog = SessionReportDialog(session_data, self)
        dialog.exec()
        
    def show_about_dialog(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        
        about_text = """
        <h3>AI Fitness Coach</h3>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Description:</b> An AI-powered squat form analyzer using computer vision and pose estimation.</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time squat form analysis</li>
        <li>Personalized feedback and coaching</li>
        <li>Session tracking and reporting</li>
        <li>Comprehensive movement quality assessment</li>
        </ul>
        <p><b>Technology:</b> Built with MediaPipe, OpenCV, and PySide6</p>
        """
        
        QMessageBox.about(self, "About AI Fitness Coach", about_text)
        
    def show_instructions_dialog(self):
        """Show instructions dialog"""
        from PySide6.QtWidgets import QMessageBox
        
        instructions_text = """
        <h3>How to Use AI Fitness Coach</h3>
        
        <h4>Setup:</h4>
        <ol>
        <li>Position your camera 6-8 feet away from your squat area</li>
        <li>Ensure good lighting and clear view of your full body</li>
        <li>Stand facing the camera for best pose detection</li>
        </ol>
        
        <h4>Starting a Session:</h4>
        <ol>
        <li>Click "Start Webcam" or "Load Video" to begin</li>
        <li>Stand in ready position for pose detection</li>
        <li>Begin performing squats with controlled movement</li>
        </ol>
        
        <h4>Understanding Feedback:</h4>
        <ul>
        <li><b>Safety messages (⚠️):</b> Address immediately</li>
        <li><b>Form tips (💡):</b> Technical improvements</li>
        <li><b>Encouragement (👍):</b> Positive reinforcement</li>
        </ul>
        
        <h4>Tips for Best Results:</h4>
        <ul>
        <li>Move slowly and controlled</li>
        <li>Focus on quality over quantity</li>
        <li>Use the feedback to improve each rep</li>
        <li>Review session reports to track progress</li>
        </ul>
        """
        
        QMessageBox.information(self, "Instructions", instructions_text)