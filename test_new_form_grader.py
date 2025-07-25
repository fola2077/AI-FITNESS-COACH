#!/usr/bin/env python3
"""
Test script for the new modular form grader implementation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.grading.advanced_form_grader import IntelligentFormGrader, BiomechanicalMetrics
import numpy as np

def create_test_metrics(num_frames=30, knee_range=(180, 90), back_angle=150, stability_std=0.01):
    """Create test biomechanical metrics for testing"""
    metrics = []
    
    for i in range(num_frames):
        # Simulate squat movement
        progress = i / num_frames
        if progress < 0.5:
            # Descending
            knee_angle = knee_range[0] - (knee_range[0] - knee_range[1]) * (progress * 2)
        else:
            # Ascending
            knee_angle = knee_range[1] + (knee_range[0] - knee_range[1]) * ((progress - 0.5) * 2)
        
        # Add some noise for realism
        knee_angle += np.random.normal(0, 2)
        back_angle_frame = back_angle + np.random.normal(0, 3)
        com_x = 0.5 + np.random.normal(0, stability_std)
        
        metric = BiomechanicalMetrics(
            knee_angle_left=knee_angle,
            knee_angle_right=knee_angle + np.random.normal(0, 1),
            back_angle=back_angle_frame,
            center_of_mass_x=com_x,
            center_of_mass_y=0.5,
            landmark_visibility=0.9
        )
        metrics.append(metric)
    
    return metrics

def test_difficulty_levels():
    """Test different difficulty levels"""
    print("🧪 Testing Difficulty Levels\n")
    
    # Create test data - good form squat
    good_metrics = create_test_metrics(
        num_frames=60,  # 2 second rep
        knee_range=(180, 80),  # Good depth
        back_angle=160,  # Good posture
        stability_std=0.008  # Good stability
    )
    
    difficulties = ['beginner', 'casual', 'professional']
    
    for difficulty in difficulties:
        print(f"--- {difficulty.upper()} DIFFICULTY ---")
        grader = IntelligentFormGrader(difficulty=difficulty)
        result = grader.grade_repetition(good_metrics)
        
        print(f"Score: {result['score']}/100")
        print(f"Faults: {result['faults']}")
        print(f"Analyzers used: {result.get('analysis_details', {}).keys()}")
        print(f"Feedback: {result['feedback'][:2]}")  # First 2 feedback items
        print()

def test_poor_form_detection():
    """Test detection of various form issues"""
    print("🚨 Testing Poor Form Detection\n")
    
    grader = IntelligentFormGrader(difficulty='casual')
    
    # Test cases with different form issues
    test_cases = [
        {
            'name': 'Partial Rep',
            'metrics': create_test_metrics(
                num_frames=30,
                knee_range=(180, 150),  # Very shallow
                back_angle=160,
                stability_std=0.01
            )
        },
        {
            'name': 'Back Rounding',
            'metrics': create_test_metrics(
                num_frames=45,
                knee_range=(180, 85),
                back_angle=125,  # Severe rounding
                stability_std=0.01
            )
        },
        {
            'name': 'Poor Stability',
            'metrics': create_test_metrics(
                num_frames=50,
                knee_range=(180, 90),
                back_angle=150,
                stability_std=0.025  # Very unstable
            )
        },
        {
            'name': 'Too Fast',
            'metrics': create_test_metrics(
                num_frames=20,  # < 1 second
                knee_range=(180, 85),
                back_angle=150,
                stability_std=0.01
            )
        }
    ]
    
    for test_case in test_cases:
        print(f"--- {test_case['name'].upper()} ---")
        result = grader.grade_repetition(test_case['metrics'])
        
        print(f"Score: {result['score']}/100")
        print(f"Main Faults: {result['faults']}")
        print(f"Key Feedback: {result['feedback'][1] if len(result['feedback']) > 1 else 'None'}")
        print(f"Analysis: {len(result.get('analysis_details', {}))} analyzers ran")
        print()

def test_excellent_form():
    """Test excellent form detection and bonuses"""
    print("🏆 Testing Excellent Form Detection\n")
    
    grader = IntelligentFormGrader(difficulty='professional')
    
    # Create excellent form metrics
    excellent_metrics = create_test_metrics(
        num_frames=90,  # 3 second rep - good tempo
        knee_range=(180, 75),  # Excellent depth
        back_angle=165,  # Excellent posture
        stability_std=0.005  # Excellent stability
    )
    
    result = grader.grade_repetition(excellent_metrics)
    
    print(f"Score: {result['score']}/100")
    print(f"Faults: {result['faults']}")
    print(f"Bonuses Applied: {result['biomechanical_summary'].get('bonus_breakdown', [])}")
    print(f"Feedback: {result['feedback']}")
    print(f"Visibility Quality: {result['biomechanical_summary'].get('visibility_quality', 'unknown')}")

if __name__ == "__main__":
    print("🤖 AI Fitness Coach - Advanced Form Grader Test Suite")
    print("=" * 60)
    
    test_difficulty_levels()
    test_poor_form_detection()
    test_excellent_form()
    
    print("✅ All tests completed!")
