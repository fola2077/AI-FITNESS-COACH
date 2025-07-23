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
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
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

class AnthropometricNormalizer:
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

class IntelligentFormGrader:
    """
    Advanced form grading engine with context awareness and personalization.
    
    This is the core of the rule-based analysis system, implementing
    sophisticated grading logic that adapts to user characteristics
    and provides nuanced, fair assessment.
    """
    
    def __init__(self, user_profile: UserProfile = None):
        self.user_profile = user_profile or UserProfile()
        self.movement_analyzer = MovementQualityAnalyzer()
        self.fatigue_predictor = FatiguePredictor()
        self.normalizer = AnthropometricNormalizer()
        
        # Adaptive thresholds based on user level
        self.thresholds = self._initialize_thresholds()
        
        # Grading history for trend analysis
        self.recent_scores = deque(maxlen=10)
        self.fault_frequency = defaultdict(int)
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize adaptive thresholds based on user skill level.
        
        Returns:
            Dictionary of thresholds organized by category and metric
        """
        base_thresholds = {
            'depth': {
                'excellent': 80,    # Hip angle at bottom
                'good': 90,
                'acceptable': 100,
                'poor': 110
            },
            'back_safety': {
                'excellent': 160,   # Back angle (higher = straighter)
                'good': 150,
                'acceptable': 140,
                'poor': 130
            },
            'knee_valgus': {
                'excellent': 5,     # Maximum inward deviation (degrees)
                'good': 10,
                'acceptable': 15,
                'poor': 20
            },
            'forward_lean': {
                'excellent': 15,    # Maximum forward lean (degrees)
                'good': 25,
                'acceptable': 35,
                'poor': 45
            }
        }
        
        # Adjust based on user level
        level_multipliers = {
            UserLevel.BEGINNER: {'tolerance': 1.3, 'penalty': 0.7},
            UserLevel.INTERMEDIATE: {'tolerance': 1.0, 'penalty': 1.0},
            UserLevel.ADVANCED: {'tolerance': 0.8, 'penalty': 1.2},
            UserLevel.EXPERT: {'tolerance': 0.6, 'penalty': 1.5}
        }
        
        multiplier = level_multipliers[self.user_profile.skill_level]
        
        # Apply tolerance adjustment (more lenient thresholds for beginners)
        adjusted_thresholds = {}
        for category, thresholds in base_thresholds.items():
            adjusted_thresholds[category] = {}
            for quality, value in thresholds.items():
                if category in ['depth', 'knee_valgus', 'forward_lean']:
                    # For these metrics, higher tolerance means more lenient (higher values)
                    adjusted_thresholds[category][quality] = value * multiplier['tolerance']
                else:
                    # For back safety, higher tolerance means more lenient (lower values)
                    adjusted_thresholds[category][quality] = value / multiplier['tolerance']
        
        return adjusted_thresholds
    
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
    
    def grade_repetition(self, rep_data: list) -> dict:
        """
        Analyzes a list of frame data for a full repetition.

        Args:
            rep_data: A list of metric dictionaries, one for each frame of the rep.

        Returns:
            A dictionary containing the overall score, faults, and other analysis.
        """
        if not rep_data:
            return {'score': 0, 'faults': [], 'summary': "No data for analysis."}

        overall_faults = set()
        min_angles = {}
        max_angles = {}
        
        # Initialize angle tracking
        if rep_data and 'angles' in rep_data[0]:
            angle_keys = rep_data[0]['angles'].keys()
            min_angles = {key: 360 for key in angle_keys}
            max_angles = {key: 0 for key in angle_keys}
        
        # Aggregate data across the entire repetition
        for frame_metrics in rep_data:
            angles = frame_metrics.get('angles', {})
            for angle_name, value in angles.items():
                if value < min_angles.get(angle_name, 360):
                    min_angles[angle_name] = value
                if value > max_angles.get(angle_name, 0):
                    max_angles[angle_name] = value

        # Comprehensive fault analysis
        self._analyze_depth_faults(min_angles, overall_faults)
        self._analyze_symmetry_faults(rep_data, overall_faults)
        self._analyze_stability_faults(rep_data, overall_faults)
        self._analyze_form_faults(rep_data, overall_faults)

        # Calculate final score
        final_score = self._calculate_rep_score(overall_faults)
        
        return {
            'score': final_score,
            'faults': list(overall_faults),
            'summary': f"Rep analysis complete. Score: {final_score}%",
            'min_angles': min_angles,
            'max_angles': max_angles,
            'confidence': self._calculate_confidence_from_data(rep_data),
            'recommendations': self._get_recommendations(overall_faults)
        }
    
    def _analyze_depth_faults(self, min_angles: dict, faults: set):
        """Analyze depth-related faults"""
        knee_angle = min_angles.get('knee', min_angles.get('left_knee', 180))
        if knee_angle > 100:  # Insufficient depth threshold
            faults.add("INSUFFICIENT_DEPTH")
    
    def _analyze_symmetry_faults(self, rep_data: list, faults: set):
        """Analyze symmetry-related faults"""
        if not rep_data:
            return
            
        # Check for asymmetric movement patterns
        left_knee_angles = []
        right_knee_angles = []
        
        for frame in rep_data:
            angles = frame.get('angles', {})
            if 'left_knee' in angles and 'right_knee' in angles:
                left_knee_angles.append(angles['left_knee'])
                right_knee_angles.append(angles['right_knee'])
        
        if left_knee_angles and right_knee_angles:
            avg_diff = sum(abs(l - r) for l, r in zip(left_knee_angles, right_knee_angles)) / len(left_knee_angles)
            if avg_diff > 15:  # More than 15 degrees average difference
                faults.add("ASYMMETRIC_MOVEMENT")
    
    def _analyze_stability_faults(self, rep_data: list, faults: set):
        """Analyze stability-related faults"""
        # Check for excessive movement or instability
        if len(rep_data) < 5:
            return
            
        # Simple stability check based on center of mass movement
        com_positions = []
        for frame in rep_data:
            if 'center_of_mass' in frame:
                com_positions.append(frame['center_of_mass'])
        
        if len(com_positions) > 5:
            x_variance = np.var([pos[0] for pos in com_positions])
            if x_variance > 0.01:  # Threshold for excessive lateral movement
                faults.add("LATERAL_INSTABILITY")
    
    def _analyze_form_faults(self, rep_data: list, faults: set):
        """Analyze general form faults"""
        # Check for common form issues
        back_angles = []
        for frame in rep_data:
            angles = frame.get('angles', {})
            if 'back' in angles:
                back_angles.append(angles['back'])
        
        if back_angles:
            max_back_angle = max(back_angles)
            if max_back_angle > 30:  # Excessive forward lean
                faults.add("FORWARD_LEAN")
            if max_back_angle > 45:  # Back rounding
                faults.add("BACK_ROUNDING")
    
    def _calculate_rep_score(self, faults: set) -> int:
        """Calculate overall repetition score based on faults"""
        base_score = 100
        
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
