#!/usr/bin/env python3
"""
Comprehensive Analyzer Validation Suite
=======================================

Tests each analyzer with synthetic data to ensure basic logic is correct.
This validates that the core scoring algorithms work as expected with 
known-good and known-bad movement data.
"""

import numpy as np

import sys
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.grading.advanced_form_grader import (
    BiomechanicalMetrics, 
    SafetyAnalyzer, 
    DepthAnalyzer, 
    StabilityAnalyzer,
    ThresholdConfig
)

class AnalyzerValidationSuite:
    """Comprehensive validation suite for individual analyzers"""
    
    def __init__(self):
        self.config = ThresholdConfig.emergency_calibrated()
        self.safety_analyzer = SafetyAnalyzer(self.config)
        self.depth_analyzer = DepthAnalyzer()
        self.stability_analyzer = StabilityAnalyzer(self.config)
        
        print("🔧 Using Emergency Calibrated Thresholds:")
        print(f"   Safety Severe Back Rounding: {self.config.safety_severe_back_rounding}°")
        print(f"   Safety Moderate Back Rounding: {self.config.safety_moderate_back_rounding}°")
        print(f"   Stability Severe Threshold: {self.config.stability_severe_instability}")
        print(f"   Stability Moderate Threshold: {self.config.stability_poor_stability}")
    
    def _calculate_component_score(self, analyzer_result, base_score=100):
        """Helper to calculate component score from analyzer result"""
        score = base_score
        
        # Apply penalties
        for penalty in analyzer_result.get('penalties', []):
            score -= penalty.get('amount', 0)
        
        # Apply bonuses
        for bonus in analyzer_result.get('bonuses', []):
            score += bonus.get('amount', 0)
        
        return max(0, min(100, score))
    
    def test_safety_analyzer(self):
        """Test SafetyAnalyzer with known scenarios"""
        print("\n🛡️ Testing Safety Analyzer")
        print("=" * 40)
        
        # Test 1: Perfect Posture (should score ~100%)
        print("\n📋 Test 1: Perfect Posture")
        perfect_frames = []
        for _ in range(50):
            perfect_frames.append(BiomechanicalMetrics(
                back_angle=145.0,  # Excellent upright posture
                landmark_visibility=0.95,
                timestamp=_ * 0.033
            ))
        
        perfect_result = self.safety_analyzer.analyze(perfect_frames)
        perfect_score = self._calculate_component_score(perfect_result)
        
        print(f"   Perfect Posture Score: {perfect_score}%")
        print(f"   Perfect Posture Faults: {perfect_result['faults']}")
        print(f"   Perfect Posture Penalties: {len(perfect_result.get('penalties', []))}")
        
        # Should score high with no faults
        assert perfect_score >= 95, f"Perfect posture should score ≥95%, got {perfect_score}%"
        assert len(perfect_result['faults']) == 0, f"Perfect posture should have no faults, got {perfect_result['faults']}"
        print("   ✅ Perfect posture test passed!")
        
        # Test 2: Moderate Back Rounding (should have moderate penalties)
        print("\n📋 Test 2: Moderate Back Rounding")
        moderate_frames = []
        for _ in range(50):
            moderate_frames.append(BiomechanicalMetrics(
                back_angle=95.0,  # Moderate rounding (below 90° threshold)
                landmark_visibility=0.95,
                timestamp=_ * 0.033
            ))
        
        moderate_result = self.safety_analyzer.analyze(moderate_frames)
        moderate_score = self._calculate_component_score(moderate_result)
        
        print(f"   Moderate Rounding Score: {moderate_score}%")
        print(f"   Moderate Rounding Faults: {moderate_result['faults']}")
        print(f"   Moderate Rounding Penalties: {len(moderate_result.get('penalties', []))}")
        
        # Should have moderate penalties
        assert moderate_score < 90, f"Moderate rounding should score <90%, got {moderate_score}%"
        assert moderate_score > 50, f"Moderate rounding should score >50%, got {moderate_score}%"
        print("   ✅ Moderate rounding test passed!")
        
        # Test 3: Severe Back Rounding (should score very low)
        print("\n📋 Test 3: Severe Back Rounding")
        dangerous_frames = []
        for _ in range(50):
            dangerous_frames.append(BiomechanicalMetrics(
                back_angle=55.0,  # Dangerously rounded (below 60° threshold)
                landmark_visibility=0.95,
                timestamp=_ * 0.033
            ))
        
        dangerous_result = self.safety_analyzer.analyze(dangerous_frames)
        dangerous_score = self._calculate_component_score(dangerous_result)
        
        print(f"   Dangerous Posture Score: {dangerous_score}%")
        print(f"   Dangerous Posture Faults: {dangerous_result['faults']}")
        print(f"   Dangerous Posture Penalties: {len(dangerous_result.get('penalties', []))}")
        
        # Should score very low with severe faults
        assert dangerous_score <= 30, f"Dangerous posture should score ≤30%, got {dangerous_score}%"
        assert 'SEVERE_BACK_ROUNDING' in dangerous_result['faults'], f"Should detect SEVERE_BACK_ROUNDING, got {dangerous_result['faults']}"
        print("   ✅ Severe rounding test passed!")
        
        print("✅ Safety Analyzer validation completed!")
        return True
    
    def test_depth_analyzer(self):
        """Test DepthAnalyzer with known scenarios"""
        print("\n📏 Testing Depth Analyzer")
        print("=" * 40)
        
        # Test 1: Excellent Depth (should score high)
        print("\n📋 Test 1: Excellent Depth")
        deep_frames = []
        for i in range(50):
            # Simulate squatting motion: 160° -> 70° -> 160° (full range)
            if i < 20:  # Descending phase
                knee_angle = 160 - (90 * i / 20)  # 160° to 70°
            elif i < 30:  # Bottom phase
                knee_angle = 70 + np.random.normal(0, 2)  # Around 70° with slight variation
            else:  # Ascending phase
                knee_angle = 70 + (90 * (i - 30) / 20)  # 70° to 160°
            
            deep_frames.append(BiomechanicalMetrics(
                knee_angle_left=max(65, min(165, knee_angle)),  # Constrain to realistic range
                knee_angle_right=max(65, min(165, knee_angle + np.random.normal(0, 1))),
                landmark_visibility=0.95,
                timestamp=i * 0.033
            ))
        
        deep_result = self.depth_analyzer.analyze(deep_frames)
        deep_score = self._calculate_component_score(deep_result)
        
        print(f"   Excellent Depth Score: {deep_score}%")
        print(f"   Excellent Depth Faults: {deep_result['faults']}")
        print(f"   Excellent Depth Bonuses: {len(deep_result.get('bonuses', []))}")
        
        # Should score high with depth bonus
        assert deep_score >= 90, f"Excellent depth should score ≥90%, got {deep_score}%"
        print("   ✅ Excellent depth test passed!")
        
        # Test 2: Adequate Depth (should score well)
        print("\n📋 Test 2: Adequate Depth")
        adequate_frames = []
        for i in range(50):
            # Simulate squatting motion: 160° -> 105° -> 160° (adequate but slight penalty range)
            if i < 20:  # Descending phase
                knee_angle = 160 - (55 * i / 20)  # 160° to 105°
            elif i < 30:  # Bottom phase
                knee_angle = 105 + np.random.normal(0, 2)  # Around 105° with slight variation
            else:  # Ascending phase
                knee_angle = 105 + (55 * (i - 30) / 20)  # 105° to 160°
            
            adequate_frames.append(BiomechanicalMetrics(
                knee_angle_left=max(100, min(165, knee_angle)),  # Constrain to realistic range
                knee_angle_right=max(100, min(165, knee_angle + np.random.normal(0, 1))),
                landmark_visibility=0.95,
                timestamp=i * 0.033
            ))
        
        adequate_result = self.depth_analyzer.analyze(adequate_frames)
        adequate_score = self._calculate_component_score(adequate_result)
        
        print(f"   Adequate Depth Score: {adequate_score}%")
        print(f"   Adequate Depth Faults: {adequate_result['faults']}")
        
        # Should score reasonably well but with small penalty
        assert adequate_score >= 70, f"Adequate depth should score ≥70%, got {adequate_score}%"
        assert adequate_score <= 85, f"Adequate depth should score ≤85%, got {adequate_score}%"
        print("   ✅ Adequate depth test passed!")
        
        # Test 3: Partial Rep (should score very low)
        print("\n📋 Test 3: Partial Rep")
        shallow_frames = []
        for i in range(50):
            # Simulate very shallow squatting motion: 160° -> 140° -> 160° (limited range)
            if i < 20:  # Descending phase
                knee_angle = 160 - (20 * i / 20)  # 160° to 140° (only 20° range)
            elif i < 30:  # Bottom phase
                knee_angle = 140 + np.random.normal(0, 1)  # Around 140° with slight variation
            else:  # Ascending phase
                knee_angle = 140 + (20 * (i - 30) / 20)  # 140° to 160°
            
            shallow_frames.append(BiomechanicalMetrics(
                knee_angle_left=max(135, min(165, knee_angle)),  # Constrain to shallow range
                knee_angle_right=max(135, min(165, knee_angle + np.random.normal(0, 1))),
                landmark_visibility=0.95,
                timestamp=i * 0.033
            ))
        
        shallow_result = self.depth_analyzer.analyze(shallow_frames)
        shallow_score = self._calculate_component_score(shallow_result)
        
        print(f"   Partial Rep Score: {shallow_score}%")
        print(f"   Partial Rep Faults: {shallow_result['faults']}")
        print(f"   Partial Rep Penalties: {len(shallow_result.get('penalties', []))}")
        
        # Should score low with depth faults
        assert shallow_score <= 50, f"Partial rep should score ≤50%, got {shallow_score}%"
        depth_faults = ['PARTIAL_REP', 'VERY_SHALLOW', 'INSUFFICIENT_DEPTH']
        has_depth_fault = any(fault in shallow_result['faults'] for fault in depth_faults)
        assert has_depth_fault, f"Should detect depth faults, got {shallow_result['faults']}"
        print("   ✅ Partial rep test passed!")
        
        print("✅ Depth Analyzer validation completed!")
        return True
    
    def test_stability_analyzer(self):
        """Test StabilityAnalyzer with known scenarios"""
        print("\n⚖️ Testing Stability Analyzer")
        print("=" * 40)
        
        # Test 1: Perfect Stability (should score high)
        print("\n📋 Test 1: Perfect Stability")
        stable_frames = []
        for _ in range(50):
            stable_frames.append(BiomechanicalMetrics(
                center_of_mass_x=0.5 + np.random.normal(0, 0.005),  # Very stable
                center_of_mass_y=0.5 + np.random.normal(0, 0.005),
                landmark_visibility=0.95,
                timestamp=_ * 0.033
            ))
        
        stable_result = self.stability_analyzer.analyze(stable_frames)
        stable_score = self._calculate_component_score(stable_result)
        
        print(f"   Perfect Stability Score: {stable_score}%")
        print(f"   Perfect Stability Faults: {stable_result['faults']}")
        print(f"   Perfect Stability Bonuses: {len(stable_result.get('bonuses', []))}")
        
        # Should score high with no stability faults
        assert stable_score >= 85, f"Perfect stability should score ≥85%, got {stable_score}%"
        print("   ✅ Perfect stability test passed!")
        
        # Test 2: Moderate Instability (should have moderate penalties)
        print("\n📋 Test 2: Moderate Instability")
        moderate_unstable_frames = []
        for _ in range(50):
            moderate_unstable_frames.append(BiomechanicalMetrics(
                center_of_mass_x=0.5 + np.random.normal(0, 0.06),  # Increased sway
                center_of_mass_y=0.5 + np.random.normal(0, 0.06),
                landmark_visibility=0.95,
                timestamp=_ * 0.033
            ))
        
        moderate_unstable_result = self.stability_analyzer.analyze(moderate_unstable_frames)
        moderate_unstable_score = self._calculate_component_score(moderate_unstable_result)
        
        print(f"   Moderate Instability Score: {moderate_unstable_score}%")
        print(f"   Moderate Instability Faults: {moderate_unstable_result['faults']}")
        
        # Should have moderate penalties
        assert moderate_unstable_score < 90, f"Moderate instability should score <90%, got {moderate_unstable_score}%"
        assert moderate_unstable_score > 40, f"Moderate instability should score >40%, got {moderate_unstable_score}%"
        print("   ✅ Moderate instability test passed!")
        
        # Test 3: Severe Instability (should score low)
        print("\n📋 Test 3: Severe Instability")
        unstable_frames = []
        for _ in range(50):
            unstable_frames.append(BiomechanicalMetrics(
                center_of_mass_x=0.5 + np.random.normal(0, 0.08),  # Very unstable
                center_of_mass_y=0.5 + np.random.normal(0, 0.08),
                landmark_visibility=0.95,
                timestamp=_ * 0.033
            ))
        
        unstable_result = self.stability_analyzer.analyze(unstable_frames)
        unstable_score = self._calculate_component_score(unstable_result)
        
        print(f"   Severe Instability Score: {unstable_score}%")
        print(f"   Severe Instability Faults: {unstable_result['faults']}")
        print(f"   Severe Instability Penalties: {len(unstable_result.get('penalties', []))}")
        
        # Should score low with stability faults
        assert unstable_score <= 60, f"Severe instability should score ≤60%, got {unstable_score}%"
        stability_faults = ['SEVERE_INSTABILITY', 'POOR_STABILITY']
        has_stability_fault = any(fault in unstable_result['faults'] for fault in stability_faults)
        assert has_stability_fault, f"Should detect stability faults, got {unstable_result['faults']}"
        print("   ✅ Severe instability test passed!")
        
        print("✅ Stability Analyzer validation completed!")
        return True
    
    def run_all_tests(self):
        """Run all analyzer validation tests"""
        print("🧪 ANALYZER UNIT VALIDATION SUITE")
        print("=" * 60)
        print("Testing each analyzer with synthetic data to verify core logic...")
        
        try:
            print(f"\n⚙️ Configuration Details:")
            print(f"   Using ThresholdConfig.emergency_calibrated()")
            print(f"   Safety thresholds: Severe<{self.config.safety_severe_back_rounding}°, Moderate<{self.config.safety_moderate_back_rounding}°")
            print(f"   Stability thresholds: Severe>{self.config.stability_severe_instability}, Poor>{self.config.stability_poor_stability}")
            
            # Run individual tests
            safety_passed = self.test_safety_analyzer()
            depth_passed = self.test_depth_analyzer()
            stability_passed = self.test_stability_analyzer()
            
            # Summary
            print(f"\n🏁 VALIDATION RESULTS SUMMARY")
            print("=" * 50)
            print(f"   Safety Analyzer:    {'✅ PASSED' if safety_passed else '❌ FAILED'}")
            print(f"   Depth Analyzer:     {'✅ PASSED' if depth_passed else '❌ FAILED'}")
            print(f"   Stability Analyzer: {'✅ PASSED' if stability_passed else '❌ FAILED'}")
            
            if safety_passed and depth_passed and stability_passed:
                print("\n🎉 ALL ANALYZER VALIDATION TESTS PASSED!")
                print("✅ Core analyzer logic is working correctly with synthetic data")
                print("✅ Thresholds are producing expected score ranges")
                print("✅ Fault detection is functioning properly")
                print("\n➡️  Next Step: Create real video validation dataset")
                return True
            else:
                print("\n❌ SOME ANALYZER TESTS FAILED!")
                print("🔧 Fix these issues before proceeding to real video validation")
                return False
                
        except Exception as e:
            print(f"\n💥 Validation failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run the analyzer validation suite"""
    validator = AnalyzerValidationSuite()
    success = validator.run_all_tests()
    
    if success:
        print("\n🚀 READY FOR NEXT PHASE!")
        print("You can now proceed to create your real video validation dataset.")
        print("Run: python tests/create_validation_dataset.py")
    else:
        print("\n⚠️ VALIDATION INCOMPLETE")
        print("Please review and fix the analyzer issues before proceeding.")

if __name__ == "__main__":
    main()
