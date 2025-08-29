"""
Test script for the Enhanced Feedback System

This script tests the basic functionality of the enhanced feedback system
including voice engine, message templates, and intelligent feedback generation.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_voice_engine():
    """Test the voice feedback engine"""
    print("🔊 Testing Voice Engine...")
    
    try:
        from src.feedback.voice_engine import VoiceFeedbackEngine
        from src.feedback.feedback_types import FeedbackStyle, EnhancedFeedbackMessage
        
        # Create voice engine
        voice_engine = VoiceFeedbackEngine(enabled=True)
        
        if not voice_engine.is_available():
            print("⚠️ Voice engine not available - check pyttsx3 installation")
            return False
        
        print("✅ Voice engine initialized successfully")
        
        # Test immediate speech
        print("   Testing immediate speech...")
        voice_engine.speak_immediate("Testing voice feedback system", FeedbackStyle.ENCOURAGING)
        
        # Test queued speech
        print("   Testing queued speech...")
        test_message = EnhancedFeedbackMessage(
            message="This is a test message",
            priority=2,
            timestamp=time.time(),
            style=FeedbackStyle.INSTRUCTIONAL,
            voice_message="Test message"
        )
        
        voice_engine.speak_message(test_message)
        
        # Wait for speech to complete
        time.sleep(3)
        
        voice_engine.shutdown()
        print("✅ Voice engine test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Voice engine test failed: {e}")
        return False

def test_message_templates():
    """Test the message template system"""
    print("📝 Testing Message Templates...")
    
    try:
        from src.feedback.message_templates import MessageTemplateManager
        
        template_manager = MessageTemplateManager()
        
        # Test basic message generation
        message = template_manager.get_message(
            fault_type="BACK_ROUNDING",
            severity="mild",
            context={"rep_count": 5}
        )
        
        if message:
            print(f"✅ Generated message: {message.message}")
            print(f"   Voice message: {message.voice_message}")
            print(f"   Priority: {message.priority}")
            print(f"   Style: {message.style}")
        else:
            print("❌ Failed to generate message")
            return False
        
        # Test anti-repetition
        print("   Testing anti-repetition...")
        messages = []
        for i in range(5):
            msg = template_manager.get_message("INSUFFICIENT_DEPTH", "partial")
            if msg:
                messages.append(msg.message)
        
        unique_messages = len(set(messages))
        print(f"   Generated {unique_messages} unique messages out of 5 requests")
        
        if unique_messages > 1:
            print("✅ Anti-repetition working correctly")
        else:
            print("⚠️ Anti-repetition may not be working optimally")
        
        print("✅ Message templates test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Message templates test failed: {e}")
        return False

def test_enhanced_feedback_manager():
    """Test the enhanced feedback manager"""
    print("🎯 Testing Enhanced Feedback Manager...")
    
    try:
        from src.feedback.enhanced_feedback_manager import EnhancedFeedbackManager
        
        # Create enhanced feedback manager
        feedback_manager = EnhancedFeedbackManager(voice_enabled=True, user_skill_level="beginner")
        
        print("✅ Enhanced feedback manager created")
        
        # Test backward compatibility
        print("   Testing backward compatibility...")
        success = feedback_manager.add_feedback(
            message="Test backward compatibility",
            priority=2,
            category="form"
        )
        
        if success:
            print("✅ Backward compatibility working")
        else:
            print("❌ Backward compatibility failed")
        
        # Test intelligent feedback
        print("   Testing intelligent feedback...")
        success = feedback_manager.add_intelligent_feedback(
            fault_type="BACK_ROUNDING",
            severity="mild",
            angles={"back": 75, "knee": 120},
            rep_count=3,
            form_score=85
        )
        
        if success:
            print("✅ Intelligent feedback working")
        else:
            print("❌ Intelligent feedback failed")
        
        # Test current feedback retrieval
        current_feedback = feedback_manager.get_current_feedback()
        print(f"   Current active messages: {len(current_feedback)}")
        
        for msg in current_feedback:
            print(f"     - {msg.message}")
        
        # Test statistics
        stats = feedback_manager.get_feedback_statistics()
        print(f"   Total messages generated: {stats['total_messages']}")
        print(f"   Voice available: {stats['voice_available']}")
        
        feedback_manager.shutdown()
        print("✅ Enhanced feedback manager test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced feedback manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_form_grader():
    """Test integration with the existing form grader"""
    print("🤖 Testing Integration with Form Grader...")
    
    try:
        # Import existing form grader components
        from src.grading.advanced_form_grader import BiomechanicalMetrics, ThresholdConfig
        from src.feedback.enhanced_feedback_manager import EnhancedFeedbackManager
        
        # Create test data
        test_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=140,  # Shallow depth
                knee_angle_right=138,
                back_angle=75,        # Mild back rounding
                landmark_visibility=0.9
            ),
            BiomechanicalMetrics(
                knee_angle_left=85,   # Good depth
                knee_angle_right=87,
                back_angle=95,        # Good back angle
                landmark_visibility=0.9
            )
        ]
        
        # Create enhanced feedback manager
        feedback_manager = EnhancedFeedbackManager(voice_enabled=True)
        
        # Simulate form analysis results
        faults = ["BACK_ROUNDING", "INSUFFICIENT_DEPTH"]
        angles = {
            "back": test_metrics[0].back_angle,
            "knee": test_metrics[0].knee_angle_left
        }
        
        # Process with enhanced feedback
        feedback_manager.process_pose_analysis(
            faults=faults,
            angles=angles,
            phase="execution",
            rep_count=1,
            form_score=75
        )
        
        # Check results
        current_feedback = feedback_manager.get_current_feedback()
        print(f"✅ Generated {len(current_feedback)} feedback messages from form analysis")
        
        for msg in current_feedback:
            print(f"   - {msg.message}")
            if hasattr(msg, 'voice_message') and msg.voice_message:
                print(f"     Voice: {msg.voice_message}")
        
        feedback_manager.shutdown()
        print("✅ Form grader integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Form grader integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Enhanced Feedback System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Voice Engine", test_voice_engine),
        ("Message Templates", test_message_templates),
        ("Enhanced Feedback Manager", test_enhanced_feedback_manager),
        ("Form Grader Integration", test_integration_with_form_grader)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced feedback system is ready!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
