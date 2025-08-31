#!/usr/bin/env python3
"""
Test the compact performance chart with simulated data
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
import random

from src.gui.main_window import MainWindow

def test_chart_functionality():
    """Test the new chart-only compact dashboard with simulated rep data"""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    
    # Navigate to analysis screen
    window.stacked_widget.setCurrentIndex(3)  # Analysis widget
    
    # Show window
    window.show()
    window.resize(1400, 800)
    
    print("✅ Chart-Only Dashboard Test")
    print("📊 The compact dashboard now shows a real-time performance chart")
    print("📈 Chart will display form scores for each rep")
    print("🔄 Reset button is now a circular icon on the right")
    print("\n🎯 Simulating rep data in 3 seconds...")
    
    # Simulate rep data after a short delay
    def simulate_reps():
        """Simulate several reps with varying scores"""
        chart = window.compact_chart
        
        # Simulate 8 reps with random scores
        for i in range(1, 9):
            score = random.uniform(60, 95)  # Random scores between 60-95%
            chart.add_rep_score(i, score)
            print(f"Rep {i}: {score:.1f}% form score")
        
        print("\n📊 Chart should now show the performance trend!")
        print("🔄 Try clicking the reset button to clear the chart")
    
    # Start simulation after 3 seconds
    QTimer.singleShot(3000, simulate_reps)
    
    # Auto-close after showing the chart
    QTimer.singleShot(15000, app.quit)
    
    app.exec()

if __name__ == "__main__":
    test_chart_functionality()
