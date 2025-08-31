#!/usr/bin/env python3
"""
Test countdown timer and session dashboard features
"""

import sys
import time
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QTimer
from src.gui.widgets.session_dashboard import SessionDashboard


def test_session_dashboard():
    """Test the session dashboard widget"""
    print("🧪 Testing Session Dashboard...")
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QMainWindow()
    window.setWindowTitle("Session Dashboard Test")
    window.setGeometry(100, 100, 600, 700)
    
    # Create dashboard
    dashboard = SessionDashboard()
    
    # Create test controls
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Test buttons
    add_rep_btn = QPushButton("Add Test Rep (Score: 85)")
    add_good_rep_btn = QPushButton("Add Good Rep (Score: 92)")
    add_poor_rep_btn = QPushButton("Add Poor Rep (Score: 65)")
    
    # Test counters
    rep_count = 0
    
    def add_test_rep(score):
        nonlocal rep_count
        rep_count += 1
        dashboard.update_session_data(rep_count, score, "Standing")
        print(f"Added rep {rep_count} with score {score}")
    
    add_rep_btn.clicked.connect(lambda: add_test_rep(85))
    add_good_rep_btn.clicked.connect(lambda: add_test_rep(92))
    add_poor_rep_btn.clicked.connect(lambda: add_test_rep(65))
    
    layout.addWidget(add_rep_btn)
    layout.addWidget(add_good_rep_btn)
    layout.addWidget(add_poor_rep_btn)
    layout.addWidget(dashboard)
    
    window.setCentralWidget(central_widget)
    window.show()
    
    # Auto-test sequence
    test_timer = QTimer()
    test_step = 0
    test_scores = [78, 85, 92, 88, 95, 72, 89, 91]
    
    def auto_test():
        nonlocal test_step, rep_count
        if test_step < len(test_scores):
            rep_count += 1
            score = test_scores[test_step]
            dashboard.update_session_data(rep_count, score, "Standing")
            print(f"Auto-test: Rep {rep_count}, Score {score}")
            test_step += 1
        else:
            test_timer.stop()
            print("✅ Auto-test complete!")
    
    test_timer.timeout.connect(auto_test)
    test_timer.start(1000)  # Add a rep every second
    
    print("✅ Session Dashboard test window launched")
    print("🎯 Dashboard should show real-time updates")
    print("📊 Chart should display score trends")
    print("💾 Export button should create session summary")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_session_dashboard()
