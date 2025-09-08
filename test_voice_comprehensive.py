import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
import threading
from src.feedback.feedback_manager import FeedbackManager
from src.processing.pose_processor import PoseProcessor, SessionState
from src.grading.advanced_form_grader import UserProfile, UserLevel, ThresholdConfig
from src.utils.rep_counter import RepCounter, MovementPhase

def test_voice_engine():
    """Test if the voice engine initializes and works"""
    print("🎤 Testing Voice Engine...")
    
    try:
        import pyttsx3
        
        # Test basic TTS engine
        engine = pyttsx3.init()
        
        # Get and display current settings
        rate = engine.getProperty('rate')
        volume = engine.getProperty('volume')
        voices = engine.getProperty('voices')
        
        print(f"✅ TTS Engine initialized successfully")
        print(f"   Rate: {rate}")
        print(f"   Volume: {volume}")
        print(f"   Available voices: {len(voices) if voices else 0}")
        
        if voices:
            for i, voice in enumerate(voices[:2]):  # Show first 2 voices
                print(f"   Voice {i}: {voice.name}")
        
        # Test voice output
        print("\n🔊 Testing voice output...")
        engine.say("Voice test successful")
        engine.runAndWait()
        
        engine.stop()
        return True
        
    except Exception as e:
        print(f"❌ Voice engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_feedback_manager():
    """Test the FeedbackManager class"""
    print("\n🎯 Testing FeedbackManager...")
    
    try:
        feedback_manager = FeedbackManager()
        
        # Test initialization
        print(f"✅ FeedbackManager initialized")
        print(f"   Voice enabled: {getattr(feedback_manager, 'voice_enabled', 'Unknown')}")
        print(f"   Voice feedback: {getattr(feedback_manager, 'enable_voice_feedback', 'Unknown')}")
        
        # Check available methods
        methods = [method for method in dir(feedback_manager) if not method.startswith('_')]
        print(f"   Available methods: {methods}")
        
        # Test different feedback types
        test_messages = [
            "Starting rep analysis",
            "Good depth achieved",
            "Keep your back straight",
            "Rep 1 completed"
        ]
        
        print("\n🔊 Testing feedback messages...")
        for i, message in enumerate(test_messages):
            print(f"   Testing message {i+1}: '{message}'")
            
            # Test text feedback
            feedback_manager.provide_feedback("info", message)
            
            # Test voice feedback if available
            if hasattr(feedback_manager, 'provide_voice_feedback'):
                feedback_manager.provide_voice_feedback(message)
            elif hasattr(feedback_manager, 'speak'):
                feedback_manager.speak(message)
            elif hasattr(feedback_manager, 'voice_engine'):
                if feedback_manager.voice_engine:
                    feedback_manager.voice_engine.say(message)
                    feedback_manager.voice_engine.runAndWait()
            
            time.sleep(2)  # Small delay between messages
        
        return True
        
    except Exception as e:
        print(f"❌ FeedbackManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_during_rep_analysis():
    """Test voice feedback during actual rep analysis"""
    print("\n🏋️ Testing Voice During Rep Analysis...")
    
    try:
        # Create processor with voice feedback
        profile = UserProfile(user_id="test_user", skill_level=UserLevel.INTERMEDIATE)
        config = ThresholdConfig.emergency_calibrated()
        processor = PoseProcessor(user_profile=profile, threshold_config=config)
        
        # Check if feedback manager has voice capabilities
        feedback_manager = processor.feedback_manager
        print(f"✅ Processor created with feedback manager")
        
        # Test voice feedback integration
        if hasattr(feedback_manager, 'voice_enabled'):
            print(f"   Voice enabled: {feedback_manager.voice_enabled}")
        
        # Simulate rep completion with voice feedback
        print("\n🎯 Simulating rep completion with voice...")
        
        # Test rep start voice
        if hasattr(feedback_manager, 'announce_rep_start'):
            feedback_manager.announce_rep_start(1)
        else:
            feedback_manager.provide_feedback("info", "Starting rep 1")
        
        time.sleep(2)
        
        # Test rep completion voice
        if hasattr(feedback_manager, 'announce_rep_completion'):
            feedback_manager.announce_rep_completion(1, 75)
        else:
            feedback_manager.provide_feedback("success", "Rep 1 completed with 75% form score")
        
        time.sleep(2)
        
        # Test form feedback voice
        form_issues = ["Keep your back straight", "Go deeper on the next rep"]
        for issue in form_issues:
            feedback_manager.provide_feedback("warning", issue)
            time.sleep(1.5)
        
        return True
        
    except Exception as e:
        print(f"❌ Rep analysis voice test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_threading():
    """Test if voice feedback works properly in threaded environment"""
    print("\n🧵 Testing Voice in Threading Environment...")
    
    try:
        feedback_manager = FeedbackManager()
        
        def voice_worker(message_id):
            message = f"Threaded voice test {message_id}"
            print(f"   🔊 Thread {message_id}: '{message}'")
            feedback_manager.provide_feedback("info", message)
            return f"Thread {message_id} completed"
        
        # Test multiple voice messages in separate threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=voice_worker, args=(i+1,))
            threads.append(thread)
            thread.start()
            time.sleep(0.5)  # Stagger the starts
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        print("✅ Threading voice test completed")
        return True
        
    except Exception as e:
        print(f"❌ Threading voice test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_voice_feedback_integration():
    """Check how voice feedback is integrated in the main processing loop"""
    print("\n🔍 Checking Voice Feedback Integration...")
    
    try:
        # Check PoseProcessor for voice feedback calls
        from src.processing.pose_processor import PoseProcessor
        
        processor_methods = dir(PoseProcessor)
        voice_related_methods = [method for method in processor_methods if 'voice' in method.lower() or 'feedback' in method.lower()]
        
        print(f"✅ PoseProcessor methods related to feedback:")
        for method in voice_related_methods:
            print(f"   • {method}")
        
        # Check FeedbackManager methods
        from src.feedback.feedback_manager import FeedbackManager
        
        feedback_methods = dir(FeedbackManager)
        voice_methods = [method for method in feedback_methods if 'voice' in method.lower() or 'speak' in method.lower() or 'announce' in method.lower()]
        
        print(f"\n✅ FeedbackManager voice-related methods:")
        for method in voice_methods:
            print(f"   • {method}")
        
        # Check if voice feedback is called during rep processing
        print(f"\n🔍 Checking _process_completed_rep method...")
        
        # This would show us if voice feedback is actually called
        import inspect
        
        if hasattr(PoseProcessor, '_process_completed_rep'):
            source = inspect.getsource(PoseProcessor._process_completed_rep)
            if 'voice' in source.lower() or 'speak' in source.lower() or 'announce' in source.lower():
                print("✅ Voice feedback calls found in rep processing")
            else:
                print("❌ No voice feedback calls found in rep processing")
                print("🔧 This might be why voice isn't working during reps!")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive voice feedback tests"""
    print("🎤 AI Fitness Coach - Voice Feedback Diagnostic")
    print("=" * 60)
    
    tests = [
        ("Voice Engine Basic Test", test_voice_engine),
        ("FeedbackManager Test", test_feedback_manager),
        ("Rep Analysis Voice Test", test_voice_during_rep_analysis),
        ("Threading Voice Test", test_voice_threading),
        ("Integration Check", check_voice_feedback_integration)
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
    print("🎯 VOICE FEEDBACK DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n🔧 RECOMMENDED FIXES:")
        if not results.get("Voice Engine Basic Test", True):
            print("1. Install/reinstall pyttsx3: pip install --upgrade pyttsx3")
        if not results.get("FeedbackManager Test", True):
            print("2. Check FeedbackManager voice initialization")
        if not results.get("Integration Check", True):
            print("3. Add voice feedback calls to rep processing methods")
    else:
        print("\n🎉 All voice tests passed! Voice should be working.")

if __name__ == "__main__":
    main()
