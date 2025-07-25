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
from collections import deque, defaultdict

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
    """Base class for all movement analyzers"""
    
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

class SafetyAnalyzer(BaseAnalyzer):
    """Analyzes critical safety issues like back rounding"""
    
    def __init__(self):
        super().__init__(required_landmarks=[11, 12, 23, 24])  # shoulders, hips
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        back_angles = [fm.back_angle for fm in frame_metrics if fm.back_angle > 0]
        if not back_angles:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        min_back_angle = np.min(back_angles)
        avg_back_angle = np.mean(back_angles)
        
        faults = []
        penalties = []
        
        # Critical back rounding check
        if min_back_angle < 130:  # Severe rounding
            faults.append('SEVERE_BACK_ROUNDING')
            penalty = 35 + (130 - min_back_angle) * 0.8
            penalties.append({'reason': 'Severe Back Rounding - DANGER!', 'amount': min(50, penalty)})
        elif min_back_angle < 145:  # Moderate rounding
            faults.append('BACK_ROUNDING')
            penalty = 20 + (145 - min_back_angle) * 0.5
            penalties.append({'reason': 'Back Rounding', 'amount': min(30, penalty)})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': []}

class DepthAnalyzer(BaseAnalyzer):
    """Analyzes squat depth and detects partial reps"""
    
    def __init__(self):
        super().__init__(required_landmarks=[25, 26, 27, 28])  # knees, ankles
    
    def _check_difficulty(self, difficulty: str) -> bool:
        return difficulty in ['casual', 'professional']
    
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
        
        # Check for partial reps first
        if movement_range < 35:
            faults.append('PARTIAL_REP')
            penalties.append({'reason': f'Partial Rep ({movement_range:.1f}° range)', 'amount': 45})
            return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}
        
        # Range-based depth scoring
        if min_knee_angle > 110:  # Very shallow
            faults.append('VERY_SHALLOW')
            penalty = 25 + (min_knee_angle - 110) * 0.5
            penalties.append({'reason': 'Very Shallow Depth', 'amount': min(35, penalty)})
        elif min_knee_angle > 95:  # Shallow
            faults.append('INSUFFICIENT_DEPTH')
            penalty = 15 + (min_knee_angle - 95) * 0.8
            penalties.append({'reason': 'Insufficient Depth', 'amount': min(25, penalty)})
        elif min_knee_angle < 75:  # Excellent depth
            bonuses.append({'reason': 'Excellent Depth', 'amount': 8})
        elif min_knee_angle < 85:  # Good depth
            bonuses.append({'reason': 'Good Depth', 'amount': 5})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': bonuses}

class StabilityAnalyzer(BaseAnalyzer):
    """Analyzes postural stability and balance"""
    
    def __init__(self):
        super().__init__(required_landmarks=[0, 15, 16])  # nose, ankles for COM
    
    def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Dict[str, Any]:
        if len(frame_metrics) < 10:
            return {'faults': [], 'penalties': [], 'bonuses': []}
        
        com_x = [fm.center_of_mass_x for fm in frame_metrics]
        stability_std = np.std(com_x)
        
        faults = []
        penalties = []
        
        # Adaptive thresholds based on rep length
        base_threshold = 0.018
        if stability_std > base_threshold * 1.8:  # Very unstable
            faults.append('SEVERE_INSTABILITY')
            penalty = 25 + (stability_std - base_threshold) * 1200
            penalties.append({'reason': 'Severe Instability', 'amount': min(35, penalty)})
        elif stability_std > base_threshold * 1.2:  # Moderate instability
            faults.append('POOR_STABILITY')
            penalty = 12 + (stability_std - base_threshold) * 800
            penalties.append({'reason': 'Poor Stability', 'amount': min(20, penalty)})
        
        return {'faults': faults, 'penalties': penalties, 'bonuses': []}

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
    """
    Normalizes biomechanical thresholds based on individual body proportions.
    
    This system accounts for natural anatomical variations to provide fair
    and personalized form assessment.
    """
    
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


class AnthropometricNormalizer:
    """Normalizes scores based on user's physical characteristics"""
    
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


class IntelligentFormGrader:
    """
    Advanced biomechanical analysis engine with modular analyzer system.
    Provides comprehensive movement quality assessment with visibility-aware analysis.
    """
    
    def __init__(self, difficulty: str = "casual", user_profile: UserProfile = None):
        """Initialize the intelligent form grader"""
        self.user_profile = user_profile or UserProfile()
        self.movement_analyzer = MovementQualityAnalyzer()
        self.fatigue_predictor = FatiguePredictor()
        self.normalizer = AnthropometricNormalizer()
        self.difficulty = difficulty.lower()  # 'beginner', 'casual', 'professional'
        self.recent_scores = deque(maxlen=10)
        self.fault_frequency = defaultdict(int)
        
        # Initialize individual analyzers for modular approach
        self.safety_analyzer = SafetyAnalyzer()
        self.depth_analyzer = DepthAnalyzer()
        self.stability_analyzer = StabilityAnalyzer()
        self.tempo_analyzer = TempoAnalyzer()
        self.symmetry_analyzer = SymmetryAnalyzer()
        
        # Update thresholds based on difficulty
        self._update_difficulty_thresholds()
    """Normalizes scores based on user's physical characteristics"""
    
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
    def __init__(self, user_profile: UserProfile = None, difficulty: str = "beginner"):
        self.user_profile = user_profile or UserProfile()
        self.movement_analyzer = MovementQualityAnalyzer()
        self.fatigue_predictor = FatiguePredictor()
        self.normalizer = AnthropometricNormalizer()
        self.difficulty = difficulty.lower()  # 'beginner', 'casual', 'professional'
        self.recent_scores = deque(maxlen=10)
        self.fault_frequency = defaultdict(int)
        
        # Initialize individual analyzers for modular approach
        self.safety_analyzer = SafetyAnalyzer()
        self.depth_analyzer = DepthAnalyzer()
        self.stability_analyzer = StabilityAnalyzer()
        self.tempo_analyzer = TempoAnalyzer()
        self.symmetry_analyzer = SymmetryAnalyzer()
        
        # Update thresholds based on difficulty
        self._update_difficulty_thresholds()
    
    def set_difficulty(self, difficulty: str) -> None:
        """Set difficulty level with validation"""
        difficulty = difficulty.lower()
        if difficulty not in ['beginner', 'casual', 'professional']:
            logging.warning(f"Invalid difficulty '{difficulty}', defaulting to 'casual'")
            difficulty = 'casual'
        
        self.difficulty = difficulty
        self._update_difficulty_thresholds()
        print(f"[FormGrader] Difficulty updated to: {self.difficulty}")
    
    def _update_difficulty_thresholds(self) -> None:
        """Update analyzer configurations based on difficulty level"""
        if self.difficulty == 'beginner':
            # More forgiving thresholds, focus only on safety
            self.safety_analyzer.min_visibility_threshold = 0.6
        elif self.difficulty == 'casual':
            # Standard thresholds, include depth analysis
            self.safety_analyzer.min_visibility_threshold = 0.7
            self.depth_analyzer.min_visibility_threshold = 0.7
        else:  # professional
            # Strict thresholds, all analyzers active
            for analyzer in [self.safety_analyzer, self.depth_analyzer, 
                           self.stability_analyzer, self.tempo_analyzer, 
                           self.symmetry_analyzer]:
                analyzer.min_visibility_threshold = 0.8
    
    def create_biomechanical_metrics(self, pose_landmarks, previous_metrics=None) -> BiomechanicalMetrics:
        """
        Create comprehensive biomechanical metrics from pose landmarks.
        
        Args:
            pose_landmarks: MediaPipe pose landmarks
            previous_metrics: Previous frame metrics for velocity/acceleration calculation
            
        Returns:
            BiomechanicalMetrics object
        """
        if not pose_landmarks:
            return BiomechanicalMetrics()
        
        try:
            # Import pose detector locally to avoid circular imports
            from ..pose.pose_detector import PoseDetector
            detector = PoseDetector()
            
            # Calculate basic angles
            angles = detector.calculate_joint_angles(pose_landmarks)
            
            # Calculate center of mass
            com_x, com_y = detector.calculate_center_of_mass(pose_landmarks)
            
            # Calculate landmark visibility
            visibility = detector.calculate_landmark_visibility(pose_landmarks)
            
            # Calculate velocity and acceleration if previous metrics available
            velocity = 0.0
            acceleration = 0.0
            jerk = 0.0
            
            if previous_metrics:
                # Simple velocity calculation based on COM movement
                dt = 1.0/30.0  # Assume 30 FPS
                dx = com_x - previous_metrics.center_of_mass_x
                dy = com_y - previous_metrics.center_of_mass_y
                velocity = math.sqrt(dx*dx + dy*dy) / dt
                
                # Acceleration calculation
                acceleration = (velocity - previous_metrics.movement_velocity) / dt
                
                # Jerk calculation
                jerk = (acceleration - previous_metrics.acceleration) / dt
            
            # Calculate symmetry metrics
            knee_symmetry = 1.0
            if angles.get('knee_left', 0) > 0 and angles.get('knee_right', 0) > 0:
                knee_symmetry = min(angles['knee_left'], angles['knee_right']) / max(angles['knee_left'], angles['knee_right'])
            
            ankle_symmetry = 1.0
            if angles.get('ankle_left', 0) > 0 and angles.get('ankle_right', 0) > 0:
                ankle_symmetry = min(angles['ankle_left'], angles['ankle_right']) / max(angles['ankle_left'], angles['ankle_right'])
            
            # Create metrics object
            metrics = BiomechanicalMetrics(
                knee_angle_left=angles.get('knee_left', 0),
                knee_angle_right=angles.get('knee_right', 0),
                hip_angle=angles.get('hip', 0),
                back_angle=angles.get('back', 0),
                ankle_angle_left=angles.get('ankle_left', 0),
                ankle_angle_right=angles.get('ankle_right', 0),
                center_of_mass_x=com_x,
                center_of_mass_y=com_y,
                movement_velocity=velocity,
                acceleration=acceleration,
                jerk=jerk,
                knee_symmetry_ratio=knee_symmetry,
                ankle_symmetry_ratio=ankle_symmetry,
                weight_distribution_ratio=1.0,  # Could be calculated from foot pressure if available
                postural_sway=abs(com_x - 0.5),  # Deviation from center
                base_of_support_width=0.6,  # Could be calculated from foot positions
                timestamp=time.time(),
                phase_duration=0.1,  # Assume frame duration
                landmark_visibility=visibility
            )
            
            return metrics
            
        except Exception as e:
            print(f"Error creating biomechanical metrics: {e}")
            return BiomechanicalMetrics()
    
    def grade_repetition(self, frame_metrics: List[BiomechanicalMetrics]) -> dict:
        """
        Grade a complete repetition using modular analyzer system with visibility-aware analysis.
        
        Args:
            frame_metrics: List of BiomechanicalMetrics objects
            
        Returns:
            Dictionary with score, faults, feedback, and detailed analysis
        """
        if not frame_metrics:
            return {
                'score': 0,
                'faults': ['NO_DATA'],
                'phase_durations': {},
                'feedback': ["No movement data available for analysis."],
                'biomechanical_summary': {}
            }
        
        print(f"[FormGrader] Analyzing {len(frame_metrics)} frames with {self.difficulty} difficulty")
        
        # Initialize analysis results
        all_faults = []
        all_penalties = []
        all_bonuses = []
        analysis_results = {}
        
        # Run applicable analyzers based on difficulty and visibility
        analyzers = [
            ('safety', self.safety_analyzer),
            ('depth', self.depth_analyzer),
            ('stability', self.stability_analyzer),
            ('tempo', self.tempo_analyzer),
            ('symmetry', self.symmetry_analyzer)
        ]
        
        for analyzer_name, analyzer in analyzers:
            if analyzer.can_analyze(frame_metrics, self.difficulty):
                try:
                    result = analyzer.analyze(frame_metrics)
                    analysis_results[analyzer_name] = result
                    
                    all_faults.extend(result.get('faults', []))
                    all_penalties.extend(result.get('penalties', []))
                    all_bonuses.extend(result.get('bonuses', []))
                    
                    print(f"[FormGrader] {analyzer_name.title()} analysis: "
                          f"faults={result.get('faults', [])}, "
                          f"penalties={len(result.get('penalties', []))}, "
                          f"bonuses={len(result.get('bonuses', []))}")
                          
                except Exception as e:
                    print(f"[FormGrader] Error in {analyzer_name} analyzer: {e}")
                    continue
            else:
                print(f"[FormGrader] Skipping {analyzer_name} analyzer (difficulty={self.difficulty}, visibility check failed)")
        
        # Calculate final score
        base_score = 100.0
        
        # Apply penalties
        total_penalty = 0.0
        for penalty in all_penalties:
            penalty_amount = penalty.get('amount', 0)
            total_penalty += penalty_amount
            base_score -= penalty_amount
        
        # Apply bonuses
        total_bonus = 0.0
        for bonus in all_bonuses:
            bonus_amount = bonus.get('amount', 0)
            total_bonus += bonus_amount
            base_score += bonus_amount
        
        # Ensure score bounds
        final_score = max(0, min(100, int(base_score)))
        
        # Generate feedback based on results
        feedback = self._generate_feedback(final_score, all_faults, all_penalties, all_bonuses)
        
        # Create biomechanical summary
        biomechanical_summary = self._create_biomechanical_summary(
            frame_metrics, analysis_results, all_penalties, all_bonuses
        )
        
        print(f"[FormGrader] FINAL SCORE: {final_score}% "
              f"(base: 100, penalties: -{total_penalty:.1f}, bonuses: +{total_bonus:.1f})")
        print(f"[FormGrader] Detected faults: {all_faults}")
        
        return {
            'score': final_score,
            'faults': all_faults,
            'feedback': feedback,
            'phase_durations': {'total': len(frame_metrics) / 30.0},
            'biomechanical_summary': biomechanical_summary,
            'analysis_details': analysis_results
        }
    
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

        
        fault_penalties = {
            "INSUFFICIENT_DEPTH": 25,
            "ASYMMETRIC_MOVEMENT": 15,
            "LATERAL_INSTABILITY": 10,
            "FORWARD_LEAN": 15,
            "BACK_ROUNDING": 20,
            "KNEE_VALGUS": 20,
            "HEEL_RISE": 10
        }
        
        for fault in faults:
            penalty = fault_penalties.get(fault, 5)
            base_score -= penalty
        
        return max(0, base_score)
    
    def _calculate_confidence_from_data(self, rep_data: list) -> float:
        """Calculate confidence based on data quality"""
        if not rep_data:
            return 0.0
        
        # Simple confidence based on data completeness
        frame_count = len(rep_data)
        return min(100.0, frame_count * 2)  # Assume 50 frames = 100% confidence
    
    def _get_recommendations(self, faults: set) -> list:
        """Get coaching recommendations based on faults"""
        recommendations = []
        fault_recommendations = {
            "INSUFFICIENT_DEPTH": "Focus on going deeper - sit back and down until thighs are parallel to floor",
            "ASYMMETRIC_MOVEMENT": "Keep movement balanced - check for strength imbalances between sides",
            "LATERAL_INSTABILITY": "Improve core stability - engage your core throughout the movement",
            "FORWARD_LEAN": "Keep chest up and back straight - avoid leaning forward excessively",
            "BACK_ROUNDING": "Maintain neutral spine - avoid rounding your back under load",
            "KNEE_VALGUS": "Track knees over toes - strengthen glutes and improve hip mobility",
            "HEEL_RISE": "Keep feet flat on ground throughout the movement"
        }
        
        for fault in faults:
            if fault in fault_recommendations:
                recommendations.append(fault_recommendations[fault])
        
        if not recommendations:
            recommendations.append("Great form! Keep up the excellent work.")
        
        return recommendations[:3]  # Limit to top 3 recommendations

    def _generate_coaching_cues(self, faults: List[Dict], positive_aspects: List[Dict]) -> List[str]:
        """
        Generate specific, actionable coaching cues based on detected patterns.
        
        Args:
            faults: List of detected faults
            positive_aspects: List of positive aspects
            
        Returns:
            List of coaching cues
        """
        cues = []
        fault_types = [f['type'] for f in faults]
        
        if 'BACK_ROUNDING' in fault_types:
            cues.append("Keep your chest up and maintain a neutral spine throughout the movement.")
        
        if 'KNEE_VALGUS' in fault_types:
            cues.append("Focus on pushing your knees out in line with your toes.")
        
        if 'INSUFFICIENT_DEPTH' in fault_types:
            cues.append("Aim to lower until your hip crease is just below your knee cap.")
        
        if 'FORWARD_LEAN' in fault_types:
            cues.append("Keep your torso more upright by engaging your core and driving through your heels.")
        
        # Add positive reinforcement cues
        positive_types = [p['type'] for p in positive_aspects]
        if 'SMOOTH_MOVEMENT' in positive_types:
            cues.append("Excellent control! Your smooth movement pattern is reducing injury risk.")
        
        if 'EXCELLENT_DEPTH' in positive_types:
            cues.append("Outstanding depth! This maximizes muscle activation and mobility benefits.")
        
        return cues[:3]  # Return max 3 cues to avoid information overload
    
    def _generate_overall_assessment(self, score: float, faults: List[Dict], positive_aspects: List[Dict]) -> str:
        """
        Generate an overall assessment narrative for the repetition.
        
        Args:
            score: Final score for the repetition
            faults: List of detected faults
            positive_aspects: List of positive aspects
            
        Returns:
            Overall assessment string
        """
        if score >= 90:
            return "Exceptional technique demonstrated. This rep showcases excellent movement quality and safety."
        elif score >= 80:
            return "Strong performance with minor areas for refinement. Form is safe and effective."
        elif score >= 70:
            return "Good foundation with some technical issues to address. Focus on highlighted areas."
        elif score >= 60:
            return "Acceptable form but several improvement opportunities. Prioritize safety and consistency."
        else:
            return "Significant form issues detected. Consider form practice with lighter weight or bodyweight."
    
    def _calculate_confidence(self, rep_data: RepetitionData) -> float:
        """
        Calculate confidence level in the analysis based on data quality.
        
        Args:
            rep_data: Repetition data to assess
            
        Returns:
            Confidence score (0-100)
        """
        if not rep_data.frame_metrics:
            return 0.0
        
        # Factors affecting confidence
        factors = []
        
        # 1. Number of frames (more frames = higher confidence)
        frame_count = len(rep_data.frame_metrics)
        frame_confidence = min(100, frame_count * 2)  # Assume 50 frames = 100% confidence
        factors.append(frame_confidence)
        
        # 2. Movement completion (full phase cycle = higher confidence)
        phases_detected = len(rep_data.phase_transitions)
        phase_confidence = min(100, phases_detected * 25)  # 4 phases = 100% confidence
        factors.append(phase_confidence)
        
        # 3. Data consistency (consistent measurements = higher confidence)
        if frame_count > 5:
            valid_hip_angles = [m.hip_angle for m in rep_data.frame_metrics if m.hip_angle > 0]
            if valid_hip_angles:
                angle_std = np.std(valid_hip_angles)
                consistency_confidence = max(0, 100 - angle_std)  # Lower std = higher confidence
                factors.append(consistency_confidence)
            else:
                factors.append(50)
        else:
            factors.append(50)  # Neutral confidence for insufficient data
        
        # 4. Landmark visibility
        if rep_data.frame_metrics:
            avg_visibility = np.mean([m.landmark_visibility for m in rep_data.frame_metrics])
            visibility_confidence = avg_visibility * 100
            factors.append(visibility_confidence)
        
        return np.mean(factors)
    
    def _get_fault_description(self, fault_type: str, severity: FaultSeverity, measured_value: float) -> str:
        """
        Generate human-readable fault descriptions.
        
        Args:
            fault_type: Type of fault detected
            severity: Severity level of the fault
            measured_value: Actual measured value
            
        Returns:
            Human-readable fault description
        """
        descriptions = {
            'BACK_ROUNDING': {
                FaultSeverity.MINOR: f"Slight back rounding detected ({measured_value:.1f}°). Keep chest up.",
                FaultSeverity.MODERATE: f"Moderate back rounding ({measured_value:.1f}°). Focus on neutral spine.",
                FaultSeverity.MAJOR: f"Significant back rounding ({measured_value:.1f}°). Reduce weight and focus on form.",
                FaultSeverity.CRITICAL: f"Dangerous back rounding ({measured_value:.1f}°). Stop and reset form."
            },
            'KNEE_VALGUS': {
                FaultSeverity.MINOR: f"Minor knee cave detected ({measured_value:.1f}°). Push knees out.",
                FaultSeverity.MODERATE: f"Moderate knee valgus ({measured_value:.1f}°). Focus on knee tracking.",
                FaultSeverity.MAJOR: f"Significant knee collapse ({measured_value:.1f}°). Strengthen glutes.",
                FaultSeverity.CRITICAL: f"Severe knee valgus ({measured_value:.1f}°). Risk of injury - reduce load."
            },
            'INSUFFICIENT_DEPTH': {
                FaultSeverity.MINOR: f"Slightly shallow squat ({measured_value:.1f}°). Aim for a bit deeper.",
                FaultSeverity.MODERATE: f"Moderate depth issue ({measured_value:.1f}°). Work on mobility.",
                FaultSeverity.MAJOR: f"Insufficient depth ({measured_value:.1f}°). Focus on hip and ankle mobility.",
                FaultSeverity.CRITICAL: f"Very shallow squat ({measured_value:.1f}°). Practice bodyweight squats first."
            },
            'FORWARD_LEAN': {
                FaultSeverity.MINOR: f"Slight forward lean ({measured_value:.1f}°). Engage core more.",
                FaultSeverity.MODERATE: f"Moderate forward lean ({measured_value:.1f}°). Keep chest up.",
                FaultSeverity.MAJOR: f"Excessive forward lean ({measured_value:.1f}°). Work on ankle mobility.",
                FaultSeverity.CRITICAL: f"Dangerous forward lean ({measured_value:.1f}°). Risk of falling - reset form."
            }
        }
        
        return descriptions.get(fault_type, {}).get(severity, f"Unspecified {fault_type} issue detected.")
