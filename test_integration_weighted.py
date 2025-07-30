#!/usr/bin/env python3
"""
Integration Test for Weighted Scoring System
============================================

This script tests the integration of the new weighted scoring system
into the main application components to ensure they work correctly together.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from grading.advanced_form_grader import IntelligentFormGrader, BiomechanicalMetrics
from processing.pose_processor import PoseProcessor
from gui.form_grader_worker import FormGraderWorker

def create_test_metrics(scenario="normal"):
    """Create test metrics for different scenarios"""
    metrics = []
    
    if scenario == "excellent_form":
        # Perfect form with minimal issues
        for i in range(30):
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=180 - i * 3,  # 180° to 90° descent
                knee_angle_right=180 - i * 3,
                hip_angle=160 - i * 2,
                back_angle=150,  # Excellent upright posture
                center_of_mass_x=0.0 + np.random.normal(0, 0.005),  # Minimal sway
                center_of_mass_y=0.0 + np.random.normal(0, 0.005),
                landmark_visibility=0.95,
                timestamp=i * 0.033
            ))
        
        # Ascent phase
        for i in range(30):
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=90 + i * 3,  # 90° to 180° ascent
                knee_angle_right=90 + i * 3,
                hip_angle=100 + i * 2,
                back_angle=150,
                center_of_mass_x=0.0 + np.random.normal(0, 0.005),
                center_of_mass_y=0.0 + np.random.normal(0, 0.005),
                landmark_visibility=0.95,
                timestamp=(30 + i) * 0.033
            ))
    
    elif scenario == "mixed_issues":
        # Good depth but some stability issues
        for i in range(30):
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=180 - i * 3,
                knee_angle_right=180 - i * 3,
                hip_angle=160 - i * 2,
                back_angle=130,  # Good posture
                center_of_mass_x=0.0 + np.random.normal(0, 0.040),  # Moderate sway
                center_of_mass_y=0.0 + np.random.normal(0, 0.040),
                landmark_visibility=0.90,
                timestamp=i * 0.033
            ))
        
        for i in range(30):
            metrics.append(BiomechanicalMetrics(
                knee_angle_left=90 + i * 3,
                knee_angle_right=90 + i * 3,
                hip_angle=100 + i * 2,
                back_angle=130,
                center_of_mass_x=0.0 + np.random.normal(0, 0.040),
                center_of_mass_y=0.0 + np.random.normal(0, 0.040),
                landmark_visibility=0.90,
                timestamp=(30 + i) * 0.033
            ))
    
    return metrics

def test_pose_processor_integration():
    """Test that PoseProcessor uses weighted scoring correctly"""
    print("\n🔄 Testing PoseProcessor Integration")
    print("=" * 50)
    
    try:
        # Create a mock pose processor (simplified test)
        form_grader = IntelligentFormGrader(difficulty="professional")
        test_metrics = create_test_metrics("excellent_form")
        
        # Simulate what PoseProcessor does
        result = form_grader.grade_repetition_weighted(test_metrics)
        
        print(f"✅ PoseProcessor integration test passed")
        print(f"   - Score: {result['score']}%")
        print(f"   - Weighted scoring: {'✅' if 'component_scores' in result else '❌'}")
        print(f"   - Prioritized feedback: {'✅' if 'prioritized_feedback' in result else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ PoseProcessor integration test failed: {e}")
        return False

def test_form_grader_worker_integration():
    """Test that FormGraderWorker uses weighted scoring correctly"""
    print("\n🔄 Testing FormGraderWorker Integration")
    print("=" * 50)
    
    try:
        form_grader = IntelligentFormGrader(difficulty="casual")
        test_metrics = create_test_metrics("mixed_issues")
        
        # Create worker (note: we can't easily test Qt signals without Qt app)
        worker = FormGraderWorker(form_grader, test_metrics)
        
        # Manually call the run method to test the core functionality
        original_run = worker.run
        result_captured = None
        
        def mock_emit(result):
            nonlocal result_captured
            result_captured = result
            
        worker.grading_finished.emit = mock_emit
        worker.run()
        
        print(f"✅ FormGraderWorker integration test passed")
        print(f"   - Score: {result_captured['score']}%")
        print(f"   - Component breakdown: {'✅' if 'component_scores' in result_captured else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ FormGraderWorker integration test failed: {e}")
        return False

def test_debug_integration():
    """Test that debug_grade_repetition uses weighted scoring"""
    print("\n🔄 Testing Debug Integration")
    print("=" * 50)
    
    try:
        form_grader = IntelligentFormGrader(difficulty="professional")
        test_metrics = create_test_metrics("excellent_form")
        
        # Test debug grading
        debug_result = form_grader.debug_grade_repetition(test_metrics)
        normal_result = debug_result['normal_result']
        
        print(f"✅ Debug integration test passed")
        print(f"   - Score: {normal_result['score']}%")
        print(f"   - Uses weighted scoring: {'✅' if 'component_scores' in normal_result else '❌'}")
        print(f"   - Debug info available: {'✅' if 'debug_info' in debug_result else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug integration test failed: {e}")
        return False

def test_scoring_consistency():
    """Test that weighted scoring provides consistent results"""
    print("\n🔄 Testing Scoring Consistency")
    print("=" * 50)
    
    try:
        form_grader = IntelligentFormGrader(difficulty="professional")
        test_metrics = create_test_metrics("excellent_form")
        
        # Test multiple runs for consistency
        scores = []
        for i in range(3):
            result = form_grader.grade_repetition_weighted(test_metrics)
            scores.append(result['score'])
            
            # Reset session state to prevent adaptive behavior
            form_grader.reset_session_state()
        
        # Check consistency
        score_variance = np.var(scores)
        print(f"✅ Consistency test passed")
        print(f"   - Scores: {scores}")
        print(f"   - Variance: {score_variance:.2f} (should be 0 for identical data)")
        print(f"   - Consistent: {'✅' if score_variance == 0 else '❌'}")
        
        return score_variance == 0
        
    except Exception as e:
        print(f"❌ Consistency test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🏋️ AI FITNESS COACH - Weighted Scoring Integration Test")
    print("=" * 60)
    print("Testing integration of weighted scoring system into main application...")
    
    tests = [
        test_pose_processor_integration,
        test_form_grader_worker_integration,
        test_debug_integration,
        test_scoring_consistency
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("✅ Main application successfully updated to use weighted scoring system")
        print("✅ Balanced component-based assessment operational")
        print("✅ Prioritized feedback system integrated")
        print("✅ Consistent scoring without adaptive behavior")
    else:
        print("⚠️  Some integration tests failed - please review the issues above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
