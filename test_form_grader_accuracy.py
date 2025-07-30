#!/usr/bin/env python3
"""
Form Grader Accuracy Test Suite

This comprehensive test suite validates that the form grader correctly identifies
good form vs bad form by creating synthetic test data with known characteristics.
"""

import sys
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.grading.advanced_form_grader import (
    BiomechanicalMetrics, 
    IntelligentFormGrader, 
    UserProfile, 
    UserLevel
)

class FormGraderAccuracyTest:
    """Test suite to validate form grader accuracy"""
    
    def __init__(self):
        self.form_grader = IntelligentFormGrader(difficulty="beginner")
    
    def create_test_metrics(self, scenario: str) -> list:
        """Create synthetic test data for different scenarios"""
        base_metrics = []
        
        if scenario == "perfect_squat":
            # Perfect squat: good depth, stable back angle, controlled movement
            for i in range(40):
                # Simulate squat movement: standing -> descent -> bottom -> ascent -> standing
                progress = i / 40.0
                if progress < 0.3:  # Descent phase
                    knee_angle = 170 - (progress / 0.3) * 90  # 170° -> 80°
                    back_angle = 130 - (progress / 0.3) * 10  # 130° -> 120°
                elif progress < 0.4:  # Bottom hold
                    knee_angle = 80 + np.random.normal(0, 2)  # Stay around 80°
                    back_angle = 120 + np.random.normal(0, 3)  # Stay around 120°
                elif progress < 0.7:  # Ascent phase
                    ascent_progress = (progress - 0.4) / 0.3
                    knee_angle = 80 + (ascent_progress * 90)  # 80° -> 170°
                    back_angle = 120 + (ascent_progress * 10)  # 120° -> 130°
                else:  # Return to standing
                    knee_angle = 170 + np.random.normal(0, 2)
                    back_angle = 130 + np.random.normal(0, 2)
                
                metrics = BiomechanicalMetrics(
                    knee_angle_left=max(30, min(180, knee_angle)),
                    knee_angle_right=max(30, min(180, knee_angle + np.random.normal(0, 2))),
                    hip_angle=max(90, min(180, knee_angle * 0.8)),
                    back_angle=max(90, min(180, back_angle)),
                    center_of_mass_x=0.5 + np.random.normal(0, 0.005),  # Minimal sway
                    landmark_visibility=0.95 + np.random.normal(0, 0.02),
                    timestamp=i * 0.033  # 30 FPS
                )
                base_metrics.append(metrics)
        
        elif scenario == "severe_back_rounding":
            # Dangerous back rounding scenario
            for i in range(40):
                progress = i / 40.0
                if progress < 0.3:  # Descent with dangerous rounding
                    knee_angle = 170 - (progress / 0.3) * 80
                    back_angle = 130 - (progress / 0.3) * 70  # Dangerous: 130° -> 60°
                elif progress < 0.4:  # Bottom with severe rounding
                    knee_angle = 90 + np.random.normal(0, 3)
                    back_angle = 60 + np.random.normal(0, 5)  # Severe rounding
                else:  # Ascent still rounded
                    ascent_progress = (progress - 0.4) / 0.6
                    knee_angle = 90 + (ascent_progress * 80)
                    back_angle = 60 + (ascent_progress * 50)  # Still some rounding
                
                metrics = BiomechanicalMetrics(
                    knee_angle_left=max(30, min(180, knee_angle)),
                    knee_angle_right=max(30, min(180, knee_angle + np.random.normal(0, 3))),
                    hip_angle=max(90, min(180, knee_angle * 0.7)),
                    back_angle=max(30, min(180, back_angle)),  # Allow dangerous angles for testing
                    center_of_mass_x=0.5 + np.random.normal(0, 0.01),
                    landmark_visibility=0.9 + np.random.normal(0, 0.03),
                    timestamp=i * 0.033
                )
                base_metrics.append(metrics)
        
        elif scenario == "partial_rep":
            # Partial rep - insufficient depth
            for i in range(30):
                progress = i / 30.0
                if progress < 0.4:  # Shallow descent
                    knee_angle = 170 - (progress / 0.4) * 40  # Only go to 130°
                    back_angle = 125 - (progress / 0.4) * 5   # 125° -> 120°
                elif progress < 0.6:  # Stay shallow
                    knee_angle = 130 + np.random.normal(0, 3)  # Shallow bottom
                    back_angle = 120 + np.random.normal(0, 3)
                else:  # Quick return
                    ascent_progress = (progress - 0.6) / 0.4
                    knee_angle = 130 + (ascent_progress * 40)  # 130° -> 170°
                    back_angle = 120 + (ascent_progress * 5)   # 120° -> 125°
                
                metrics = BiomechanicalMetrics(
                    knee_angle_left=max(30, min(180, knee_angle)),
                    knee_angle_right=max(30, min(180, knee_angle + np.random.normal(0, 2))),
                    hip_angle=max(90, min(180, knee_angle * 0.9)),
                    back_angle=max(90, min(180, back_angle)),
                    center_of_mass_x=0.5 + np.random.normal(0, 0.008),
                    landmark_visibility=0.85 + np.random.normal(0, 0.04),
                    timestamp=i * 0.033
                )
                base_metrics.append(metrics)
        
        elif scenario == "unstable_movement":
            # Unstable, wobbly movement
            for i in range(45):
                progress = i / 45.0
                # Base movement pattern
                if progress < 0.4:
                    base_knee = 170 - (progress / 0.4) * 90  # 170° -> 80°
                    base_back = 130 - (progress / 0.4) * 10  # 130° -> 120°
                elif progress < 0.6:
                    base_knee = 80
                    base_back = 120
                else:
                    ascent_progress = (progress - 0.6) / 0.4
                    base_knee = 80 + (ascent_progress * 90)
                    base_back = 120 + (ascent_progress * 10)
                
                # Add high instability
                metrics = BiomechanicalMetrics(
                    knee_angle_left=max(30, min(180, base_knee + np.random.normal(0, 8))),
                    knee_angle_right=max(30, min(180, base_knee + np.random.normal(0, 8))),
                    hip_angle=max(90, min(180, base_knee * 0.8 + np.random.normal(0, 5))),
                    back_angle=max(90, min(180, base_back + np.random.normal(0, 15))),
                    center_of_mass_x=0.5 + np.random.normal(0, 0.03),  # High sway
                    landmark_visibility=0.75 + np.random.normal(0, 0.05),
                    timestamp=i * 0.033
                )
                base_metrics.append(metrics)
        
        elif scenario == "moderate_back_rounding":
            # Moderate back rounding (should get penalties but not severe)
            for i in range(35):
                progress = i / 35.0
                if progress < 0.3:
                    knee_angle = 170 - (progress / 0.3) * 85  # 170° -> 85°
                    back_angle = 130 - (progress / 0.3) * 50  # 130° -> 80° (moderate rounding)
                elif progress < 0.4:
                    knee_angle = 85 + np.random.normal(0, 3)
                    back_angle = 80 + np.random.normal(0, 3)  # Moderate rounding
                else:
                    ascent_progress = (progress - 0.4) / 0.6
                    knee_angle = 85 + (ascent_progress * 85)
                    back_angle = 80 + (ascent_progress * 40)
                
                metrics = BiomechanicalMetrics(
                    knee_angle_left=max(30, min(180, knee_angle)),
                    knee_angle_right=max(30, min(180, knee_angle + np.random.normal(0, 2))),
                    hip_angle=max(90, min(180, knee_angle * 0.8)),
                    back_angle=max(70, min(180, back_angle)),  # Moderate rounding range
                    center_of_mass_x=0.5 + np.random.normal(0, 0.01),
                    landmark_visibility=0.9 + np.random.normal(0, 0.03),
                    timestamp=i * 0.033
                )
                base_metrics.append(metrics)
        
        return base_metrics
    
    def test_scenario(self, scenario_name: str):
        """Test a specific scenario and validate results"""
        print(f"\n{'='*70}")
        print(f"🧪 TESTING SCENARIO: {scenario_name.upper()}")
        print(f"{'='*70}")
        
        test_metrics = self.create_test_metrics(scenario_name)
        print(f"Created {len(test_metrics)} test frames")
        
        # Run normal grading
        result = self.form_grader.grade_repetition(test_metrics)
        
        # Expected results for validation
        expected_results = {
            "perfect_squat": {
                "score_range": (85, 100), 
                "should_have_faults": False,
                "description": "Perfect form should score 85-100% with no faults"
            },
            "severe_back_rounding": {
                "score_range": (0, 50), 
                "should_have_faults": True, 
                "expected_faults": ["SEVERE_BACK_ROUNDING"],
                "description": "Severe back rounding should score 0-50% with SEVERE_BACK_ROUNDING fault"
            },
            "partial_rep": {
                "score_range": (20, 70), 
                "should_have_faults": True, 
                "expected_faults": ["PARTIAL_REP", "VERY_SHALLOW"],
                "description": "Partial reps should score 20-70% with depth-related faults"
            },
            "unstable_movement": {
                "score_range": (30, 80), 
                "should_have_faults": True, 
                "expected_faults": ["POOR_STABILITY", "SEVERE_INSTABILITY"],
                "description": "Unstable movement should score 30-80% with stability faults"
            },
            "moderate_back_rounding": {
                "score_range": (50, 80), 
                "should_have_faults": True, 
                "expected_faults": ["BACK_ROUNDING"],
                "description": "Moderate back rounding should score 50-80% with BACK_ROUNDING fault"
            }
        }
        
        expected = expected_results.get(scenario_name, {})
        actual_score = result['score']
        actual_faults = result['faults']
        
        print(f"\n📊 TEST PARAMETERS:")
        print(f"Description: {expected.get('description', 'N/A')}")
        print(f"Expected score range: {expected.get('score_range', 'N/A')}")
        print(f"Expected faults: {expected.get('expected_faults', [])}")
        
        print(f"\n📋 ACTUAL RESULTS:")
        print(f"Actual score: {actual_score}%")
        print(f"Actual faults: {actual_faults}")
        print(f"Feedback: {result.get('feedback', [])}")
        
        # Validate score range
        score_valid = False
        score_range = expected.get('score_range')
        if score_range:
            score_valid = score_range[0] <= actual_score <= score_range[1]
            print(f"\n✅ Score validation: {'PASS' if score_valid else 'FAIL'}")
            if not score_valid:
                print(f"   Expected: {score_range[0]}-{score_range[1]}%, Got: {actual_score}%")
        
        # Validate fault detection
        expected_faults = expected.get('expected_faults', [])
        fault_detection_valid = True
        missing_faults = []
        
        for expected_fault in expected_faults:
            if expected_fault not in actual_faults:
                fault_detection_valid = False
                missing_faults.append(expected_fault)
        
        print(f"✅ Fault detection: {'PASS' if fault_detection_valid else 'FAIL'}")
        if missing_faults:
            print(f"   Missing expected faults: {missing_faults}")
        
        # Overall validation
        test_passed = score_valid and fault_detection_valid
        print(f"\n🎯 OVERALL TEST RESULT: {'✅ PASS' if test_passed else '❌ FAIL'}")
        
        return {
            'scenario': scenario_name,
            'score_valid': score_valid,
            'fault_detection_valid': fault_detection_valid,
            'test_passed': test_passed,
            'actual_score': actual_score,
            'actual_faults': actual_faults,
            'expected_score_range': score_range,
            'expected_faults': expected_faults
        }
    
    def analyze_current_configuration(self):
        """Analyze current form grader configuration"""
        print(f"\n{'='*70}")
        print(f"🔍 CURRENT FORM GRADER CONFIGURATION ANALYSIS")
        print(f"{'='*70}")
        
        print(f"Difficulty Level: {self.form_grader.difficulty}")
        print(f"Available Analyzers: {list(self.form_grader.analyzers.keys())}")
        
        print(f"\n📊 ANALYZER CONFIGURATIONS:")
        for name, analyzer in self.form_grader.analyzers.items():
            print(f"\n{name.upper()} ANALYZER:")
            print(f"  Required landmarks: {getattr(analyzer, 'required_landmarks', 'N/A')}")
            print(f"  Min visibility threshold: {getattr(analyzer, 'min_visibility_threshold', 'N/A')}")
            
            # Check difficulty requirements
            test_metrics = []  # Empty for testing
            can_run_beginner = analyzer.can_analyze(test_metrics, "beginner")
            can_run_casual = analyzer.can_analyze(test_metrics, "casual") 
            can_run_professional = analyzer.can_analyze(test_metrics, "professional")
            
            print(f"  Can run on beginner: {can_run_beginner}")
            print(f"  Can run on casual: {can_run_casual}")
            print(f"  Can run on professional: {can_run_professional}")
        
        print(f"\n⚠️ POTENTIAL ISSUES IDENTIFIED:")
        
        # Check why depth analyzer might be skipping
        depth_analyzer = self.form_grader.analyzers['depth']
        print(f"\nDepth Analyzer Analysis:")
        print(f"  Runs on beginner: {depth_analyzer._check_difficulty('beginner')}")
        print(f"  Runs on casual: {depth_analyzer._check_difficulty('casual')}")
        print(f"  Runs on professional: {depth_analyzer._check_difficulty('professional')}")
        print(f"  → ISSUE: Depth analyzer skipped on beginner mode!")
        print(f"  → This means no depth penalties for shallow squats")
        
        # Analyze safety thresholds
        print(f"\nSafety Analyzer Thresholds:")
        print(f"  Severe back rounding: < 70°")
        print(f"  Moderate back rounding: 70-85°") 
        print(f"  Normal range: 85-180°")
        print(f"  Excellent posture bonus: >= 120°")
        print(f"  → Your typical range: 90-128° falls in 'normal' = no penalties")
        
        print(f"\n🔧 RECOMMENDATIONS:")
        print(f"1. Enable depth analyzer on beginner mode for better analysis")
        print(f"2. Consider making back angle thresholds more strict")
        print(f"3. Test with deliberately bad form to verify penalty system")
        print(f"4. Add more granular scoring within the 'normal' ranges")
    
    def run_all_tests(self):
        """Run all accuracy tests"""
        print(f"\n🔬 FORM GRADER ACCURACY TEST SUITE")
        print(f"{'='*70}")
        print(f"Testing form grader's ability to distinguish good vs bad form")
        
        # First analyze current configuration
        self.analyze_current_configuration()
        
        # Test scenarios
        test_scenarios = [
            "perfect_squat",
            "severe_back_rounding", 
            "moderate_back_rounding",
            "partial_rep",
            "unstable_movement"
        ]
        
        results = []
        for scenario in test_scenarios:
            result = self.test_scenario(scenario)
            results.append(result)
        
        # Summary
        print(f"\n{'='*70}")
        print(f"📋 COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*70}")
        
        passed_tests = 0
        print(f"{'Scenario':<25} {'Score':<10} {'Faults':<10} {'Result':<10} {'Actual Score'}")
        print(f"{'-'*70}")
        
        for result in results:
            scenario = result['scenario'].replace('_', ' ').title()
            score_ok = "✅ PASS" if result['score_valid'] else "❌ FAIL"
            fault_ok = "✅ PASS" if result['fault_detection_valid'] else "❌ FAIL"
            overall = "✅ PASS" if result['test_passed'] else "❌ FAIL"
            
            print(f"{scenario:<25} {score_ok:<10} {fault_ok:<10} {overall:<10} {result['actual_score']}%")
            
            if result['test_passed']:
                passed_tests += 1
        
        accuracy_percentage = (passed_tests / len(results)) * 100
        print(f"\n🎯 OVERALL ACCURACY: {accuracy_percentage:.1f}% ({passed_tests}/{len(results)} tests passed)")
        
        if accuracy_percentage < 75:
            print(f"\n⚠️ CRITICAL: Form grader accuracy is below acceptable threshold!")
            print(f"The form grader is not reliably distinguishing good vs bad form.")
            print(f"Recommend immediate review of thresholds and analyzer logic.")
        elif accuracy_percentage < 90:
            print(f"\n⚠️ WARNING: Form grader accuracy is moderate - fine-tuning needed.")
            print(f"Some scenarios are not being detected correctly.")
        else:
            print(f"\n✅ EXCELLENT: Form grader accuracy is within acceptable range!")
        
        # Detailed failure analysis
        failed_tests = [r for r in results if not r['test_passed']]
        if failed_tests:
            print(f"\n🔍 FAILED TEST ANALYSIS:")
            for result in failed_tests:
                print(f"\n❌ {result['scenario'].replace('_', ' ').title()}:")
                if not result['score_valid']:
                    expected_range = result['expected_score_range']
                    print(f"   Score issue: Expected {expected_range[0]}-{expected_range[1]}%, got {result['actual_score']}%")
                if not result['fault_detection_valid']:
                    expected_faults = result['expected_faults']
                    actual_faults = result['actual_faults']
                    missing = [f for f in expected_faults if f not in actual_faults]
                    print(f"   Fault detection issue: Missing {missing}")
        
        return results

if __name__ == "__main__":
    print("🚀 Starting Form Grader Accuracy Validation")
    print("This test will validate that the form grader correctly identifies good vs bad form")
    
    try:
        tester = FormGraderAccuracyTest()
        results = tester.run_all_tests()
        
        print(f"\n✅ Test suite completed successfully!")
        print(f"Check the results above to see if your form grader is working accurately.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
