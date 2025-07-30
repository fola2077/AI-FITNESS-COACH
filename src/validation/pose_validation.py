"""
Comprehensive validation system for pose detection and form grading.
Helps debug and verify that landmarks, angles, and scores are accurate.
"""

import numpy as np
import cv2
import math
import time
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

@dataclass
class ValidationResults:
    """Results from validation checks"""
    valid: bool = True
    warnings: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []

class PoseValidationSystem:
    """
    Comprehensive validation system for pose detection and form grading.
    Helps debug and verify that landmarks, angles, and scores are accurate.
    """
    
    def __init__(self):
        self.validation_log = []
        self.angle_history = []
        
    def validate_landmarks(self, landmarks, frame_shape) -> Dict:
        """
        Validate that MediaPipe landmarks are reasonable and properly positioned.
        
        Args:
            landmarks: MediaPipe pose landmarks
            frame_shape: (height, width) of the frame
            
        Returns:
            Dictionary with validation results
        """
        if not landmarks:
            return {'valid': False, 'error': 'No landmarks detected'}
        
        validation_results = {
            'valid': True,
            'warnings': [],
            'landmark_positions': {},
            'visibility_scores': {},
            'anatomical_checks': {}
        }
        
        height, width = frame_shape[:2]
        
        # Key landmarks for squat analysis
        key_landmarks = {
            'nose': 0,
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28
        }
        
        for name, idx in key_landmarks.items():
            if idx < len(landmarks.landmark):
                landmark = landmarks.landmark[idx]
                
                # Convert to pixel coordinates
                x_px = int(landmark.x * width)
                y_px = int(landmark.y * height)
                
                validation_results['landmark_positions'][name] = {
                    'x': x_px, 'y': y_px,
                    'x_norm': landmark.x, 'y_norm': landmark.y,
                    'visibility': landmark.visibility
                }
                validation_results['visibility_scores'][name] = landmark.visibility
                
                # Check if landmark is within frame bounds
                if not (0 <= x_px <= width and 0 <= y_px <= height):
                    validation_results['warnings'].append(f'{name} is outside frame bounds')
                
                # Check visibility threshold
                if landmark.visibility < 0.5:
                    validation_results['warnings'].append(f'{name} has low visibility: {landmark.visibility:.2f}')
        
        # Anatomical consistency checks
        self._check_anatomical_consistency(validation_results)
        
        return validation_results
    
    def _check_anatomical_consistency(self, validation_results):
        """Check if landmark positions make anatomical sense"""
        positions = validation_results['landmark_positions']
        checks = validation_results['anatomical_checks']
        
        # Check if shoulders are above hips
        if 'left_shoulder' in positions and 'left_hip' in positions:
            shoulder_y = positions['left_shoulder']['y']
            hip_y = positions['left_hip']['y']
            checks['shoulders_above_hips'] = shoulder_y < hip_y
            if shoulder_y >= hip_y:
                validation_results['warnings'].append('Shoulders appear below hips - check pose detection')
        
        # Check if hips are above knees
        if 'left_hip' in positions and 'left_knee' in positions:
            hip_y = positions['left_hip']['y']
            knee_y = positions['left_knee']['y']
            checks['hips_above_knees'] = hip_y < knee_y
            if hip_y >= knee_y:
                validation_results['warnings'].append('Hips appear below knees - unusual pose')
        
        # Check bilateral symmetry
        left_shoulder = positions.get('left_shoulder', {})
        right_shoulder = positions.get('right_shoulder', {})
        if left_shoulder and right_shoulder:
            height_diff = abs(left_shoulder['y'] - right_shoulder['y'])
            checks['shoulder_symmetry'] = height_diff < 30  # pixels
            if height_diff >= 30:
                validation_results['warnings'].append(f'Shoulder height asymmetry: {height_diff}px')
    
    def validate_angle_calculations(self, landmarks, calculated_angles) -> Dict:
        """
        Validate that angle calculations are mathematically correct.
        
        Args:
            landmarks: MediaPipe pose landmarks
            calculated_angles: Dictionary of calculated angles
            
        Returns:
            Validation results for angles
        """
        validation_results = {
            'valid': True,
            'angle_checks': {},
            'warnings': [],
            'manual_calculations': {}
        }
        
        # Manually recalculate key angles to verify
        try:
            # Recalculate left knee angle manually
            hip = landmarks.landmark[23]  # left hip
            knee = landmarks.landmark[25]  # left knee  
            ankle = landmarks.landmark[27]  # left ankle
            
            manual_knee_angle = self._calculate_angle_manual(
                (hip.x, hip.y), (knee.x, knee.y), (ankle.x, ankle.y)
            )
            
            validation_results['manual_calculations']['knee_left'] = manual_knee_angle
            
            # Compare with calculated angle
            if 'knee_left' in calculated_angles:
                calculated = calculated_angles['knee_left']
                difference = abs(manual_knee_angle - calculated)
                validation_results['angle_checks']['knee_left_accuracy'] = difference < 5  # degrees
                
                if difference >= 5:
                    validation_results['warnings'].append(
                        f'Knee angle calculation mismatch: manual={manual_knee_angle:.1f}°, '
                        f'calculated={calculated:.1f}°, diff={difference:.1f}°'
                    )
            
            # Validate angle ranges
            for angle_name, angle_value in calculated_angles.items():
                if not (0 <= angle_value <= 180):
                    validation_results['warnings'].append(
                        f'{angle_name} angle out of valid range: {angle_value:.1f}°'
                    )
                    validation_results['valid'] = False
                    
        except Exception as e:
            validation_results['warnings'].append(f'Error in angle validation: {e}')
            validation_results['valid'] = False
            
        return validation_results
    
    def _calculate_angle_manual(self, point1: Tuple, point2: Tuple, point3: Tuple) -> float:
        """
        Manually calculate angle between three points for validation.
        
        Args:
            point1, point2, point3: (x, y) coordinates
            point2 is the vertex of the angle
            
        Returns:
            Angle in degrees
        """
        # Calculate vectors
        vector1 = (point1[0] - point2[0], point1[1] - point2[1])
        vector2 = (point3[0] - point2[0], point3[1] - point2[1])
        
        # Calculate dot product and magnitudes
        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        magnitude1 = math.sqrt(vector1[0]**2 + vector1[1]**2)
        magnitude2 = math.sqrt(vector2[0]**2 + vector2[1]**2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        # Calculate angle
        cos_angle = dot_product / (magnitude1 * magnitude2)
        cos_angle = max(-1, min(1, cos_angle))  # Clamp to valid range
        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg
    
    def validate_biomechanical_metrics(self, metrics) -> Dict:
        """
        Validate that biomechanical metrics are reasonable for squat movement.
        
        Args:
            metrics: BiomechanicalMetrics object
            
        Returns:
            Validation results
        """
        validation_results = {
            'valid': True,
            'warnings': [],
            'metric_ranges': {},
            'squat_phase_analysis': {}
        }
        
        # Expected ranges for squat exercises
        expected_ranges = {
            'knee_angle_left': (30, 180),    # Full flex to full extension
            'knee_angle_right': (30, 180),
            'hip_angle': (45, 180),          # Hip flexion range
            'back_angle': (60, 180),         # Back angle (180° = upright)
        }
        
        # Validate each metric
        for metric_name, (min_val, max_val) in expected_ranges.items():
            metric_value = getattr(metrics, metric_name, 0)
            validation_results['metric_ranges'][metric_name] = {
                'value': metric_value,
                'expected_range': (min_val, max_val),
                'in_range': min_val <= metric_value <= max_val
            }
            
            if not (min_val <= metric_value <= max_val):
                validation_results['warnings'].append(
                    f'{metric_name} outside expected range: {metric_value:.1f}° '
                    f'(expected: {min_val}-{max_val}°)'
                )
        
        # Analyze squat phase based on knee angle
        knee_avg = (metrics.knee_angle_left + metrics.knee_angle_right) / 2
        if knee_avg > 160:
            phase = 'STANDING'
        elif knee_avg > 120:
            phase = 'DESCENT/ASCENT'
        elif knee_avg > 90:
            phase = 'BOTTOM'
        else:
            phase = 'DEEP_SQUAT'
        
        validation_results['squat_phase_analysis'] = {
            'detected_phase': phase,
            'knee_average': knee_avg,
            'depth_percentage': max(0, (180 - knee_avg) / 90 * 100)  # Rough depth estimate
        }
        
        return validation_results
    
    def create_validation_visualization(self, frame, landmarks, angles, metrics, validation_results):
        """
        Create a visual overlay showing validation information.
        
        Args:
            frame: Original video frame
            landmarks: MediaPipe landmarks
            angles: Calculated angles
            metrics: BiomechanicalMetrics
            validation_results: Results from validation methods
            
        Returns:
            Frame with validation overlay
        """
        vis_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # Draw landmark positions with validation status
        landmark_positions = validation_results.get('landmark_positions', {})
        for name, pos in landmark_positions.items():
            x, y = pos['x'], pos['y']
            visibility = pos['visibility']
            
            # Color based on visibility
            if visibility > 0.8:
                color = (0, 255, 0)  # Green - good
            elif visibility > 0.5:
                color = (0, 255, 255)  # Yellow - moderate
            else:
                color = (0, 0, 255)  # Red - poor
            
            cv2.circle(vis_frame, (x, y), 5, color, -1)
            cv2.putText(vis_frame, f'{name[:3]}', (x-15, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        # Display angle information
        y_offset = 30
        for angle_name, angle_value in angles.items():
            text = f'{angle_name}: {angle_value:.1f}°'
            cv2.putText(vis_frame, text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 25
        
        # Display warnings
        if validation_results.get('warnings'):
            cv2.putText(vis_frame, 'VALIDATION WARNINGS:', (10, height-100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            for i, warning in enumerate(validation_results['warnings'][:3]):  # Show max 3
                cv2.putText(vis_frame, warning[:50], (10, height-70+i*20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        return vis_frame

    def log_validation_results(self, validation_results, rep_number=None):
        """Log validation results for analysis"""
        log_entry = {
            'timestamp': time.time(),
            'rep_number': rep_number,
            'results': validation_results
        }
        self.validation_log.append(log_entry)
        
        # Print summary
        warnings = validation_results.get('warnings', [])
        if warnings:
            print(f"[VALIDATION] Rep {rep_number} - {len(warnings)} warnings:")
            for warning in warnings:
                print(f"  ⚠️ {warning}")
        else:
            print(f"[VALIDATION] Rep {rep_number} - All checks passed ✅")
    
    def validate_rep_analysis(self, frame_metrics, pose_detector, form_grader) -> Dict:
        """
        Comprehensive validation of a complete repetition analysis.
        
        Args:
            frame_metrics: List of BiomechanicalMetrics for the rep
            pose_detector: PoseDetector instance for validation
            form_grader: FormGrader instance for validation
            
        Returns:
            Dictionary with complete validation results
        """
        validation_results = {
            'landmarks': {'is_valid': True, 'issues': []},
            'angles': {'is_valid': True, 'issues': []},
            'biomechanics': {'is_valid': True, 'issues': []},
            'overall_valid': True,
            'frame_count': len(frame_metrics),
            'summary': {}
        }
        
        print(f"🔍 Validating rep with {len(frame_metrics)} frames...")
        
        # 1. Validate frame metrics
        valid_frame_count = 0
        angle_issues = []
        visibility_issues = []
        
        for i, fm in enumerate(frame_metrics):
            # Check landmark visibility
            if fm.landmark_visibility < 0.5:
                visibility_issues.append(f"Frame {i}: Low visibility {fm.landmark_visibility:.2f}")
            
            # Check angle ranges
            angles = {
                'knee_left': fm.knee_angle_left,
                'knee_right': fm.knee_angle_right,
                'hip_angle': fm.hip_angle,
                'back_angle': fm.back_angle
            }
            
            frame_valid = True
            for angle_name, angle_value in angles.items():
                if angle_value <= 0 or angle_value > 180:
                    angle_issues.append(f"Frame {i}: Invalid {angle_name} = {angle_value:.1f}°")
                    frame_valid = False
            
            if frame_valid:
                valid_frame_count += 1
        
        # Update landmarks validation
        if visibility_issues:
            validation_results['landmarks']['issues'].extend(visibility_issues[:5])  # Limit to first 5
            if len(visibility_issues) > 5:
                validation_results['landmarks']['issues'].append(f"... and {len(visibility_issues)-5} more visibility issues")
        
        # Update angles validation
        if angle_issues:
            validation_results['angles']['issues'].extend(angle_issues[:5])  # Limit to first 5
            validation_results['angles']['is_valid'] = False
            if len(angle_issues) > 5:
                validation_results['angles']['issues'].append(f"... and {len(angle_issues)-5} more angle issues")
        
        # 2. Validate biomechanical ranges
        if frame_metrics:
            knee_angles = [fm.knee_angle_left for fm in frame_metrics if fm.knee_angle_left > 0]
            back_angles = [fm.back_angle for fm in frame_metrics if fm.back_angle > 0]
            
            biomech_issues = []
            
            if knee_angles:
                min_knee = min(knee_angles)
                max_knee = max(knee_angles)
                range_knee = max_knee - min_knee
                
                if range_knee < 20:
                    biomech_issues.append(f"Insufficient knee movement range: {range_knee:.1f}°")
                if min_knee < 30:
                    biomech_issues.append(f"Extremely deep squat detected: {min_knee:.1f}°")
                if min_knee > 140:
                    biomech_issues.append(f"Very shallow movement: {min_knee:.1f}°")
            
            if back_angles:
                min_back = min(back_angles)
                max_back = max(back_angles)
                
                if min_back < 45:
                    biomech_issues.append(f"Extreme forward lean detected: {min_back:.1f}°")
                if max_back > 200:  # Should not exceed 180° much
                    biomech_issues.append(f"Invalid back angle calculation: {max_back:.1f}°")
            
            if biomech_issues:
                validation_results['biomechanics']['issues'] = biomech_issues
                validation_results['biomechanics']['is_valid'] = False
        
        # 3. Overall validation
        if not validation_results['angles']['is_valid'] or not validation_results['biomechanics']['is_valid']:
            validation_results['overall_valid'] = False
        
        # 4. Create summary
        validation_results['summary'] = {
            'valid_frames_percentage': (valid_frame_count / len(frame_metrics)) * 100 if frame_metrics else 0,
            'total_issues': len(visibility_issues) + len(angle_issues) + len(validation_results['biomechanics']['issues']),
            'recommendation': (
                'Analysis reliable' if validation_results['overall_valid'] and valid_frame_count / len(frame_metrics) > 0.8 else
                'Analysis questionable - check data quality' if validation_results['overall_valid'] else
                'Analysis unreliable - significant data issues detected'
            )
        }
        
        # Print validation summary
        print(f"Landmark validation: {'✅ PASS' if validation_results['landmarks']['is_valid'] else '❌ FAIL'}")
        print(f"Angle validation: {'✅ PASS' if validation_results['angles']['is_valid'] else '❌ FAIL'}")
        print(f"Biomechanics validation: {'✅ PASS' if validation_results['biomechanics']['is_valid'] else '❌ FAIL'}")
        print(f"Valid frames: {valid_frame_count}/{len(frame_metrics)} ({validation_results['summary']['valid_frames_percentage']:.1f}%)")
        print(f"Recommendation: {validation_results['summary']['recommendation']}")
        
        return validation_results
