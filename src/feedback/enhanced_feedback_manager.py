"""
Enhanced Feedback Manager for AI Fitness Coach

This module extends the existing FeedbackManager with voice capabilities,
intelligent message selection, and adaptive feedback based on user context.
Maintains backward compatibility while adding advanced features.
"""

import time
from collections import deque
from typing import Dict, List, Optional, Any, Union

# Import the existing FeedbackMessage for compatibility
from .feedback_manager import FeedbackMessage

# Import new enhanced components
from .feedback_types import (
    FeedbackPriority, FeedbackStyle, MessageCategory, 
    EnhancedFeedbackMessage, UserFeedbackContext
)
from .voice_engine import VoiceFeedbackEngine
from .message_templates import MessageTemplateManager

class EnhancedFeedbackManager:
    """Enhanced feedback manager with voice support and intelligent messaging
    
    This class extends the functionality of the original FeedbackManager while
    maintaining backward compatibility. It adds:
    - Voice feedback with TTS
    - Intelligent message templates with anti-repetition
    - Adaptive feedback based on user progress
    - Context-aware message selection
    """
    
    def __init__(self, voice_enabled: bool = True, user_skill_level: str = "beginner"):
        # Maintain compatibility with existing FeedbackManager interface
        self.active_messages = deque(maxlen=5)
        self.message_history = deque(maxlen=50)
        self.last_feedback_time = {}
        
        # Base cooldown periods (can be adapted based on performance)
        self.base_cooldown_periods = {
            "safety": 2.0,      # Safety messages more frequent
            "form": 5.0,        # Form corrections moderate frequency
            "encouragement": 10.0,  # Encouragement less frequent
            "depth": 4.0,       # Depth feedback moderate frequency
            "stability": 6.0,   # Stability feedback moderate frequency
            "tempo": 8.0,       # Tempo feedback less frequent
            "technique": 7.0,   # General technique moderate frequency
            "motivation": 12.0, # Motivation infrequent
            "session": 15.0     # Session messages very infrequent
        }
        
        # Adaptive cooldown periods (will be adjusted based on user performance)
        self.adaptive_cooldowns = self.base_cooldown_periods.copy()
        
        # Enhanced components
        self.voice_engine = VoiceFeedbackEngine(enabled=voice_enabled)
        self.message_templates = MessageTemplateManager()
        self.user_context = UserFeedbackContext(skill_level=user_skill_level)
        
        # Performance tracking for adaptive behavior
        self.performance_metrics = {
            'total_feedback_given': 0,
            'voice_feedback_given': 0,
            'faults_detected': {},
            'improvement_tracking': {},
            'session_start_time': time.time()
        }
        
        print(f"✅ Enhanced feedback manager initialized")
        print(f"   Voice enabled: {self.voice_engine.is_available()}")
        print(f"   User skill level: {user_skill_level}")
    
    def add_feedback(self, message: str, priority: int = 2, 
                    category: str = "general", duration: float = 3.0) -> bool:
        """Backward compatible method for existing code
        
        This maintains the exact interface of the original FeedbackManager
        while internally using the enhanced system.
        """
        current_time = time.time()
        
        # Check cooldown using adaptive cooldowns
        if category in self.last_feedback_time:
            time_since_last = current_time - self.last_feedback_time[category]
            cooldown = self.adaptive_cooldowns.get(category, 3.0)
            if time_since_last < cooldown:
                return False
        
        # Create basic feedback message (backward compatible)
        feedback = FeedbackMessage(
            message=message,
            priority=priority,
            timestamp=current_time,
            duration=duration,
            category=category
        )
        
        # Add to queues
        self.active_messages.append(feedback)
        self.message_history.append(feedback)
        self.last_feedback_time[category] = current_time
        
        # Update performance metrics
        self.performance_metrics['total_feedback_given'] += 1
        
        return True
    
    def add_intelligent_feedback(self, fault_type: str, severity: str = "mild", 
                               angles: Dict[str, float] = None,
                               rep_count: int = 0, form_score: int = None,
                               force_voice: bool = False) -> bool:
        """Enhanced feedback method with intelligent message generation
        
        This is the new enhanced method that should be used for intelligent feedback.
        
        Args:
            fault_type: Type of fault detected (e.g., 'BACK_ROUNDING', 'INSUFFICIENT_DEPTH')
            severity: Severity level ('mild', 'moderate', 'severe')
            angles: Dictionary of current joint angles
            rep_count: Current repetition count
            form_score: Overall form score (0-100)
            force_voice: Force voice feedback even if voice is normally disabled
        """
        current_time = time.time()
        
        # Map fault type to category for cooldown management
        category = self._map_fault_to_category(fault_type)
        
        # Check adaptive cooldown
        if category in self.last_feedback_time:
            time_since_last = current_time - self.last_feedback_time[category]
            cooldown = self.adaptive_cooldowns.get(category, 3.0)
            
            # Allow critical messages to bypass cooldown
            if severity != 'severe' and time_since_last < cooldown:
                return False
        
        # Update user context
        self.user_context.update_fault_occurrence(fault_type)
        self.user_context.session_rep_count = rep_count
        
        # Create context for message generation
        message_context = {
            'rep_count': rep_count,
            'form_score': form_score,
            'timestamp': current_time,
            'angles': angles or {},
            'fault_frequency': self.user_context.get_fault_frequency(fault_type),
            'skill_level': self.user_context.skill_level
        }
        
        # Generate intelligent message
        enhanced_message = self.message_templates.get_message(
            fault_type=fault_type,
            severity=severity,
            context=message_context,
            voice_mode=False
        )
        
        if not enhanced_message:
            return False
        
        # Update timestamp
        enhanced_message.timestamp = current_time
        
        # Add to queues
        self.active_messages.append(enhanced_message)
        self.message_history.append(enhanced_message)
        self.last_feedback_time[category] = current_time
        
        # Handle voice feedback
        if (self.voice_engine.is_available() and 
            (enhanced_message.voice_message or force_voice) and
            self.user_context.voice_preference):
            
            # Use voice message if available, otherwise use shortened text
            voice_text = enhanced_message.voice_message or enhanced_message.message
            
            # Create a copy for voice with appropriate settings
            voice_message = EnhancedFeedbackMessage(
                message=voice_text,
                priority=enhanced_message.priority,
                timestamp=current_time,
                style=enhanced_message.style,
                voice_message=voice_text,
                interrupt_allowed=enhanced_message.interrupt_allowed
            )
            
            # Queue voice feedback
            voice_delivered = self.voice_engine.speak_message(
                voice_message, 
                force=enhanced_message.interrupt_allowed or force_voice
            )
            
            if voice_delivered:
                enhanced_message.voice_delivered = True
                self.performance_metrics['voice_feedback_given'] += 1
        
        # Update performance tracking
        self.performance_metrics['total_feedback_given'] += 1
        fault_count = self.performance_metrics['faults_detected'].get(fault_type, 0)
        self.performance_metrics['faults_detected'][fault_type] = fault_count + 1
        
        # Adapt cooldowns based on performance
        self._adapt_cooldowns()
        
        return True
    
    def process_pose_analysis(self, faults: List[str], angles: Dict[str, float], 
                            phase: str, rep_count: int, form_score: int = None) -> None:
        """Enhanced version of the original pose analysis processing
        
        This method maintains the original interface while adding intelligent processing.
        """
        
        # Update user context
        self.user_context.session_rep_count = rep_count
        
        # Process each fault with intelligent feedback
        for fault in faults:
            # Determine severity based on context
            severity = self._determine_fault_severity(fault, angles, form_score)
            
            # Generate intelligent feedback
            self.add_intelligent_feedback(
                fault_type=fault,
                severity=severity,
                angles=angles,
                rep_count=rep_count,
                form_score=form_score
            )
        
        # Positive reinforcement for good form
        if not faults and form_score and form_score >= 90:
            self.add_intelligent_feedback(
                fault_type='ENCOURAGEMENT',
                severity='perfect_form',
                rep_count=rep_count,
                form_score=form_score
            )
        
        # Milestone encouragement
        if rep_count > 0 and rep_count % 5 == 0 and len(faults) <= 1:
            self.add_intelligent_feedback(
                fault_type='ENCOURAGEMENT',
                severity='milestone',
                rep_count=rep_count,
                form_score=form_score
            )
    
    def _determine_fault_severity(self, fault: str, angles: Dict[str, float], 
                                 form_score: int = None) -> str:
        """Determine fault severity based on measurements and context"""
        
        if fault == 'BACK_ROUNDING':
            back_angle = angles.get('back', 90)
            if back_angle < 70:
                return 'severe'
            elif back_angle < 80:
                return 'moderate'
            else:
                return 'mild'
        
        elif fault == 'INSUFFICIENT_DEPTH':
            knee_angle = min(angles.get('knee', 180), 
                           angles.get('knee_left', 180), 
                           angles.get('left_knee', 180))
            if knee_angle > 140:  # Very shallow
                return 'micro_movement'
            elif knee_angle > 110:  # Partial depth
                return 'partial'
            else:
                return 'good'
        
        elif fault == 'KNEE_VALGUS':
            # Could add specific angle measurements for knee tracking
            return 'mild'  # Default for now
        
        elif form_score is not None:
            if form_score < 40:
                return 'severe'
            elif form_score < 70:
                return 'moderate'
            else:
                return 'mild'
        
        return 'mild'  # Default severity
    
    def _map_fault_to_category(self, fault_type: str) -> str:
        """Map fault types to categories for cooldown management"""
        
        safety_faults = ['BACK_ROUNDING', 'DANGEROUS_LEAN', 'SEVERE_FORM_BREAKDOWN']
        depth_faults = ['INSUFFICIENT_DEPTH', 'PARTIAL_REP', 'MICRO_MOVEMENT']
        stability_faults = ['KNEE_VALGUS', 'HEEL_RISE', 'ASYMMETRIC_MOVEMENT']
        tempo_faults = ['TOO_FAST', 'TOO_SLOW', 'INCONSISTENT_TEMPO']
        technique_faults = ['FORWARD_LEAN', 'BUTT_WINK', 'SHALLOW_BREATHING']
        motivation_faults = ['ENCOURAGEMENT', 'MILESTONE', 'PERFECT_FORM']
        
        if fault_type in safety_faults:
            return "safety"
        elif fault_type in depth_faults:
            return "depth"
        elif fault_type in stability_faults:
            return "stability"
        elif fault_type in tempo_faults:
            return "tempo"
        elif fault_type in technique_faults:
            return "technique"
        elif fault_type in motivation_faults:
            return "motivation"
        else:
            return "form"  # Default category
    
    def _adapt_cooldowns(self):
        """Adapt cooldown periods based on user performance and progress"""
        
        total_feedback = self.performance_metrics['total_feedback_given']
        
        # Only adapt after sufficient data
        if total_feedback < 10:
            return
        
        # Calculate error rate for each category
        session_duration = time.time() - self.performance_metrics['session_start_time']
        feedback_rate = total_feedback / max(session_duration / 60, 1)  # per minute
        
        # If user is getting lots of feedback (high error rate), reduce cooldowns
        if feedback_rate > 8:  # More than 8 feedbacks per minute = struggling
            for category in self.adaptive_cooldowns:
                self.adaptive_cooldowns[category] = self.base_cooldown_periods[category] * 0.7
        
        # If user is doing well (low feedback rate), increase cooldowns
        elif feedback_rate < 3:  # Less than 3 feedbacks per minute = doing well
            for category in self.adaptive_cooldowns:
                self.adaptive_cooldowns[category] = self.base_cooldown_periods[category] * 1.3
        
        # Reset to base if in middle range
        else:
            self.adaptive_cooldowns = self.base_cooldown_periods.copy()
    
    def get_current_feedback(self) -> List[Union[FeedbackMessage, EnhancedFeedbackMessage]]:
        """Get current active feedback messages (backward compatible)"""
        current_time = time.time()
        
        # Remove expired messages
        active = [msg for msg in self.active_messages 
                 if current_time - msg.timestamp < msg.duration]
        
        # Sort by priority (lower number = higher priority)
        # Handle both old and new message types
        def get_priority(msg):
            if hasattr(msg, 'style') and msg.style == FeedbackStyle.URGENT:
                return 0  # Urgent messages always first
            return msg.priority
        
        active.sort(key=get_priority)
        
        # Return max 2 messages to avoid clutter
        return active[:2]
    
    def announce_session_start(self):
        """Announce the start of a workout session"""
        session_message = self.message_templates.get_session_message(
            'session_start',
            context={'timestamp': time.time()}
        )
        
        if session_message:
            self.active_messages.append(session_message)
            
            if self.voice_engine.is_available() and self.user_context.voice_preference:
                self.voice_engine.speak_immediate(
                    session_message.voice_message or session_message.message,
                    style=FeedbackStyle.MOTIVATIONAL
                )
    
    def announce_session_end(self, total_reps: int, avg_score: float):
        """Announce the end of a workout session"""
        session_message = self.message_templates.get_session_message(
            'session_end',
            context={
                'total_reps': total_reps,
                'avg_score': avg_score,
                'timestamp': time.time()
            }
        )
        
        if session_message:
            self.active_messages.append(session_message)
            
            if self.voice_engine.is_available() and self.user_context.voice_preference:
                self.voice_engine.speak_immediate(
                    session_message.voice_message or session_message.message,
                    style=FeedbackStyle.MOTIVATIONAL
                )
    
    # Maintain backward compatibility methods
    def clear_messages(self):
        """Clear all active messages (backward compatible)"""
        self.active_messages.clear()
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get comprehensive feedback statistics"""
        return {
            'total_messages': len(self.message_history),
            'active_messages': len(self.active_messages),
            'voice_available': self.voice_engine.is_available(),
            'voice_enabled': self.user_context.voice_preference,
            'performance_metrics': self.performance_metrics,
            'adaptive_cooldowns': self.adaptive_cooldowns,
            'user_context': {
                'skill_level': self.user_context.skill_level,
                'session_rep_count': self.user_context.session_rep_count,
                'fault_frequency': self.user_context.fault_frequency
            }
        }
    
    def adjust_sensitivity(self, sensitivity_level: float):
        """Adjust feedback sensitivity (1.0 = normal, 0.5 = less frequent, 2.0 = more frequent)"""
        for category in self.adaptive_cooldowns:
            self.adaptive_cooldowns[category] = self.base_cooldown_periods[category] / sensitivity_level
    
    def set_voice_enabled(self, enabled: bool):
        """Enable or disable voice feedback"""
        self.user_context.voice_preference = enabled
        self.voice_engine.set_enabled(enabled)
    
    def set_user_skill_level(self, skill_level: str):
        """Update user skill level for adaptive feedback"""
        self.user_context.skill_level = skill_level
    
    def shutdown(self):
        """Gracefully shutdown the feedback system"""
        if self.voice_engine:
            self.voice_engine.shutdown()
        print("✅ Enhanced feedback manager shutdown complete")
