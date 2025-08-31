#!/usr/bin/env python3
"""
Test the compact session dashboard layout
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer

from src.gui.main_window import MainWindow

def test_compact_layout():
    """Test the new compact layout"""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    
    # Navigate to analysis screen
    window.stacked_widget.setCurrentIndex(3)  # Analysis widget
    
    # Show window
    window.show()
    window.resize(1400, 800)
    
    print("✅ Compact Layout Test")
    print("📊 Check that session dashboard is now compact and on the left")
    print("🎥 Video should be below the compact dashboard on the left side")
    print("📈 Analytics panel should be on the right without the large dashboard")
    print("🔄 Try the reset button in the compact dashboard")
    
    # Auto-close after a few seconds for testing
    QTimer.singleShot(8000, app.quit)
    
    app.exec()

if __name__ == "__main__":
    test_compact_layout()
