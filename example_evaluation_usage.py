#!/usr/bin/env python3
"""
Example: Using integrated evaluation log    print(f"1. Add processor.start_evaluation_session('P01_A')")
    print("2. Run your normal webcam loop (UNCHANGED)")
    print("3. Add processor.finalize_evaluation_session() at the end")
    print("4. All evaluation data automatically collected!") in your AI Fitness Coach app

This shows how to use the evaluation logging that's now built into your existing DataLogger.
No separate systems needed - everything integrates seamlessly!
"""

from src.processing.pose_processor import PoseProcessor
from src.grading.advanced_form_grader import UserProfile, UserLevel, ThresholdConfig
import cv2
import time

def run_evaluation_session_example():
    """Example of running an evaluation session with integrated logging"""
    
    print("🎯 AI FITNESS COACH - EVALUATION SESSION EXAMPLE")
    print("=" * 60)
    
    # 1. Initialize your existing processor (same as always)
    user_profile = UserProfile(user_id="P01", skill_level=UserLevel.INTERMEDIATE)
    threshold_config = ThresholdConfig.emergency_calibrated()
    
    processor = PoseProcessor(
        user_profile=user_profile, 
        threshold_config=threshold_config,
        enable_validation=True
    )
    
    print("✅ PoseProcessor initialized (same as normal)")
    
    # 2. START EVALUATION SESSION (NEW!)
    # This is the ONLY new thing you need to add
    eval_session_id = processor.start_evaluation_session("P01_A")  # or "P01_B" for condition B
    
    print(f"🎯 Evaluation session started: {eval_session_id}")
    print("   Data will be automatically logged during processing!")
    
    # 3. Run your normal session (UNCHANGED!)
    # Everything else stays exactly the same
    print("\n📹 Starting webcam capture...")
    print("   (In real app, you'd open cv2.VideoCapture here)")
    print("   (All frame processing automatically logs evaluation data)")
    
    # Simulate some frame processing
    print("\n🔄 Simulating frame processing...")
    for i in range(10):
        print(f"   Frame {i+1}: Processing... (auto-logging evaluation data)")
        time.sleep(0.1)  # Simulate processing time
    
    print("\n✅ Session completed!")
    
    # 4. FINALIZE EVALUATION (NEW!)
    # Just one call at the end
    metadata = processor.finalize_evaluation_session()
    
    print(f"📊 Evaluation data saved:")
    print(f"   Location: data/logs/evaluation/P01_A/")
    print(f"   Files: frames_P01_A.csv, reps_P01_A.csv, cues_P01_A.csv")
    print(f"   Metadata: {metadata}")
    
    print(f"\n🎯 INTEGRATION COMPLETE!")
    print("=" * 60)
    print("✅ Zero changes to your existing processing loop")
    print("✅ Automatic evaluation data collection")
    print("✅ All data saved in your existing data/logs structure")
    print("✅ Ready for dissertation analysis")
    
    print(f"\n📋 TO USE IN YOUR REAL APP:")
    print("1. Add processor.start_evaluation_session(participant_id, condition)")
    print("2. Run your normal webcam loop (UNCHANGED)")
    print("3. Add processor.finalize_evaluation_session() at the end")
    print("4. All evaluation data automatically collected!")

if __name__ == "__main__":
    run_evaluation_session_example()
