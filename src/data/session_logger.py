"""
Comprehensive Data Logging System for AI Fitness Coach

This module implements a robust CSV-based data logging system designed for:
- ML model training and evaluation
- Performance analysis and metrics tracking
- User progress monitoring
- System optimization and research

Features:
- Multiple CSV output formats for different analysis needs
- Automatic data validation and quality checks
- Configurable logging levels and data retention
- Session-based and rep-based data aggregation
- Export utilities for research and ML training
"""

import csv
import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Set up module logger
logger = logging.getLogger(__name__)

@dataclass
class LoggingConfig:
    """Configuration for data logging system"""
    # Output directories
    base_output_dir: str = "data/logs"
    session_logs_dir: str = "sessions"
    rep_logs_dir: str = "reps"
    biomech_logs_dir: str = "biomechanics"
    ml_training_dir: str = "ml_training"
    
    # File naming
    session_file_prefix: str = "session"
    rep_file_prefix: str = "rep_data"
    biomech_file_prefix: str = "biomech"
    ml_file_prefix: str = "ml_dataset"
    
    # Data retention
    max_sessions_per_file: int = 100
    max_days_retention: int = 90
    auto_cleanup: bool = True
    
    # Logging levels
    log_frame_level: bool = True  # Log every frame
    log_rep_level: bool = True    # Log every rep
    log_session_level: bool = True # Log every session
    
    # Quality control
    min_frames_per_rep: int = 10
    min_reps_per_session: int = 1
    quality_threshold: float = 0.7
    
    # ML training specific
    include_raw_landmarks: bool = True
    include_validation_data: bool = True
    normalize_coordinates: bool = True

class DataLogger:
    """Comprehensive data logging system for AI Fitness Coach"""
    
    def __init__(self, config: LoggingConfig = None):
        self.config = config or LoggingConfig()
        self.session_start_time = None
        self.current_session_id = None
        self.current_rep_id = None
        self.session_data_buffer = []
        self.rep_data_buffer = []
        self.frame_data_buffer = []
        
        # Initialize directories
        self._setup_directories()
        
        # CSV field definitions
        self._define_csv_schemas()
        
        # ENHANCED: Initialize difficulty tracking
        self.current_difficulty_level = "beginner"
        self.difficulty_changes = []  # Track difficulty changes during session
        
        print(f"✅ Data logging system initialized with difficulty tracking")
        print(f"   Output directory: {self.config.base_output_dir}")
        print(f"   Frame logging: {self.config.log_frame_level}")
        print(f"   Rep logging: {self.config.log_rep_level}")
        print(f"   Session logging: {self.config.log_session_level}")
        print(f"   Difficulty tracking: Enabled")
    
    def _setup_directories(self):
        """Create all necessary directories for data logging"""
        directories = [
            self.config.base_output_dir,
            os.path.join(self.config.base_output_dir, self.config.session_logs_dir),
            os.path.join(self.config.base_output_dir, self.config.rep_logs_dir),
            os.path.join(self.config.base_output_dir, self.config.biomech_logs_dir),
            os.path.join(self.config.base_output_dir, self.config.ml_training_dir),
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _define_csv_schemas(self):
        """Define CSV column schemas for different data types"""
        
        # Session-level data schema
        self.session_schema = [
            'session_id', 'user_id', 'timestamp', 'session_start', 'session_end',
            'total_duration_seconds', 'total_reps', 'completed_reps', 'failed_reps',
            'average_form_score', 'best_form_score', 'worst_form_score',
            'total_faults', 'safety_faults', 'form_faults', 'depth_faults',
            'user_skill_level', 'difficulty_level', 'difficulty_changes_count',  # ENHANCED: Added difficulty tracking
            'exercise_type', 'voice_feedback_enabled',
            'session_quality_score', 'improvement_score', 'fatigue_detected',
            'session_notes', 'system_version'
        ]
        
        # Rep-level data schema
        self.rep_schema = [
            'session_id', 'rep_id', 'rep_number', 'rep_start_time', 'rep_end_time',
            'rep_duration_seconds', 'total_frames', 'valid_frames', 'frame_quality',
            'final_form_score', 'safety_score', 'depth_score', 'stability_score',
            'tempo_score', 'symmetry_score', 'technique_score',
            'faults_detected', 'fault_categories', 'fault_severities',
            'movement_phase_durations', 'peak_depth_angle', 'min_knee_angle',
            'max_knee_angle', 'depth_percentage', 'movement_smoothness',
            'bilateral_asymmetry', 'center_of_mass_deviation', 'postural_stability',
            'voice_feedback_given', 'voice_messages_count', 'feedback_messages_generated',
            'feedback_categories', 'enhanced_feedback_status', 'feedback_content',
            'enhanced_feedback_content', 'user_response_time', 'correction_made',
            # ENHANCED: Added comprehensive difficulty analysis fields
            'difficulty_level_used', 'skill_level_used', 'threshold_multiplier_applied',
            'active_analyzers_count', 'active_analyzers_list', 'component_weights_used',
            'safety_weight', 'depth_weight', 'stability_weight', 'tempo_weight',
            'symmetry_weight', 'butt_wink_weight', 'knee_valgus_weight', 
            'head_position_weight', 'foot_stability_weight'
        ]
        
        # Frame-level biomechanical data schema
        self.biomech_schema = [
            'session_id', 'rep_id', 'frame_number', 'timestamp', 'phase',
            'knee_angle_left', 'knee_angle_right', 'hip_angle', 'back_angle',
            'ankle_angle_left', 'ankle_angle_right', 'center_of_mass_x', 'center_of_mass_y',
            'movement_velocity', 'acceleration', 'jerk', 'knee_symmetry_ratio',
            'ankle_symmetry_ratio', 'weight_distribution_ratio', 'postural_sway',
            'base_of_support_width', 'landmark_visibility', 'frame_quality_score',
            'head_position_x', 'head_position_y', 'shoulder_alignment',
            'heel_lift_left', 'heel_lift_right', 'foot_stability_score',
            # ENHANCED: Added difficulty context to frame data
            'difficulty_level', 'threshold_multiplier_active'
        ]
        
        # ML training dataset schema (comprehensive)
        self.ml_schema = [
            # Identifiers
            'session_id', 'rep_id', 'frame_id', 'timestamp', 'user_id',
            
            # Labels/Targets
            'form_score', 'is_good_rep', 'fault_present', 'fault_type', 'fault_severity',
            'movement_phase', 'depth_classification', 'safety_classification',
            
            # Features - Basic angles
            'knee_left', 'knee_right', 'hip_angle', 'back_angle', 'ankle_left', 'ankle_right',
            
            # Features - Derived metrics
            'knee_symmetry', 'depth_percentage', 'movement_velocity', 'acceleration',
            'center_of_mass_x', 'center_of_mass_y', 'postural_sway', 'stability_score',
            
            # Features - Advanced metrics
            'bilateral_asymmetry', 'movement_smoothness', 'temporal_consistency',
            'head_alignment', 'foot_stability', 'weight_distribution',
            
            # Context features
            'rep_number', 'session_progress', 'user_fatigue_level', 'skill_level',
            'frame_quality', 'landmark_confidence', 'previous_rep_score',
            # ENHANCED: Added difficulty context for ML training
            'difficulty_level', 'threshold_multiplier', 'component_weight_distribution',
            'safety_threshold_used', 'depth_threshold_used', 'stability_threshold_used',
            
            # Sequence features (for temporal ML models)
            'velocity_trend', 'acceleration_trend', 'angle_trend', 'stability_trend'
        ]
    
    def start_session(self, user_id: str = "default_user", exercise_type: str = "squat", 
                      user_profile: Dict = None) -> str:
        """Start a new logging session"""
        self.session_start_time = time.time()
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        # Initialize session data
        session_info = {
            'session_id': self.current_session_id,
            'user_id': user_id,
            'timestamp': self.session_start_time,
            'session_start': datetime.now().isoformat(),
            'exercise_type': exercise_type,
            'user_skill_level': user_profile.get('skill_level', 'INTERMEDIATE') if user_profile else 'INTERMEDIATE',
            'voice_feedback_enabled': user_profile.get('voice_enabled', True) if user_profile else True,
            'system_version': '2.0'
        }
        
        # Reset buffers
        self.session_data_buffer = [session_info]
        self.rep_data_buffer = []
        self.frame_data_buffer = []
        
        print(f"📊 Data logging session started: {self.current_session_id}")
        return self.current_session_id
    
    def log_difficulty_change(self, new_difficulty: str, rep_number: int = None, 
                             threshold_multiplier: float = None, skill_level: str = None):
        """Log difficulty level changes during session"""
        if not self.current_session_id:
            return
        
        old_difficulty = self.current_difficulty_level
        self.current_difficulty_level = new_difficulty
        
        change_record = {
            'timestamp': time.time(),
            'rep_number': rep_number or len(self.rep_data_buffer) + 1,
            'from_difficulty': old_difficulty,
            'to_difficulty': new_difficulty,
            'threshold_multiplier': threshold_multiplier,
            'skill_level': skill_level,
            'change_reason': 'user_selection'
        }
        
        self.difficulty_changes.append(change_record)
        
        print(f"🎯 Difficulty changed: {old_difficulty} → {new_difficulty} (Rep {change_record['rep_number']})")
        
        # Update session data with latest difficulty
        if self.session_data_buffer:
            self.session_data_buffer[0]['difficulty_level'] = new_difficulty
            self.session_data_buffer[0]['difficulty_changes_count'] = len(self.difficulty_changes)
    
    def log_rep_start(self, rep_number: int) -> str:
        """Log the start of a new repetition"""
        if not self.current_session_id:
            raise ValueError("No active session. Call start_session() first.")
        
        self.current_rep_id = f"{self.current_session_id}_rep_{rep_number:03d}"
        rep_start_data = {
            'session_id': self.current_session_id,
            'rep_id': self.current_rep_id,
            'rep_number': rep_number,
            'rep_start_time': time.time(),
            'rep_start_timestamp': datetime.now().isoformat()
        }
        
        self.rep_data_buffer.append(rep_start_data)
        return self.current_rep_id
    
    def log_frame_data(self, biomech_metrics, analysis_results: Dict = None, 
                       frame_number: int = 0, movement_phase: str = "UNKNOWN"):
        """Log frame-level biomechanical data"""
        if not self.config.log_frame_level or not self.current_rep_id:
            return
        
        frame_data = {
            'session_id': self.current_session_id,
            'rep_id': self.current_rep_id,
            'frame_number': frame_number,
            'timestamp': time.time(),
            'phase': movement_phase,
            
            # Basic biomechanical metrics
            'knee_angle_left': biomech_metrics.knee_angle_left,
            'knee_angle_right': biomech_metrics.knee_angle_right,
            'hip_angle': biomech_metrics.hip_angle,
            'back_angle': biomech_metrics.back_angle,
            'ankle_angle_left': biomech_metrics.ankle_angle_left,
            'ankle_angle_right': biomech_metrics.ankle_angle_right,
            
            # Movement metrics
            'center_of_mass_x': biomech_metrics.center_of_mass_x,
            'center_of_mass_y': biomech_metrics.center_of_mass_y,
            'movement_velocity': biomech_metrics.movement_velocity,
            'acceleration': biomech_metrics.acceleration,
            'jerk': biomech_metrics.jerk,
            
            # Symmetry and stability
            'knee_symmetry_ratio': biomech_metrics.knee_symmetry_ratio,
            'ankle_symmetry_ratio': biomech_metrics.ankle_symmetry_ratio,
            'weight_distribution_ratio': biomech_metrics.weight_distribution_ratio,
            'postural_sway': biomech_metrics.postural_sway,
            'base_of_support_width': biomech_metrics.base_of_support_width,
            
            # Quality metrics
            'landmark_visibility': biomech_metrics.landmark_visibility,
            'frame_quality_score': self._calculate_frame_quality(biomech_metrics)
        }
        
        # Add analysis results if available
        if analysis_results:
            frame_data.update({
                'head_position_x': getattr(biomech_metrics, 'nose_pos', {}).get('x', 0) if hasattr(biomech_metrics, 'nose_pos') else 0,
                'head_position_y': getattr(biomech_metrics, 'nose_pos', {}).get('y', 0) if hasattr(biomech_metrics, 'nose_pos') else 0,
                'heel_lift_left': self._calculate_heel_lift(biomech_metrics, 'left'),
                'heel_lift_right': self._calculate_heel_lift(biomech_metrics, 'right'),
                'foot_stability_score': analysis_results.get('foot_stability_score', 0)
            })
        
        self.frame_data_buffer.append(frame_data)
    
    def log_rep_completion(self, form_analysis: Dict, feedback_data: Dict = None):
        """Log completed repetition data"""
        if not self.current_rep_id or not self.rep_data_buffer:
            return
        
        # Get the current rep data
        current_rep = self.rep_data_buffer[-1]
        rep_end_time = time.time()
        
        # Calculate rep metrics
        rep_duration = rep_end_time - current_rep['rep_start_time']
        total_frames = len([f for f in self.frame_data_buffer if f['rep_id'] == self.current_rep_id])
        valid_frames = len([f for f in self.frame_data_buffer 
                           if f['rep_id'] == self.current_rep_id and f['frame_quality_score'] > 0.5])
        
        # Update rep data with completion info
        current_rep.update({
            'rep_end_time': rep_end_time,
            'rep_duration_seconds': rep_duration,
            'total_frames': total_frames,
            'valid_frames': valid_frames,
            'frame_quality': valid_frames / total_frames if total_frames > 0 else 0,
            
            # Form analysis results
            'final_form_score': form_analysis.get('overall_score', 0),
            'safety_score': form_analysis.get('safety_score', 0),
            'depth_score': form_analysis.get('depth_score', 0),
            'stability_score': form_analysis.get('stability_score', 0),
            'tempo_score': form_analysis.get('tempo_score', 0),
            'symmetry_score': form_analysis.get('symmetry_score', 0),
            'technique_score': form_analysis.get('technique_score', 0),
            
            # Fault information
            'faults_detected': len(form_analysis.get('faults', [])),
            'fault_categories': ','.join(form_analysis.get('fault_categories', [])),
            'fault_severities': ','.join(form_analysis.get('fault_severities', [])),
            
            # ENHANCED: Difficulty analysis tracking
            'difficulty_level_used': form_analysis.get('difficulty_level', self.current_difficulty_level),
            'skill_level_used': form_analysis.get('skill_level', 'unknown'),
            'threshold_multiplier_applied': form_analysis.get('threshold_multiplier', 1.0),
            'active_analyzers_count': form_analysis.get('active_analyzers_count', 0),
            'active_analyzers_list': '|'.join(form_analysis.get('active_analyzers', [])),
            'component_weights_used': form_analysis.get('component_weights_summary', ''),
            
            # Component weight breakdown
            'safety_weight': self._extract_component_weight(form_analysis, 'safety'),
            'depth_weight': self._extract_component_weight(form_analysis, 'depth'),
            'stability_weight': self._extract_component_weight(form_analysis, 'stability'),
            'tempo_weight': self._extract_component_weight(form_analysis, 'tempo'),
            'symmetry_weight': self._extract_component_weight(form_analysis, 'symmetry'),
            'butt_wink_weight': self._extract_component_weight(form_analysis, 'butt_wink'),
            'knee_valgus_weight': self._extract_component_weight(form_analysis, 'knee_valgus'),
            'head_position_weight': self._extract_component_weight(form_analysis, 'head_position'),
            'foot_stability_weight': self._extract_component_weight(form_analysis, 'foot_stability'),
            
            # Movement analysis
            'peak_depth_angle': self._calculate_peak_depth(),
            'min_knee_angle': self._calculate_min_knee_angle(),
            'max_knee_angle': self._calculate_max_knee_angle(),
            'depth_percentage': self._calculate_depth_percentage(),
            'movement_smoothness': self._calculate_movement_smoothness(),
            'bilateral_asymmetry': self._calculate_bilateral_asymmetry(),
            'center_of_mass_deviation': self._calculate_com_deviation(),
            'postural_stability': self._calculate_postural_stability(),
            
            # Feedback data - enhanced with new feedback system
            'voice_feedback_given': feedback_data.get('voice_messages_sent', 0) > 0 if feedback_data else False,
            'voice_messages_count': feedback_data.get('voice_messages_sent', 0) if feedback_data else 0,
            'feedback_messages_generated': feedback_data.get('messages_generated', 0) if feedback_data else 0,
            'feedback_categories': ','.join(feedback_data.get('feedback_categories', [])) if feedback_data else '',
            'enhanced_feedback_status': feedback_data.get('enhanced_feedback_status', 'not_available') if feedback_data else 'not_available',
            'feedback_content': str(form_analysis.get('feedback', [])),
            'enhanced_feedback_content': str(form_analysis.get('enhanced_feedback', {})),
            'user_response_time': feedback_data.get('response_time', 0) if feedback_data else 0,
            'correction_made': feedback_data.get('correction_made', False) if feedback_data else False
        })
    
    def end_session(self, session_summary: Dict = None):
        """End the current session and write all data to CSV files"""
        if not self.current_session_id:
            return
        
        session_end_time = time.time()
        session_duration = session_end_time - self.session_start_time
        
        # Calculate session-level metrics
        completed_reps = len(self.rep_data_buffer)
        if completed_reps > 0:
            form_scores = [rep.get('final_form_score', 0) for rep in self.rep_data_buffer]
            avg_score = np.mean(form_scores) if form_scores else 0
            best_score = np.max(form_scores) if form_scores else 0
            worst_score = np.min(form_scores) if form_scores else 0
            
            total_faults = sum(rep.get('faults_detected', 0) for rep in self.rep_data_buffer)
        else:
            avg_score = best_score = worst_score = total_faults = 0
        
        # Update session data
        session_data = self.session_data_buffer[0]
        session_data.update({
            'session_end': datetime.now().isoformat(),
            'total_duration_seconds': session_duration,
            'total_reps': completed_reps,
            'completed_reps': completed_reps,
            'failed_reps': 0,  # Could be calculated based on quality thresholds
            'average_form_score': avg_score,
            'best_form_score': best_score,
            'worst_form_score': worst_score,
            'total_faults': total_faults,
            'session_quality_score': self._calculate_session_quality(),
            'improvement_score': self._calculate_improvement_score(),
            'fatigue_detected': self._detect_fatigue(),
            'session_notes': session_summary.get('notes', '') if session_summary else ''
        })
        
        # Write all data to CSV files
        self._write_session_data()
        self._write_rep_data()
        self._write_biomech_data()
        self._write_ml_training_data()
        
        # Generate summary report
        self._generate_session_report()
        
        # Cleanup old data if configured
        if self.config.auto_cleanup:
            self._cleanup_old_data()
        
        print(f"📊 Session completed: {completed_reps} reps, {len(self.frame_data_buffer)} frames analyzed")
        print(f"   Session quality: {session_data['session_quality_score']:.1f}/100")
        print(f"   Average form score: {avg_score:.1f}/100")
        
        # Reset for next session
        self.current_session_id = None
        self.current_rep_id = None
        self.session_data_buffer = []
        self.rep_data_buffer = []
        self.frame_data_buffer = []
    
    def _calculate_frame_quality(self, biomech_metrics) -> float:
        """Calculate quality score for a single frame"""
        quality_score = 0.0
        
        # Landmark visibility contributes 40%
        quality_score += biomech_metrics.landmark_visibility * 0.4
        
        # Angle validity contributes 30%
        valid_angles = 0
        total_angles = 0
        
        for angle in [biomech_metrics.knee_angle_left, biomech_metrics.knee_angle_right,
                     biomech_metrics.hip_angle, biomech_metrics.back_angle]:
            total_angles += 1
            if 0 < angle < 360:  # Valid angle range
                valid_angles += 1
        
        if total_angles > 0:
            quality_score += (valid_angles / total_angles) * 0.3
        
        # Movement consistency contributes 30%
        if hasattr(biomech_metrics, 'jerk') and biomech_metrics.jerk < 100:  # Low jerk = smooth movement
            quality_score += 0.3
        
        return min(1.0, quality_score)
    
    def _calculate_heel_lift(self, biomech_metrics, side: str) -> float:
        """Calculate heel lift for left or right foot"""
        try:
            if side == 'left' and hasattr(biomech_metrics, 'left_heel_pos') and biomech_metrics.left_heel_pos:
                return biomech_metrics.left_heel_pos.y
            elif side == 'right' and hasattr(biomech_metrics, 'right_heel_pos') and biomech_metrics.right_heel_pos:
                return biomech_metrics.right_heel_pos.y
        except (AttributeError, TypeError):
            pass
        return 0.0
    
    def _calculate_peak_depth(self) -> float:
        """Calculate the peak depth achieved in current rep"""
        if not self.current_rep_id:
            return 0.0
        
        rep_frames = [f for f in self.frame_data_buffer if f['rep_id'] == self.current_rep_id]
        if not rep_frames:
            return 0.0
        
        knee_angles = [min(f['knee_angle_left'], f['knee_angle_right']) for f in rep_frames]
        return min(knee_angles) if knee_angles else 0.0
    
    def _calculate_min_knee_angle(self) -> float:
        """Calculate minimum knee angle in current rep"""
        return self._calculate_peak_depth()
    
    def _calculate_max_knee_angle(self) -> float:
        """Calculate maximum knee angle in current rep"""
        if not self.current_rep_id:
            return 0.0
        
        rep_frames = [f for f in self.frame_data_buffer if f['rep_id'] == self.current_rep_id]
        if not rep_frames:
            return 0.0
        
        knee_angles = [max(f['knee_angle_left'], f['knee_angle_right']) for f in rep_frames]
        return max(knee_angles) if knee_angles else 0.0
    
    def _calculate_depth_percentage(self) -> float:
        """Calculate depth percentage based on knee angle range"""
        min_angle = self._calculate_min_knee_angle()
        max_angle = self._calculate_max_knee_angle()
        
        if max_angle <= min_angle:
            return 0.0
        
        # Full squat is typically 90 degrees or less
        # Standing is typically 170-180 degrees
        depth_range = max_angle - min_angle
        full_range = 90  # Expected range for good squat
        
        return min(100.0, (depth_range / full_range) * 100)
    
    def _calculate_movement_smoothness(self) -> float:
        """Calculate movement smoothness based on jerk values"""
        if not self.current_rep_id:
            return 0.0
        
        rep_frames = [f for f in self.frame_data_buffer if f['rep_id'] == self.current_rep_id]
        if len(rep_frames) < 3:
            return 0.0
        
        # Calculate velocity changes (jerk approximation)
        velocities = [f.get('movement_velocity', 0) for f in rep_frames]
        jerk_values = []
        
        for i in range(2, len(velocities)):
            accel1 = velocities[i-1] - velocities[i-2]
            accel2 = velocities[i] - velocities[i-1]
            jerk = abs(accel2 - accel1)
            jerk_values.append(jerk)
        
        if jerk_values:
            avg_jerk = np.mean(jerk_values)
            # Lower jerk = smoother movement (inverse relationship)
            smoothness = max(0, 100 - avg_jerk * 10)
            return min(100.0, smoothness)
        
        return 50.0  # Default neutral score
    
    def _calculate_bilateral_asymmetry(self) -> float:
        """Calculate bilateral asymmetry between left and right sides"""
        if not self.current_rep_id:
            return 0.0
        
        rep_frames = [f for f in self.frame_data_buffer if f['rep_id'] == self.current_rep_id]
        if not rep_frames:
            return 0.0
        
        asymmetries = []
        for frame in rep_frames:
            left_knee = frame.get('knee_angle_left', 0)
            right_knee = frame.get('knee_angle_right', 0)
            
            if left_knee > 0 and right_knee > 0:
                asymmetry = abs(left_knee - right_knee) / max(left_knee, right_knee) * 100
                asymmetries.append(asymmetry)
        
        return np.mean(asymmetries) if asymmetries else 0.0
    
    def _calculate_com_deviation(self) -> float:
        """Calculate center of mass deviation from ideal path"""
        if not self.current_rep_id:
            return 0.0
        
        rep_frames = [f for f in self.frame_data_buffer if f['rep_id'] == self.current_rep_id]
        if len(rep_frames) < 5:
            return 0.0
        
        com_x_values = [f.get('center_of_mass_x', 0) for f in rep_frames]
        com_y_values = [f.get('center_of_mass_y', 0) for f in rep_frames]
        
        # Calculate standard deviation as a measure of deviation
        x_deviation = np.std(com_x_values) if com_x_values else 0
        y_deviation = np.std(com_y_values) if com_y_values else 0
        
        return (x_deviation + y_deviation) * 100  # Scale for percentage
    
    def _calculate_postural_stability(self) -> float:
        """Calculate postural stability score"""
        if not self.current_rep_id:
            return 0.0
        
        rep_frames = [f for f in self.frame_data_buffer if f['rep_id'] == self.current_rep_id]
        if not rep_frames:
            return 0.0
        
        sway_values = [f.get('postural_sway', 0) for f in rep_frames]
        avg_sway = np.mean(sway_values) if sway_values else 0
        
        # Lower sway = higher stability (inverse relationship)
        stability = max(0, 100 - avg_sway * 50)
        return min(100.0, stability)
    
    def _calculate_session_quality(self) -> float:
        """Calculate overall session quality score"""
        if not self.rep_data_buffer:
            return 0.0
        
        # Average frame quality across all reps
        frame_qualities = [rep.get('frame_quality', 0) for rep in self.rep_data_buffer]
        avg_frame_quality = np.mean(frame_qualities) if frame_qualities else 0
        
        # Average form scores
        form_scores = [rep.get('final_form_score', 0) for rep in self.rep_data_buffer]
        avg_form_score = np.mean(form_scores) if form_scores else 0
        
        # Rep consistency (lower standard deviation = higher consistency)
        form_std = np.std(form_scores) if len(form_scores) > 1 else 0
        consistency_score = max(0, 100 - form_std)
        
        # Combine factors
        quality_score = (avg_frame_quality * 30 + avg_form_score * 50 + consistency_score * 20) / 100
        return min(100.0, quality_score * 100)
    
    def _calculate_improvement_score(self) -> float:
        """Calculate improvement score throughout the session"""
        if len(self.rep_data_buffer) < 3:
            return 0.0  # Need at least 3 reps to measure improvement
        
        form_scores = [rep.get('final_form_score', 0) for rep in self.rep_data_buffer]
        
        # Calculate trend (simple linear regression slope)
        x = list(range(len(form_scores)))
        y = form_scores
        
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Convert slope to improvement score (positive slope = improvement)
        improvement = max(-100, min(100, slope * 10))
        return improvement
    
    def _detect_fatigue(self) -> bool:
        """Detect if user showed signs of fatigue during session"""
        if len(self.rep_data_buffer) < 4:
            return False
        
        # Look for declining performance in the last 3 reps
        recent_scores = [rep.get('final_form_score', 0) for rep in self.rep_data_buffer[-3:]]
        early_scores = [rep.get('final_form_score', 0) for rep in self.rep_data_buffer[:3]]
        
        if not recent_scores or not early_scores:
            return False
        
        avg_recent = np.mean(recent_scores)
        avg_early = np.mean(early_scores)
        
        # Fatigue detected if recent performance is significantly lower
        decline_threshold = 15  # 15 point decline indicates fatigue
        return (avg_early - avg_recent) > decline_threshold
    
    def _extract_component_weight(self, form_analysis: Dict, component_name: str) -> float:
        """Extract weight for a specific component from form analysis"""
        component_scores = form_analysis.get('component_scores', {})
        if component_name in component_scores:
            comp_data = component_scores[component_name]
            if isinstance(comp_data, dict):
                return comp_data.get('weight', 0.0)
        return 0.0
    
    def _write_session_data(self):
        """Write session data to CSV file"""
        if not self.session_data_buffer:
            return
        
        session_file = os.path.join(
            self.config.base_output_dir,
            self.config.session_logs_dir,
            f"{self.config.session_file_prefix}_{datetime.now().strftime('%Y%m')}.csv"
        )
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(session_file)
        
        with open(session_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.session_schema)
            
            if not file_exists:
                writer.writeheader()
            
            for session_data in self.session_data_buffer:
                # Ensure all schema fields are present
                row_data = {field: session_data.get(field, '') for field in self.session_schema}
                writer.writerow(row_data)
    
    def _write_rep_data(self):
        """Write rep data to CSV file"""
        if not self.rep_data_buffer:
            return
        
        rep_file = os.path.join(
            self.config.base_output_dir,
            self.config.rep_logs_dir,
            f"{self.config.rep_file_prefix}_{datetime.now().strftime('%Y%m')}.csv"
        )
        
        file_exists = os.path.exists(rep_file)
        
        with open(rep_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.rep_schema)
            
            if not file_exists:
                writer.writeheader()
            
            for rep_data in self.rep_data_buffer:
                row_data = {field: rep_data.get(field, '') for field in self.rep_schema}
                writer.writerow(row_data)
    
    def _write_biomech_data(self):
        """Write frame-level biomechanical data to CSV file"""
        if not self.frame_data_buffer:
            return
        
        biomech_file = os.path.join(
            self.config.base_output_dir,
            self.config.biomech_logs_dir,
            f"{self.config.biomech_file_prefix}_{datetime.now().strftime('%Y%m')}.csv"
        )
        
        file_exists = os.path.exists(biomech_file)
        
        with open(biomech_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.biomech_schema)
            
            if not file_exists:
                writer.writeheader()
            
            for frame_data in self.frame_data_buffer:
                row_data = {field: frame_data.get(field, '') for field in self.biomech_schema}
                writer.writerow(row_data)
    
    def _write_ml_training_data(self):
        """Write ML training dataset to CSV file"""
        if not self.frame_data_buffer or not self.rep_data_buffer:
            return
        
        ml_file = os.path.join(
            self.config.base_output_dir,
            self.config.ml_training_dir,
            f"{self.config.ml_file_prefix}_{datetime.now().strftime('%Y%m')}.csv"
        )
        
        file_exists = os.path.exists(ml_file)
        
        with open(ml_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.ml_schema)
            
            if not file_exists:
                writer.writeheader()
            
            # Create ML training records by combining frame and rep data
            for frame_data in self.frame_data_buffer:
                rep_data = next((r for r in self.rep_data_buffer if r['rep_id'] == frame_data['rep_id']), {})
                session_data = self.session_data_buffer[0] if self.session_data_buffer else {}
                
                ml_record = self._create_ml_training_record(frame_data, rep_data, session_data)
                writer.writerow(ml_record)
    
    def _create_ml_training_record(self, frame_data: Dict, rep_data: Dict, session_data: Dict) -> Dict:
        """Create a comprehensive ML training record"""
        
        # Generate labels/targets
        form_score = rep_data.get('final_form_score', 0)
        is_good_rep = form_score >= 80  # Threshold for "good" rep
        fault_present = rep_data.get('faults_detected', 0) > 0
        fault_types = rep_data.get('fault_categories', '').split(',') if rep_data.get('fault_categories') else []
        primary_fault = fault_types[0] if fault_types else 'NONE'
        
        # Calculate derived features
        knee_symmetry = abs(frame_data.get('knee_angle_left', 0) - frame_data.get('knee_angle_right', 0))
        depth_percentage = self._calculate_depth_from_angles(
            frame_data.get('knee_angle_left', 0), 
            frame_data.get('knee_angle_right', 0)
        )
        
        # Context features
        rep_progress = rep_data.get('rep_number', 0) / max(session_data.get('total_reps', 1), 1)
        
        ml_record = {
            # Identifiers
            'session_id': frame_data.get('session_id', ''),
            'rep_id': frame_data.get('rep_id', ''),
            'frame_id': f"{frame_data.get('rep_id', '')}_{frame_data.get('frame_number', 0)}",
            'timestamp': frame_data.get('timestamp', 0),
            'user_id': session_data.get('user_id', ''),
            
            # Labels/Targets
            'form_score': form_score,
            'is_good_rep': 1 if is_good_rep else 0,
            'fault_present': 1 if fault_present else 0,
            'fault_type': primary_fault,
            'fault_severity': 'LOW' if form_score > 70 else 'MEDIUM' if form_score > 50 else 'HIGH',
            'movement_phase': frame_data.get('phase', 'UNKNOWN'),
            'depth_classification': self._classify_depth(depth_percentage),
            'safety_classification': self._classify_safety(rep_data.get('safety_score', 0)),
            
            # Features - Basic angles
            'knee_left': frame_data.get('knee_angle_left', 0),
            'knee_right': frame_data.get('knee_angle_right', 0),
            'hip_angle': frame_data.get('hip_angle', 0),
            'back_angle': frame_data.get('back_angle', 0),
            'ankle_left': frame_data.get('ankle_angle_left', 0),
            'ankle_right': frame_data.get('ankle_angle_right', 0),
            
            # Features - Derived metrics
            'knee_symmetry': knee_symmetry,
            'depth_percentage': depth_percentage,
            'movement_velocity': frame_data.get('movement_velocity', 0),
            'acceleration': frame_data.get('acceleration', 0),
            'center_of_mass_x': frame_data.get('center_of_mass_x', 0),
            'center_of_mass_y': frame_data.get('center_of_mass_y', 0),
            'postural_sway': frame_data.get('postural_sway', 0),
            'stability_score': rep_data.get('stability_score', 0),
            
            # Features - Advanced metrics
            'bilateral_asymmetry': rep_data.get('bilateral_asymmetry', 0),
            'movement_smoothness': rep_data.get('movement_smoothness', 0),
            'temporal_consistency': self._calculate_temporal_consistency(frame_data),
            'head_alignment': frame_data.get('head_position_y', 0),
            'foot_stability': frame_data.get('foot_stability_score', 0),
            'weight_distribution': frame_data.get('weight_distribution_ratio', 1.0),
            
            # Context features
            'rep_number': rep_data.get('rep_number', 0),
            'session_progress': rep_progress,
            'user_fatigue_level': self._estimate_fatigue_level(rep_data, session_data),
            'skill_level': session_data.get('user_skill_level', 'INTERMEDIATE'),
            'frame_quality': frame_data.get('frame_quality_score', 0),
            'landmark_confidence': frame_data.get('landmark_visibility', 0),
            'previous_rep_score': self._get_previous_rep_score(rep_data.get('rep_number', 0)),
            
            # Sequence features (simplified for now)
            'velocity_trend': self._calculate_velocity_trend(frame_data),
            'acceleration_trend': self._calculate_acceleration_trend(frame_data),
            'angle_trend': self._calculate_angle_trend(frame_data),
            'stability_trend': self._calculate_stability_trend(frame_data),
            
            # ENHANCED: Difficulty context for ML training
            'difficulty_level': rep_data.get('difficulty_level_used', session_data.get('difficulty_level', 'beginner')),
            'difficulty_threshold_multiplier': rep_data.get('threshold_multiplier_applied', 1.0),
            'component_weight_safety': rep_data.get('safety_weight', 0.0),
            'component_weight_depth': rep_data.get('depth_weight', 0.0),
            'component_weight_stability': rep_data.get('stability_weight', 0.0)
        }
        
        return {field: ml_record.get(field, '') for field in self.ml_schema}
    
    def _calculate_depth_from_angles(self, knee_left: float, knee_right: float) -> float:
        """Calculate depth percentage from knee angles"""
        avg_knee = (knee_left + knee_right) / 2 if knee_left > 0 and knee_right > 0 else 0
        if avg_knee <= 0:
            return 0
        
        # 180° = standing, 90° = parallel, lower = deeper
        depth = max(0, (180 - avg_knee) / 90 * 100)
        return min(100, depth)
    
    def _classify_depth(self, depth_percentage: float) -> str:
        """Classify squat depth"""
        if depth_percentage < 30:
            return 'SHALLOW'
        elif depth_percentage < 70:
            return 'PARTIAL'
        elif depth_percentage < 100:
            return 'GOOD'
        else:
            return 'DEEP'
    
    def _classify_safety(self, safety_score: float) -> str:
        """Classify safety level"""
        if safety_score >= 90:
            return 'EXCELLENT'
        elif safety_score >= 75:
            return 'GOOD'
        elif safety_score >= 60:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _calculate_temporal_consistency(self, frame_data: Dict) -> float:
        """Calculate temporal consistency (simplified)"""
        # This would need frame sequence analysis for full implementation
        return frame_data.get('frame_quality_score', 0) * 100
    
    def _estimate_fatigue_level(self, rep_data: Dict, session_data: Dict) -> str:
        """Estimate user fatigue level"""
        rep_number = rep_data.get('rep_number', 0)
        total_reps = session_data.get('total_reps', 1)
        form_score = rep_data.get('final_form_score', 100)
        
        progress = rep_number / max(total_reps, 1)
        
        if progress < 0.3:
            return 'FRESH'
        elif progress < 0.6:
            return 'MODERATE'
        elif form_score > 80:
            return 'MODERATE'
        else:
            return 'FATIGUED'
    
    def _get_previous_rep_score(self, current_rep_number: int) -> float:
        """Get the form score from the previous rep"""
        if current_rep_number <= 1:
            return 0
        
        prev_rep = next((r for r in self.rep_data_buffer if r.get('rep_number') == current_rep_number - 1), None)
        return prev_rep.get('final_form_score', 0) if prev_rep else 0
    
    def _calculate_velocity_trend(self, frame_data: Dict) -> str:
        """Calculate velocity trend (simplified)"""
        velocity = frame_data.get('movement_velocity', 0)
        if velocity > 10:
            return 'INCREASING'
        elif velocity < -10:
            return 'DECREASING'
        else:
            return 'STABLE'
    
    def _calculate_acceleration_trend(self, frame_data: Dict) -> str:
        """Calculate acceleration trend (simplified)"""
        acceleration = frame_data.get('acceleration', 0)
        if acceleration > 5:
            return 'ACCELERATING'
        elif acceleration < -5:
            return 'DECELERATING'
        else:
            return 'CONSTANT'
    
    def _calculate_angle_trend(self, frame_data: Dict) -> str:
        """Calculate angle trend (simplified)"""
        knee_avg = (frame_data.get('knee_angle_left', 0) + frame_data.get('knee_angle_right', 0)) / 2
        if knee_avg > 150:
            return 'EXTENDING'
        elif knee_avg < 100:
            return 'FLEXING'
        else:
            return 'MID_RANGE'
    
    def _calculate_stability_trend(self, frame_data: Dict) -> str:
        """Calculate stability trend (simplified)"""
        sway = frame_data.get('postural_sway', 0)
        if sway > 0.1:
            return 'UNSTABLE'
        elif sway < 0.05:
            return 'STABLE'
        else:
            return 'MODERATE'
    
    def _generate_session_report(self):
        """Generate a summary report for the session"""
        if not self.current_session_id:
            return
        
        report_file = os.path.join(
            self.config.base_output_dir,
            f"session_report_{self.current_session_id}.txt"
        )
        
        session_data = self.session_data_buffer[0] if self.session_data_buffer else {}
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"AI Fitness Coach - Session Report\n")
            f.write(f"={'='*50}\n\n")
            f.write(f"Session ID: {session_data.get('session_id', 'Unknown')}\n")
            f.write(f"User: {session_data.get('user_id', 'Unknown')}\n")
            f.write(f"Date: {session_data.get('session_start', 'Unknown')}\n")
            f.write(f"Duration: {session_data.get('total_duration_seconds', 0):.1f} seconds\n\n")
            
            f.write(f"Performance Summary:\n")
            f.write(f"- Total Reps: {session_data.get('total_reps', 0)}\n")
            f.write(f"- Average Score: {session_data.get('average_form_score', 0):.1f}/100\n")
            f.write(f"- Best Score: {session_data.get('best_form_score', 0):.1f}/100\n")
            f.write(f"- Session Quality: {session_data.get('session_quality_score', 0):.1f}/100\n")
            f.write(f"- Improvement: {session_data.get('improvement_score', 0):.1f}\n")
            f.write(f"- Fatigue Detected: {'Yes' if session_data.get('fatigue_detected') else 'No'}\n\n")
            
            f.write(f"Data Logged:\n")
            f.write(f"- Session Records: {len(self.session_data_buffer)}\n")
            f.write(f"- Rep Records: {len(self.rep_data_buffer)}\n")
            f.write(f"- Frame Records: {len(self.frame_data_buffer)}\n")
            f.write(f"- ML Training Records: {len(self.frame_data_buffer)}\n\n")
            
            if self.rep_data_buffer:
                f.write(f"Rep-by-Rep Breakdown:\n")
                for i, rep in enumerate(self.rep_data_buffer, 1):
                    f.write(f"  Rep {i}: Score {rep.get('final_form_score', 0):.1f}, ")
                    f.write(f"Faults {rep.get('faults_detected', 0)}, ")
                    f.write(f"Duration {rep.get('rep_duration_seconds', 0):.1f}s\n")
    
    def _cleanup_old_data(self):
        """Clean up old data files based on retention policy"""
        if not self.config.auto_cleanup:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.config.max_days_retention)
        directories_to_clean = [
            os.path.join(self.config.base_output_dir, self.config.session_logs_dir),
            os.path.join(self.config.base_output_dir, self.config.rep_logs_dir),
            os.path.join(self.config.base_output_dir, self.config.biomech_logs_dir),
            os.path.join(self.config.base_output_dir, self.config.ml_training_dir)
        ]
        
        for directory in directories_to_clean:
            if not os.path.exists(directory):
                continue
            
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    try:
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            logger.info(f"Cleaned up old data file: {filename}")
                    except (OSError, ValueError) as e:
                        logger.warning(f"Could not clean up file {filename}: {e}")
    
    def get_session_stats(self) -> Dict:
        """Get current session statistics"""
        if not self.current_session_id:
            return {}
        
        return {
            'session_id': self.current_session_id,
            'duration_seconds': time.time() - self.session_start_time if self.session_start_time else 0,
            'total_reps': len(self.rep_data_buffer),
            'total_frames': len(self.frame_data_buffer),
            'average_frame_quality': np.mean([f.get('frame_quality_score', 0) for f in self.frame_data_buffer]) if self.frame_data_buffer else 0,
            'current_session_quality': self._calculate_session_quality()
        }
    
    def cleanup_old_logs(self, days_to_keep: int = None) -> Dict:
        """Clean up old log files beyond retention period"""
        
        days_to_keep = days_to_keep or self.config.max_days_retention
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleanup_results = {
            'cutoff_date': cutoff_date.isoformat(),
            'files_removed': 0,
            'space_freed_mb': 0,
            'errors': []
        }
        
        base_dir = self.config.base_output_dir
        log_dirs = [
            ('sessions', self.config.session_logs_dir),
            ('reps', self.config.rep_logs_dir), 
            ('biomechanics', self.config.biomech_logs_dir),
            ('ml_training', self.config.ml_training_dir)
        ]
        
        for log_type, dir_name in log_dirs:
            log_dir = os.path.join(base_dir, dir_name)
            
            if not os.path.exists(log_dir):
                continue
                
            try:
                for filename in os.listdir(log_dir):
                    if not filename.endswith('.csv'):
                        continue
                        
                    file_path = os.path.join(log_dir, filename)
                    
                    try:
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        
                        if file_time < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            
                            cleanup_results['files_removed'] += 1
                            cleanup_results['space_freed_mb'] += file_size / (1024 * 1024)
                            
                            logger.info(f"Removed old {log_type} log: {filename}")
                            
                    except (OSError, ValueError) as e:
                        error_msg = f"Could not process {filename}: {e}"
                        cleanup_results['errors'].append(error_msg)
                        logger.warning(error_msg)
                        
            except Exception as e:
                error_msg = f"Could not clean {log_type} directory: {e}"
                cleanup_results['errors'].append(error_msg)
                logger.error(error_msg)
        
        return cleanup_results
    
    def validate_data_integrity(self) -> Dict:
        """Validate data integrity with comprehensive checks"""
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'checks_performed': []
        }
        
        # Check 1: Directory structure
        structure_check = self._check_directory_structure()
        validation_results['directory_structure'] = structure_check
        validation_results['checks_performed'].append('directory_structure')
        
        # Check 2: File consistency
        file_check = self._check_file_consistency()
        validation_results['file_consistency'] = file_check
        validation_results['checks_performed'].append('file_consistency')
        
        # Check 3: Data quality
        quality_check = self._check_data_quality()
        validation_results['data_quality'] = quality_check
        validation_results['checks_performed'].append('data_quality')
        
        # Check 4: Cross-reference integrity
        cross_ref_check = self._check_cross_references()
        validation_results['cross_references'] = cross_ref_check
        validation_results['checks_performed'].append('cross_references')
        
        # Calculate overall status
        all_scores = []
        for check_name in validation_results['checks_performed']:
            check_data = validation_results.get(check_name, {})
            if isinstance(check_data, dict) and 'score' in check_data:
                all_scores.append(check_data['score'])
        
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            if avg_score >= 90:
                validation_results['overall_status'] = 'EXCELLENT'
            elif avg_score >= 75:
                validation_results['overall_status'] = 'GOOD'
            elif avg_score >= 60:
                validation_results['overall_status'] = 'FAIR'
            else:
                validation_results['overall_status'] = 'POOR'
        
        validation_results['overall_score'] = sum(all_scores) / len(all_scores) if all_scores else 0
        
        return validation_results
    
    def _check_directory_structure(self) -> Dict:
        """Check if all required directories exist"""
        
        required_dirs = [
            self.config.session_logs_dir,
            self.config.rep_logs_dir,
            self.config.biomech_logs_dir,
            self.config.ml_training_dir
        ]
        
        missing_dirs = []
        existing_dirs = []
        
        for dir_name in required_dirs:
            full_path = os.path.join(self.config.base_output_dir, dir_name)
            if os.path.exists(full_path):
                existing_dirs.append(dir_name)
            else:
                missing_dirs.append(dir_name)
        
        score = (len(existing_dirs) / len(required_dirs)) * 100 if required_dirs else 0
        
        return {
            'score': score,
            'status': 'PASS' if score == 100 else 'FAIL',
            'existing_directories': existing_dirs,
            'missing_directories': missing_dirs,
            'issues': [f"Missing directory: {d}" for d in missing_dirs]
        }
    
    def _check_file_consistency(self) -> Dict:
        """Check file consistency and headers"""
        
        issues = []
        total_files = 0
        valid_files = 0
        
        # Check each log type
        log_configs = [
            (self.config.session_logs_dir, self.session_schema, 'session'),
            (self.config.rep_logs_dir, self.rep_schema, 'rep'),
            (self.config.biomech_logs_dir, self.biomech_schema, 'biomech'),
            (self.config.ml_training_dir, self.ml_schema, 'ml_training')
        ]
        
        for dir_name, expected_schema, log_type in log_configs:
            log_dir = os.path.join(self.config.base_output_dir, dir_name)
            
            if not os.path.exists(log_dir):
                continue
            
            for filename in os.listdir(log_dir):
                if not filename.endswith('.csv'):
                    continue
                
                total_files += 1
                file_path = os.path.join(log_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        
                        # Check headers
                        if set(reader.fieldnames) != set(expected_schema):
                            missing = set(expected_schema) - set(reader.fieldnames or [])
                            extra = set(reader.fieldnames or []) - set(expected_schema)
                            
                            if missing:
                                issues.append(f"{log_type} file {filename}: Missing columns {missing}")
                            if extra:
                                issues.append(f"{log_type} file {filename}: Extra columns {extra}")
                        else:
                            valid_files += 1
                            
                except Exception as e:
                    issues.append(f"Cannot read {log_type} file {filename}: {e}")
        
        score = (valid_files / total_files * 100) if total_files > 0 else 100
        
        return {
            'score': score,
            'status': 'PASS' if score >= 90 else 'FAIL',
            'total_files': total_files,
            'valid_files': valid_files,
            'issues': issues[:10]  # Limit to first 10 issues
        }
    
    def _check_data_quality(self) -> Dict:
        """Check data quality metrics"""
        
        quality_issues = []
        quality_scores = []
        
        # Check session data quality
        session_quality = self._check_session_data_quality()
        quality_scores.append(session_quality['score'])
        quality_issues.extend(session_quality.get('issues', []))
        
        # Check rep data quality
        rep_quality = self._check_rep_data_quality()
        quality_scores.append(rep_quality['score'])
        quality_issues.extend(rep_quality.get('issues', []))
        
        # Check biomech data quality
        biomech_quality = self._check_biomech_data_quality()
        quality_scores.append(biomech_quality['score'])
        quality_issues.extend(biomech_quality.get('issues', []))
        
        avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'score': avg_score,
            'status': 'PASS' if avg_score >= 75 else 'FAIL',
            'session_quality': session_quality,
            'rep_quality': rep_quality,
            'biomech_quality': biomech_quality,
            'overall_issues': quality_issues[:5]
        }
    
    def _check_session_data_quality(self) -> Dict:
        """Check session data quality"""
        
        session_dir = os.path.join(self.config.base_output_dir, self.config.session_logs_dir)
        if not os.path.exists(session_dir):
            return {'score': 0, 'issues': ['Session directory not found']}
        
        total_records = 0
        valid_records = 0
        issues = []
        
        for filename in os.listdir(session_dir):
            if not filename.endswith('.csv'):
                continue
                
            try:
                with open(os.path.join(session_dir, filename), 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        total_records += 1
                        
                        # Check required fields
                        if not row.get('session_id') or not row.get('user_id'):
                            issues.append(f"Missing required fields in {filename}")
                            continue
                        
                        # Check data ranges
                        try:
                            form_score = float(row.get('average_form_score', 0))
                            if not (0 <= form_score <= 100):
                                issues.append(f"Invalid form score in {filename}: {form_score}")
                                continue
                        except (ValueError, TypeError):
                            issues.append(f"Invalid form score format in {filename}")
                            continue
                        
                        valid_records += 1
                        
            except Exception as e:
                issues.append(f"Cannot process session file {filename}: {e}")
        
        score = (valid_records / total_records * 100) if total_records > 0 else 0
        
        return {
            'score': score,
            'total_records': total_records,
            'valid_records': valid_records,
            'issues': issues[:3]
        }
    
    def _check_rep_data_quality(self) -> Dict:
        """Check rep data quality"""
        
        rep_dir = os.path.join(self.config.base_output_dir, self.config.rep_logs_dir)
        if not os.path.exists(rep_dir):
            return {'score': 0, 'issues': ['Rep directory not found']}
        
        total_records = 0
        valid_records = 0
        issues = []
        
        for filename in os.listdir(rep_dir):
            if not filename.endswith('.csv'):
                continue
                
            try:
                with open(os.path.join(rep_dir, filename), 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        total_records += 1
                        
                        # Check rep number consistency
                        try:
                            rep_num = int(row.get('rep_number', 0))
                            if rep_num <= 0:
                                issues.append(f"Invalid rep number in {filename}: {rep_num}")
                                continue
                        except (ValueError, TypeError):
                            issues.append(f"Invalid rep number format in {filename}")
                            continue
                        
                        # Check form score range
                        try:
                            form_score = float(row.get('final_form_score', 0))
                            if not (0 <= form_score <= 100):
                                issues.append(f"Invalid rep form score in {filename}: {form_score}")
                                continue
                        except (ValueError, TypeError):
                            issues.append(f"Invalid rep form score format in {filename}")
                            continue
                        
                        valid_records += 1
                        
            except Exception as e:
                issues.append(f"Cannot process rep file {filename}: {e}")
        
        score = (valid_records / total_records * 100) if total_records > 0 else 0
        
        return {
            'score': score,
            'total_records': total_records,
            'valid_records': valid_records,
            'issues': issues[:3]
        }
    
    def _check_biomech_data_quality(self) -> Dict:
        """Check biomechanical data quality"""
        
        biomech_dir = os.path.join(self.config.base_output_dir, self.config.biomech_logs_dir)
        if not os.path.exists(biomech_dir):
            return {'score': 0, 'issues': ['Biomech directory not found']}
        
        total_records = 0
        valid_records = 0
        issues = []
        
        for filename in os.listdir(biomech_dir):
            if not filename.endswith('.csv'):
                continue
                
            try:
                with open(os.path.join(biomech_dir, filename), 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        total_records += 1
                        
                        # Check angle ranges
                        angle_fields = ['knee_angle_left', 'knee_angle_right', 'hip_angle']
                        valid_angles = 0
                        
                        for field in angle_fields:
                            try:
                                angle = float(row.get(field, 0))
                                if 0 <= angle <= 180:  # Basic angle validation
                                    valid_angles += 1
                            except (ValueError, TypeError):
                                pass
                        
                        if valid_angles >= 2:  # At least 2 valid angles
                            valid_records += 1
                        else:
                            issues.append(f"Invalid angles in {filename}")
                        
            except Exception as e:
                issues.append(f"Cannot process biomech file {filename}: {e}")
        
        score = (valid_records / total_records * 100) if total_records > 0 else 0
        
        return {
            'score': score,
            'total_records': total_records,
            'valid_records': valid_records,
            'issues': issues[:3]
        }
    
    def _check_cross_references(self) -> Dict:
        """Check cross-reference integrity between data files"""
        
        # Load session IDs
        session_ids = set()
        session_dir = os.path.join(self.config.base_output_dir, self.config.session_logs_dir)
        
        if os.path.exists(session_dir):
            for filename in os.listdir(session_dir):
                if filename.endswith('.csv'):
                    try:
                        with open(os.path.join(session_dir, filename), 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                if row.get('session_id'):
                                    session_ids.add(row['session_id'])
                    except Exception:
                        pass
        
        # Check rep references
        orphaned_reps = 0
        total_reps = 0
        rep_dir = os.path.join(self.config.base_output_dir, self.config.rep_logs_dir)
        
        if os.path.exists(rep_dir):
            for filename in os.listdir(rep_dir):
                if filename.endswith('.csv'):
                    try:
                        with open(os.path.join(rep_dir, filename), 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                total_reps += 1
                                if row.get('session_id') not in session_ids:
                                    orphaned_reps += 1
                    except Exception:
                        pass
        
        # Calculate score
        if total_reps > 0:
            orphan_rate = orphaned_reps / total_reps
            score = max(0, (1 - orphan_rate) * 100)
        else:
            score = 100
        
        issues = []
        if orphaned_reps > 0:
            issues.append(f"Found {orphaned_reps} orphaned rep records")
        
        return {
            'score': score,
            'status': 'PASS' if score >= 95 else 'FAIL',
            'session_ids_found': len(session_ids),
            'total_reps_checked': total_reps,
            'orphaned_reps': orphaned_reps,
            'orphan_rate_percent': (orphaned_reps / total_reps * 100) if total_reps > 0 else 0,
            'issues': issues
        }
    
    def export_summary_report(self, output_file: str = None) -> Dict:
        """Export comprehensive summary report"""
        
        output_file = output_file or os.path.join(
            self.config.base_output_dir,
            f"data_summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        # Gather all information
        summary = {
            'report_timestamp': datetime.now().isoformat(),
            'data_integrity_check': self.validate_data_integrity(),
            'file_statistics': self._get_file_stats(),
            'data_coverage': self._get_data_coverage_stats(),
            'recent_activity': self._get_recent_activity_stats(),
            'recommendations': self._get_improvement_recommendations()
        }
        
        # Write to file
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            summary['export_success'] = True
            summary['export_file'] = output_file
        except Exception as e:
            summary['export_success'] = False
            summary['export_error'] = str(e)
        
        return summary
    
    def _get_file_stats(self) -> Dict:
        """Get file statistics"""
        
        stats = {}
        base_dir = self.config.base_output_dir
        
        for log_type, dir_name in [
            ('sessions', self.config.session_logs_dir),
            ('reps', self.config.rep_logs_dir),
            ('biomechanics', self.config.biomech_logs_dir),
            ('ml_training', self.config.ml_training_dir)
        ]:
            log_dir = os.path.join(base_dir, dir_name)
            
            if os.path.exists(log_dir):
                files = [f for f in os.listdir(log_dir) if f.endswith('.csv')]
                total_size = sum(
                    os.path.getsize(os.path.join(log_dir, f))
                    for f in files if os.path.exists(os.path.join(log_dir, f))
                )
                
                stats[log_type] = {
                    'file_count': len(files),
                    'total_size_mb': total_size / (1024 * 1024),
                    'avg_file_size_kb': (total_size / len(files) / 1024) if files else 0,
                    'latest_file': max(files, key=lambda f: os.path.getctime(os.path.join(log_dir, f))) if files else None
                }
            else:
                stats[log_type] = {
                    'file_count': 0,
                    'total_size_mb': 0,
                    'avg_file_size_kb': 0,
                    'latest_file': None
                }
        
        return stats
    
    def _get_data_coverage_stats(self) -> Dict:
        """Get data coverage statistics"""
        
        unique_sessions = set()
        unique_users = set()
        timestamps = []
        
        session_dir = os.path.join(self.config.base_output_dir, self.config.session_logs_dir)
        
        if os.path.exists(session_dir):
            for filename in os.listdir(session_dir):
                if filename.endswith('.csv'):
                    try:
                        with open(os.path.join(session_dir, filename), 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                if row.get('session_id'):
                                    unique_sessions.add(row['session_id'])
                                if row.get('user_id'):
                                    unique_users.add(row['user_id'])
                                if row.get('timestamp'):
                                    try:
                                        timestamps.append(float(row['timestamp']))
                                    except (ValueError, TypeError):
                                        pass
                    except Exception:
                        pass
        
        # Calculate date range
        date_range = {}
        if timestamps:
            timestamps.sort()
            earliest = datetime.fromtimestamp(timestamps[0])
            latest = datetime.fromtimestamp(timestamps[-1])
            span_days = (latest - earliest).days
            
            date_range = {
                'earliest_session': earliest.isoformat(),
                'latest_session': latest.isoformat(),
                'span_days': span_days,
                'sessions_per_day': len(unique_sessions) / max(span_days, 1)
            }
        
        return {
            'unique_sessions': len(unique_sessions),
            'unique_users': len(unique_users),
            'sessions_per_user': len(unique_sessions) / len(unique_users) if unique_users else 0,
            'date_range': date_range
        }
    
    def _get_recent_activity_stats(self) -> Dict:
        """Get recent activity statistics (last 7 days)"""
        
        cutoff_date = datetime.now() - timedelta(days=7)
        cutoff_timestamp = cutoff_date.timestamp()
        
        recent_sessions = 0
        recent_users = set()
        
        session_dir = os.path.join(self.config.base_output_dir, self.config.session_logs_dir)
        
        if os.path.exists(session_dir):
            for filename in os.listdir(session_dir):
                if filename.endswith('.csv'):
                    try:
                        with open(os.path.join(session_dir, filename), 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                try:
                                    timestamp = float(row.get('timestamp', 0))
                                    if timestamp >= cutoff_timestamp:
                                        recent_sessions += 1
                                        if row.get('user_id'):
                                            recent_users.add(row['user_id'])
                                except (ValueError, TypeError):
                                    pass
                    except Exception:
                        pass
        
        return {
            'sessions_last_7_days': recent_sessions,
            'active_users_last_7_days': len(recent_users),
            'avg_sessions_per_day': recent_sessions / 7,
            'cutoff_date': cutoff_date.isoformat()
        }
    
    def _get_improvement_recommendations(self) -> List[str]:
        """Get data improvement recommendations"""
        
        recommendations = []
        
        # Check file counts
        file_stats = self._get_file_stats()
        
        for log_type, stats in file_stats.items():
            if stats['file_count'] == 0:
                recommendations.append(f"Start collecting {log_type} data - no files found")
            elif stats['file_count'] < 5:
                recommendations.append(f"Increase {log_type} data collection - only {stats['file_count']} files")
        
        # Check user diversity
        coverage = self._get_data_coverage_stats()
        
        if coverage['unique_users'] < 3:
            recommendations.append("Recruit more users for better data diversity")
        
        if coverage.get('date_range', {}).get('span_days', 0) < 7:
            recommendations.append("Collect data over longer time periods")
        
        # Check data quality
        integrity = self.validate_data_integrity()
        
        if integrity.get('overall_score', 0) < 75:
            recommendations.append("Improve data quality - multiple validation issues found")
        
        # Check recent activity
        recent = self._get_recent_activity_stats()
        
        if recent['sessions_last_7_days'] < 10:
            recommendations.append("Increase recent data collection activity")
        
        return recommendations[:5]

    # ========================================
    # EVALUATION LOGGING FOR DISSERTATION
    # ========================================
    
    def start_evaluation_session(self, user_name: str) -> str:
        """
        Start an evaluation session for dissertation research.
        
        Args:
            user_name: Combined participant and condition (e.g., 'P01_A', 'P02_B')
            
        Returns:
            evaluation_session_id: Unique identifier for this evaluation session
        """
        if not user_name:
            raise ValueError("User name is required for evaluation session")
        
        # Parse participant and condition from user_name (e.g., "P01_A" -> "P01", "A")
        if '_' in user_name:
            participant_id, condition = user_name.split('_', 1)
        else:
            # Fallback if no underscore
            participant_id = user_name
            condition = "A"
        
        # Create evaluation subdirectory using user_name
        eval_dir = os.path.join(self.config.base_output_dir, "evaluation", user_name)
        Path(eval_dir).mkdir(parents=True, exist_ok=True)
        
        # Start regular session and get session ID
        session_id = self.start_session(user_id=user_name)
        
        # Create evaluation-specific session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eval_session_id = f"{user_name}_{timestamp}"
        
        # Store evaluation context
        self._evaluation_context = {
            'user_name': user_name,
            'participant_id': participant_id,
            'condition': condition,
            'eval_session_id': eval_session_id,
            'eval_dir': eval_dir,
            'regular_session_id': session_id,
            'start_timestamp': time.time(),
            'frame_counter': 0,
            'rep_counter': 0,
            'cue_counter': 0
        }
        
        # Initialize CSV files for evaluation
        self._init_evaluation_csvs()
        
        print(f"🎯 Evaluation session started:")
        print(f"   User: {user_name}")
        print(f"   Participant: {participant_id}, Condition: {condition}")
        print(f"   Session ID: {eval_session_id}")
        print(f"   Output: {eval_dir}")
        
        return eval_session_id
    
    def _init_evaluation_csvs(self):
        """Initialize CSV files for evaluation data collection"""
        eval_dir = self._evaluation_context['eval_dir']
        user_name = self._evaluation_context['user_name']
        
        # Frame-level CSV
        self._eval_frame_csv = os.path.join(eval_dir, f"frames_{user_name}.csv")
        self._eval_frame_headers = [
            'timestamp_ms', 'frame_id', 'pose_confidence', 'fps',
            'knee_left_deg', 'knee_right_deg', 'knee_avg_deg',
            'trunk_angle_deg', 'hip_angle_deg', 'ankle_angle_deg',
            'movement_phase', 'valgus_deviation_deg', 'depth_achieved',
            'trunk_flex_excessive', 'landmarks_visible_count'
        ]
        
        # Rep-level CSV
        self._eval_rep_csv = os.path.join(eval_dir, f"reps_{user_name}.csv")
        self._eval_rep_headers = [
            'rep_id', 'start_timestamp_ms', 'bottom_timestamp_ms', 'end_timestamp_ms',
            'duration_ms', 'min_knee_angle_deg', 'max_trunk_flex_deg', 'max_valgus_dev_deg',
            'depth_fault_flag', 'valgus_fault_flag', 'trunk_fault_flag', 'form_score_percent',
            'stability_index_knee', 'stability_index_trunk', 'aot_valgus_ms_deg',
            'aot_trunk_ms_deg', 'ai_rep_detected'
        ]
        
        # Cue-level CSV
        self._eval_cue_csv = os.path.join(eval_dir, f"cues_{user_name}.csv")
        self._eval_cue_headers = [
            'cue_timestamp_ms', 'rep_id', 'cue_type', 'cue_message',
            'movement_phase_at_cue', 'in_actionable_window', 'reaction_detected',
            'reaction_latency_ms', 'correction_magnitude_deg'
        ]
        
        # Write headers
        self._write_csv_headers(self._eval_frame_csv, self._eval_frame_headers)
        self._write_csv_headers(self._eval_rep_csv, self._eval_rep_headers)
        self._write_csv_headers(self._eval_cue_csv, self._eval_cue_headers)
    
    def log_evaluation_frame(self, frame_data: Dict[str, Any]):
        """Log frame-level data for evaluation analysis"""
        if not hasattr(self, '_evaluation_context'):
            return
            
        timestamp_ms = int(time.time() * 1000)
        frame_id = self._evaluation_context['frame_counter']
        self._evaluation_context['frame_counter'] += 1
        
        # Extract or default frame data
        row = [
            timestamp_ms,
            frame_id,
            frame_data.get('pose_confidence', 0.0),
            frame_data.get('fps', 0),
            frame_data.get('knee_left_deg', 0),
            frame_data.get('knee_right_deg', 0),
            frame_data.get('knee_avg_deg', 0.0),
            frame_data.get('trunk_angle_deg', 0),
            frame_data.get('hip_angle_deg', 0),
            frame_data.get('ankle_angle_deg', 0),
            frame_data.get('movement_phase', 'standing'),
            frame_data.get('valgus_deviation_deg', 0),
            frame_data.get('depth_achieved', 0),
            frame_data.get('trunk_flex_excessive', 0),
            frame_data.get('landmarks_visible_count', 33)
        ]
        
        self._append_csv_row(self._eval_frame_csv, row)
    
    def log_evaluation_rep(self, rep_data: Dict[str, Any]):
        """Log rep-level data for evaluation analysis"""
        if not hasattr(self, '_evaluation_context'):
            return
            
        rep_id = self._evaluation_context['rep_counter'] + 1
        self._evaluation_context['rep_counter'] = rep_id
        
        # Extract or default rep data
        row = [
            rep_id,
            rep_data.get('start_timestamp_ms', int(time.time() * 1000)),
            rep_data.get('bottom_timestamp_ms', int(time.time() * 1000)),
            rep_data.get('end_timestamp_ms', int(time.time() * 1000)),
            rep_data.get('duration_ms', 0),
            rep_data.get('min_knee_angle_deg', 180),
            rep_data.get('max_trunk_flex_deg', 0),
            rep_data.get('max_valgus_dev_deg', 0),
            rep_data.get('depth_fault_flag', 0),
            rep_data.get('valgus_fault_flag', 0),
            rep_data.get('trunk_fault_flag', 0),
            rep_data.get('form_score_percent', 85),
            rep_data.get('stability_index_knee', 0.0),
            rep_data.get('stability_index_trunk', 0.0),
            rep_data.get('aot_valgus_ms_deg', 0),
            rep_data.get('aot_trunk_ms_deg', 0),
            rep_data.get('ai_rep_detected', 1)
        ]
        
        self._append_csv_row(self._eval_rep_csv, row)
        return rep_id
    
    def log_evaluation_cue(self, cue_data: Dict[str, Any]):
        """Log cue/feedback data for evaluation analysis"""
        if not hasattr(self, '_evaluation_context'):
            return
            
        cue_id = self._evaluation_context['cue_counter'] + 1
        self._evaluation_context['cue_counter'] = cue_id
        
        # Extract or default cue data
        row = [
            cue_data.get('cue_timestamp_ms', int(time.time() * 1000)),
            cue_data.get('rep_id', self._evaluation_context['rep_counter']),
            cue_data.get('cue_type', 'general'),
            cue_data.get('cue_message', 'Feedback given'),
            cue_data.get('movement_phase_at_cue', 'DESCENT'),
            cue_data.get('in_actionable_window', 1),
            cue_data.get('reaction_detected', 0),
            cue_data.get('reaction_latency_ms', 0),
            cue_data.get('correction_magnitude_deg', 0)
        ]
        
        self._append_csv_row(self._eval_cue_csv, row)
        return cue_id
    
    def finalize_evaluation_session(self):
        """Finalize evaluation session and save metadata"""
        if not hasattr(self, '_evaluation_context'):
            return
            
        # Create metadata file
        eval_dir = self._evaluation_context['eval_dir']
        user_name = self._evaluation_context['user_name']
        metadata_file = os.path.join(eval_dir, f"metadata_{user_name}.json")
        
        metadata = {
            'user_name': user_name,
            'participant_id': self._evaluation_context['participant_id'],
            'condition': self._evaluation_context['condition'],
            'session_start': self._evaluation_context['start_timestamp'],
            'session_end': time.time(),
            'duration_seconds': time.time() - self._evaluation_context['start_timestamp'],
            'total_frames': self._evaluation_context['frame_counter'],
            'total_reps': self._evaluation_context['rep_counter'],
            'total_cues': self._evaluation_context['cue_counter'],
            'thresholds': {
                'depth_knee_angle_deg': 100,
                'valgus_deviation_deg': 10,
                'trunk_flex_deg': 40,
                'pose_confidence_min': 0.5
            }
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Evaluation session finalized:")
        print(f"   Frames logged: {self._evaluation_context['frame_counter']}")
        print(f"   Reps logged: {self._evaluation_context['rep_counter']}")
        print(f"   Cues logged: {self._evaluation_context['cue_counter']}")
        print(f"   Duration: {metadata['duration_seconds']:.1f}s")
        
        # Clean up evaluation context
        delattr(self, '_evaluation_context')
        
        return metadata
    
    def _write_csv_headers(self, filepath: str, headers: List[str]):
        """Write CSV headers to file"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _append_csv_row(self, filepath: str, row: List[Any]):
        """Append a row to CSV file"""
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
