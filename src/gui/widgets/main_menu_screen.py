"""
Main Menu Screen - Navigation hub after user profile creation
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

class ClickableMenuButton(QWidget):
    """Custom clickable button widget with title and subtitle"""
    clicked = Signal()

    def __init__(self, title, subtitle, color, hover_color, parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.color = color
        self.hover_color = hover_color
        self.setFixedSize(350, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()

    def setup_ui(self):
        """Setup the button UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(2)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title label
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background: transparent;")
        
        # Subtitle label
        subtitle_label = QLabel(self.subtitle)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Segoe UI", 11)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background: transparent;")
        
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        
        # Set initial style
        self.setStyleSheet(f"""
            ClickableMenuButton {{
                background-color: {self.color};
                border: none;
                border-radius: 15px;
            }}
        """)

    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter (hover)"""
        self.setStyleSheet(f"""
            ClickableMenuButton {{
                background-color: {self.hover_color};
                border: none;
                border-radius: 15px;
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.setStyleSheet(f"""
            ClickableMenuButton {{
                background-color: {self.color};
                border: none;
                border-radius: 15px;
            }}
        """)
        super().leaveEvent(event)

class MainMenuScreen(QWidget):
    """Main menu with navigation options"""
    start_analysis = Signal()
    show_guide = Signal()
    exit_app = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MainMenuScreen")
        self.user_name = "User"
        self.setup_ui()

    def setup_ui(self):
        """Setup the main menu UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(25)

        # Welcome message
        self.welcome_label = QLabel("Welcome, User!")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = QFont("Arial", 32, QFont.Weight.Bold)
        self.welcome_label.setFont(welcome_font)
        self.welcome_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                margin: 20px;
                font-weight: bold;
            }
        """)

        # Subtitle
        subtitle = QLabel("Choose your next action")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Arial", 16)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("""
            QLabel {
                color: #B0B0B0;
                margin-bottom: 30px;
            }
        """)

        # Create menu buttons
        self.start_button = ClickableMenuButton(
            "🎯 START ANALYSIS", 
            "Begin your workout session",
            "#4CAF50", "#45A049"
        )
        
        self.guide_button = ClickableMenuButton(
            "📖 SQUAT GUIDE", 
            "Learn proper squat technique",
            "#2196F3", "#1976D2"
        )
        
        self.exit_button = ClickableMenuButton(
            "🚪 EXIT", 
            "Close the application",
            "#f44336", "#d32f2f"
        )

        # Connect signals
        self.start_button.clicked.connect(self.start_analysis.emit)
        self.guide_button.clicked.connect(self.show_guide.emit)
        self.exit_button.clicked.connect(self.exit_app.emit)

        # Layout assembly
        layout.addStretch(2)
        layout.addWidget(self.welcome_label)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(15)
        layout.addWidget(self.guide_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(15)
        layout.addWidget(self.exit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(3)

        # Main background
        self.setStyleSheet("""
            MainMenuScreen {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a1a, stop:0.5 #2d2d30, stop:1 #1a1a1a);
            }
        """)

    def set_user_name(self, name):
        """Update the welcome message with user's name"""
        self.user_name = name
        self.welcome_label.setText(f"Welcome, {name}!")

    def set_user_profile(self, profile):
        """Update display with full user profile"""
        self.set_user_name(profile.get('name', 'User'))
        # Could add more profile-based customization here
