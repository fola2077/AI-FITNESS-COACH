"""
Welcome Screen Widget - First screen users see when opening the AI Fitness Coach
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QLinearGradient, QColor

class WelcomeScreen(QWidget):
    """A professional welcome screen with AI Fitness Coach branding"""
    start_pressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomeScreen")
        self.setup_ui()

    def setup_ui(self):
        """Setup the welcome screen UI components"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)

        # Main title
        title = QLabel("AI FITNESS COACH")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Arial", 48, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                margin: 20px;
                font-weight: bold;
            }
        """)

        # Subtitle
        subtitle = QLabel("Your Personal Form Analyzer & Trainer")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Arial", 20, QFont.Weight.Normal)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("""
            QLabel {
                color: #B0B0B0;
                margin: 10px;
            }
        """)

        # Feature highlights
        features = QLabel("🎯 Real-time pose analysis  •  📊 Intelligent feedback  •  📈 Progress tracking")
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_font = QFont("Arial", 14)
        features.setFont(features_font)
        features.setStyleSheet("""
            QLabel {
                color: #808080;
                margin: 20px;
            }
        """)

        # Start button
        self.start_button = QPushButton("GET STARTED")
        self.start_button.setFixedSize(250, 60)
        start_font = QFont("Arial", 16, QFont.Weight.Bold)
        self.start_button.setFont(start_font)
        self.start_button.setStyleSheet("""
            QPushButton {
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45A049);
                border: none;
                border-radius: 30px;
                padding: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45A049, stop:1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d8b40, stop:1 #2e7d32);
            }
        """)
        self.start_button.clicked.connect(self.start_pressed.emit)

        # Layout assembly
        layout.addStretch(2)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(features)
        layout.addSpacing(40)
        layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(3)

        # Main background styling
        self.setStyleSheet("""
            WelcomeScreen {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a1a, stop:0.5 #2d2d30, stop:1 #1a1a1a);
            }
        """)

    def paintEvent(self, event):
        """Custom paint event for gradient background"""
        super().paintEvent(event)
