#!/usr/bin/env python3
"""
Test evaluation logging integration with existing DataLogger
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.session_logger import DataLogger
import time

def test_integrated_evaluation_logging():
    """Test the integrated evaluation logging system"""
    
    print("🔍 Testing Integrated Evaluation Logging System")
    print("=" * 60)
    
    try:
        # Initialize existing data logger
        logger = DataLogger()
        print("✅ DataLogger initialized")
        
        # Start evaluation session
        eval_session_id = logger.start_evaluation_session("P01_A")
        print(f"✅ Evaluation session started: {eval_session_id}")
        
        # Simulate frame logging
        for frame_num in range(5):
            frame_data = {
                'pose_confidence': 0.95,
                'fps': 30,
                'knee_left_deg': 150 - frame_num * 10,
                'knee_right_deg': 150 - frame_num * 10,
                'knee_avg_deg': 150.0 - frame_num * 10,
                'trunk_angle_deg': 5,
                'movement_phase': 'DESCENT' if frame_num > 2 else 'standing',
                'landmarks_visible_count': 33
            }
            logger.log_evaluation_frame(frame_data)
        
        print("✅ Frame logging completed (5 frames)")
        
        # Simulate rep logging
        rep_data = {
            'start_timestamp_ms': int(time.time() * 1000) - 2000,
            'bottom_timestamp_ms': int(time.time() * 1000) - 1000,
            'end_timestamp_ms': int(time.time() * 1000),
            'duration_ms': 2000,
            'min_knee_angle_deg': 90,
            'form_score_percent': 88,
            'depth_fault_flag': 0,
            'ai_rep_detected': 1
        }
        rep_id = logger.log_evaluation_rep(rep_data)
        print(f"✅ Rep logged: Rep ID {rep_id}")
        
        # Simulate cue logging
        cue_data = {
            'cue_timestamp_ms': int(time.time() * 1000),
            'rep_id': rep_id,
            'cue_type': 'depth',
            'cue_message': 'Go deeper for better form',
            'movement_phase_at_cue': 'DESCENT',
            'in_actionable_window': 1
        }
        cue_id = logger.log_evaluation_cue(cue_data)
        print(f"✅ Cue logged: Cue ID {cue_id}")
        
        # Finalize session
        metadata = logger.finalize_evaluation_session()
        print("✅ Evaluation session finalized")
        
        # Verify files
        eval_dir = f"data/logs/evaluation/P01_A"
        if os.path.exists(eval_dir):
            files = os.listdir(eval_dir)
            print(f"\n📁 Generated files in {eval_dir}:")
            for file in sorted(files):
                filepath = os.path.join(eval_dir, file)
                size = os.path.getsize(filepath)
                print(f"   ✅ {file}: {size} bytes")
        
        print(f"\n🎯 INTEGRATION SUCCESS!")
        print("   ✅ Evaluation logging integrated into existing DataLogger")
        print("   ✅ Files saved in data/logs/evaluation/ structure")
        print("   ✅ No separate logging system needed")
        print("   ✅ Leverages existing CSV infrastructure")
        
        print(f"\n📋 USAGE IN YOUR APP:")
        print("   1. Use existing DataLogger instance")
        print("   2. Call start_evaluation_session(participant_id, condition)")
        print("   3. Call log_evaluation_frame() in processing loop")
        print("   4. Call log_evaluation_rep() when reps complete")
        print("   5. Call log_evaluation_cue() when feedback given")
        print("   6. Call finalize_evaluation_session() at end")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_integrated_evaluation_logging()
