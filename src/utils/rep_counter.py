"""
Repetition Counter for AI Fitness Coach

This module provides intelligent repetition counting with phase detection
and form validation for exercise tracking.
"""

import time
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

class MovementPhase(Enum):
    """Movement phases for exercise tracking"""
    STANDING = "standing"
    DESCENT = "descent"
    BOTTOM = "bottom"
    ASCENT = "ascent"
    TRANSITION = "transition"

@dataclass
class RepState:
    """State information for a repetition"""
    phase: str
    rep_completed: bool = False
    rep_failed: bool = False
    depth_achieved: bool = False
    phase_duration: float = 0.0

class RepCounter:
    """
    Intelligent repetition counter with phase detection and validation.
    
    This class handles the logic for detecting and counting valid repetitions
    based on joint angles and movement phases.
    """
    
    def __init__(self, exercise_type: str = "squat"):
        self.exercise_type = exercise_type
        self.rep_count = 0
        self.current_phase = MovementPhase.STANDING
        self.previous_phase = MovementPhase.STANDING
        
        # Phase timing
        self.phase_start_time = time.time()
        self.last_phase_change = time.time()
        
        # Depth tracking for validation
        self.hit_bottom_this_rep = False
        self.min_knee_angle_this_rep = 180.0
        
        # Phase history for smoothing
        self.phase_history = []
        self.phase_buffer_size = 5
        
        # Exercise-specific thresholds
        self.thresholds = self._get_exercise_thresholds(exercise_type)
        
    def _get_exercise_thresholds(self, exercise_type: str) -> Dict[str, float]:
        """Get exercise-specific thresholds for phase detection"""
        thresholds = {
            "squat": {
                "standing_threshold": 150.0,  # More lenient - was 160.0
                "descent_threshold": 130.0,   # More lenient - was 140.0  
                "bottom_threshold": 110.0,    # More lenient - was 100.0
                "ascent_threshold": 120.0,    # Keep same
                "min_rep_duration": 0.5,      # Faster reps - was 1.0
                "max_rep_duration": 15.0      # Longer max - was 10.0
            }
        }
        return thresholds.get(exercise_type, thresholds["squat"])
    
    def update(self, angles: Dict[str, float]) -> RepState:
        """
        Update the repetition counter with new angle data.
        
        Args:
            angles: Dictionary of joint angles (e.g., {'knee': 120.0, 'hip': 90.0})
            
        Returns:
            RepState object with current phase and completion status
        """
        # Get primary angle for phase detection (knee for squats)
        primary_angle = angles.get('knee', angles.get('left_knee', angles.get('knee_left', 180.0)))
        
        # Update minimum angle for this rep
        if self.current_phase != MovementPhase.STANDING:
            self.min_knee_angle_this_rep = min(self.min_knee_angle_this_rep, primary_angle)
        
        # Detect phase transitions
        new_phase = self._detect_phase(primary_angle)
        phase_changed = new_phase != self.current_phase
        
        if phase_changed:
            print(f"� Phase: {self.current_phase.value} → {new_phase.value} (angle: {primary_angle:.1f}°)")
            self._handle_phase_transition(new_phase)
        
        # Check for rep completion
        rep_completed = self._check_rep_completion(new_phase)
        rep_failed = False
        
        if rep_completed:
            # Validate the rep
            if self.hit_bottom_this_rep:
                self.rep_count += 1
                print(f"🎉 REP {self.rep_count} COMPLETED! (min depth: {self.min_knee_angle_this_rep:.1f}°)")
            else:
                rep_failed = True
                print(f"❌ Rep failed - didn't hit bottom (min_angle: {self.min_knee_angle_this_rep:.1f}°)")
            
            # Reset for next rep
            self._reset_rep_tracking()
        
        return RepState(
            phase=new_phase.value,
            rep_completed=rep_completed and not rep_failed,
            rep_failed=rep_failed,
            depth_achieved=self.hit_bottom_this_rep,
            phase_duration=time.time() - self.phase_start_time
        )
    
    def _detect_phase(self, primary_angle: float) -> MovementPhase:
        """Detect the current movement phase based on primary angle"""
        thresholds = self.thresholds
        
        # Standing position - high angle
        if primary_angle > thresholds["standing_threshold"]:
            return MovementPhase.STANDING
        
        # Bottom position - very low angle (takes priority)
        elif primary_angle < thresholds["bottom_threshold"]:
            self.hit_bottom_this_rep = True
            return MovementPhase.BOTTOM
        
        # Descent phase - coming down from standing
        elif (self.current_phase == MovementPhase.STANDING and 
              primary_angle < thresholds["descent_threshold"]):
            return MovementPhase.DESCENT
        
        # Ascent phase - coming up from bottom or descent
        elif (self.current_phase in [MovementPhase.BOTTOM, MovementPhase.DESCENT] and 
              primary_angle > thresholds["ascent_threshold"]):
            return MovementPhase.ASCENT
        
        # If we're in ascent and angle is high enough, go to standing
        elif (self.current_phase == MovementPhase.ASCENT and 
              primary_angle > thresholds["standing_threshold"]):
            return MovementPhase.STANDING
        
        # Default to current phase if no clear transition
        return self.current_phase
    
    def _handle_phase_transition(self, new_phase: MovementPhase):
        """Handle transition between movement phases"""
        self.previous_phase = self.current_phase
        self.current_phase = new_phase
        self.last_phase_change = time.time()
        self.phase_start_time = time.time()
        
        print(f"Phase transition: {self.previous_phase.value} → {new_phase.value}")
    
    def _check_rep_completion(self, current_phase: MovementPhase) -> bool:
        """Check if a repetition has been completed"""
        # Rep is complete when returning to standing after hitting bottom
        # This handles cases where we might skip the ascent phase due to fast transitions
        return (current_phase == MovementPhase.STANDING and 
                self.hit_bottom_this_rep and
                self.previous_phase in [MovementPhase.ASCENT, MovementPhase.BOTTOM])
    
    def _reset_rep_tracking(self):
        """Reset tracking variables for the next repetition"""
        self.hit_bottom_this_rep = False
        self.min_knee_angle_this_rep = 180.0
        self.phase_start_time = time.time()
    
    def reset(self):
        """Reset the entire counter for a new session"""
        self.rep_count = 0
        self.current_phase = MovementPhase.STANDING
        self.previous_phase = MovementPhase.STANDING
        self.phase_start_time = time.time()
        self.last_phase_change = time.time()
        self._reset_rep_tracking()
        self.phase_history.clear()
        
        print("🔄 RepCounter reset for new session")
    
    def get_stats(self) -> Dict[str, any]:
        """Get current statistics"""
        return {
            'rep_count': self.rep_count,
            'current_phase': self.current_phase.value,
            'hit_bottom_this_rep': self.hit_bottom_this_rep,
            'min_angle_this_rep': self.min_knee_angle_this_rep,
            'phase_duration': time.time() - self.phase_start_time
        }
