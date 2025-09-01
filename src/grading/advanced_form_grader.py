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
    
    # Depth Analyzer Thresholds (degrees)
    depth_bad_shallow_threshold: float = 130.0     # Very shallow squat (knee angle > 130°)
    depth_insufficient_threshold: float = 115.0    # Shallow squat (knee angle > 115°)
    depth_partial_rep_threshold: float = 100.0     # Incomplete range of motion
    depth_movement_range_threshold: float = 50.0   # Minimum movement range (degrees)
    depth_excellent_range: float = 0.9             # Placeholder for future depth analysis
    
    # NEW: Enhanced Partial Rep Detection Thresholds
    depth_micro_movement_threshold: float = 20.0   # Minimum range to count as movement
    depth_micro_movement_angle: float = 155.0      # Angle threshold for micro-movement detection
    depth_standing_angle_threshold: float = 160.0  # What counts as "standing position"
    
    # Butt Wink (Back Rounding) Analyzer Thresholds
    butt_wink_std_threshold: float = 8.0           # Standard deviation threshold for back angle variation
    butt_wink_range_threshold: float = 15.0        # Range threshold for back angle variation
    butt_wink_bottom_variation_threshold: float = 8.0  # Variation at bottom position
    
    # Knee Valgus Analyzer Thresholds
    knee_valgus_ratio_threshold: float = 0.85      # Knee-to-ankle distance ratio (< 0.85 = valgus)
    knee_valgus_penalty_multiplier: float = 1.5    # Severity multiplier for penalties
    knee_valgus_max_penalty: float = 30.0          # Maximum penalty for knee valgus
    
    # Head Position Analyzer Thresholds (degrees)
    head_position_angle_threshold: float = 25.0    # Max head angle from vertical (degrees)
    head_position_fault_ratio: float = 0.3         # Fault threshold (30% of frames)
    head_position_max_penalty: float = 20.0        # Maximum penalty for head position
    
    # Foot Stability Analyzer Thresholds
    foot_heel_lift_threshold: float = 0.02         # Heel lift detection threshold
    foot_stability_fault_ratio: float = 0.2        # Fault threshold (20% of frames)
    foot_stability_max_penalty: float = 15.0       # Maximum penalty for foot instability
    
    # Symmetry Analyzer Thresholds
    symmetry_threshold: float = 0.85               # Minimum symmetry ratio
    symmetry_penalty_multiplier: float = 100.0     # Penalty calculation multiplier
    
    # Tempo Analyzer Thresholds (seconds)
    tempo_too_fast_threshold: float = 1.2          # Minimum rep duration
    tempo_too_slow_threshold: float = 6.0          # Maximum rep duration
    tempo_optimal_min: float = 2.0                 # Optimal rep duration minimum
    tempo_optimal_max: float = 4.5                 # Optimal rep duration maximum
    
    # Frame Rate Configuration
    frame_rate: float = 30.0                       # Current frame rate setting
    mediapipe_landmark_count: int = 33             # Expected MediaPipe landmark count
    
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

class FaultType(Enum):
    """Enhanced fault types for comprehensive form analysis"""
    # Safety faults
    SEVERE_BACK_ROUNDING = "severe_back_rounding"
    MODERATE_BACK_ROUNDING = "moderate_back_rounding"
    BAD_BACK_ROUND = "bad_back_round"
    BAD_BACK_WARP = "bad_back_warp"  # Butt wink
    
    # Depth faults
    PARTIAL_REP = "partial_rep"
    INSUFFICIENT_DEPTH = "insufficient_depth"
    BAD_SHALLOW_DEPTH = "bad_shallow_depth"  # Very shallow
    MICRO_MOVEMENT = "micro_movement"        # NEW: Barely moving (fake squats)
    
    # Stability faults
    SEVERE_INSTABILITY = "severe_instability"
    MODERATE_INSTABILITY = "moderate_instability"
    
    # Knee tracking faults
    BAD_INNER_THIGH = "bad_inner_thigh"  # Knee valgus
    KNEE_VALGUS = "knee_valgus"
    
    # Head position faults
    BAD_HEAD = "bad_head"  # Looking down too much
    HEAD_FORWARD = "head_forward"
    
    # Foot position faults
    BAD_TOE = "bad_toe"  # Heel lift
    HEEL_LIFT = "heel_lift"
    FOOT_INSTABILITY = "foot_instability"

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
    
    # Enhanced tracking data for new analyzers
    raw_landmarks: List = field(default_factory=list)
    
    # User skill level for adaptive analysis
    skill_level: str = 'INTERMEDIATE'  # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    
    # Additional landmark positions (extracted from raw_landmarks)
    left_knee_pos: Optional[Any] = None
    right_knee_pos: Optional[Any] = None
    left_ankle_pos: Optional[Any] = None
    right_ankle_pos: Optional[Any] = None
    left_heel_pos: Optional[Any] = None
    right_heel_pos: Optional[Any] = None
    left_toe_pos: Optional[Any] = None
    right_toe_pos: Optional[Any] = None
    nose_pos: Optional[Any] = None
    left_ear_pos: Optional[Any] = None
    right_ear_pos: Optional[Any] = None
    left_shoulder_pos: Optional[Any] = None
    right_shoulder_pos: Optional[Any] = None
    left_hip_pos: Optional[Any] = None
    right_hip_pos: Optional[Any] = None
    
    def __post_init__(self):
        """Extract enhanced metrics from raw landmark data if available"""
        # Use configurable landmark count instead of hardcoded 33
        landmark_count = getattr(self, '_config_landmark_count', 33)  # Default to 33 for backward compatibility
        if self.raw_landmarks and len(self.raw_landmarks) >= landmark_count:
            self._extract_enhanced_metrics()
    
    def _extract_enhanced_metrics(self):
        """Extract enhanced metrics from raw landmark data"""
        try:
            landmarks = self.raw_landmarks
            
            # Knee positions (landmarks 25, 26)
            self.left_knee_pos = landmarks[25] if len(landmarks) > 25 else None
            self.right_knee_pos = landmarks[26] if len(landmarks) > 26 else None
            
            # Ankle positions (landmarks 27, 28)
            self.left_ankle_pos = landmarks[27] if len(landmarks) > 27 else None
            self.right_ankle_pos = landmarks[28] if len(landmarks) > 28 else None
            
            # Heel positions (landmarks 29, 30)
            self.left_heel_pos = landmarks[29] if len(landmarks) > 29 else None
            self.right_heel_pos = landmarks[30] if len(landmarks) > 30 else None
            
            # Toe positions (landmarks 31, 32)
            self.left_toe_pos = landmarks[31] if len(landmarks) > 31 else None
            self.right_toe_pos = landmarks[32] if len(landmarks) > 32 else None
            
            # Head landmarks
            self.nose_pos = landmarks[0] if len(landmarks) > 0 else None
            self.left_ear_pos = landmarks[7] if len(landmarks) > 7 else None
            self.right_ear_pos = landmarks[8] if len(landmarks) > 8 else None
            
            # Shoulder positions (landmarks 11, 12)
            self.left_shoulder_pos = landmarks[11] if len(landmarks) > 11 else None
            self.right_shoulder_pos = landmarks[12] if len(landmarks) > 12 else None
            
            # Hip positions (landmarks 23, 24)
            self.left_hip_pos = landmarks[23] if len(landmarks) > 23 else None
            self.right_hip_pos = landmarks[24] if len(landmarks) > 24 else None
            
        except (IndexError, AttributeError, TypeError) as e:
            logger.warning(f"Could not extract enhanced metrics: {e}")
            self._set_default_positions()
    
    def _set_default_positions(self):
        """Set default values when landmarks are not available"""
        self.left_knee_pos = None
        self.right_knee_pos = None
        self.left_ankle_pos = None
        self.right_ankle_pos = None
        self.left_heel_pos = None
        self.right_heel_pos = None
        self.left_toe_pos = None
        self.right_toe_pos = None
        self.nose_pos = None
        self.left_ear_pos = None
        self.right_ear_pos = None
        self.left_shoulder_pos = None
        self.right_shoulder_pos = None
        self.left_hip_pos = None
        self.right_hip_pos = None

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
    
    def __init__(self, config: ThresholdConfig):
        super().__init__(required_landmarks=[11, 12, 23, 24])  # shoulders, hips
        
        if not isinstance(config, ThresholdConfig):
            raise TypeError("SafetyAnalyzer requires a valid ThresholdConfig object")
        
        self.config = config
        
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
        
        # Debug: Show actual back angle vs thresholds
        print(f"🔧 BACK ANGLE DEBUG: min={min_back_angle:.1f}°, severe_thresh={self.SEVERE_BACK_ROUNDING_THRESHOLD:.1f}°, moderate_thresh={self.MODERATE_BACK_ROUNDING_THRESHOLD:.1f}°")
        
        faults = []
        penalties = []
        bonuses = []
        
        # CONSISTENT: Fixed thresholds for all reps
        # Back angle ranges: 180° = perfectly upright, 90° = horizontal
        if min_back_angle < self.SEVERE_BACK_ROUNDING_THRESHOLD:  # < 60° - very dangerous
            faults.append('SEVERE_BACK_ROUNDING')
            # Log the exact comparison for debugging
            print(f"🔧 SAFETY DEBUG: Back angle {min_back_angle:.1f}° < SEVERE threshold {self.SEVERE_BACK_ROUNDING_THRESHOLD:.1f}° = SEVERE")
            # More severe penalty for dangerous postures
            degrees_below = self.SEVERE_BACK_ROUNDING_THRESHOLD - min_back_angle
            # Scale penalty based on difficulty strictness - lower threshold = higher multiplier
            strictness_multiplier = 80.0 / self.SEVERE_BACK_ROUNDING_THRESHOLD  # Beginner ~1.0, Expert ~1.3
            penalty_amount = 40 + degrees_below * 2.0 * strictness_multiplier
            print(f"🔧 SEVERE PENALTY DEBUG: degrees_below={degrees_below:.1f}, strictness={strictness_multiplier:.2f}, penalty={penalty_amount:.1f}")
            penalties.append({
                'reason': 'DANGER: Severe back rounding detected!', 
                'amount': min(80, penalty_amount),  # Increased cap to allow for difficulty differences
                'metric_value': min_back_angle
            })
        elif min_back_angle < self.MODERATE_BACK_ROUNDING_THRESHOLD:  # < 90° - excessive lean
            faults.append('BACK_ROUNDING')
            # For same back angle, Expert should give higher penalty than Beginner
            # Use a fixed reference angle (100°) and scale penalty by difficulty strictness
            reference_good_angle = 100.0  # Minimum acceptable back angle
            angle_deficit = max(0, reference_good_angle - min_back_angle)  # How far below acceptable
            # Higher strictness (lower threshold) = higher multiplier
            strictness_multiplier = 150.0 / self.MODERATE_BACK_ROUNDING_THRESHOLD  # Beginner ~1.1, Expert ~1.6
            penalty_amount = 15 + angle_deficit * 1.5 * strictness_multiplier
            print(f"🔧 MODERATE PENALTY: angle={min_back_angle:.1f}°, threshold={self.MODERATE_BACK_ROUNDING_THRESHOLD:.1f}°, deficit={angle_deficit:.1f}, strictness={strictness_multiplier:.2f}, penalty={penalty_amount:.1f}")
            penalties.append({
                'reason': 'Back rounding - keep chest up and spine neutral', 
                'amount': min(70, penalty_amount),  # High cap to allow full difficulty range
                'metric_value': min_back_angle
            })
        elif min_back_angle >= self.EXCELLENT_POSTURE_THRESHOLD:  # >= 120° - excellent
            bonuses.append({
                'reason': 'Excellent upright posture maintained', 
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
    
    def __init__(self, config: ThresholdConfig):
        super().__init__(required_landmarks=[25, 26, 27, 28])  # knees, ankles
        if not isinstance(config, ThresholdConfig):
            raise TypeError("DepthAnalyzer requires a valid ThresholdConfig object")
        self.config = config
        
        # Initialize thresholds from config (will be updated by difficulty scaling)
        self.BAD_SHALLOW_THRESHOLD = self.config.depth_bad_shallow_threshold
        self.INSUFFICIENT_THRESHOLD = self.config.depth_insufficient_threshold
        self.MOVEMENT_RANGE_THRESHOLD = self.config.depth_movement_range_threshold
    
    def _check_difficulty(self, difficulty: str) -> bool:
        # FIXED: Enable depth analysis for ALL difficulty levels - depth is critical for safety!
        return True  # Depth analysis is critical for all users regardless of skill level
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        """Enhanced depth analysis with three-tier detection and skill-based sensitivity.
        
        Three-Tier System:
        1. Micro-movement (barely moving - fake squats)
        2. Partial rep (some depth but not enough)  
        3. Good depth (meets requirements, potential rewards)
        """
        knee_angles = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
        if not knee_angles:
            return {'faults': [], 'penalties': [], 'bonuses': []}

        min_knee_angle = np.min(knee_angles)
        max_knee_angle = np.max(knee_angles)
        movement_range = max_knee_angle - min_knee_angle
        
        faults = []
        penalties = []
        bonuses = []
        
        # Get skill-based thresholds (default to intermediate if not available)
        user_skill = 'INTERMEDIATE'  # Default fallback
        if frame_metrics and len(frame_metrics) > 0:
            # Try to get skill level from frame metrics first
            if hasattr(frame_metrics[0], 'skill_level') and frame_metrics[0].skill_level:
                user_skill = frame_metrics[0].skill_level
            # Otherwise use the grader's user profile skill level
            elif self.user_profile and hasattr(self.user_profile, 'skill_level'):
                user_skill = str(self.user_profile.skill_level).replace('UserLevel.', '').upper()
                
        micro_threshold = self._get_skill_adjusted_micro_threshold(user_skill)
        depth_threshold = self._get_skill_adjusted_depth_threshold(user_skill)
        
        # TIER 1: Micro-movement detection (fake squats)
        if movement_range < micro_threshold:
            severity = self._calculate_micro_movement_severity(movement_range, micro_threshold)
            faults.append(FaultType.MICRO_MOVEMENT.value)
            penalties.append({
                'reason': f"Barely moving - only {movement_range:.1f}° range of motion. "
                         f"Need at least {micro_threshold:.1f}° for a real squat.",
                'amount': min(45, severity),
                'analysis_details': {
                    'movement_range': movement_range,
                    'required_range': micro_threshold,
                    'skill_level': user_skill,
                    'tier': 'micro_movement'
                }
            })
            return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}  # Don't continue with other analysis
        
        # TIER 2: Traditional depth analysis with skill-based adjustments
        if min_knee_angle > self.config.depth_bad_shallow_threshold:  # Very shallow (barely squatting)
            faults.append(FaultType.BAD_SHALLOW_DEPTH.value)
            penalty = 35 + (min_knee_angle - self.config.depth_bad_shallow_threshold) * 1.5
            penalties.append({
                'reason': 'Extremely shallow squat - barely bending knees',
                'amount': min(50, penalty)
            })
        elif min_knee_angle > self.config.depth_insufficient_threshold:  # Shallow (above parallel)
            faults.append(FaultType.INSUFFICIENT_DEPTH.value)
            penalty = 20 + (min_knee_angle - self.config.depth_insufficient_threshold) * 1.0
            penalties.append({
                'reason': 'Insufficient depth - not reaching parallel',
                'amount': min(30, penalty)
            })
        elif min_knee_angle > depth_threshold:  # Skill-based partial rep
            severity = self._calculate_partial_rep_severity(min_knee_angle, depth_threshold, user_skill)
            
            # Skill-based feedback
            if user_skill == 'BEGINNER':
                encouragement = "Getting there! Try to sit back a bit more."
            elif user_skill == 'INTERMEDIATE':
                encouragement = "Close! Aim for a slightly deeper squat."
            elif user_skill == 'ADVANCED':
                encouragement = "Not quite full depth - you can do better!"
            else:  # EXPERT
                encouragement = "Depth standards are high for your level."
            
            faults.append(FaultType.PARTIAL_REP.value)
            penalties.append({
                'reason': f"Partial rep - {encouragement} Current: {min_knee_angle:.1f}°, Target: <{depth_threshold:.1f}°",
                'amount': min(20, severity),
                'analysis_details': {
                    'min_knee_angle': min_knee_angle,
                    'required_angle': depth_threshold,
                    'depth_deficit': min_knee_angle - depth_threshold,
                    'skill_level': user_skill,
                    'tier': 'partial_rep'
                }
            })
        
        # TIER 3: Good depth (potential for positive feedback/rewards)
        else:
            # Good depth - potential bonus
            if min_knee_angle <= 85:  # Excellent depth
                depth_quality = self._assess_depth_quality(min_knee_angle, depth_threshold, user_skill)
                bonus_amount = 5 if depth_quality == 'excellent' else 3
                bonuses.append({
                    'reason': f'Excellent squat depth achieved ({depth_quality})',
                    'amount': bonus_amount,
                    'analysis_details': {
                        'min_knee_angle': min_knee_angle,
                        'depth_quality': depth_quality,
                        'skill_level': user_skill,
                        'tier': 'good_depth'
                    }
                })

        return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}

    def _get_skill_adjusted_micro_threshold(self, user_skill: str) -> float:
        """Get micro-movement threshold based on user skill level."""
        base_threshold = self.config.depth_micro_movement_threshold
        
        skill_adjustments = {
            'BEGINNER': 1.2,     # More lenient for beginners
            'INTERMEDIATE': 1.0,  # Standard threshold
            'ADVANCED': 0.8,     # Stricter for advanced users
            'EXPERT': 0.6        # Very strict for experts
        }
        
        multiplier = skill_adjustments.get(user_skill, 1.0)
        return base_threshold * multiplier
    
    def _get_skill_adjusted_depth_threshold(self, user_skill: str) -> float:
        """Get depth threshold based on user skill level."""
        base_threshold = self.config.depth_partial_rep_threshold
        
        # Skill-based adjustments for depth requirements
        skill_adjustments = {
            'BEGINNER': 95.0,      # More lenient - focus on learning form
            'INTERMEDIATE': 90.0,   # Standard depth requirement
            'ADVANCED': 85.0,      # Deeper squats expected
            'EXPERT': 80.0         # Professional-level depth
        }
        
        return skill_adjustments.get(user_skill, base_threshold)
    
    def _calculate_micro_movement_severity(self, movement_range: float, required_range: float) -> float:
        """Calculate severity penalty for micro-movements."""
        deficit = required_range - movement_range
        severity_ratio = deficit / required_range
        return 35 + (severity_ratio * 15)  # 35-50 point penalty range
    
    def _calculate_partial_rep_severity(self, angle: float, target_angle: float, user_skill: str) -> float:
        """Calculate severity penalty for partial reps based on skill level."""
        deficit = angle - target_angle
        
        # Skill-based penalty scaling
        skill_multipliers = {
            'BEGINNER': 0.5,     # Gentler penalties for beginners
            'INTERMEDIATE': 1.0,  # Standard penalties
            'ADVANCED': 1.3,     # Higher penalties for advanced users
            'EXPERT': 1.5        # Highest penalties for experts
        }
        
        multiplier = skill_multipliers.get(user_skill, 1.0)
        base_penalty = 8 + (deficit * 0.8)
        return base_penalty * multiplier
    
    def _assess_depth_quality(self, angle: float, target_angle: float, user_skill: str) -> str:
        """Assess the quality of achieved depth."""
        depth_margin = target_angle - angle
        
        if depth_margin >= 15:
            return 'excellent'
        elif depth_margin >= 8:
            return 'good'  
        elif depth_margin >= 3:
            return 'adequate'
        else:
            return 'minimal'

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
    
    def __init__(self, config: ThresholdConfig):
        super().__init__(required_landmarks=[0, 15, 16])  # nose, ankles for COM
        
        if not isinstance(config, ThresholdConfig):
            raise TypeError("StabilityAnalyzer requires a valid ThresholdConfig object")
        
        self.config = config
        
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
                'reason': 'Severe balance issues - focus on core stability',
                'amount': penalty_amount,
                'metric_value': total_sway
            })
        elif total_sway > self.POOR_STABILITY_THRESHOLD:
            faults.append('POOR_STABILITY')
            penalty_amount = 8 + min(12, (total_sway - self.POOR_STABILITY_THRESHOLD) * 800)
            penalties.append({
                'reason': 'Poor balance control - engage core muscles',
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
    
    def __init__(self, config: ThresholdConfig):
        super().__init__()
        if not isinstance(config, ThresholdConfig):
            raise TypeError("TempoAnalyzer requires a valid ThresholdConfig object")
        self.config = config
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['casual', 'professional', 'expert']
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        duration = len(frame_metrics) / self.config.frame_rate
        
        faults = []
        penalties = []
        bonuses = []
        
        if duration < self.config.tempo_too_fast_threshold:  # Too fast
            faults.append('TOO_FAST')
            penalty = (self.config.tempo_too_fast_threshold - duration) * 20
            penalties.append({'reason': 'Too fast - slow down and control the movement', 'amount': min(25, penalty)})
        elif duration > self.config.tempo_too_slow_threshold:  # Too slow
            faults.append('TOO_SLOW')
            penalty = (duration - self.config.tempo_too_slow_threshold) * 3
            penalties.append({'reason': 'Too slow - maintain steady tempo', 'amount': min(15, penalty)})
        elif self.config.tempo_optimal_min <= duration <= self.config.tempo_optimal_max:  # Good tempo
            bonuses.append({'reason': 'Good tempo maintained', 'amount': 5})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}

class SymmetryAnalyzer(BaseAnalyzer):
    """Analyzes bilateral symmetry and movement patterns"""
    
    def __init__(self, config: ThresholdConfig):
        super().__init__()
        if not isinstance(config, ThresholdConfig):
            raise TypeError("SymmetryAnalyzer requires a valid ThresholdConfig object")
        self.config = config
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['professional', 'expert']
    
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
        
        if avg_symmetry < self.config.symmetry_threshold:  # Significant asymmetry
            faults.append('ASYMMETRIC_MOVEMENT')
            penalty = (self.config.symmetry_threshold - avg_symmetry) * self.config.symmetry_penalty_multiplier
            penalties.append({'reason': 'Uneven movement - check left/right balance', 'amount': min(20, penalty)})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': []}

class ButtWinkAnalyzer(BaseAnalyzer):
    """Analyzes for pelvic tilt (butt wink) at the bottom of the squat"""
    
    def __init__(self, config: ThresholdConfig):
        super().__init__()
        if not isinstance(config, ThresholdConfig):
            raise TypeError("ButtWinkAnalyzer requires a valid ThresholdConfig object")
        self.config = config
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['casual', 'professional', 'expert']
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        if len(frame_metrics) < 15:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        faults, penalties, bonuses = [], [], []
        
        try:
            # Find the bottom of the squat (minimum knee angle)
            knee_angles = [min(fm.knee_angle_left, fm.knee_angle_right) for fm in frame_metrics]
            bottom_frame_index = np.argmin(knee_angles)
            
            # Analyze back angle around the bottom (±5 frames)
            window_size = 5
            start_idx = max(0, bottom_frame_index - window_size)
            end_idx = min(len(frame_metrics), bottom_frame_index + window_size + 1)
            
            back_angles_window = [fm.back_angle for fm in frame_metrics[start_idx:end_idx]]
            
            if len(back_angles_window) > 3:
                # Calculate back angle variation
                back_angle_std = np.std(back_angles_window)
                back_angle_range = max(back_angles_window) - min(back_angles_window)
                
                # Detect butt wink patterns using config thresholds
                if (back_angle_std > self.config.butt_wink_std_threshold or 
                    back_angle_range > self.config.butt_wink_range_threshold):
                    # Check for the characteristic dip pattern
                    bottom_angle = frame_metrics[bottom_frame_index].back_angle
                    pre_bottom = np.mean([fm.back_angle for fm in frame_metrics[max(0, bottom_frame_index-3):bottom_frame_index]])
                    post_bottom = np.mean([fm.back_angle for fm in frame_metrics[bottom_frame_index+1:min(len(frame_metrics), bottom_frame_index+4)]])
                    
                    # Butt wink: back angle drops significantly at bottom then recovers
                    if ((pre_bottom - bottom_angle > self.config.butt_wink_bottom_variation_threshold) and 
                        (post_bottom - bottom_angle > self.config.butt_wink_bottom_variation_threshold)):
                        severity = min(25, back_angle_range * 1.2)
                        faults.append(FaultType.BAD_BACK_WARP.value)
                        penalties.append({
                            'reason': 'Butt wink detected - lower back rounding at bottom position',
                            'amount': severity
                        })
                        
        except Exception as e:
            logger.warning(f"ButtWinkAnalyzer error: {e}")
        
        return {
            'faults': faults,
            'penalties': penalties,
            'bonuses': bonuses
        }

class KneeValgusAnalyzer(BaseAnalyzer):
    """Analyzes for knee valgus (knees caving inward)"""
    
    def __init__(self, config: ThresholdConfig):
        super().__init__()
        if not isinstance(config, ThresholdConfig):
            raise TypeError("KneeValgusAnalyzer requires a valid ThresholdConfig object")
        self.config = config
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['casual', 'professional', 'expert']
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        if not frame_metrics:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        faults, penalties, bonuses = [], [], []
        
        valgus_detected = False
        max_valgus_severity = 0
        
        for metrics in frame_metrics:
            try:
                # Check if we have knee and ankle position data
                if (metrics.left_knee_pos and metrics.right_knee_pos and 
                    metrics.left_ankle_pos and metrics.right_ankle_pos):
                    
                    # Calculate horizontal distances
                    knee_distance = abs(metrics.left_knee_pos.x - metrics.right_knee_pos.x)
                    ankle_distance = abs(metrics.left_ankle_pos.x - metrics.right_ankle_pos.x)
                    
                    # Knee valgus ratio - knees should be at least as wide as ankles
                    if ankle_distance > 0:
                        valgus_ratio = knee_distance / ankle_distance
                        
                        # Detect knee valgus using config threshold
                        if valgus_ratio < self.config.knee_valgus_ratio_threshold:
                            valgus_detected = True
                            severity = (self.config.knee_valgus_ratio_threshold - valgus_ratio) * 100
                            max_valgus_severity = max(max_valgus_severity, severity)
                        
            except (AttributeError, TypeError, ZeroDivisionError):
                continue  # Skip frames with missing data
        
        if valgus_detected:
            penalty_amount = min(self.config.knee_valgus_max_penalty, 
                               max_valgus_severity * self.config.knee_valgus_penalty_multiplier)
            faults.append(FaultType.BAD_INNER_THIGH.value)
            penalties.append({
                'reason': 'Knees caving inward - push knees out over toes',
                'amount': penalty_amount
            })
        
        return {
            'faults': faults,
            'penalties': penalties,
            'bonuses': bonuses
        }

class HeadPositionAnalyzer(BaseAnalyzer):
    """Analyzes head position during the squat"""
    
    def __init__(self, config: ThresholdConfig):
        super().__init__()
        if not isinstance(config, ThresholdConfig):
            raise TypeError("HeadPositionAnalyzer requires a valid ThresholdConfig object")
        self.config = config
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['casual', 'professional', 'expert']
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        if not frame_metrics:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        faults, penalties, bonuses = [], [], []
        
        head_fault_count = 0
        total_frames_checked = 0
        
        for metrics in frame_metrics:
            try:
                # Check if we have head and shoulder position data
                if (metrics.nose_pos and metrics.left_shoulder_pos and metrics.right_shoulder_pos):
                    
                    # Calculate shoulder midpoint
                    shoulder_mid_x = (metrics.left_shoulder_pos.x + metrics.right_shoulder_pos.x) / 2
                    shoulder_mid_y = (metrics.left_shoulder_pos.y + metrics.right_shoulder_pos.y) / 2
                    
                    # Vector from shoulders to nose
                    head_vector_x = metrics.nose_pos.x - shoulder_mid_x
                    head_vector_y = metrics.nose_pos.y - shoulder_mid_y
                    
                    # Calculate head angle relative to vertical
                    if abs(head_vector_y) > 0.01:  # Avoid division by zero
                        head_angle = np.degrees(np.arctan(abs(head_vector_x) / abs(head_vector_y)))
                        
                        total_frames_checked += 1
                        
                        # Head should be relatively upright using config threshold
                        if head_angle > self.config.head_position_angle_threshold:
                            head_fault_count += 1
                        
            except (AttributeError, TypeError, ZeroDivisionError):
                continue
        
        # If head position is bad in more than configured threshold of frames
        if (total_frames_checked > 0 and 
            (head_fault_count / total_frames_checked) > self.config.head_position_fault_ratio):
            penalty_severity = min(self.config.head_position_max_penalty, 
                                 (head_fault_count / total_frames_checked) * 25)
            faults.append(FaultType.BAD_HEAD.value)
            penalties.append({
                'reason': 'Keep head up - looking down too much',
                'amount': penalty_severity
            })
        
        return {
            'faults': faults,
            'penalties': penalties,
            'bonuses': bonuses
        }

class FootStabilityAnalyzer(BaseAnalyzer):
    """Analyzes foot stability and heel lift during the squat"""
    
    def __init__(self, config: ThresholdConfig):
        super().__init__()
        if not isinstance(config, ThresholdConfig):
            raise TypeError("FootStabilityAnalyzer requires a valid ThresholdConfig object")
        self.config = config
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['casual', 'professional', 'expert']
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        if not frame_metrics:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        faults, penalties, bonuses = [], [], []
        
        try:
            # Track heel positions over time
            left_heel_heights = []
            right_heel_heights = []
            
            for metrics in frame_metrics:
                if metrics.left_heel_pos and metrics.right_heel_pos:
                    left_heel_heights.append(metrics.left_heel_pos.y)
                    right_heel_heights.append(metrics.right_heel_pos.y)
            
            if len(left_heel_heights) > 5 and len(right_heel_heights) > 5:
                # Calculate heel lift (decrease in y-coordinate indicates lift)
                left_heel_baseline = np.mean(left_heel_heights[:3])  # Initial position
                right_heel_baseline = np.mean(right_heel_heights[:3])
                
                left_min_y = min(left_heel_heights)
                right_min_y = min(right_heel_heights)
                
                # Check for significant heel lift (coordinate system dependent)
                left_heel_lift = left_heel_baseline - left_min_y
                right_heel_lift = right_heel_baseline - right_min_y
                
                max_heel_lift = max(left_heel_lift, right_heel_lift)
                
                # Threshold for heel lift detection (needs calibration)
                heel_lift_threshold = 0.05  # 5% of frame height
                
                if max_heel_lift > heel_lift_threshold:
                    penalty_amount = min(25, max_heel_lift * 200)
                    faults.append(FaultType.BAD_TOE.value)
                    penalties.append({
                        'reason': 'Keep feet flat - heels lifting off ground',
                        'amount': penalty_amount
                    })
                
                # Check foot stability (heel position variance)
                left_heel_stability = np.std(left_heel_heights)
                right_heel_stability = np.std(right_heel_heights)
                avg_foot_instability = (left_heel_stability + right_heel_stability) / 2
                
                if avg_foot_instability > 0.03:  # High variance indicates instability
                    penalty_amount = min(15, avg_foot_instability * 300)
                    faults.append(FaultType.FOOT_INSTABILITY.value)
                    penalties.append({
                        'reason': 'Unstable foot position - maintain stable base',
                        'amount': penalty_amount
                    })
                
        except Exception as e:
            logger.warning(f"FootStabilityAnalyzer error: {e}")
        
        return {
            'faults': faults,
            'penalties': penalties,
            'bonuses': bonuses
        }

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
            'depth': DepthAnalyzer(self.config),
            'stability': StabilityAnalyzer(self.config),
            'tempo': TempoAnalyzer(self.config),
            'symmetry': SymmetryAnalyzer(self.config),
            'butt_wink': ButtWinkAnalyzer(self.config),
            'knee_valgus': KneeValgusAnalyzer(self.config),
            'head_position': HeadPositionAnalyzer(self.config),
            'foot_stability': FootStabilityAnalyzer(self.config),
        }

        # Set initial difficulty
        self.set_difficulty(difficulty)
        
        # Initialize difficulty thresholds mapping for logging
        self.difficulty_thresholds = {
            'beginner': 1.1,
            'casual': 1.0,
            'professional': 0.9,
            'expert': 0.8
        }
        
        # Initialize enhanced feedback system (new Phase 2 integration)
        self.enhanced_feedback_enabled = True
        self.enhanced_feedback_manager = None
        self._initialize_enhanced_feedback(user_profile)
    
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
    
    def _initialize_enhanced_feedback(self, user_profile):
        """Initialize enhanced feedback system with graceful fallback"""
        try:
            from src.feedback.enhanced_feedback_manager import EnhancedFeedbackManager
            
            # Determine user skill level
            skill_level = "beginner"  # default
            if user_profile and hasattr(user_profile, 'skill_level'):
                skill_level = str(user_profile.skill_level).lower()
            
            # Initialize enhanced feedback manager
            self.enhanced_feedback_manager = EnhancedFeedbackManager(
                voice_enabled=True,  # Can be overridden later
                user_skill_level=skill_level
            )
            
            self.logger.info(f"✅ Enhanced feedback system initialized (skill: {skill_level})")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Enhanced feedback system unavailable: {e}")
            self.enhanced_feedback_enabled = False
        except Exception as e:
            self.logger.error(f"❌ Enhanced feedback initialization failed: {e}")
            self.enhanced_feedback_enabled = False
    
    def set_voice_feedback_enabled(self, enabled: bool):
        """Enable or disable voice feedback"""
        if self.enhanced_feedback_manager:
            self.enhanced_feedback_manager.set_voice_enabled(enabled)
            self.logger.info(f"Voice feedback {'enabled' if enabled else 'disabled'}")
    
    def get_enhanced_feedback_status(self) -> Dict[str, Any]:
        """Get status of enhanced feedback system"""
        if not self.enhanced_feedback_enabled or not self.enhanced_feedback_manager:
            return {"enabled": False, "reason": "Not initialized"}
        
        return {
            "enabled": True,
            "status": self.enhanced_feedback_manager.get_feedback_statistics()
        }
    
    def _process_enhanced_feedback(self, faults, analysis_details, score, frame_metrics, rep_number):
        """Process enhanced feedback if system is initialized and enabled"""
        if not self.enhanced_feedback_enabled or not self.enhanced_feedback_manager:
            return None
        
        try:
            # Create pose analysis result compatible with enhanced feedback
            pose_analysis = {
                'faults': faults,
                'scores': {'overall': score, 'component_scores': analysis_details.get('component_scores', {})},
                'rep_number': rep_number,
                'frame_count': len(frame_metrics),
                'analysis_details': analysis_details
            }
            
            # Process with enhanced feedback manager
            enhanced_result = self.enhanced_feedback_manager.process_pose_analysis(pose_analysis)
            
            return {
                'messages_generated': len(enhanced_result.get('messages', [])),
                'voice_messages_sent': enhanced_result.get('voice_messages_sent', 0),
                'priority_levels': [msg.get('priority', 'MEDIUM') for msg in enhanced_result.get('messages', [])],
                'feedback_categories': [msg.get('category', 'GENERAL') for msg in enhanced_result.get('messages', [])],
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced feedback processing error: {e}")
            return {'status': 'error', 'error': str(e)}
    
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
        """Set difficulty level with validation - UPDATED for 4 levels"""
        difficulty = difficulty.lower()
        
        # UPDATED: Support 4 difficulty levels to match skill levels
        valid_difficulties = ['beginner', 'casual', 'professional', 'expert']
        
        if difficulty not in valid_difficulties:
            logging.warning(f"Invalid difficulty '{difficulty}', defaulting to 'casual'")
            difficulty = 'casual'
        
        self.difficulty = difficulty
        
        # CRITICAL FIX: Map difficulty to user skill level for weight calculation
        difficulty_to_skill = {
            'beginner': UserLevel.BEGINNER,
            'casual': UserLevel.INTERMEDIATE,  # Map casual to intermediate
            'professional': UserLevel.ADVANCED,
            'expert': UserLevel.EXPERT
        }
        
        # Update user profile skill level to match difficulty
        if self.user_profile:
            self.user_profile.skill_level = difficulty_to_skill[difficulty]
        
        self._update_difficulty_thresholds()
        
        # Update component weights based on new difficulty/skill level
        self.component_weights = self._get_skill_based_weights()
        
        logger.debug(f"FormGrader: Difficulty updated to: {self.difficulty}, skill level: {difficulty_to_skill[difficulty]}")
    
    def _update_difficulty_thresholds(self) -> None:
        """Update analyzer configurations based on difficulty level with proper threshold scaling"""
        
        # Define difficulty scaling factors
        # Higher difficulty = stricter thresholds = lower scores for same performance
        if self.difficulty == 'beginner':
            # Most forgiving thresholds (easiest to get high scores)
            threshold_multiplier = 1.1  # 10% more forgiving (was 1.2)
            visibility_threshold = 0.6
        elif self.difficulty == 'casual':
            # Standard thresholds (baseline)
            threshold_multiplier = 1.0  # No change from config
            visibility_threshold = 0.7
        elif self.difficulty == 'professional':
            # Stricter thresholds (harder to get high scores)
            threshold_multiplier = 0.9  # 10% stricter (was 0.85)
            visibility_threshold = 0.8
        elif self.difficulty == 'expert':
            # Strictest thresholds (hardest to get high scores)
            threshold_multiplier = 0.8  # 20% stricter (was 0.7)
            visibility_threshold = 0.85
        
        # Apply visibility thresholds
        for analyzer in self.analyzers.values():
            analyzer.min_visibility_threshold = visibility_threshold
        
        # Apply threshold scaling to specific analyzers
        self._apply_difficulty_scaling(threshold_multiplier)
        
        logger.debug(f"FormGrader: Difficulty {self.difficulty} applied with {threshold_multiplier}x scaling")
    
    def _apply_difficulty_scaling(self, multiplier: float) -> None:
        """Apply difficulty scaling to analyzer thresholds"""
        
        # Scale Safety Analyzer thresholds
        safety_analyzer = self.analyzers.get('safety')
        if safety_analyzer:
            # CORRECTED LOGIC: For safety thresholds, MULTIPLY to make stricter, DIVIDE to make more forgiving
            # Expert (0.7): threshold * 0.7 = LOWER threshold = MORE STRICT  
            # Beginner (1.2): threshold * 1.2 = HIGHER threshold = MORE FORGIVING
            safety_analyzer.SEVERE_BACK_ROUNDING_THRESHOLD = self.config.safety_severe_back_rounding * multiplier
            safety_analyzer.MODERATE_BACK_ROUNDING_THRESHOLD = self.config.safety_moderate_back_rounding * multiplier
            safety_analyzer.EXCELLENT_POSTURE_THRESHOLD = self.config.safety_excellent_posture * multiplier
        
        # Scale Depth Analyzer thresholds  
        depth_analyzer = self.analyzers.get('depth')
        if depth_analyzer:
            # For depth: higher knee angles = shallower squat
            # CORRECTED: For more forgiving (beginner), allow shallower squats (higher threshold)
            depth_analyzer.BAD_SHALLOW_THRESHOLD = self.config.depth_bad_shallow_threshold * multiplier
            depth_analyzer.INSUFFICIENT_THRESHOLD = self.config.depth_insufficient_threshold * multiplier
            depth_analyzer.MOVEMENT_RANGE_THRESHOLD = self.config.depth_movement_range_threshold / multiplier
        
        # Scale Stability Analyzer thresholds
        stability_analyzer = self.analyzers.get('stability') 
        if stability_analyzer:
            # For stability: higher sway = worse stability
            # CORRECTED: For more forgiving (beginner), allow more sway (higher threshold)
            stability_analyzer.SEVERE_INSTABILITY_THRESHOLD = self.config.stability_severe_instability * multiplier
            stability_analyzer.POOR_STABILITY_THRESHOLD = self.config.stability_poor_stability * multiplier
            stability_analyzer.EXCELLENT_STABILITY_THRESHOLD = self.config.stability_excellent_stability * multiplier
        
        # Scale other analyzers if they have relevant thresholds
        butt_wink_analyzer = self.analyzers.get('butt_wink')
        if butt_wink_analyzer:
            butt_wink_analyzer.STD_THRESHOLD = self.config.butt_wink_std_threshold * multiplier
            butt_wink_analyzer.RANGE_THRESHOLD = self.config.butt_wink_range_threshold * multiplier
        
        knee_valgus_analyzer = self.analyzers.get('knee_valgus')
        if knee_valgus_analyzer:
            # Lower ratio = worse knee tracking
            # CORRECTED: For more forgiving (beginner), allow worse knee tracking (lower threshold)
            knee_valgus_analyzer.RATIO_THRESHOLD = self.config.knee_valgus_ratio_threshold / multiplier
        
        # Scale tempo thresholds
        tempo_analyzer = self.analyzers.get('tempo')
        if tempo_analyzer:
            # CORRECTED: For more forgiving (beginner), widen tempo range
            optimal_range = self.config.tempo_optimal_max - self.config.tempo_optimal_min
            range_adjustment = optimal_range * (multiplier - 1) * 0.2
            tempo_analyzer.OPTIMAL_MIN = self.config.tempo_optimal_min - range_adjustment
            tempo_analyzer.OPTIMAL_MAX = self.config.tempo_optimal_max + range_adjustment
    

    def _validate_input_contracts(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        """
        TASK 1: Validate that input data meets basic contracts for reliable analysis.
        Essential for dissertation-level robustness.
        """
        validation_result = {
            'is_valid': True,
            'error_message': '',
            'warnings': [],
            'data_quality_score': 0.0
        }
        
        # Check 1: Minimum frame count
        if len(frame_metrics) < 10:
            validation_result['is_valid'] = False
            validation_result['error_message'] = f"Insufficient data: {len(frame_metrics)} frames (minimum: 10)"
            return validation_result
        
        # Check 2: Data integrity
        valid_frames = 0
        total_visibility = 0.0
        
        for i, fm in enumerate(frame_metrics):
            if fm is None:
                validation_result['warnings'].append(f"Frame {i}: Null frame metrics")
                continue
                
            # Check landmark visibility
            if fm.landmark_visibility < 0.5:
                validation_result['warnings'].append(f"Frame {i}: Low visibility ({fm.landmark_visibility:.2f})")
            
            # Check for valid angle measurements
            if fm.knee_angle_left <= 0 or fm.knee_angle_right <= 0:
                validation_result['warnings'].append(f"Frame {i}: Invalid knee angles")
                continue
                
            valid_frames += 1
            total_visibility += fm.landmark_visibility
        
        # Check 3: Minimum valid frame ratio
        valid_frame_ratio = valid_frames / len(frame_metrics)
        if valid_frame_ratio < 0.7:
            validation_result['is_valid'] = False
            validation_result['error_message'] = f"Too many invalid frames: {valid_frame_ratio:.1%} valid (minimum: 70%)"
            return validation_result
        
        # Calculate data quality score
        avg_visibility = total_visibility / valid_frames if valid_frames > 0 else 0
        validation_result['data_quality_score'] = (valid_frame_ratio * 0.6) + (avg_visibility * 0.4)
        
        if validation_result['data_quality_score'] < 0.6:
            validation_result['warnings'].append(f"Low data quality score: {validation_result['data_quality_score']:.2f}")
        
        return validation_result

    def _get_active_analyzers(self) -> Dict[str, BaseAnalyzer]:
        """Get analyzers that should be active for current difficulty level"""
        active_analyzers = {}
        
        for name, analyzer in self.analyzers.items():
            if analyzer.can_analyze([], self.difficulty):  # Just check difficulty, not data yet
                active_analyzers[name] = analyzer
        
        logger.debug(f"Active analyzers for {self.difficulty}: {list(active_analyzers.keys())}")
        return active_analyzers

    def _check_data_requirements(self, frame_metrics: List[BiomechanicalMetrics], 
                               active_analyzers: Dict[str, BaseAnalyzer]) -> Dict[str, Any]:
        """
        TASK 1: Check if active analyzers have the data they need.
        Prevents silent failures of new analyzers.
        """
        requirements_result = {
            'all_met': True,
            'missing': [],
            'analyzer_status': {}
        }
        
        if not frame_metrics:
            requirements_result['all_met'] = False
            requirements_result['missing'].append('No frame metrics provided')
            return requirements_result
        
        # Check first valid frame for data availability
        sample_frame = next((fm for fm in frame_metrics if fm), None)
        if not sample_frame:
            requirements_result['all_met'] = False
            requirements_result['missing'].append('No valid frame metrics found')
            return requirements_result
        
        # Check analyzer-specific requirements
        for analyzer_name, analyzer in active_analyzers.items():
            status = {'can_analyze': True, 'missing_data': []}
            
            # Check if new analyzers have the raw landmark data they need
            if analyzer_name in ['knee_valgus', 'head_position', 'foot_stability', 'butt_wink']:
                if not hasattr(sample_frame, 'raw_landmarks') or not sample_frame.raw_landmarks:
                    status['can_analyze'] = False
                    status['missing_data'].append('raw_landmarks')
                    requirements_result['missing'].append(f"{analyzer_name}: missing raw_landmarks")
            
            # Check visibility requirements
            avg_visibility = np.mean([fm.landmark_visibility for fm in frame_metrics if fm])
            min_visibility = getattr(analyzer, 'min_visibility_threshold', 0.5)
            if avg_visibility < min_visibility:
                status['can_analyze'] = False
                status['missing_data'].append(f'visibility too low: {avg_visibility:.2f}')
                requirements_result['missing'].append(f"{analyzer_name}: insufficient visibility")
            
            requirements_result['analyzer_status'][analyzer_name] = status
            
            if not status['can_analyze']:
                requirements_result['all_met'] = False
        
        return requirements_result

    def _get_skill_based_weights(self) -> Dict[str, float]:
        """
        TASK 5: Dynamic skill-based weighting system.
        
        Different skill levels focus on different aspects of movement quality:
        - Beginners: Heavy emphasis on safety and basic depth
        - Intermediate: Balanced focus with tempo and stability
        - Advanced: Fine-tuned biomechanics and symmetry
        - Professional: Full analysis including advanced patterns
        
        Returns:
            Dictionary of analyzer weights that sum to 1.0
        """
        skill_level = self.user_profile.skill_level if self.user_profile else UserLevel.BEGINNER
        
        if skill_level == UserLevel.BEGINNER:
            # Beginners: Focus on fundamental movement patterns
            return {
                'safety': 0.25,       # Important but not overwhelming for beginners
                'depth': 0.40,        # Primary focus on learning basic depth
                'stability': 0.30,    # Basic balance development
                'tempo': 0.05,        # Minimal tempo awareness
                'symmetry': 0.0,      # Not evaluated yet
                'butt_wink': 0.0,     # Too advanced
                'knee_valgus': 0.0,   # Too advanced
                'head_position': 0.0, # Too advanced
                'foot_stability': 0.0 # Too advanced
            }
        
        elif skill_level == UserLevel.INTERMEDIATE:
            # Intermediate: Balanced approach with more components introduced
            return {
                'safety': 0.30,       # Moderate safety focus
                'depth': 0.25,        # Consistent depth expected
                'stability': 0.20,    # Good stability expected
                'tempo': 0.15,        # Tempo control introduced
                'symmetry': 0.08,     # Basic symmetry awareness
                'butt_wink': 0.02,    # Basic spinal awareness introduction
                'knee_valgus': 0.0,   # Not yet evaluated
                'head_position': 0.0, # Not yet evaluated
                'foot_stability': 0.0 # Not yet evaluated
            }
        
        elif skill_level == UserLevel.ADVANCED:
            # Advanced: Full biomechanical analysis with comprehensive detail
            return {
                'safety': 0.35,       # Strong safety focus
                'depth': 0.20,        # Expected to hit depth consistently
                'stability': 0.15,    # Good stability expected
                'tempo': 0.12,        # Good tempo control expected
                'symmetry': 0.10,     # Symmetry becomes important
                'butt_wink': 0.04,    # Advanced pattern awareness
                'knee_valgus': 0.02,  # Advanced pattern awareness
                'head_position': 0.01, # Fine motor control development
                'foot_stability': 0.01 # Fine stability control
            }
        
        elif skill_level == UserLevel.EXPERT:
            # Expert: Comprehensive analysis with MAXIMUM safety emphasis
            return {
                'safety': 0.45,       # Maximum safety standards - highest priority
                'depth': 0.20,        # Consistent depth precision expected
                'stability': 0.12,    # Advanced stability control
                'tempo': 0.08,        # Precise tempo control
                'symmetry': 0.07,     # Bilateral balance critical
                'butt_wink': 0.04,    # Advanced spinal mechanics monitoring
                'knee_valgus': 0.02,  # Advanced knee tracking
                'head_position': 0.01, # Fine motor control
                'foot_stability': 0.01 # Foundation stability
            }
        
        else:
            # Fallback to intermediate weights
            self.logger.warning(f"Unknown skill level {skill_level}, using intermediate weights")
            return self._get_skill_based_weights_for_intermediate()
    
    def _get_skill_based_weights_for_intermediate(self) -> Dict[str, float]:
        """Helper method for fallback intermediate weights"""
        return {
            'safety': 0.35, 'depth': 0.25, 'stability': 0.20, 'tempo': 0.15, 'symmetry': 0.05,
            'butt_wink': 0.0, 'knee_valgus': 0.0, 'head_position': 0.0, 'foot_stability': 0.0
        }
    
    def _get_analyzer_priority(self, analyzer_name: str) -> int:
        """
        Get priority ranking for analyzers (1 = highest priority).
        Used for feedback prioritization and fault hierarchy.
        """
        priority_map = {
            'safety': 1,        # Most critical
            'depth': 2,         # Core movement quality
            'stability': 3,     # Important for injury prevention
            'tempo': 4,         # Movement control
            'symmetry': 5,      # Balance and coordination
            'butt_wink': 6,     # Advanced biomechanics
            'knee_valgus': 7,   # Advanced biomechanics
            'head_position': 8, # Fine motor control
            'foot_stability': 9 # Fine stability control
        }
        return priority_map.get(analyzer_name, 10)

    
    def grade_repetition(self, frame_metrics: List[BiomechanicalMetrics]) -> dict:
        """
        ENHANCED: Robust multi-component scoring with input validation.
        
        This method prevents the "broken compass" problem by scoring each component
        independently and combining them with weights, so no single issue destroys the entire score.
        """
        # TASK 1: Input validation and contract enforcement
        validation_result = self._validate_input_contracts(frame_metrics)
        if not validation_result['is_valid']:
            logger.error(f"Input validation failed: {validation_result['error_message']}")
            return {
                'score': 0,
                'faults': ['SYSTEM_ERROR'],
                'feedback': [f"Analysis failed: {validation_result['error_message']}"],
                'scoring_method': 'input_validation_failed',
                'validation_result': validation_result
            }
        
        # Log any data quality warnings
        for warning in validation_result['warnings']:
            logger.warning(f"Data quality issue: {warning}")
        
        # TASK 1: Check analyzer-specific data requirements
        active_analyzers = self._get_active_analyzers()
        data_requirements = self._check_data_requirements(frame_metrics, active_analyzers)
        
        if not data_requirements['all_met']:
            logger.warning(f"Some analyzers cannot run due to missing data: {data_requirements['missing']}")
            # Continue with reduced analyzer set rather than failing completely
            usable_analyzers = {
                name: analyzer for name, analyzer in active_analyzers.items()
                if data_requirements['analyzer_status'][name]['can_analyze']
            }
            logger.info(f"Proceeding with {len(usable_analyzers)}/{len(active_analyzers)} analyzers")
        else:
            usable_analyzers = active_analyzers
        
        # Ensure we're working with a fresh session (prevents carryover)
        self.ensure_fresh_session()
        
        if not frame_metrics:
            logger.warning("FormGrader: No frame metrics provided")
            return {
                'score': 0,
                'faults': ['NO_DATA'],
                'feedback': ["No movement data available for analysis."],
                'scoring_method': 'input_validation_failed',
                'validation_result': {'is_valid': False, 'error_message': 'No data provided'}
            }
        
        rep_number = len(self.recent_scores) + 1
        logger.info(f"FormGrader: VALIDATED ANALYSIS - Rep #{rep_number} with {len(usable_analyzers)} analyzers")
        
        # TASK 5: Get skill-based dynamic weights
        skill_weights = self._get_skill_based_weights()
        
        # Calculate component scores separately using dynamic weights
        component_scores = {}
        all_faults = []
        analysis_details = {}
        
        # Analyze each component based on skill level and active analyzers
        for analyzer_name, analyzer in usable_analyzers.items():
            weight = skill_weights.get(analyzer_name, 0.0)
            
            # Skip analyzers with zero weight for this skill level
            if weight <= 0.0:
                logger.debug(f"Skipping {analyzer_name} (weight: {weight:.3f} for {self.user_profile.skill_level})")
                continue
            
            # Only analyze if the analyzer can handle this difficulty/data
            if hasattr(analyzer, 'can_analyze') and not analyzer.can_analyze(frame_metrics, self.difficulty):
                logger.debug(f"Skipping {analyzer_name} - cannot analyze current difficulty/data")
                continue
            
            # Perform analysis
            result = analyzer.analyze(frame_metrics)
            score = self._calculate_component_score(result, base_score=100)
            
            component_scores[analyzer_name] = {
                'score': score,
                'weight': weight,
                'priority': self._get_analyzer_priority(analyzer_name),
                'result': result
            }
            
            all_faults.extend(result.get('faults', []))
            analysis_details[analyzer_name] = result
            
            logger.debug(f"FormGrader: {analyzer_name.title()}: {score:.1f}% (weight: {weight:.1%})")
        
        # Calculate weighted final score - PREVENTS "broken compass" problem
        weighted_score = 0.0
        total_weight = 0.0
        
        for component, data in component_scores.items():
            weighted_score += data['score'] * data['weight']
            total_weight += data['weight']
        
        base_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # ENHANCEMENT: Add data-driven variation based on actual movement quality
        final_score = int(self._add_realistic_variation(base_score, frame_metrics, rep_number))
        
        # TASK 6: Apply intelligent fault hierarchy to prevent double-penalization
        filtered_faults = self._apply_intelligent_fault_hierarchy(all_faults, component_scores)
        
        # Generate varied, contextual feedback
        feedback = self._generate_prioritized_feedback(component_scores, final_score, rep_number)
        
        logger.info(f"FormGrader: SCORE: {base_score:.1f}% → {final_score}% (after data-driven variation)")
        logger.info(f"FormGrader: FAULTS: {len(all_faults)} total → {len(filtered_faults)} after hierarchy filtering")
        
        self.recent_scores.append(final_score)
        
        # PHASE 2: Enhanced feedback integration
        enhanced_feedback_result = self._process_enhanced_feedback(
            filtered_faults, analysis_details, final_score, frame_metrics, rep_number
        )
        
        result = {
            'score': final_score,
            'base_score': base_score,  # FIXED: Include base score for validation
            'faults': filtered_faults,  # TASK 6: Use hierarchy-filtered faults
            'raw_faults': all_faults,   # Keep original for debugging/analysis
            'feedback': feedback,
            'component_scores': component_scores,
            'analysis_details': analysis_details,
            'scoring_method': 'balanced_multi_component_with_hierarchy',
            'phase_durations': {'total': len(frame_metrics) / 30.0},
            # Add difficulty tracking data for CSV logging
            'difficulty_data': {
                'difficulty_level': self.difficulty,
                'skill_level': self.user_profile.skill_level.value if self.user_profile and self.user_profile.skill_level else self.difficulty,
                'threshold_multiplier': self.difficulty_thresholds.get(self.difficulty, 1.0),
                'component_weights': self.component_weights,
                'active_analyzers': list(self.component_weights.keys())
            }
        }
        
        # Add enhanced feedback to result if available
        if enhanced_feedback_result:
            result['enhanced_feedback'] = enhanced_feedback_result
        
        return result
    
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
    
    def _apply_intelligent_fault_hierarchy(self, all_faults: List[str], component_scores: Dict[str, Any]) -> List[str]:
        """
        TASK 6: Intelligent fault hierarchy to prevent double-penalization - FIXED VERSION.
        
        CRITICAL FIX: Use actual FaultType enum values that analyzers generate,
        not made-up fault names that never match.
        
        Many movement faults are related and stem from the same root cause.
        This method identifies fault relationships and filters redundant penalties
        to provide more accurate and fair scoring.
        
        Returns:
            Filtered list of primary faults, removing redundant secondary faults
        """
        if not all_faults:
            return all_faults
        
        # FIXED: Define fault relationships using ACTUAL fault strings generated by analyzers
        # UPDATED: Keep partial_rep visible for better user feedback
        fault_hierarchy = {
            # Safety faults take highest precedence but don't suppress effectiveness feedback
            'SEVERE_BACK_ROUNDING': {  # Actual string generated by SafetyAnalyzer
                'suppresses': [
                    'moderate_back_rounding',  # Less severe back issue
                    'BAD_BACK_ROUND',          # General back issue
                    'BAD_BACK_WARP',           # Butt wink is secondary to severe rounding
                    'BAD_HEAD'                 # Head position affected by back rounding
                    # REMOVED: 'partial_rep' - Users need to see depth issues separately!
                ],
                'reasoning': 'Severe back rounding is critical safety issue but users still need depth feedback'
            },
            
            # Depth hierarchy - most severe depth fault suppresses lesser ones
            'BAD_SHALLOW_DEPTH': {
                'suppresses': [
                    'INSUFFICIENT_DEPTH'     # Less severe depth issue
                    # REMOVED: 'partial_rep' - Let partial_rep show for different reasons
                ],
                'reasoning': 'Very shallow squats encompass insufficient depth but not all partial reps'
            },
            
            # Stability hierarchy - severe instability encompasses other balance issues
            'SEVERE_INSTABILITY': {
                'suppresses': [
                    'moderate_instability',   # Less severe instability
                    'FOOT_INSTABILITY',       # Foot issues are secondary to major instability
                    'BAD_TOE'                 # Heel lift is secondary to major balance issues
                ],
                'reasoning': 'Major stability issues encompass minor balance problems'
            },
            
            # Knee tracking hierarchy - major knee issues suppress minor ones
            'BAD_INNER_THIGH': {  # Knee valgus
                'suppresses': [
                    'KNEE_VALGUS',            # Alternative knee tracking fault
                    'FOOT_INSTABILITY'        # Foot position often relates to knee tracking
                ],
                'reasoning': 'Major knee tracking issues cause related stability problems'
            },
            
            # Tempo hierarchy - severe tempo issues suppress related faults
            'TOO_FAST': {  # Actual fault generated by TempoAnalyzer
                'suppresses': [
                    'erratic_tempo',          # Related tempo issue
                    'tempo_inconsistency'     # Consistency is secondary to speed issues
                ],
                'reasoning': 'Major tempo violations encompass minor timing issues'
            }
        }
        
        # Find which primary faults are present
        primary_faults_present = set()
        faults_to_suppress = set()
        
        for fault in all_faults:
            if fault in fault_hierarchy:
                primary_faults_present.add(fault)
                # Mark secondary faults for suppression
                suppressed_faults = fault_hierarchy[fault]['suppresses']
                for suppressed_fault in suppressed_faults:
                    if suppressed_fault in all_faults:
                        faults_to_suppress.add(suppressed_fault)
                        self.logger.debug(f"Fault hierarchy: {fault} suppresses {suppressed_fault}")
        
        # Create filtered fault list
        filtered_faults = []
        suppressed_count = 0
        
        for fault in all_faults:
            if fault not in faults_to_suppress:
                filtered_faults.append(fault)
            else:
                suppressed_count += 1
                self.logger.debug(f"Suppressed secondary fault: {fault}")
        
        # Log hierarchy decisions for academic transparency
        if suppressed_count > 0:
            self.logger.info(f"Intelligent fault hierarchy: {suppressed_count} secondary faults suppressed")
            self.logger.info(f"Primary faults present: {list(primary_faults_present)}")
            self.logger.info(f"Filtered: {len(all_faults)} → {len(filtered_faults)} faults")
        
        return filtered_faults

    def _add_realistic_variation(self, base_score: float, frame_metrics: List, rep_number: int) -> float:
        """
        Add DATA-DRIVEN variation based on actual movement quality analysis.
        
        Instead of simulating variation with random numbers, this calculates real metrics 
        from the user's actual movement data to adjust scores based on genuine performance factors.
        
        Real Analysis Factors:
        - Movement consistency: Calculated from joint angle variability (CV = std/mean)
        - Tempo quality: Based on actual movement phases and timing
        - Stability assessment: Uses real center-of-mass sway measurements  
        - Fatigue detection: Analyzes actual score trends from recent performance
        - Smoothness metrics: Calculates movement jerk from position data
        
        Args:
            base_score: Base weighted score from analyzers
            frame_metrics: Actual movement data from the user's performance
            rep_number: Current repetition number for fatigue analysis
            
        Returns:
            Adjusted score based on real movement quality factors
        """
        import math
        import numpy as np
        
        # Start with base score
        varied_score = base_score
        variation_factors = []
        
        # Factor 1: REAL Movement Consistency Analysis
        if len(frame_metrics) > 10:
            # Analyze actual knee angle consistency throughout the movement
            knee_angles = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
            if knee_angles and len(knee_angles) > 5:
                # Calculate coefficient of variation (std/mean) for consistency
                mean_angle = np.mean(knee_angles)
                std_angle = np.std(knee_angles)
                cv = std_angle / mean_angle if mean_angle > 0 else 0
                
                # Convert to consistency score: lower CV = higher consistency
                consistency_score = max(0, 1.0 - (cv * 2))  # CV > 0.5 = poor consistency
                
                # Apply consistency adjustment based on real data
                if consistency_score < 0.7:  # Poor consistency (CV > 0.15)
                    consistency_adjustment = -3 * (0.7 - consistency_score)  # Up to -3 points
                elif consistency_score > 0.9:  # Excellent consistency (CV < 0.05)
                    consistency_adjustment = 2 * (consistency_score - 0.9) * 10  # Up to +2 points
                else:
                    consistency_adjustment = 0
                    
                variation_factors.append(consistency_adjustment)
                self.logger.debug(f"Movement consistency: CV={cv:.3f}, score={consistency_score:.3f}, adj={consistency_adjustment:.1f}")
        
        # Factor 2: REAL Tempo Analysis from Movement Data
        if len(frame_metrics) > 15:
            rep_duration = len(frame_metrics) / 30.0  # Convert frames to seconds (30 FPS)
            
            # Analyze movement phases from actual data
            knee_angles = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
            if knee_angles:
                # Find descent and ascent phases
                min_angle_frame = knee_angles.index(min(knee_angles))
                descent_duration = (min_angle_frame / len(knee_angles)) * rep_duration
                ascent_duration = ((len(knee_angles) - min_angle_frame) / len(knee_angles)) * rep_duration
                
                # Optimal tempo ranges based on biomechanics research
                optimal_total = (2.0, 4.0)  # 2-4 seconds total
                optimal_descent = (1.0, 2.5)  # 1-2.5 seconds descent
                
                tempo_adjustment = 0
                
                # Total duration analysis
                if rep_duration < optimal_total[0]:  # Too fast
                    tempo_adjustment -= (optimal_total[0] - rep_duration) * 2  # -2 per second under
                elif rep_duration > optimal_total[1]:  # Too slow
                    tempo_adjustment -= (rep_duration - optimal_total[1]) * 1  # -1 per second over
                elif optimal_total[0] <= rep_duration <= optimal_total[1]:  # Perfect
                    tempo_adjustment += 1  # Bonus for optimal timing
                
                # Descent phase analysis
                if descent_duration > optimal_descent[1]:  # Descent too slow
                    tempo_adjustment -= 0.5
                elif descent_duration < optimal_descent[0]:  # Descent too fast
                    tempo_adjustment -= 1
                    
                variation_factors.append(tempo_adjustment)
                self.logger.debug(f"Tempo analysis: total={rep_duration:.1f}s, descent={descent_duration:.1f}s, adj={tempo_adjustment:.1f}")
        
        # Factor 3: REAL Stability Analysis from Center of Mass Data
        if len(frame_metrics) > 10:
            com_x_values = [fm.center_of_mass_x for fm in frame_metrics]
            com_y_values = [fm.center_of_mass_y for fm in frame_metrics]
            
            if com_x_values and com_y_values:
                # Calculate actual postural sway
                x_sway = np.std(com_x_values)
                y_sway = np.std(com_y_values)
                total_sway = math.sqrt(x_sway**2 + y_sway**2)
                
                # Stability thresholds based on research
                excellent_sway = 0.01   # Very stable
                poor_sway = 0.05       # Unstable
                
                if total_sway > poor_sway:  # Poor stability
                    stability_adjustment = -2 - min(3, (total_sway - poor_sway) * 100)
                elif total_sway < excellent_sway:  # Excellent stability
                    stability_adjustment = 1.5
                else:  # Normal range
                    stability_adjustment = 0
                    
                variation_factors.append(stability_adjustment)
                self.logger.debug(f"Stability analysis: sway={total_sway:.4f}, adj={stability_adjustment:.1f}")
        
        # Factor 4: REAL Fatigue Analysis Based on Rep History
        if rep_number > 3 and len(self.recent_scores) >= 3:
            # Calculate actual performance decline trend
            recent_scores = list(self.recent_scores)[-3:]  # Last 3 scores
            if len(recent_scores) >= 3:
                # Linear regression to detect declining trend
                x_vals = list(range(len(recent_scores)))
                slope = np.polyfit(x_vals, recent_scores, 1)[0]  # Linear trend
                
                # If scores are declining (negative slope), apply fatigue penalty
                if slope < -2:  # Declining more than 2 points per rep
                    fatigue_adjustment = min(-1, slope / 2)  # Progressive penalty
                    variation_factors.append(fatigue_adjustment)
                    self.logger.debug(f"Fatigue detected: slope={slope:.2f}, adj={fatigue_adjustment:.1f}")
                elif slope > 1:  # Improving performance (learning effect)
                    improvement_bonus = min(1, slope / 3)
                    variation_factors.append(improvement_bonus)
                    self.logger.debug(f"Improvement detected: slope={slope:.2f}, adj={improvement_bonus:.1f}")
        
        # Factor 5: REAL Smoothness Analysis from Movement Jerk
        if len(frame_metrics) > 5:
            # Calculate movement smoothness from velocity changes
            positions = [(fm.center_of_mass_x, fm.center_of_mass_y) for fm in frame_metrics]
            if len(positions) > 3:
                # Calculate velocities and accelerations
                velocities = []
                for i in range(1, len(positions)):
                    dx = positions[i][0] - positions[i-1][0]
                    dy = positions[i][1] - positions[i-1][1]
                    velocity = math.sqrt(dx**2 + dy**2)
                    velocities.append(velocity)
                
                # Calculate jerk (rate of change of acceleration)
                if len(velocities) > 2:
                    jerks = []
                    for i in range(2, len(velocities)):
                        jerk = abs(velocities[i] - 2*velocities[i-1] + velocities[i-2])
                        jerks.append(jerk)
                    
                    if jerks:
                        avg_jerk = np.mean(jerks)
                        # Smooth movement has low jerk
                        if avg_jerk < 0.001:  # Very smooth
                            smoothness_adjustment = 1
                        elif avg_jerk > 0.01:  # Jerky movement
                            smoothness_adjustment = -2
                        else:
                            smoothness_adjustment = 0
                            
                        variation_factors.append(smoothness_adjustment)
                        self.logger.debug(f"Smoothness analysis: jerk={avg_jerk:.4f}, adj={smoothness_adjustment:.1f}")
        
        # Apply all variation factors
        total_variation = sum(variation_factors)
        varied_score += total_variation
        
        # Ensure realistic bounds
        final_score = max(0, min(100, varied_score))
        
        if variation_factors:
            self.logger.debug(f"DATA-DRIVEN Score variation: {base_score:.1f} → {final_score:.1f} "
                             f"(factors: {[f'{f:.1f}' for f in variation_factors]})")
        
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
        """
        FIXED: Validate the base score calculation (before variation is applied)
        
        This validates that the weighted averaging calculation is correct,
        not the final score which includes data-driven variation.
        
        The mismatch was: final_score = base_score + variation, but we were
        comparing final_score to expected_base_score, which will always differ.
        """
        validation = {
            'final_score': grading_result.get('score', 0),
            'base_score': grading_result.get('base_score', 0),  # FIXED: Validate base score
            'is_valid': True,
            'calculation_details': [],
            'component_breakdown': {}
        }
        
        # Extract component scores from grading result
        component_scores = grading_result.get('component_scores', {})
        
        if not component_scores:
            validation['validation_method'] = 'skipped_no_component_data'
            return validation
        
        # Replicate the exact weighted calculation from grade_repetition
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
        
        # Calculate expected base score (before variation)
        expected_base_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # FIXED: Validate against base score, not final score
        actual_base_score = validation['base_score']
        score_diff = abs(expected_base_score - actual_base_score)
        
        if score_diff > 0.1:  # Allow small rounding differences
            validation['is_valid'] = False
            validation['expected_base_score'] = expected_base_score
            validation['actual_base_score'] = actual_base_score
            validation['difference'] = score_diff
            validation['error'] = 'base_score_calculation_mismatch'
        else:
            validation['is_valid'] = True
            validation['expected_base_score'] = expected_base_score
            validation['validation_method'] = 'base_score_weighted_component_matching'
        
        # Also validate that variation was applied correctly
        variation_applied = validation['final_score'] - validation['base_score']
        validation['variation_applied'] = variation_applied
        validation['variation_reasonable'] = abs(variation_applied) <= 8  # Max ±8 points variation
        
        if not validation['variation_reasonable']:
            validation['variation_warning'] = f'Large variation applied: {variation_applied:.1f} points'
        
        # Add summary
        validation['summary'] = {
            'base_score_valid': validation['is_valid'],
            'variation_reasonable': validation['variation_reasonable'],
            'total_weight_used': total_weight,
            'components_analyzed': len(component_scores)
        }
        
        return validation

