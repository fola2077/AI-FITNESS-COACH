import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """
    Check if all required dependencies are installed and provide helpful guidance.
    """
    required_packages = {
        'PySide6': 'pip install PySide6',
        'cv2': 'pip install opencv-python',
        'mediapipe': 'pip install mediapipe',
        'numpy': 'pip install numpy'
    }
    
    missing_packages = []
    
    for package, install_cmd in required_packages.items():
        try:
            if package == 'cv2':
                import cv2
            else:
                __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append((package, install_cmd))
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print("\n🔧 Missing Dependencies Detected!")
        print("Please install the following packages:")
        print("-" * 50)
        for package, cmd in missing_packages:
            print(f"  {cmd}")
        
        print("\nOr install all at once:")
        print("  pip install -r requirements.txt")
        
        # Ask user if they want to auto-install
        try:
            response = input("\nWould you like to auto-install missing packages? (y/n): ").lower()
            if response in ['y', 'yes']:
                print("\n🚀 Installing packages...")
                try:
                    # Install from requirements.txt if it exists
                    if Path("requirements.txt").exists():
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                    else:
                        # Install individual packages
                        for package, cmd in missing_packages:
                            package_name = cmd.split()[-1]  # Extract package name from command
                            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                    
                    print("✅ Installation completed! Please restart the application.")
                    return False
                except subprocess.CalledProcessError as e:
                    print(f"❌ Installation failed: {e}")
                    print("Please install manually using the commands above.")
                    return False
            else:
                print("Please install the required packages manually and restart the application.")
                return False
        except KeyboardInterrupt:
            print("\nInstallation cancelled.")
            return False
    
    return True

def setup_environment():
    """
    Setup the Python environment and paths.
    """
    # Add the project's root directory to the Python path
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Verify critical directories exist
    critical_dirs = [
        project_root / "src",
        project_root / "src" / "gui",
        project_root / "src" / "processing",
        project_root / "src" / "feedback"
    ]
    
    for dir_path in critical_dirs:
        if not dir_path.exists():
            print(f"❌ Critical directory missing: {dir_path}")
            print("Please ensure you have the complete project structure.")
            return False
    
    return True

def print_startup_info():
    """
    Print helpful startup information.
    """
    print("AI Fitness Coach - Form Analyzer")
    print("=" * 50)
    print("📋 Startup Checklist:")
    print("  • Camera/webcam connected and working")
    print("  • Good lighting in workout area")
    print("  • 6-8 feet distance from camera")
    print("  • Full body visible in frame")
    print("\n🎯 Features:")
    print("  • Real-time pose analysis")
    print("  • Form feedback and coaching")
    print("  • Session tracking and reports")
    print("  • Customizable analysis settings")
    print("\n🚀 Starting application...")
    print("-" * 50)

def validate_form_grader():
    """Validate form grader configuration on startup."""
    try:
        from src.grading.advanced_form_grader import (
            IntelligentFormGrader, 
            ThresholdConfig,
            BiomechanicalMetrics
        )
        
        # Test form grader initialization
        config = ThresholdConfig.emergency_calibrated()
        grader = IntelligentFormGrader(difficulty="casual", config=config)
        
        print("✅ Advanced Form Grader initialized successfully")
        
        # Test with dummy data
        test_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=90,
                knee_angle_right=92,
                back_angle=110,
                landmark_visibility=0.9
            )
        ]
        
        result = grader.grade_repetition(test_metrics)
        print(f"✅ Form grader test passed - Score: {result['score']}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Form grader validation failed: {e}")
        return False

def run_application():
    """
    Main application entry point with comprehensive error handling.
    """
    try:
        print_startup_info()
        
        # Check environment setup
        if not setup_environment():
            print("❌ Environment setup failed. Please check your installation.")
            input("Press Enter to exit...")
            return 1
        
        # Check dependencies
        if not check_dependencies():
            print("❌ Dependency check failed. Please install required packages.")
            input("Press Enter to exit...")
            return 1
        
        # NEW: Validate form grader
        if not validate_form_grader():
            print("⚠️ Form grader validation failed, but continuing anyway...")
        
        # Import Qt after dependency check
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # Import MainWindow after the path has been adjusted
        from src.gui.main_window import MainWindow
        
        print("✅ All checks passed! Launching GUI...")
        
        # Create and configure Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("AI Fitness Coach")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("AI Fitness Coach")
        
        # Set application icon if available
        icon_path = Path(__file__).parent / "resources" / "icon.png"
        if icon_path.exists():
            from PySide6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        print("🎉 Application launched successfully!")
        print("💡 Check the Help menu for usage instructions.")
        
        # Run the application
        return app.exec()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("This usually means a required package is not installed.")
        print("Please run the dependency check again or install packages manually.")
        input("Press Enter to exit...")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("Please check your installation and try again.")
        print("If the problem persists, please report this issue.")
        input("Press Enter to exit...")
        return 1

if __name__ == '__main__':
    exit_code = run_application()
    sys.exit(exit_code)