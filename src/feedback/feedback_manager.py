import time
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class FeedbackMessage:
    message: str
    priority: int  # 1=critical, 2=important, 3=minor
    timestamp: float
    duration: float = 3.0  # How long to show
    category: str = "general"  # "safety", "form", "encouragement"

class FeedbackManager:
    def __init__(self):
        self.active_messages = deque(maxlen=5)
        self.message_history = deque(maxlen=50)
        self.last_feedback_time = {}
        self.cooldown_periods = {
            "safety": 2.0,      # Safety messages every 2 seconds max
            "form": 5.0,        # Form tips every 5 seconds max  
            "encouragement": 10.0  # Encouragement every 10 seconds max
        }
        
    def add_feedback(self, message: str, priority: int = 2, 
                    category: str = "general", duration: float = 3.0):
        """Add feedback message with smart filtering"""
        current_time = time.time()
        
        # Check cooldown
        if category in self.last_feedback_time:
            time_since_last = current_time - self.last_feedback_time[category]
            if time_since_last < self.cooldown_periods.get(category, 3.0):
                return False  # Skip due to cooldown
        
        # Create feedback message
        feedback = FeedbackMessage(
            message=message,
            priority=priority,
            timestamp=current_time,
            duration=duration,
            category=category
        )
        
        # Add to active messages (sorted by priority)
        self.active_messages.append(feedback)
        self.message_history.append(feedback)
        self.last_feedback_time[category] = current_time
        
        return True
    
    def get_current_feedback(self) -> List[FeedbackMessage]:
        """Get current active feedback messages"""
        current_time = time.time()
        
        # Remove expired messages
        active = [msg for msg in self.active_messages 
                 if current_time - msg.timestamp < msg.duration]
        
        # Sort by priority (lower number = higher priority)
        active.sort(key=lambda x: x.priority)
        
        return active[:2]  # Show max 2 messages
    
    def process_pose_analysis(self, faults: List[str], angles: Dict, 
                            phase: str, rep_count: int, form_score: int = None):
        """Process pose analysis and generate appropriate feedback"""
        
        # Safety feedback (highest priority)
        if "BACK_ROUNDING" in faults:
            self.add_feedback(
                "Keep chest up! Protect your spine", 
                priority=1, category="safety", duration=4.0
            )
        
        # Form feedback  
        if "KNEE_VALGUS" in faults:
            self.add_feedback(
                "Push knees out over toes",
                priority=2, category="form", duration=3.0
            )
            
        if "INSUFFICIENT_DEPTH" in faults:
            self.add_feedback(
                "Squat deeper - hip below knee", 
                priority=2, category="form", duration=3.0
            )
            
        if "FORWARD_LEAN" in faults:
            self.add_feedback(
                "Stay more upright - engage your core",
                priority=2, category="form", duration=3.0
            )
            
        if "ASYMMETRIC_MOVEMENT" in faults:
            self.add_feedback(
                "Keep movement balanced left and right",
                priority=2, category="form", duration=3.0
            )
            
        if "HEEL_RISE" in faults:
            self.add_feedback(
                "Keep heels on the ground",
                priority=2, category="form", duration=3.0
            )
        
        # Encouragement feedback
        if not faults and phase == "STANDING":
            if rep_count > 0 and rep_count % 5 == 0:
                self.add_feedback(
                    f"Excellent! {rep_count} reps completed",
                    priority=3, category="encouragement", duration=2.0
                )
        
        # Form score feedback
        if form_score is not None:
            if form_score >= 90 and not faults:
                self.add_feedback(
                    "Perfect form! Keep it up!",
                    priority=3, category="encouragement", duration=2.0
                )
            elif form_score < 60:
                self.add_feedback(
                    "Focus on form over speed",
                    priority=2, category="form", duration=3.0
                )
        
        # Phase-specific coaching
        if phase == "DESCENT" and angles.get('knee', 180) > 120:
            self.add_feedback(
                "Continue descending slowly",
                priority=3, category="form", duration=1.5
            )
        elif phase == "BOTTOM" and angles.get('knee', 180) > 100:
            self.add_feedback(
                "Go a bit deeper if comfortable",
                priority=3, category="form", duration=2.0
            )
    
    def clear_messages(self):
        """Clear all active messages"""
        self.active_messages.clear()
        
    def get_feedback_statistics(self):
        """Get statistics about feedback provided"""
        categories = {}
        total_messages = len(self.message_history)
        
        for msg in self.message_history:
            category = msg.category
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_messages': total_messages,
            'by_category': categories,
            'recent_messages': list(self.message_history)[-10:]  # Last 10 messages
        }
    
    def adjust_sensitivity(self, sensitivity_level):
        """Adjust feedback sensitivity (1.0 = normal, 0.5 = less sensitive, 2.0 = more sensitive)"""
        base_cooldowns = {
            'safety': 2.0,
            'form': 5.0,
            'encouragement': 10.0
        }
        
        for category, base_cooldown in base_cooldowns.items():
            self.cooldown_periods[category] = base_cooldown / sensitivity_level
