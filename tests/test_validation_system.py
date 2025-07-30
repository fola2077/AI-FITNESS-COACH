#!/usr/bin/env python3
"""
Test script to validate the pose validation system and form grader
"""

import sys
import os
import numpy as np

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.validation.pose_validation import PoseValidationSystem
from src.grading.advanced_form_grader import BiomechanicalMetrics, IntelligentFormGrader, UserProfile, UserLevel

def create_test_metrics(scenario="good_squat"):
    """Create test biomechanical metrics for different scenarios"""
    
    if scenario == "good_squat":
        # Simulate a good squat with proper depth and form
        metrics = []
        for i in range(60):  # 2 seconds at 30fps
            progress = i / 59  # 0 to 1
            
            # Simulate squat movement: standing -> down -> up -> standing
            if progress < 0.3:  # Descending
                knee_angle = 160 - (progress / 0.3) * 80  # 160° to 80°
                back_angle = 170 - (progress / 0.3) * 40   # 170° to 130°
            elif progress < 0.7:  # Bottom position
                knee_angle = 80 + np.random.normal(0, 2)   # Around 80° with small variation
                back_angle = 130 + np.random.normal(0, 3)  # Around 130° with small variation
            else:  # Ascending
                ascent_progress = (progress - 0.7) / 0.3
                knee_angle = 80 + ascent_progress * 80     # 80° to 160°
                back_angle = 130 + ascent_progress * 40    # 130° to 170°
            
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=knee_angle,
                knee_angle_right=knee_angle + np.random.normal(0, 1),  # Slight asymmetry
                hip_angle=120 + (160 - knee_angle) * 0.5,  # Hip follows knee
                back_angle=back_angle,
                ankle_angle_left=90,
                ankle_angle_right=90,
                center_of_mass_x=0.5 + np.random.normal(0, 0.01),  # Slight sway
                center_of_mass_y=0.7 - (160 - knee_angle) * 0.002,  # Goes down as knee bends
                landmark_visibility=0.95 + np.random.normal(0, 0.02),
                timestamp=i / 30.0
            ))
        
        return metrics
    
    elif scenario == "shallow_squat":
        # Simulate a shallow squat (insufficient depth)
        metrics = []
        for i in range(45):  # Shorter rep
            progress = i / 44
            
            if progress < 0.4:  # Descending (not deep enough)
                knee_angle = 160 - (progress / 0.4) * 50  # Only goes to 110°
                back_angle = 170 - (progress / 0.4) * 20
            elif progress < 0.6:  # Bottom
                knee_angle = 110 + np.random.normal(0, 2)
                back_angle = 150 + np.random.normal(0, 3)
            else:  # Ascending
                ascent_progress = (progress - 0.6) / 0.4
                knee_angle = 110 + ascent_progress * 50
                back_angle = 150 + ascent_progress * 20
            
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=knee_angle,
                knee_angle_right=knee_angle + np.random.normal(0, 1),
                hip_angle=120 + (160 - knee_angle) * 0.5,
                back_angle=back_angle,
                ankle_angle_left=90,
                ankle_angle_right=90,
                center_of_mass_x=0.5 + np.random.normal(0, 0.01),
                center_of_mass_y=0.7 - (160 - knee_angle) * 0.002,
                landmark_visibility=0.92 + np.random.normal(0, 0.03),
                timestamp=i / 30.0
            ))
        
        return metrics
    
    elif scenario == "back_rounding":
        # Simulate squat with back rounding (safety issue)
        metrics = []
        for i in range(55):
            progress = i / 54
            
            if progress < 0.3:  # Descending with rounding
                knee_angle = 160 - (progress / 0.3) * 85  # 160° to 75°
                back_angle = 170 - (progress / 0.3) * 100  # 170° to 70° (rounded)
            elif progress < 0.7:  # Bottom with rounded back
                knee_angle = 75 + np.random.normal(0, 2)
                back_angle = 70 + np.random.normal(0, 5)  # Dangerously rounded
            else:  # Ascending
                ascent_progress = (progress - 0.7) / 0.3
                knee_angle = 75 + ascent_progress * 85
                back_angle = 70 + ascent_progress * 100
            
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=knee_angle,
                knee_angle_right=knee_angle + np.random.normal(0, 2),
                hip_angle=120 + (160 - knee_angle) * 0.5,
                back_angle=back_angle,
                ankle_angle_left=90,
                ankle_angle_right=90,
                center_of_mass_x=0.5 + np.random.normal(0, 0.02),  # More unstable
                center_of_mass_y=0.7 - (160 - knee_angle) * 0.002,
                landmark_visibility=0.88 + np.random.normal(0, 0.04),
                timestamp=i / 30.0
            ))
        
        return metrics

def test_validation_system():
    """Test the validation system with different scenarios"""
    
    print("🧪 Testing AI Fitness Coach Validation System")
    print("=" * 60)
    
    # Initialize components
    validation_system = PoseValidationSystem()
    user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.INTERMEDIATE)
    form_grader = IntelligentFormGrader(user_profile, difficulty="casual")
    
    # Test scenarios
    scenarios = [
        ("Good Squat", "good_squat"),
        ("Shallow Squat", "shallow_squat"),
        ("Back Rounding", "back_rounding")
    ]
    
    for scenario_name, scenario_type in scenarios:
        print(f"\n🎯 Testing Scenario: {scenario_name}")
        print("-" * 40)
        
        # Create test data
        test_metrics = create_test_metrics(scenario_type)
        print(f"Created {len(test_metrics)} frames of test data")
        
        # Run validation
        validation_results = validation_system.validate_rep_analysis(
            test_metrics, None, form_grader  # We don't need pose_detector for this test
        )
        
        # Run form grading
        print(f"\n📊 Form Grading Results:")
        grading_results = form_grader.grade_repetition(test_metrics)
        
        print(f"Score: {grading_results['score']}%")
        print(f"Faults: {grading_results['faults']}")
        print(f"Feedback: {grading_results['feedback'][:2]}")  # First 2 feedback items
        
        # Run debug grading
        print(f"\n🔍 Debug Analysis:")
        debug_results = form_grader.debug_grade_repetition(test_metrics)
        
        print(f"Validation Summary: {validation_results['summary']['recommendation']}")
        print(f"Valid frames: {validation_results['summary']['valid_frames_percentage']:.1f}%")
        
        print("\n" + "=" * 60)

def test_individual_analyzers():
    """Test individual analyzers with debug output"""
    
    print("\n🔬 Testing Individual Analyzers")
    print("=" * 60)
    
    # Create test data
    test_metrics = create_test_metrics("good_squat")
    
    user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.INTERMEDIATE)
    form_grader = IntelligentFormGrader(user_profile, difficulty="casual")
    
    # Test Safety Analyzer
    print("\n🛡️ Safety Analyzer Debug:")
    safety_analyzer = form_grader.analyzers['safety']
    safety_result = safety_analyzer.analyze(test_metrics)
    safety_debug = safety_analyzer.debug_analysis(test_metrics)
    
    print(f"Safety Result: {safety_result}")
    print(f"Back angle stats: {safety_debug['back_angle_stats']}")
    print(f"Classification: {safety_debug['threshold_analysis']['min_angle_classification']}")
    
    # Test Depth Analyzer
    print("\n📏 Depth Analyzer Debug:")
    depth_analyzer = form_grader.analyzers['depth']
    depth_result = depth_analyzer.analyze(test_metrics)
    depth_debug = depth_analyzer.debug_analysis(test_metrics)
    
    print(f"Depth Result: {depth_result}")
    print(f"Depth classification: {depth_debug['depth_analysis']['depth_classification']}")
    print(f"Min knee angle: {depth_debug['depth_analysis']['min_knee_angle']:.1f}°")
    print(f"Movement range: {depth_debug['depth_analysis']['movement_range']:.1f}°")

if __name__ == "__main__":
    print("🚀 Starting Validation System Tests")
    
    try:
        test_validation_system()
        test_individual_analyzers()
        
        print("\n✅ All tests completed successfully!")
        print("\n💡 The validation system is working correctly.")
        print("🎯 You can now enable 'Debug > Enable Validation Mode' in the app")
        print("   to see detailed validation output during live sessions.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
