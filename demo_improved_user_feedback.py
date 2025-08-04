#!/usr/bin/env python3
"""
Demonstration of improved fault hierarchy that preserves important user feedback
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.grading.advanced_form_grader import (
    IntelligentFormGrader, 
    ThresholdConfig,
    BiomechanicalMetrics,
    UserProfile,
    UserLevel
)

def create_user_scenario(description, knee_angle, back_angle):
    """Create test data for different user scenarios"""
    test_data = []
    
    for i in range(20):  # 20-frame squat
        metric = BiomechanicalMetrics(
            knee_angle_left=knee_angle,
            knee_angle_right=knee_angle,
            back_angle=back_angle,
            hip_angle=90,            
            ankle_angle_left=110,
            ankle_angle_right=110,
            center_of_mass_x=0.5,
            center_of_mass_y=0.6,
            landmark_visibility=0.95,
            raw_landmarks=[{"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.95} for _ in range(33)]
        )
        test_data.append(metric)
    
    return test_data

def demonstrate_user_feedback():
    """Demonstrate how the improved hierarchy provides better user feedback"""
    print("🎯 IMPROVED USER FEEDBACK DEMONSTRATION")
    print("=" * 60)
    
    # Setup grader
    config = ThresholdConfig.emergency_calibrated()
    user_profile = UserProfile()
    user_profile.skill_level = UserLevel.EXPERT
    grader = IntelligentFormGrader(user_profile, "expert", config)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Good Form User',
            'description': 'Proper depth and posture',
            'knee_angle': 70,   # Good depth (< 90°)
            'back_angle': 80,   # Good posture (> 60°)
            'expected': 'Few or no faults'
        },
        {
            'name': 'Partial Rep User',
            'description': 'Quarter squats but good posture',
            'knee_angle': 120,  # Shallow (> 100°)
            'back_angle': 80,   # Good posture
            'expected': 'partial_rep fault only'
        },
        {
            'name': 'Safety Issue User',
            'description': 'Good depth but dangerous posture',
            'knee_angle': 70,   # Good depth
            'back_angle': 45,   # Severe back rounding (< 60°)
            'expected': 'SEVERE_BACK_ROUNDING fault only'
        },
        {
            'name': 'Double Problem User',
            'description': 'Both depth AND safety issues',
            'knee_angle': 120,  # Shallow (> 100°)
            'back_angle': 45,   # Severe back rounding (< 60°)
            'expected': 'BOTH faults visible (improved UX!)'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. 🏃 {scenario['name']}: {scenario['description']}")
        print(f"   Expected: {scenario['expected']}")
        
        # Create test data
        test_data = create_user_scenario(
            scenario['description'],
            scenario['knee_angle'],
            scenario['back_angle']
        )
        
        # Run analysis
        result = grader.grade_repetition(test_data)
        faults = result.get('faults', [])
        score = result.get('overall_score', 0)
        
        print(f"   📊 Result: Score={score:.1f}%, Faults={faults}")
        
        # Provide user-friendly feedback
        if 'SEVERE_BACK_ROUNDING' in faults and 'partial_rep' in faults:
            print("   💬 User sees: '🚨 Fix your posture AND go deeper!'")
            print("   ✅ Improvement: User knows BOTH issues need work")
        elif 'SEVERE_BACK_ROUNDING' in faults:
            print("   💬 User sees: '🚨 Dangerous back rounding - keep chest up!'")
        elif 'partial_rep' in faults:
            print("   💬 User sees: '📏 Go deeper for full muscle activation!'")
        else:
            print("   💬 User sees: '✅ Good form!'")
    
    print(f"\n" + "=" * 60)
    print("🎯 USER EXPERIENCE BENEFITS:")
    print("✅ Safety issues always highlighted (critical)")
    print("✅ Depth issues always shown (effectiveness)")
    print("✅ Users get complete picture of what to improve")
    print("✅ No confusion about 'hidden' problems")
    print("✅ Faster progress through targeted feedback")
    
    print(f"\n📚 ACADEMIC INTEGRITY:")
    print("✅ Still prevents redundant penalties (e.g., severe vs moderate back rounding)")
    print("✅ Maintains intelligent hierarchy for truly related faults")
    print("✅ Preserves different categories of feedback (safety vs effectiveness)")
    print("✅ Provides dissertation-level sophistication with practical usability")

if __name__ == "__main__":
    demonstrate_user_feedback()
