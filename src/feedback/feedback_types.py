"""
Feedback System Core Types and Data Structures

This module defines the foundational enums and dataclasses for the enhanced feedback system.
Separated from the main manager to maintain clean architecture and enable easy testing.
"""

from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time

class FeedbackPriority(IntEnum):
    """Priority levels for feedback messages (lower number = higher priority)"""
    CRITICAL = 1    # Safety issues, immediate danger
    HIGH = 2        # Major form issues affecting effectiveness
    MEDIUM = 3      # Improvement opportunities
    LOW = 4         # Fine-tuning, encouragement
    INFO = 5        # General information

class FeedbackStyle(Enum):
    """Feedback delivery styles for different coaching approaches"""
    URGENT = "urgent"           # Immediate attention required
    CORRECTIVE = "corrective"   # Direct correction needed
    INSTRUCTIONAL = "instructional"  # Clear, educational guidance
    ENCOURAGING = "encouraging"  # Positive, supportive tone
    MOTIVATIONAL = "motivational"   # Pump-up, energetic

class MessageCategory(Enum):
    """Categories of feedback messages for organization and cooldown management"""
    SAFETY = "safety"           # Back rounding, dangerous positions
    DEPTH = "depth"             # Squat depth, range of motion
    STABILITY = "stability"     # Balance, core engagement
    TEMPO = "tempo"             # Movement speed, control
    SYMMETRY = "symmetry"       # Left/right balance
    TECHNIQUE = "technique"     # General form improvements
    MOTIVATION = "motivation"   # Encouragement, progress
    SESSION = "session"         # Set/session level feedback

@dataclass
class EnhancedFeedbackMessage:
    """Enhanced feedback message with comprehensive metadata
    
    This extends the original FeedbackMessage with voice support,
    intelligent context tracking, and adaptive features.
    """
    # Core message data (compatible with existing system)
    message: str
    priority: int
    timestamp: float
    duration: float = 3.0
    category: str = "general"
    
    # Enhanced features
    style: FeedbackStyle = FeedbackStyle.INSTRUCTIONAL
    voice_enabled: bool = True
    voice_message: Optional[str] = None  # Shorter version for TTS
    occurrence_count: int = 1
    severity_level: str = "moderate"
    target_skill_level: str = "general"
    interrupt_allowed: bool = False
    
    # Context and tracking
    fault_type: Optional[str] = None
    user_context: Dict[str, Any] = field(default_factory=dict)
    delivery_attempted: bool = False
    voice_delivered: bool = False

@dataclass
class UserFeedbackContext:
    """User context for adaptive feedback generation"""
    # User profile
    skill_level: str = "beginner"  # beginner, intermediate, advanced, expert
    session_rep_count: int = 0
    total_session_reps: int = 0
    
    # Performance tracking
    fault_frequency: Dict[str, int] = field(default_factory=dict)
    improvement_trend: str = "stable"  # improving, stable, declining
    fatigue_level: str = "low"  # low, medium, high
    
    # Session state
    last_feedback_time: Dict[str, float] = field(default_factory=dict)
    consecutive_same_fault: int = 0
    session_start_time: float = field(default_factory=time.time)
    
    # Environment
    voice_preference: bool = True
    noise_level: str = "quiet"  # quiet, moderate, loud
    
    def update_fault_occurrence(self, fault_type: str):
        """Track fault frequency for adaptive feedback"""
        self.fault_frequency[fault_type] = self.fault_frequency.get(fault_type, 0) + 1
    
    def get_fault_frequency(self, fault_type: str) -> int:
        """Get how often a specific fault has occurred"""
        return self.fault_frequency.get(fault_type, 0)
    
    def is_frequent_fault(self, fault_type: str, threshold: int = 3) -> bool:
        """Check if a fault is occurring frequently"""
        return self.get_fault_frequency(fault_type) >= threshold
