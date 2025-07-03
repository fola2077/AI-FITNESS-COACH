from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
                               QGroupBox, QFormLayout, QSlider, QComboBox)
from PySide6.QtCore import Qt, Signal

class SettingsDialog(QDialog):
    """Settings dialog for configuring analysis parameters"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Settings")
        self.setModal(True)
        self.resize(400, 500)
        
        self.setup_ui()
        self.load_default_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Detection settings
        detection_group = QGroupBox("Pose Detection")
        detection_layout = QFormLayout(detection_group)
        
        self.confidence_threshold = QDoubleSpinBox()
        self.confidence_threshold.setRange(0.1, 1.0)
        self.confidence_threshold.setSingleStep(0.1)
        self.confidence_threshold.setDecimals(1)
        detection_layout.addRow("Confidence Threshold:", self.confidence_threshold)
        
        layout.addWidget(detection_group)
        
        # Form analysis settings
        form_group = QGroupBox("Form Analysis")
        form_layout = QFormLayout(form_group)
        
        self.back_angle_threshold = QSpinBox()
        self.back_angle_threshold.setRange(10, 45)
        self.back_angle_threshold.setSuffix("°")
        form_layout.addRow("Back Rounding Threshold:", self.back_angle_threshold)
        
        self.knee_depth_threshold = QSpinBox()
        self.knee_depth_threshold.setRange(70, 120)
        self.knee_depth_threshold.setSuffix("°")
        form_layout.addRow("Knee Depth Threshold:", self.knee_depth_threshold)
        
        self.symmetry_threshold = QSpinBox()
        self.symmetry_threshold.setRange(5, 30)
        self.symmetry_threshold.setSuffix("°")
        form_layout.addRow("Symmetry Threshold:", self.symmetry_threshold)
        
        layout.addWidget(form_group)
        
        # Feedback settings
        feedback_group = QGroupBox("Feedback Settings")
        feedback_layout = QFormLayout(feedback_group)
        
        self.feedback_frequency = QComboBox()
        self.feedback_frequency.addItems(["High", "Medium", "Low"])
        feedback_layout.addRow("Feedback Frequency:", self.feedback_frequency)
        
        self.show_angles = QCheckBox()
        feedback_layout.addRow("Show Joint Angles:", self.show_angles)
        
        self.show_skeleton = QCheckBox()
        feedback_layout.addRow("Show Pose Skeleton:", self.show_skeleton)
        
        layout.addWidget(feedback_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout(advanced_group)
        
        self.smoothing_frames = QSpinBox()
        self.smoothing_frames.setRange(1, 10)
        advanced_layout.addRow("Smoothing Frames:", self.smoothing_frames)
        
        self.min_frames_for_fault = QSpinBox()
        self.min_frames_for_fault.setRange(1, 10)
        advanced_layout.addRow("Min Frames for Fault:", self.min_frames_for_fault)
        
        layout.addWidget(advanced_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply")
        self.reset_button = QPushButton("Reset to Defaults")
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.apply_button.clicked.connect(self.apply_settings)
        self.reset_button.clicked.connect(self.load_default_settings)
        self.cancel_button.clicked.connect(self.reject)
        
    def load_default_settings(self):
        """Load default settings values"""
        self.confidence_threshold.setValue(0.7)
        self.back_angle_threshold.setValue(25)
        self.knee_depth_threshold.setValue(90)
        self.symmetry_threshold.setValue(15)
        self.feedback_frequency.setCurrentText("Medium")
        self.show_angles.setChecked(True)
        self.show_skeleton.setChecked(True)
        self.smoothing_frames.setValue(5)
        self.min_frames_for_fault.setValue(3)
        
    def apply_settings(self):
        """Apply current settings"""
        settings = {
            'confidence_threshold': self.confidence_threshold.value(),
            'back_angle_threshold': self.back_angle_threshold.value(),
            'knee_depth_threshold': self.knee_depth_threshold.value(),
            'symmetry_threshold': self.symmetry_threshold.value(),
            'feedback_frequency': self.feedback_frequency.currentText(),
            'show_angles': self.show_angles.isChecked(),
            'show_skeleton': self.show_skeleton.isChecked(),
            'smoothing_frames': self.smoothing_frames.value(),
            'min_frames_for_fault': self.min_frames_for_fault.value()
        }
        
        self.settings_changed.emit(settings)
        self.accept()
        
    def get_settings(self):
        """Get current settings as dictionary"""
        return {
            'confidence_threshold': self.confidence_threshold.value(),
            'back_angle_threshold': self.back_angle_threshold.value(),
            'knee_depth_threshold': self.knee_depth_threshold.value(),
            'symmetry_threshold': self.symmetry_threshold.value(),
            'feedback_frequency': self.feedback_frequency.currentText(),
            'show_angles': self.show_angles.isChecked(),
            'show_skeleton': self.show_skeleton.isChecked(),
            'smoothing_frames': self.smoothing_frames.value(),
            'min_frames_for_fault': self.min_frames_for_fault.value()
        }
