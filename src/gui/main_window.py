import sys
import cv2
import time
from pathlib import Path
import time
import cv2
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QLabel, QFileDialog,
                             QTextEdit, QSplitter, QGridLayout,
                             QGroupBox, QMenuBar, QMessageBox, QComboBox,
                             QProgressBar, QFrame, QScrollArea, QSpacerItem,
                             QSizePolicy, QStackedWidget)
from PySide6.QtGui import (QImage, QPixmap, QAction, QFont, QPainter, QPen, 
                          QBrush, QColor, QConicalGradient, QLinearGradient)
from PySide6.QtCore import Qt, QTimer, QRect
from src.capture.camera import CameraManager
from src.processing.pose_processor import PoseProcessor
from src.grading.advanced_form_grader import UserProfile, UserLevel, IntelligentFormGrader, ThresholdConfig
from src.pose.pose_detector import PoseDetector
from src.utils.rep_counter import RepCounter
from src.gui.widgets.settings_dialog import SettingsDialog
from src.gui.widgets.session_report import SessionReportDialog
from src.config.config_manager import ConfigManager
from src.gui.widgets.session_report import SessionManager

# Import our new UI components
from src.gui.widgets.welcome_screen import WelcomeScreen
from src.gui.widgets.user_profile_dialog import UserProfileDialog
from src.gui.widgets.main_menu_screen import MainMenuScreen
from src.gui.widgets.squat_guide_screen import SquatGuideScreen


class ModernProgressBar(QWidget):
    """Clean, modern progress bar with labels and colors"""
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self._value = 0
        self._target_value = 0
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_value)
        
        self.setFixedHeight(35)  # Compact height
        self.setMinimumWidth(120)
        
    def setValue(self, value):
        """Set value with smooth animation"""
        if isinstance(value, str):
            self._value = 0
            self._target_value = 0
            self.update()
            return
        
        self._target_value = max(0, min(value, 100))
        if not self.animation_timer.isActive():
            self.animation_timer.start(50)
    
    def _animate_value(self):
        """Smooth animation to target value"""
        diff = self._target_value - self._value
        if abs(diff) < 1:
            self._value = self._target_value
            self.animation_timer.stop()
        else:
            self._value += diff * 0.2
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            # Background
            bg_rect = QRect(0, 15, self.width(), 12)
            painter.fillRect(bg_rect, QColor("#333333"))
            
            # Progress bar
            if self._value > 0:
                progress_width = int((self._value / 100) * self.width())
                progress_rect = QRect(0, 15, progress_width, 12)
                
                # Color based on value
                if self._value >= 85:
                    color = QColor("#4CAF50")  # Green
                elif self._value >= 70:
                    color = QColor("#FF9800")  # Orange
                else:
                    color = QColor("#F44336")  # Red
                
                painter.fillRect(progress_rect, color)
            
            # Title and value text
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(QRect(0, 0, self.width(), 15), Qt.AlignLeft, self.title)
            
            # Value text
            value_text = f"{int(self._value)}%"
            painter.drawText(QRect(0, 0, self.width(), 15), Qt.AlignRight, value_text)
            
        except Exception as e:
            print(f"Error painting progress bar: {e}")
        finally:
            painter.end()


class CompactMetricWidget(QWidget):
    """Ultra-compact metric display with icon and value"""
    def __init__(self, title, icon, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        icon_label.setFixedWidth(20)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
        title_label.setFixedWidth(35)
        
        # Value
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                background: {color};
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 40px;
            }}
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
        
        self.setFixedHeight(30)
        
    def setValue(self, value):
        """Update the displayed value"""
        self.value_label.setText(str(value))


class ModernCardWidget(QFrame):
    """A modern card widget with gradient background and subtle shadow effect"""
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCard")
        self.setFrameStyle(QFrame.NoFrame)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title if provided
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            title_label.setStyleSheet("""
                #CardTitle {
                    color: #4CAF50;
                    font-size: 16px;
                    font-weight: bold;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #4CAF50;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(title_label)
        
        # Content area
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
        # Modern card styling
        self.setStyleSheet("""
            #ModernCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3a, stop:1 #2d2d2d);
                border: 1px solid #555;
                border-radius: 15px;
                margin: 5px;
            }
            #ModernCard:hover {
                border: 1px solid #4CAF50;
            }
        """)

class EnhancedCircularGauge(QWidget):
    """Beautiful circular gauge with gradients and animations - RESIZED"""
    def __init__(self, title="", color="#4CAF50", parent=None):
        super().__init__(parent)
        self.setFixedSize(90, 110)  # Reduced from 120x140
        self._value = 0
        self._max_value = 100
        self._color = color
        self._title = title
        self._target_value = 0
        
        # Animation timer for smooth value changes
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_value)
        
    def setValue(self, value):
        """Set value with smooth animation and update color"""
        # If value is a string (e.g., phase), just display it
        if isinstance(value, str):
            self._value = 0
            self._target_value = 0
            self.update()
            return
        self._target_value = max(0, min(value, self._max_value))
        # Traffic light color system
        if self._target_value >= 85:
            self._color = "#4CAF50"  # Green
        elif self._target_value >= 70:
            self._color = "#FFEB3B"  # Yellow
        else:
            self._color = "#F44336"  # Red
        if not self.animation_timer.isActive():
            self.animation_timer.start(50)
    
    def _animate_value(self):
        """Smooth animation to target value"""
        diff = self._target_value - self._value
        if abs(diff) < 1:
            self._value = self._target_value
            self.animation_timer.stop()
        else:
            self._value += diff * 0.2  # Ease-out animation
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions - ADJUSTED
        rect = QRect(8, 8, 74, 74)  # Smaller gauge
        center = rect.center()
        
        try:
            # Background circle
            bg_pen = QPen(QColor("#404040"), 6, Qt.SolidLine, Qt.RoundCap)  # Thinner
            painter.setPen(bg_pen)
            painter.drawArc(rect, 0, 360 * 16)
            
            # Progress arc with gradient
            if self._value > 0:
                # Create gradient based on score
                gradient = QConicalGradient(center, -90)
                if self._value >= 85:
                    gradient.setColorAt(0, QColor("#4CAF50"))
                    gradient.setColorAt(1, QColor("#81C784"))
                elif self._value >= 70:
                    gradient.setColorAt(0, QColor("#FF9800"))
                    gradient.setColorAt(1, QColor("#FFB74D"))
                else:
                    gradient.setColorAt(0, QColor("#F44336"))
                    gradient.setColorAt(1, QColor("#EF5350"))
                
                progress_pen = QPen(QBrush(gradient), 6, Qt.SolidLine, Qt.RoundCap)  # Thinner
                painter.setPen(progress_pen)
                span_angle = int(-360 * (self._value / self._max_value) * 16)
                painter.drawArc(rect, 90 * 16, span_angle)
            
            # Center text - SMALLER
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Arial", 16, QFont.Bold))  # Reduced from 20
            text = f"{int(self._value)}"
            painter.drawText(rect, Qt.AlignCenter, text)
            
            # Percentage symbol
            painter.setFont(QFont("Arial", 10))  # Reduced from 12
            painter.setPen(QColor("#CCCCCC"))
            painter.drawText(rect.adjusted(0, 18, 0, 0), Qt.AlignCenter, "%")
            
            # Title below gauge - ADJUSTED
            if self._title:
                painter.setFont(QFont("Arial", 9, QFont.Bold))  # Reduced from 11
                painter.setPen(QColor(self._color))
                title_rect = QRect(0, 85, 90, 20)  # Adjusted position
                painter.drawText(title_rect, Qt.AlignCenter, self._title)
                
        except Exception as e:
            print(f"Error painting gauge: {e}")
        finally:
            painter.end()

class MetricDisplayWidget(QWidget):
    """Modern metric display - COMPACT VERSION"""
    def __init__(self, title, icon, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(3)  # Reduced spacing
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        
        # Icon and title - COMPACT
        header_layout = QHBoxLayout()
        header_layout.setSpacing(3)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 14px;")  # Smaller icon
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")  # Smaller text
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value display - COMPACT
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                font-size: 18px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3a, stop:1 #2d2d2d);
                border: 2px solid {color};
                border-radius: 6px;
                padding: 6px;
                min-height: 25px;
            }}
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Set compact size
        self.setMinimumSize(85, 70)  # Much smaller
        self.setMaximumSize(100, 80)
    
    def setValue(self, value):
        """Update the displayed value"""
        self.value_label.setText(str(value))

class CompactPerformanceChart(QWidget):
    """Compact real-time performance chart for session dashboard"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = []
        self.max_points = 15  # Show last 15 reps
        self.setMinimumHeight(80)
        self.current_rep = 0
        self.current_score = 0
        
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a, stop:1 #1e1e1e);
                border: 1px solid #444;
                border-radius: 8px;
                margin: 2px;
            }
        """)
    
    def add_rep_score(self, rep_count, score):
        """Add a new rep with its form score"""
        self.current_rep = rep_count
        self.current_score = score
        self.data_points.append(float(score))
        
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()
    
    def reset_chart(self):
        """Reset the chart data"""
        self.data_points = []
        self.current_rep = 0
        self.current_score = 0
        self.update()
    
    def paintEvent(self, event):
        """Draw the compact performance chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        
        # Draw current stats text (top area)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        
        stats_text = f"Rep: {self.current_rep} | Score: {self.current_score:.1f}%"
        painter.drawText(10, 15, stats_text)
        
        # Draw chart if we have data
        if len(self.data_points) < 2:
            painter.setPen(QColor("#666666"))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(10, 50, "Start exercising to see performance...")
            return
        
        # Calculate chart area (lower 60% of widget)
        margin = 8
        chart_width = self.width() - 2 * margin
        chart_height = self.height() - 35  # Leave space for stats text
        chart_top = 25
        
        # Find min/max for scaling
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        if max_val == min_val:
            max_val = min_val + 10  # Avoid division by zero
        
        # Draw subtle grid
        painter.setPen(QPen(QColor("#333333"), 1))
        for i in range(3):  # 3 horizontal lines
            y = chart_top + (i * chart_height // 2)
            painter.drawLine(margin, y, self.width() - margin, y)
        
        # Draw performance line
        painter.setPen(QPen(QColor("#4CAF50"), 2))
        
        for i in range(len(self.data_points) - 1):
            # Calculate x positions
            x1 = margin + (i * chart_width // max(self.max_points - 1, 1))
            x2 = margin + ((i + 1) * chart_width // max(self.max_points - 1, 1))
            
            # Calculate y positions (invert for screen coordinates)
            y1 = chart_top + chart_height - int(((self.data_points[i] - min_val) / (max_val - min_val)) * chart_height)
            y2 = chart_top + chart_height - int(((self.data_points[i + 1] - min_val) / (max_val - min_val)) * chart_height)
            
            painter.drawLine(x1, y1, x2, y2)
            
            # Draw dots at data points
            painter.setPen(QPen(QColor("#81C784"), 1))
            painter.setBrush(QBrush(QColor("#4CAF50")))
            painter.drawEllipse(x1 - 2, y1 - 2, 4, 4)
        
        # Draw the last point
        if self.data_points:
            last_i = len(self.data_points) - 1
            x_last = margin + (last_i * chart_width // max(self.max_points - 1, 1))
            y_last = chart_top + chart_height - int(((self.data_points[-1] - min_val) / (max_val - min_val)) * chart_height)
            painter.drawEllipse(x_last - 2, y_last - 2, 4, 4)

class MainWindow(QMainWindow):
    """Modern AI Fitness Coach Main Window with Welcome Screen System"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Fitness Coach - Advanced Form Analysis")
        
        # User profile data
        self.user_profile_data = None
        
        # Core components
        self.config_manager = ConfigManager()
        self.camera_manager = None
        self.session_manager = SessionManager()
        
        # Session tracking
        self.session_start_time = None
        self.session_duration = 0
        self.session_feedback_messages = []  # Store all feedback messages
        self._last_rep_count = 0  # Track rep count for visual effects
        self._last_report_ts = 0  # Track report timestamps
        
        # Load settings
        self.current_settings = self.config_manager.get_analysis_settings()
        ui_settings = self.config_manager.get_ui_settings()
        self.resize(ui_settings.get('window_width', 1600), ui_settings.get('window_height', 1000))
        
        # UPDATED: Create threshold configuration (now required for Task 2)
        self.threshold_config = ThresholdConfig.emergency_calibrated()
        
        # UPDATED: Create user profile with proper skill level mapping
        self.user_profile = UserProfile(user_id="main_user", skill_level=UserLevel.INTERMEDIATE)
        
        # UPDATED: Create pose processor that will initialize form grader with proper config
        self.pose_processor = PoseProcessor(
            user_profile=self.user_profile,
            threshold_config=self.threshold_config
        )
        
        # Timers
        self.timer = QTimer(self)
        self.rep_analysis_display_timer = QTimer(self)
        self.rep_analysis_display_timer.setSingleShot(True)
        self._last_report_ts = 0
        
        # Session duration timer
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self.update_session_duration)
        
        # Countdown timer for 3-second start delay
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_active = False
        self.countdown_seconds = 3
        
        # Setup UI
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the modern UI with screen management system"""
        # Modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e1e1e, stop:1 #2d2d2d);
            }
            QLabel { color: #e0e0e0; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #388E3C);
                color: white; border: none;
                padding: 12px 20px; border-radius: 8px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66BB6A, stop:1 #4CAF50);
            }
            QPushButton:disabled {
                background-color: #555; color: #aaa;
            }
            QTextEdit {
                background-color: #2a2a2a; color: #e0e0e0;
                border: 1px solid #555; border-radius: 8px;
                padding: 10px; font-size: 13px;
            }
            QComboBox {
                background-color: #3c3c3c; color: #e0e0e0;
                border: 1px solid #555; border-radius: 6px;
                padding: 8px; font-size: 14px;
            }
        """)
        
        # Create the stacked widget for screen management
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create screens
        self.welcome_screen = WelcomeScreen()
        self.main_menu_screen = MainMenuScreen()
        self.squat_guide_screen = SquatGuideScreen()
        self.analysis_widget = self._create_analysis_widget()  # The original main interface
        
        # Add screens to stack
        self.stacked_widget.addWidget(self.welcome_screen)      # Index 0
        self.stacked_widget.addWidget(self.main_menu_screen)    # Index 1
        self.stacked_widget.addWidget(self.squat_guide_screen)  # Index 2
        self.stacked_widget.addWidget(self.analysis_widget)     # Index 3
        
        # Start with welcome screen
        self.stacked_widget.setCurrentIndex(0)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e; color: #4CAF50;
                border-top: 1px solid #555; padding: 5px;
                font-size: 13px; font-weight: bold;
            }
        """)
        self.status_bar.showMessage("🏋️ Welcome to AI Fitness Coach - Click Start to begin!")
    
    def _create_analysis_widget(self):
        """Create the original analysis interface as a widget"""
        # Main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)  # Reduced spacing
        main_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (compact dashboard + video)
        left_panel = self._create_video_panel_with_dashboard()
        
        # Right panel (analytics) - completely redesigned
        right_panel = self._create_modern_analytics_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([1000, 600])  # Adjusted for dashboard + video
        
        # Allow splitter to be resizable
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(3)
        
        return central_widget
        main_layout.setSpacing(10)  # Reduced spacing
        main_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (video)
        left_panel = self._create_video_panel()
        
        # Right panel (analytics) - completely redesigned
        right_panel = self._create_modern_analytics_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([1200, 400])  # Give even more space to video (was 1000, 500)
        
        # Allow splitter to be resizable
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(3)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e; color: #4CAF50;
                border-top: 1px solid #555; padding: 5px;
                font-size: 13px; font-weight: bold;
            }
        """)
        self.status_bar.showMessage("🏋️ AI Fitness Coach Ready - Select a source to start training")
    
    def _create_video_panel(self):
        """Create the video panel with improved full-window display"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)  # Small margins instead of none
        layout.setSpacing(8)  # Increased spacing for better separation
        
        # Video card - expanded for full window usage
        video_card = ModernCardWidget("🎥 Live Video Feed")
        video_card.content_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins
        
        self.video_label = QLabel("Press 'Start Webcam' or 'Load Video'")
        self.video_label.setAlignment(Qt.AlignCenter)
        
        # Remove fixed minimum size and let it expand
        self.video_label.setMinimumSize(400, 300)  # Reduced from 800x600
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setScaledContents(False)  # Keep this False for proper aspect ratio
        
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #555; 
                background-color: #222;
                border-radius: 10px;
                margin: 2px;
            }
        """)
        
        video_card.content_layout.addWidget(self.video_label)
        layout.addWidget(video_card, 3)  # Give video card high stretch but not maximum
        
        # Controls card - compact
        controls_card = ModernCardWidget("🎮 Controls")
        controls_layout = QHBoxLayout()
        
        self.webcam_button = QPushButton("🎥 Start Webcam")
        self.video_button = QPushButton("📁 Load Video")
        self.stop_button = QPushButton("⏹️ Stop Session")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F44336, stop:1 #D32F2F);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #EF5350, stop:1 #F44336);
            }
        """)
        
        # UPDATED: 4-level difficulty system
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner", "Casual", "Professional", "Expert"])
        self.difficulty_combo.setCurrentText("Casual")
        
        controls_layout.addWidget(self.webcam_button)
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.stop_button)
        
        # Voice feedback controls
        self.voice_feedback_button = QPushButton("🔊 Voice: ON")
        self.voice_feedback_button.setCheckable(True)
        self.voice_feedback_button.setChecked(True)
        self.voice_feedback_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #388E3C);
            }
        """)
        controls_layout.addWidget(self.voice_feedback_button)
        
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Difficulty:"))
        controls_layout.addWidget(self.difficulty_combo)
        
        controls_card.content_layout.addLayout(controls_layout)
        controls_card.setMinimumHeight(100)  # Ensure controls are visible
        controls_card.setMaximumHeight(120)  # Increased from 80 to give more space
        layout.addWidget(controls_card, 0)  # No stretch for controls
        
        return panel
    
    def _create_video_panel_with_dashboard(self):
        """Create the video panel with compact session dashboard on the left"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # === COMPACT SESSION DASHBOARD ===
        self.session_dashboard = self._create_compact_session_dashboard()
        layout.addWidget(self.session_dashboard, 0)  # No stretch - fixed height
        
        # === VIDEO SECTION ===
        video_card = ModernCardWidget("🎥 Live Video Feed")
        video_card.content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.video_label = QLabel("Press 'Start Webcam' or 'Load Video'")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(400, 300)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setScaledContents(False)
        
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #555; 
                background-color: #222;
                border-radius: 10px;
                margin: 2px;
            }
        """)
        
        video_card.content_layout.addWidget(self.video_label)
        layout.addWidget(video_card, 3)  # Give video most of the space
        
        # === CONTROLS ===
        controls_card = ModernCardWidget("🎮 Controls")
        controls_layout = QHBoxLayout()
        
        self.webcam_button = QPushButton("🎥 Start Webcam")
        self.video_button = QPushButton("📁 Load Video")
        self.stop_button = QPushButton("⏹️ Stop Session")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F44336, stop:1 #D32F2F);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #EF5350, stop:1 #F44336);
            }
        """)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner", "Casual", "Professional", "Expert"])
        self.difficulty_combo.setCurrentText("Casual")
        
        controls_layout.addWidget(self.webcam_button)
        controls_layout.addWidget(self.video_button)
        controls_layout.addWidget(self.stop_button)
        
        # Voice feedback controls
        self.voice_feedback_button = QPushButton("🔊 Voice: ON")
        self.voice_feedback_button.setCheckable(True)
        self.voice_feedback_button.setChecked(True)
        self.voice_feedback_button.clicked.connect(self.toggle_voice_feedback)
        controls_layout.addWidget(self.voice_feedback_button)
        
        controls_layout.addWidget(QLabel("Difficulty:"))
        controls_layout.addWidget(self.difficulty_combo)
        
        controls_card.content_layout.addLayout(controls_layout)
        controls_card.setMaximumHeight(120)
        layout.addWidget(controls_card, 0)
        
        return panel
    
    def _create_compact_session_dashboard(self):
        """Create a compact session dashboard with just a performance chart"""
        dashboard_card = ModernCardWidget("📊 Performance Chart")
        dashboard_card.setMaximumHeight(120)  # Keep it compact
        dashboard_card.setMinimumHeight(120)
        
        # Create main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        
        # Create simple performance chart
        self.compact_chart = CompactPerformanceChart()
        main_layout.addWidget(self.compact_chart, 1)  # Take most space
        
        # Reset button for session (smaller, on the right)
        reset_button = QPushButton("🔄")
        reset_button.setMaximumWidth(40)
        reset_button.setMaximumHeight(40)
        reset_button.setToolTip("Reset Session")
        reset_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #607D8B, stop:1 #455A64);
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #78909C, stop:1 #607D8B);
            }
        """)
        reset_button.clicked.connect(self._reset_session)
        
        main_layout.addWidget(reset_button, 0)  # No stretch - fixed size
        
        dashboard_card.content_layout.addLayout(main_layout)
        
        # Initialize session tracking
        self.session_start_time = None
        self.session_reps = 0
        self.session_scores = []
        
        return dashboard_card
    
    def _reset_session(self):
        """Reset the session statistics"""
        self.session_start_time = None
        self.session_reps = 0
        self.session_scores = []
        
        # Reset compact chart
        if hasattr(self, 'compact_chart'):
            self.compact_chart.reset_chart()
        
        print("🔄 Session stats reset")
    
    def _create_modern_analytics_panel(self):
        """Create OPTIMIZED analytics panel with feedback prioritized"""
        panel = QWidget()
        panel.setMinimumWidth(450)
        panel.setMaximumWidth(700) 
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        self._prev_scores = {'overall': None, 'safety': None, 'depth': None, 'stability': None}
        
        # === AI COACHING FEEDBACK CARD - EXPANDED ===
        feedback_card = ModernCardWidget("💬 AI Coaching Feedback")
        
        # Enhanced feedback status bar
        feedback_status_layout = QHBoxLayout()
        self.voice_status_label = QLabel("🔊 Voice: Ready")
        self.voice_status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50; font-weight: bold; font-size: 12px;
                padding: 4px 8px; background-color: rgba(76, 175, 80, 0.1);
                border-radius: 4px; border: 1px solid rgba(76, 175, 80, 0.3);
            }
        """)
        
        self.feedback_stats_label = QLabel("Messages: 0 | Voice: 0")
        self.feedback_stats_label.setStyleSheet("""
            QLabel {
                color: #2196F3; font-size: 11px; padding: 4px 8px;
                background-color: rgba(33, 150, 243, 0.1);
                border-radius: 4px; border: 1px solid rgba(33, 150, 243, 0.3);
            }
        """)
        
        feedback_status_layout.addWidget(self.voice_status_label)
        feedback_status_layout.addStretch()
        feedback_status_layout.addWidget(self.feedback_stats_label)
        
        feedback_card.content_layout.addLayout(feedback_status_layout)
        
        # Main feedback display
        self.feedback_display = QTextEdit()
        self.feedback_display.setReadOnly(True)
        self.feedback_display.setPlaceholderText("🏋️ Complete a rep to receive detailed coaching feedback...")
        self.feedback_display.setMinimumHeight(200)
        self.feedback_display.setMaximumHeight(280)
        
        self.feedback_display.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a; 
                color: #e0e0e0;
                border: 1px solid #555; 
                border-radius: 8px;
                padding: 12px; 
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        
        feedback_card.content_layout.addWidget(self.feedback_display)
        layout.addWidget(feedback_card)
        
        # === PERFORMANCE DASHBOARD CARD - COMPLETELY REDESIGNED ===
        dashboard_card = ModernCardWidget("📊 Performance Dashboard")
        dashboard_layout = QVBoxLayout()
        dashboard_layout.setSpacing(8)
        dashboard_layout.setContentsMargins(10, 10, 10, 10)

        # Top row: Rep counter and reset button
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        # Rep counter - modern circular design
        rep_container = QWidget()
        rep_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            QWidget:hover {
                border: 2px solid rgba(255, 255, 255, 0.4);
            }
        """)
        rep_layout = QVBoxLayout(rep_container)
        rep_layout.setSpacing(1)
        rep_layout.setContentsMargins(8, 6, 8, 6)
        
        rep_title = QLabel("REPS")
        rep_title.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9); 
                font-size: 9px; 
                font-weight: bold;
                background: transparent;
                border: none;
                letter-spacing: 1px;
            }
        """)
        rep_title.setAlignment(Qt.AlignCenter)
        
        self.rep_label = QLabel("0")
        self.rep_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 900;
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 2px;
                min-height: 35px;
                text-align: center;
                font-family: 'Arial Black', Arial, sans-serif;
            }
        """)
        self.rep_label.setAlignment(Qt.AlignCenter)
        
        rep_layout.addWidget(rep_title)
        rep_layout.addWidget(self.rep_label)
        rep_container.setFixedSize(85, 65)  # Much more compact size
        
        # Reset button
        reset_button = QPushButton("🔄 Reset")
        reset_button.setFixedSize(80, 30)
        reset_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF6B6B, stop:1 #E63946);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E63946, stop:1 #D62828);
            }
        """)
        reset_button.clicked.connect(self._reset_analytics_panel)
        
        top_row.addWidget(rep_container)
        top_row.addStretch()
        top_row.addWidget(reset_button)
        
        # Progress bars for scores
        scores_layout = QVBoxLayout()
        scores_layout.setSpacing(4)
        
        self.overall_progress = ModernProgressBar("Overall Score", "#2196F3")
        self.safety_progress = ModernProgressBar("Safety", "#FF5722")
        self.depth_progress = ModernProgressBar("Depth", "#9C27B0") 
        self.stability_progress = ModernProgressBar("Stability", "#FF9800")
        
        scores_layout.addWidget(self.overall_progress)
        scores_layout.addWidget(self.safety_progress)
        scores_layout.addWidget(self.depth_progress)
        scores_layout.addWidget(self.stability_progress)
        
        dashboard_layout.addLayout(top_row)
        dashboard_layout.addLayout(scores_layout)
        dashboard_card.content_layout.addLayout(dashboard_layout)
        layout.addWidget(dashboard_card)
        
        # === LIVE METRICS CARD - REDESIGNED ===
        metrics_card = ModernCardWidget("⚡ Live Metrics")
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(4)
        
        self.tempo_widget = CompactMetricWidget("Tempo", "⏱️", "#00BCD4")
        self.depth_widget = CompactMetricWidget("Depth", "⬇️", "#8BC34A")  # Changed from ROM
        self.phase_widget = CompactMetricWidget("Phase", "🎯", "#E91E63")
        
        metrics_layout.addWidget(self.tempo_widget)
        metrics_layout.addWidget(self.depth_widget)
        metrics_layout.addWidget(self.phase_widget)
        
        metrics_card.content_layout.addLayout(metrics_layout)
        layout.addWidget(metrics_card)
        
        layout.addStretch(1)
        return panel
        
        # === LIVE METRICS CARD - IMPROVED DEFINITIONS ===
        metrics_card = ModernCardWidget("⚡ Live Metrics")
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(5)
        
        # Better defined metrics
        self.tempo_widget = MetricDisplayWidget("Tempo", "⏱️", "#00BCD4")
        self.rom_widget = MetricDisplayWidget("ROM", "�", "#8BC34A")  # Changed from "Range"
        self.phase_widget = MetricDisplayWidget("Phase", "🎯", "#E91E63")
        
        metrics_layout.addWidget(self.tempo_widget)
        metrics_layout.addWidget(self.rom_widget)
        metrics_layout.addWidget(self.phase_widget)
        
        metrics_card.content_layout.addLayout(metrics_layout)
        layout.addWidget(metrics_card)
        
        # Add minimal stretch
        layout.addStretch(1)
        
        return panel
    
    def setup_menu_bar(self):
        """Setup menu bar with navigation options"""
        menubar = self.menuBar()
        
        # Navigation menu
        nav_menu = menubar.addMenu('🏠 Navigation')
        back_to_menu_action = QAction('🏠 Back to Main Menu', self, triggered=self.show_main_menu)
        show_guide_action = QAction('📖 Squat Guide', self, triggered=self.show_squat_guide)
        nav_menu.addActions([back_to_menu_action, show_guide_action])
        nav_menu.addSeparator()
        
        file_menu = menubar.addMenu('📁 File')
        open_video_action = QAction('📹 Open Video...', self, triggered=self.open_video_file)
        start_webcam_action = QAction('🎥 Start Webcam', self, triggered=self.start_webcam)
        file_menu.addActions([open_video_action, start_webcam_action])
        file_menu.addSeparator()
        exit_action = QAction('🚪 Exit', self, triggered=self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu('📊 View')
        show_report_action = QAction('📈 Session Report...', self, triggered=self.show_session_report)
        view_menu.addAction(show_report_action)
        
        debug_menu = menubar.addMenu('🔧 Debug')
        self.validation_action = QAction('🔍 Enable Validation Mode', self, checkable=True)
        self.validation_action.setChecked(False)
        self.validation_action.triggered.connect(self.toggle_validation_mode)
        debug_menu.addAction(self.validation_action)
    
    def setup_connections(self):
        """Setup signal connections for all screens"""
        # Analysis screen connections (original)
        self.webcam_button.clicked.connect(self.start_webcam)
        self.video_button.clicked.connect(self.open_video_file)
        self.stop_button.clicked.connect(self.stop_session)
        self.timer.timeout.connect(self.update_frame)
        self.difficulty_combo.currentTextChanged.connect(self.on_difficulty_changed)
        self.rep_analysis_display_timer.timeout.connect(self.clear_rep_analysis_display)
        
        # Voice feedback connection
        self.voice_feedback_button.clicked.connect(self.toggle_voice_feedback)
        
        # Welcome screen connections
        self.welcome_screen.start_pressed.connect(self.show_user_profile_dialog)
        
        # Main menu connections
        self.main_menu_screen.start_analysis.connect(self.show_analysis_screen)
        self.main_menu_screen.show_guide.connect(self.show_squat_guide)
        self.main_menu_screen.exit_app.connect(self.close)
        
        # Guide screen connections
        self.squat_guide_screen.back_to_menu.connect(self.show_main_menu)
    
    def show_user_profile_dialog(self):
        """Show user profile collection dialog"""
        dialog = UserProfileDialog(self)
        if dialog.exec() == 1:  # QDialog.Accepted = 1
            self.user_profile_data = dialog.get_user_data()
            
            # Update user profile and interface
            if self.user_profile_data:
                self.main_menu_screen.set_user_profile(self.user_profile_data)
                
                # Update the actual user profile object
                self.user_profile.user_id = self.user_profile_data['name'].lower().replace(' ', '_')
                
                # Update status
                self.status_bar.showMessage(f"Welcome {self.user_profile_data['name']}! Ready to start training.", 5000)
            
            # Move to main menu
            self.show_main_menu()
    
    def show_main_menu(self):
        """Show the main menu screen"""
        self.stacked_widget.setCurrentIndex(1)
        self.status_bar.showMessage("🏠 Main Menu - Choose your next action")
    
    def show_squat_guide(self):
        """Show the squat guide screen"""
        self.stacked_widget.setCurrentIndex(2)
        self.status_bar.showMessage("📖 Squat Guide - Learn proper technique")
    
    def show_analysis_screen(self):
        """Show the analysis screen"""
        self.stacked_widget.setCurrentIndex(3)
        self.status_bar.showMessage("🎯 Analysis Mode - Select webcam or video to begin")
    
    # === CORE METHODS (keeping existing logic but updating display calls) ===
    
    def start_webcam(self):
        self._start_session(0)
    
    def open_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self._start_session(file_path)
    
    def _start_session(self, source):
        """Start session (keeping existing logic)"""
        try:
            if self.camera_manager:
                self.camera_manager.release()
            
            self.camera_manager = CameraManager(source)
            if not self.camera_manager.isOpened():
                raise RuntimeError(f"Failed to open source: {source}")
            
            if isinstance(source, int):
                self.camera_manager.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.camera_manager.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            source_type = 'video' if isinstance(source, str) else 'webcam'
            self.pose_processor.start_session(source_type)
            
            # Start session timing
            self.session_start_time = time.time()
            self.session_feedback_messages = []  # Clear previous messages
            self.session_timer.start(1000)  # Update every second
            
            self.webcam_button.setEnabled(False)
            self.video_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Start countdown before beginning analysis
            self.countdown_active = True
            self.countdown_seconds = 3
            self.countdown_timer.start(1000)  # Update every second
            self.status_bar.showMessage("🕐 Get ready! Starting in 3 seconds...")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start session:\n{e}")
    
    def stop_session(self):
        """Stop session (keeping existing logic)"""
        if not self.stop_button.isEnabled():
            return
        
        # Calculate session duration
        if self.session_start_time:
            self.session_duration = time.time() - self.session_start_time
        
        self.timer.stop()
        
        # Stop countdown timer if active
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()
            self.countdown_active = False
        
        # Stop session timing
        self.session_timer.stop()
        
        if self.camera_manager:
            self.camera_manager.release()
            self.camera_manager = None
        
        self.pose_processor.end_session()
        
        self.webcam_button.setEnabled(True)
        self.video_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.video_label.setText("Session stopped. Select a source to begin.")
        
        # Keep compact dashboard stats for review - user can manually reset
        
        # Show report after delay
        from PySide6.QtCore import QTimer
        def show_delayed_report():
            total_reps = int(self.rep_label.text()) if self.rep_label.text().isdigit() else 0
            if total_reps > 0:
                self.show_enhanced_session_report()
        
        QTimer.singleShot(500, show_delayed_report)
    
    def update_session_duration(self):
        """Update the session duration display"""
        try:
            if hasattr(self, 'session_start_time') and self.session_start_time:
                current_time = time.time()
                duration = current_time - self.session_start_time
                
                # Update the session duration metric
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes:02d}:{seconds:02d}"
                
                # Update the session duration widget if it exists
                if hasattr(self, 'session_duration_widget'):
                    self.session_duration_widget.value_label.setText(duration_text)
        except Exception as e:
            print(f"Error updating session duration: {e}")
    
    def update_countdown(self):
        """Update countdown timer and start session when complete"""
        try:
            if self.countdown_seconds > 0:
                self.countdown_seconds -= 1
                # Force frame update to show countdown
                if self.camera_manager and self.camera_manager.isOpened():
                    frame = self.camera_manager.get_frame()
                    if frame is not None:
                        # Draw countdown overlay
                        frame = self.draw_countdown_overlay(frame)
                        self.display_frame_improved(frame)
            else:
                # Countdown finished, start actual analysis
                self.countdown_timer.stop()
                self.countdown_active = False
                self.timer.start(30)  # Start main frame processing
                self.status_bar.showMessage("🏋️ Session Started - Begin your workout!")
        except Exception as e:
            print(f"Error updating countdown: {e}")
    
    def draw_countdown_overlay(self, frame):
        """Draw countdown overlay on video frame"""
        try:
            height, width = frame.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            # Draw semi-transparent background circle
            overlay = frame.copy()
            cv2.circle(overlay, (center_x, center_y), 100, (0, 0, 0), -1)
            frame = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
            
            # Draw countdown number or "START!"
            font_scale = 4
            thickness = 8
            if self.countdown_seconds > 0:
                text = str(self.countdown_seconds)
                color = (0, 255, 255)  # Yellow
            else:
                text = "START!"
                color = (0, 255, 0)    # Green
                font_scale = 2.5
                
            # Get text size for centering
            (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_x = center_x - text_width // 2
            text_y = center_y + text_height // 2
            
            # Draw text with black outline
            cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 4)
            cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
            
            # Draw instruction text
            instruction = "Get ready to start squatting!"
            if self.countdown_seconds <= 0:
                instruction = "Begin your workout now!"
                
            (inst_width, inst_height), _ = cv2.getTextSize(instruction, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
            inst_x = center_x - inst_width // 2
            inst_y = center_y + 150
            
            cv2.putText(frame, instruction, (inst_x, inst_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
            cv2.putText(frame, instruction, (inst_x, inst_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        except Exception as e:
            print(f"Error drawing countdown overlay: {e}")
        
        return frame
    
    def update_frame(self):
        """Main update loop with enhanced display"""
        frame = self.camera_manager.get_frame()
        if frame is None:
            self.stop_session()
            return
        
        live_metrics = self.pose_processor.process_frame(frame)
        
        # Update rep count with visual feedback
        rep_count = live_metrics.get('rep_count', 0)
        self.rep_label.setText(str(rep_count))
        
        # Add visual flash effect when rep count increases
        if hasattr(self, '_last_rep_count'):
            if rep_count > self._last_rep_count:
                # Flash effect for new rep
                self.rep_label.setStyleSheet("""
                    QLabel {
                        color: #FFD700;
                        font-size: 32px;
                        font-weight: 900;
                        background: rgba(255, 215, 0, 0.15);
                        border: 2px solid #FFD700;
                        border-radius: 8px;
                        padding: 2px;
                        min-height: 35px;
                        text-align: center;
                        font-family: 'Arial Black', Arial, sans-serif;
                    }
                """)
                # Reset to normal after brief flash
                QTimer.singleShot(500, lambda: self.rep_label.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 32px;
                        font-weight: 900;
                        background: transparent;
                        border: none;
                        border-radius: 8px;
                        padding: 2px;
                        min-height: 35px;
                        text-align: center;
                        font-family: 'Arial Black', Arial, sans-serif;
                    }
                """))
        self._last_rep_count = rep_count
        
        # Update phase
        phase = live_metrics.get('phase', 'Ready')
        phase_map = {
            'bottom': 'Bottom',
            'descent': 'Down', 
            'ascent': 'Up',
            'standing': 'Ready',
            'ready': 'Ready',
        }
        friendly_phase = phase_map.get(phase.lower(), phase.capitalize() if phase else 'Ready')
        self.phase_widget.setValue(friendly_phase)
        
        # UPDATE: Real-time depth calculation per phase
        current_depth_rating = self._calculate_live_depth_rating(live_metrics)
        self.depth_widget.setValue(current_depth_rating)
        
        # Update tempo based on current movement
        tempo_info = live_metrics.get('tempo', '--')
        if isinstance(tempo_info, (int, float)) and tempo_info > 0:
            self.tempo_widget.setValue(f"{tempo_info:.1f}s")
        else:
            self.tempo_widget.setValue("--")
        
        # Display frame
        processed_frame = live_metrics.get('processed_frame')
        if processed_frame is not None:
            self.display_frame_improved(processed_frame)
        
        # Handle rep analysis
        report = live_metrics.get('last_rep_analysis')
        if report and report.get('timestamp', 0) > self._last_report_ts:
            self._last_report_ts = report['timestamp']
            self.display_comprehensive_analysis(report)
            
            self.session_manager.update_session(
                rep_count=rep_count,
                form_score=report.get('score', 0),
                phase=phase,
                fault_data=report.get('faults', [])
            )
            
            # Update session dashboard
            if hasattr(self, 'compact_chart'):
                # Initialize session start time on first rep
                if self.session_start_time is None:
                    self.session_start_time = time.time()
                
                # Update session tracking
                self.session_reps = rep_count
                current_score = report.get('score', 0)
                self.session_scores.append(current_score)
                
                # Update the performance chart
                self.compact_chart.add_rep_score(rep_count, current_score)
        
        # Status bar
        status_msg = (f"📊 FPS: {live_metrics.get('fps', 0):.1f} | "
                     f"🎯 Reps: {rep_count} | "
                     f"🤖 Pose: {'✅' if live_metrics.get('landmarks_detected') else '❌'}")
        self.status_bar.showMessage(status_msg)
    
    def display_frame_improved(self, frame):
        """Enhanced frame display with better window filling"""
        try:
            h, w, ch = frame.shape
            
            if ch == 3:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytes_per_line = ch * w
                q_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            else:
                bytes_per_line = ch * w
                q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
            
            pixmap = QPixmap.fromImage(q_image)
            
            # Get the actual available space in the video label
            label_size = self.video_label.size()
            
            # Scale to fit the available space while maintaining aspect ratio
            if label_size.width() > 0 and label_size.height() > 0:
                scaled_pixmap = pixmap.scaled(
                    label_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error displaying frame: {e}")
    
    def display_comprehensive_analysis(self, analysis: dict):
        """FIXED: Display analysis with proper data extraction"""
        if not isinstance(analysis, dict):
            return
        
        try:
            # Overall score
            overall_score = self._safe_extract_number(analysis.get('score', 0))
            # Progress indicator for overall
            prev_overall = self._prev_scores.get('overall')
            delta_overall = None
            if prev_overall is not None:
                delta_overall = overall_score - prev_overall
            # Store current score for progress tracking
            self._prev_scores['overall'] = overall_score
            
            # Component scores - FIXED data extraction
            component_scores = analysis.get('component_scores', {})
            
            # Extract safety score
            safety_data = component_scores.get('safety', {})
            if isinstance(safety_data, dict):
                safety_score = self._safe_extract_number(safety_data.get('score', 0))
            else:
                safety_score = self._safe_extract_number(safety_data)
            
            # Extract depth score  
            depth_data = component_scores.get('depth', {})
            if isinstance(depth_data, dict):
                depth_score = self._safe_extract_number(depth_data.get('score', 0))
            else:
                depth_score = self._safe_extract_number(depth_data)
            
            # Extract stability score
            stability_data = component_scores.get('stability', {})
            if isinstance(stability_data, dict):
                stability_score = self._safe_extract_number(stability_data.get('score', 0))
            else:
                stability_score = self._safe_extract_number(stability_data)
            
            # Update progress bars
            self.overall_progress.setValue(overall_score)
            self.safety_progress.setValue(safety_score)
            self.depth_progress.setValue(depth_score)
            self.stability_progress.setValue(stability_score)
            
            # Store current scores for next comparison
            self._prev_scores['overall'] = overall_score
            self._prev_scores['safety'] = safety_score
            self._prev_scores['depth'] = depth_score
            self._prev_scores['stability'] = stability_score
            
            # Store feedback message for session summary
            # Calculate tempo from phase durations
            phase_durations = analysis.get('phase_durations', {})
            rep_tempo = 0
            if isinstance(phase_durations, dict):
                rep_tempo = sum(v for v in phase_durations.values() if isinstance(v, (int, float)))
            
            feedback_entry = {
                'timestamp': time.time(),
                'rep_number': self.rep_label.text(),
                'overall_score': overall_score,
                'safety_score': safety_score,
                'depth_score': depth_score,
                'stability_score': stability_score,
                'tempo': rep_tempo,  # Add tempo per rep
                'faults': analysis.get('faults', []),
                'feedback': analysis.get('feedback', []),
                'recommendations': analysis.get('recommendations', [])
            }
            self.session_feedback_messages.append(feedback_entry)
            
            # Update live metrics
            phase_durations = analysis.get('phase_durations', {})
            if isinstance(phase_durations, dict):
                total_duration = sum(v for v in phase_durations.values() if isinstance(v, (int, float)))
                self.tempo_widget.setValue(f"{total_duration:.1f}s" if total_duration > 0 else "--")
            else:
                self.tempo_widget.setValue("--")

            # Convert depth score to user-friendly depth rating
            depth_score = self._safe_extract_number(depth_data.get('score', 0)) if isinstance(depth_data, dict) else self._safe_extract_number(depth_data)
            depth_rating = "N/A"
            if depth_score is not None and depth_score > 0:
                if depth_score >= 0.8:
                    depth_rating = "Full"
                elif depth_score >= 0.6:
                    depth_rating = "Good"
                elif depth_score >= 0.4:
                    depth_rating = "Partial"
                else:
                    depth_rating = "Shallow"
            
            self.depth_widget.setValue(depth_rating)

            # Phase - user-friendly
            phase_map = {
                'bottom': 'Bottom',
                'descent': 'Down',
                'ascent': 'Up',
                'standing': 'Ready',
                'ready': 'Ready',
            }
            phase = analysis.get('phase', '').lower()
            friendly_phase = phase_map.get(phase, phase.capitalize() if phase else '--')
            self.phase_widget.setValue(friendly_phase)
            
            # Enhanced feedback display with reduced items and smaller fonts
            feedback = analysis.get('feedback', [])
            faults = analysis.get('faults', [])
            
            feedback_html = f"""
            <div style='font-family: Arial; color: #e0e0e0; line-height: 1.4; font-size: 15px;'>
                <h2 style='color: #4CAF50; text-align: center; margin: 0 0 12px 0; font-size: 20px; font-weight: bold;'>
                    Rep Analysis: {overall_score:.1f}%
                </h2>
            """

            if faults:
                feedback_html += """
                <div style='background: rgba(244, 67, 54, 0.18); padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 2px solid #FF5252;'>
                    <h3 style='color: #FF1744; margin: 0 0 10px 0; font-size: 18px; font-weight: bold; letter-spacing: 1px;'>
                        ⚠️ Key Issues
                    </h3>
                    <ul style='margin: 0; padding-left: 22px; font-size: 15px; font-weight: bold;'>
                """
                for fault in faults[:2]:
                    feedback_html += f"<li style='color: #FF8A80; margin-bottom: 6px;'>{fault}</li>"
                feedback_html += "</ul></div>"

            if feedback:
                feedback_html += """
                <div style='background: rgba(33, 150, 243, 0.10); padding: 10px; border-radius: 8px; margin-bottom: 10px;'>
                    <h3 style='color: #2196F3; margin: 0 0 8px 0; font-size: 16px; font-weight: bold;'>💡 Tips</h3>
                    <ul style='margin: 0; padding-left: 20px; font-size: 14px;'>
                """
                for tip in feedback[:2]:
                    feedback_html += f"<li style='color: #B2DFDB; margin-bottom: 4px;'>{tip}</li>"
                feedback_html += "</ul></div>"

            recommendations = analysis.get('recommendations', [])
            if recommendations:
                feedback_html += """
                <div style='background: rgba(156, 39, 176, 0.10); padding: 10px; border-radius: 8px;'>
                    <h3 style='color: #9C27B0; margin: 0 0 8px 0; font-size: 16px; font-weight: bold;'>🎯 Focus</h3>
                    <ul style='margin: 0; padding-left: 20px; font-size: 14px;'>
                """
                for rec in recommendations[:2]:
                    feedback_html += f"<li style='color: #CE93D8; margin-bottom: 4px;'>{rec}</li>"
                feedback_html += "</ul></div>"

            if not faults and not feedback and not recommendations:
                feedback_html += """
                <div style='background: rgba(76, 175, 80, 0.12); padding: 18px; border-radius: 8px; text-align: center;'>
                    <p style='color: #4CAF50; margin: 0; font-size: 18px; font-weight: bold;'>✨ Excellent form!</p>
                </div>
                """

            feedback_html += "</div>"

            # Enhanced feedback display integration
            self._update_enhanced_feedback_display(analysis)

            self.feedback_display.setHtml(feedback_html)
            self.rep_analysis_display_timer.start(10000)  # Show longer for better readability
            
        except Exception as e:
            print(f"❌ Error in display_comprehensive_analysis: {e}")
    
    def _update_enhanced_feedback_display(self, analysis: dict):
        """Update enhanced feedback status display"""
        try:
            enhanced_feedback = analysis.get('enhanced_feedback', {})
            
            if enhanced_feedback:
                # Update voice status
                if enhanced_feedback.get('status') == 'success':
                    self.voice_status_label.setText("🔊 Voice: Active")
                    self.voice_status_label.setStyleSheet("""
                        QLabel {
                            color: #4CAF50; font-weight: bold; font-size: 12px;
                            padding: 4px 8px; background-color: rgba(76, 175, 80, 0.1);
                            border-radius: 4px; border: 1px solid rgba(76, 175, 80, 0.3);
                        }
                    """)
                else:
                    self.voice_status_label.setText("⚠️ Voice: Error")
                    self.voice_status_label.setStyleSheet("""
                        QLabel {
                            color: #FF9800; font-weight: bold; font-size: 12px;
                            padding: 4px 8px; background-color: rgba(255, 152, 0, 0.1);
                            border-radius: 4px; border: 1px solid rgba(255, 152, 0, 0.3);
                        }
                    """)
                
                # Update feedback statistics
                msg_count = enhanced_feedback.get('messages_generated', 0)
                voice_count = enhanced_feedback.get('voice_messages_sent', 0)
                self.feedback_stats_label.setText(f"Messages: {msg_count} | Voice: {voice_count}")
                
                # Show enhanced feedback details in status bar
                categories = enhanced_feedback.get('feedback_categories', [])
                if categories:
                    unique_categories = list(set(categories))
                    self.status_bar.showMessage(f"🎯 Enhanced feedback: {', '.join(unique_categories[:3])}", 5000)
            else:
                # No enhanced feedback available
                if self.voice_feedback_button.isChecked():
                    self.voice_status_label.setText("🔊 Voice: Ready")
                else:
                    self.voice_status_label.setText("🔇 Voice: OFF")
                    self.voice_status_label.setStyleSheet("""
                        QLabel {
                            color: #757575; font-weight: bold; font-size: 12px;
                            padding: 4px 8px; background-color: rgba(117, 117, 117, 0.1);
                            border-radius: 4px; border: 1px solid rgba(117, 117, 117, 0.3);
                        }
                    """)
                    
        except Exception as e:
            print(f"Error updating enhanced feedback display: {e}")
    
    def update_rep_display(self, rep_count):
        """Manually update rep display with better visual feedback"""
        try:
            self.rep_label.setText(str(rep_count))
            
            # Ensure the label is visible and properly styled
            self.rep_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 32px;
                    font-weight: 900;
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 2px;
                    min-height: 35px;
                    text-align: center;
                    font-family: 'Arial Black', Arial, sans-serif;
                }
            """)
            
            # Force a repaint to make sure the update is visible
            self.rep_label.repaint()
            
        except Exception as e:
            pass  # Silently handle errors

    def clear_rep_analysis_display(self):
        """Clear current rep analysis while preserving session info."""
        try:
            # Reset progress bars for next rep
            self.overall_progress.setValue(0)
            self.safety_progress.setValue(0)
            self.depth_progress.setValue(0)
            self.stability_progress.setValue(0)

            # Update feedback with rep completion
            if hasattr(self, 'rep_label'):
                current_reps = int(self.rep_label.text())
                self.feedback_display.append(f"""
                    <div style='color: #4CAF50; font-size: 10px; margin: 4px 0;'>
                        ✅ Rep {current_reps} completed - Ready for next rep
                    </div>
                """)
            
        except Exception as e:
            # Fallback to simple clear
            self.feedback_display.clear()
            self.feedback_display.setPlaceholderText("🏋️ Complete another rep for coaching feedback...")

    def _reset_analytics_panel(self):
        """Reset all analytics and start fresh session."""
        try:
            # Clear feedback display with welcome message
            self.feedback_display.clear()
            self.feedback_display.append("""
                <div style='color: #4CAF50; font-size: 12px; font-weight: bold; margin-bottom: 8px;'>
                    🚀 SESSION RESET - Ready for new workout!
                </div>
                <div style='color: #888; font-size: 10px;'>
                    📊 All metrics cleared | 🔄 Calibration ready | ⏱️ Timer reset
                </div>
            """)

            # Reset progress bars to zero
            self.overall_progress.setValue(0)
            self.safety_progress.setValue(0)
            self.depth_progress.setValue(0)
            self.stability_progress.setValue(0)

            # Reset performance metrics
            self.rep_label.setText("0")
            
            # Reset live metrics - Updated for per-phase depth
            self.tempo_widget.setValue("--")
            self.depth_widget.setValue("Ready")  # Changed from "--" to "Ready"
            self.phase_widget.setValue("Ready")

            # Reset session data
            if hasattr(self.session_manager, 'reset_session'):
                self.session_manager.reset_session()
            
            # Reset session feedback messages
            self.session_feedback_messages = []
            self.session_start_time = None
            self.session_duration = 0
                
            # Reset pose processor if available
            if hasattr(self, 'pose_processor') and hasattr(self.pose_processor, 'reset'):
                self.pose_processor.reset()

            # Reset progress tracking
            self._prev_scores = {'overall': None, 'safety': None, 'depth': None, 'stability': None}
            
        except Exception as e:
            pass  # Silently handle errors
    
    def _safe_extract_number(self, value, default=0):
        """Safely extract numeric value"""
        try:
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return max(0, min(100, float(value)))
            if isinstance(value, str):
                return max(0, min(100, float(value)))
            return default
        except (ValueError, TypeError):
            return default
    
    def _calculate_rom_from_analysis(self, analysis: dict):
        """Calculate Range of Motion (ROM) from analysis data"""
        try:
            # Try to get ROM from depth analysis
            analysis_details = analysis.get('analysis_details', {})
            if isinstance(analysis_details, dict):
                depth_analysis = analysis_details.get('depth', {})
                if isinstance(depth_analysis, dict):
                    analysis_data = depth_analysis.get('analysis_data', {})
                    if isinstance(analysis_data, dict):
                        # Look for movement range or knee angle range
                        movement_range = analysis_data.get('movement_range', 0)
                        if movement_range > 0:
                            return f"{movement_range:.0f}°"
                        
                        # Fallback: calculate from knee angles if available
                        knee_range = analysis_data.get('knee_angle_range', 0)
                        if knee_range > 0:
                            return f"{knee_range:.0f}°"
            
            # Fallback: use depth score as ROM indicator
            component_scores = analysis.get('component_scores', {})
            depth_data = component_scores.get('depth', {})
            if isinstance(depth_data, dict):
                depth_score = self._safe_extract_number(depth_data.get('score', 0))
                if depth_score > 0:
                    # Convert score to approximate ROM (good score = good ROM)
                    estimated_rom = 60 + (depth_score * 0.8)  # 60-140° range
                    return f"{estimated_rom:.0f}°"
            
            return "--"
            
        except Exception as e:
            print(f"Error calculating ROM: {e}")
            return "--"
    
    def _calculate_live_depth_rating(self, live_metrics):
        """Calculate depth rating based on current pose data - REAL-TIME"""
        try:
            # Get current phase for context
            phase = live_metrics.get('phase', 'ready').lower()
            
            # If not in a movement phase, show ready state
            if phase in ['ready', 'standing']:
                return "Ready"
            
            # Get current pose landmarks for real-time angle calculation
            pose_data = live_metrics.get('pose_data', {})
            landmarks = live_metrics.get('landmarks')
            
            # Try to get knee angles from live pose data
            angles = live_metrics.get('angles', {})
            left_knee = angles.get('knee_angle_left', 180)
            right_knee = angles.get('knee_angle_right', 180)
            
            # Use the minimum (deepest) knee angle for depth assessment
            min_knee_angle = min(left_knee, right_knee)
            
            # Convert knee angle to depth rating (lower angles = deeper squats)
            if min_knee_angle <= 90:
                depth_rating = "Full"      # Excellent depth - competition level
            elif min_knee_angle <= 100:
                depth_rating = "Deep"      # Very good depth - below parallel
            elif min_knee_angle <= 110:
                depth_rating = "Good"      # Good depth - at parallel
            elif min_knee_angle <= 125:
                depth_rating = "Partial"   # Moderate depth - quarter squat
            else:
                depth_rating = "Shallow"   # Needs improvement - barely squatting
            
            # Debug: Print depth info occasionally (every 30 frames)
            import random
            if random.randint(1, 30) == 1:
                print(f"🔍 Live Depth: {depth_rating} (knee: {min_knee_angle:.1f}°, phase: {phase})")
            
            return depth_rating
                
        except Exception as e:
            # Fallback to phase-based estimation if angle calculation fails
            phase = live_metrics.get('phase', 'ready').lower()
            if phase == 'bottom':
                return "Good"      # Assume good depth at bottom
            elif phase == 'descent':
                return "Going"     # In progress
            elif phase == 'ascent':
                return "Done"      # Coming back up
            else:
                return "Ready"     # Default state

    # === REMAINING METHODS (keeping existing implementations) ===
    def on_difficulty_changed(self, text: str):
        """Handle difficulty level changes with proper skill mapping"""
        difficulty = text.lower()
        
        # UPDATED: Map UI difficulty levels to form grader skill levels
        skill_mapping = {
            "beginner": UserLevel.BEGINNER,
            "casual": UserLevel.INTERMEDIATE,     # casual → intermediate  
            "professional": UserLevel.ADVANCED,  # professional → advanced
            "expert": UserLevel.EXPERT           # expert → expert
        }
        
        # Update user profile skill level
        new_skill_level = skill_mapping.get(difficulty, UserLevel.INTERMEDIATE)
        self.user_profile.skill_level = new_skill_level
        
        # Update pose processor with new configuration
        try:
            self.pose_processor = PoseProcessor(
                user_profile=self.user_profile,
                threshold_config=self.threshold_config
            )
            print(f"Difficulty changed to: {difficulty} (Skill Level: {new_skill_level.value})")
        except Exception as e:
            print(f"Error updating difficulty: {e}")
            # Fallback - just change the form grader difficulty if pose processor update fails
            if hasattr(self.pose_processor, 'form_grader'):
                self.pose_processor.form_grader.set_difficulty(difficulty)
    
    def toggle_voice_feedback(self):
        """Toggle voice feedback on/off"""
        try:
            is_enabled = self.voice_feedback_button.isChecked()
            
            # Update button text and style
            if is_enabled:
                self.voice_feedback_button.setText("🔊 Voice: ON")
                self.status_bar.showMessage("🔊 Voice feedback enabled", 3000)
            else:
                self.voice_feedback_button.setText("🔇 Voice: OFF")
                self.status_bar.showMessage("🔇 Voice feedback disabled", 3000)
            
            # Update the form grader voice setting if available
            if (hasattr(self.pose_processor, 'form_grader') and 
                hasattr(self.pose_processor.form_grader, 'set_voice_feedback_enabled')):
                self.pose_processor.form_grader.set_voice_feedback_enabled(is_enabled)
                print(f"Voice feedback {'enabled' if is_enabled else 'disabled'}")
            else:
                print("Enhanced feedback system not available")
                
        except Exception as e:
            print(f"Error toggling voice feedback: {e}")
            self.status_bar.showMessage(f"❌ Error: {e}", 5000)
    
    def show_enhanced_session_report(self):
        """Show comprehensive session report with duration and feedback"""
        try:
            # Calculate session statistics
            total_reps = int(self.rep_label.text()) if self.rep_label.text().isdigit() else 0
            duration_mins = int(self.session_duration // 60) if self.session_duration else 0
            duration_secs = int(self.session_duration % 60) if self.session_duration else 0
            
            # Calculate average scores from feedback messages
            if self.session_feedback_messages:
                avg_overall = sum(msg['overall_score'] for msg in self.session_feedback_messages) / len(self.session_feedback_messages)
                avg_safety = sum(msg['safety_score'] for msg in self.session_feedback_messages) / len(self.session_feedback_messages)
                avg_depth = sum(msg['depth_score'] for msg in self.session_feedback_messages) / len(self.session_feedback_messages)
                avg_stability = sum(msg['stability_score'] for msg in self.session_feedback_messages) / len(self.session_feedback_messages)
                avg_tempo = sum(msg['tempo'] for msg in self.session_feedback_messages if msg['tempo'] > 0) / len([msg for msg in self.session_feedback_messages if msg['tempo'] > 0]) if any(msg['tempo'] > 0 for msg in self.session_feedback_messages) else 0
            else:
                avg_overall = avg_safety = avg_depth = avg_stability = avg_tempo = 0
            
            # Collect all unique issues and tips
            all_faults = []
            all_feedback = []
            all_recommendations = []
            for msg in self.session_feedback_messages:
                all_faults.extend(msg['faults'])
                all_feedback.extend(msg['feedback'])
                all_recommendations.extend(msg['recommendations'])
            
            unique_faults = list(set(all_faults))[:5]  # Top 5 unique issues
            unique_feedback = list(set(all_feedback))[:5]  # Top 5 unique tips
            unique_recommendations = list(set(all_recommendations))[:3]  # Top 3 recommendations
            
            # Create enhanced HTML report
            report_html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        background: linear-gradient(135deg, #1e1e1e, #2d2d2d);
                        color: #e0e0e0; 
                        margin: 20px; 
                        line-height: 1.6;
                    }}
                    .header {{ 
                        text-align: center; 
                        background: linear-gradient(135deg, #4CAF50, #45a049);
                        color: white; 
                        padding: 20px; 
                        border-radius: 15px; 
                        margin-bottom: 20px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    }}
                    .section {{ 
                        background: rgba(42, 42, 42, 0.8); 
                        padding: 15px; 
                        margin: 15px 0; 
                        border-radius: 10px;
                        border-left: 4px solid #4CAF50;
                    }}
                    .stats-grid {{ 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                        gap: 15px; 
                        margin: 15px 0; 
                    }}
                    .stat-card {{ 
                        background: linear-gradient(135deg, #333, #444);
                        padding: 15px; 
                        border-radius: 8px; 
                        text-align: center;
                        border: 2px solid #555;
                    }}
                    .stat-value {{ 
                        font-size: 24px; 
                        font-weight: bold; 
                        color: #4CAF50; 
                    }}
                    .feedback-item {{ 
                        background: rgba(60, 60, 60, 0.6); 
                        padding: 8px; 
                        margin: 5px 0; 
                        border-radius: 5px;
                        border-left: 3px solid #2196F3;
                    }}
                    .fault-item {{ 
                        background: rgba(244, 67, 54, 0.1); 
                        border-left: 3px solid #F44336;
                    }}
                    .tip-item {{ 
                        background: rgba(76, 175, 80, 0.1); 
                        border-left: 3px solid #4CAF50;
                    }}
                    .duration {{ 
                        font-size: 18px; 
                        color: #FFD700; 
                        font-weight: bold; 
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🏋️ Workout Session Complete!</h1>
                    <div class="duration">Session Duration: {duration_mins:02d}:{duration_secs:02d}</div>
                </div>
                
                <div class="section">
                    <h2>📊 Session Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{total_reps}</div>
                            <div>Total Reps</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{avg_overall:.1f}%</div>
                            <div>Avg Overall</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{avg_safety:.1f}%</div>
                            <div>Avg Safety</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{avg_depth:.1f}%</div>
                            <div>Avg Depth</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{avg_stability:.1f}%</div>
                            <div>Avg Stability</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{avg_tempo:.1f}s</div>
                            <div>Avg Tempo</div>
                        </div>
                    </div>
                </div>
            """
            
            # Add feedback messages section
            if self.session_feedback_messages:
                report_html += """
                <div class="section">
                    <h2>💬 Rep-by-Rep Performance</h2>
                """
                
                for msg in self.session_feedback_messages[-5:]:  # Last 5 reps
                    tempo_display = f"{msg['tempo']:.1f}s" if msg['tempo'] > 0 else "N/A"
                    report_html += f"""
                    <div class="feedback-item">
                        <strong>Rep {msg['rep_number']} - Overall: {msg['overall_score']:.1f}% | Tempo: {tempo_display}</strong>
                        <br>Safety: {msg['safety_score']:.1f}% | Depth: {msg['depth_score']:.1f}% | Stability: {msg['stability_score']:.1f}%
                    </div>
                    """
                
                report_html += "</div>"
            
            # Add key issues section
            if unique_faults:
                report_html += """
                <div class="section">
                    <h2>⚠️ Key Areas for Improvement</h2>
                """
                for fault in unique_faults:
                    report_html += f'<div class="feedback-item fault-item">• {fault}</div>'
                report_html += "</div>"
            
            # Add tips section
            if unique_feedback:
                report_html += """
                <div class="section">
                    <h2>💡 Key Tips from This Session</h2>
                """
                for tip in unique_feedback:
                    report_html += f'<div class="feedback-item tip-item">• {tip}</div>'
                report_html += "</div>"
            
            # Add recommendations section
            if unique_recommendations:
                report_html += """
                <div class="section">
                    <h2>🎯 Recommendations</h2>
                """
                for rec in unique_recommendations:
                    report_html += f'<div class="feedback-item">• {rec}</div>'
                report_html += "</div>"
            
            report_html += """
                <div class="section">
                    <h2>🚀 Next Session Goals</h2>
                    <div class="feedback-item">
            """
            
            # Generate personalized goals
            if avg_overall < 70:
                report_html += "• Focus on fundamental form improvements<br>"
            if avg_safety < 75:
                report_html += "• Pay attention to back posture and joint alignment<br>"
            if avg_depth < 80:
                report_html += "• Work on achieving better squat depth<br>"
            if avg_stability < 75:
                report_html += "• Practice balance and core stability<br>"
            if avg_tempo > 4.0:
                report_html += "• Try to increase tempo for more dynamic movement<br>"
            elif avg_tempo < 2.0 and avg_tempo > 0:
                report_html += "• Slow down for better control and form<br>"
            
            report_html += """
                        • Aim to complete more reps with consistent form<br>
                        • Review feedback tips and implement gradually
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Show in dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Session Report")
            dialog.setGeometry(200, 200, 800, 600)
            dialog.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1e1e1e, stop:1 #2d2d2d);
                }
            """)
            
            layout = QVBoxLayout()
            
            # Report display
            report_display = QTextEdit()
            report_display.setHtml(report_html)
            report_display.setReadOnly(True)
            report_display.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    border: none;
                    border-radius: 10px;
                }
            """)
            
            # Buttons
            button_layout = QHBoxLayout()
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            close_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #388E3C);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #66BB6A, stop:1 #4CAF50);
                }
            """)
            
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            
            layout.addWidget(report_display)
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            
            dialog.exec()
            
        except Exception as e:
            print(f"Error showing enhanced session report: {e}")
            # Fallback to basic message
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Session Complete", 
                f"Session completed with {int(self.rep_label.text()) if self.rep_label.text().isdigit() else 0} reps!")

    def show_session_report(self):
        report_data = self.session_manager.get_session_summary()
        if not report_data or report_data.get('total_reps', 0) == 0:
            QMessageBox.information(self, "Session Report", "No reps were completed in the session.")
            return
        dialog = SessionReportDialog(report_data, self)
        dialog.exec()
    
    def toggle_validation_mode(self, enabled):
        try:
            self.pose_processor = PoseProcessor(
                user_profile=self.user_profile,
                enable_validation=enabled
            )
            status_text = "Validation mode enabled" if enabled else "Validation mode disabled"
            self.status_bar.showMessage(status_text, 3000)
        except Exception as e:
            print(f"Error toggling validation mode: {e}")
            self.validation_action.setChecked(not enabled)
    
    def closeEvent(self, event):
        self.stop_session()
        self.config_manager.save_ui_settings({'window_width': self.width(), 'window_height': self.height()})
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())