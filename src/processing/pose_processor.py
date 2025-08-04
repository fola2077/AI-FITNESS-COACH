import cv2
import numpy as np
import time
import math
from collections import deque
from src.pose.pose_detector import PoseDetector
from src.utils.math_utils import joint_angle
from src.feedback.feedback_manager import FeedbackManager
from src.grading.advanced_form_grader import (
    IntelligentFormGrader,
    UserProfile,
    UserLevel,
    BiomechanicalMetrics,
    ThresholdConfig
)
from src.gui.widgets.session_report import SessionManager
from src.utils.rep_counter import RepCounter, MovementPhase
from src.validation.pose_validation import PoseValidationSystem
from enum import Enum

class SessionState(Enum):
    """Session state enumeration for robust state management"""
    STOPPED = "stopped"
    CALIBRATING = "calibrating"
    ACTIVE = "active"
    PAUSED = "paused"

class PoseProcessor:
    def __init__(self, user_profile: UserProfile = None, threshold_config: ThresholdConfig = None, enable_validation: bool = False):
        self.pose_detector = PoseDetector()
        self.feedback_manager = FeedbackManager()
        self.session_manager = SessionManager()
        self.rep_counter = RepCounter(exercise_type="squat")

        self.user_profile = user_profile or UserProfile(user_id="default_user", skill_level=UserLevel.INTERMEDIATE)
        
        # UPDATED: Use provided threshold_config or create default one (required for Task 2)
        self.threshold_config = threshold_config or ThresholdConfig.emergency_calibrated()
        
        # UPDATED: Pass both user_profile and config to form grader (now required)
        self.form_grader = IntelligentFormGrader(
            user_profile=self.user_profile,
            difficulty="casual",  # Default difficulty
            config=self.threshold_config
        )
        
        # Validation system (optional for debugging)
        self.enable_validation = enable_validation
        self.validation_system = PoseValidationSystem() if enable_validation else None

        self.settings = {
            'show_skeleton': True,
            'show_angles': True,
            'confidence_threshold': 0.7,
            'calibration_required_frames': 90,
        }
        self.reset()

    def reset(self):
        """Resets the processor for a new session."""
        print("🔄 Processor reset for new session.")
        self.rep_counter.reset()
        self.session_manager.reset_session()
        self.form_grader.reset_workout_session()  # Full reset for new workout session
        self.session_state = SessionState.STOPPED
        self.current_rep_metrics = []
        self.last_rep_analysis = {}
        self.previous_metrics = None
        self.frame_counter = 0
        self.fps = 0
        self.start_time = time.time()
        self.stability_buffer = deque(maxlen=30)
        self.calibration_frames = 0

    def start_session(self, source_type='webcam'):
        """Starts a new analysis session."""
        print("🚀 Starting new session...")
        self.reset()
        self.session_manager.start_session()
        if source_type == 'webcam':
            self.session_state = SessionState.CALIBRATING
            print("✅ Session started - Beginning calibration...")
        else:
            self.session_state = SessionState.ACTIVE
            print("✅ Session started - Video analysis mode")

    def end_session(self):
        """Ends the current session."""
        print("🛑 Ending session.")
        self.session_state = SessionState.STOPPED
        self.session_manager.end_session()
        # Return session summary instead of calling non-existent method
        return self.session_manager.get_session_summary()

    def process_frame(self, frame):
        """Processes a single video frame for pose analysis."""
        if frame is None or frame.size == 0:
            print("❌ Invalid frame provided.")
            return self._get_error_metrics(frame, "Invalid Frame")

        display_frame = frame.copy()
        self._calculate_fps()

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pose_results = self.pose_detector.process_frame(frame_rgb)

        if not pose_results or not pose_results.pose_landmarks:
            return self._get_error_metrics(display_frame, "No Pose Detected")
        
        self.pose_detector.results = pose_results
        self.pose_detector.draw_landmarks(display_frame)
        
        landmarks = pose_results.pose_landmarks.landmark

        if self.session_state == SessionState.CALIBRATING:
            return self._handle_calibration(landmarks, display_frame)
        
        if self.session_state == SessionState.ACTIVE:
            return self._handle_active_analysis(landmarks, display_frame)

        return self._get_error_metrics(display_frame, f"Unhandled State: {self.session_state.value}")

    def _calculate_fps(self):
        """Calculates the frames per second."""
        self.frame_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            self.fps = self.frame_counter / elapsed_time
            self.frame_counter = 0
            self.start_time = time.time()

    def _convert_landmarks_to_metrics(self, landmarks, previous_metrics):
        """Converts raw MediaPipe landmarks to a BiomechanicalMetrics object."""
        # This function encapsulates the logic we removed from the form grader
        try:
            angles = self.pose_detector.calculate_angles(landmarks)
            com_x, com_y = self.pose_detector.calculate_center_of_mass(landmarks)
            visibility = self.pose_detector.calculate_landmark_visibility(landmarks)
            
            velocity, acceleration, jerk = 0.0, 0.0, 0.0
            dt = 1.0 / (self.fps if self.fps > 0 else 30.0)

            if previous_metrics:
                dx = com_x - previous_metrics.center_of_mass_x
                dy = com_y - previous_metrics.center_of_mass_y
                velocity = math.sqrt(dx**2 + dy**2) / dt
                acceleration = (velocity - previous_metrics.movement_velocity) / dt
                jerk = (acceleration - previous_metrics.acceleration) / dt

            # FIX: Add validation to ensure we have valid angle data
            if not angles or all(angle == 0 for angle in angles.values()):
                print("⚠️ Warning: No valid angles calculated from landmarks")
                return None  # Return None instead of default metrics

            return BiomechanicalMetrics(
                knee_angle_left=angles.get('knee_left', 0),
                knee_angle_right=angles.get('knee_right', 0),
                hip_angle=angles.get('hip', 0),
                back_angle=angles.get('back', 0),
                center_of_mass_x=com_x,
                center_of_mass_y=com_y,
                movement_velocity=velocity,
                acceleration=acceleration,
                jerk=jerk,
                timestamp=time.time(),
                landmark_visibility=visibility,
                raw_landmarks=landmarks  # Pass raw landmarks for enhanced analysis
            )
        except Exception as e:
            print(f"Error creating biomechanical metrics: {e}")
            return None  # Return None on error instead of default object

    def _handle_active_analysis(self, landmarks, frame):
        """Handles analysis during an active session."""
        angles = self.pose_detector.calculate_angles(landmarks)
        rep_state = self.rep_counter.update(angles)

        # Collect metrics for the current rep - SKIP invalid metrics
        if rep_state.phase != MovementPhase.STANDING or self.current_rep_metrics:
            current_metric = self._convert_landmarks_to_metrics(landmarks, self.previous_metrics)
            if current_metric is not None:  # Only add valid metrics
                self.current_rep_metrics.append(current_metric)
                self.previous_metrics = current_metric

        # When a rep is completed, trigger the full analysis
        if rep_state.rep_completed:
            self._process_completed_rep()
            self.current_rep_metrics = []
            self.previous_metrics = None

        # Prepare live data for the UI
        live_results = {
            'rep_count': self.rep_counter.rep_count,
            'phase': rep_state.phase,  # phase is already a string, no need for .value
            'fps': self.fps,
            'session_state': self.session_state.value,
            'landmarks_detected': True,
            'processed_frame': frame,
            'last_rep_analysis': self.last_rep_analysis
        }
        return live_results

    def _process_completed_rep(self):
        """
        Processes a completed repetition by converting landmarks to metrics
        and sending them to the form grader.
        """
        try:
            if not self.current_rep_metrics:
                print("⚠️ Rep completed with no landmark data.")
                return

            frame_metrics = self.current_rep_metrics
            print(f"🔄 Processing completed rep {self.rep_counter.rep_count} with {len(frame_metrics)} metrics.")
            
            # Run validation if enabled
            # Reset form grader state for fresh analysis of each rep
            self.form_grader.reset_session_state()
            
            if self.enable_validation and self.validation_system:
                print(f"\n{'='*60}")
                print(f"🔍 VALIDATION MODE - Rep {self.rep_counter.rep_count}")
                print(f"{'='*60}")
                
                # Validate the frame metrics
                validation_results = self.validation_system.validate_rep_analysis(
                    frame_metrics, self.pose_detector, self.form_grader
                )
                
                # Print validation summary
                print(f"Validation Results:")
                print(f"- Landmark validation: {'✅ PASS' if validation_results['landmarks']['is_valid'] else '❌ FAIL'}")
                print(f"- Angle validation: {'✅ PASS' if validation_results['angles']['is_valid'] else '❌ FAIL'}")
                print(f"- Metrics validation: {'✅ PASS' if validation_results['biomechanics']['is_valid'] else '❌ FAIL'}")
                
                # Use debug grading if validation is enabled
                debug_results = self.form_grader.debug_grade_repetition(frame_metrics)
                self.last_rep_analysis = debug_results['normal_result']
                
                # Store debug info for analysis
                self.last_rep_analysis['debug_info'] = debug_results
                self.last_rep_analysis['validation_results'] = validation_results
                
            else:
                # Standard grading - using improved weighted scoring system
                self.last_rep_analysis = self.form_grader.grade_repetition(frame_metrics)
            
            # Add timestamp for UI tracking
            self.last_rep_analysis['timestamp'] = time.time()
            
            # Update session manager with the analysis
            if hasattr(self, 'session_manager'):
                self.session_manager.update_session(
                    rep_count=self.rep_counter.rep_count,
                    form_score=self.last_rep_analysis.get('score', 0),
                    phase='COMPLETED',
                    fault_data=self.last_rep_analysis.get('faults', [])
                )

        except Exception as e:
            print(f"⚠️ Error in rep analysis: {e}")
            import traceback
            traceback.print_exc()
            self.last_rep_analysis = {
                'score': 0, 
                'feedback': ['Analysis failed.'],
                'timestamp': time.time()
            }
        

    def _handle_calibration(self, landmarks, frame):
        """Handles the calibration phase."""
        com_x, com_y = self.pose_detector.calculate_center_of_mass(landmarks)
        self.stability_buffer.append((com_x, com_y))
        
        is_stable = False
        if len(self.stability_buffer) == self.stability_buffer.maxlen:
            x_var = np.var([pos[0] for pos in self.stability_buffer])
            y_var = np.var([pos[1] for pos in self.stability_buffer])
            if x_var < 0.0001 and y_var < 0.0001:
                is_stable = True
        
        if is_stable:
            self.calibration_frames += 1
        else:
            self.calibration_frames = 0 # Reset if unstable

        progress = self.calibration_frames / self.settings['calibration_required_frames']

        if progress >= 1.0:
            print("✅ Calibration Complete!")
            self.session_state = SessionState.ACTIVE
            feedback = ["Ready to start! Begin your first squat."]
        else:
            feedback = [f"Hold steady... {int(progress * 100)}%" if is_stable else "Please stand still."]

        return {
            'rep_count': 0, 'phase': 'CALIBRATING', 'fps': self.fps,
            'session_state': self.session_state.value, 'landmarks_detected': True,
            'processed_frame': frame, 'feedback': feedback, 'last_rep_analysis': {}
        }

    def _get_error_metrics(self, frame, message):
        """Returns a standard dictionary for error states or no pose."""
        # You can draw the error message on the frame here if you want
        cv2.putText(frame, message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return {
            'rep_count': self.rep_counter.rep_count,
            'phase': 'ERROR', 'fps': self.fps,
            'session_state': self.session_state.value, 'landmarks_detected': False,
            'processed_frame': frame, 'last_rep_analysis': self.last_rep_analysis
        }