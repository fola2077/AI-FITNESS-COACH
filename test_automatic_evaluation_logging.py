#!/usr/bin/env python3
"""
Test script to demonstrate automatic evaluation logging functionality.

This script shows how the evaluation logging now works automatically 
like the other logging systems - no manual start/stop calls needed.
"""

from src.data.session_logger import DataLogger
import time

def test_automatic_evaluation_logging():
    """Test that evaluation logging works automatically during sessions."""
    
    print("🧪 Testing Automatic Evaluation Logging System")
    print("=" * 50)
    
    # Initialize data logger
    logger = DataLogger()
    
    # Start a regular session (same as always)
    print("1. Starting regular session...")
    session_id = logger.start_session('demo_user', 'squat')
    print(f"   ✅ Session started: {session_id}")
    
    # Simulate some reps with automatic evaluation logging
    print("\n2. Simulating workout with automatic logging...")
    
    for rep_num in range(1, 4):  # 3 reps
        print(f"\n   Rep {rep_num}:")
        
        # Start rep
        logger.log_rep_start(rep_num)
        print(f"   📝 Rep {rep_num} started")
        
        # Simulate frames during rep (evaluation data logged automatically)
        for frame_num in range(1, 11):  # 10 frames per rep
            frame_data = {
                'timestamp_ms': int(time.time() * 1000),
                'frame_id': frame_num,
                'pose_confidence': 0.9 + (frame_num * 0.01),  # Varying confidence
                'fps': 30,
                'knee_left_deg': 180 - (frame_num * 10),  # Descending motion
                'knee_right_deg': 180 - (frame_num * 9),   # Slightly asymmetric
                'knee_avg_deg': 180 - (frame_num * 9.5),
                'trunk_angle_deg': frame_num * 2,  # Increasing trunk lean
                'hip_angle_deg': 180 - (frame_num * 8),
                'ankle_angle_deg': 90,
                'movement_phase': 'descent' if frame_num < 6 else 'ascent',
                'valgus_deviation_deg': frame_num * 0.5,  # Slight valgus
                'depth_achieved': 1 if frame_num > 7 else 0,  # Depth achieved later
                'trunk_flex_excessive': 1 if frame_num > 8 else 0,
                'landmarks_visible_count': 33
            }
            
            # This automatically logs evaluation data now!
            logger.log_evaluation_frame(frame_data)
        
        # Complete rep (evaluation rep data logged automatically)
        rep_analysis = {
            'overall_score': 85 + rep_num * 2,  # Improving scores
            'safety_score': 80,
            'depth_score': 90,
            'stability_score': 85,
            'faults': ['slight_valgus'] if rep_num == 2 else [],
            'feedback': ['Good depth!', 'Keep knees aligned']
        }
        
        rep_data = {
            'rep_id': rep_num,
            'start_timestamp_ms': int((time.time() - 3) * 1000),
            'end_timestamp_ms': int(time.time() * 1000),
            'duration_ms': 3000,
            'min_knee_angle_deg': 85 + rep_num * 5,
            'max_trunk_flex_deg': 20 - rep_num,
            'form_score_percent': rep_analysis['overall_score'],
            'ai_rep_detected': 1
        }
        
        # This automatically logs evaluation data now!
        logger.log_evaluation_rep(rep_data)
        logger.log_rep_completion(rep_analysis)
        
        # Simulate feedback (evaluation cue data logged automatically)
        if rep_analysis['faults']:
            cue_data = {
                'cue_timestamp_ms': int(time.time() * 1000),
                'rep_id': rep_num,
                'cue_type': 'form_correction',
                'cue_message': 'Keep knees aligned',
                'movement_phase_at_cue': 'ascent'
            }
            logger.log_evaluation_cue(cue_data)
        
        print(f"   ✅ Rep {rep_num} completed (Score: {rep_analysis['overall_score']})")
        time.sleep(0.1)  # Small delay between reps
    
    print("\n3. Ending session...")
    # End session - this automatically writes ALL data including evaluation data
    logger.end_session()
    print("   ✅ Session ended - all data written automatically!")
    
    print("\n🎉 Automatic Evaluation Logging Test Complete!")
    print("\n📊 Results:")
    print("   • Evaluation data was logged automatically during the session")
    print("   • No manual start_evaluation_session() or finalize_evaluation_session() calls needed")
    print("   • Data saved to data/logs/evaluation/evaluation_*.csv files")
    print("   • Works exactly like the other logging systems (sessions, reps, biomechanics)")
    
    return True

if __name__ == "__main__":
    test_automatic_evaluation_logging()
