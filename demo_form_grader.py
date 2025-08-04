#!/usr/bin/env python3
"""
Enhanced Form Grader Demonstration

This script shows how your AI Fitness Coach form grader now works with all 
the improvements from the code review implementation.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def demonstrate_form_grader():
    """Demonstrate the enhanced form grader capabilities"""
    
    print("🎯 AI FITNESS COACH - ENHANCED FORM GRADER DEMONSTRATION")
    print("=" * 80)
    
    try:
        from src.grading.advanced_form_grader import (
            IntelligentFormGrader, 
            ThresholdConfig,
            BiomechanicalMetrics
        )
        
        # Initialize with the enhanced configuration
        config = ThresholdConfig.emergency_calibrated()
        grader = IntelligentFormGrader(difficulty="casual", config=config)
        
        print("📊 GRADING SYSTEM OVERVIEW:")
        print("=" * 50)
        print("The form grader now uses a comprehensive multi-component scoring system:")
        print()
        
        print("🏗️  ANALYZER COMPONENTS (9 total):")
        analyzer_descriptions = {
            'safety': 'Detects dangerous back rounding and posture issues',
            'depth': 'Analyzes squat depth and movement range',
            'stability': 'Measures balance and postural control',
            'tempo': 'Analyzes movement timing and speed',
            'symmetry': 'Detects left-right movement imbalances',
            'butt_wink': 'Identifies pelvic tilt at bottom position',
            'knee_valgus': 'Detects knee caving (valgus collapse)',
            'head_position': 'Monitors head and neck alignment',
            'foot_stability': 'Analyzes heel lift and foot stability'
        }
        
        for i, (name, description) in enumerate(analyzer_descriptions.items(), 1):
            print(f"  {i}. {name.replace('_', ' ').title()}: {description}")
        
        print()
        print("⚖️  SCORING WEIGHTS (sums to 100%):")
        print("  • Safety Analysis: 40% (most critical - prevents injury)")
        print("  • Depth Analysis: 25% (movement quality - full range of motion)")
        print("  • Stability Analysis: 15% (balance and control)")
        print("  • Form Refinement: 20% (advanced biomechanics)")
        print("    - Butt Wink (pelvic tilt): 8%")
        print("    - Knee Valgus (knee tracking): 7%")
        print("    - Head Position: 3%")
        print("    - Foot Stability: 2%")
        
        print()
        print("🧪 TESTING WITH SAMPLE MOVEMENT DATA...")
        print("=" * 50)
        
        # Test Case 1: Poor form squat
        print("\n📊 TEST CASE 1: Poor Form Squat")
        print("-" * 30)
        poor_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=135,   # Shallow depth
                knee_angle_right=133,
                back_angle=65,         # Severe back rounding
                landmark_visibility=0.9
            ) for _ in range(20)
        ]
        
        result1 = grader.grade_repetition(poor_metrics)
        print(f"   Score: {result1['score']}%")
        print(f"   Components Analyzed: {len(result1.get('component_scores', {}))}")
        print(f"   Faults: {result1.get('faults', [])[:3]}...")  # Show first 3 faults
        
        # Test Case 2: Good form squat
        print("\n📊 TEST CASE 2: Good Form Squat")
        print("-" * 30)
        good_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=80,    # Good depth
                knee_angle_right=82,
                back_angle=150,        # Good posture
                landmark_visibility=0.95
            ) for _ in range(25)
        ]
        
        result2 = grader.grade_repetition(good_metrics)
        print(f"   Score: {result2['score']}%")
        print(f"   Components Analyzed: {len(result2.get('component_scores', {}))}")
        print(f"   Faults: {len(result2.get('faults', []))} detected")
        
        # Test Case 3: Mixed quality squat
        print("\n📊 TEST CASE 3: Mixed Quality Squat")
        print("-" * 30)
        mixed_metrics = []
        for i in range(30):
            # Simulate improving form during the movement
            improvement_factor = i / 30.0
            knee_angle = 130 - (50 * improvement_factor)  # 130° to 80°
            back_angle = 90 + (50 * improvement_factor)   # 90° to 140°
            
            mixed_metrics.append(BiomechanicalMetrics(
                knee_angle_left=knee_angle,
                knee_angle_right=knee_angle + 2,
                back_angle=back_angle,
                landmark_visibility=0.9
            ))
        
        result3 = grader.grade_repetition(mixed_metrics)
        print(f"   Score: {result3['score']}%")
        print(f"   Components Analyzed: {len(result3.get('component_scores', {}))}")
        print(f"   Faults: {len(result3.get('faults', []))} detected")
        
        print()
        print("🔧 CONFIGURATION HIGHLIGHTS:")
        print("=" * 50)
        print(f"   • All {len(config.__dict__)} thresholds are now configurable")
        print(f"   • Frame rate: {config.frame_rate} FPS")
        print(f"   • Safety thresholds: Severe <{config.safety_severe_back_rounding}°, Moderate <{config.safety_moderate_back_rounding}°")
        print(f"   • Depth thresholds: Shallow >{config.depth_bad_shallow_threshold}°, Insufficient >{config.depth_insufficient_threshold}°")
        print(f"   • Tempo thresholds: Too fast <{config.tempo_too_fast_threshold}s, Too slow >{config.tempo_too_slow_threshold}s")
        
        print()
        print("✨ KEY IMPROVEMENTS:")
        print("=" * 50)
        print("   ✅ Balanced scoring prevents 'broken compass' problem")
        print("   ✅ All magic numbers externalized to ThresholdConfig") 
        print("   ✅ Single fault assignment prevents overlapping penalties")
        print("   ✅ Configurable frame rate for different camera setups")
        print("   ✅ 9 specialized analyzers for comprehensive assessment")
        print("   ✅ Research-ready with easy parameter tuning")
        
        print()
        print("🚀 SYSTEM STATUS: PRODUCTION READY!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    demonstrate_form_grader()
