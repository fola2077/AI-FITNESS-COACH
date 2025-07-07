#!/usr/bin/env python3
"""
Test script to verify the main window functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        from src.gui.main_window import MainWindow
        print("✅ MainWindow imported successfully")
        
        from src.processing.pose_processor import PoseProcessor
        print("✅ PoseProcessor imported successfully")
        
        from src.feedback.feedback_manager import FeedbackManager
        print("✅ FeedbackManager imported successfully")
        
        from src.capture.camera import CameraManager
        print("✅ CameraManager imported successfully")
        
        from src.config.config_manager import ConfigManager
        print("✅ ConfigManager imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_main_window_creation():
    """Test MainWindow creation without showing it"""
    print("\nTesting MainWindow creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create MainWindow
        window = MainWindow()
        print("✅ MainWindow created successfully")
        
        # Test basic attributes
        assert hasattr(window, 'pose_processor'), "Missing pose_processor"
        assert hasattr(window, 'feedback_manager'), "Missing feedback_manager"
        assert hasattr(window, 'session_manager'), "Missing session_manager"
        assert hasattr(window, 'config_manager'), "Missing config_manager"
        print("✅ All required attributes present")
        
        # Test UI elements
        assert hasattr(window, 'video_label'), "Missing video_label"
        assert hasattr(window, 'rep_label'), "Missing rep_label"
        assert hasattr(window, 'form_score_label'), "Missing form_score_label"
        assert hasattr(window, 'feedback_display'), "Missing feedback_display"
        print("✅ All UI elements present")
        
        return True
        
    except Exception as e:
        print(f"❌ MainWindow creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pose_processor_integration():
    """Test pose processor integration"""
    print("\nTesting PoseProcessor integration...")
    
    try:
        from src.processing.pose_processor import PoseProcessor
        import numpy as np
        
        processor = PoseProcessor()
        
        # Test with dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = processor.process_frame(dummy_frame)
        
        print("✅ PoseProcessor can process frames")
        
        # Test settings update
        if hasattr(processor, 'update_settings'):
            test_settings = {
                'confidence_threshold': 0.8,
                'show_skeleton': True,
                'feedback_frequency': 'Medium'
            }
            processor.update_settings(test_settings)
            print("✅ PoseProcessor settings update works")
        
        return True
        
    except Exception as e:
        print(f"❌ PoseProcessor integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 AI Fitness Coach - Component Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_main_window_creation,
        test_pose_processor_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Application should work correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
