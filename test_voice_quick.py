"""
Simple test to verify voice feedback is working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_basic_voice():
    """Test basic voice functionality"""
    print("🎤 Testing Basic Voice Functionality...")
    
    try:
        from src.feedback.enhanced_feedback_manager import EnhancedFeedbackManager
        
        # Create feedback manager with voice enabled
        feedback_manager = EnhancedFeedbackManager(voice_enabled=True, user_skill_level="beginner")
        
        print("✅ EnhancedFeedbackManager created successfully")
        
        # Test intelligent feedback with voice
        print("🔊 Testing intelligent feedback with voice...")
        
        # Test rep completion feedback
        success = feedback_manager.add_intelligent_feedback(
            fault_type='ENCOURAGEMENT',
            severity='completion',
            rep_count=1,
            form_score=75,
            force_voice=True
        )
        
        print(f"Rep completion feedback: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        # Test form correction feedback
        success = feedback_manager.add_intelligent_feedback(
            fault_type='BACK_ROUNDING',
            severity='moderate',
            rep_count=1,
            form_score=60,
            force_voice=True
        )
        
        print(f"Form correction feedback: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        # Test depth feedback
        success = feedback_manager.add_intelligent_feedback(
            fault_type='INSUFFICIENT_DEPTH',
            severity='mild',
            rep_count=2,
            form_score=70,
            force_voice=True
        )
        
        print(f"Depth feedback: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        # Get statistics
        stats = feedback_manager.get_feedback_statistics()
        print(f"\n📊 Feedback Statistics:")
        print(f"   Total messages: {stats.get('total_messages', 0)}")
        print(f"   Voice available: {stats.get('voice_available', False)}")
        print(f"   Voice enabled: {stats.get('voice_enabled', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic voice test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pose_processor_voice():
    """Test voice feedback through PoseProcessor"""
    print("\n🏋️ Testing Voice Through PoseProcessor...")
    
    try:
        from src.processing.pose_processor import PoseProcessor
        from src.grading.advanced_form_grader import UserProfile, UserLevel, ThresholdConfig
        
        # Create processor with voice feedback
        profile = UserProfile(user_id="test_user", skill_level=UserLevel.BEGINNER)
        config = ThresholdConfig.emergency_calibrated()
        processor = PoseProcessor(user_profile=profile, threshold_config=config)
        
        print("✅ PoseProcessor created with voice feedback")
        print(f"   Feedback manager type: {type(processor.feedback_manager).__name__}")
        
        # Check if voice is available
        if hasattr(processor.feedback_manager, 'voice_engine'):
            voice_available = processor.feedback_manager.voice_engine.is_available()
            print(f"   Voice engine available: {voice_available}")
        
        # Test direct feedback through processor
        print("🔊 Testing direct feedback...")
        
        # Simulate some feedback
        feedback_manager = processor.feedback_manager
        
        # Test with simple message
        result = feedback_manager.add_intelligent_feedback(
            fault_type='ENCOURAGEMENT',
            severity='rep_start',
            rep_count=1,
            force_voice=True
        )
        
        print(f"Direct feedback test: {'✅ SUCCESS' if result else '❌ FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ PoseProcessor voice test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎤 AI Fitness Coach - Quick Voice Test")
    print("=" * 50)
    
    # Run basic tests
    basic_result = test_basic_voice()
    processor_result = test_pose_processor_voice()
    
    print("\n" + "=" * 50)
    print("🎯 QUICK VOICE TEST SUMMARY")
    print("=" * 50)
    print(f"{'✅ PASSED' if basic_result else '❌ FAILED'} - Basic Voice Test")
    print(f"{'✅ PASSED' if processor_result else '❌ FAILED'} - PoseProcessor Voice Test")
    
    if basic_result and processor_result:
        print("\n🎉 Voice feedback should be working!")
        print("💡 Try running the main application and start a webcam session")
    else:
        print("\n⚠️ Voice feedback has issues that need to be fixed")
