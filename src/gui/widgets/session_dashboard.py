#!/usr/bin/env python3
"""
Session Dashboard Widget - Real-time visual dashboard for session progress
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient


class StatCardWidget(QFrame):
    """Modern stat card with icon and value"""
    def __init__(self, title, icon, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.value = "0"
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the stat card UI"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a, stop:1 #1e1e1e);
                border: 1px solid #444;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        self.setFixedHeight(80)
        self.setMinimumWidth(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        
        # Icon and title row
        top_layout = QHBoxLayout()
        
        self.icon_label = QLabel(self.icon)
        self.icon_label.setStyleSheet("font-size: 16px; color: #4CAF50;")
        
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-size: 11px; color: #ccc; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignRight)
        
        top_layout.addWidget(self.icon_label)
        top_layout.addStretch()
        top_layout.addWidget(self.title_label)
        
        # Value label
        self.value_label = QLabel(self.value)
        self.value_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: white;
            margin-top: 5px;
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(top_layout)
        layout.addWidget(self.value_label)
    
    def update_value(self, value):
        """Update the displayed value"""
        self.value = str(value)
        self.value_label.setText(self.value)


class SimpleChartWidget(QWidget):
    """Simple line chart widget for score trends"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.data_points = []
        self.max_points = 10
        self.setMinimumHeight(120)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a, stop:1 #1e1e1e);
                border: 1px solid #444;
                border-radius: 8px;
                margin: 2px;
            }
        """)
    
    def add_data_point(self, value):
        """Add a new data point"""
        self.data_points.append(float(value))
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()
    
    def paintEvent(self, event):
        """Draw the simple line chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        
        # Draw title
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(10, 20, self.title)
        
        if len(self.data_points) < 2:
            painter.setPen(QColor("#666"))
            painter.drawText(self.width()//2 - 50, self.height()//2, "No data yet...")
            return
        
        # Calculate chart area
        margin = 20
        chart_width = self.width() - 2 * margin
        chart_height = self.height() - 40
        chart_top = 30
        
        # Find min/max for scaling
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        if max_val == min_val:
            max_val = min_val + 1
        
        # Draw grid lines
        painter.setPen(QPen(QColor("#333"), 1))
        for i in range(5):
            y = chart_top + (i * chart_height // 4)
            painter.drawLine(margin, y, self.width() - margin, y)
        
        # Draw line chart
        painter.setPen(QPen(QColor("#4CAF50"), 2))
        
        for i in range(len(self.data_points) - 1):
            x1 = margin + (i * chart_width // (self.max_points - 1))
            x2 = margin + ((i + 1) * chart_width // (self.max_points - 1))
            
            # Scale y values
            y1 = chart_top + chart_height - int(((self.data_points[i] - min_val) / (max_val - min_val)) * chart_height)
            y2 = chart_top + chart_height - int(((self.data_points[i + 1] - min_val) / (max_val - min_val)) * chart_height)
            
            painter.drawLine(x1, y1, x2, y2)
            
            # Draw points
            painter.setBrush(QBrush(QColor("#4CAF50")))
            painter.drawEllipse(x1 - 3, y1 - 3, 6, 6)
            
        # Draw last point
        if self.data_points:
            last_x = margin + ((len(self.data_points) - 1) * chart_width // (self.max_points - 1))
            last_y = chart_top + chart_height - int(((self.data_points[-1] - min_val) / (max_val - min_val)) * chart_height)
            painter.drawEllipse(last_x - 3, last_y - 3, 6, 6)


class SessionDashboard(QWidget):
    """Real-time session dashboard with stats and visualizations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.reset_session()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel("📊 Session Dashboard")
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #4CAF50;
            margin-bottom: 5px;
        """)
        layout.addWidget(title_label)
        
        # Stats cards row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(5)
        
        self.total_reps_card = StatCardWidget("Total Reps", "🏋️", self)
        self.avg_score_card = StatCardWidget("Avg Score", "⭐", self)
        self.best_rep_card = StatCardWidget("Best Rep", "🎯", self)
        
        stats_layout.addWidget(self.total_reps_card)
        stats_layout.addWidget(self.avg_score_card)
        stats_layout.addWidget(self.best_rep_card)
        
        layout.addLayout(stats_layout)
        
        # Form score trend chart
        self.score_chart = SimpleChartWidget("Form Score Trend", self)
        layout.addWidget(self.score_chart)
        
        # Session controls
        controls_layout = QHBoxLayout()
        
        self.export_session_btn = QPushButton("📄 Export Session")
        self.export_session_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
        """)
        
        self.reset_session_btn = QPushButton("🔄 Reset")
        self.reset_session_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF9800, stop:1 #F57C00);
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB74D, stop:1 #FF9800);
            }
        """)
        
        controls_layout.addWidget(self.export_session_btn)
        controls_layout.addWidget(self.reset_session_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Connect signals
        self.reset_session_btn.clicked.connect(self.reset_session)
        self.export_session_btn.clicked.connect(self.export_session_data)
    
    def reset_session(self):
        """Reset session data"""
        self.rep_scores = []
        self.total_reps = 0
        self.best_score = 0
        
        self.total_reps_card.update_value(0)
        self.avg_score_card.update_value("--")
        self.best_rep_card.update_value(0)
        
        self.score_chart.data_points.clear()
        self.score_chart.update()
    
    def update_session_data(self, rep_count, form_score=None, phase="Ready"):
        """Update session with new data"""
        # Update rep count
        if rep_count != self.total_reps:
            self.total_reps = rep_count
            self.total_reps_card.update_value(self.total_reps)
            
            # Add form score to tracking
            if form_score is not None and form_score > 0:
                self.rep_scores.append(form_score)
                self.score_chart.add_data_point(form_score)
                
                # Update best score
                if form_score > self.best_score:
                    self.best_score = form_score
                    self.best_rep_card.update_value(int(self.best_score))
                
                # Update average score
                if self.rep_scores:
                    avg_score = sum(self.rep_scores) / len(self.rep_scores)
                    self.avg_score_card.update_value(f"{avg_score:.1f}")
    
    def get_session_summary(self):
        """Get current session summary"""
        return {
            'total_reps': self.total_reps,
            'rep_scores': self.rep_scores.copy(),
            'avg_score': sum(self.rep_scores) / len(self.rep_scores) if self.rep_scores else 0,
            'best_score': self.best_score,
            'worst_score': min(self.rep_scores) if self.rep_scores else 0,
            'consistency': self._calculate_consistency()
        }
    
    def _calculate_consistency(self):
        """Calculate consistency score based on score variance"""
        if len(self.rep_scores) < 2:
            return 100
        
        avg = sum(self.rep_scores) / len(self.rep_scores)
        variance = sum((score - avg) ** 2 for score in self.rep_scores) / len(self.rep_scores)
        std_dev = variance ** 0.5
        
        # Convert to consistency percentage (lower std_dev = higher consistency)
        consistency = max(0, 100 - (std_dev * 2))
        return round(consistency, 1)
    
    def export_session_data(self):
        """Export session data to a simple text file"""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            import datetime
            
            if not self.rep_scores:
                QMessageBox.information(self, "No Data", "No session data to export. Complete some reps first!")
                return
            
            # Get export location
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"session_summary_{timestamp}.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Session Summary", 
                default_filename,
                "Text Files (*.txt);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Generate summary text
            summary = self.get_session_summary()
            
            export_text = f"""AI FITNESS COACH - SESSION SUMMARY
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
========================================

SESSION STATISTICS:
📊 Total Reps: {summary['total_reps']}
⭐ Average Score: {summary['avg_score']:.1f}
🎯 Best Rep: {summary['best_score']:.1f}
📉 Worst Rep: {summary['worst_score']:.1f}
🎚️ Consistency: {summary['consistency']:.1f}%

REP-BY-REP SCORES:
"""
            
            for i, score in enumerate(summary['rep_scores'], 1):
                export_text += f"Rep {i:2d}: {score:5.1f}\n"
            
            export_text += f"""
PERFORMANCE ANALYSIS:
• Improvement: {'+' if len(summary['rep_scores']) > 1 and summary['rep_scores'][-1] > summary['rep_scores'][0] else ''}{summary['rep_scores'][-1] - summary['rep_scores'][0]:.1f} points (first to last rep)
• Score Range: {summary['best_score'] - summary['worst_score']:.1f} points
• Reps Above 80: {len([s for s in summary['rep_scores'] if s >= 80])}/{len(summary['rep_scores'])}
• Reps Above 90: {len([s for s in summary['rep_scores'] if s >= 90])}/{len(summary['rep_scores'])}

RECOMMENDATIONS:
"""
            
            if summary['avg_score'] >= 85:
                export_text += "🌟 Excellent form! Focus on maintaining consistency.\n"
            elif summary['avg_score'] >= 70:
                export_text += "👍 Good form. Work on depth and stability for higher scores.\n"
            else:
                export_text += "💪 Keep practicing! Focus on the basics: depth, knee alignment, and back posture.\n"
            
            if summary['consistency'] < 70:
                export_text += "🎯 Focus on consistency - try to maintain steady form across all reps.\n"
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(export_text)
            
            QMessageBox.information(self, "Export Complete", f"Session summary exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export session data:\n{str(e)}")
            print(f"Error exporting session data: {e}")
