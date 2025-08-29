#!/usr/bin/env python3
"""
GUI Voice Feedback Demo
Launch the actual GUI with enhanced voice feedback for testing
"""

import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def launch_gui_with_voice_demo():
    """Launch the GUI and demonstrate voice feedback features"""
    
    print("🎙️ GUI VOICE FEEDBACK DEMO")
    print("=" * 40)
    print("This will launch the actual AI Fitness Coach GUI")
    print("with enhanced voice feedback enabled!")
    print()
    print("🔊 VOICE FEATURES TO TEST:")
    print("1. Click the '🔊 Voice: ON/OFF' button to toggle voice")
    print("2. Start a webcam or load a video")
    print("3. Perform squats to hear real-time voice coaching")
    print("4. Watch the feedback status indicators")
    print("5. Listen for different voice styles based on your form")
    print()
    print("Make sure your speakers/headphones are on! 🔊")
    print()
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        print("✅ Starting AI Fitness Coach GUI with voice feedback...")
        
        # Create application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        print("✅ GUI launched successfully!")
        print("\n🎯 TESTING INSTRUCTIONS:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("1. VOICE TOGGLE TEST:")
        print("   - Click the '🔊 Voice: ON' button")
        print("   - It should change to '🔇 Voice: OFF'")
        print("   - Click again to turn it back on")
        print()
        print("2. WEBCAM TEST:")
        print("   - Click 'Start Webcam'")
        print("   - Perform squats in front of the camera")
        print("   - Listen for voice coaching messages")
        print()
        print("3. VIDEO TEST:")
        print("   - Click 'Load Video'")
        print("   - Select one of the squat videos:")
        print("     * 0918_squat_000064.mp4")
        print("     * 0922_squat_000003.mp4") 
        print("     * 1108_squat_000144.mp4")
        print("   - Listen for voice analysis")
        print()
        print("4. WATCH FOR:")
        print("   - Voice status: '🔊 Voice: Active' when speaking")
        print("   - Message stats: 'Messages: X | Voice: Y'")
        print("   - Status bar updates with feedback categories")
        print()
        print("Press Ctrl+C or close the window to exit")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Run the application
        app.exec()
        
        print("\n✅ GUI demo completed!")
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ GUI Demo Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Make sure your speakers/headphones are on!")
    print("This will launch the full GUI application.")
    print("Press Enter when ready...")
    input()
    
    success = launch_gui_with_voice_demo()
    
    print(f"\n{'='*40}")
    if success:
        print("🎉 GUI voice demo completed!")
    else:
        print("❌ GUI voice demo failed.")
    
    sys.exit(0 if success else 1)
