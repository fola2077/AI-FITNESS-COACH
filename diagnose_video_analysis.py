#!/usr/bin/env python3
"""
Video Analysis Diagnostics - Test video processing and data logging
"""

import cv2
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

class VideoAnalysisDiagnostics:
    """Comprehensive video analysis troubleshooting"""
    
    def __init__(self):
        self.test_results = {}
        self.errors = []
        
    def run_full_diagnostics(self, video_path=None):
        """Run comprehensive video analysis diagnostics"""
        
        print("🔍 Video Analysis Diagnostics")
        print("=" * 50)
        
        # Test 1: Check imports
        self.test_imports()
        
        # Test 2: Check video file
        if video_path:
            self.test_video_file(video_path)
        
        # Test 3: Test data logger independently
        self.test_data_logger()
        
        # Test 4: Test pose detection
        self.test_pose_detection()
        
        # Test 5: Test complete pipeline
        if video_path:
            self.test_video_pipeline(video_path)
        
        # Show results
        self.show_diagnostic_results()
        
        return len(self.errors) == 0
    
    def test_imports(self):
        """Test all required imports"""
        print("\n🔧 Test 1: Checking Imports")
        print("-" * 30)
        
        imports_to_test = [
            ("cv2", "OpenCV"),
            ("mediapipe", "MediaPipe"),
            ("numpy", "NumPy"),
            ("pandas", "Pandas"),
            ("src.data.session_logger", "Session Logger"),
            ("src.pose.pose_detector", "Pose Detector"),
            ("src.grading.advanced_form_grader", "Form Analyzer"),
        ]
        
        for module, name in imports_to_test:
            try:
                if "src." in module:
                    # Test custom modules
                    exec(f"from {module} import *")
                else:
                    # Test external modules
                    __import__(module)
                print(f"   ✅ {name}: Available")
                self.test_results[f"import_{module}"] = True
            except ImportError as e:
                print(f"   ❌ {name}: Missing - {e}")
                self.errors.append(f"Import error for {name}: {e}")
                self.test_results[f"import_{module}"] = False
            except Exception as e:
                print(f"   ⚠️ {name}: Error - {e}")
                self.errors.append(f"Error importing {name}: {e}")
                self.test_results[f"import_{module}"] = False
    
    def test_video_file(self, video_path):
        """Test if video file can be opened and read"""
        print(f"\n🎥 Test 2: Video File Analysis")
        print("-" * 30)
        print(f"Video: {video_path}")
        
        if not Path(video_path).exists():
            print(f"   ❌ Video file not found: {video_path}")
            self.errors.append(f"Video file not found: {video_path}")
            return False
        
        try:
            import cv2
            
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                print(f"   ❌ Cannot open video file")
                self.errors.append("Cannot open video file")
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            print(f"   ✅ Video opened successfully")
            print(f"   📊 Properties:")
            print(f"      Resolution: {width}x{height}")
            print(f"      FPS: {fps:.2f}")
            print(f"      Frames: {frame_count:,}")
            print(f"      Duration: {duration:.1f} seconds")
            
            # Test reading first few frames
            frames_read = 0
            for i in range(5):
                ret, frame = cap.read()
                if ret:
                    frames_read += 1
                else:
                    break
            
            cap.release()
            
            print(f"   ✅ Successfully read {frames_read}/5 test frames")
            
            if frames_read == 0:
                print(f"   ❌ Could not read any frames from video")
                self.errors.append("Could not read frames from video")
                return False
            
            self.test_results["video_file"] = True
            return True
            
        except Exception as e:
            print(f"   ❌ Video test failed: {e}")
            self.errors.append(f"Video test failed: {e}")
            self.test_results["video_file"] = False
            return False
    
    def test_data_logger(self):
        """Test data logger independently"""
        print(f"\n📊 Test 3: Data Logger Test")
        print("-" * 30)
        
        try:
            from src.data.session_logger import DataLogger
            
            # Test logger creation
            logger = DataLogger()
            print(f"   ✅ DataLogger created")
            
            # Test session start
            session_id = logger.start_session("diagnostic_test_user")
            print(f"   ✅ Session started: {session_id}")
            
            # Test frame logging with minimal data
            test_biomech_data = self.create_test_biomech_data()
            
            logger.log_frame_data(test_biomech_data)
            print(f"   ✅ Frame data logged")
            
            # Test rep completion
            test_rep_data = {
                'rep_number': 1,
                'start_time': datetime.now(),
                'end_time': datetime.now(),
                'max_depth': 85.0,
                'form_score': 88.5,
                'faults': ['NONE']
            }
            
            logger.log_rep_completion(test_rep_data)
            print(f"   ✅ Rep completion logged")
            
            # Test session end
            logger.end_session()
            print(f"   ✅ Session ended")
            
            # Check if files were created
            self.check_csv_files_created()
            
            self.test_results["data_logger"] = True
            return True
            
        except Exception as e:
            print(f"   ❌ Data logger test failed: {e}")
            print(f"   📍 Error details: {traceback.format_exc()}")
            self.errors.append(f"Data logger failed: {e}")
            self.test_results["data_logger"] = False
            return False
    
    def create_test_biomech_data(self):
        """Create test biomechanical data object"""
        class TestBiomechData:
            def __init__(self):
                self.knee_angle_left = 125.0
                self.knee_angle_right = 127.0
                self.hip_angle = 145.0
                self.back_angle = 175.0
                self.ankle_angle_left = 88.0
                self.ankle_angle_right = 89.0
                self.center_of_mass_x = 0.5
                self.center_of_mass_y = 0.6
                self.movement_velocity = 25.0
                self.acceleration = 5.0
                self.jerk = 2.0
                self.knee_symmetry_ratio = 1.02
                self.ankle_symmetry_ratio = 1.01
                self.weight_distribution_ratio = 0.98
                self.postural_sway = 0.05
                self.base_of_support_width = 0.4
                self.landmark_visibility = 0.95
                self.frame_quality_score = 0.88
                self.head_position_x = 0.5
                self.head_position_y = 0.2
                self.shoulder_alignment = 175.0
                self.heel_lift_left = 0.0
                self.heel_lift_right = 0.0
                self.foot_stability_score = 0.92
                self.movement_phase = "DESCENDING"
                self.form_score = 88.5
                self.depth_percentage = 65.0
                self.safety_classification = "GOOD"
                self.faults = ["NONE"]
        
        return TestBiomechData()
    
    def check_csv_files_created(self):
        """Check if CSV files were actually created and populated"""
        print(f"   🔍 Checking CSV files...")
        
        expected_files = [
            "data/logs/sessions/session_202508.csv",
            "data/logs/reps/rep_data_202508.csv",
            "data/logs/biomechanics/biomech_202508.csv",
            "data/logs/ml_training/ml_dataset_202508.csv"
        ]
        
        for file_path in expected_files:
            full_path = project_root / file_path
            
            if full_path.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(full_path)
                    row_count = len(df)
                    
                    if row_count > 0:
                        print(f"      ✅ {full_path.name}: {row_count} rows")
                    else:
                        print(f"      ⚠️ {full_path.name}: Empty (headers only)")
                        
                except Exception as e:
                    print(f"      ❌ {full_path.name}: Error reading - {e}")
            else:
                print(f"      ❌ {full_path.name}: Not found")
    
    def test_pose_detection(self):
        """Test pose detection with a simple test"""
        print(f"\n🤖 Test 4: Pose Detection Test")
        print("-" * 30)
        
        try:
            import mediapipe as mp
            import numpy as np
            import cv2
            
            # Initialize MediaPipe
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            print(f"   ✅ MediaPipe Pose initialized")
            
            # Create a simple test image with a person-like shape
            test_image = np.zeros((480, 640, 3), dtype=np.uint8)
            test_image.fill(128)  # Gray background
            
            # Process the test image
            results = pose.process(cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB))
            
            if results.pose_landmarks:
                print(f"   ✅ Pose landmarks detected")
                landmark_count = len(results.pose_landmarks.landmark)
                print(f"   📊 Landmarks found: {landmark_count}")
            else:
                print(f"   ⚠️ No pose landmarks detected (expected for empty test image)")
            
            pose.close()
            
            self.test_results["pose_detection"] = True
            return True
            
        except Exception as e:
            print(f"   ❌ Pose detection test failed: {e}")
            self.errors.append(f"Pose detection failed: {e}")
            self.test_results["pose_detection"] = False
            return False
    
    def test_video_pipeline(self, video_path):
        """Test complete video analysis pipeline"""
        print(f"\n🔄 Test 5: Complete Video Pipeline")
        print("-" * 30)
        
        try:
            # This would be your actual video analysis code
            self.run_minimal_video_analysis(video_path)
            
            self.test_results["video_pipeline"] = True
            return True
            
        except Exception as e:
            print(f"   ❌ Video pipeline test failed: {e}")
            print(f"   📍 Error details: {traceback.format_exc()}")
            self.errors.append(f"Video pipeline failed: {e}")
            self.test_results["video_pipeline"] = False
            return False
    
    def run_minimal_video_analysis(self, video_path):
        """Run minimal video analysis to test the pipeline"""
        import cv2
        import mediapipe as mp
        from src.data.session_logger import DataLogger
        
        print(f"   🎥 Starting minimal video analysis...")
        
        # Initialize components
        logger = DataLogger()
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Start session
        session_id = logger.start_session("video_test_user")
        print(f"   📊 Session started: {session_id}")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        frames_processed = 0
        frames_with_pose = 0
        max_frames = 30  # Limit for testing
        
        while frames_processed < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            frames_processed += 1
            
            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            
            if results.pose_landmarks:
                frames_with_pose += 1
                
                # Create biomech data (simplified)
                biomech_data = self.create_test_biomech_data()
                
                # Log frame data
                logger.log_frame_data(biomech_data)
                
                if frames_processed % 10 == 0:
                    print(f"   🔄 Processed {frames_processed} frames, {frames_with_pose} with pose")
        
        # End session
        logger.end_session()
        
        cap.release()
        pose.close()
        
        print(f"   ✅ Pipeline test completed")
        print(f"   📊 Results: {frames_processed} frames processed, {frames_with_pose} with pose data")
        
        # Check results
        self.check_csv_files_created()
    
    def show_diagnostic_results(self):
        """Show comprehensive diagnostic results"""
        print(f"\n" + "=" * 50)
        print(f"🎯 DIAGNOSTIC RESULTS SUMMARY")
        print(f"=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        print(f"📊 Tests: {passed_tests}/{total_tests} passed")
        
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        if self.errors:
            print(f"\n❌ ERRORS FOUND:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"The video analysis system should be working correctly.")
        else:
            print(f"\n⚠️ ISSUES DETECTED")
            print(f"Please fix the errors above before proceeding.")
        
        # Specific recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        
        if not self.test_results.get("data_logger", True):
            print(f"   1. Fix data logger issues first")
            print(f"   2. Check CSV file permissions")
            print(f"   3. Verify directory structure exists")
        
        if not self.test_results.get("pose_detection", True):
            print(f"   1. Reinstall MediaPipe: pip install --upgrade mediapipe")
            print(f"   2. Check camera/video compatibility")
        
        if not self.test_results.get("video_file", True):
            print(f"   1. Verify video file format (MP4, AVI, MOV)")
            print(f"   2. Check video file corruption")
            print(f"   3. Try a different video file")

def main():
    """Main diagnostic function"""
    print("Starting Video Analysis Diagnostics...")
    
    # Check if video path provided
    video_path = None
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        if not Path(video_path).exists():
            print(f"❌ Video file not found: {video_path}")
            video_path = None
    else:
        print("ℹ️ No video file provided - will run basic diagnostics only")
        print("Usage: python diagnose_video_analysis.py <video_path>")
    
    try:
        diagnostics = VideoAnalysisDiagnostics()
        success = diagnostics.run_full_diagnostics(video_path)
        
        if success:
            print(f"\n🎉 Diagnostics completed successfully!")
            if video_path:
                print(f"Video analysis should work with your file: {video_path}")
        else:
            print(f"\n❌ Issues found - please fix errors above")
            
    except KeyboardInterrupt:
        print(f"\n\nDiagnostics cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error during diagnostics: {e}")
        print(f"Traceback: {traceback.format_exc()}")
    
    input(f"\nPress Enter to exit...")

if __name__ == "__main__":
    main()
