# ai_fitness_coach/src/processing/pose_processor.py
import cv2
import numpy as np
import time
from collections import deque
from src.pose.pose_detector import PoseDetector
from src.utils.math_utils import joint_angle
from src.feedback.feedback_manager import FeedbackManager

class PoseProcessor:
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.feedback_manager = FeedbackManager()
        
        # State Management
        self.rep_counter = 0
        self.phase = "STANDING"
        self.feedback_log = []
        
        # Form analysis improvements
        self.back_angle_buffer = deque(maxlen=5)
        self.back_rounding_frames = 0
        self.current_angles = {}
        self.form_score = 100

        # FPS calculation
        self.start_time = time.time()
        self.frame_counter = 0
        self.fps = 0
        
        # Settings
        self.settings = {
            'show_skeleton': True,
            'show_angles': True,
            'confidence_threshold': 0.7,
            'back_angle_threshold': 25,
            'knee_depth_threshold': 90,
            'smoothing_frames': 5
        }

    def reset(self):
        """Resets the processor for a new session."""
        self.rep_counter = 0
        self.phase = "STANDING"
        self.feedback_log = []
        self.start_time = time.time()
        self.frame_counter = 0
        self.fps = 0
        self.back_angle_buffer.clear()
        self.back_rounding_frames = 0
        self.current_angles = {}
        self.form_score = 100
        self.feedback_manager.clear_messages()

    def process_frame(self, frame):
        # 1. FPS Calculation
        self.frame_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            self.fps = self.frame_counter / elapsed_time
            self.frame_counter = 0
            self.start_time = time.time()

        # 2. Pose Detection
        pose_results = self.pose_detector.process_frame(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 3. Enhanced Form Analysis
        metrics, faults = {}, []
        if pose_results and pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            faults, angles = self.analyze_form_improved(landmarks)
            self.current_angles = angles
            
            # Calculate form score
            self.form_score = self.calculate_form_score(faults)
            
            # Update phase detection
            self.update_phase_detection(angles.get('knee', 180))
            
            # Process feedback
            self.feedback_manager.process_pose_analysis(
                faults, angles, self.phase, self.rep_counter, self.form_score
            )
            
            metrics.update(angles)
            metrics['form_score'] = self.form_score

        metrics['fps'] = self.fps

        # 4. Draw Enhanced Overlays
        annotated_frame = self.draw_overlays_improved(frame.copy(), metrics, faults, pose_results)
        return annotated_frame

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
        """Enhanced phase detection"""
        previous_phase = self.phase
        
        if knee_angle > 160:
            self.phase = "STANDING"
        elif previous_phase == "STANDING" and knee_angle < 160:
            self.phase = "DESCENT"
        elif knee_angle < 100:
            self.phase = "BOTTOM"
        elif previous_phase == "BOTTOM" and knee_angle > 100:
            self.phase = "ASCENT"

        # Rep counting - only count when returning to standing from bottom
        if self.phase == "STANDING" and previous_phase == "ASCENT":
            self.rep_counter += 1

    def draw_overlays_improved(self, frame, metrics, faults, pose_results=None):
        """Improved overlay with better proportions and feedback integration"""
        height, width = frame.shape[:2]
        
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
            cv2.putText(frame, "No pose detected", (10, height - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.6, (0, 0, 255), thickness)
        
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
        return colors.get(phase, (255, 255, 255))

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