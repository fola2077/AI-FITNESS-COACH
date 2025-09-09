# AI Fitness Coach: A Deep Dive into the Codebase

## For Chapters 3 & 4 of a Computer Science Dissertation

---

### **Chapter 3: System Design & Architecture**

#### **3.1 High-Level Architecture**

The AI Fitness Coach is a real-time, modular, and extensible system designed for the biomechanical analysis of human movement, specifically the squat exercise. The architecture follows a classic **pipeline pattern**, where data flows sequentially through distinct, decoupled processing stages. This design promotes a strong separation of concerns, enhances testability, and ensures the system is maintainable and extensible.

The primary architectural layers are:

1.  **Capture Layer**: Responsible for acquiring raw video frames from a camera source.
2.  **Pose Estimation Layer**: Detects and extracts human pose landmarks from the video frames.
3.  **Processing & State Management Layer**: Orchestrates the flow of data, manages the application's state (e.g., repetition counting), and integrates all other components.
4.  **Grading & Analysis Layer**: The intellectual core of the system, containing the biomechanical rules engine, modular form analyzers, and adaptive difficulty logic.
5.  **Feedback Layer**: Delivers real-time, contextual auditory and visual feedback to the user.
6.  **Data & Persistence Layer**: Manages session state, user profiles, and the structured logging of data for performance tracking and future machine learning applications.
7.  **Presentation Layer (GUI)**: Renders the user interface, visualizes complex data in a comprehensible manner, and captures user input.

#### **3.2 Architectural Diagram**

*(This description can be used to generate a formal diagram for your dissertation.)*

```
+-------------------+      +---------------------+      +------------------------+
|  Capture Layer    |----->| Pose Estimation     |----->| Processing & State     |
| (video_capture.py)|      | (pose_detector.py)  |      | (pose_processor.py)    |
+-------------------+      +----------+----------+      +-----------+------------+
                                      |                         |
                                      | (Landmarks)             | (Repetition Metrics)
                                      v                         v
+-------------------+      +----------+----------+      +-----------+------------+
|  Feedback Layer   |<-----| Grading & Analysis  |<-----| Data & Persistence     |
| (feedback_manager)|      | (form_grader.py)    |      | (session_logger.py)    |
+-------------------+      +---------------------+      +------------------------+
        ^                                                         ^
        | (UI Updates, Feedback Cues)                             | (Session Data)
        |                                                         |
        +---------------------------------------------------------+
        |
        v
+-------------------+
| Presentation (GUI)|
| (main_window.py)  |
+-------------------+
```

#### **3.3 Data Flow Model**

The system's data flow is unidirectional and cyclical, processing one video frame at a time in a continuous loop:

1.  **Frame Capture**: The `VideoCaptureThread` in `src/capture` acquires a frame from the webcam to prevent blocking the main GUI thread. It emits the frame as a `QImage`.
2.  **Pose Detection**: The frame is passed to the `PoseDetector` in `src/pose`. This module uses Google's MediaPipe Pose model to run inference and extract the 33 Cartesian coordinates (`x`, `y`, `z`, `visibility`) for each pose landmark.
3.  **Biomechanical Metrics Calculation**: The raw landmark data is immediately converted into a structured `BiomechanicalMetrics` object. This crucial abstraction layer translates low-level coordinates into high-level, domain-specific data like joint angles, velocities, and symmetry ratios. The angle calculation is performed using the dot product of vectors formed by the relevant joints.
4.  **Stateful Processing**: The `PoseProcessor` in `src/processing` receives the `BiomechanicalMetrics` object. It maintains the application's state, primarily through the `RepCounter` state machine, which tracks the user's movement phase (e.g., "up" phase, "down" phase) by monitoring the vertical trajectory of the hip landmarks.
5.  **Repetition Aggregation**: As the user performs a squat, the `PoseProcessor` collects a time-series list of `BiomechanicalMetrics` objects for the entire repetition.
6.  **Grading Trigger**: Upon the `RepCounter` detecting the completion of a repetition, the aggregated list of metrics is dispatched to the `IntelligentFormGrader`.
7.  **Expert System Analysis**: The `IntelligentFormGrader` iterates through its modular analyzers (e.g., `SafetyAnalyzer`, `DepthAnalyzer`), each of which evaluates the repetition data against skill-level-adjusted thresholds.
8.  **Feedback Generation**: The analysis results—a comprehensive dictionary containing scores, detected faults, and recommendations—are passed to the `EnhancedFeedbackManager`, which prioritizes the most critical feedback and uses the `VoiceFeedbackEngine` to deliver it audibly.
9.  **UI Rendering**: The main GUI thread receives the original frame, the pose overlay, and the latest analysis data to render a new view for the user, updating dashboards and performance charts.
10. **Data Persistence**: The results of the repetition and the overall session summary are passed to the `DataLogger`, which appends the structured data to the relevant CSV files.
11. **Loop**: The cycle repeats for the next frame, ensuring real-time performance.

---

### **Chapter 4: Detailed Implementation**

This chapter provides a detailed breakdown of the implementation of each core module within the `src/` directory.

#### **4.1 `src/grading`: The Biomechanical Analysis Engine**

This module is the intellectual heart of the application, implementing a sophisticated rule-based expert system for form evaluation.

*   **`advanced_form_grader.py`**:
    *   **`IntelligentFormGrader`**: The primary class that orchestrates the grading process. It is initialized with a `UserProfile` and a `ThresholdConfig` object. Its main public method, `grade_repetition`, takes a list of `BiomechanicalMetrics` and returns a complete analysis.
    *   **Modular Analyzer Design**: The system's extensibility is derived from its modular design. Each biomechanical principle is encapsulated in its own class (e.g., `SafetyAnalyzer`, `StabilityAnalyzer`). All analyzers inherit from a (conceptual) base class and implement an `analyze` method. This allows new rules to be added without modifying the core grading logic.

        *Code Snippet: Structure of a typical analyzer.*
        ```python
        class SafetyAnalyzer:
            def __init__(self, config: ThresholdConfig):
                self.config = config

            def analyze(self, frame_metrics: List[BiomechanicalMetrics]) -> Tuple[float, List[str]]:
                score = 100.0
                faults = []
                # ... logic to check for back rounding, etc. ...
                min_back_angle = min(m.back_angle for m in frame_metrics if m.back_angle > 0)
                if min_back_angle < self.config.safety_severe_back_rounding:
                    score -= 50  # Apply penalty
                    faults.append("Severe back rounding detected.")
                # ... more rules ...
                return score, faults
        ```
    *   **`ThresholdConfig`**: A `dataclass` that centralizes all numerical thresholds. This is a critical design choice, moving magic numbers out of the logic and into a configurable object. This makes the system tunable and is essential for implementing adaptive difficulty.
    *   **Adaptive Difficulty**: The `set_difficulty` method is the core of the adaptive system. It adjusts both the scoring weights and the fault thresholds.
        1.  **Threshold Scaling**: A multiplier is applied to the base thresholds. For `Beginner`, thresholds are relaxed (e.g., multiplier of 1.1), while for `Expert`, they are tightened (e.g., multiplier of 0.8).
        2.  **Weight Re-distribution**: The importance of each analyzer's score is adjusted based on skill level. For instance, an expert user is expected to have mastered basic depth, so the system places a higher emphasis on stability and safety.

        *Code Snippet: Skill-based weight distribution.*
        ```python
        def _get_skill_based_weights(self) -> Dict[str, float]:
            skill_level = self.user_profile.skill_level if self.user_profile else UserLevel.BEGINNER
            if skill_level == UserLevel.EXPERT:
                return {
                    'safety': 0.45, 'depth': 0.20, 'stability': 0.15,
                    'tempo': 0.10, 'symmetry': 0.10
                }
            # ... other skill levels ...
            else: # Beginner
                return {
                    'safety': 0.30, 'depth': 0.30, 'stability': 0.15,
                    'tempo': 0.15, 'symmetry': 0.10
                }
        ```

#### **4.2 `src/processing`: Pipeline Orchestration**

This module acts as the central nervous system, connecting raw data processing to high-level application logic.

*   **`pose_processor.py`**:
    *   **`PoseProcessor`**: The main state-management class. It is initialized with instances of `IntelligentFormGrader` and `EnhancedFeedbackManager`, acting as a mediator.
    *   **`RepCounter`**: A finite state machine that determines the user's exercise phase. It operates on a simple but effective principle: tracking the vertical position of the hip.

        *Algorithm: Repetition Counting*
        1.  Establish a baseline "up" position.
        2.  When the hip's y-coordinate drops below a certain threshold, transition to the `STATE_DOWN`.
        3.  When the hip's y-coordinate rises back above the threshold from a `STATE_DOWN`, transition to `STATE_UP` and count this as one completed repetition.
        4.  This state-based approach is robust against small jitters or pauses during the movement.
    *   **`_process_completed_rep`**: This method is triggered by the `RepCounter`. It takes the buffered list of `BiomechanicalMetrics` for the completed rep and sends it to the `IntelligentFormGrader` for analysis, demonstrating the hand-off between the processing and grading layers.

#### **4.3 `src/gui`: Graphical User Interface**

The GUI is a sophisticated, multi-component application built with **PySide6**, chosen for its robust support for multimedia and cross-platform compatibility.

*   **`main_window.py`**:
    *   **`MainWindow`**: The central `QMainWindow` class. It orchestrates the layout and interaction of all UI components.
    *   **Video Rendering**: A `QLabel` is used as the canvas for the video feed. The `QImage` from the `VideoCaptureThread` is converted to a `QPixmap`. The pose overlay (lines and landmarks) is drawn directly onto this pixmap using a `QPainter`, which is more efficient than using overlay widgets.
    *   **Custom Widgets**: The UI is composed of custom, reusable widgets (`MetricsDashboard`, `SessionDashboard`, `SparklineWidget`), each with its own file. This follows the component-based design principle, making the UI easier to manage.
    *   **`SparklineWidget`**: A notable custom component that displays a minimalist, lightweight graph of the user's score over the session. This is an example of efficient data visualization, providing trend information without the overhead of a full charting library.
    *   **Thread-Safe Signal/Slot Mechanism**: The GUI interacts with the backend processing threads exclusively through Qt's signal and slot mechanism. For example, the `VideoCaptureThread` emits a `new_frame` signal, which is connected to a slot in `MainWindow` to update the UI. This is the standard, thread-safe way to update a GUI from other threads and is critical for application stability.

#### **4.4 `src/pose` and `src/capture`: Data Acquisition**

These modules form the entry point of the data pipeline.

*   **`src/capture/video_capture.py`**:
    *   **`VideoCaptureThread`**: This class subclasses `QThread`. Its `run` method contains an infinite loop that continuously polls the camera using `cv2.VideoCapture`. This design is essential to prevent the GUI from freezing, as camera I/O is a blocking operation.
*   **`src/pose/pose_detector.py`**:
    *   **`PoseDetector`**: This class is a wrapper around the `mediapipe.solutions.pose` model. It handles the initialization of the model and the inference process.
    *   **`_calculate_biomechanical_metrics`**: This private method contains the vector math for angle calculations.

        *Algorithm: Angle Calculation*
        To calculate the angle of a joint (e.g., the knee, formed by hip-knee-ankle), it treats the landmarks as vectors.
        1.  Define vectors: `vector1 = hip - knee`, `vector2 = ankle - knee`.
        2.  Normalize the vectors.
        3.  Compute the dot product of the normalized vectors.
        4.  The angle is the arccosine of the dot product, converted to degrees. `angle = np.arccos(dot_product) * (180.0 / np.pi)`.
        This mathematical abstraction is fundamental to the entire system.

#### **4.5 `src/data`: Data Persistence and Modeling**

This module is responsible for how data is structured and stored.

*   **`session_logger.py`**:
    *   **`DataLogger`**: Manages all file I/O for CSV logging.
    *   **Multi-Schema Logging**: The logger writes to four distinct CSV files:
        1.  `session_YYYYMM.csv`: High-level summary of each session.
        2.  `rep_data_YYYYMM.csv`: Detailed breakdown of every single repetition.
        3.  `biomech_YYYYMM.csv`: Frame-by-frame biomechanical data (optional, for deep analysis).
        4.  `ml_dataset_YYYYMM.csv`: A flattened, analysis-ready dataset designed for future ML model training.
    *   This structured approach is far superior to logging all data to a single file, as it organizes the data by its level of granularity, making subsequent analysis significantly more manageable. The inclusion of a dedicated ML dataset file shows foresight in the system's design.

---
This document provides a comprehensive, technically detailed overview of the AI Fitness Coach codebase, suitable for a dissertation. It covers the system's architecture, data flow, and the specific implementation details of its core modules, highlighting key algorithms and design decisions.
