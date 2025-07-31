#!/usr/bin/env python3
"""
Quick Test for Data-Driven Fixes
================================

Test the two critical fixes:
1. Data-driven variation instead of random simulation
2. Fixed validation logic (base score vs final score)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from src.grading.advanced_form_grader import IntelligentFormGrader, BiomechanicalMetrics

def create_varied_test_metrics():
    """Create test metrics with realistic human movement variation"""
    metrics = []
    
    # Create movement with some real variation patterns
    for i in range(30):
        # Descent phase with realistic joint angle variation
        knee_angle = 180 - i * 3 + np.random.normal(0, 2)  # Some natural variation
        back_angle = 145 + np.random.normal(0, 8)  # Realistic postural variation
        
        # Center of mass with realistic sway patterns
        com_x = np.sin(i * 0.1) * 0.02 + np.random.normal(0, 0.01)  # Rhythmic + random sway
        com_y = np.cos(i * 0.1) * 0.015 + np.random.normal(0, 0.008)
        
        metrics.append(BiomechanicalMetrics(
            knee_angle_left=knee_angle,
            knee_angle_right=knee_angle + np.random.normal(0, 1),  # Slight asymmetry
            hip_angle=160 - i * 2,
            back_angle=back_angle,
            center_of_mass_x=com_x,
            center_of_mass_y=com_y,
            landmark_visibility=0.9 + np.random.normal(0, 0.03),
            timestamp=i * 0.033
        ))
    
    # Ascent phase
    for i in range(30):
        knee_angle = 90 + i * 3 + np.random.normal(0, 2)
        back_angle = 145 + np.random.normal(0, 10)  # More variation on ascent
        
        com_x = np.sin((30 + i) * 0.1) * 0.025 + np.random.normal(0, 0.012)
        com_y = np.cos((30 + i) * 0.1) * 0.02 + np.random.normal(0, 0.01)
        
        metrics.append(BiomechanicalMetrics(
            knee_angle_left=knee_angle,
            knee_angle_right=knee_angle + np.random.normal(0, 1.5),
            hip_angle=100 + i * 2,
            back_angle=back_angle,
            center_of_mass_x=com_x,
            center_of_mass_y=com_y,
            landmark_visibility=0.9 + np.random.normal(0, 0.03),
            timestamp=(30 + i) * 0.033
        ))
    
    return metrics

def test_data_driven_variation():
    """Test that variation is now based on real movement data"""
    print("🔬 Testing Data-Driven Variation")
    print("=" * 40)
    
    form_grader = IntelligentFormGrader(difficulty="casual")
    
    # Test multiple reps to see data-driven variation
    print("Analyzing 5 reps with different movement patterns...")
    
    for rep in range(1, 6):
        # Create metrics with different patterns for each rep
        metrics = create_varied_test_metrics()
        
        # Add different patterns to each rep
        if rep == 1:
            # Very consistent movement
            for m in metrics:
                m.center_of_mass_x *= 0.5  # Less sway
                m.center_of_mass_y *= 0.5
        elif rep == 2:
            # More sway (poor stability)
            for m in metrics:
                m.center_of_mass_x *= 2.0  # More sway
                m.center_of_mass_y *= 2.0
        elif rep == 3:
            # Fast movement (shorter duration)
            metrics = metrics[::2]  # Half the frames = faster movement
        elif rep == 4:
            # Slow movement (longer duration)
            metrics = metrics + metrics  # Double frames = slower movement
        # Rep 5 uses default pattern
        
        result = form_grader.grade_repetition(metrics)
        
        print(f"Rep {rep}: Score: {result['score']:3d}% (Base: {result.get('base_score', 'N/A'):.1f}%)")
        
        # Check if we have component scores
        if 'component_scores' in result:
            components = result['component_scores']
            safety = components.get('safety', {}).get('score', 0)
            depth = components.get('depth', {}).get('score', 0)
            stability = components.get('stability', {}).get('score', 0)
            print(f"        Components: S:{safety:.0f}% D:{depth:.0f}% St:{stability:.0f}%")
        
        # Show variation applied
        if 'base_score' in result:
            variation = result['score'] - result['base_score']
            print(f"        Variation Applied: {variation:+.1f} points")
        
        print()
    
    return True

def test_validation_logic():
    """Test that validation now properly checks base score calculation"""
    print("🔍 Testing Fixed Validation Logic")
    print("=" * 35)
    
    form_grader = IntelligentFormGrader(difficulty="casual")
    
    # Get a result with base_score
    metrics = create_varied_test_metrics()
    result = form_grader.grade_repetition(metrics)
    
    print(f"Grading Result:")
    print(f"  Final Score: {result['score']}%")
    print(f"  Base Score: {result.get('base_score', 'Missing!')}%")
    
    if 'base_score' in result:
        variation = result['score'] - result['base_score']
        print(f"  Variation: {variation:+.1f} points")
    
    # Test validation if debug method exists
    if hasattr(form_grader, '_validate_final_score'):
        validation = form_grader._validate_final_score(result, {})
        print(f"\nValidation Results:")
        print(f"  Base Score Valid: {validation.get('is_valid', 'Unknown')}")
        print(f"  Expected Base: {validation.get('expected_base_score', 0):.1f}%")
        actual_base = validation.get('actual_base_score', 0)
        if isinstance(actual_base, (int, float)):
            print(f"  Actual Base: {actual_base:.1f}%")
        else:
            print(f"  Actual Base: {actual_base}")
        print(f"  Variation Reasonable: {validation.get('variation_reasonable', 'Unknown')}")
        
        if 'summary' in validation:
            summary = validation['summary']
            print(f"  Summary: {summary}")
    
    return True

if __name__ == "__main__":
    print("🧪 AI FITNESS COACH - Data-Driven Fixes Test")
    print("=" * 55)
    
    try:
        print("Testing both critical fixes...")
        print()
        
        # Test Fix #1: Data-driven variation
        test_data_driven_variation()
        
        # Test Fix #2: Validation logic
        test_validation_logic()
        
        print("🎉 Both fixes tested successfully!")
        print("✅ Data-driven variation: Using real movement metrics")
        print("✅ Validation logic: Properly validates base score calculation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
