# ai_fitness_coach/src/processing/pose_processor.py
import cv2
import numpy as np
import time
from collections import deque
from src.pose.pose_detector import PoseDetector
from src.utils.math_utils import joint_angle
from src.feedback.feedback_manager import FeedbackManager
from src.grading.advanced_form_grader import (
    IntelligentFormGrader, 
    UserProfile, 
    UserLevel, 
    BiomechanicalMetrics, 
    RepetitionData, 
    MovementPhase
)
from enum import Enum

class SessionState(Enum):
    """Session state enumeration for robust state management"""
    STOPPED = "stopped"
    CALIBRATING = "calibrating"
    ACTIVE = "active"
    PAUSED = "paused"

class PoseProcessor:
    def __init__(self, user_profile: UserProfile = None):
        self.pose_detector = PoseDetector()
        self.feedback_manager = FeedbackManager()
        
        # Initialize advanced form grader
        self.user_profile = user_profile or UserProfile(
            user_id="default_user",
            skill_level=UserLevel.INTERMEDIATE
        )
        self.form_grader = IntelligentFormGrader(self.user_profile)
        
        # Enhanced State Management
        self.session_state = SessionState.STOPPED
        self.rep_counter = 0
        self.phase = MovementPhase.STANDING
        self.previous_phase = MovementPhase.STANDING
        self.feedback_log = []
        
        # Current pose results (for drawing)
        self.current_pose_results = None
        
        # Calibration system
        self.calibration_frames = 0
        self.stability_buffer = deque(maxlen=30)  # 1 second at 30fps
        self.pose_stable_threshold = 0.05  # COM movement threshold for stability
        
        # Current repetition tracking
        self.current_rep_data = None
        self.current_rep_metrics = []
        self.rep_start_time = 0.0
        self.phase_transitions = []
        self.previous_metrics = None
        
        # Legacy compatibility (for existing code)
        self.back_angle_buffer = deque(maxlen=5)
        self.back_rounding_frames = 0
        self.current_angles = {}
        self.current_faults = []
        self.form_score = 100
        self.hit_bottom_this_rep = False

        # FPS calculation
        self.start_time = time.time()
        self.frame_counter = 0
        self.fps = 0
        
        # Enhanced settings
        self.settings = {
            'show_skeleton': True,
            'show_angles': True,
            'confidence_threshold': 0.7,
            'back_angle_threshold': 25,
            'knee_depth_threshold': 90,
            'smoothing_frames': 5,
            'calibration_required_frames': 90,  # 3 seconds at 30fps
            'enable_advanced_grading': True,
            'source_type': 'webcam'  # 'webcam' or 'video'
        }

    def reset(self):
        """Resets the processor for a new session."""
        self.rep_counter = 0
        self.phase = MovementPhase.STANDING
        self.previous_phase = MovementPhase.STANDING
        self.feedback_log = []
        self.start_time = time.time()
        self.frame_counter = 0
        
        # Reset advanced tracking
        self.session_state = SessionState.STOPPED
        self.calibration_frames = 0
        self.stability_buffer.clear()
        self.current_rep_data = None
        self.current_rep_metrics = []
        self.rep_start_time = 0.0
        self.phase_transitions = []
        self.previous_metrics = None
        
        # Reset legacy fields
        self.back_angle_buffer.clear()
        self.back_rounding_frames = 0
        self.current_angles = {}
        self.current_faults = []
        self.form_score = 100
        self.hit_bottom_this_rep = False
    
    def start_session(self, source_type='webcam'):
        """
        Start a new analysis session.
        
        Args:
            source_type: 'webcam' for live analysis, 'video' for pre-recorded analysis
        """
        self.settings['source_type'] = source_type
        
        if source_type == 'webcam':
            # For live webcam, start with calibration
            self.session_state = SessionState.CALIBRATING
            self.calibration_frames = 0
        else:
            # For pre-recorded videos, go directly to active
            self.session_state = SessionState.ACTIVE
        
        print(f"Session started in {self.session_state.value} mode for {source_type}")
    
    def _check_pose_stability(self, landmarks):
        """
        Check if the user's pose is stable for calibration.
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            True if pose is stable, False otherwise
        """
        if not landmarks:
            return False
        
        # Calculate center of mass
        com_x, com_y = self.pose_detector.calculate_center_of_mass(landmarks)
        self.stability_buffer.append((com_x, com_y))
        
        if len(self.stability_buffer) < 10:
            return False
        
        # Check if COM has remained relatively stable
        recent_positions = list(self.stability_buffer)[-10:]
        x_positions = [pos[0] for pos in recent_positions]
        y_positions = [pos[1] for pos in recent_positions]
        
        x_variance = np.var(x_positions)
        y_variance = np.var(y_positions)
        
        # Pose is stable if both variances are below threshold
        return x_variance < self.pose_stable_threshold and y_variance < self.pose_stable_threshold
    
    def _detect_movement_phase(self, landmarks):
        """
        Enhanced phase detection with better transition logic.
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            Detected movement phase
        """
        if not landmarks:
            return self.phase
        
        # Calculate joint angles
        angles = self.pose_detector.calculate_joint_angles(landmarks)
        
        if not angles:
            return self.phase
        
        # Get key angles
        hip_angle = angles.get('hip', 180)
        knee_angle = (angles.get('knee_left', 180) + angles.get('knee_right', 180)) / 2
        
        # Phase detection logic
        is_standing = hip_angle > 160 and knee_angle > 160
        is_at_bottom = hip_angle < 100 and knee_angle < 100
        is_descending = hip_angle < 140 and knee_angle < 140 and not is_at_bottom
        
        prev_phase = self.phase
        
        if prev_phase == MovementPhase.STANDING and is_descending:
            self.phase = MovementPhase.DESCENT
            self._start_new_rep()
        elif prev_phase == MovementPhase.DESCENT:
            if is_at_bottom:
                self.phase = MovementPhase.BOTTOM
                self.hit_bottom_this_rep = True
            elif is_standing:
                # User gave up mid-descent
                self.phase = MovementPhase.STANDING
                self._complete_rep(failed=True)
        elif prev_phase == MovementPhase.BOTTOM and not is_at_bottom:
            self.phase = MovementPhase.ASCENT
        elif prev_phase == MovementPhase.ASCENT and is_standing:
            self.phase = MovementPhase.STANDING
            self._complete_rep(failed=False)
        
        # Log phase transition
        if prev_phase != self.phase:
            self.phase_transitions.append((self.phase, time.time()))
            print(f"Phase transition: {prev_phase.value} -> {self.phase.value}")
        
        return self.phase
    
    def _start_new_rep(self):
        """Start tracking a new repetition."""
        self.rep_counter += 1
        self.rep_start_time = time.time()
        self.current_rep_metrics = []
        self.phase_transitions = [(MovementPhase.DESCENT, self.rep_start_time)]
        self.hit_bottom_this_rep = False
        
        print(f"Started rep {self.rep_counter}")
    
    def _complete_rep(self, failed=False):
        """
        Complete the current repetition and analyze it.
        
        Args:
            failed: Whether the rep failed (didn't reach bottom)
        """
        if self.rep_counter == 0:
            return  # No active rep to complete
        
        rep_end_time = time.time()
        
        # If failed rep (insufficient depth), add the fault
        if failed or not self.hit_bottom_this_rep:
            # Add insufficient depth fault to the last frame metrics
            if self.current_rep_metrics:
                # This will be handled by the form grader's penalty system
                pass
        
        # Create repetition data
        rep_data = RepetitionData(
            rep_number=self.rep_counter,
            start_time=self.rep_start_time,
            end_time=rep_end_time,
            phase_transitions=self.phase_transitions.copy(),
            frame_metrics=self.current_rep_metrics.copy(),
            total_duration=rep_end_time - self.rep_start_time
        )
        
        # Analyze the completed rep
        if self.settings['enable_advanced_grading']:
            analysis_result = self.form_grader.grade_repetition(rep_data)
            
            # Update legacy form score for compatibility
            self.form_score = analysis_result['final_score']
            
            # Extract faults for feedback system
            self.current_faults = [fault['type'] for fault in analysis_result['faults']]
            
            # Generate feedback
            feedback_text = analysis_result['feedback']['motivation']
            if analysis_result['feedback']['coaching_cues']:
                feedback_text += " " + analysis_result['feedback']['coaching_cues'][0]
            
            self.feedback_log.append({
                'timestamp': time.time(),
                'message': feedback_text,
                'rep_number': self.rep_counter,
                'score': self.form_score,
                'analysis': analysis_result
            })
            
            print(f"Rep {self.rep_counter} completed - Score: {self.form_score:.1f}")
        
        # Reset for next rep
        self.hit_bottom_this_rep = False
        self.frame_counter = 0
        self.fps = 0
        self.back_angle_buffer.clear()
        self.back_rounding_frames = 0
        self.current_angles = {}
        self.current_faults = []
        self.form_score = 100
        
        # Reset attempt tracking
        self.hit_bottom_this_rep = False
        self.feedback_manager.clear_messages()

    def process_frame(self, frame):
        """
        Enhanced frame processing with advanced biomechanical analysis.
        
        Args:
            frame: Input video frame
            
        Returns:
            Dictionary containing analysis results and metrics
        """
        # Validate input frame
        if frame is None or frame.size == 0:
            print("❌ Invalid frame provided to pose processor")
            return self._get_basic_metrics()
        
        # 1. FPS Calculation
        self.frame_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            self.fps = self.frame_counter / elapsed_time
            self.frame_counter = 0
            self.start_time = time.time()

        # 2. Pose Detection - convert to RGB since MediaPipe expects RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Log frame details for debugging
        # Only print frame processing info occasionally for performance
        self.frame_debug_counter = getattr(self, 'frame_debug_counter', 0) + 1
        if self.frame_debug_counter % 60 == 0:  # Every 2 seconds
            print(f"⚙️ Processing frame: {frame.shape[1]}x{frame.shape[0]} px")
        
        # Process the frame with MediaPipe
        pose_results = self.pose_detector.process_frame(frame_rgb)
        self.current_pose_results = pose_results  # Store for drawing

        # Diagnostic output about pose detection (reduced for performance)
        if pose_results and pose_results.pose_landmarks:
            if self.frame_debug_counter % 60 == 0:
                print("✅ Pose detected successfully!")
                landmarks_count = len(pose_results.pose_landmarks.landmark)
                print(f"   Found {landmarks_count} landmarks")
        else:
            if self.frame_debug_counter % 60 == 0:
                print("❌ No pose detected in this frame")
            
        # 3. State Management
        if self.session_state == SessionState.STOPPED:
            if self.frame_debug_counter % 180 == 0:  # Only every 6 seconds
                print("ℹ️ Session is currently stopped")
            return self._get_basic_metrics()
        
        if not pose_results or not pose_results.pose_landmarks:
            if self.frame_debug_counter % 180 == 0:  # Only every 6 seconds
                print("ℹ️ No landmarks to process")
            return self._get_basic_metrics()
        
        landmarks = pose_results.pose_landmarks.landmark
        
        # 4. Handle Calibration State
        if self.session_state == SessionState.CALIBRATING:
            if self.frame_debug_counter % 90 == 0:  # Only every 3 seconds
                print("ℹ️ Session in calibration mode")
            return self._handle_calibration(landmarks, frame)
        
        # 5. Active Analysis
        if self.session_state == SessionState.ACTIVE:
            if self.frame_debug_counter % 180 == 0:  # Only every 6 seconds
                print("ℹ️ Session in active analysis mode")
            return self._handle_active_analysis(landmarks, frame)
        
        return self._get_basic_metrics()
    
    def _get_basic_metrics(self):
        """Return basic metrics when no pose is detected or session is stopped."""
        return {
            'reps': self.rep_counter,
            'phase': self.phase.value if hasattr(self.phase, 'value') else str(self.phase),
            'form_score': self.form_score,
            'fps': self.fps,
            'session_state': self.session_state.value,
            'landmarks_detected': False,
            'faults': [],
            'feedback': []
        }
    
    def _handle_calibration(self, landmarks, frame):
        """
        Handle calibration state - ensure user is in stable position.
        
        Args:
            landmarks: MediaPipe pose landmarks
            frame: Current frame for overlay
            
        Returns:
            Calibration status and metrics
        """
        is_stable = self._check_pose_stability(landmarks)
        
        if is_stable:
            self.calibration_frames += 1
        else:
            self.calibration_frames = 0  # Reset if pose becomes unstable
        
        # Calculate anthropometric ratio during calibration
        if self.calibration_frames == 30:  # Update ratio partway through calibration
            torso_leg_ratio = self.form_grader.normalizer.calculate_torso_leg_ratio(landmarks)
            self.user_profile.torso_to_leg_ratio = torso_leg_ratio
            print(f"Calibrated torso-to-leg ratio: {torso_leg_ratio:.2f}")
        
        # Complete calibration
        if self.calibration_frames >= self.settings['calibration_required_frames']:
            self.session_state = SessionState.ACTIVE
            print("Calibration complete - Session now active!")
            return {
                'reps': self.rep_counter,
                'phase': 'READY',
                'form_score': 100,
                'fps': self.fps,
                'session_state': self.session_state.value,
                'landmarks_detected': True,
                'calibration_complete': True,
                'faults': [],
                'feedback': ["Ready to start! Begin your first squat."]
            }
        
        # Still calibrating
        remaining_frames = self.settings['calibration_required_frames'] - self.calibration_frames
        countdown_seconds = remaining_frames / 30.0
        
        return {
            'reps': self.rep_counter,
            'phase': 'CALIBRATING',
            'form_score': 100,
            'fps': self.fps,
            'session_state': self.session_state.value,
            'landmarks_detected': True,
            'calibration_progress': self.calibration_frames / self.settings['calibration_required_frames'],
            'calibration_countdown': countdown_seconds,
            'is_stable': is_stable,
            'faults': [],
            'feedback': [f"Hold steady position... {countdown_seconds:.1f}s" if is_stable else "Please stand still in view"]
        }
    
    def _handle_active_analysis(self, landmarks, frame):
        """
        Handle active analysis state - perform full biomechanical analysis.
        
        Args:
            landmarks: MediaPipe pose landmarks
            frame: Current frame
            
        Returns:
            Complete analysis results
        """
        # Create biomechanical metrics for this frame
        current_metrics = self.form_grader.create_biomechanical_metrics(
            landmarks, 
            self.previous_metrics
        )
        
        # Store metrics for current rep
        if self.session_state == SessionState.ACTIVE:
            self.current_rep_metrics.append(current_metrics)
        
        # Update previous metrics for next frame
        self.previous_metrics = current_metrics
        
        # Detect movement phase
        detected_phase = self._detect_movement_phase(landmarks)
        
        # Legacy form analysis for compatibility
        faults, angles = self.analyze_form_improved(landmarks)
        self.current_angles = angles
        
        # Merge legacy faults with advanced analysis
        if hasattr(self, 'current_faults') and isinstance(self.current_faults, list):
            all_faults = list(set(faults + self.current_faults))
            faults = all_faults
        
        # Update form score (will be overridden by advanced grader for completed reps)
        if faults:
            self.form_score = max(60, self.form_score - len(faults) * 5)
        else:
            self.form_score = min(100, self.form_score + 1)
        
        # Generate feedback
        # feedback_messages = self.feedback_manager.process_faults(faults, angles)
        feedback_messages = []  # No feedback for now; fix or implement as needed
        
        # Get recent analysis if available
        recent_analysis = None
        if self.feedback_log and len(self.feedback_log) > 0:
            recent_analysis = self.feedback_log[-1].get('analysis')
        
        return {
            'reps': self.rep_counter,
            'phase': detected_phase.value,
            'form_score': self.form_score,
            'fps': self.fps,
            'session_state': self.session_state.value,
            'landmarks_detected': True,
            'faults': faults,
            'feedback': feedback_messages,
            'angles': angles,
            'biomechanical_metrics': {
                'knee_left': current_metrics.knee_angle_left,
                'knee_right': current_metrics.knee_angle_right,
                'hip': current_metrics.hip_angle,
                'back': current_metrics.back_angle,
                'symmetry': current_metrics.knee_symmetry_ratio,
                'smoothness': 0,  # Would need sequence analysis
                'confidence': current_metrics.landmark_visibility
            },
            'advanced_analysis': recent_analysis,
            'hit_bottom_this_rep': self.hit_bottom_this_rep
        }
    
    def process_frame_legacy(self, frame):
        """
        Legacy frame processing method for backward compatibility.
        
        This method maintains the original interface for existing code.
        """
        # Process frame with new method
        result = self.process_frame(frame)
        
        # Convert to legacy format
        metrics = {
            'fps': result.get('fps', 0),
            'reps': result.get('reps', 0),
            'phase': result.get('phase', 'STANDING'),
            'form_score': result.get('form_score', 100)
        }
        
        if 'angles' in result:
            metrics.update(result['angles'])
        
        faults = result.get('faults', [])
        
        # Draw overlays
        annotated_frame = self.draw_overlays_improved(frame.copy(), metrics, faults, None)
        
        return annotated_frame, metrics, faults

    def analyze_form_improved(self, landmarks):
        """Improved form analysis with better thresholds and smoothing"""
        faults = []
        angles = {}
        
        try:
            # Get landmarks for calculations
            left_shoulder = landmarks[11].x, landmarks[11].y
            left_hip = landmarks[23].x, landmarks[23].y
            left_knee = landmarks[25].x, landmarks[25].y
            left_ankle = landmarks[27].x, landmarks[27].y
            
            right_shoulder = landmarks[12].x, landmarks[12].y
            right_hip = landmarks[24].x, landmarks[24].y
            right_knee = landmarks[26].x, landmarks[26].y
            right_ankle = landmarks[28].x, landmarks[28].y

            # Calculate angles with error handling
            try:
                knee_angle = joint_angle(left_hip[0], left_hip[1], left_knee[0], left_knee[1], left_ankle[0], left_ankle[1])
                angles['knee'] = knee_angle
            except:
                angles['knee'] = 180

            try:
                back_angle = joint_angle(left_shoulder[0], left_shoulder[1], left_hip[0], left_hip[1], left_knee[0], left_knee[1])
                
                # Apply smoothing to back angle
                self.back_angle_buffer.append(back_angle)
                smoothed_back_angle = np.mean(list(self.back_angle_buffer))
                angles['back'] = smoothed_back_angle
                
                # Improved back rounding detection with persistence
                if smoothed_back_angle < 140:  # More lenient threshold
                    self.back_rounding_frames += 1
                    # Only flag if it persists for multiple frames
                    if self.back_rounding_frames > 8:  # ~0.25 seconds at 30fps
                        faults.append("BACK_ROUNDING")
                else:
                    self.back_rounding_frames = max(0, self.back_rounding_frames - 2)
                    
            except:
                angles['back'] = 170

            # Depth check (only when in bottom phase)
            if self.phase in ["BOTTOM", "DOWN"] and angles['knee'] > 95:
                faults.append("INSUFFICIENT_DEPTH")
            
            # Knee valgus check (simplified)
            try:
                knee_distance = abs(left_knee[0] - right_knee[0])
                ankle_distance = abs(left_ankle[0] - right_ankle[0])
                if ankle_distance > 0 and (knee_distance / ankle_distance) < 0.8:
                    faults.append("KNEE_VALGUS")
            except:
                pass
            
            # Forward lean check
            try:
                trunk_angle = self.calculate_trunk_lean(left_shoulder, left_hip)
                angles['trunk'] = trunk_angle
                if trunk_angle > 30:  # Degrees from vertical
                    faults.append("FORWARD_LEAN")
            except:
                angles['trunk'] = 0

        except Exception as e:
            print(f"Form analysis error: {e}")
            angles = {'knee': 180, 'back': 170, 'trunk': 0}

        return faults, angles

    def calculate_trunk_lean(self, shoulder, hip):
        """Calculate forward lean angle"""
        # Vector from hip to shoulder
        trunk_vector = np.array([shoulder[0] - hip[0], shoulder[1] - hip[1]])
        # Vertical reference vector (pointing up)
        vertical_vector = np.array([0, -1])
        
        # Calculate angle
        cos_angle = np.dot(trunk_vector, vertical_vector) / (np.linalg.norm(trunk_vector) * np.linalg.norm(vertical_vector))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))
        
        return abs(angle)

    def calculate_form_score(self, faults):
        """Calculate overall form score"""
        base_score = 100
        
        fault_penalties = {
            "BACK_ROUNDING": 25,
            "KNEE_VALGUS": 20,
            "INSUFFICIENT_DEPTH": 15,
            "FORWARD_LEAN": 15,
            "ASYMMETRIC_MOVEMENT": 10,
            "HEEL_RISE": 10
        }
        
        for fault in faults:
            penalty = fault_penalties.get(fault, 5)
            base_score -= penalty
        
        return max(0, min(100, base_score))

    def update_phase_detection(self, knee_angle):
        """Enhanced phase detection with failed attempt tracking"""
        previous_phase = self.phase
        
        # Phase transitions
        if knee_angle > 160:
            # User is standing - check if this completes an attempt
            if previous_phase == "ASCENT":
                # This is the end of an attempt (successful or failed)
                self.rep_counter += 1
                
                # Check if they achieved proper depth
                if not self.hit_bottom_this_rep:
                    # Failed attempt - add insufficient depth fault
                    if not hasattr(self, 'current_faults'):
                        self.current_faults = []
                    self.current_faults.append("INSUFFICIENT_DEPTH")
                    
                    # Give feedback about the failed attempt
                    if hasattr(self, 'feedback_manager'):
                        self.feedback_manager.add_feedback(
                            "Go deeper next time - reach full squat depth",
                            priority=2, category="form", duration=3.0
                        )
                
                # Reset for next attempt
                self.hit_bottom_this_rep = False
                
            self.phase = "STANDING"
            
        elif previous_phase == "STANDING" and knee_angle < 160:
            self.phase = "DESCENT"
            # Reset depth flag when starting new attempt
            self.hit_bottom_this_rep = False
            
        elif knee_angle < 100:
            # User reached proper depth
            self.phase = "BOTTOM" 
            self.hit_bottom_this_rep = True
            
        elif previous_phase == "BOTTOM" and knee_angle > 100:
            self.phase = "ASCENT"
        elif previous_phase == "DESCENT" and knee_angle > 140:
            # User is coming back up without reaching bottom - shallow squat
            self.phase = "ASCENT"

    def draw_overlays_improved(self, frame, metrics, faults, pose_results=None):
        """Improved overlay with better proportions and feedback integration"""
        height, width = frame.shape[:2]
        
        # Use stored pose results if not provided
        if pose_results is None:
            pose_results = self.current_pose_results
        
        # Dynamic sizing based on frame dimensions
        base_font_scale = min(width, height) / 1000.0
        font_scale = max(0.4, min(1.0, base_font_scale))
        thickness = max(1, int(font_scale * 2))
        line_height = max(25, int(font_scale * 35))
        
        # Draw pose skeleton if available and enabled
        skeleton_drawn = False
        if pose_results and pose_results.pose_landmarks and self.settings.get('show_skeleton', True):
            skeleton_drawn = self.pose_detector.draw_landmarks(frame)
            
        # If no skeleton was drawn, show a message
        if not skeleton_drawn and self.settings.get('show_skeleton', True):
            # Create a more noticeable "No pose detected" message
            cv2.putText(
                frame, 
                "NO POSE DETECTED", 
                (width // 2 - 150, height // 2), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1.2, 
                (0, 0, 255),  # Red
                3
            )
            
            # Add troubleshooting tips with better visibility
            tips = [
                "Make sure your FULL BODY is visible in the frame",
                "Stand 6-8 feet (2-3 meters) from camera",
                "Ensure good lighting - avoid backlighting",
                "Wear contrasting clothing from background",
                "Try simpler movements until detection works",
                "Face the camera directly at first"
            ]
            
            # Draw a semi-transparent background for the tips
            tip_box_height = len(tips) * 30 + 20
            tip_box_top = height // 2 + 20
            overlay = frame.copy()
            cv2.rectangle(overlay, (width // 2 - 280, tip_box_top), 
                         (width // 2 + 280, tip_box_top + tip_box_height), 
                         (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            y_pos = height // 2 + 50
            for tip in tips:
                cv2.putText(
                    frame, 
                    f"• {tip}", 
                    (width // 2 - 270, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 255),  # Yellow
                    2
                )
                y_pos += 30
        
        # Create semi-transparent header bar
        overlay_height = max(50, int(height * 0.08))
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, overlay_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Main status line - more compact
        phase_color = self.get_phase_color(self.phase)
        status_y = int(overlay_height * 0.4)
        
        # Compact status display
        status_parts = [
            f"Reps: {self.rep_counter}",
            f"Phase: {self.phase}",
            f"FPS: {int(metrics.get('fps', 0))}"
        ]
        
        if 'form_score' in metrics:
            score = metrics['form_score']
            grade = self.score_to_grade(score)
            status_parts.append(f"Score: {score} ({grade})")
        
        status_text = "  |  ".join(status_parts)
        
        # Draw main status with better contrast
        # Add text background for better visibility
        text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.8, thickness)[0]
        cv2.rectangle(frame, (5, status_y - text_size[1] - 5), (text_size[0] + 15, status_y + 5), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (10, status_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.8, (255, 255, 255), thickness)
        
        # Draw session state indicator
        session_state_text = f"State: {self.session_state.value.upper()}"
        state_color = (0, 255, 0) if self.session_state == SessionState.ACTIVE else (0, 165, 255)
        cv2.putText(frame, session_state_text, (width - 230, status_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.8, state_color, thickness)
        
        # Draw faults and feedback
        y_offset = overlay_height + 20
        
        # Draw "Detected Issues" if there are faults
        if faults:
            cv2.putText(frame, "Detected Issues:", (10, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, (0, 0, 255), thickness)
            y_offset += line_height
            
            for fault in faults[:3]:  # Limit to 3 faults to avoid cluttering
                cv2.putText(frame, f"• {fault}", (20, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, (0, 0, 255), 1)
                y_offset += line_height
            
            if len(faults) > 3:
                cv2.putText(frame, f"... and {len(faults) - 3} more", (20, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, (0, 0, 255), 1)
                y_offset += line_height
        
        # Display feedback messages
        feedback = metrics.get('feedback', [])
        if feedback:
            y_offset += 10
            cv2.putText(frame, "Coaching Cues:", (10, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, (255, 255, 0), thickness)
            y_offset += line_height
            
            for message in feedback[:2]:  # Limit to 2 messages
                cv2.putText(frame, f"• {message}", (20, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, (255, 255, 0), 1)
                y_offset += line_height
        
        return frame
        cv2.rectangle(frame, (5, status_y - text_size[1] - 5), (text_size[0] + 15, status_y + 5), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (10, status_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.8, (255, 255, 255), thickness)
        
        # Secondary info line with angles
        if self.current_angles:
            angles_y = int(overlay_height * 0.8)
            angle_parts = []
            for angle_type, angle_value in self.current_angles.items():
                if angle_type in ['knee', 'back']:
                    angle_parts.append(f"{angle_type.title()}: {angle_value:.0f}°")
            
            if angle_parts:
                angle_text = "  |  ".join(angle_parts)
                # Add background for angle text
                text_size = cv2.getTextSize(angle_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, 1)[0]
                cv2.rectangle(frame, (5, angles_y - text_size[1] - 3), (text_size[0] + 15, angles_y + 3), (0, 0, 0), -1)
                cv2.putText(frame, angle_text, (10, angles_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, (220, 220, 220), 1)
        
        # Display current feedback from feedback manager with better visibility
        current_feedback = self.feedback_manager.get_current_feedback()
        if current_feedback:
            feedback_y = overlay_height + 20
            for i, feedback in enumerate(current_feedback[:2]):  # Show max 2 messages
                color = self.get_feedback_color(feedback.priority)
                bg_color = self.get_feedback_bg_color(feedback.priority)
                text = feedback.message
                
                # Truncate long messages
                if len(text) > 50:
                    text = text[:47] + "..."
                
                # Calculate text position and size
                y_pos = feedback_y + i * line_height
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, thickness)[0]
                
                # Draw background rectangle for better contrast
                padding = 8
                cv2.rectangle(frame, 
                            (5, y_pos - text_size[1] - padding), 
                            (text_size[0] + 15, y_pos + padding), 
                            bg_color, -1)
                
                # Draw border for emphasis
                cv2.rectangle(frame, 
                            (5, y_pos - text_size[1] - padding), 
                            (text_size[0] + 15, y_pos + padding), 
                            color, 2)
                
                # Draw text
                cv2.putText(frame, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, color, thickness)
        
        # Debug: Print current feedback to console for troubleshooting
        if current_feedback:
            print(f"Debug: Displaying {len(current_feedback)} feedback messages:")
            for i, feedback in enumerate(current_feedback[:2]):
                print(f"  {i+1}. [{feedback.category}] {feedback.message}")
        else:
            print("Debug: No active feedback messages")
            
        # Add a test feedback message for debugging
        if not current_feedback:
            # Draw a test message to verify overlay is working
            test_y = overlay_height + 20
            test_text = "Test: Overlay system active"
            text_size = cv2.getTextSize(test_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, 1)[0]
            
            # Draw background
            cv2.rectangle(frame, (5, test_y - text_size[1] - 5), 
                         (text_size[0] + 15, test_y + 5), (0, 0, 0), -1)
            # Draw text in bright green
            cv2.putText(frame, test_text, (10, test_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, (0, 255, 0), 1)
        
        return frame

    def get_phase_color(self, phase):
        """Get color based on movement phase (BGR format)"""
        colors = {
            "STANDING": (0, 200, 0),      # Green
            "DESCENT": (0, 200, 255),     # Orange  
            "BOTTOM": (0, 0, 200),        # Red
            "ASCENT": (200, 100, 0)       # Blue
        }
        
        # Handle Enum cases
        if hasattr(phase, 'value'):
            phase_name = phase.value
        else:
            phase_name = str(phase)
            
        # Default to white if not found
        return colors.get(phase_name.upper(), (255, 255, 255))

    def get_feedback_color(self, priority):
        """Get text color based on feedback priority (BGR format)"""
        if priority == 1:  # Critical - Red text
            return (0, 0, 200)      
        elif priority == 2:  # Important - Orange text
            return (0, 100, 255)    
        else:  # Minor - Dark blue text
            return (150, 150, 0)    

    def get_feedback_bg_color(self, priority):
        """Get background color based on feedback priority (BGR format)"""
        if priority == 1:  # Critical - Light red background
            return (200, 200, 255)      
        elif priority == 2:  # Important - Light orange background
            return (200, 240, 255)    
        else:  # Minor - Light yellow background
            return (200, 255, 255)

    def score_to_grade(self, score):
        """Convert score to letter grade"""
        if score >= 90: return "A"
        elif score >= 80: return "B" 
        elif score >= 70: return "C"
        elif score >= 60: return "D"
        else: return "F"

    def get_current_feedback_messages(self):
        """Get current feedback messages for UI display"""
        return self.feedback_manager.get_current_feedback()
    
    def update_settings(self, new_settings):
        """Update processor settings from GUI"""
        self.settings.update(new_settings)
        
        # Update pose detector confidence if needed
        if 'confidence_threshold' in new_settings:
            confidence = new_settings['confidence_threshold']
            # Recreate pose detector with new confidence
            import mediapipe as mp
            self.pose_detector._pose = self.pose_detector.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=confidence,
                min_tracking_confidence=confidence
            )

    def get_analysis_summary(self):
        """Get current analysis summary for UI display"""
        return {
            'rep_count': self.rep_counter,
            'phase': self.phase,
            'form_score': self.form_score,
            'current_angles': self.current_angles,
            'active_feedback': self.feedback_manager.get_current_feedback(),
            'fps': self.fps
        }
    
    def toggle_overlay_component(self, component, enabled):
        """Toggle specific overlay components"""
        if not hasattr(self, 'overlay_settings'):
            self.overlay_settings = {
                'show_metrics': True,
                'show_feedback': True,
                'show_skeleton': True,
                'show_angles': True
            }
        
        self.overlay_settings[component] = enabled
        
    def create_contrast_text(self, frame, text, position, font_scale, color, thickness):
        """Draw text with background for better contrast"""
        x, y = position
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        
        # Draw black background with some padding
        padding = 4
        cv2.rectangle(frame, 
                     (x - padding, y - text_size[1] - padding), 
                     (x + text_size[0] + padding, y + padding), 
                     (0, 0, 0), -1)
        
        # Draw white border for extra contrast
        cv2.rectangle(frame, 
                     (x - padding, y - text_size[1] - padding), 
                     (x + text_size[0] + padding, y + padding), 
                     (255, 255, 255), 1)
        
        # Draw the text
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        
        return text_size