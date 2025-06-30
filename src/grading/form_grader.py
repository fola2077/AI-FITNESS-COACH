import numpy as np
from src.utils.math_utils import joint_angle

class FormGrader:
    def __init__(self):
        # --- State Management ---
        self.rep_counter = 0
        self.phase = "TOP"
        self.feedback_log = []
        self.rep_scorecard = None

        # --- Biomechanical Thresholds (based on research) ---
        self.depth_threshold_angle = 90.0
        self.back_safety_threshold = 150.0
        self.knee_valgus_threshold_ratio = 0.8
        self.forward_lean_threshold = 45.0

    def get_landmark(self, landmarks, name):
        """Safely gets a landmark by name."""
        return landmarks[self.mp_pose.PoseLandmark[name].value]

    def reset(self):
        """Resets the grader state for a new session."""
        self.rep_counter = 0
        self.phase = "TOP"
        self.feedback_log = []
        self.rep_scorecard = None

    def grade_frame(self, landmarks):
        """
        Processes a single frame of landmarks to update form, phase, and score.
        Returns real-time feedback for the current frame.
        """
        if not landmarks:
            return {}, [] # Return empty metrics and faults if no landmarks

        # 1. Calculate all relevant metrics for the current frame
        metrics = self._calculate_all_metrics(landmarks)
        
        # 2. Detect the current phase of the squat
        previous_phase = self.phase
        self.phase = self._detect_phase(metrics['knee_angle'])

        # 3. Manage repetition state transitions
        if self.phase == "DESC" and previous_phase == "TOP":
            # New repetition has started
            self._start_new_rep()
        
        # 4. Detect real-time faults
        faults = self._detect_realtime_faults(metrics)

        # 5. Update the scorecard for the current rep (if one is in progress)
        if self.rep_scorecard:
            self._update_scorecard(metrics, faults)
            
        # 6. Finalize rep and generate summary if rep is completed
        if self.phase == "TOP" and previous_phase == "ASCENT":
            self._finalize_rep()

        return metrics, faults

    def _calculate_all_metrics(self, landmarks):
        """Calculates and returns a dictionary of all biomechanical metrics."""
        metrics = {}
        
        # Knee angle for phase detection and depth
        left_hip = landmarks[11].x, landmarks[11].y
        left_knee = landmarks[13].x, landmarks[13].y
        left_ankle = landmarks[15].x, landmarks[15].y
        metrics['knee_angle'] = joint_angle(left_hip[0], left_hip[1], left_knee[0], left_knee[1], left_ankle[0], left_ankle[1])

        # Back angle for safety
        left_shoulder = landmarks[5].x, landmarks[5].y
        metrics['back_angle'] = joint_angle(left_shoulder[0], left_shoulder[1], left_hip[0], left_hip[1], left_knee[0], left_knee[1])
        
        # Knee valgus ratio
        right_knee_x = landmarks[14].x
        right_ankle_x = landmarks[16].x
        metrics['knee_ankle_ratio'] = abs(right_knee_x - left_knee[0]) / abs(right_ankle_x - left_ankle[0]) if abs(right_ankle_x - left_ankle[0]) > 0 else 1.0

        # Depth check (hip vs knee vertical position)
        metrics['hip_lower_than_knee'] = left_hip[1] > left_knee[1]

        return metrics

    def _detect_phase(self, knee_angle):
        """Determines the current phase of the squat."""
        if knee_angle > 160:
            return "TOP"
        elif self.phase == "TOP" and knee_angle < 160:
            return "DESC"
        elif knee_angle < 100:
            return "BOTTOM"
        elif self.phase == "BOTTOM" and knee_angle > 100:
            return "ASCENT"
        return self.phase

    def _detect_realtime_faults(self, metrics):
        """Checks for form faults on the current frame."""
        faults = []
        if metrics['back_angle'] < self.back_safety_threshold:
            faults.append("BACK_ROUNDING")
        if metrics['knee_ankle_ratio'] < self.knee_valgus_threshold_ratio:
            faults.append("KNEE_VALGUS")
        return faults

    def _start_new_rep(self):
        """Initializes a new scorecard for the start of a repetition."""
        self.rep_scorecard = {
            "rep_number": self.rep_counter + 1,
            "depth_achieved": False,
            "faults_detected": set(),
        }

    def _update_scorecard(self, metrics, faults):
        """Updates the current repetition's scorecard with new data."""
        # Check if depth was achieved during this frame
        if metrics['hip_lower_than_knee'] and metrics['knee_angle'] < self.depth_threshold_angle:
            self.rep_scorecard['depth_achieved'] = True
        
        # Add any newly detected faults to the set
        for fault in faults:
            self.rep_scorecard['faults_detected'].add(fault)

    def _finalize_rep(self):
        """Calculates the final score for the completed rep and logs feedback."""
        if not self.rep_scorecard:
            return

        final_score = 100
        feedback_summary = f"Rep {self.rep_counter + 1}: "

        # Apply weighted penalties
        if "BACK_ROUNDING" in self.rep_scorecard["faults_detected"]:
            final_score -= 40
        if "KNEE_VALGUS" in self.rep_scorecard["faults_detected"]:
            final_score -= 30
        if not self.rep_scorecard["depth_achieved"]:
            final_score -= 30

        feedback_summary += f"Score: {max(0, final_score)}. Faults: "
        if self.rep_scorecard["faults_detected"]:
            feedback_summary += ", ".join(self.rep_scorecard["faults_detected"])
        else:
            feedback_summary += "None"
        
        self.feedback_log.append(feedback_summary)
        print(feedback_summary) # For console logging

        self.rep_counter += 1
        self.rep_scorecard = None # Reset for the next rep