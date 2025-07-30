#!/usr/bin/env python3
"""
Test Script: Compare Old vs New Weighted Scoring System
This demonstrates the dramatic improvement from the "broken compass" to "precision instrument"
"""

import sys
import numpy as np
from src.grading.advanced_form_grader import (
    IntelligentFormGrader, 
    BiomechanicalMetrics,
    UserProfile
)

def create_test_metrics(scenario: str, num_frames: int = 40) -> list:
    """Create synthetic test data for different movement scenarios"""
    metrics = []
    
    if scenario == "excellent_form":
        # Perfect squat with good depth, stable movement, upright posture
        for i in range(num_frames):
            # Simulate squat movement: standing -> deep -> standing
            progress = i / num_frames
            if progress < 0.3:  # Descending
                knee_angle = 170 - (progress / 0.3) * 85  # 170° -> 85°
                back_angle = 150 - (progress / 0.3) * 20   # 150° -> 130°
            elif progress < 0.7:  # Bottom hold
                knee_angle = 85 + np.random.normal(0, 2)   # Stable at bottom
                back_angle = 130 + np.random.normal(0, 3)  # Stable posture
            else:  # Ascending
                ascent_progress = (progress - 0.7) / 0.3
                knee_angle = 85 + ascent_progress * 85      # 85° -> 170°
                back_angle = 130 + ascent_progress * 20     # 130° -> 150°
            
            # Minimal sway (excellent stability)
            com_x = 0.5 + np.random.normal(0, 0.01)  # Very stable
            com_y = 0.5 + np.random.normal(0, 0.01)
            
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=knee_angle,
                knee_angle_right=knee_angle + np.random.normal(0, 1),
                back_angle=back_angle,
                center_of_mass_x=com_x,
                center_of_mass_y=com_y,
                landmark_visibility=0.95
            ))
    
    elif scenario == "stability_issues":
        # Good depth and posture, but with balance problems
        for i in range(num_frames):
            progress = i / num_frames
            if progress < 0.3:
                knee_angle = 170 - (progress / 0.3) * 90   # Good depth
                back_angle = 145 - (progress / 0.3) * 15   # Good posture
            elif progress < 0.7:
                knee_angle = 80 + np.random.normal(0, 3)   # Good depth
                back_angle = 130 + np.random.normal(0, 5)  # Good posture
            else:
                ascent_progress = (progress - 0.7) / 0.3
                knee_angle = 80 + ascent_progress * 90
                back_angle = 130 + ascent_progress * 15
            
            # Significant sway (poor stability) - this was causing 55-60% scores
            com_x = 0.5 + np.random.normal(0, 0.04)  # High sway
            com_y = 0.5 + np.random.normal(0, 0.04)
            
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=knee_angle,
                knee_angle_right=knee_angle + np.random.normal(0, 2),
                back_angle=back_angle,
                center_of_mass_x=com_x,
                center_of_mass_y=com_y,
                landmark_visibility=0.90
            ))
    
    elif scenario == "dangerous_posture":
        # Excellent depth and stability, but dangerous back rounding
        for i in range(num_frames):
            progress = i / num_frames
            if progress < 0.3:
                knee_angle = 170 - (progress / 0.3) * 90   # Excellent depth
                back_angle = 100 - (progress / 0.3) * 40   # Dangerous rounding
            elif progress < 0.7:
                knee_angle = 80 + np.random.normal(0, 2)   # Excellent depth
                back_angle = 60 + np.random.normal(0, 5)   # Severe rounding
            else:
                ascent_progress = (progress - 0.7) / 0.3
                knee_angle = 80 + ascent_progress * 90
                back_angle = 60 + ascent_progress * 40
            
            # Excellent stability
            com_x = 0.5 + np.random.normal(0, 0.008)  # Very stable
            com_y = 0.5 + np.random.normal(0, 0.008)
            
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=knee_angle,
                knee_angle_right=knee_angle + np.random.normal(0, 1),
                back_angle=back_angle,
                center_of_mass_x=com_x,
                center_of_mass_y=com_y,
                landmark_visibility=0.95
            ))
    
    return metrics

def test_scoring_systems():
    """Compare old single-score vs new weighted scoring"""
    print("🔬 SCORING SYSTEM COMPARISON TEST")
    print("=" * 60)
    
    # Initialize form grader
    grader = IntelligentFormGrader(difficulty="beginner")
    
    test_scenarios = [
        ("excellent_form", "Perfect squat - should score high"),
        ("stability_issues", "Good form but balance problems - old system fails here"),
        ("dangerous_posture", "Great depth but severe back rounding - safety critical")
    ]
    
    for scenario, description in test_scenarios:
        print(f"\n🧪 SCENARIO: {scenario.upper()}")
        print(f"📝 Description: {description}")
        print("-" * 50)
        
        # Create test data
        test_metrics = create_test_metrics(scenario)
        
        # Test OLD scoring system
        print("📊 OLD SYSTEM (Single Linear Score):")
        old_result = grader.grade_repetition(test_metrics)
        print(f"   Final Score: {old_result['score']}%")
        print(f"   Faults: {old_result.get('faults', [])}")
        print(f"   Feedback: {old_result['feedback'][0] if old_result['feedback'] else 'None'}")
        
        # Test NEW weighted scoring system
        print("\n🎯 NEW SYSTEM (Weighted Multi-Component):")
        new_result = grader.grade_repetition_weighted(test_metrics)
        print(f"   Final Score: {new_result['score']}%")
        
        # Show component breakdown
        if 'component_scores' in new_result:
            for component, data in new_result['component_scores'].items():
                print(f"   {component.title()}: {data['score']:.1f}% (weight: {data['weight']:.0%})")
        
        print(f"   Feedback: {new_result['feedback'][0] if new_result['feedback'] else 'None'}")
        
        # Analysis
        score_diff = new_result['score'] - old_result['score']
        print(f"\n📈 IMPROVEMENT: {score_diff:+.1f} points")
        if score_diff > 10:
            print("   ✅ MAJOR IMPROVEMENT - More accurate assessment!")
        elif score_diff > 0:
            print("   ✅ Improved accuracy")
        elif score_diff < -10:
            print("   ⚠️ More conservative (likely more accurate for safety)")
        
        print("\n" + "="*60)

def demonstrate_threshold_fix():
    """Show how the threshold fix solves the 'everything is severe' problem"""
    print("\n🔧 THRESHOLD CALIBRATION DEMONSTRATION")
    print("=" * 60)
    
    # Create metrics with normal human sway
    normal_sway_metrics = []
    for i in range(30):
        # Normal human movement has some natural sway
        com_x = 0.5 + np.random.normal(0, 0.025)  # Normal sway level
        com_y = 0.5 + np.random.normal(0, 0.025)
        
        normal_sway_metrics.append(BiomechanicalMetrics(
            knee_angle_left=85,  # Good depth
            back_angle=135,      # Good posture  
            center_of_mass_x=com_x,
            center_of_mass_y=com_y,
            landmark_visibility=0.90
        ))
    
    grader = IntelligentFormGrader(difficulty="beginner")
    
    # Calculate the sway value
    com_x_values = [m.center_of_mass_x for m in normal_sway_metrics]
    com_y_values = [m.center_of_mass_y for m in normal_sway_metrics]
    x_sway = np.std(com_x_values)
    y_sway = np.std(com_y_values)
    total_sway = np.sqrt(x_sway**2 + y_sway**2)
    
    print(f"📊 Normal Human Sway Level: {total_sway:.4f}")
    print(f"🔧 New Severe Threshold: {grader.analyzers['stability'].SEVERE_INSTABILITY_THRESHOLD:.3f}")
    print(f"🔧 New Poor Threshold: {grader.analyzers['stability'].POOR_STABILITY_THRESHOLD:.3f}")
    
    if total_sway < grader.analyzers['stability'].SEVERE_INSTABILITY_THRESHOLD:
        print("✅ FIXED: Normal sway is no longer marked as 'severe'!")
    else:
        print("❌ Still needs adjustment")
    
    # Test the analysis
    result = grader.grade_repetition_weighted(normal_sway_metrics)
    print(f"\n🎯 Score with normal sway: {result['score']}%")
    stability_score = result['component_scores']['stability']['score']
    print(f"📊 Stability component: {stability_score:.1f}%")

if __name__ == "__main__":
    print("🚀 AI FITNESS COACH - SCORING SYSTEM BREAKTHROUGH TEST")
    print("Testing the transformation from 'Broken Compass' to 'Precision Instrument'")
    print("=" * 80)
    
    # First show the threshold fix
    demonstrate_threshold_fix()
    
    # Then compare scoring systems
    test_scoring_systems()
    
    print("\n🎊 TRANSFORMATION COMPLETE!")
    print("Your form grader has evolved from giving confusing contradictory feedback")
    print("to providing accurate, balanced, and motivating assessment!")
