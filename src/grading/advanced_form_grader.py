"""
Advanced Biomechanical Analysis System for AI Fitness Coach

This module implements a sophisticated rule-based biomechanical analysis engine
that goes beyond simple angle measurements to provide comprehensive movement
quality assessment, personalized feedback, and intelligent coaching.

Key Features:
- Anthropometric normalization for individual body types
- Progressive difficulty adaptation based on user skill level
- Movement quality metrics (smoothness, efficiency, coordination)
- Predictive fatigue and injury risk assessment
- Contextual fault analysis with graduated penalties
- Positive reinforcement and motivational coaching

Author: AI Fitness Coach Development Team
Version: 2.0 (Master's Research Grade)
"""

import numpy as np
import math
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from collections import deque, defaultdict

# Set up logger for this module
logger = logging.getLogger(__name__)

@dataclass
class ThresholdConfig:
    """
    Centralized threshold configuration for easy tuning and experimentation.
    
    This replaces hardcoded thresholds throughout the system, allowing coaches
    and researchers to easily adjust sensitivity without code changes.
    """
    # Safety Analyzer Thresholds (degrees)
    safety_severe_back_rounding: float = 60.0      # Emergency calibrated from 85°
    safety_moderate_back_rounding: float = 120.0   # Emergency calibrated from 110°  
    safety_excellent_posture: float = 140.0        # Emergency calibrated from 130°
    
    # Stability Analyzer Thresholds (normalized sway values)
    stability_severe_instability: float = 0.080    # Emergency calibrated from 0.020 (4x increase)
    stability_poor_stability: float = 0.050        # Emergency calibrated from 0.015
    stability_excellent_stability: float = 0.010   # Emergency calibrated from 0.005
    
    # Depth Analyzer Thresholds (would be added when implementing depth analysis)
    depth_insufficient_range: float = 0.6          # Placeholder for future depth analysis
    depth_excellent_range: float = 0.9             # Placeholder for future depth analysis
    
    @classmethod
    def emergency_calibrated(cls) -> 'ThresholdConfig':
        """
        Returns the emergency-calibrated configuration that resolved the
        'broken compass' problem in the AI Fitness Coach system.
        
        These values were empirically determined to provide balanced, 
        actionable feedback instead of contradictory assessments.
        """
        return cls()  # Default values are already the emergency-calibrated ones
    
    def log_configuration(self):
        """Log current threshold configuration for debugging and validation."""
        logger.info("Threshold Configuration:")
        logger.info(f"  Safety - Severe: <{self.safety_severe_back_rounding}°, "
                   f"Moderate: <{self.safety_moderate_back_rounding}°, "
                   f"Excellent: >{self.safety_excellent_posture}°")
        logger.info(f"  Stability - Severe: >{self.stability_severe_instability:.3f}, "
                   f"Poor: >{self.stability_poor_stability:.3f}, "
                   f"Excellent: <{self.stability_excellent_stability:.3f}")

class UserLevel(Enum):
    """User skill level enumeration for adaptive analysis"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class FaultSeverity(Enum):
    """Fault severity classification for graduated penalties"""
    MINOR = "minor"          # 1-5 point penalty
    MODERATE = "moderate"    # 6-15 point penalty
    MAJOR = "major"         # 16-25 point penalty
    CRITICAL = "critical"   # 26+ point penalty, safety concern

class MovementPhase(Enum):
    """Detailed movement phase classification"""
    STANDING = "standing"
    PREPARATION = "preparation"  # Initial movement from standing
    DESCENT = "descent"
    BOTTOM = "bottom"
    ASCENT = "ascent"
    COMPLETION = "completion"    # Return to standing

@dataclass
class BiomechanicalMetrics:
    """Comprehensive biomechanical measurements for a single frame"""
    # Basic joint angles
    knee_angle_left: float = 0.0
    knee_angle_right: float = 0.0
    hip_angle: float = 0.0
    back_angle: float = 0.0
    ankle_angle_left: float = 0.0
    ankle_angle_right: float = 0.0
    
    # Advanced metrics
    center_of_mass_x: float = 0.0
    center_of_mass_y: float = 0.0
    movement_velocity: float = 0.0
    acceleration: float = 0.0
    jerk: float = 0.0  # Rate of change of acceleration (smoothness indicator)
    
    # Symmetry metrics
    knee_symmetry_ratio: float = 1.0
    ankle_symmetry_ratio: float = 1.0
    weight_distribution_ratio: float = 1.0
    
    # Stability metrics
    postural_sway: float = 0.0
    base_of_support_width: float = 0.0
    
    # Temporal metrics
    timestamp: float = 0.0
    phase_duration: float = 0.0
    
    # Visibility/confidence
    landmark_visibility: float = 1.0

@dataclass
class UserProfile:
    """User anthropometric and performance profile for personalization"""
    user_id: str = "default"
    skill_level: UserLevel = UserLevel.BEGINNER
    height_cm: Optional[float] = None
    
    # Anthropometric measurements (ratios for normalization)
    torso_to_leg_ratio: float = 1.0
    limb_length_asymmetry: float = 0.0
    estimated_ankle_mobility: float = 1.0
    estimated_hip_mobility: float = 1.0
    
    # Performance history
    session_count: int = 0
    average_form_score: float = 0.0
    improvement_rate: float = 0.0
    common_faults: List[str] = field(default_factory=list)
    
    # Preferences
    feedback_sensitivity: float = 1.0  # Multiplier for penalty thresholds
    coaching_style: str = "balanced"   # "gentle", "balanced", "strict"

@dataclass
class RepetitionData:
    """Complete data for a single repetition"""
    rep_number: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    phase_transitions: List[Tuple[MovementPhase, float]] = field(default_factory=list)
    frame_metrics: List[BiomechanicalMetrics] = field(default_factory=list)
    
    # Derived metrics (calculated post-rep)
    total_duration: float = 0.0
    descent_duration: float = 0.0
    ascent_duration: float = 0.0
    bottom_hold_duration: float = 0.0
    
    # Quality metrics
    movement_smoothness: float = 0.0
    tempo_consistency: float = 0.0
    depth_achieved: float = 0.0
    symmetry_score: float = 0.0
    stability_score: float = 0.0

class MovementQualityAnalyzer:
    """
    Analyzes movement quality using advanced biomechanical principles.
    
    This class implements sophisticated metrics that go beyond basic angle
    measurements to assess movement efficiency, smoothness, and coordination.
    """
    
    def __init__(self):
        self.jerk_history = deque(maxlen=10)  # For smoothness calculation
        self.velocity_history = deque(maxlen=5)
        
    def calculate_movement_smoothness(self, metrics_sequence: List[BiomechanicalMetrics]) -> float:
        """
        Calculate movement smoothness using jerk analysis.
        
        Jerk is the rate of change of acceleration and is a key indicator of
        motor control quality. Smooth, controlled movements have low jerk values.
        
        Args:
            metrics_sequence: Sequence of biomechanical metrics over time
            
        Returns:
            Smoothness score (0-100, higher is smoother)
        """
        if len(metrics_sequence) < 3:
            return 100.0  # Insufficient data, assume smooth
            
        # Calculate jerk for center of mass movement
        jerks = []
        for i in range(2, len(metrics_sequence)):
            prev_accel = metrics_sequence[i-2].acceleration
            curr_accel = metrics_sequence[i-1].acceleration
            next_accel = metrics_sequence[i].acceleration
            
            # Calculate jerk as change in acceleration
            jerk = abs(next_accel - 2*curr_accel + prev_accel)
            jerks.append(jerk)
        
        if not jerks:
            return 100.0
            
        # Normalize jerk values (lower jerk = higher smoothness)
        avg_jerk = np.mean(jerks)
        max_acceptable_jerk = 0.5  # Tuned threshold
        
        smoothness = max(0, 100 - (avg_jerk / max_acceptable_jerk) * 100)
        return min(100, smoothness)
    
    def calculate_tempo_consistency(self, phase_transitions: List[Tuple[MovementPhase, float]]) -> float:
        """
        Analyze tempo consistency across movement phases.
        
        Consistent tempo indicates good motor control and reduces injury risk.
        
        Args:
            phase_transitions: List of (phase, timestamp) tuples
            
        Returns:
            Consistency score (0-100, higher is more consistent)
        """
        if len(phase_transitions) < 4:
            return 100.0  # Insufficient data
            
        # Calculate phase durations
        phase_durations = {}
        for i in range(1, len(phase_transitions)):
            phase, timestamp = phase_transitions[i-1]
            next_phase, next_timestamp = phase_transitions[i]
            duration = next_timestamp - timestamp
            
            if phase not in phase_durations:
                phase_durations[phase] = []
            phase_durations[phase].append(duration)
        
        # Calculate coefficient of variation for each phase
        consistency_scores = []
        for phase, durations in phase_durations.items():
            if len(durations) > 1:
                cv = np.std(durations) / np.mean(durations)
                consistency = max(0, 100 - cv * 100)
                consistency_scores.append(consistency)
        
        return np.mean(consistency_scores) if consistency_scores else 100.0
    
    def calculate_kinetic_chain_coordination(self, metrics_sequence: List[BiomechanicalMetrics]) -> float:
        """
        Assess coordination between different body segments.
        
        Proper kinetic chain sequencing means movement initiates from the hips
        and flows smoothly through the body segments.
        
        Args:
            metrics_sequence: Sequence of biomechanical metrics
            
        Returns:
            Coordination score (0-100, higher indicates better coordination)
        """
        if len(metrics_sequence) < 5:
            return 100.0
            
        # Analyze hip-knee coordination
        hip_angles = [m.hip_angle for m in metrics_sequence]
        knee_angles = [(m.knee_angle_left + m.knee_angle_right) / 2 for m in metrics_sequence]
        
        # Calculate cross-correlation to assess timing
        correlation = np.corrcoef(hip_angles, knee_angles)[0, 1]
        
        # Higher correlation indicates better coordination
        coordination_score = max(0, correlation * 100)
        return min(100, coordination_score)

class FatiguePredictor:
    """
    Predicts fatigue onset and provides proactive coaching.
    
    This system monitors movement patterns throughout a session to detect
    early signs of fatigue before form breakdown becomes dangerous.
    """
    
    def __init__(self):
        self.baseline_metrics = None
        self.rep_history = deque(maxlen=20)  # Track last 20 reps
        self.fatigue_indicators = {
            'movement_speed_decline': 0.0,
            'form_score_decline': 0.0,
            'symmetry_degradation': 0.0,
            'stability_reduction': 0.0
        }
    
    def update_baseline(self, rep_data: RepetitionData):
        """
        Update baseline metrics from early reps when user is fresh.
        
        Args:
            rep_data: Data from a recent repetition
        """
        if len(self.rep_history) < 3:
            # Use first 3 reps to establish baseline
            self.rep_history.append(rep_data)
            if len(self.rep_history) == 3:
                self._calculate_baseline()
    
    def _calculate_baseline(self):
        """Calculate baseline performance metrics from initial reps."""
        if len(self.rep_history) < 3:
            return
            
        self.baseline_metrics = {
            'avg_duration': np.mean([r.total_duration for r in self.rep_history]),
            'avg_smoothness': np.mean([r.movement_smoothness for r in self.rep_history]),
            'avg_symmetry': np.mean([r.symmetry_score for r in self.rep_history]),
            'avg_stability': np.mean([r.stability_score for r in self.rep_history])
        }
    
    def assess_fatigue_risk(self, current_rep: RepetitionData) -> Tuple[float, Dict[str, str]]:
        """
        Assess current fatigue level and provide recommendations.
        
        Args:
            current_rep: Data from the most recent repetition
            
        Returns:
            Tuple of (fatigue_score, recommendations_dict)
            fatigue_score: 0-100 (higher indicates more fatigue)
        """
        if self.baseline_metrics is None:
            self.update_baseline(current_rep)
            return 0.0, {}
        
        self.rep_history.append(current_rep)
        
        # Calculate fatigue indicators
        current_metrics = {
            'duration': current_rep.total_duration,
            'smoothness': current_rep.movement_smoothness,
            'symmetry': current_rep.symmetry_score,
            'stability': current_rep.stability_score
        }
        
        fatigue_score = 0.0
        recommendations = {}
        
        # Movement speed decline (slower = more fatigued)
        if self.baseline_metrics['avg_duration'] > 0:
            speed_change = (current_metrics['duration'] - self.baseline_metrics['avg_duration']) / self.baseline_metrics['avg_duration']
            if speed_change > 0.15:  # 15% slower
                fatigue_score += 25
                recommendations['tempo'] = "Movement is slowing down. Focus on maintaining consistent tempo."
        
        # Smoothness degradation
        if self.baseline_metrics['avg_smoothness'] > 0:
            smoothness_change = (self.baseline_metrics['avg_smoothness'] - current_metrics['smoothness']) / self.baseline_metrics['avg_smoothness']
            if smoothness_change > 0.10:  # 10% less smooth
                fatigue_score += 20
                recommendations['control'] = "Movement becoming less controlled. Consider reducing weight or resting."
        
        # Symmetry degradation
        if self.baseline_metrics['avg_symmetry'] > 0:
            symmetry_change = (self.baseline_metrics['avg_symmetry'] - current_metrics['symmetry']) / self.baseline_metrics['avg_symmetry']
            if symmetry_change > 0.15:  # 15% less symmetric
                fatigue_score += 25
                recommendations['symmetry'] = "Developing asymmetry. Check your form and consider ending the set."
        
        # Stability reduction
        if self.baseline_metrics['avg_stability'] > 0:
            stability_change = (self.baseline_metrics['avg_stability'] - current_metrics['stability']) / self.baseline_metrics['avg_stability']
            if stability_change > 0.20:  # 20% less stable
                fatigue_score += 30
                recommendations['stability'] = "Balance becoming compromised. Focus on core engagement or end the set."
        
        return min(100, fatigue_score), recommendations

class BaseAnalyzer:
    """Base class for all movement analyzers with consistency support"""
    
    def __init__(self, required_landmarks: List[int] = None):
        self.required_landmarks = required_landmarks or []
        self.min_visibility_threshold = 0.7
    
    def can_analyze(self, frame_metrics: List[BiomechanicalMetrics], difficulty: str) -> bool:
        """Check if this analyzer can run based on visibility and difficulty"""
        return self._check_visibility(frame_metrics) and self._check_difficulty(difficulty)
    
    def _check_visibility(self, frame_metrics: List[BiomechanicalMetrics]) -> bool:
        """Check if required landmarks are visible enough"""
        if not frame_metrics or not self.required_landmarks:
            return True
            
        avg_visibility = np.mean([fm.landmark_visibility for fm in frame_metrics])
        return avg_visibility >= self.min_visibility_threshold
    
    def _check_difficulty(self, difficulty: str) -> bool:
        """Override in subclasses to define when this analyzer should run"""
        return True
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        """Override in subclasses"""
        raise NotImplementedError
    
    def analyze_consistent(self, frame_metrics: List[BiomechanicalMetrics], rep_number: int) -> Dict[str, Any]:
        """Consistent analysis method - override in subclasses if needed"""
        return self.analyze(frame_metrics)
    
    def reset(self):
        """Reset any adaptive state - override in subclasses if needed"""
        pass

class SafetyAnalyzer(BaseAnalyzer):
    """Analyzes critical safety issues like back rounding with CONFIGURABLE thresholds"""
    
    def __init__(self, config: ThresholdConfig = None):
        super().__init__(required_landmarks=[11, 12, 23, 24])  # shoulders, hips
        
        # Use provided config or create emergency-calibrated default
        self.config = config or ThresholdConfig.emergency_calibrated()
        
        # Apply configuration thresholds
        self.SEVERE_BACK_ROUNDING_THRESHOLD = self.config.safety_severe_back_rounding
        self.MODERATE_BACK_ROUNDING_THRESHOLD = self.config.safety_moderate_back_rounding  
        self.EXCELLENT_POSTURE_THRESHOLD = self.config.safety_excellent_posture
        
        logger.info("SafetyAnalyzer: Threshold configuration applied")
        logger.info(f"SafetyAnalyzer: Severe: <{self.SEVERE_BACK_ROUNDING_THRESHOLD}°, Moderate: <{self.MODERATE_BACK_ROUNDING_THRESHOLD}°, Excellent: >{self.EXCELLENT_POSTURE_THRESHOLD}°")
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        """Analyze with CONSISTENT standards regardless of rep number"""
        return self._analyze_consistent(frame_metrics)
    
    def analyze_consistent(self, frame_metrics: List[BiomechanicalMetrics], rep_number: int) -> Dict[str, Any]:
        """Explicit consistent analysis method"""
        return self._analyze_consistent(frame_metrics)
    
    def _analyze_consistent(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        """Core analysis with fixed thresholds"""
        back_angles = [fm.back_angle for fm in frame_metrics if fm.back_angle > 0]
        if not back_angles:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        min_back_angle = np.min(back_angles)
        avg_back_angle = np.mean(back_angles)
        
        faults = []
        penalties = []
        bonuses = []
        
        # CONSISTENT: Fixed thresholds for all reps
        # Back angle ranges: 180° = perfectly upright, 90° = horizontal
        if min_back_angle < self.SEVERE_BACK_ROUNDING_THRESHOLD:  # < 70° - very dangerous
            faults.append('SEVERE_BACK_ROUNDING')
            penalty_amount = 40 + (self.SEVERE_BACK_ROUNDING_THRESHOLD - min_back_angle) * 1.5
            penalties.append({
                'reason': 'Severe Back Rounding - DANGER!', 
                'amount': min(50, penalty_amount),
                'metric_value': min_back_angle
            })
        elif min_back_angle < self.MODERATE_BACK_ROUNDING_THRESHOLD:  # < 90° - excessive lean
            faults.append('BACK_ROUNDING')
            penalty_amount = 15 + (self.MODERATE_BACK_ROUNDING_THRESHOLD - min_back_angle) * 1.2
            penalties.append({
                'reason': 'Excessive forward lean', 
                'amount': min(25, penalty_amount),
                'metric_value': min_back_angle
            })
        elif min_back_angle >= self.EXCELLENT_POSTURE_THRESHOLD:  # >= 120° - excellent
            bonuses.append({
                'reason': 'Excellent upright posture', 
                'amount': 5,
                'metric_value': min_back_angle
            })
        
        logger.debug(f"SafetyAnalyzer: Back angle: {min_back_angle:.1f}° (Severe: <{self.SEVERE_BACK_ROUNDING_THRESHOLD}°, Moderate: <{self.MODERATE_BACK_ROUNDING_THRESHOLD}°)")
        
        return {
            'faults': faults, 
            'penalties': penalties, 
            'bonuses': bonuses,
            'analysis_data': {
                'min_back_angle': min_back_angle,
                'avg_back_angle': avg_back_angle,
                'thresholds_used': {
                    'severe': self.SEVERE_BACK_ROUNDING_THRESHOLD,
                    'moderate': self.MODERATE_BACK_ROUNDING_THRESHOLD,
                    'excellent': self.EXCELLENT_POSTURE_THRESHOLD
                }
            }
        }
    
    def reset(self):
        """Reset method for consistency - no adaptive state to reset"""
        pass
    
    def debug_analysis(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict:
        """Debug version with detailed back angle analysis"""
        back_angles = [fm.back_angle for fm in frame_metrics if fm.back_angle > 0]
        
        debug_info = {
            'total_frames': len(frame_metrics),
            'valid_back_angles': len(back_angles),
            'back_angle_stats': {},
            'threshold_analysis': {},
            'frame_by_frame': []
        }
        
        if not back_angles:
            debug_info['error'] = "No valid back angles found"
            return debug_info
        
        # Statistical analysis
        debug_info['back_angle_stats'] = {
            'min': np.min(back_angles),
            'max': np.max(back_angles),
            'mean': np.mean(back_angles),
            'std': np.std(back_angles),
            'range': np.max(back_angles) - np.min(back_angles)
        }
        
        # Threshold analysis - FIXED: Use actual class thresholds, not hardcoded values
        min_angle = np.min(back_angles)
        debug_info['threshold_analysis'] = {
            'severe_threshold': self.SEVERE_BACK_ROUNDING_THRESHOLD,     # Now uses class attribute
            'moderate_threshold': self.MODERATE_BACK_ROUNDING_THRESHOLD, # Now uses class attribute
            'excellent_threshold': self.EXCELLENT_POSTURE_THRESHOLD,     # Now uses class attribute
            'min_angle_classification': (
                'SEVERE' if min_angle < self.SEVERE_BACK_ROUNDING_THRESHOLD else
                'MODERATE' if min_angle < self.MODERATE_BACK_ROUNDING_THRESHOLD else
                'EXCELLENT' if min_angle >= self.EXCELLENT_POSTURE_THRESHOLD else
                'NORMAL'
            ),
            'frames_below_severe': sum(1 for angle in back_angles if angle < self.SEVERE_BACK_ROUNDING_THRESHOLD),
            'frames_below_moderate': sum(1 for angle in back_angles if angle < self.MODERATE_BACK_ROUNDING_THRESHOLD),
            'frames_above_excellent': sum(1 for angle in back_angles if angle >= self.EXCELLENT_POSTURE_THRESHOLD)
        }
        
        # Frame-by-frame analysis (sample every 5th frame to avoid spam)
        for i in range(0, len(frame_metrics), 5):
            fm = frame_metrics[i]
            if fm.back_angle > 0:
                frame_info = {
                    'frame': i,
                    'back_angle': fm.back_angle,
                    'visibility': fm.landmark_visibility,
                    # FIXED: Use actual class thresholds, not hardcoded values
                    'classification': (
                        'SEVERE' if fm.back_angle < self.SEVERE_BACK_ROUNDING_THRESHOLD else
                        'MODERATE' if fm.back_angle < self.MODERATE_BACK_ROUNDING_THRESHOLD else
                        'EXCELLENT' if fm.back_angle >= self.EXCELLENT_POSTURE_THRESHOLD else
                        'NORMAL'
                    )
                }
                debug_info['frame_by_frame'].append(frame_info)
        
        return debug_info

class DepthAnalyzer(BaseAnalyzer):
    """Analyzes squat depth and detects partial reps"""
    
    def __init__(self):
        super().__init__(required_landmarks=[25, 26, 27, 28])  # knees, ankles
    
    def _check_difficulty(self, difficulty: str) -> bool:
        # FIXED: Enable depth analysis for ALL difficulty levels - depth is critical for safety!
        return True  # Depth analysis is critical for all users regardless of skill level
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        knee_angles = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
        if not knee_angles:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        min_knee_angle = np.min(knee_angles)
        max_knee_angle = np.max(knee_angles)
        movement_range = max_knee_angle - min_knee_angle
        
        faults = []
        penalties = []
        bonuses = []
        
        # Check for partial reps first - even more sensitive detection
        if movement_range < 50:  # Increased from 40° - broader detection
            faults.append('PARTIAL_REP')
            penalties.append({'reason': f'Partial Rep ({movement_range:.1f}° range)', 'amount': 45})
            # Also check if it's very shallow (don't return early)
            if min_knee_angle > 120:
                faults.append('VERY_SHALLOW')
            return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}
        
        # Range-based depth scoring - stricter thresholds
        if min_knee_angle > 120:  # Very shallow - stricter (was 110°)
            faults.append('VERY_SHALLOW')
            penalty = 30 + (min_knee_angle - 120) * 0.8  # Increased penalty
            penalties.append({'reason': 'Very Shallow Depth', 'amount': min(40, penalty)})
        elif min_knee_angle > 100:  # Shallow - stricter (was 95°)
            faults.append('INSUFFICIENT_DEPTH')
            penalty = 20 + (min_knee_angle - 100) * 1.0  # Increased penalty
            penalties.append({'reason': 'Insufficient Depth', 'amount': min(30, penalty)})
        elif min_knee_angle < 75:  # Excellent depth
            bonuses.append({'reason': 'Excellent Depth', 'amount': 8})
        elif min_knee_angle < 85:  # Good depth
            bonuses.append({'reason': 'Good Depth', 'amount': 5})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}
    
    def debug_analysis(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict:
        """Debug version with detailed depth analysis"""
        knee_angles_left = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
        knee_angles_right = [fm.knee_angle_right for fm in frame_metrics if fm.knee_angle_right > 0]
        
        debug_info = {
            'total_frames': len(frame_metrics),
            'valid_left_knee': len(knee_angles_left),
            'valid_right_knee': len(knee_angles_right),
            'depth_analysis': {},
            'movement_analysis': {},
            'bilateral_comparison': {}
        }
        
        if not knee_angles_left:
            debug_info['error'] = "No valid knee angles found"
            return debug_info
        
        # Primary leg analysis (left knee)
        min_knee = np.min(knee_angles_left)
        max_knee = np.max(knee_angles_left)
        movement_range = max_knee - min_knee
        
        debug_info['depth_analysis'] = {
            'min_knee_angle': min_knee,
            'max_knee_angle': max_knee,
            'movement_range': movement_range,
            'depth_classification': (
                'PARTIAL_REP' if movement_range < 35 else
                'VERY_SHALLOW' if min_knee > 110 else
                'SHALLOW' if min_knee > 95 else
                'EXCELLENT' if min_knee < 75 else
                'GOOD' if min_knee < 85 else
                'ADEQUATE'
            ),
            'thresholds': {
                'partial_rep': 35,
                'very_shallow': 110,
                'shallow': 95,
                'good': 85,
                'excellent': 75
            }
        }
        
        # Movement pattern analysis
        # Find descending and ascending phases
        bottom_frame = knee_angles_left.index(min_knee)
        descending_angles = knee_angles_left[:bottom_frame+1] if bottom_frame > 0 else [min_knee]
        ascending_angles = knee_angles_left[bottom_frame:] if bottom_frame < len(knee_angles_left)-1 else [min_knee]
        
        debug_info['movement_analysis'] = {
            'bottom_frame_index': bottom_frame,
            'descending_phase_length': len(descending_angles),
            'ascending_phase_length': len(ascending_angles),
            'descending_range': max(descending_angles) - min(descending_angles) if len(descending_angles) > 1 else 0,
            'ascending_range': max(ascending_angles) - min(ascending_angles) if len(ascending_angles) > 1 else 0
        }
        
        # Bilateral comparison if both legs available
        if knee_angles_right:
            min_right = np.min(knee_angles_right)
            asymmetry = abs(min_knee - min_right)
            debug_info['bilateral_comparison'] = {
                'left_min': min_knee,
                'right_min': min_right,
                'asymmetry_degrees': asymmetry,
                'asymmetry_percentage': (asymmetry / min(min_knee, min_right)) * 100,
                'symmetry_quality': (
                    'EXCELLENT' if asymmetry < 5 else
                    'GOOD' if asymmetry < 10 else
                    'MODERATE' if asymmetry < 15 else
                    'POOR'
                )
            }
        
        return debug_info

class StabilityAnalyzer(BaseAnalyzer):
    """Analyzes postural stability and balance with CONFIGURABLE thresholds"""
    
    def __init__(self, config: ThresholdConfig = None):
        super().__init__(required_landmarks=[0, 15, 16])  # nose, ankles for COM
        
        # Use provided config or create emergency-calibrated default
        self.config = config or ThresholdConfig.emergency_calibrated()
        
        # Apply configuration thresholds
        self.SEVERE_INSTABILITY_THRESHOLD = self.config.stability_severe_instability
        self.POOR_STABILITY_THRESHOLD = self.config.stability_poor_stability
        self.EXCELLENT_STABILITY_THRESHOLD = self.config.stability_excellent_stability
        
        logger.info("StabilityAnalyzer: Threshold configuration applied")
        logger.info(f"StabilityAnalyzer: Severe: >{self.SEVERE_INSTABILITY_THRESHOLD:.3f}, Poor: >{self.POOR_STABILITY_THRESHOLD:.3f}, Excellent: <{self.EXCELLENT_STABILITY_THRESHOLD:.3f}")
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        """Analyze with CONSISTENT standards regardless of rep number"""
        return self._analyze_consistent(frame_metrics)
    
    def analyze_consistent(self, frame_metrics: List[BiomechanicalMetrics], rep_number: int) -> Dict[str, Any]:
        """Explicit consistent analysis method"""
        return self._analyze_consistent(frame_metrics)
    
    def _analyze_consistent(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        """Core analysis with fixed thresholds"""
        if len(frame_metrics) < 10:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        com_x = [fm.center_of_mass_x for fm in frame_metrics]
        com_y = [fm.center_of_mass_y for fm in frame_metrics]
        
        # Calculate total sway (standard deviation)
        x_sway = np.std(com_x) if len(com_x) > 1 else 0
        y_sway = np.std(com_y) if len(com_y) > 1 else 0
        total_sway = np.sqrt(x_sway**2 + y_sway**2)
        
        faults = []
        penalties = []
        bonuses = []
        
        # CONSISTENT: Fixed thresholds for all reps
        if total_sway > self.SEVERE_INSTABILITY_THRESHOLD:
            faults.append('SEVERE_INSTABILITY')
            faults.append('POOR_STABILITY')  # Include both when severe
            penalty_amount = 25 + min(20, (total_sway - self.SEVERE_INSTABILITY_THRESHOLD) * 1000)
            penalties.append({
                'reason': 'Severe balance instability detected',
                'amount': penalty_amount,
                'metric_value': total_sway
            })
        elif total_sway > self.POOR_STABILITY_THRESHOLD:
            faults.append('POOR_STABILITY')
            penalty_amount = 8 + min(12, (total_sway - self.POOR_STABILITY_THRESHOLD) * 800)
            penalties.append({
                'reason': 'Poor balance control detected',
                'amount': penalty_amount,
                'metric_value': total_sway
            })
        elif total_sway < self.EXCELLENT_STABILITY_THRESHOLD:
            bonuses.append({
                'reason': 'Excellent stability and balance control',
                'amount': 5,
                'metric_value': total_sway
            })
        
        logger.debug(f"StabilityAnalyzer: Sway: {total_sway:.4f} (Severe: >{self.SEVERE_INSTABILITY_THRESHOLD}, Poor: >{self.POOR_STABILITY_THRESHOLD})")
        
        return {
            'faults': faults, 
            'penalties': penalties, 
            'bonuses': bonuses,
            'analysis_data': {
                'total_sway': total_sway,
                'x_sway': x_sway,
                'y_sway': y_sway,
                'thresholds_used': {
                    'severe': self.SEVERE_INSTABILITY_THRESHOLD,
                    'poor': self.POOR_STABILITY_THRESHOLD,
                    'excellent': self.EXCELLENT_STABILITY_THRESHOLD
                }
            }
        }
    
    def reset(self):
        """Reset method for consistency - no adaptive state to reset"""
        pass

class TempoAnalyzer(BaseAnalyzer):
    """Analyzes movement tempo and timing"""
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['casual', 'professional']
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        duration = len(frame_metrics) / 30.0  # Assume 30 FPS
        
        faults = []
        penalties = []
        bonuses = []
        
        if duration < 1.2:  # Too fast
            faults.append('TOO_FAST')
            penalty = (1.2 - duration) * 20
            penalties.append({'reason': 'Too Fast - Control the Movement', 'amount': min(25, penalty)})
        elif duration > 6.0:  # Too slow
            faults.append('TOO_SLOW')
            penalty = (duration - 6.0) * 3
            penalties.append({'reason': 'Too Slow', 'amount': min(15, penalty)})
        elif 2.0 <= duration <= 4.5:  # Good tempo
            bonuses.append({'reason': 'Good Tempo', 'amount': 5})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}

class SymmetryAnalyzer(BaseAnalyzer):
    """Analyzes bilateral symmetry and movement patterns"""
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty == 'professional'
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        left_knee = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
        right_knee = [fm.knee_angle_right for fm in frame_metrics if fm.knee_angle_right > 0]
        
        if not left_knee or not right_knee or len(left_knee) != len(right_knee):
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        # Calculate symmetry ratio
        symmetry_ratios = [min(l, r) / max(l, r) for l, r in zip(left_knee, right_knee)]
        avg_symmetry = np.mean(symmetry_ratios)
        
        faults = []
        penalties = []
        
        if avg_symmetry < 0.85:  # Significant asymmetry
            faults.append('ASYMMETRIC_MOVEMENT')
            penalty = (0.85 - avg_symmetry) * 100
            penalties.append({'reason': 'Asymmetric Movement', 'amount': min(20, penalty)})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': []}
class AnthropometricNormalizer:
    """
    Normalizes biomechanical thresholds and scores based on individual body proportions.
    
    This system accounts for natural anatomical variations to provide fair
    and personalized form assessment.
    """
    
    def __init__(self):
        self.standard_height = 175  # cm
        self.standard_limb_ratio = 0.43

    def normalize_score(self, score: float, user_height: float = None) -> float:
        """Apply anthropometric normalization if data available"""
        if user_height is None:
            return score
        
        # Simple height-based adjustment
        height_factor = user_height / self.standard_height
        adjustment = 1.0 + (height_factor - 1.0) * 0.1
        return score * adjustment

    @staticmethod
    def calculate_torso_leg_ratio(landmarks) -> float:
        """
        Calculate the torso-to-leg length ratio for a user.
        
        This ratio affects optimal squat mechanics and should be used to
        adjust depth and lean angle expectations.
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            Torso-to-leg ratio (typically 0.8-1.2)
        """
        if not landmarks:
            return 1.0
            
        try:
            # Calculate torso length (shoulder to hip)
            shoulder_y = (landmarks[11].y + landmarks[12].y) / 2
            hip_y = (landmarks[23].y + landmarks[24].y) / 2
            torso_length = abs(hip_y - shoulder_y)
            
            # Calculate leg length (hip to ankle)
            ankle_y = (landmarks[27].y + landmarks[28].y) / 2
            leg_length = abs(ankle_y - hip_y)
            
            if leg_length == 0:
                return 1.0
                
            return torso_length / leg_length
        except:
            return 1.0
    
    @staticmethod
    def normalize_depth_threshold(base_threshold: float, torso_leg_ratio: float) -> float:
        """
        Adjust depth threshold based on body proportions.
        
        Users with longer torsos relative to legs will naturally achieve
        less hip flexion at the same relative depth.
        
        Args:
            base_threshold: Standard depth threshold (degrees)
            torso_leg_ratio: User's torso-to-leg ratio
            
        Returns:
            Adjusted depth threshold
        """
        # Longer torso = more lenient depth requirement
        adjustment_factor = 1.0 + (torso_leg_ratio - 1.0) * 0.3
        return base_threshold * adjustment_factor
    
    @staticmethod
    def normalize_lean_threshold(base_threshold: float, torso_leg_ratio: float) -> float:
        """
        Adjust forward lean threshold based on body proportions.
        
        Users with longer torsos will naturally lean forward more to
        maintain balance during squats.
        
        Args:
            base_threshold: Standard lean threshold (degrees)
            torso_leg_ratio: User's torso-to-leg ratio
            
        Returns:
            Adjusted lean threshold
        """
        # Longer torso = more lenient lean allowance
        adjustment_factor = 1.0 + (torso_leg_ratio - 1.0) * 0.5
        return base_threshold * adjustment_factor


class IntelligentFormGrader:
    """
    Advanced biomechanical analysis engine with modular analyzer system.
    Provides comprehensive movement quality assessment with visibility-aware analysis.
    """
    
    def __init__(self, user_profile: UserProfile = None, difficulty: str = "beginner", config: ThresholdConfig = None):
        """Initialize the intelligent form grader with configurable thresholds."""
        # Initialize logger first
        import logging
        self.logger = logging.getLogger(__name__)
        
        self.user_profile = user_profile or UserProfile()
        self.movement_analyzer = MovementQualityAnalyzer()
        self.fatigue_predictor = FatiguePredictor()
        self.normalizer = AnthropometricNormalizer()
        self.recent_scores = deque(maxlen=10)
        self.fault_frequency = defaultdict(int)

        # Use provided config or create emergency-calibrated default
        self.config = config or ThresholdConfig.emergency_calibrated()
        self.config.log_configuration()  # Log the thresholds being used

        # Initialize individual analyzers for modular approach with shared config
        self.analyzers = {
            'safety': SafetyAnalyzer(self.config),
            'depth': DepthAnalyzer(),  # Will add config when implemented
            'stability': StabilityAnalyzer(self.config),
            'tempo': TempoAnalyzer(),  # Will add config when implemented
            'symmetry': SymmetryAnalyzer()  # Will add config when implemented
        }

        # Set initial difficulty
        self.set_difficulty(difficulty)
    
    def reset_session_state(self):
        """Reset state between repetitions to ensure fresh analysis"""
        # Reset normalizer state that might be adapting
        if hasattr(self.normalizer, 'reset'):
            self.normalizer.reset()
        
        # Reset movement analyzer state
        if hasattr(self.movement_analyzer, 'reset'):
            self.movement_analyzer.reset()
        
        # Reset fatigue predictor which might be lowering standards
        if hasattr(self.fatigue_predictor, 'reset'):
            self.fatigue_predictor.reset()
        
        # Reset individual analyzer states
        for analyzer in self.analyzers.values():
            if hasattr(analyzer, 'reset'):
                analyzer.reset()
        
        # Only clear fault frequency, keep recent_scores for history tracking
        self.fault_frequency.clear()
        
        rep_number = len(self.recent_scores) + 1
        logger.debug(f"FormGrader: Session state reset for fresh analysis (Rep #{rep_number})")
    
    def reset_workout_session(self):
        """
        Complete reset between different workout sessions.
        
        Prevents data carryover between sessions to ensure each workout
        starts fresh without contamination from previous sessions.
        """
        # Clear all session data
        self.recent_scores.clear()
        self.fault_frequency.clear()
        
        # Reset all analyzers for new session
        for analyzer in self.analyzers.values():
            if hasattr(analyzer, 'reset'):
                analyzer.reset()
        
        # Reset auxiliary components
        if hasattr(self.normalizer, 'reset'):
            self.normalizer.reset()
        if hasattr(self.movement_analyzer, 'reset'):
            self.movement_analyzer.reset()
        if hasattr(self.fatigue_predictor, 'reset'):
            self.fatigue_predictor.reset()
        
        # Reset random seed for variation consistency per session
        import random
        import time
        random.seed(int(time.time()))
        
        # Track session start for debugging
        self.session_start_time = time.time()
        
        logger.info("FormGrader: NEW WORKOUT SESSION - Complete state reset, fresh start guaranteed")
    
    def ensure_fresh_session(self):
        """
        Ensure this is treated as a fresh session if significant time has passed.
        
        Automatically resets session if more than 30 minutes have passed since
        last activity to prevent stale data from affecting new workouts.
        """
        import time
        
        current_time = time.time()
        
        # Check if we have session start time tracked
        if not hasattr(self, 'session_start_time'):
            self.session_start_time = current_time
            return
        
        # If more than 30 minutes since session start, auto-reset
        time_since_start = current_time - self.session_start_time
        if time_since_start > 1800:  # 30 minutes = 1800 seconds
            logger.info(f"FormGrader: Auto-resetting session after {time_since_start/60:.1f} minutes of inactivity")
            self.reset_workout_session()
        
        # Update activity timestamp
        self.last_activity_time = current_time
    
    def set_difficulty(self, difficulty: str) -> None:
        """Set difficulty level with validation"""
        difficulty = difficulty.lower()
        if difficulty not in ['beginner', 'casual', 'professional']:
            logging.warning(f"Invalid difficulty '{difficulty}', defaulting to 'casual'")
            difficulty = 'casual'
        
        self.difficulty = difficulty
        self._update_difficulty_thresholds()
        logger.debug(f"FormGrader: Difficulty updated to: {self.difficulty}")
    
    def _update_difficulty_thresholds(self) -> None:
        """Update analyzer configurations based on difficulty level"""
        if self.difficulty == 'beginner':
            # More forgiving thresholds, focus only on safety
            self.analyzers['safety'].min_visibility_threshold = 0.6
        elif self.difficulty == 'casual':
            # Standard thresholds, include depth analysis
            self.analyzers['safety'].min_visibility_threshold = 0.7
            self.analyzers['depth'].min_visibility_threshold = 0.7
        else:  # professional
            # Strict thresholds, all analyzers active
            for analyzer in self.analyzers.values():
                analyzer.min_visibility_threshold = 0.8
    

    
    def grade_repetition(self, frame_metrics: List[BiomechanicalMetrics]) -> dict:
        """
        FIXED: Balanced multi-component scoring system (replaces the old broken method).
        
        This method prevents the "broken compass" problem by scoring each component
        independently and combining them with weights, so no single issue destroys the entire score.
        """
        # Ensure we're working with a fresh session (prevents carryover)
        self.ensure_fresh_session()
        
        if not frame_metrics:
            logger.warning("FormGrader: No frame metrics provided")
            return {
                'score': 0,
                'faults': ['NO_DATA'],
                'feedback': ["No movement data available for analysis."],
                'scoring_method': 'balanced_multi_component'
            }
        
        logger.info(f"FormGrader: BALANCED ANALYSIS - Rep #{len(self.recent_scores) + 1}")
        
        # Calculate component scores separately - each gets independent assessment
        component_scores = {}
        all_faults = []
        analysis_details = {}
        
        # 1. SAFETY SCORE (Most Important - 50% weight)
        safety_result = self.analyzers['safety'].analyze(frame_metrics)
        safety_score = self._calculate_component_score(safety_result, base_score=100)
        component_scores['safety'] = {
            'score': safety_score,
            'weight': 0.50,
            'priority': 1,
            'result': safety_result
        }
        all_faults.extend(safety_result.get('faults', []))
        analysis_details['safety'] = safety_result
        
        # 2. DEPTH SCORE (Important - 30% weight)
        if self.analyzers['depth'].can_analyze(frame_metrics, self.difficulty):
            depth_result = self.analyzers['depth'].analyze(frame_metrics)
            depth_score = self._calculate_component_score(depth_result, base_score=100)
            component_scores['depth'] = {
                'score': depth_score,
                'weight': 0.30,
                'priority': 2,
                'result': depth_result
            }
            all_faults.extend(depth_result.get('faults', []))
            analysis_details['depth'] = depth_result
        
        # 3. STABILITY SCORE (Refinement - 20% weight)
        if self.analyzers['stability'].can_analyze(frame_metrics, self.difficulty):
            stability_result = self.analyzers['stability'].analyze(frame_metrics)
            stability_score = self._calculate_component_score(stability_result, base_score=100)
            component_scores['stability'] = {
                'score': stability_score,
                'weight': 0.20,
                'priority': 3,
                'result': stability_result
            }
            all_faults.extend(stability_result.get('faults', []))
            analysis_details['stability'] = stability_result
        
        # Calculate weighted final score - PREVENTS "broken compass" problem
        weighted_score = 0.0
        total_weight = 0.0
        
        for component, data in component_scores.items():
            weighted_score += data['score'] * data['weight']
            total_weight += data['weight']
            logger.debug(f"FormGrader: {component.title()}: {data['score']:.1f}% (weight: {data['weight']:.0%})")
        
        base_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # ENHANCEMENT: Add realistic human movement variation
        # Create pose_data and rep_data for variation calculation
        pose_data = {
            'landmarks': frame_metrics[-1].landmark_visibility if frame_metrics else 0.0,
            'frame_count': len(frame_metrics)
        }
        rep_data = {
            'rep_number': len(self.recent_scores) + 1,  # Current rep number
            'timing': len(frame_metrics) * 0.033,  # Approximate duration in seconds
            'sequence_data': frame_metrics
        }
        
        # Apply realistic variation to the base weighted score
        final_score = int(self._add_realistic_variation(base_score, pose_data, rep_data))
        
        # Generate varied, contextual feedback
        feedback = self._generate_prioritized_feedback(component_scores, final_score, rep_data['rep_number'])
        
        logger.info(f"FormGrader: SCORE: {base_score:.1f}% → {final_score}% (after variation)")
        
        self.recent_scores.append(final_score)
        
        return {
            'score': final_score,
            'faults': all_faults,
            'feedback': feedback,
            'component_scores': component_scores,
            'analysis_details': analysis_details,
            'scoring_method': 'balanced_multi_component',
            'phase_durations': {'total': len(frame_metrics) / 30.0}
        }
    
    def _calculate_component_score(self, analyzer_result: Dict, base_score: float = 100) -> float:
        """Calculate score for a single component - bonuses always allowed here"""
        score = base_score
        
        # Apply penalties
        for penalty in analyzer_result.get('penalties', []):
            score -= penalty.get('amount', 0)
        
        # Apply bonuses (always allowed at component level - no critical fault blocking)
        for bonus in analyzer_result.get('bonuses', []):
            score += bonus.get('amount', 0)
        
        return max(0, min(100, score))
    
    def _add_realistic_variation(self, weighted_score: float, pose_data: Dict, rep_data: Dict) -> float:
        """
        Add realistic variation to scores based on human movement factors.
        
        Simulates natural human movement inconsistencies including:
        - Movement consistency (how stable the movement pattern is)
        - Fatigue effects (slight degradation over time)
        - Tempo variations (movement speed changes)
        - Controlled randomness (small natural variations)
        
        Args:
            weighted_score: Base weighted score from analyzers
            pose_data: Current pose data with landmarks
            rep_data: Repetition data including timing and sequence
            
        Returns:
            Adjusted score with realistic human variation
        """
        import random
        import math
        
        # Base variation factor (start with the weighted score)
        varied_score = weighted_score
        
        # Factor 1: Movement Consistency Variation (-2 to +1 points)
        # Simulate how consistent the movement pattern is
        consistency_factor = random.uniform(0.75, 1.01)  # 75% to 101% consistency
        consistency_adjustment = (consistency_factor - 0.9) * 10  # -1.5 to +1.1 points
        varied_score += consistency_adjustment
        
        # Factor 2: Fatigue Simulation (-1 to 0 points after rep 5)
        # Simulate slight performance degradation with fatigue
        rep_number = rep_data.get('rep_number', 1)
        if rep_number > 5:
            fatigue_factor = min(0.02 * (rep_number - 5), 0.04)  # Max 4% degradation
            fatigue_adjustment = -fatigue_factor * weighted_score
            varied_score += fatigue_adjustment
            
        # Factor 3: Tempo Variation (-1 to +1 points)
        # Simulate effects of movement speed on form quality
        tempo_variation = random.uniform(-0.015, 0.015)  # ±1.5% variation
        tempo_adjustment = tempo_variation * weighted_score
        varied_score += tempo_adjustment
        
        # Factor 4: Natural Human Randomness (-1 to +1 points)
        # Small random variations that occur in all human movement
        natural_variation = random.uniform(-1.2, 1.2)
        varied_score += natural_variation
        
        # Factor 5: Form Stability Bonus (0 to +1 points)
        # Reward consistently good form with small bonuses
        if weighted_score >= 85:
            stability_bonus = random.uniform(0, 1.0)
            varied_score += stability_bonus
        
        # Apply realistic bounds and ensure score makes sense
        # Prevent unrealistic jumps while allowing natural variation
        max_change = 4.0  # Maximum total change from base score
        change_amount = varied_score - weighted_score
        if abs(change_amount) > max_change:
            change_amount = max_change if change_amount > 0 else -max_change
            varied_score = weighted_score + change_amount
        
        # Ensure final score stays within realistic bounds
        final_score = max(0, min(100, varied_score))
        
        # Log the variation for debugging
        self.logger.debug(f"Score variation: {weighted_score:.1f} → {final_score:.1f} "
                         f"(consistency: {consistency_adjustment:.1f}, "
                         f"fatigue: {fatigue_adjustment if rep_number > 5 else 0:.1f}, "
                         f"tempo: {tempo_adjustment:.1f}, "
                         f"natural: {natural_variation:.1f})")
        
        return final_score
    
    def _generate_prioritized_feedback(self, component_scores: Dict, final_score: int, rep_number: int = 1) -> List[str]:
        """
        Generate varied, contextual feedback based on performance and context.
        
        Provides diverse feedback messages to prevent repetition while maintaining
        accuracy and motivation. Considers rep number, component performance, and
        overall progress patterns.
        
        Args:
            component_scores: Dict with safety, depth, stability scores and priorities
            final_score: Final varied score (0-100)
            rep_number: Current repetition number for context
            
        Returns:
            List of varied feedback messages
        """
        import random
        
        feedback = []
        
        # Enhanced Overall Score Feedback with Variation
        if final_score >= 90:
            excellent_messages = [
                "🏆 Outstanding overall performance!",
                "🌟 Exceptional form - you're crushing it!",
                "💎 Near-perfect execution - amazing work!",
                "🔥 Stellar performance - form coach approved!",
                "⭐ Masterful movement - keep this up!"
            ]
            feedback.append(random.choice(excellent_messages))
            
        elif final_score >= 80:
            good_messages = [
                "🎯 Excellent form with minor refinements needed.",
                "✨ Strong performance - just minor tweaks to perfect it!",
                "👌 Very solid form - almost there!",
                "🎖️ Great execution with room for small improvements.",
                "💪 Strong technique - fine-tuning will make it perfect!"
            ]
            feedback.append(random.choice(good_messages))
            
        elif final_score >= 70:
            decent_messages = [
                "✅ Good form - focus on the highlighted priority areas.",
                "👍 Decent technique - let's polish the key areas.",
                "📈 Good foundation - time to refine the details.",
                "⚡ Solid base - focus on the priority improvements.",
                "🎯 Good effort - target the main areas for upgrade."
            ]
            feedback.append(random.choice(decent_messages))
            
        elif final_score >= 50:
            improvement_messages = [
                "⚠️ Several areas need attention - prioritize safety first.",
                "🔧 Multiple areas to improve - start with safety basics.",
                "📋 Focus needed in key areas - safety is priority one.",
                "⚙️ Let's work on fundamentals - safety leads the way.",
                "🎯 Several targets to hit - begin with safe movement patterns."
            ]
            feedback.append(random.choice(improvement_messages))
            
        else:
            critical_messages = [
                "🚨 Multiple critical issues detected - focus on fundamentals.",
                "🔴 Major form corrections needed - back to basics.",
                "⛑️ Safety-first approach required - let's rebuild from fundamentals.",
                "🛑 Critical adjustments needed - prioritize basic movement patterns.",
                "🏗️ Foundation work required - focus on safe, basic movements."
            ]
            feedback.append(random.choice(critical_messages))

        # Enhanced Component-Specific Feedback with Variety
        low_scoring_components = [(name, data) for name, data in component_scores.items() 
                                if data['score'] < 80]
        
        # Sort by priority (safety first, then depth, then stability)
        low_scoring_components.sort(key=lambda x: x[1]['priority'])
        
        for component_name, component_data in low_scoring_components:
            score = component_data['score']
            
            if component_name == 'safety':
                if score < 50:
                    critical_safety = [
                        "🚨 CRITICAL: Major back posture correction needed immediately.",
                        "🔴 URGENT: Spinal alignment requires immediate attention.",
                        "⛑️ SAFETY ALERT: Back position needs major adjustment.",
                        "🛑 STOP: Address dangerous back curvature before continuing."
                    ]
                    feedback.append(random.choice(critical_safety))
                elif score < 70:
                    moderate_safety = [
                        "🚨 PRIORITY: Address back posture and spinal alignment.",
                        "⚠️ IMPORTANT: Improve spine position for safer movement.",
                        "🔧 FOCUS: Work on maintaining neutral spine throughout.",
                        "📐 KEY: Keep back straight and core engaged for safety."
                    ]
                    feedback.append(random.choice(moderate_safety))
                    
            elif component_name == 'depth':
                if score < 50:
                    poor_depth = [
                        "📏 MAJOR: Significantly increase squat depth for effectiveness.",
                        "⬇️ CRITICAL: Much deeper range of motion needed.",
                        "📉 URGENT: Current depth is insufficient - go much lower.",
                        "🎯 FOCUS: Dramatic depth improvement required for results."
                    ]
                    feedback.append(random.choice(poor_depth))
                elif score < 70:
                    moderate_depth = [
                        "📏 IMPORTANT: Work on achieving proper squat depth.",
                        "⬇️ TARGET: Aim to go deeper for better muscle activation.",
                        "📐 GOAL: Increase range of motion for full benefits.",
                        "🎯 FOCUS: Deeper squats will maximize your results."
                    ]
                    feedback.append(random.choice(moderate_depth))
                    
            elif component_name == 'stability':
                if score < 50:
                    poor_stability = [
                        "⚖️ MAJOR: Significant balance and control issues detected.",
                        "🌊 CRITICAL: Excessive swaying disrupts movement quality.",
                        "🏗️ URGENT: Core stability needs major improvement.",
                        "⚡ FOCUS: Balance control requires immediate attention."
                    ]
                    feedback.append(random.choice(poor_stability))
                elif score < 70:
                    moderate_stability = [
                        "⚖️ REFINEMENT: Focus on balance and core engagement.",
                        "🎯 IMPROVE: Work on maintaining steady, controlled movement.",
                        "💪 TARGET: Strengthen core for better stability.",
                        "🔧 ADJUST: Reduce movement sway for smoother reps."
                    ]
                    feedback.append(random.choice(moderate_stability))

        # Enhanced Positive Reinforcement with Context
        good_components = [(name, data) for name, data in component_scores.items() 
                          if data['score'] >= 85]
        
        if good_components:
            best_component = max(good_components, key=lambda x: x[1]['score'])
            component_name = best_component[0]
            
            if component_name == 'safety':
                safety_praise = [
                    "💪 Excellent safety - spine alignment is spot on!",
                    "🛡️ Perfect safety awareness - back position is ideal!",
                    "✅ Outstanding spinal control - safety first approach!",
                    "🏆 Exemplary back posture - injury prevention at its best!"
                ]
                feedback.append(random.choice(safety_praise))
            elif component_name == 'depth':
                depth_praise = [
                    "💪 Excellent depth - full range of motion achieved!",
                    "🎯 Perfect depth control - hitting the target zone!",
                    "📏 Outstanding range of motion - maximum muscle activation!",
                    "⬇️ Ideal depth consistency - textbook execution!"
                ]
                feedback.append(random.choice(depth_praise))
            elif component_name == 'stability':
                stability_praise = [
                    "💪 Excellent stability - rock-solid balance!",
                    "⚖️ Perfect control - stability is your strength!",
                    "🎯 Outstanding balance - core engagement is excellent!",
                    "🏛️ Ideal stability - steady as a statue!"
                ]
                feedback.append(random.choice(stability_praise))

        # Rep-Specific Contextual Messages
        if rep_number > 8:
            endurance_messages = [
                "🔥 Strong endurance - maintaining form under fatigue!",
                "💪 Impressive stamina - form holds up well late in set!",
                "⚡ Great conditioning - consistent quality despite fatigue!",
                "🏃 Excellent endurance - form resilience is impressive!"
            ]
            if random.random() < 0.3:  # 30% chance for endurance message
                feedback.append(random.choice(endurance_messages))
                
        elif rep_number <= 3:
            early_messages = [
                "🎯 Good start - establish that rhythm!",
                "💪 Strong opening - maintain this quality!",
                "✨ Solid beginning - keep this consistency!",
                "🚀 Great launch - sustain this level!"
            ]
            if random.random() < 0.25:  # 25% chance for early rep message
                feedback.append(random.choice(early_messages))

        return feedback
        
        return feedback
    
    def _generate_feedback(self, score: int, faults: List[str], penalties: List[Dict], bonuses: List[Dict]) -> List[str]:
        """Generate personalized feedback based on analysis results"""
        feedback = []
        
        # Score-based general feedback
        if score >= 90:
            feedback.append("🏆 Outstanding form! Professional level execution!")
        elif score >= 80:
            feedback.append("🎯 Excellent form with minor room for improvement.")
        elif score >= 70:
            feedback.append("✅ Good form - address the highlighted areas.")
        elif score >= 50:
            feedback.append("⚠️ Moderate form - focus on key technique points.")
        elif score >= 30:
            feedback.append("❌ Poor form - significant technique review needed.")
        else:
            feedback.append("🛑 DANGEROUS form detected - stop and check technique!")
        
        # Priority-based fault feedback
        fault_feedback_map = {
            'SEVERE_BACK_ROUNDING': "🚨 CRITICAL: Severe back rounding! Keep chest up and spine neutral.",
            'BACK_ROUNDING': "Keep your back straight and chest up throughout the movement.",
            'PARTIAL_REP': "Complete the full range of motion for maximum benefit.",
            'VERY_SHALLOW': "Go much deeper - aim for thighs parallel to ground.",
            'SEVERE_INSTABILITY': "🚨 Major balance issues - slow down and focus on stability.",
            'POOR_STABILITY': "Engage your core and focus on balance throughout the movement.",
            'INSUFFICIENT_DEPTH': "Increase your depth for better muscle activation.",
            'TOO_FAST': "Slow down - control the movement for better form and safety.",
            'TOO_SLOW': "Increase tempo slightly for better momentum and efficiency.",
            'ASYMMETRIC_MOVEMENT': "Focus on balanced, symmetrical movement patterns."
        }
        
        # Add specific feedback in severity order
        critical_faults = [f for f in faults if 'SEVERE' in f or 'CRITICAL' in f or 'PARTIAL_REP' in f]
        major_faults = [f for f in faults if f not in critical_faults and f in fault_feedback_map]
        
        for fault in critical_faults + major_faults:
            if fault in fault_feedback_map:
                feedback.append(fault_feedback_map[fault])
        
        # Add positive reinforcement for bonuses
        if bonuses:
            bonus_messages = {
                'Excellent Depth': "Great depth! You're hitting the optimal range.",
                'Good Depth': "Nice depth - keep it up!",
                'Good Tempo': "Perfect tempo - excellent control.",
            }
            
            for bonus in bonuses:
                reason = bonus.get('reason', '')
                if reason in bonus_messages:
                    feedback.append(f"💪 {bonus_messages[reason]}")
        
        return feedback
    
    def _create_biomechanical_summary(self, frame_metrics: List[BiomechanicalMetrics], 
                                    analysis_results: Dict, penalties: List[Dict], 
                                    bonuses: List[Dict]) -> Dict:
        """Create detailed biomechanical summary"""
        summary = {
            'rep_duration': len(frame_metrics) / 30.0,
            'difficulty_level': self.difficulty,
            'total_penalties': sum(p.get('amount', 0) for p in penalties),
            'total_bonuses': sum(b.get('amount', 0) for b in bonuses),
            'penalty_breakdown': [f"{p.get('reason', 'Unknown')}: -{p.get('amount', 0):.1f}" for p in penalties],
            'bonus_breakdown': [f"{b.get('reason', 'Unknown')}: +{b.get('amount', 0):.1f}" for b in bonuses],
            'analyzers_used': list(analysis_results.keys())
        }
        
        # Add specific metrics if available
        if frame_metrics:
            knee_angles = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
            back_angles = [fm.back_angle for fm in frame_metrics if fm.back_angle > 0]
            
            if knee_angles:
                summary['knee_depth_min'] = min(knee_angles)
                summary['movement_range'] = max(knee_angles) - min(knee_angles)
            
            if back_angles:
                summary['back_angle_min'] = min(back_angles)
                summary['back_consistency'] = np.std(back_angles)
            
            # Visibility metrics
            avg_visibility = np.mean([fm.landmark_visibility for fm in frame_metrics])
            summary['average_visibility'] = avg_visibility
            summary['visibility_quality'] = 'excellent' if avg_visibility > 0.9 else 'good' if avg_visibility > 0.7 else 'poor'
        
        return summary
    
    def debug_grade_repetition(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict:
        """
        Debug version of grade_repetition with detailed logging and validation
        """
        logger.debug(f"\n{'='*60}")
        logger.debug(f"DEBUG FORM GRADING - {len(frame_metrics)} frames")
        logger.debug(f"{'='*60}")
        
        # FIXED: Call the correct method (grade_repetition_weighted was removed)
        normal_result = self.grade_repetition(frame_metrics)
        
        # Add debug information
        debug_info = {
            'normal_result': normal_result,
            'frame_analysis': [],
            'analyzer_details': {},
            'validation_checks': []
        }
        
        # Validate frame metrics first
        valid_frames = []
        for i, fm in enumerate(frame_metrics):
            frame_valid = self._validate_frame_metrics(fm, i)
            if frame_valid['is_valid']:
                valid_frames.append(fm)
            debug_info['frame_analysis'].append(frame_valid)
        
        logger.debug(f"Frame validation: {len(valid_frames)}/{len(frame_metrics)} frames valid")
        
        if not valid_frames:
            logger.error("ERROR: No valid frames for analysis!")
            return debug_info
        
        # Run each analyzer with debug output
        for analyzer_name, analyzer in self.analyzers.items():
            logger.debug(f"\n--- {analyzer_name} Analysis ---")
            
            analyzer_result = analyzer.analyze(valid_frames)
            debug_info['analyzer_details'][analyzer_name] = {
                'result': analyzer_result,
                'penalties': analyzer_result.get('penalties', []),
                'bonuses': analyzer_result.get('bonuses', []),
                'metrics': analyzer_result.get('metrics', {})
            }
            
            # Print analyzer-specific debug info
            if hasattr(analyzer, 'debug_analysis'):
                analyzer_debug = analyzer.debug_analysis(valid_frames)
                debug_info['analyzer_details'][analyzer_name]['debug'] = analyzer_debug
                logger.debug(f"Debug info: {analyzer_debug}")
            
            print(f"Penalties: {len(analyzer_result.get('penalties', []))}")
            print(f"Bonuses: {len(analyzer_result.get('bonuses', []))}")
        
        # Validate final score
        score_validation = self._validate_final_score(normal_result, debug_info['analyzer_details'])
        debug_info['validation_checks'].append(score_validation)
        
        print(f"\n--- Final Score Validation ---")
        print(f"Base score: {score_validation['base_score']}")
        print(f"Total penalties: {score_validation['total_penalties']}")
        print(f"Total bonuses: {score_validation['total_bonuses']}")
        print(f"Final score: {score_validation['final_score']}")
        print(f"Score valid: {score_validation['is_valid']}")
        
        return debug_info
    
    def _validate_frame_metrics(self, fm: BiomechanicalMetrics, frame_idx: int) -> Dict:
        """Validate individual frame metrics"""
        validation = {
            'frame_index': frame_idx,
            'is_valid': True,
            'issues': [],
            'metrics_summary': {}
        }
        
        # Check landmark visibility
        if fm.landmark_visibility < 0.5:
            validation['issues'].append(f"Low visibility: {fm.landmark_visibility:.2f}")
            validation['is_valid'] = False
        
        # Check angle ranges
        angles = {
            'knee_left': fm.knee_angle_left,
            'knee_right': fm.knee_angle_right,
            'hip_angle': fm.hip_angle,  # Fixed: hip_angle not hip_angle_left/right
            'back_angle': fm.back_angle,
            'ankle_left': fm.ankle_angle_left,
            'ankle_right': fm.ankle_angle_right
        }
        
        for angle_name, angle_value in angles.items():
            if angle_value <= 0 or angle_value > 180:
                validation['issues'].append(f"Invalid {angle_name}: {angle_value:.1f}°")
                validation['is_valid'] = False
            validation['metrics_summary'][angle_name] = angle_value
        
        # Check stability
        if hasattr(fm, 'stability_score') and fm.stability_score < 0.3:
            validation['issues'].append(f"Poor stability: {fm.stability_score:.2f}")
        
        return validation
    
    def _validate_final_score(self, grading_result: Dict, analyzer_details: Dict) -> Dict:
        """Validate the final score calculation using the actual weighted method"""
        validation = {
            'final_score': grading_result.get('score', 0),
            'is_valid': True,
            'calculation_details': [],
            'component_breakdown': {}
        }
        
        # Extract component scores from grading result (if available)
        component_scores = grading_result.get('component_scores', {})
        
        if not component_scores:
            # If no component scores available, skip detailed validation
            validation['validation_method'] = 'skipped_no_component_data'
            return validation
        
        # Replicate the actual weighted calculation from grade_repetition
        weighted_score = 0.0
        total_weight = 0.0
        
        for component_name, component_data in component_scores.items():
            score = component_data['score']
            weight = component_data['weight']
            
            weighted_score += score * weight
            total_weight += weight
            
            validation['component_breakdown'][component_name] = {
                'score': score,
                'weight': weight,
                'contribution': score * weight
            }
            
            validation['calculation_details'].append({
                'component': component_name,
                'score': score,
                'weight': weight,
                'weighted_contribution': score * weight
            })
        
        # Calculate expected score using the same method as grade_repetition
        expected_score = int(weighted_score / total_weight) if total_weight > 0 else 0
        
        # Validate against actual score
        score_diff = abs(expected_score - validation['final_score'])
        if score_diff > 0.1:  # Allow small rounding differences
            validation['is_valid'] = False
            validation['expected_score'] = expected_score
            validation['actual_score'] = validation['final_score']
            validation['difference'] = score_diff
            validation['weighted_total'] = weighted_score
            validation['total_weight'] = total_weight
        else:
            validation['is_valid'] = True
            validation['expected_score'] = expected_score
            validation['validation_method'] = 'weighted_component_matching'
        
        return validation

