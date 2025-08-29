import sys
import os
import subprocess
from pathlib import Path

def is_interactive() -> bool:
    """
    Determine if the process is attached to an interactive TTY (safe to prompt).
    """
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except Exception:
        return False

def check_dependencies():
    """
    Check if all required dependencies are installed and provide helpful guidance.
    """
    required_packages = {
        'PySide6': 'pip install PySide6',
        'cv2': 'pip install opencv-python',
        'mediapipe': 'pip install mediapipe',
        'numpy': 'pip install numpy',
        'pyttsx3': 'pip install pyttsx3'
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
        
        # Ask user if they want to auto-install (only when interactive)
        if not is_interactive():
            print("\nℹ️ Non-interactive environment detected; skipping auto-install prompt.")
            return False
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
        project_root / "src" / "feedback",
        project_root / "src" / "grading",
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

def validate_enhanced_form_grader():
    """Validate enhanced form grader with all new analyzers"""
    try:
        from src.grading.advanced_form_grader import (
            IntelligentFormGrader, 
            ThresholdConfig,
            BiomechanicalMetrics,
            FaultType
        )
        
        print("🧪 Testing Enhanced Form Grader...")
        
        # Test form grader initialization
        config = ThresholdConfig.emergency_calibrated()
        grader = IntelligentFormGrader(difficulty="casual", config=config)
        
        print("✅ Enhanced Form Grader initialized with new analyzers:")
        for analyzer_name in grader.analyzers.keys():
            print(f"   • {analyzer_name.title()}Analyzer")
        
        # Test with synthetic data that should trigger various faults
        test_metrics = [
            # Frame 1: Bad shallow depth
            BiomechanicalMetrics(
                knee_angle_left=140,  # Very shallow
                knee_angle_right=138,
                back_angle=70,        # Bad back rounding
                landmark_visibility=0.9
            ),
            # Frame 2: Better depth but still issues
            BiomechanicalMetrics(
                knee_angle_left=110,
                knee_angle_right=108,
                back_angle=85,
                landmark_visibility=0.9
            ),
            # Frame 3: Good depth
            BiomechanicalMetrics(
                knee_angle_left=85,   # Good depth
                knee_angle_right=87,
                back_angle=95,        # Good back angle
                landmark_visibility=0.9
            )
        ]
        
        result = grader.grade_repetition(test_metrics)
        
        print(f"✅ Enhanced form grader test passed:")
        print(f"   Overall Score: {result['score']:.1f}%")
        print(f"   Components Analyzed: {len(result.get('component_scores', {}))}")
        print(f"   Faults Detected: {len(result.get('faults', []))}")
        print(f"   Key Issues: {len(result.get('key_issues', []))}")
        
        # Test fault detection
        detected_faults = result.get('faults', [])
        if any('shallow' in fault.lower() for fault in detected_faults):
            print("✅ Shallow depth detection working")
        
        if any('back' in fault.lower() for fault in detected_faults):
            print("✅ Back rounding detection working")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced form grader validation failed: {e}")
        import traceback
        traceback.print_exc()
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
            if is_interactive():
                input("Press Enter to exit...")
            return 1

        # Check dependencies
        if not check_dependencies():
            print("❌ Dependency check failed. Please install required packages.")
            if is_interactive():
                input("Press Enter to exit...")
            return 1

        # Optionally validate enhanced form grader (can slow startup)
        should_validate = os.getenv("AIFC_VALIDATE_GRADER", "1") == "1"
        if should_validate:
            if not validate_enhanced_form_grader():
                print("⚠️ Enhanced form grader validation failed, but continuing anyway...")
        else:
            print("ℹ️ Skipping grader self-test (set AIFC_VALIDATE_GRADER=1 to enable).")

        # Import Qt after dependency check
        from PySide6.QtWidgets import QApplication
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
        if is_interactive():
            input("Press Enter to exit...")
        return 1

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("Please check your installation and try again.")
        print("If the problem persists, please report this issue.")
        if is_interactive():
            input("Press Enter to exit...")
        return 1

if __name__ == '__main__':
    exit_code = run_application()
    sys.exit(exit_code)