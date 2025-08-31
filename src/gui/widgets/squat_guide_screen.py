"""
Squat Guide Screen - Educational content for proper squat technique
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

class SquatGuideScreen(QWidget):
    """Comprehensive squat guide with technique tips"""
    back_to_menu = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SquatGuideScreen")
        self.setup_ui()

    def setup_ui(self):
        """Setup the guide screen UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Back to Menu")
        self.back_button.setFixedSize(150, 40)
        self.back_button.clicked.connect(self.back_to_menu.emit)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border: 1px solid #666666;
                border-radius: 8px;
                font-size: 14px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)

        title = QLabel("Squat Technique Guide")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Arial", 28, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                margin: 10px;
                font-weight: bold;
            }
        """)

        header_layout.addWidget(self.back_button)
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QWidget())  # Spacer for symmetry

        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #3a3a3a;
                border: none;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #606060;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #707070;
            }
        """)

        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # Add guide sections
        self.add_guide_section(content_layout, "🎯 Setup Position", [
            "• Stand with feet shoulder-width apart",
            "• Toes slightly pointed outward (15-30 degrees)",
            "• Keep your chest up and shoulders back",
            "• Engage your core muscles",
            "• Look straight ahead or slightly upward"
        ])

        self.add_guide_section(content_layout, "⬇️ The Descent", [
            "• Initiate movement by pushing hips back",
            "• Bend at hips and knees simultaneously",
            "• Keep knees aligned with your toes",
            "• Descend until thighs are parallel to floor",
            "• Maintain neutral spine throughout"
        ])

        self.add_guide_section(content_layout, "⬆️ The Ascent", [
            "• Drive through your heels",
            "• Push the floor away with your feet",
            "• Extend hips and knees together",
            "• Keep chest up and knees tracking over toes",
            "• Return to starting position with control"
        ])

        self.add_guide_section(content_layout, "⚠️ Common Mistakes", [
            "• Knees caving inward (valgus collapse)",
            "• Forward lean or rounded back",
            "• Not reaching adequate depth",
            "• Rising on toes instead of staying flat-footed",
            "• Moving too fast without control"
        ])

        self.add_guide_section(content_layout, "✅ Our AI Analysis Checks", [
            "• Depth: Ensuring proper range of motion",
            "• Knee alignment: Preventing valgus collapse",
            "• Balance: Monitoring weight distribution",
            "• Tempo: Checking movement speed",
            "• Stability: Assessing overall control"
        ])

        self.add_guide_section(content_layout, "💡 Pro Tips", [
            "• Start with bodyweight before adding weight",
            "• Focus on quality over quantity",
            "• Warm up thoroughly before squatting",
            "• Practice consistently for improvement",
            "• Listen to your body and rest when needed"
        ])

        scroll_area.setWidget(content_widget)

        # Assembly
        layout.addLayout(header_layout)
        layout.addWidget(scroll_area)

        # Main background
        self.setStyleSheet("""
            SquatGuideScreen {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a1a, stop:0.5 #2d2d30, stop:1 #1a1a1a);
            }
        """)

    def add_guide_section(self, layout, title, points):
        """Add a guide section with title and bullet points"""
        # Section frame
        section_frame = QFrame()
        section_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 48, 0.8);
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        section_layout = QVBoxLayout(section_frame)
        section_layout.setSpacing(10)

        # Section title
        title_label = QLabel(title)
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                margin-bottom: 8px;
                padding: 5px;
            }
        """)

        section_layout.addWidget(title_label)

        # Section points
        for point in points:
            point_label = QLabel(point)
            point_font = QFont("Arial", 14)
            point_label.setFont(point_font)
            point_label.setWordWrap(True)
            point_label.setStyleSheet("""
                QLabel {
                    color: #E0E0E0;
                    padding: 3px 0px;
                    line-height: 1.4;
                }
            """)
            section_layout.addWidget(point_label)

        layout.addWidget(section_frame)
