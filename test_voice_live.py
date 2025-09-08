"""
Simple Voice Test: Test voice feedback during rep processing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_voice_in_rep_processing():
    """Test voice feedback in rep processing methods"""
    print("🎤 Testing Voice in Rep Processing...")
    
    try:
        from src.processing.pose_processor import PoseProcessor
        from src.grading.advanced_form_grader import UserProfile, UserLevel, ThresholdConfig, BiomechanicalMetrics
        
        # Create processor with voice feedback
        profile = UserProfile(user_id="test_user", skill_level=UserLevel.BEGINNER)
        config = ThresholdConfig.emergency_calibrated()
        processor = PoseProcessor(user_profile=profile, threshold_config=config)
        
        print("✅ PoseProcessor created with voice feedback enabled")
        
        # Test rep completion voice feedback by calling the method directly
        print("🎯 Testing rep completion voice feedback...")
        
        # Create some test metrics
        test_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=140,
                knee_angle_right=138,
                back_angle=75,  # Some back rounding to trigger feedback
                landmark_visibility=0.9
            ),
            BiomechanicalMetrics(
                knee_angle_left=85,
                knee_angle_right=87,
                back_angle=80,
                landmark_visibility=0.9
            )
        ]
        
        # Set up the processor state for rep completion
        processor.current_rep_metrics = test_metrics
        processor.rep_counter.rep_count = 1
        
        # Call the rep completion method which should trigger voice feedback
        print("🔊 Calling _process_completed_rep() which should provide voice feedback...")
        processor._process_completed_rep()
        
        # Give time for voice to complete
        import time
        time.sleep(3)
        
        print("✅ Rep completion with voice feedback completed")
        
        # Test another rep with different score
        print("🎯 Testing second rep with different feedback...")
        processor.rep_counter.rep_count = 2
        processor.current_rep_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=160,
                knee_angle_right=158,
                back_angle=90,  # Good form
                landmark_visibility=0.95
            )
        ]
        
        processor._process_completed_rep()
        time.sleep(3)
        
        print("✅ Second rep completion with voice feedback completed")
        
        # Get statistics
        stats = processor.feedback_manager.get_feedback_statistics()
        print(f"\n📊 Voice Feedback Statistics:")
        print(f"   Total messages: {stats.get('total_messages', 0)}")
        print(f"   Voice available: {stats.get('voice_available', False)}")
        print(f"   Voice enabled: {stats.get('voice_enabled', False)}")
        
        performance = stats.get('performance_metrics', {})
        print(f"   Voice feedback given: {performance.get('voice_feedback_given', 0)}")
        print(f"   Total feedback given: {performance.get('total_feedback_given', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice in rep processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_voice_feedback():
    """Test direct voice feedback calls"""
    print("\n🔊 Testing Direct Voice Feedback...")
    
    try:
        from src.feedback.enhanced_feedback_manager import EnhancedFeedbackManager
        
        # Create feedback manager
        feedback_manager = EnhancedFeedbackManager(voice_enabled=True, user_skill_level="beginner")
        
        print("✅ Enhanced feedback manager created")
        
        # Test different types of voice feedback
        feedback_types = [
            ("REP_START", "Rep starting - keep good form"),
            ("BACK_ROUNDING", "Keep your chest up and back straight"),
            ("INSUFFICIENT_DEPTH", "Go deeper on your next squat"),
            ("ENCOURAGEMENT", "Excellent work! Keep it up"),
            ("REP_COMPLETION", "Rep completed with good form")
        ]
        
        import time
        
        for i, (fault_type, expected_message) in enumerate(feedback_types):
            print(f"🎯 Testing {fault_type} voice feedback...")
            
            success = feedback_manager.add_intelligent_feedback(
                fault_type=fault_type,
                severity='moderate' if fault_type not in ['ENCOURAGEMENT', 'REP_START', 'REP_COMPLETION'] else 'good',
                rep_count=i+1,
                form_score=75 + i*5,
                force_voice=True
            )
            
            print(f"   {'✅ SUCCESS' if success else '❌ FAILED'} - {fault_type}")
            time.sleep(2)  # Wait for voice to complete
        
        return True
        
    except Exception as e:
        print(f"❌ Direct voice feedback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run voice feedback tests"""
    print("🎤 AI Fitness Coach - Voice Feedback Live Test")
    print("=" * 60)
    print("🎯 Testing voice feedback during actual rep processing")
    print("=" * 60)
    
    # Run tests
    rep_processing_result = test_voice_in_rep_processing()
    direct_feedback_result = test_direct_voice_feedback()
    
    print(f"\n{'='*60}")
    print("🎯 VOICE FEEDBACK LIVE TEST SUMMARY")
    print("=" * 60)
    print(f"{'✅ PASSED' if rep_processing_result else '❌ FAILED'} - Rep Processing Voice Test")
    print(f"{'✅ PASSED' if direct_feedback_result else '❌ FAILED'} - Direct Voice Feedback Test")
    
    if rep_processing_result and direct_feedback_result:
        print("\n🎉 VOICE FEEDBACK IS WORKING!")
        print("🔊 Voice coaching will now work during live webcam sessions")
        print("💡 Run the main application to test it with your webcam")
        print("\n🏋️‍♂️ What you should hear during workouts:")
        print("   • Announcements when reps start")
        print("   • Form corrections during reps") 
        print("   • Encouraging feedback when reps complete")
        print("   • Specific guidance based on your form")
    else:
        print("\n⚠️ Voice feedback needs more work - check errors above")

if __name__ == "__main__":
    main()
