from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QScrollArea, QWidget,
                               QGridLayout, QProgressBar, QFrame, QSplitter,
                               QTabWidget)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette
import time
import json

class SessionReportDialog(QDialog):
    """Comprehensive session report and analytics"""
    
    def __init__(self, session_data, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.setWindowTitle("Session Report & Analytics")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.populate_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Summary tab
        self.create_summary_tab()
        
        # Detailed analysis tab
        self.create_analysis_tab()
        
        # Feedback history tab
        self.create_feedback_tab()
        
        # Export tab
        self.create_export_tab()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
    def create_summary_tab(self):
        """Create the summary overview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header with session info
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_layout = QGridLayout(header_frame)
        
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        
        title_label = QLabel("Session Summary")
        title_label.setFont(title_font)
        header_layout.addWidget(title_label, 0, 0, 1, 2)
        
        # Session stats grid
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        
        self.total_reps_label = QLabel("0")
        self.session_duration_label = QLabel("0:00")
        self.avg_form_score_label = QLabel("--")
        self.best_form_score_label = QLabel("--")
        self.total_feedback_label = QLabel("0")
        
        # Style the stat values
        stat_font = QFont()
        stat_font.setPointSize(18)
        stat_font.setBold(True)
        
        for label in [self.total_reps_label, self.session_duration_label, 
                     self.avg_form_score_label, self.best_form_score_label,
                     self.total_feedback_label]:
            label.setFont(stat_font)
            label.setAlignment(Qt.AlignCenter)
        
        stats_layout.addWidget(QLabel("Total Repetitions:"), 0, 0)
        stats_layout.addWidget(self.total_reps_label, 1, 0)
        
        stats_layout.addWidget(QLabel("Session Duration:"), 0, 1)
        stats_layout.addWidget(self.session_duration_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Average Form Score:"), 0, 2)
        stats_layout.addWidget(self.avg_form_score_label, 1, 2)
        
        stats_layout.addWidget(QLabel("Best Form Score:"), 2, 0)
        stats_layout.addWidget(self.best_form_score_label, 3, 0)
        
        stats_layout.addWidget(QLabel("Feedback Messages:"), 2, 1)
        stats_layout.addWidget(self.total_feedback_label, 3, 1)
        
        layout.addWidget(header_frame)
        layout.addWidget(stats_widget)
        
        # Performance trends
        trends_frame = QFrame()
        trends_frame.setFrameStyle(QFrame.Box)
        trends_layout = QVBoxLayout(trends_frame)
        
        trends_label = QLabel("Performance Analysis")
        trends_label.setFont(title_font)
        trends_layout.addWidget(trends_label)
        
        self.performance_text = QTextEdit()
        self.performance_text.setMaximumHeight(200)
        self.performance_text.setReadOnly(True)
        trends_layout.addWidget(self.performance_text)
        
        layout.addWidget(trends_frame)
        
        self.tab_widget.addTab(tab, "Summary")
        
    def create_analysis_tab(self):
        """Create detailed form analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Fault frequency analysis
        faults_frame = QFrame()
        faults_frame.setFrameStyle(QFrame.Box)
        faults_layout = QVBoxLayout(faults_frame)
        
        faults_label = QLabel("Common Form Issues")
        faults_label.setFont(QFont("Arial", 14, QFont.Bold))
        faults_layout.addWidget(faults_label)
        
        self.faults_widget = QWidget()
        self.faults_layout = QVBoxLayout(self.faults_widget)
        faults_layout.addWidget(self.faults_widget)
        
        layout.addWidget(faults_frame)
        
        # Movement quality metrics
        quality_frame = QFrame()
        quality_frame.setFrameStyle(QFrame.Box)
        quality_layout = QVBoxLayout(quality_frame)
        
        quality_label = QLabel("Movement Quality Metrics")
        quality_label.setFont(QFont("Arial", 14, QFont.Bold))
        quality_layout.addWidget(quality_label)
        
        self.quality_text = QTextEdit()
        self.quality_text.setReadOnly(True)
        quality_layout.addWidget(self.quality_text)
        
        layout.addWidget(quality_frame)
        
        self.tab_widget.addTab(tab, "Analysis")
        
    def create_feedback_tab(self):
        """Create feedback history tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        feedback_label = QLabel("Feedback History")
        feedback_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(feedback_label)
        
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        layout.addWidget(self.feedback_text)
        
        self.tab_widget.addTab(tab, "Feedback History")
        
    def create_export_tab(self):
        """Create data export tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        export_label = QLabel("Export Session Data")
        export_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(export_label)
        
        # Export options
        export_buttons_layout = QHBoxLayout()
        
        self.export_json_button = QPushButton("Export as JSON")
        self.export_csv_button = QPushButton("Export as CSV")
        self.export_report_button = QPushButton("Export Full Report")
        
        export_buttons_layout.addWidget(self.export_json_button)
        export_buttons_layout.addWidget(self.export_csv_button)
        export_buttons_layout.addWidget(self.export_report_button)
        
        layout.addLayout(export_buttons_layout)
        
        # Preview area
        preview_label = QLabel("Data Preview:")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Connect export buttons
        self.export_json_button.clicked.connect(self.export_json)
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_report_button.clicked.connect(self.export_report)
        
        self.tab_widget.addTab(tab, "Export")
        
    def populate_data(self):
        """Populate the dialog with session data"""
        if not self.session_data:
            return
            
        # Summary tab
        self.total_reps_label.setText(str(self.session_data.get('total_reps', 0)))
        
        duration = self.session_data.get('duration', 0)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
        self.session_duration_label.setText(duration_str)
        
        avg_score = self.session_data.get('avg_form_score', 0)
        self.avg_form_score_label.setText(f"{avg_score:.1f}%")
        
        best_score = self.session_data.get('best_form_score', 0)
        self.best_form_score_label.setText(f"{best_score}%")
        
        feedback_count = len(self.session_data.get('feedback_history', []))
        self.total_feedback_label.setText(str(feedback_count))
        
        # Performance analysis
        self.analyze_performance()
        
        # Fault analysis
        self.analyze_faults()
        
        # Feedback history
        self.populate_feedback_history()
        
        # Export preview
        self.update_export_preview()
        
    def analyze_performance(self):
        """Analyze performance trends and provide insights"""
        analysis = []
        
        total_reps = self.session_data.get('total_reps', 0)
        avg_score = self.session_data.get('avg_form_score', 0)
        best_score = self.session_data.get('best_form_score', 0)
        
        # Performance assessment
        if avg_score >= 90:
            analysis.append("🌟 Excellent overall form quality! You maintained great technique throughout the session.")
        elif avg_score >= 80:
            analysis.append("👍 Good form quality with room for minor improvements.")
        elif avg_score >= 70:
            analysis.append("⚠️ Moderate form quality. Focus on the feedback to improve technique.")
        else:
            analysis.append("📚 Form needs improvement. Consider reviewing proper squat technique.")
        
        # Rep analysis
        if total_reps >= 20:
            analysis.append(f"💪 Great workout volume with {total_reps} repetitions!")
        elif total_reps >= 10:
            analysis.append(f"✅ Good workout with {total_reps} repetitions.")
        elif total_reps > 0:
            analysis.append(f"👶 Getting started with {total_reps} repetitions. Keep building!")
        
        # Consistency analysis
        score_range = best_score - (avg_score - 10)  # Rough estimate of consistency
        if score_range <= 15:
            analysis.append("🎯 Consistent form throughout the session.")
        else:
            analysis.append("📈 Form varied during the session - focus on maintaining consistent technique.")
        
        self.performance_text.setPlainText('\n\n'.join(analysis))
        
    def analyze_faults(self):
        """Analyze common faults and create visual representation"""
        faults_data = self.session_data.get('fault_frequency', {})
        
        # Clear existing widgets
        for i in reversed(range(self.faults_layout.count())): 
            self.faults_layout.itemAt(i).widget().setParent(None)
        
        if not faults_data:
            no_faults_label = QLabel("No significant form issues detected! 🎉")
            no_faults_label.setAlignment(Qt.AlignCenter)
            self.faults_layout.addWidget(no_faults_label)
            return
        
        # Create progress bars for each fault type
        fault_descriptions = {
            'BACK_ROUNDING': 'Back Rounding',
            'KNEE_VALGUS': 'Knee Valgus (knees caving in)',
            'INSUFFICIENT_DEPTH': 'Insufficient Depth',
            'FORWARD_LEAN': 'Forward Lean',
            'ASYMMETRIC_MOVEMENT': 'Asymmetric Movement',
            'HEEL_RISE': 'Heel Rise'
        }
        
        for fault, count in faults_data.items():
            if count > 0:
                fault_widget = QWidget()
                fault_layout = QHBoxLayout(fault_widget)
                
                fault_label = QLabel(fault_descriptions.get(fault, fault))
                fault_label.setMinimumWidth(200)
                
                fault_bar = QProgressBar()
                fault_bar.setMaximum(max(faults_data.values()))
                fault_bar.setValue(count)
                fault_bar.setFormat(f"{count} occurrences")
                
                fault_layout.addWidget(fault_label)
                fault_layout.addWidget(fault_bar)
                
                self.faults_layout.addWidget(fault_widget)
        
    def populate_feedback_history(self):
        """Populate feedback history tab"""
        feedback_history = self.session_data.get('feedback_history', [])
        
        if not feedback_history:
            self.feedback_text.setPlainText("No feedback recorded during this session.")
            return
        
        feedback_text = []
        for feedback in feedback_history:
            timestamp = feedback.get('timestamp', 'Unknown')
            message = feedback.get('message', '')
            category = feedback.get('category', 'general')
            
            category_icon = {
                'safety': '⚠️',
                'form': '💡',
                'encouragement': '👍',
                'general': '📋'
            }.get(category, '📋')
            
            feedback_text.append(f"[{timestamp}] {category_icon} {message}")
        
        self.feedback_text.setPlainText('\n'.join(feedback_text))
        
    def update_export_preview(self):
        """Update the export preview"""
        preview_data = {
            'session_summary': {
                'total_reps': self.session_data.get('total_reps', 0),
                'duration': self.session_data.get('duration', 0),
                'avg_form_score': self.session_data.get('avg_form_score', 0),
                'best_form_score': self.session_data.get('best_form_score', 0)
            },
            'feedback_count': len(self.session_data.get('feedback_history', [])),
            'fault_frequency': self.session_data.get('fault_frequency', {})
        }
        
        preview_json = json.dumps(preview_data, indent=2)
        self.preview_text.setPlainText(preview_json)
        
    def export_json(self):
        """Export session data as JSON"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Session Data", "session_data.json", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.session_data, f, indent=2)
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export data: {str(e)}")
        
    def export_csv(self):
        """Export session data as CSV"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import csv
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Session Data", "session_data.csv", "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write headers and session summary
                    writer.writerow(['Metric', 'Value'])
                    writer.writerow(['Total Reps', self.session_data.get('total_reps', 0)])
                    writer.writerow(['Duration (seconds)', self.session_data.get('duration', 0)])
                    writer.writerow(['Average Form Score', self.session_data.get('avg_form_score', 0)])
                    writer.writerow(['Best Form Score', self.session_data.get('best_form_score', 0)])
                    writer.writerow([])
                    
                    # Write feedback history
                    writer.writerow(['Timestamp', 'Category', 'Message'])
                    for feedback in self.session_data.get('feedback_history', []):
                        writer.writerow([
                            feedback.get('timestamp', ''),
                            feedback.get('category', ''),
                            feedback.get('message', '')
                        ])
                        
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export data: {str(e)}")
        
    def export_report(self):
        """Export a comprehensive text report"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Session Report", "session_report.txt", "Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("AI FITNESS COACH - SESSION REPORT\n")
                    f.write("=" * 40 + "\n\n")
                    
                    # Session summary
                    f.write("SESSION SUMMARY:\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"Total Repetitions: {self.session_data.get('total_reps', 0)}\n")
                    duration = self.session_data.get('duration', 0)
                    f.write(f"Duration: {int(duration // 60)}:{int(duration % 60):02d}\n")
                    f.write(f"Average Form Score: {self.session_data.get('avg_form_score', 0):.1f}%\n")
                    f.write(f"Best Form Score: {self.session_data.get('best_form_score', 0)}%\n\n")
                    
                    # Performance analysis
                    f.write("PERFORMANCE ANALYSIS:\n")
                    f.write("-" * 25 + "\n")
                    f.write(self.performance_text.toPlainText() + "\n\n")
                    
                    # Feedback history
                    f.write("FEEDBACK HISTORY:\n")
                    f.write("-" * 20 + "\n")
                    f.write(self.feedback_text.toPlainText() + "\n")
                    
                QMessageBox.information(self, "Success", f"Report exported to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export report: {str(e)}")


class SessionManager:
    """Manages session data collection and analysis"""
    
    def __init__(self):
        self.reset_session()
        
    def reset_session(self):
        """Reset session data"""
        self.session_data = {
            'start_time': None,
            'end_time': None,
            'total_reps': 0,
            'form_scores': [],
            'feedback_history': [],
            'fault_frequency': {},
            'phase_transitions': []
        }
        
    def start_session(self):
        """Start a new session"""
        self.session_data['start_time'] = time.time()
        
    def end_session(self):
        """End the current session"""
        self.session_data['end_time'] = time.time()
        
    def update_session(self, rep_count, form_score, feedback_history, fault_data=None):
        """Update session with current data"""
        self.session_data['total_reps'] = rep_count
        
        if form_score is not None:
            self.session_data['form_scores'].append(form_score)
            
        # Update feedback history
        if feedback_history:
            for feedback in feedback_history:
                if feedback not in self.session_data['feedback_history']:
                    self.session_data['feedback_history'].append(feedback)
        
        # Update fault frequency
        if fault_data:
            for fault in fault_data:
                self.session_data['fault_frequency'][fault] = \
                    self.session_data['fault_frequency'].get(fault, 0) + 1
    
    def get_session_summary(self):
        """Get session summary for reporting"""
        duration = 0
        if self.session_data['start_time'] and self.session_data['end_time']:
            duration = self.session_data['end_time'] - self.session_data['start_time']
        elif self.session_data['start_time']:
            duration = time.time() - self.session_data['start_time']
            
        avg_form_score = 0
        best_form_score = 0
        if self.session_data['form_scores']:
            avg_form_score = sum(self.session_data['form_scores']) / len(self.session_data['form_scores'])
            best_form_score = max(self.session_data['form_scores'])
            
        return {
            **self.session_data,
            'duration': duration,
            'avg_form_score': avg_form_score,
            'best_form_score': best_form_score
        }
