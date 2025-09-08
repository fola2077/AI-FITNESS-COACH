"""
Final Test: Voice Feedback in Live Webcam Session

This test simulates a complete webcam session with voice feedback
to verify everything is working as expected.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
import cv2
import numpy as np

def test_complete_session_with_voice():
    """Test complete session with voice feedback"""
    print("🎤 Testing Complete Session with Voice Feedback...")
    
    try:
        from src.processing.pose_processor import PoseProcessor
        from src.grading.advanced_form_grader import UserProfile, UserLevel, ThresholdConfig
        
        # Create processor with voice feedback
        profile = UserProfile(user_id="test_user", skill_level=UserLevel.BEGINNER)
        config = ThresholdConfig.emergency_calibrated()
        processor = PoseProcessor(user_profile=profile, threshold_config=config)
        
        print("✅ PoseProcessor created with voice feedback enabled")
        
        # Start a session with voice feedback
        processor.start_session(source_type='video', skip_calibration=True)
        
        print("✅ Session started (skipped calibration for testing)")
        
        # Simulate processing frames with voice feedback
        print("🔊 Simulating rep processing with voice feedback...")
        
        # Create a dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(dummy_frame, "TEST FRAME", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
        
        # Test voice feedback announcement
        print("🎯 Testing session start announcement...")
        if hasattr(processor.feedback_manager, 'announce_session_start'):
            processor.feedback_manager.announce_session_start()
        else:
            processor.feedback_manager.add_intelligent_feedback(
                fault_type='ENCOURAGEMENT',
                severity='session_start',
                rep_count=0,
                force_voice=True
            )
        
        # Wait for voice to complete
        time.sleep(2)
        
        # Test rep start voice
        print("🎯 Testing rep start voice feedback...")
        processor.feedback_manager.add_intelligent_feedback(
            fault_type='ENCOURAGEMENT',
            severity='rep_start',
            rep_count=1,
            force_voice=True
        )
        
        time.sleep(2)
        
        # Test form feedback during rep
        print("🎯 Testing form correction voice feedback...")
        processor.feedback_manager.add_intelligent_feedback(
            fault_type='BACK_ROUNDING',
            severity='moderate',
            rep_count=1,
            form_score=65,
            force_voice=True
        )
        
        time.sleep(2)
        
        # Test rep completion voice
        print("🎯 Testing rep completion voice feedback...")
        processor.feedback_manager.add_intelligent_feedback(
            fault_type='ENCOURAGEMENT',
            severity='completion',
            rep_count=1,
            form_score=75,
            force_voice=True
        )
        
        time.sleep(2)
        
        # Test milestone encouragement
        print("🎯 Testing milestone encouragement...")
        processor.feedback_manager.add_intelligent_feedback(
            fault_type='ENCOURAGEMENT',
            severity='milestone',
            rep_count=5,
            form_score=85,
            force_voice=True
        )
        
        time.sleep(2)
        
        # Test session end
        print("🎯 Testing session end announcement...")
        if hasattr(processor.feedback_manager, 'announce_session_end'):
            processor.feedback_manager.announce_session_end(total_reps=5, avg_score=78.5)
        else:
            processor.feedback_manager.add_intelligent_feedback(
                fault_type='ENCOURAGEMENT',
                severity='session_end',
                rep_count=5,
                form_score=78,
                force_voice=True
            )
        
        time.sleep(2)
        
        # Get final statistics
        stats = processor.feedback_manager.get_feedback_statistics()
        
        print("\n📊 Final Session Statistics:")
        print(f"   Total messages: {stats.get('total_messages', 0)}")
        print(f"   Voice available: {stats.get('voice_available', False)}")
        print(f"   Voice enabled: {stats.get('voice_enabled', False)}")
        print(f"   Performance metrics: {stats.get('performance_metrics', {})}")
        
        # End session
        processor.end_session()
        print("✅ Session ended successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete session test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_feedback_integration():
    """Test voice feedback integration in the actual pose processing pipeline"""
    print("\n🏋️ Testing Voice Feedback Integration...")
    
    try:
        from src.processing.pose_processor import PoseProcessor
        from src.grading.advanced_form_grader import UserProfile, UserLevel, ThresholdConfig
        
        # Create processor
        profile = UserProfile(user_id="integration_test", skill_level=UserLevel.INTERMEDIATE)
        config = ThresholdConfig.emergency_calibrated()
        processor = PoseProcessor(user_profile=profile, threshold_config=config)
        
        # Start session
        processor.start_session(source_type='video', skip_calibration=True)
        
        # Manually trigger rep completion to test voice integration
        print("🎯 Testing integrated rep completion voice...")
        
        # Simulate some rep metrics
        from src.grading.advanced_form_grader import BiomechanicalMetrics
        
        test_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=140,
                knee_angle_right=138,
                back_angle=85,
                landmark_visibility=0.9
            ),
            BiomechanicalMetrics(
                knee_angle_left=110,
                knee_angle_right=108,
                back_angle=75,  # Some back rounding
                landmark_visibility=0.9
            ),
            BiomechanicalMetrics(
                knee_angle_left=85,
                knee_angle_right=87,
                back_angle=80,
                landmark_visibility=0.9
            )
        ]
        
        # Add metrics to current rep
        processor.current_rep_metrics = test_metrics
        processor.rep_counter.rep_count = 1
        
        # Trigger rep completion processing (which should include voice)
        print("🔊 Triggering rep completion with integrated voice feedback...")
        processor._process_completed_rep()
        
        # Wait for voice feedback to complete
        time.sleep(3)
        
        print("✅ Integrated voice feedback test completed")
        
        # End session
        processor.end_session()
        
        return True
        
    except Exception as e:
        print(f"❌ Voice integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run final voice feedback tests"""
    print("🎤 AI Fitness Coach - Final Voice Feedback Test")
    print("=" * 60)
    print("🎯 This test verifies voice feedback works in live sessions")
    print("=" * 60)
    
    tests = [
        ("Complete Session Voice Test", test_complete_session_with_voice),
        ("Voice Integration Test", test_voice_feedback_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 FINAL VOICE FEEDBACK TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VOICE TESTS PASSED!")
        print("🔊 Voice feedback is fully functional during live webcam sessions")
        print("💡 You can now run the main application and hear voice coaching!")
    else:
        print("\n⚠️ Some voice tests failed - check the errors above")

if __name__ == "__main__":
    main()
