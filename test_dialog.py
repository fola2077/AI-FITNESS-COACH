#!/usr/bin/env python3
"""
Quick test script to verify the user profile dialog visibility
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from src.gui.widgets.user_profile_dialog import UserProfileDialog

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Test button
        test_button = QPushButton("Test User Profile Dialog")
        test_button.clicked.connect(self.show_dialog)
        test_button.setStyleSheet("""
            QPushButton {
                padding: 15px;
                font-size: 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        
        layout.addWidget(test_button)
        
        # Dark theme for test window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d30;
            }
        """)
    
    def show_dialog(self):
        dialog = UserProfileDialog(self)
        result = dialog.exec()
        
        if result == 1:  # Accepted
            user_data = dialog.get_user_data()
            print("User data collected:")
            print(f"  Name: {user_data.get('name', 'N/A')}")
            print(f"  Gender: {user_data.get('gender', 'N/A')}")
            print(f"  Fitness Level: {user_data.get('fitness_level', 'N/A')}")
        else:
            print("Dialog was cancelled")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set dark style for the entire application
    app.setStyleSheet("""
        QApplication {
            background-color: #2d2d30;
        }
    """)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())
