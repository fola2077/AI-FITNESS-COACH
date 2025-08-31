"""
User Profile Dialog - Modern and clean user information collection
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

class UserProfileDialog(QDialog):
    """Modern dialog to collect user profile information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Fitness Coach - Setup")
        self.setModal(True)
        self.setMinimumSize(500, 450)
        self.setMaximumSize(600, 550)
        self.user_data = {}
        self.setup_ui()
        self.setup_validation()

    def setup_ui(self):
        """Setup the modern dialog UI with improved layout"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header section with better visual hierarchy
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setStyleSheet("""
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50, stop:1 #45A049);
                border-radius: 0px;
                min-height: 120px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(40, 30, 40, 30)

        # Welcome message with better typography
        welcome_label = QLabel("👋 Welcome to AI Fitness Coach!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet("color: white; background: transparent;")

        # Improved subtitle with user benefit
        subtitle = QLabel("Let's personalize your fitness experience")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Segoe UI", 14)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); background: transparent;")

        header_layout.addWidget(welcome_label)
        header_layout.addWidget(subtitle)

        # Main content with better spacing
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("""
            QFrame#contentFrame {
                background-color: #2d2d30;
                border-radius: 0px;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(40, 35, 40, 25)

        # Name field with better UX
        name_section = self.create_improved_input_section(
            "What should we call you?", 
            "👤", 
            "This helps us personalize your experience"
        )
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name (e.g., Fola)")
        self.name_input.setStyleSheet(self.get_modern_input_style())
        self.name_input.textChanged.connect(self.validate_name)
        name_section.layout().addWidget(self.name_input)

        # Validation message for name
        self.name_error = QLabel()
        self.name_error.setStyleSheet("color: #f44336; font-size: 12px; margin-left: 25px;")
        self.name_error.hide()
        name_section.layout().addWidget(self.name_error)

        # Gender field with better options
        gender_section = self.create_improved_input_section(
            "Gender (Optional)", 
            "👥", 
            "Helps us provide more accurate recommendations"
        )
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Prefer not to say", "Male", "Female", "Non-binary", "Other"])
        self.gender_combo.setStyleSheet(self.get_modern_combo_style())
        gender_section.layout().addWidget(self.gender_combo)

        # Fitness level with detailed descriptions
        fitness_section = self.create_improved_input_section(
            "Current Fitness Level", 
            "💪", 
            "We'll adjust our analysis to match your experience"
        )
        self.fitness_combo = QComboBox()
        fitness_items = [
            "Beginner - New to exercise",
            "Casual - Exercise occasionally", 
            "Professional - Regular training",
            "Expert - Advanced athlete"
        ]
        self.fitness_combo.addItems(fitness_items)
        self.fitness_combo.setStyleSheet(self.get_modern_combo_style())
        fitness_section.layout().addWidget(self.fitness_combo)

        # Add sections to content
        content_layout.addWidget(name_section)
        content_layout.addWidget(gender_section)
        content_layout.addWidget(fitness_section)
        
        # Add flexible spacer
        content_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Improved button section
        button_frame = QFrame()
        button_frame.setStyleSheet("QFrame { background-color: #2d2d30; }")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(40, 15, 40, 35)

        # Skip button for optional setup
        self.skip_button = QPushButton("Skip Setup")
        self.skip_button.setFixedHeight(45)
        self.skip_button.clicked.connect(self.skip_setup)
        self.skip_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888888;
                border: 2px solid #555555;
                border-radius: 22px;
                font-size: 14px;
                font-weight: normal;
                padding: 0 20px;
            }
            QPushButton:hover {
                color: #CCCCCC;
                border-color: #777777;
            }
        """)

        # Main action button
        self.continue_button = QPushButton("START MY FITNESS JOURNEY")
        self.continue_button.setFixedHeight(45)
        self.continue_button.clicked.connect(self.accept_profile)
        self.continue_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45A049);
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 0.5px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45A049, stop:1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d8b40, stop:1 #2e7d32);
            }
            QPushButton:disabled {
                background: #555555;
                color: #888888;
            }
        """)

        button_layout.addWidget(self.skip_button)
        button_layout.addStretch()
        button_layout.addWidget(self.continue_button)

        # Assembly with better structure
        layout.addWidget(header_frame)
        layout.addWidget(content_frame, 1)  # Allow content to expand
        layout.addWidget(button_frame)

        # Set initial focus and tab order
        self.name_input.setFocus()
        self.setTabOrder(self.name_input, self.gender_combo)
        self.setTabOrder(self.gender_combo, self.fitness_combo)
        self.setTabOrder(self.fitness_combo, self.continue_button)

        # Enhanced dialog styling with shadow effect
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d30;
                border-radius: 12px;
            }
        """)

        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

    def create_improved_input_section(self, label_text, icon, description):
        """Create an improved input section with icon, label, and description"""
        section = QFrame()
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label row with icon
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("color: #4CAF50; font-size: 18px;")
        icon_label.setFixedWidth(30)
        
        text_label = QLabel(label_text)
        text_label.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 15px;")
        
        label_layout.addWidget(icon_label)
        label_layout.addWidget(text_label)
        label_layout.addStretch()

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #B0B0B0; font-size: 12px; margin-left: 30px;")
        desc_label.setWordWrap(True)

        layout.addLayout(label_layout)
        layout.addWidget(desc_label)
        
        return section

    def get_modern_input_style(self):
        """Enhanced input field styling"""
        return """
            QLineEdit {
                padding: 15px 18px;
                border: 2px solid #404040;
                border-radius: 10px;
                font-size: 14px;
                background-color: #3a3a3a;
                color: #FFFFFF;
                selection-background-color: #4CAF50;
                font-family: 'Segoe UI';
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: #424242;
            }
            QLineEdit::placeholder {
                color: #999999;
                font-style: italic;
            }
            QLineEdit[error="true"] {
                border-color: #f44336;
                background-color: rgba(244, 67, 54, 0.1);
            }
        """

    def get_modern_combo_style(self):
        """Enhanced combo box styling"""
        return """
            QComboBox {
                padding: 15px 18px;
                border: 2px solid #404040;
                border-radius: 10px;
                font-size: 14px;
                background-color: #3a3a3a;
                color: #FFFFFF;
                selection-background-color: #4CAF50;
                font-family: 'Segoe UI';
                min-height: 20px;
                white-space: nowrap;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background-color: #424242;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #FFFFFF;
                margin-right: 12px;
            }
            QComboBox:hover::down-arrow {
                border-top-color: #4CAF50;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                selection-background-color: #4CAF50;
                outline: none;
                border-radius: 8px;
                padding: 5px;
                min-width: 250px;
            }
            QComboBox QAbstractItemView::item {
                padding: 12px 16px;
                border-radius: 4px;
                margin: 2px;
                white-space: nowrap;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #4CAF50;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """

    def setup_validation(self):
        """Setup real-time validation"""
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.update_continue_button)

    def validate_name(self):
        """Real-time name validation with gentle feedback"""
        name = self.name_input.text().strip()
        
        # Clear previous error state
        self.name_input.setProperty("error", False)
        self.name_error.hide()
        
        if len(name) == 0:
            # Empty is okay, just disable continue
            pass
        elif len(name) < 2:
            self.show_name_error("Name should be at least 2 characters")
        elif len(name) > 50:
            self.show_name_error("Name is too long (max 50 characters)")
        elif not name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            self.show_name_error("Please use only letters, spaces, hyphens, and apostrophes")
        
        # Update continue button state
        self.validation_timer.start(300)  # Debounce validation

    def show_name_error(self, message):
        """Show gentle error feedback"""
        self.name_input.setProperty("error", True)
        self.name_input.setStyle(self.name_input.style())  # Refresh style
        self.name_error.setText(message)
        self.name_error.show()

    def update_continue_button(self):
        """Update continue button state based on validation"""
        name = self.name_input.text().strip()
        is_valid = len(name) >= 2 and len(name) <= 50 and name.replace(' ', '').replace('-', '').replace("'", '').isalpha()
        self.continue_button.setEnabled(is_valid)

    def skip_setup(self):
        """Allow users to skip profile setup"""
        self.user_data = {
            'name': 'User',
            'gender': 'Prefer not to say',
            'fitness_level': 'casual'  # Default to casual level
        }
        self.accept()

    def accept_profile(self):
        """Validate and accept the profile data"""
        name = self.name_input.text().strip()
        
        if not name or len(name) < 2:
            self.name_input.setFocus()
            self.show_name_error("Please enter your name to continue")
            return

        # Map display text to actual difficulty levels used by the grading system
        fitness_text = self.fitness_combo.currentText()
        fitness_mapping = {
            "Beginner - New to exercise": "beginner",
            "Casual - Exercise occasionally": "casual", 
            "Professional - Regular training": "professional",
            "Expert - Advanced athlete": "expert"
        }
        
        # Get the actual difficulty level for the grading system
        fitness_level = fitness_mapping.get(fitness_text, "casual")  # Default to casual

        # Store user data
        self.user_data = {
            'name': name,
            'gender': self.gender_combo.currentText(),
            'fitness_level': fitness_level
        }
        
        self.accept()

    def get_user_data(self):
        """Return the collected user data"""
        return self.user_data
