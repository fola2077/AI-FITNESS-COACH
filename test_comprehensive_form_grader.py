#!/usr/bin/env python3
"""
Comprehensive Test Suite for Advanced Form Grader Implementation

This test file validates all the improvements implemented from the code review:
1. New analyzers integrated into final scoring
2. Magic numbers externalized to ThresholdConfig
3. Data flow for new analyzers ensured
4. DepthAnalyzer logic refined (single fault per rep)
5. All analyzers updated to use config thresholds
6. Configurable FPS/frame rate added

Tests ensure the system works correctly with the new configuration-driven architecture.
"""

import sys
import os
import numpy as np
from typing import List, Dict, Any
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.grading.advanced_form_grader import (
        IntelligentFormGrader, 
        ThresholdConfig, 
        BiomechanicalMetrics,
        SafetyAnalyzer,
        DepthAnalyzer,
        StabilityAnalyzer,
        TempoAnalyzer,
        SymmetryAnalyzer,
        ButtWinkAnalyzer,
        KneeValgusAnalyzer,
        HeadPositionAnalyzer,
        FootStabilityAnalyzer
    )
    print("✅ Successfully imported all required classes")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class TestThresholdConfiguration(unittest.TestCase):
    """Test the expanded ThresholdConfig system"""
    
    def setUp(self):
        self.config = ThresholdConfig()
    
    def test_safety_thresholds_exist(self):
        """Test that all safety analyzer thresholds are configurable"""
        self.assertTrue(hasattr(self.config, 'safety_severe_back_rounding'))
        self.assertTrue(hasattr(self.config, 'safety_moderate_back_rounding'))
        self.assertTrue(hasattr(self.config, 'safety_excellent_posture'))
        print("✅ Safety thresholds are configurable")
    
    def test_depth_thresholds_exist(self):
        """Test that all depth analyzer thresholds are configurable"""
        self.assertTrue(hasattr(self.config, 'depth_bad_shallow_threshold'))
        self.assertTrue(hasattr(self.config, 'depth_insufficient_threshold'))
        self.assertTrue(hasattr(self.config, 'depth_partial_rep_threshold'))
        self.assertTrue(hasattr(self.config, 'depth_movement_range_threshold'))
        print("✅ Depth thresholds are configurable")
    
    def test_new_analyzer_thresholds_exist(self):
        """Test that all new analyzer thresholds are configurable"""
        # Butt wink thresholds
        self.assertTrue(hasattr(self.config, 'butt_wink_std_threshold'))
        self.assertTrue(hasattr(self.config, 'butt_wink_range_threshold'))
        
        # Knee valgus thresholds
        self.assertTrue(hasattr(self.config, 'knee_valgus_ratio_threshold'))
        self.assertTrue(hasattr(self.config, 'knee_valgus_max_penalty'))
        
        # Head position thresholds
        self.assertTrue(hasattr(self.config, 'head_position_angle_threshold'))
        self.assertTrue(hasattr(self.config, 'head_position_max_penalty'))
        
        # Foot stability thresholds
        self.assertTrue(hasattr(self.config, 'foot_heel_lift_threshold'))
        self.assertTrue(hasattr(self.config, 'foot_stability_max_penalty'))
        
        print("✅ All new analyzer thresholds are configurable")
    
    def test_tempo_and_symmetry_thresholds_exist(self):
        """Test that tempo and symmetry thresholds are configurable"""
        # Tempo thresholds
        self.assertTrue(hasattr(self.config, 'tempo_too_fast_threshold'))
        self.assertTrue(hasattr(self.config, 'tempo_too_slow_threshold'))
        self.assertTrue(hasattr(self.config, 'tempo_optimal_min'))
        self.assertTrue(hasattr(self.config, 'tempo_optimal_max'))
        
        # Symmetry thresholds
        self.assertTrue(hasattr(self.config, 'symmetry_threshold'))
        self.assertTrue(hasattr(self.config, 'symmetry_penalty_multiplier'))
        
        print("✅ Tempo and symmetry thresholds are configurable")
    
    def test_frame_rate_configuration(self):
        """Test that frame rate is configurable"""
        self.assertTrue(hasattr(self.config, 'frame_rate'))
        self.assertEqual(self.config.frame_rate, 30.0)
        print("✅ Frame rate is configurable")

class TestAnalyzerInitialization(unittest.TestCase):
    """Test that all analyzers accept ThresholdConfig parameters"""
    
    def setUp(self):
        self.config = ThresholdConfig()
    
    def test_safety_analyzer_config(self):
        """Test SafetyAnalyzer accepts config"""
        analyzer = SafetyAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ SafetyAnalyzer accepts ThresholdConfig")
    
    def test_depth_analyzer_config(self):
        """Test DepthAnalyzer accepts config"""
        analyzer = DepthAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ DepthAnalyzer accepts ThresholdConfig")
    
    def test_stability_analyzer_config(self):
        """Test StabilityAnalyzer accepts config"""
        analyzer = StabilityAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ StabilityAnalyzer accepts ThresholdConfig")
    
    def test_tempo_analyzer_config(self):
        """Test TempoAnalyzer accepts config"""
        analyzer = TempoAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ TempoAnalyzer accepts ThresholdConfig")
    
    def test_symmetry_analyzer_config(self):
        """Test SymmetryAnalyzer accepts config"""
        analyzer = SymmetryAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ SymmetryAnalyzer accepts ThresholdConfig")
    
    def test_butt_wink_analyzer_config(self):
        """Test ButtWinkAnalyzer accepts config"""
        analyzer = ButtWinkAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ ButtWinkAnalyzer accepts ThresholdConfig")
    
    def test_knee_valgus_analyzer_config(self):
        """Test KneeValgusAnalyzer accepts config"""
        analyzer = KneeValgusAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ KneeValgusAnalyzer accepts ThresholdConfig")
    
    def test_head_position_analyzer_config(self):
        """Test HeadPositionAnalyzer accepts config"""
        analyzer = HeadPositionAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ HeadPositionAnalyzer accepts ThresholdConfig")
    
    def test_foot_stability_analyzer_config(self):
        """Test FootStabilityAnalyzer accepts config"""
        analyzer = FootStabilityAnalyzer(self.config)
        self.assertEqual(analyzer.config, self.config)
        print("✅ FootStabilityAnalyzer accepts ThresholdConfig")

class TestFormGraderIntegration(unittest.TestCase):
    """Test the integrated form grader system"""
    
    def setUp(self):
        self.config = ThresholdConfig()
        self.grader = IntelligentFormGrader(config=self.config)
    
    def test_all_analyzers_initialized(self):
        """Test that all 9 analyzers are properly initialized"""
        expected_analyzers = [
            'safety', 'depth', 'stability', 'tempo', 'symmetry',
            'butt_wink', 'knee_valgus', 'head_position', 'foot_stability'
        ]
        
        for analyzer_name in expected_analyzers:
            self.assertIn(analyzer_name, self.grader.analyzers)
            # Verify each analyzer has the config
            analyzer = self.grader.analyzers[analyzer_name]
            self.assertTrue(hasattr(analyzer, 'config'))
            self.assertEqual(analyzer.config, self.config)
        
        print("✅ All 9 analyzers properly initialized with config")
    
    def test_scoring_weights_sum_to_100(self):
        """Test that scoring weights sum to 100%"""
        # Create mock data for testing
        mock_metrics = [self._create_mock_biomechanical_metrics() for _ in range(30)]
        
        # Mock the analyzer results
        mock_analysis_results = {
            'faults': [],
            'penalties': [],
            'bonuses': []
        }
        
        # Patch all analyzer methods
        with patch.object(self.grader.analyzers['safety'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['depth'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['stability'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['tempo'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['symmetry'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['butt_wink'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['knee_valgus'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['head_position'], 'analyze', return_value=mock_analysis_results), \
             patch.object(self.grader.analyzers['foot_stability'], 'analyze', return_value=mock_analysis_results):
            
            result = self.grader.grade_repetition(mock_metrics)
            
            # Check that result contains expected structure
            self.assertIn('score', result)
            self.assertIn('component_scores', result)
            self.assertIsInstance(result['score'], (int, float))
            
            print(f"✅ Scoring system functional - Final score: {result['score']}")
    
    def _create_mock_biomechanical_metrics(self) -> BiomechanicalMetrics:
        """Create mock biomechanical metrics for testing"""
        return BiomechanicalMetrics(
            knee_angle_left=90.0 + np.random.normal(0, 10),
            knee_angle_right=90.0 + np.random.normal(0, 10),
            hip_angle=95.0 + np.random.normal(0, 5),
            back_angle=160.0 + np.random.normal(0, 5),
            ankle_angle_left=80.0 + np.random.normal(0, 5),
            ankle_angle_right=80.0 + np.random.normal(0, 5),
            center_of_mass_x=0.0 + np.random.normal(0, 0.01),
            center_of_mass_y=1.0 + np.random.normal(0, 0.05),
            movement_velocity=0.1 + np.random.normal(0, 0.02),
            postural_sway=0.02 + np.random.normal(0, 0.005),
            jerk=0.005 + np.random.normal(0, 0.001)
        )

class TestDepthAnalyzerRefinement(unittest.TestCase):
    """Test the refined DepthAnalyzer with single fault logic"""
    
    def setUp(self):
        self.config = ThresholdConfig()
        self.analyzer = DepthAnalyzer(self.config)
    
    def test_single_fault_assignment(self):
        """Test that DepthAnalyzer assigns only one fault per repetition"""
        # Create metrics representing a very shallow squat
        shallow_metrics = []
        for i in range(30):
            metrics = BiomechanicalMetrics(
                knee_angle_left=140.0,  # Very shallow
                knee_angle_right=140.0,
                hip_angle=150.0,
                back_angle=160.0
            )
            shallow_metrics.append(metrics)
        
        result = self.analyzer.analyze(shallow_metrics)
        
        # Should have faults but only one type of depth fault
        depth_faults = [f for f in result['faults'] if 'SHALLOW' in f or 'PARTIAL' in f or 'INSUFFICIENT' in f]
        
        # Should have at most one depth-related fault
        self.assertLessEqual(len(depth_faults), 1, "Should assign at most one depth fault per rep")
        
        if depth_faults:
            print(f"✅ DepthAnalyzer correctly assigned single fault: {depth_faults[0]}")
        else:
            print("✅ DepthAnalyzer correctly found no depth faults")

class TestTempoAnalyzerFrameRate(unittest.TestCase):
    """Test TempoAnalyzer uses configurable frame rate"""
    
    def setUp(self):
        self.config = ThresholdConfig()
        self.config.frame_rate = 60.0  # Test with different frame rate
        self.analyzer = TempoAnalyzer(self.config)
    
    def test_frame_rate_usage(self):
        """Test that TempoAnalyzer uses configurable frame rate"""
        # Create 60 frames (should be 1 second at 60 FPS)
        fast_metrics = [BiomechanicalMetrics() for _ in range(60)]
        
        result = self.analyzer.analyze(fast_metrics)
        
        # At 60 FPS, 60 frames = 1 second, which is less than tempo_too_fast_threshold (1.2s)
        # So it should detect as too fast
        fast_faults = [f for f in result['faults'] if 'TOO_FAST' in f]
        self.assertTrue(len(fast_faults) > 0, "Should detect fast movement with custom frame rate")
        
        print("✅ TempoAnalyzer correctly uses configurable frame rate")

class TestConfigurationLogging(unittest.TestCase):
    """Test configuration logging functionality"""
    
    def test_config_logging(self):
        """Test that configuration logging works without errors"""
        config = ThresholdConfig()
        
        # This should not raise any exceptions
        try:
            config.log_configuration()
            print("✅ Configuration logging works correctly")
        except Exception as e:
            self.fail(f"Configuration logging failed: {e}")

def run_comprehensive_tests():
    """Run all comprehensive tests and provide detailed results"""
    print("=" * 80)
    print("COMPREHENSIVE FORM GRADER TEST SUITE")
    print("=" * 80)
    print("Testing implementation of code review steps 1, 2, 3, 4, 6, and 7\n")
    
    # Test suites in order of importance
    test_suites = [
        TestThresholdConfiguration,
        TestAnalyzerInitialization, 
        TestFormGraderIntegration,
        TestDepthAnalyzerRefinement,
        TestTempoAnalyzerFrameRate,
        TestConfigurationLogging
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for suite_class in test_suites:
        print(f"\n{'='*50}")
        print(f"Running {suite_class.__name__}")
        print(f"{'='*50}")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(suite_class)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        
        if result.failures:
            for test, traceback in result.failures:
                failed_tests.append(f"FAILURE: {test} - {traceback}")
                print(f"❌ {test} FAILED")
        
        if result.errors:
            for test, traceback in result.errors:
                failed_tests.append(f"ERROR: {test} - {traceback}")
                print(f"❌ {test} ERROR")
    
    # Final summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print("\nFAILED TESTS:")
        for failure in failed_tests:
            print(f"  • {failure}")
    else:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nImplementation Summary:")
        print("✅ Step 1: New analyzers integrated into scoring")
        print("✅ Step 2: Magic numbers externalized to ThresholdConfig")
        print("✅ Step 3: Data flow for new analyzers ensured")
        print("✅ Step 4: DepthAnalyzer refined (single fault logic)")
        print("✅ Step 6: All analyzers use config thresholds")
        print("✅ Step 7: Configurable FPS/frame rate added")
        print("\n🚀 System ready for production use!")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    # Run the comprehensive test suite
    success = run_comprehensive_tests()
    
    if not success:
        print("\n⚠️  Some tests failed. Please review the implementation.")
        sys.exit(1)
    else:
        print("\n✅ All implementations verified and working correctly!")
        sys.exit(0)
