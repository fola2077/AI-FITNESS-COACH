#!/usr/bin/env python3
"""
Interactive Voice Feedback Test
This script lets you test and hear the voice feedback system in action
"""

import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_voice_feedback_interactive():
    """Interactive test to hear the voice feedback system"""
    
    print("🎙️ INTERACTIVE VOICE FEEDBACK TEST")
    print("=" * 50)
    print("This test will play voice messages so you can hear the feedback system!")
    print("Make sure your speakers/headphones are on! 🔊")
    print()
    
    try:
        # Import required components
        from src.feedback.voice_engine import VoiceFeedbackEngine
        from src.feedback.enhanced_feedback_manager import EnhancedFeedbackManager
        from src.feedback.feedback_types import (FeedbackStyle, FeedbackPriority, 
                                                EnhancedFeedbackMessage, MessageCategory)
        
        print("✅ Voice system components imported successfully")
        
        # Test 1: Direct Voice Engine Test
        print("\n" + "="*50)
        print("🔊 TEST 1: Direct Voice Engine")
        print("="*50)
        
        voice_engine = VoiceFeedbackEngine()
        time.sleep(1)  # Let it initialize
        
        print("Testing different voice styles and messages...")
        
        # Test different voice styles with proper EnhancedFeedbackMessage objects
        test_messages = [
            ("Welcome to your AI Fitness Coach!", FeedbackStyle.MOTIVATIONAL),
            ("Keep your back straight and chest up", FeedbackStyle.INSTRUCTIONAL),
            ("Great job! Your form is improving", FeedbackStyle.ENCOURAGING),
            ("Warning: Your knees are caving inward", FeedbackStyle.URGENT),
            ("Focus on going deeper in your squat", FeedbackStyle.CORRECTIVE)
        ]
        
        for i, (text, style) in enumerate(test_messages, 1):
            print(f"\n🎵 Playing message {i}/5: {style.value}")
            print(f"   Text: '{text}'")
            
            # Create proper EnhancedFeedbackMessage object
            message = EnhancedFeedbackMessage(
                message=text,
                priority=FeedbackPriority.HIGH.value,  # Use .value for int
                timestamp=time.time(),
                style=style,
                voice_message=text,  # Shorter voice version
                category="technique"  # Use string category
            )
            
            voice_engine.speak_message(message)
            time.sleep(0.5)  # Small delay between messages
            
            # Wait for message to finish
            while voice_engine.is_speaking:  # is_speaking is a property, not method
                time.sleep(0.1)
            
            time.sleep(1)  # Pause between messages
        
        voice_engine.shutdown()
        print("✅ Voice engine test completed")
        
        # Test 2: Enhanced Feedback Manager Test
        print("\n" + "="*50)
        print("🤖 TEST 2: Enhanced Feedback Manager")
        print("="*50)
        
        enhanced_manager = EnhancedFeedbackManager()
        time.sleep(1)  # Let it initialize
        
        print("Testing intelligent feedback with realistic squat analysis...")
        
        # Simulate realistic squat analysis results
        squat_scenarios = [
            {
                "name": "Perfect Squat",
                "analysis": {
                    "faults": [],
                    "scores": {"overall": 95, "depth": 90, "safety": 98},
                    "rep_number": 1,
                    "analysis_details": {"phase": "ascent"}
                }
            },
            {
                "name": "Knee Cave Issue",
                "analysis": {
                    "faults": ["Knees caving inward", "Insufficient depth"],
                    "scores": {"overall": 65, "depth": 60, "safety": 70},
                    "rep_number": 2,
                    "analysis_details": {"phase": "bottom"}
                }
            },
            {
                "name": "Back Rounding",
                "analysis": {
                    "faults": ["Back rounding detected", "Forward lean excessive"],
                    "scores": {"overall": 55, "depth": 80, "safety": 40},
                    "rep_number": 3,
                    "analysis_details": {"phase": "descent"}
                }
            },
            {
                "name": "Partial Rep",
                "analysis": {
                    "faults": ["Partial repetition - insufficient depth"],
                    "scores": {"overall": 75, "depth": 45, "safety": 85},
                    "rep_number": 4,
                    "analysis_details": {"phase": "ascent"}
                }
            }
        ]
        
        for i, scenario in enumerate(squat_scenarios, 1):
            print(f"\n🏋️ Scenario {i}: {scenario['name']}")
            print(f"   Faults: {scenario['analysis']['faults']}")
            print(f"   Overall Score: {scenario['analysis']['scores']['overall']}%")
            
            # Process with enhanced feedback
            result = enhanced_manager.process_pose_analysis(scenario["analysis"])
            
            print(f"   Generated {len(result.get('messages', []))} feedback messages")
            for msg in result.get('messages', []):
                print(f"   - {msg.get('text', 'N/A')} (Voice: {msg.get('voice_text', 'N/A')})")
            
            # Wait for voice to finish
            time.sleep(3)  # Give time for voice feedback
            while enhanced_manager.voice_engine.is_speaking:  # Property, not method
                time.sleep(0.1)
            
            time.sleep(1)  # Pause between scenarios
        
        enhanced_manager.shutdown()
        print("✅ Enhanced feedback manager test completed")
        
        # Test 3: Form Grader Integration Test
        print("\n" + "="*50)
        print("🎯 TEST 3: Form Grader Integration")
        print("="*50)
        
        print("Testing integration with actual form grader...")
        
        from src.grading.advanced_form_grader import IntelligentFormGrader, UserProfile, UserLevel
        
        # Create form grader with enhanced feedback
        user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.BEGINNER)
        form_grader = IntelligentFormGrader(user_profile=user_profile)
        
        # Enable voice feedback
        form_grader.set_voice_feedback_enabled(True)
        status = form_grader.get_enhanced_feedback_status()
        
        print(f"Enhanced feedback enabled: {status.get('enabled', False)}")
        
        # Simulate form analysis with enhanced feedback
        print("\n🔍 Simulating form analysis with voice feedback...")
        
        # Mock frame metrics for a squat rep
        mock_frame_metrics = [
            {"overall_score": 0.8, "safety_score": 0.9, "timestamp": 0.1},
            {"overall_score": 0.7, "safety_score": 0.6, "timestamp": 0.2},  # Issues detected
            {"overall_score": 0.85, "safety_score": 0.9, "timestamp": 0.3}
        ]
        
        # This would normally be called during actual analysis
        print("📊 Processing mock squat analysis...")
        
        # Simulate the analysis that would trigger enhanced feedback
        mock_analysis = {
            "faults": ["Hip shift to right side", "Slight forward lean"],
            "scores": {"overall": 75, "depth": 80, "safety": 70},
            "rep_number": 1,
            "component_scores": {
                "depth": {"score": 80},
                "safety": {"score": 70},
                "stability": {"score": 75}
            },
            "analysis_details": {"phase": "ascent"}
        }
        
        # Process enhanced feedback
        enhanced_result = form_grader._process_enhanced_feedback(
            mock_analysis["faults"], 
            mock_analysis["analysis_details"], 
            mock_analysis["scores"]["overall"],
            mock_frame_metrics,
            1
        )
        
        if enhanced_result:
            print(f"✅ Enhanced feedback processed: {enhanced_result.get('status', 'unknown')}")
            print(f"   Messages generated: {enhanced_result.get('messages_generated', 0)}")
            print(f"   Voice messages sent: {enhanced_result.get('voice_messages_sent', 0)}")
        
        # Wait for any remaining voice
        time.sleep(2)
        
        form_grader.enhanced_feedback_manager.shutdown()
        print("✅ Form grader integration test completed")
        
        print("\n" + "="*50)
        print("🎉 VOICE FEEDBACK TEST SUMMARY")
        print("="*50)
        print("Direct Voice Engine            ✅ PASS")
        print("Enhanced Feedback Manager      ✅ PASS") 
        print("Form Grader Integration        ✅ PASS")
        print("\n🔊 You should have heard various voice messages!")
        print("   - Motivational messages")
        print("   - Form corrections")
        print("   - Encouragement")
        print("   - Safety warnings")
        print("   - Instructional guidance")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Voice Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Make sure your speakers/headphones are on!")
    print("Press Enter when ready to start the voice test...")
    input()
    
    success = test_voice_feedback_interactive()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 Voice feedback test completed successfully!")
        print("You should have heard the AI coach speaking!")
    else:
        print("❌ Voice feedback test failed.")
    
    print("Press Enter to exit...")
    input()
    
    sys.exit(0 if success else 1)
