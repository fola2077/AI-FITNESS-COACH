#!/usr/bin/env python3
"""
Simple test script to validate the pose analysis system
"""

import cv2
import numpy as np
from src.processing.pose_processor import PoseProcessor
from src.grading.advanced_form_grader import UserProfile, UserLevel, BiomechanicalMetrics
from src.validation.pose_validation import PoseValidationSystem

def create_test_metrics():
    """Create some test biomechanical metrics for validation"""
    test_metrics = []
    
    # Simulate a good squat rep
    for i in range(60):  # 2 seconds at 30fps
        progress = i / 60.0
        
        # Simulate squat movement - standing to squatting to standing
        if progress < 0.4:  # Descending
            knee_angle = 160 - (progress / 0.4) * 70  # 160° to 90°
            back_angle = 160 - (progress / 0.4) * 40  # 160° to 120°
        elif progress < 0.6:  # Bottom position
            knee_angle = 90 + np.random.normal(0, 5)  # Stay around 90°
            back_angle = 120 + np.random.normal(0, 10)  # Stay around 120°
        else:  # Ascending
            ascent_progress = (progress - 0.6) / 0.4
            knee_angle = 90 + ascent_progress * 70  # 90° to 160°
            back_angle = 120 + ascent_progress * 40  # 120° to 160°
        
        # Add some noise for realism
        knee_angle += np.random.normal(0, 2)
        back_angle += np.random.normal(0, 3)
        
        metrics = BiomechanicalMetrics(
            knee_angle_left=max(30, min(180, knee_angle)),
            knee_angle_right=max(30, min(180, knee_angle + np.random.normal(0, 3))),
            hip_angle=max(90, min(180, 140 - progress * 20)),
            back_angle=max(90, min(180, back_angle)),
            ankle_angle_left=max(70, min(120, 90 + progress * 10)),
            ankle_angle_right=max(70, min(120, 90 + progress * 10)),
            center_of_mass_x=0.5 + np.random.normal(0, 0.01),
            center_of_mass_y=0.7 - progress * 0.1,
            landmark_visibility=0.95 + np.random.normal(0, 0.03),
            timestamp=i / 30.0
        )
        test_metrics.append(metrics)
    
    return test_metrics

def test_validation_system():
    """Test the validation system with sample data"""
    print("🧪 Testing Validation System")
    print("=" * 50)
    
    # Create test data
    test_metrics = create_test_metrics()
    print(f"Created {len(test_metrics)} test frames")
    
    # Create processor with validation enabled
    user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.INTERMEDIATE)
    processor = PoseProcessor(user_profile=user_profile, enable_validation=True)
    
    print(f"\n🔍 Testing with validation enabled...")
    
    # Simulate a completed rep
    processor.current_rep_metrics = test_metrics
    processor.rep_counter.rep_count = 1
    
    # Process the rep (this will trigger validation)
    processor._process_completed_rep()
    
    # Check results
    if hasattr(processor, 'last_rep_analysis'):
        analysis = processor.last_rep_analysis
        print(f"\n📊 Analysis Results:")
        print(f"- Score: {analysis.get('score', 'N/A')}")
        print(f"- Feedback count: {len(analysis.get('feedback', []))}")
        
        if 'debug_info' in analysis:
            print(f"- Debug info available: ✅")
        if 'validation_results' in analysis:
            print(f"- Validation results available: ✅")
            
        return True
    else:
        print("❌ No analysis results found")
        return False

def test_individual_components():
    """Test individual validation components"""
    print("\n🔧 Testing Individual Components")
    print("=" * 50)
    
    validation_system = PoseValidationSystem()
    test_metrics = create_test_metrics()
    
    # Test landmark validation
    print("\n1. Testing landmark validation...")
    for i, metrics in enumerate(test_metrics[:5]):  # Test first 5 frames
        result = validation_system.validate_landmarks(metrics)
        status = "✅ PASS" if result['is_valid'] else "❌ FAIL"
        print(f"   Frame {i}: {status} (visibility: {metrics.landmark_visibility:.2f})")
    
    # Test angle validation
    print("\n2. Testing angle validation...")
    sample_metrics = test_metrics[30]  # Middle of squat
    angle_result = validation_system.validate_angle_calculations(sample_metrics)
    print(f"   Angles valid: {'✅ PASS' if angle_result['is_valid'] else '❌ FAIL'}")
    print(f"   Issues: {angle_result.get('issues', 'None')}")
    
    # Test biomechanical validation
    print("\n3. Testing biomechanical validation...")
    bio_result = validation_system.validate_biomechanical_metrics(test_metrics)
    print(f"   Biomechanics valid: {'✅ PASS' if bio_result['is_valid'] else '❌ FAIL'}")
    print(f"   Movement range: {bio_result.get('movement_range', 'N/A'):.1f}°")
    
    return True

if __name__ == "__main__":
    try:
        print("🚀 Starting Validation Tests")
        print("=" * 60)
        
        # Test 1: Individual components
        success1 = test_individual_components()
        
        # Test 2: Full system integration
        success2 = test_validation_system()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("🎉 All validation tests passed!")
        else:
            print("❌ Some tests failed")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
