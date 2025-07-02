import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class FaultSeverity(Enum):
    CRITICAL = "critical"  # Safety issues
    MAJOR = "major"       # Form breakdown
    MINOR = "minor"       # Optimization issues

@dataclass
class BiomechanicalMetrics:
    """Container for all biomechanical measurements"""
    knee_angle: float
    hip_angle: float
    back_angle: float
    trunk_angle: float
    ankle_angle: float
    knee_valgus_ratio: float
    asymmetry_score: float
    depth_achieved: bool
    confidence_scores: Dict[str, float]

@dataclass
class FaultDetails:
    """Detailed fault information"""
    fault_type: str
    severity: FaultSeverity
    confidence: float
    description: str
    correction_cue: str
    penalty_weight: float

class SquatFormGrader:
    """
    Advanced form grading system with research-based biomechanical analysis
    """
    
    def __init__(self):
        # Research-based thresholds
        self.thresholds = {
            'depth_knee_angle': 90,
            'back_safety_angle': 150,
            'knee_valgus_ratio': 0.8,
            'forward_lean_angle': 45,
            'asymmetry_threshold': 0.15,  # 15% asymmetry
            'ankle_dorsiflexion': 20,
            'confidence_minimum': 0.6
        }
        
        # Fault definitions with penalties
        self.fault_definitions = {
            'BACK_ROUNDING': FaultDetails(
                fault_type='BACK_ROUNDING',
                severity=FaultSeverity.CRITICAL,
                confidence=0.0,
                description='Excessive spinal flexion - safety risk',
                correction_cue='Keep your chest up and maintain spine neutrality',
                penalty_weight=40
            ),
            'KNEE_VALGUS': FaultDetails(
                fault_type='KNEE_VALGUS',
                severity=FaultSeverity.MAJOR,
                confidence=0.0,
                description='Knees caving inward',
                correction_cue='Push your knees out in line with your toes',
                penalty_weight=30
            ),
            'INSUFFICIENT_DEPTH': FaultDetails(
                fault_type='INSUFFICIENT_DEPTH',
                severity=FaultSeverity.MAJOR,
                confidence=0.0,
                description='Hip crease not below knee level',
                correction_cue='Squat deeper - aim for hip below knee',
                penalty_weight=25
            ),
            'FORWARD_LEAN': FaultDetails(
                fault_type='FORWARD_LEAN',
                severity=FaultSeverity.MAJOR,
                confidence=0.0,
                description='Excessive forward torso lean',
                correction_cue='Stay more upright, engage your core',
                penalty_weight=20
            ),
            'ASYMMETRIC_MOVEMENT': FaultDetails(
                fault_type='ASYMMETRIC_MOVEMENT',
                severity=FaultSeverity.MINOR,
                confidence=0.0,
                description='Uneven left-right movement pattern',
                correction_cue='Focus on balanced, symmetrical movement',
                penalty_weight=15
            ),
            'HEEL_RISE': FaultDetails(
                fault_type='HEEL_RISE',
                severity=FaultSeverity.MINOR,
                confidence=0.0,
                description='Heels lifting off ground',
                correction_cue='Keep your heels down, improve ankle mobility',
                penalty_weight=10
            )
        }
        
        # Scoring weights for different aspects
        self.scoring_weights = {
            'safety': 0.4,      # Back angle, knee tracking
            'depth': 0.3,       # Squat depth achievement
            'technique': 0.2,   # Forward lean, asymmetry
            'stability': 0.1    # Heel rise, balance
        }

    def analyze_squat_form(self, metrics: BiomechanicalMetrics) -> Dict:
        """
        Comprehensive form analysis returning detailed scoring
        """
        detected_faults = []
        fault_confidences = {}
        
        # Safety Analysis (Critical)
        back_fault = self._analyze_back_safety(metrics)
        if back_fault:
            detected_faults.append(back_fault)
            fault_confidences[back_fault.fault_type] = back_fault.confidence
        
        knee_fault = self._analyze_knee_tracking(metrics)
        if knee_fault:
            detected_faults.append(knee_fault)
            fault_confidences[knee_fault.fault_type] = knee_fault.confidence
        
        # Depth Analysis
        depth_fault = self._analyze_depth(metrics)
        if depth_fault:
            detected_faults.append(depth_fault)
            fault_confidences[depth_fault.fault_type] = depth_fault.confidence
        
        # Technique Analysis
        lean_fault = self._analyze_forward_lean(metrics)
        if lean_fault:
            detected_faults.append(lean_fault)
            fault_confidences[lean_fault.fault_type] = lean_fault.confidence
        
        asymmetry_fault = self._analyze_asymmetry(metrics)
        if asymmetry_fault:
            detected_faults.append(asymmetry_fault)
            fault_confidences[asymmetry_fault.fault_type] = asymmetry_fault.confidence
        
        # Calculate overall score
        overall_score = self._calculate_weighted_score(detected_faults, metrics)
        
        # Generate detailed feedback
        feedback = self._generate_detailed_feedback(detected_faults, overall_score)
        
        return {
            'overall_score': overall_score,
            'detected_faults': detected_faults,
            'fault_confidences': fault_confidences,
            'feedback': feedback,
            'safety_score': self._calculate_safety_score(detected_faults),
            'technique_score': self._calculate_technique_score(detected_faults),
            'recommendations': self._generate_recommendations(detected_faults)
        }

    def _analyze_back_safety(self, metrics: BiomechanicalMetrics) -> Optional[FaultDetails]:
        """Analyze spinal safety - most critical assessment"""
        if metrics.back_angle < self.thresholds['back_safety_angle']:
            confidence = metrics.confidence_scores.get('back_angle', 0.0)
            
            if confidence > self.thresholds['confidence_minimum']:
                fault = self.fault_definitions['BACK_ROUNDING'].copy()
                fault.confidence = confidence
                
                # Adjust penalty based on severity
                angle_deviation = self.thresholds['back_safety_angle'] - metrics.back_angle
                severity_multiplier = min(2.0, angle_deviation / 30)  # More severe = higher penalty
                fault.penalty_weight *= severity_multiplier
                
                return fault
        return None

    def _analyze_knee_tracking(self, metrics: BiomechanicalMetrics) -> Optional[FaultDetails]:
        """Analyze knee valgus/varus"""
        if metrics.knee_valgus_ratio < self.thresholds['knee_valgus_ratio']:
            confidence = metrics.confidence_scores.get('knee_valgus', 0.0)
            
            if confidence > self.thresholds['confidence_minimum']:
                fault = self.fault_definitions['KNEE_VALGUS'].copy()
                fault.confidence = confidence
                
                # Adjust based on severity of valgus
                ratio_deviation = self.thresholds['knee_valgus_ratio'] - metrics.knee_valgus_ratio
                severity_multiplier = min(1.5, ratio_deviation / 0.2)
                fault.penalty_weight *= severity_multiplier
                
                return fault
        return None

    def _analyze_depth(self, metrics: BiomechanicalMetrics) -> Optional[FaultDetails]:
        """Analyze squat depth achievement"""
        if not metrics.depth_achieved:
            confidence = metrics.confidence_scores.get('depth', 0.8)  # High confidence for depth
            
            fault = self.fault_definitions['INSUFFICIENT_DEPTH'].copy()
            fault.confidence = confidence
            
            # Adjust penalty based on how close to depth
            if metrics.knee_angle > 110:  # Very shallow
                fault.penalty_weight *= 1.2
            elif metrics.knee_angle < 95:  # Close to depth
                fault.penalty_weight *= 0.7
            
            return fault
        return None

    def _analyze_forward_lean(self, metrics: BiomechanicalMetrics) -> Optional[FaultDetails]:
        """Analyze excessive forward lean"""
        if metrics.trunk_angle > self.thresholds['forward_lean_angle']:
            confidence = metrics.confidence_scores.get('trunk_angle', 0.0)
            
            if confidence > self.thresholds['confidence_minimum']:
                fault = self.fault_definitions['FORWARD_LEAN'].copy()
                fault.confidence = confidence
                
                # Adjust based on lean severity
                lean_excess = metrics.trunk_angle - self.thresholds['forward_lean_angle']
                severity_multiplier = min(1.5, lean_excess / 20)
                fault.penalty_weight *= severity_multiplier
                
                return fault
        return None

    def _analyze_asymmetry(self, metrics: BiomechanicalMetrics) -> Optional[FaultDetails]:
        """Analyze movement asymmetry"""
        if metrics.asymmetry_score > self.thresholds['asymmetry_threshold']:
            confidence = 0.7  # Medium confidence for asymmetry detection
            
            fault = self.fault_definitions['ASYMMETRIC_MOVEMENT'].copy()
            fault.confidence = confidence
            
            # Scale penalty with asymmetry severity
            asymmetry_excess = metrics.asymmetry_score - self.thresholds['asymmetry_threshold']
            severity_multiplier = min(1.3, asymmetry_excess / 0.1)
            fault.penalty_weight *= severity_multiplier
            
            return fault
        return None

    def _calculate_weighted_score(self, faults: List[FaultDetails], metrics: BiomechanicalMetrics) -> int:
        """Calculate weighted overall score (0-100)"""
        base_score = 100
        
        # Apply fault penalties
        for fault in faults:
            penalty = fault.penalty_weight * fault.confidence
            base_score -= penalty
        
        # Bonus for perfect depth
        if metrics.depth_achieved and metrics.knee_angle < 85:
            base_score += 5  # Bonus for excellent depth
        
        # Ensure score stays within bounds
        return max(0, min(100, int(base_score)))

    def _calculate_safety_score(self, faults: List[FaultDetails]) -> int:
        """Calculate safety-specific score"""
        safety_score = 100
        
        for fault in faults:
            if fault.severity == FaultSeverity.CRITICAL:
                safety_score -= fault.penalty_weight * fault.confidence
        
        return max(0, min(100, int(safety_score)))

    def _calculate_technique_score(self, faults: List[FaultDetails]) -> int:
        """Calculate technique-specific score"""
        technique_score = 100
        
        for fault in faults:
            if fault.severity in [FaultSeverity.MAJOR, FaultSeverity.MINOR]:
                technique_score -= fault.penalty_weight * fault.confidence * 0.7
        
        return max(0, min(100, int(technique_score)))

    def _generate_detailed_feedback(self, faults: List[FaultDetails], score: int) -> Dict:
        """Generate comprehensive feedback"""
        feedback = {
            'overall_grade': self._score_to_grade(score),
            'priority_corrections': [],
            'secondary_improvements': [],
            'positive_aspects': []
        }
        
        # Sort faults by severity and confidence
        sorted_faults = sorted(faults, 
                             key=lambda f: (f.severity.value, -f.confidence), 
                             reverse=True)
        
        # Categorize feedback
        for fault in sorted_faults:
            if fault.severity == FaultSeverity.CRITICAL:
                feedback['priority_corrections'].append({
                    'issue': fault.description,
                    'correction': fault.correction_cue,
                    'confidence': fault.confidence
                })
            else:
                feedback['secondary_improvements'].append({
                    'issue': fault.description,
                    'correction': fault.correction_cue,
                    'confidence': fault.confidence
                })
        
        # Add positive feedback
        if score >= 80:
            feedback['positive_aspects'].append("Excellent overall form!")
        elif score >= 70:
            feedback['positive_aspects'].append("Good technique with room for refinement")
        elif len([f for f in faults if f.severity == FaultSeverity.CRITICAL]) == 0:
            feedback['positive_aspects'].append("Safe movement pattern maintained")
        
        return feedback

    def _generate_recommendations(self, faults: List[FaultDetails]) -> List[str]:
        """Generate training recommendations based on faults"""
        recommendations = []
        
        fault_types = [f.fault_type for f in faults]
        
        if 'BACK_ROUNDING' in fault_types:
            recommendations.extend([
                "Work on thoracic spine mobility",
                "Strengthen posterior chain (glutes, hamstrings)",
                "Practice wall sits with proper posture"
            ])
        
        if 'KNEE_VALGUS' in fault_types:
            recommendations.extend([
                "Strengthen hip abductors and external rotators",
                "Improve ankle mobility",
                "Practice lateral band walks"
            ])
        
        if 'INSUFFICIENT_DEPTH' in fault_types:
            recommendations.extend([
                "Work on ankle and hip mobility",
                "Practice goblet squats",
                "Use heel elevation initially"
            ])
        
        if 'FORWARD_LEAN' in fault_types:
            recommendations.extend([
                "Strengthen anterior core",
                "Improve thoracic extension mobility",
                "Practice front-loaded squats"
            ])
        
        return recommendations[:5]  # Limit to top 5 recommendations

    def _score_to_grade(self, score: int) -> str:
        """Convert numerical score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def batch_analyze_video(self, metrics_sequence: List[BiomechanicalMetrics]) -> Dict:
        """Analyze entire video sequence for comprehensive assessment"""
        frame_scores = []
        all_faults = []
        fault_frequency = {}
        
        for metrics in metrics_sequence:
            analysis = self.analyze_squat_form(metrics)
            frame_scores.append(analysis['overall_score'])
            
            for fault in analysis['detected_faults']:
                all_faults.append(fault)
                fault_frequency[fault.fault_type] = fault_frequency.get(fault.fault_type, 0) + 1
        
        # Calculate video-level metrics
        avg_score = np.mean(frame_scores) if frame_scores else 0
        consistency_score = 100 - (np.std(frame_scores) if len(frame_scores) > 1 else 0)
        
        # Identify persistent issues
        total_frames = len(metrics_sequence)
        persistent_faults = {
            fault_type: frequency/total_frames 
            for fault_type, frequency in fault_frequency.items()
            if frequency/total_frames > 0.3  # Present in >30% of frames
        }
        
        return {
            'video_average_score': int(avg_score),
            'consistency_score': int(consistency_score),
            'frame_scores': frame_scores,
            'persistent_faults': persistent_faults,
            'improvement_priorities': self._get_improvement_priorities(persistent_faults),
            'overall_video_grade': self._score_to_grade(int(avg_score))
        }

    def _get_improvement_priorities(self, persistent_faults: Dict[str, float]) -> List[str]:
        """Get prioritized list of improvements based on persistent faults"""
        # Sort by frequency and severity
        fault_priorities = []
        
        for fault_type, frequency in persistent_faults.items():
            fault_def = self.fault_definitions[fault_type]
            priority_score = frequency * fault_def.penalty_weight
            
            if fault_def.severity == FaultSeverity.CRITICAL:
                priority_score *= 2  # Double weight for safety issues
            
            fault_priorities.append((fault_type, priority_score))
        
        # Sort by priority score and return correction cues
        sorted_faults = sorted(fault_priorities, key=lambda x: x[1], reverse=True)
        
        return [
            self.fault_definitions[fault_type].correction_cue 
            for fault_type, _ in sorted_faults[:3]  # Top 3 priorities
        ]