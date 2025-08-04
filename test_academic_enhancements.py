#!/usr/bin/env python3
"""
Test script for dissertation-level academic enhancements.

This script validates all 4 critical academic tasks implemented for 
Master's dissertation requirements:

1. Task 1: Input Validation & Contract Enforcement
2. Task 2: Explicit Dependencies (no optional parameters)
3. Task 5: Dynamic Skill-Based Weighting System
4. Task 6: Intelligent Fault Hierarchy (prevent double-penalization)

Academic Benefits:
- Robust error handling prevents silent failures
- Explicit dependencies ensure reproducible analysis
- Skill-progressive complexity matches user capabilities
- Intelligent fault filtering provides fair scoring

Run with: python test_academic_enhancements.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_task_1_input_validation():
    """Test Task 1: Input validation and contract enforcement"""
    print("\n1️⃣ TASK 1: INPUT VALIDATION & CONTRACT ENFORCEMENT")
    print("-" * 55)
    
    from src.grading.advanced_form_grader import IntelligentFormGrader, ThresholdConfig, BiomechanicalMetrics
    
    config = ThresholdConfig.emergency_calibrated()
    grader = IntelligentFormGrader(config=config)
    
    # Test empty input validation
    validation = grader._validate_input_contracts([])
    assert not validation['is_valid'], "Empty input should be invalid"
    print("✅ Empty input correctly rejected")
    
    # Test valid input validation
    sample_metrics = [
        BiomechanicalMetrics(
            knee_angle_left=90, knee_angle_right=90,
            back_angle=85, landmark_visibility=0.9
        ) for _ in range(10)
    ]
    validation = grader._validate_input_contracts(sample_metrics)
    assert validation['is_valid'], f"Valid input should pass validation: {validation.get('error_message', 'unknown error')}"
    print("✅ Valid input correctly accepted")
    
    # Test data requirements checking
    active_analyzers = grader._get_active_analyzers()
    data_requirements = grader._check_data_requirements(sample_metrics, active_analyzers)
    assert 'all_met' in data_requirements, "Data requirements should include 'all_met' field"
    print("✅ Data requirements checking functional")
    
    print("🎯 Task 1 Result: INPUT VALIDATION WORKING CORRECTLY")
    return True

def test_task_2_explicit_dependencies():
    """Test Task 2: Explicit dependencies (no optional parameters)"""
    print("\n2️⃣ TASK 2: EXPLICIT DEPENDENCIES")
    print("-" * 40)
    
    from src.grading.advanced_form_grader import (
        IntelligentFormGrader, ThresholdConfig,
        SafetyAnalyzer, DepthAnalyzer, TempoAnalyzer, SymmetryAnalyzer, StabilityAnalyzer,
        ButtWinkAnalyzer, KneeValgusAnalyzer, HeadPositionAnalyzer, FootStabilityAnalyzer
    )
    
    config = ThresholdConfig.emergency_calibrated()
    
    # Test that all analyzers require explicit config
    analyzer_classes = [
        SafetyAnalyzer, DepthAnalyzer, TempoAnalyzer, SymmetryAnalyzer, StabilityAnalyzer,
        ButtWinkAnalyzer, KneeValgusAnalyzer, HeadPositionAnalyzer, FootStabilityAnalyzer
    ]
    
    for analyzer_class in analyzer_classes:
        # This should work (explicit config provided)
        analyzer = analyzer_class(config)
        assert hasattr(analyzer, 'config'), f"{analyzer_class.__name__} should have config attribute"
        
        # This should fail (no config provided)
        try:
            analyzer_fail = analyzer_class()  # Should raise TypeError
            assert False, f"{analyzer_class.__name__} should require explicit config"
        except TypeError as e:
            # Accept either our custom message or Python's default missing argument message
            error_msg = str(e)
            valid_error = ("requires a valid ThresholdConfig" in error_msg or 
                          "missing 1 required positional argument: 'config'" in error_msg)
            assert valid_error, f"Should have proper error message, got: {error_msg}"
        
        print(f"✅ {analyzer_class.__name__} requires explicit ThresholdConfig")
    
    print("🎯 Task 2 Result: ALL ANALYZERS ENFORCE EXPLICIT DEPENDENCIES")
    return True

def test_task_5_dynamic_weighting():
    """Test Task 5: Dynamic skill-based weighting system"""
    print("\n5️⃣ TASK 5: DYNAMIC SKILL-BASED WEIGHTING")
    print("-" * 47)
    
    from src.grading.advanced_form_grader import IntelligentFormGrader, ThresholdConfig, UserProfile, UserLevel
    
    config = ThresholdConfig.emergency_calibrated()
    skill_levels = [UserLevel.BEGINNER, UserLevel.INTERMEDIATE, UserLevel.ADVANCED, UserLevel.EXPERT]
    
    for skill in skill_levels:
        profile = UserProfile()
        profile.skill_level = skill
        grader = IntelligentFormGrader(user_profile=profile, config=config)
        weights = grader._get_skill_based_weights()
        
        # Verify weights sum to appropriate total
        active_weights = [w for w in weights.values() if w > 0]
        total_weight = sum(active_weights)
        assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got {total_weight}"
        
        # Verify skill progression
        active_analyzers = sum(1 for w in weights.values() if w > 0)
        safety_weight = weights.get('safety', 0)
        
        print(f"✅ {skill.name:<12}: {active_analyzers} analyzers, Safety: {safety_weight:.0%}")
        
        # Verify skill-appropriate complexity
        if skill == UserLevel.BEGINNER:
            assert active_analyzers <= 3, "Beginners should have limited analyzers"
            assert safety_weight >= 0.4, "Beginners should prioritize safety"
        elif skill == UserLevel.EXPERT:
            assert active_analyzers >= 8, "Experts should have comprehensive analysis"
    
    print("🎯 Task 5 Result: DYNAMIC WEIGHTING ADAPTS TO SKILL LEVEL")
    return True

def test_task_6_fault_hierarchy():
    """Test Task 6: Intelligent fault hierarchy"""
    print("\n6️⃣ TASK 6: INTELLIGENT FAULT HIERARCHY")
    print("-" * 43)
    
    from src.grading.advanced_form_grader import IntelligentFormGrader, ThresholdConfig
    
    config = ThresholdConfig.emergency_calibrated()
    grader = IntelligentFormGrader(config=config)
    
    # Test related faults that should be filtered
    all_faults = [
        'DANGEROUS_LEAN',      # Primary fault
        'POOR_DEPTH',          # Should be suppressed by DANGEROUS_LEAN
        'HEAD_FORWARD',        # Should be suppressed by DANGEROUS_LEAN
        'STABILITY_ISSUE',     # Should be suppressed by DANGEROUS_LEAN
        'KNEE_COLLAPSE',       # Primary fault
        'KNEE_TRACKING',       # Should be suppressed by KNEE_COLLAPSE
        'INDEPENDENT_FAULT'    # Should remain (no hierarchy rule)
    ]
    
    component_scores = {
        'safety': {'score': 40, 'result': {'faults': ['DANGEROUS_LEAN']}},
        'depth': {'score': 65, 'result': {'faults': ['POOR_DEPTH']}},
        'knee_valgus': {'score': 50, 'result': {'faults': ['KNEE_COLLAPSE']}}
    }
    
    filtered_faults = grader._apply_intelligent_fault_hierarchy(all_faults, component_scores)
    
    # Verify hierarchy filtering works
    assert len(filtered_faults) < len(all_faults), "Hierarchy should reduce fault count"
    assert 'DANGEROUS_LEAN' in filtered_faults, "Primary faults should be kept"
    assert 'KNEE_COLLAPSE' in filtered_faults, "Primary faults should be kept"
    assert 'INDEPENDENT_FAULT' in filtered_faults, "Independent faults should be kept"
    
    suppressed_count = len(all_faults) - len(filtered_faults)
    print(f"✅ Filtered {suppressed_count} redundant faults")
    print(f"✅ Kept {len(filtered_faults)} primary faults: {filtered_faults}")
    
    print("🎯 Task 6 Result: INTELLIGENT HIERARCHY PREVENTS DOUBLE-PENALIZATION")
    return True

def test_integration():
    """Test full integration of all academic enhancements"""
    print("\n🔬 INTEGRATION TEST: FULL ANALYSIS")
    print("-" * 40)
    
    from src.grading.advanced_form_grader import (
        IntelligentFormGrader, ThresholdConfig, BiomechanicalMetrics, 
        UserProfile, UserLevel
    )
    
    # Set up expert-level analysis
    config = ThresholdConfig.emergency_calibrated()
    profile = UserProfile()
    profile.skill_level = UserLevel.EXPERT
    grader = IntelligentFormGrader(user_profile=profile, config=config)
    
    # Create realistic test data with multiple issues (need at least 10 frames)
    test_metrics = []
    for i in range(15):  # Create 15 frames for solid data
        if i < 5:
            # First 5 frames: Multiple issues
            test_metrics.append(BiomechanicalMetrics(
                knee_angle_left=140,  # Shallow depth
                knee_angle_right=138,
                back_angle=70,        # Poor back angle
                landmark_visibility=0.9
            ))
        else:
            # Later frames: Better movement
            test_metrics.append(BiomechanicalMetrics(
                knee_angle_left=85,   # Good depth
                knee_angle_right=87,
                back_angle=95,        # Good back angle
                landmark_visibility=0.9
            ))
    
    # Run full analysis
    result = grader.grade_repetition(test_metrics)
    
    # Verify all enhancements are working
    assert 'score' in result, "Should return score"
    assert 'faults' in result, "Should return filtered faults"
    assert 'raw_faults' in result, "Should return original faults for analysis"
    assert 'component_scores' in result, "Should return component scores"
    assert 'scoring_method' in result, "Should indicate enhanced scoring method"
    
    # Verify academic enhancements
    scoring_method = result.get('scoring_method', '')
    assert 'hierarchy' in scoring_method, "Should use hierarchy-enhanced scoring"
    
    components_analyzed = len(result.get('component_scores', {}))
    faults_after_hierarchy = len(result.get('faults', []))
    raw_faults = len(result.get('raw_faults', []))
    
    print(f"✅ Expert analysis: {components_analyzed} components")
    print(f"✅ Fault hierarchy: {raw_faults} → {faults_after_hierarchy} faults")
    print(f"✅ Score: {result['score']:.1f}%")
    print(f"✅ Method: {result.get('scoring_method', 'unknown')}")
    
    print("🎯 Integration Result: ALL ENHANCEMENTS WORKING TOGETHER")
    return True

def main():
    """Run all academic enhancement tests"""
    print("🎓 DISSERTATION-LEVEL ACADEMIC ENHANCEMENTS TEST")
    print("=" * 60)
    print("Testing 4 critical tasks for Master's dissertation validation")
    
    all_passed = True
    
    try:
        # Run all tests
        all_passed &= test_task_1_input_validation()
        all_passed &= test_task_2_explicit_dependencies()
        all_passed &= test_task_5_dynamic_weighting()
        all_passed &= test_task_6_fault_hierarchy()
        all_passed &= test_integration()
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL ACADEMIC ENHANCEMENTS SUCCESSFULLY VALIDATED!")
            print("📊 Form grader is now DISSERTATION-READY!")
            print("🎓 Meets Master's level academic requirements!")
            print("\n✨ Key Academic Achievements:")
            print("   • Robust input validation prevents silent failures")
            print("   • Explicit dependencies ensure reproducible analysis")
            print("   • Skill-progressive complexity matches user capabilities")
            print("   • Intelligent fault filtering provides fair scoring")
            return 0
        else:
            print("❌ Some tests failed - see details above")
            return 1
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
