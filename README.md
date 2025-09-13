# AI Fitness Coach

A real-time AI-powered fitness coaching application that provides intelligent form correction and biomechanical analysis for squat exercises using computer vision and pose estimation.

## 🎯 Overview

The AI Fitness Coach is a sophisticated biomechanical analysis system that uses MediaPipe pose detection to provide real-time feedback on exercise form. The application analyzes movement patterns, detects form faults, and provides personalized coaching feedback to help users improve their squat technique while preventing injuries.

## ✨ Key Features

### 🔍 **Advanced Pose Analysis**
- Real-time pose detection using Google's MediaPipe
- 42+ engineered biomechanical features
- 9 specialized movement analyzers (depth, symmetry, stability, tempo, etc.)
- Anthropometric normalization for individual body types

### 🎯 **Intelligent Form Grading**
- Progressive difficulty adaptation based on user skill level
- Movement quality metrics (smoothness, efficiency, coordination)
- Contextual fault analysis with graduated penalties
- Predictive fatigue and injury risk assessment

### 🗣️ **Enhanced Feedback System**
- Voice feedback with PowerShell TTS integration
- Anti-repetition intelligent messaging
- Priority-based feedback delivery
- Contextual coaching based on movement phase

### 📊 **Comprehensive Data Logging**
- Session tracking and progress reports
- CSV data export across 4 output formats
- Biomechanical metrics logging
- ML training data generation

### 🖥️ **Modern User Interface**
- Clean, intuitive GUI built with PySide6
- Real-time performance metrics display
- Live depth rating and form scoring
- Session reports and progress tracking

## 🛠️ Technical Stack

- **Python 3.12+** - Core application language
- **MediaPipe** - Pose detection and landmark extraction
- **PySide6** - Modern GUI framework
- **OpenCV** - Computer vision and image processing
- **NumPy** - Numerical computations and biomechanical analysis
- **pyttsx3** - Text-to-speech for voice feedback

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux Ubuntu 18.04+
- **Python**: 3.12 or higher
- **Webcam**: USB camera or built-in webcam (720p+ recommended)
- **Lighting**: Good ambient lighting for pose detection
- **Space**: 6-8 feet distance from camera with full body visibility

### Hardware Recommendations
- **Processor**: Intel i5 or AMD equivalent (2.5GHz+)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Graphics**: Integrated graphics sufficient, dedicated GPU preferred for better performance
- **Storage**: 1GB free space for application and data logging

## 🚀 Installation

### Method 1: Quick Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/fola2077/AI-FITNESS-COACH.git
   cd AI-FITNESS-COACH
   ```

2. **Run the application**
   ```bash
   python run_app.py
   ```
   
   The application will automatically:
   - Check for missing dependencies
   - Offer to install required packages
   - Set up the environment
   - Launch the GUI interface

### Method 2: Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fola2077/AI-FITNESS-COACH.git
   cd AI-FITNESS-COACH
   ```

2. **Create virtual environment (optional but recommended)**
   ```bash
   python -m venv ai_fitness_env
   
   # On Windows
   ai_fitness_env\Scripts\activate
   
   # On macOS/Linux
   source ai_fitness_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application**
   ```bash
   python run_app.py
   ```

### Dependencies
The application requires the following packages:
- `PySide6>=6.7` - GUI framework
- `opencv-python-headless>=4.10` - Computer vision
- `mediapipe>=0.10.0` - Pose detection
- `numpy>=1.21.0` - Numerical computations
- `pyttsx3>=2.90` - Text-to-speech

## 📖 User Guide

### Getting Started

1. **Launch the Application**
   ```bash
   python run_app.py
   ```

2. **Setup Checklist**
   Before starting your workout, ensure:
   - ✅ Camera/webcam is connected and working
   - ✅ Good lighting in workout area
   - ✅ 6-8 feet distance from camera
   - ✅ Full body visible in frame
   - ✅ Stable internet connection (for initial setup)

3. **Camera Setup**
   - Position camera at chest height
   - Ensure your entire body is visible in the frame
   - Test camera view before starting exercise

### Basic Usage

#### 1. **Starting a Session**
- Click "Start Session" to begin pose detection
- Enter your user ID when prompted
- Select your skill level (Beginner/Intermediate/Advanced)
- Choose difficulty setting (Casual/Standard/Strict/Competition)

#### 2. **Performing Squats**
- Stand in the camera view with feet shoulder-width apart
- Begin squatting when the system detects your pose
- Follow the real-time feedback displayed on screen
- Listen to voice coaching cues (if enabled)

#### 3. **Understanding Feedback**

**Visual Indicators:**
- **Green**: Good form
- **Yellow**: Minor form issues
- **Red**: Major form faults requiring immediate attention

**Common Feedback Messages:**
- *"Squat deeper - hip below knee"* - Insufficient depth
- *"Push knees out over toes"* - Knee valgus (inward collapse)
- *"Keep chest up! Protect your spine"* - Back rounding
- *"Keep heels on the ground"* - Heel rise during movement

#### 4. **Session Management**
- View real-time metrics: rep count, form score, depth rating
- Monitor session progress in the performance panel
- Review detailed session reports after completion

### Advanced Features

#### **Difficulty Levels**
- **Casual**: Relaxed thresholds, encouraging feedback
- **Standard**: Balanced analysis for general fitness
- **Strict**: Precise form requirements for experienced users
- **Competition**: Elite-level standards for competitive athletes

#### **User Profiles**
- **Beginner**: Basic form focus with safety emphasis
- **Intermediate**: Balanced technique and performance
- **Advanced**: Complex biomechanical analysis

#### **Voice Feedback**
- Toggle voice coaching on/off via settings
- Contextual audio cues based on movement phase
- Priority-based message delivery (safety > form > encouragement)

#### **Data Export**
Access your training data:
- Session summaries in `data/logs/`
- Detailed biomechanical data in CSV format
- Progress tracking reports
- ML training datasets for research

### Troubleshooting

#### **Camera Issues**
```
Problem: Camera not detected
Solution: 
1. Check camera connections
2. Close other applications using camera
3. Restart the application
4. Update camera drivers
```

#### **Pose Detection Issues**
```
Problem: Pose not detected consistently
Solution:
1. Improve lighting conditions
2. Ensure full body visibility
3. Move to recommended 6-8 feet distance
4. Wear contrasting clothing
5. Check camera resolution settings
```

#### **Performance Issues**
```
Problem: Application running slowly
Solution:
1. Close unnecessary applications
2. Lower camera resolution if possible
3. Ensure adequate system resources
4. Update graphics drivers
```

#### **Installation Issues**
```
Problem: Dependencies not installing
Solution:
1. Update pip: pip install --upgrade pip
2. Try manual installation of each package
3. Check Python version compatibility
4. Use virtual environment
5. Check internet connection
```

## 🏗️ Architecture

### System Components

```
AI Fitness Coach
├── Capture Layer          # Video input and frame processing
├── Pose Estimation        # MediaPipe pose detection
├── Processing Engine      # Movement analysis and state management
├── Form Analysis          # 9 specialized analyzers
├── Feedback System        # Intelligent coaching messages
├── Data Logger           # CSV export and session tracking
└── GUI Interface         # PySide6 user interface
```

### Data Flow
1. **Video Capture** → Raw frames from webcam
2. **Pose Detection** → Extract body landmarks
3. **Biomechanical Analysis** → Calculate joint angles and metrics
4. **Form Grading** → Analyze movement quality
5. **Feedback Generation** → Create coaching messages
6. **Data Logging** → Export session data
7. **GUI Update** → Display results to user

## 📊 Data Output

The application generates comprehensive data in multiple formats:

### Session Reports (`data/logs/`)
```
Session ID: session_20250909_154629_user
Duration: 106.4 seconds
Total Reps: 11
Average Score: 81.1/100
Best Score: 94.0/100
Improvement: +7.3 points
```

### Biomechanical Data (CSV)
- Joint angles (knees, hips, ankles)
- Center of mass tracking
- Movement velocity and acceleration
- Symmetry ratios
- Stability metrics

### ML Training Data
- 42+ engineered features
- Movement phase classifications
- Binary fault labels
- Sequence and context features

## 🧪 Development & Testing

### Running Tests
```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run all tests with coverage
python -m pytest --cov=src tests/
```

### Development Mode
```bash
# Enable enhanced grader validation
set AIFC_VALIDATE_GRADER=1

# Run with debug logging
python run_app.py --debug
```

### Code Structure
```
src/
├── capture/          # Video capture and camera management
├── config/           # Configuration management
├── data/             # Data logging and session management
├── feedback/         # Feedback generation and voice systems
├── grading/          # Form analysis and biomechanical graders
├── gui/              # PySide6 interface components
├── ml/               # Machine learning utilities
├── pose/             # Pose detection and landmark processing
├── processing/       # Core movement analysis engine
├── session/          # Session management and tracking
├── utils/            # Utility functions and helpers
└── validation/       # Testing and validation tools
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** with proper documentation
4. **Add tests** for new functionality
5. **Run the test suite**: `python -m pytest`
6. **Submit a pull request**

### Code Standards
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Write unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support & Contact

### Getting Help
- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check the `docs/` folder for detailed guides
- **Email**: Contact the development team for research collaboration

### Research Citations
If you use this software in academic research, please cite:
```bibtex
@software{ai_fitness_coach_2025,
  title={AI Fitness Coach: Real-time Biomechanical Analysis for Exercise Form Correction},
  author={AI Fitness Coach Development Team},
  year={2025},
  url={https://github.com/fola2077/AI-FITNESS-COACH}
}
```

## 🚧 Future Development

### Planned Features
- [ ] Additional exercise types (deadlift, bench press)
- [ ] Machine learning model integration
- [ ] Mobile application development
- [ ] Cloud-based progress tracking
- [ ] Multi-user support and coaching dashboard
- [ ] Advanced biomechanical visualizations
- [ ] Integration with wearable devices

### Research Applications
- Exercise physiology studies
- Movement quality assessment
- Rehabilitation monitoring
- Sports performance analysis
- Machine learning model training

---

**Built with ❤️ for fitness enthusiasts and researchers**

*This application is designed for educational and research purposes. Always consult with qualified fitness professionals for personalized exercise guidance and injury prevention.*
