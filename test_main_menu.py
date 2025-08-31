#!/usr/bin/env python3
"""
Test script for main menu screen
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from src.gui.widgets.main_menu_screen import MainMenuScreen
    
    def test_main_menu():
        """Test the main menu screen"""
        app = QApplication(sys.argv)
        
        # Create main menu
        menu = MainMenuScreen()
        menu.set_user_name("Test User")
        menu.show()
        
        # Center on screen
        screen = app.primaryScreen().geometry()
        menu.move(
            (screen.width() - menu.width()) // 2,
            (screen.height() - menu.height()) // 2
        )
        
        print("✅ Main menu displayed successfully!")
        print("  Check that buttons show:")
        print("  - 🎯 START ANALYSIS")
        print("  - 📖 SQUAT GUIDE") 
        print("  - 🚪 EXIT")
        print("  (without any HTML code)")
        
        return app.exec()

    if __name__ == '__main__':
        test_main_menu()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure PySide6 is installed: pip install PySide6")
except Exception as e:
    print(f"❌ Error: {e}")
