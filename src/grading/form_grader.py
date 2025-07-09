import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import copy

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
    
    def copy(self):
        """Create a copy of this fault details object"""
        return copy.deepcopy(self)

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
            ),
            'INCOMPLETE_ATTEMPT': FaultDetails(
                fault_type='INCOMPLETE_ATTEMPT',
                severity=FaultSeverity.MAJOR,
                confidence=0.9,
                description='Squat attempt not completed through full range of motion',
                correction_cue='Focus on completing the full movement pattern',
                penalty_weight=35
            ),
            'SEVERE_KNEE_VALGUS': FaultDetails(
                fault_type='SEVERE_KNEE_VALGUS',
                severity=FaultSeverity.CRITICAL,
                confidence=0.0,
                description='Dangerous knee collapse - stop immediately',
                correction_cue='Stop movement, focus on knee tracking over toes',
                penalty_weight=50
            ),
            'PARTIAL_RANGE_OF_MOTION': FaultDetails(
                fault_type='PARTIAL_RANGE_OF_MOTION',
                severity=FaultSeverity.MAJOR,
                confidence=0.8,
                description='Consistently not reaching full depth',
                correction_cue='Work on mobility to achieve full squat depth',
                penalty_weight=30
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

    def analyze_attempt_completion(self, metrics: BiomechanicalMetrics, phase: str) -> Dict:
        """
        Analyze if a squat attempt is complete and log any failures
        
        Args:
            metrics: Current frame biomechanical metrics
            phase: Current squat phase ('descending', 'bottom', 'ascending', 'top')
            
        Returns:
            Dict containing attempt status and failure reasons
        """
        attempt_status = {
            'is_complete': False,
            'is_valid': False,
            'failure_reasons': [],
            'completion_score': 0,
            'phase_reached': phase
        }
        
        # Check if attempt reached minimum depth
        depth_reached = metrics.depth_achieved or metrics.knee_angle <= self.thresholds['depth_knee_angle']
        
        if not depth_reached:
            attempt_status['failure_reasons'].append('INSUFFICIENT_DEPTH')
            attempt_status['completion_score'] = 30  # Partial credit for attempting
        
        # Check if attempt completed full range of motion
        if phase in ['ascending', 'top'] and depth_reached:
            attempt_status['is_complete'] = True
            attempt_status['completion_score'] = 100
        elif phase == 'bottom' and depth_reached:
            attempt_status['is_complete'] = True
            attempt_status['completion_score'] = 80  # Good depth but incomplete ascent
        elif phase == 'descending':
            attempt_status['completion_score'] = 20  # Early in attempt
        
        # Check for safety violations that invalidate the attempt
        safety_violations = []
        
        # Critical back rounding
        if metrics.back_angle < self.thresholds['back_safety_angle']:
            safety_violations.append('BACK_ROUNDING')
        
        # Severe knee valgus
        if metrics.knee_valgus_ratio < 0.6:  # More strict than normal threshold
            safety_violations.append('SEVERE_KNEE_VALGUS')
        
        # Heel rise indicating instability
        if metrics.ankle_angle < self.thresholds['ankle_dorsiflexion']:
            safety_violations.append('HEEL_RISE')
        
        # If safety violations are present, mark as invalid
        if safety_violations:
            attempt_status['is_valid'] = False
            attempt_status['failure_reasons'].extend(safety_violations)
            attempt_status['completion_score'] = max(0, attempt_status['completion_score'] - 30)
        else:
            attempt_status['is_valid'] = True
        
        return attempt_status

    def log_failed_attempt(self, metrics: BiomechanicalMetrics, failure_reasons: List[str]) -> Dict:
        """
        Log details of a failed squat attempt for learning purposes
        
        Args:
            metrics: Biomechanical metrics at failure point
            failure_reasons: List of reasons why attempt failed
            
        Returns:
            Dict containing failure analysis and coaching recommendations
        """
        failure_analysis = {
            'failure_type': 'INCOMPLETE_ATTEMPT',
            'primary_reason': failure_reasons[0] if failure_reasons else 'UNKNOWN',
            'all_reasons': failure_reasons,
            'depth_achieved': metrics.depth_achieved,
            'knee_angle_at_failure': metrics.knee_angle,
            'safety_compromised': any(reason in ['BACK_ROUNDING', 'SEVERE_KNEE_VALGUS'] 
                                   for reason in failure_reasons),
            'coaching_points': []
        }
        
        # Generate specific coaching based on failure type
        if 'INSUFFICIENT_DEPTH' in failure_reasons:
            failure_analysis['coaching_points'].extend([
                "Focus on sitting back into your heels",
                "Aim to get your hip crease below knee level",
                "Work on ankle and hip mobility outside of training"
            ])
        
        if 'BACK_ROUNDING' in failure_reasons:
            failure_analysis['coaching_points'].extend([
                "Stop the movement - spine safety is priority",
                "Focus on chest up, shoulders back",
                "Reduce depth until you can maintain spine neutrality"
            ])
        
        if 'SEVERE_KNEE_VALGUS' in failure_reasons:
            failure_analysis['coaching_points'].extend([
                "Focus on pushing knees out over toes",
                "Strengthen hip abductors and glutes",
                "Reduce weight/depth until tracking improves"
            ])
        
        if 'HEEL_RISE' in failure_reasons:
            failure_analysis['coaching_points'].extend([
                "Keep heels planted throughout movement",
                "Work on ankle mobility and calf flexibility",
                "Consider heel elevation temporarily"
            ])
        
        return failure_analysis

    def grade_incomplete_attempt(self, metrics: BiomechanicalMetrics, phase_reached: str) -> Dict:
        """
        Grade an incomplete squat attempt
        
        Args:
            metrics: Best biomechanical metrics achieved during attempt
            phase_reached: Furthest phase reached ('descending', 'bottom', 'ascending')
            
        Returns:
            Dict containing partial scoring and feedback
        """
        partial_score = 0
        feedback_points = []
        
        # Base score based on phase reached
        phase_scores = {
            'descending': 25,
            'bottom': 60,
            'ascending': 80,
            'top': 100
        }
        
        partial_score = phase_scores.get(phase_reached, 0)
        
        # Adjust score based on form quality during the attempt
        form_analysis = self.analyze_squat_form(metrics)
        form_quality_bonus = min(20, form_analysis['overall_score'] * 0.2)
        partial_score += form_quality_bonus
        
        # Generate feedback for incomplete attempt
        feedback_points.append(f"Attempt reached {phase_reached} phase")
        
        if phase_reached == 'descending':
            feedback_points.append("Focus on completing the full range of motion")
        elif phase_reached == 'bottom':
            feedback_points.append("Good depth achieved, work on driving up")
        elif phase_reached == 'ascending':
            feedback_points.append("Nearly complete - focus on finishing strong")
        
        # Add form-specific feedback
        if form_analysis['detected_faults']:
            priority_fault = form_analysis['detected_faults'][0]
            feedback_points.append(f"Improvement needed: {priority_fault.correction_cue}")
        
        return {
            'partial_score': min(100, int(partial_score)),
            'phase_reached': phase_reached,
            'form_score': form_analysis['overall_score'],
            'feedback_points': feedback_points,
            'attempt_type': 'INCOMPLETE',
            'recommendations': form_analysis['recommendations'][:3]  # Top 3 recommendations
        }

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
    
    def analyze_attempt_statistics(self, attempt_data: List[Dict]) -> Dict:
        """
        Analyze statistics across multiple squat attempts
        
        Args:
            attempt_data: List of attempt dictionaries with completion status and scores
            
        Returns:
            Dict containing comprehensive attempt statistics
        """
        if not attempt_data:
            return {
                'total_attempts': 0,
                'successful_reps': 0,
                'failed_attempts': 0,
                'success_rate': 0,
                'average_completion_score': 0,
                'failure_patterns': {},
                'improvement_trends': []
            }
        
        total_attempts = len(attempt_data)
        successful_reps = sum(1 for attempt in attempt_data if attempt.get('is_complete', False))
        failed_attempts = total_attempts - successful_reps
        
        # Calculate success rate
        success_rate = (successful_reps / total_attempts) * 100 if total_attempts > 0 else 0
        
        # Average completion score
        completion_scores = [attempt.get('completion_score', 0) for attempt in attempt_data]
        avg_completion = np.mean(completion_scores) if completion_scores else 0
        
        # Analyze failure patterns
        failure_patterns = {}
        for attempt in attempt_data:
            if not attempt.get('is_complete', False):
                for reason in attempt.get('failure_reasons', []):
                    failure_patterns[reason] = failure_patterns.get(reason, 0) + 1
        
        # Calculate failure percentages
        failure_percentages = {
            reason: (count / failed_attempts) * 100 
            for reason, count in failure_patterns.items()
        } if failed_attempts > 0 else {}
        
        # Identify improvement trends (if we have enough data)
        improvement_trends = []
        if len(attempt_data) >= 5:
            # Check if success rate is improving over time
            first_half = attempt_data[:len(attempt_data)//2]
            second_half = attempt_data[len(attempt_data)//2:]
            
            first_half_success = sum(1 for a in first_half if a.get('is_complete', False)) / len(first_half)
            second_half_success = sum(1 for a in second_half if a.get('is_complete', False)) / len(second_half)
            
            if second_half_success > first_half_success:
                improvement_trends.append("Success rate improving over session")
            elif second_half_success < first_half_success:
                improvement_trends.append("Success rate declining - fatigue or form breakdown")
            
            # Check completion score trends
            first_half_scores = [a.get('completion_score', 0) for a in first_half]
            second_half_scores = [a.get('completion_score', 0) for a in second_half]
            
            if np.mean(second_half_scores) > np.mean(first_half_scores):
                improvement_trends.append("Form quality improving throughout session")
        
        return {
            'total_attempts': total_attempts,
            'successful_reps': successful_reps,
            'failed_attempts': failed_attempts,
            'success_rate': round(success_rate, 1),
            'average_completion_score': round(avg_completion, 1),
            'failure_patterns': failure_percentages,
            'improvement_trends': improvement_trends,
            'completion_scores': completion_scores,
            'most_common_failure': max(failure_patterns, key=failure_patterns.get) if failure_patterns else None
        }

    def generate_session_summary(self, attempt_statistics: Dict, overall_metrics: Dict) -> Dict:
        """
        Generate a comprehensive session summary with actionable insights
        
        Args:
            attempt_statistics: Output from analyze_attempt_statistics
            overall_metrics: Overall session performance metrics
            
        Returns:
            Dict containing session summary and recommendations
        """
        summary = {
            'session_grade': self._calculate_session_grade(attempt_statistics, overall_metrics),
            'key_achievements': [],
            'primary_focus_areas': [],
            'specific_recommendations': [],
            'next_session_goals': []
        }
        
        # Identify achievements
        if attempt_statistics['success_rate'] >= 80:
            summary['key_achievements'].append("Excellent rep completion rate")
        elif attempt_statistics['success_rate'] >= 60:
            summary['key_achievements'].append("Good consistency in movement completion")
        
        if attempt_statistics['average_completion_score'] >= 75:
            summary['key_achievements'].append("Strong form quality maintained")
        
        if 'Form quality improving throughout session' in attempt_statistics['improvement_trends']:
            summary['key_achievements'].append("Progressive improvement during session")
        
        # Identify focus areas based on failure patterns
        failure_patterns = attempt_statistics['failure_patterns']
        
        if failure_patterns.get('INSUFFICIENT_DEPTH', 0) > 30:
            summary['primary_focus_areas'].append("Depth Achievement")
            summary['specific_recommendations'].extend([
                "Work on ankle and hip mobility daily",
                "Practice goblet squats for depth training",
                "Consider heel elevation during training"
            ])
        
        if failure_patterns.get('BACK_ROUNDING', 0) > 20:
            summary['primary_focus_areas'].append("Spinal Safety")
            summary['specific_recommendations'].extend([
                "Reduce load until form improves",
                "Focus on thoracic spine mobility",
                "Strengthen posterior chain muscles"
            ])
        
        if failure_patterns.get('SEVERE_KNEE_VALGUS', 0) > 15:
            summary['primary_focus_areas'].append("Knee Tracking")
            summary['specific_recommendations'].extend([
                "Strengthen hip abductors and glutes",
                "Practice bodyweight squats with resistance band",
                "Work on lateral movement patterns"
            ])
        
        # Set next session goals
        if attempt_statistics['success_rate'] < 70:
            summary['next_session_goals'].append("Increase rep completion rate to 70%+")
        
        if attempt_statistics['average_completion_score'] < 70:
            summary['next_session_goals'].append("Improve average form score to 70+")
        
        if not summary['next_session_goals']:
            summary['next_session_goals'].append("Maintain current quality while adding volume")
        
        return summary

    def _calculate_session_grade(self, attempt_stats: Dict, overall_metrics: Dict) -> str:
        """Calculate overall session grade based on multiple factors"""
        grade_points = 0
        
        # Success rate contribution (40%)
        success_rate = attempt_stats['success_rate']
        if success_rate >= 90:
            grade_points += 40
        elif success_rate >= 80:
            grade_points += 35
        elif success_rate >= 70:
            grade_points += 30
        elif success_rate >= 60:
            grade_points += 25
        else:
            grade_points += success_rate * 0.4
        
        # Form quality contribution (40%)
        avg_completion = attempt_stats['average_completion_score']
        grade_points += avg_completion * 0.4
        
        # Improvement trend bonus (20%)
        if 'improving' in str(attempt_stats['improvement_trends']):
            grade_points += 20
        elif 'declining' in str(attempt_stats['improvement_trends']):
            grade_points += 10
        else:
            grade_points += 15
        
        return self._score_to_grade(int(grade_points))