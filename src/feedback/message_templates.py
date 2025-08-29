"""
Intelligent Message Templates for AI Fitness Coach

This module manages all feedback message templates with smart selection logic,
anti-repetition mechanisms, and context-aware message generation.
"""

import random
from typing import Dict, List, Optional, Any
from .feedback_types import FeedbackPriority, FeedbackStyle, MessageCategory, EnhancedFeedbackMessage

class MessageTemplateManager:
    """Manages feedback message templates with intelligent selection and anti-repetition"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.usage_history = {}  # Track recent message usage to avoid repetition
        self.max_history_length = 10  # Remember last 10 messages per fault type
    
    def _initialize_templates(self) -> Dict[str, Dict]:
        """Initialize comprehensive message templates organized by fault and severity"""
        return {
            'BACK_ROUNDING': {
                'category': MessageCategory.SAFETY,
                'base_priority': FeedbackPriority.HIGH,
                'severity_levels': {
                    'mild': {
                        'priority': FeedbackPriority.MEDIUM,
                        'style': FeedbackStyle.INSTRUCTIONAL,
                        'text_messages': [
                            "Lift your chest slightly for better posture",
                            "Keep a proud chest position throughout",
                            "Imagine someone gently pulling your shoulders back",
                            "Focus on maintaining that natural spine curve",
                            "Engage your core to support your spine"
                        ],
                        'voice_messages': [
                            "Chest up",
                            "Straighten back",
                            "Better posture",
                            "Core engaged",
                            "Shoulders back"
                        ]
                    },
                    'moderate': {
                        'priority': FeedbackPriority.HIGH,
                        'style': FeedbackStyle.CORRECTIVE,
                        'text_messages': [
                            "⚠️ Your back is rounding - lift that chest!",
                            "⚠️ Dangerous back position - straighten up now",
                            "⚠️ Your spine needs protection - engage your core",
                            "⚠️ Back rounding detected - focus on posture"
                        ],
                        'voice_messages': [
                            "Warning: straighten your back",
                            "Back rounding detected",
                            "Chest up immediately",
                            "Dangerous back position"
                        ]
                    },
                    'severe': {
                        'priority': FeedbackPriority.CRITICAL,
                        'style': FeedbackStyle.URGENT,
                        'interrupt_allowed': True,
                        'text_messages': [
                            "🚨 STOP - Critical back rounding detected!",
                            "🚨 DANGEROUS spine position - straighten immediately!",
                            "🚨 Your back is at risk - end the rep now!",
                            "🚨 Critical form failure - protect your spine!"
                        ],
                        'voice_messages': [
                            "Stop! Dangerous back position!",
                            "Critical spine error!",
                            "End the rep now!",
                            "Protect your spine!"
                        ]
                    }
                }
            },
            
            'INSUFFICIENT_DEPTH': {
                'category': MessageCategory.DEPTH,
                'base_priority': FeedbackPriority.MEDIUM,
                'severity_levels': {
                    'micro_movement': {
                        'priority': FeedbackPriority.HIGH,
                        'style': FeedbackStyle.CORRECTIVE,
                        'text_messages': [
                            "That's barely a knee bend - squat means SIT DOWN!",
                            "You need to actually lower your body significantly",
                            "Real squats require real movement - go much deeper!",
                            "This isn't a squat yet - sit back and down!"
                        ],
                        'voice_messages': [
                            "Go much deeper!",
                            "That's not a squat!",
                            "Sit down properly!",
                            "Real movement needed!"
                        ]
                    },
                    'partial': {
                        'priority': FeedbackPriority.MEDIUM,
                        'style': FeedbackStyle.ENCOURAGING,
                        'text_messages': [
                            "Good start! Now aim for thighs parallel to ground",
                            "You're moving well - just need more depth",
                            "Almost there - another few inches down",
                            "Nice progress - push for full range of motion"
                        ],
                        'voice_messages': [
                            "Go deeper",
                            "More depth needed",
                            "Almost there",
                            "Keep going down"
                        ]
                    },
                    'good': {
                        'priority': FeedbackPriority.LOW,
                        'style': FeedbackStyle.ENCOURAGING,
                        'text_messages': [
                            "Excellent depth! That's a real squat!",
                            "Perfect range of motion - muscles fully activated!",
                            "Outstanding depth control!",
                            "That's how squats should look!"
                        ],
                        'voice_messages': [
                            "Perfect depth!",
                            "Excellent squat!",
                            "Outstanding form!",
                            "Perfect range!"
                        ]
                    }
                }
            },
            
            'KNEE_VALGUS': {
                'category': MessageCategory.STABILITY,
                'base_priority': FeedbackPriority.HIGH,
                'severity_levels': {
                    'mild': {
                        'priority': FeedbackPriority.MEDIUM,
                        'style': FeedbackStyle.INSTRUCTIONAL,
                        'text_messages': [
                            "Push your knees out over your toes",
                            "Don't let those knees cave inward",
                            "Think 'knees track over toes'",
                            "Focus on knee alignment throughout the movement"
                        ],
                        'voice_messages': [
                            "Knees out",
                            "Don't cave inward",
                            "Better tracking",
                            "Knees over toes"
                        ]
                    },
                    'severe': {
                        'priority': FeedbackPriority.HIGH,
                        'style': FeedbackStyle.CORRECTIVE,
                        'text_messages': [
                            "⚠️ Knees caving dangerously - push them OUT!",
                            "⚠️ Your knee stability is compromised",
                            "⚠️ Force those knees out over your toes",
                            "⚠️ Knee valgus detected - engage your glutes!"
                        ],
                        'voice_messages': [
                            "Knees out immediately!",
                            "Dangerous knee position!",
                            "Push knees out!",
                            "Engage glutes!"
                        ]
                    }
                }
            },
            
            'FORWARD_LEAN': {
                'category': MessageCategory.TECHNIQUE,
                'base_priority': FeedbackPriority.MEDIUM,
                'severity_levels': {
                    'mild': {
                        'priority': FeedbackPriority.MEDIUM,
                        'style': FeedbackStyle.INSTRUCTIONAL,
                        'text_messages': [
                            "Try to stay more upright - less forward lean",
                            "Keep your torso more vertical",
                            "Sit back more, lean forward less",
                            "Focus on keeping your chest up and back"
                        ],
                        'voice_messages': [
                            "More upright",
                            "Less forward lean",
                            "Sit back more",
                            "Vertical torso"
                        ]
                    }
                }
            },
            
            'ASYMMETRIC_MOVEMENT': {
                'category': MessageCategory.SYMMETRY,
                'base_priority': FeedbackPriority.MEDIUM,
                'severity_levels': {
                    'mild': {
                        'priority': FeedbackPriority.MEDIUM,
                        'style': FeedbackStyle.INSTRUCTIONAL,
                        'text_messages': [
                            "Balance your movement - both sides equal",
                            "Your left and right sides are uneven",
                            "Focus on symmetrical movement",
                            "Make sure both legs work equally"
                        ],
                        'voice_messages': [
                            "Balance both sides",
                            "Uneven movement",
                            "Equal effort",
                            "Symmetrical motion"
                        ]
                    }
                }
            },
            
            'HEEL_RISE': {
                'category': MessageCategory.STABILITY,
                'base_priority': FeedbackPriority.MEDIUM,
                'severity_levels': {
                    'mild': {
                        'priority': FeedbackPriority.MEDIUM,
                        'style': FeedbackStyle.INSTRUCTIONAL,
                        'text_messages': [
                            "Keep your heels planted on the ground",
                            "Don't let your heels come up",
                            "Maintain contact between heels and floor",
                            "Root through your whole foot"
                        ],
                        'voice_messages': [
                            "Heels down",
                            "Don't rise up",
                            "Plant your feet",
                            "Whole foot contact"
                        ]
                    }
                }
            },
            
            'TOO_FAST': {
                'category': MessageCategory.TEMPO,
                'base_priority': FeedbackPriority.MEDIUM,
                'severity_levels': {
                    'mild': {
                        'priority': FeedbackPriority.MEDIUM,
                        'style': FeedbackStyle.INSTRUCTIONAL,
                        'text_messages': [
                            "Slow down - control the movement",
                            "Quality over speed - take your time",
                            "Think '2 seconds down, 1 second up'",
                            "Controlled movement builds better strength"
                        ],
                        'voice_messages': [
                            "Slow down",
                            "Control the movement",
                            "Take your time",
                            "Quality over speed"
                        ]
                    }
                }
            },
            
            'ENCOURAGEMENT': {
                'category': MessageCategory.MOTIVATION,
                'base_priority': FeedbackPriority.LOW,
                'severity_levels': {
                    'general': {
                        'priority': FeedbackPriority.LOW,
                        'style': FeedbackStyle.MOTIVATIONAL,
                        'text_messages': [
                            "You're doing great - keep pushing!",
                            "Strong work! Your form is improving!",
                            "Excellent effort - consistency pays off!",
                            "Your dedication is showing results!",
                            "Power through - you've got this!",
                            "Quality reps building quality strength!"
                        ],
                        'voice_messages': [
                            "Keep it up!",
                            "You've got this!",
                            "Strong work!",
                            "Excellent effort!",
                            "Great job!",
                            "Keep pushing!"
                        ]
                    },
                    'milestone': {
                        'priority': FeedbackPriority.LOW,
                        'style': FeedbackStyle.MOTIVATIONAL,
                        'text_messages': [
                            "Milestone reached! {rep_count} reps completed!",
                            "Halfway there - momentum is building!",
                            "New personal record - {total_reps} total reps!",
                            "Consistency champion - great work!"
                        ],
                        'voice_messages': [
                            "{rep_count} reps done!",
                            "Milestone reached!",
                            "Great progress!",
                            "Keep the momentum!"
                        ]
                    },
                    'perfect_form': {
                        'priority': FeedbackPriority.LOW,
                        'style': FeedbackStyle.ENCOURAGING,
                        'text_messages': [
                            "Perfect form! Keep it up!",
                            "Textbook squat - excellent!",
                            "Your technique is spot on!",
                            "Outstanding movement quality!",
                            "That's exactly how it should look!"
                        ],
                        'voice_messages': [
                            "Perfect form!",
                            "Excellent technique!",
                            "Spot on!",
                            "Outstanding!",
                            "Perfect squat!"
                        ]
                    }
                }
            }
        }
    
    def get_message(self, fault_type: str, severity: str = "mild", 
                   context: Dict[str, Any] = None, 
                   voice_mode: bool = False) -> Optional[EnhancedFeedbackMessage]:
        """Generate appropriate message based on fault type, severity, and context"""
        
        # Get template for this fault type
        template = self.templates.get(fault_type.upper())
        if not template:
            return self._generate_fallback_message(fault_type, severity, voice_mode)
        
        # Get severity level data
        severity_data = template.get('severity_levels', {}).get(severity)
        if not severity_data:
            # Fallback to first available severity level
            available_severities = list(template.get('severity_levels', {}).keys())
            if available_severities:
                severity_data = template['severity_levels'][available_severities[0]]
                severity = available_severities[0]
            else:
                return self._generate_fallback_message(fault_type, severity, voice_mode)
        
        # Select message text (voice or text)
        if voice_mode:
            message_pool = severity_data.get('voice_messages', severity_data.get('text_messages', []))
        else:
            message_pool = severity_data.get('text_messages', [])
        
        if not message_pool:
            return self._generate_fallback_message(fault_type, severity, voice_mode)
        
        # Select non-repetitive message
        selected_text = self._select_non_repetitive_message(fault_type, message_pool)
        
        # Format with context if provided
        if context:
            try:
                selected_text = selected_text.format(**context)
            except (KeyError, ValueError):
                pass  # Use message as-is if formatting fails
        
        # Create voice message if not in voice mode but voice is needed
        voice_message = None
        if not voice_mode:
            voice_pool = severity_data.get('voice_messages', [])
            if voice_pool:
                voice_message = self._select_non_repetitive_message(f"{fault_type}_voice", voice_pool)
                if context and voice_message:
                    try:
                        voice_message = voice_message.format(**context)
                    except (KeyError, ValueError):
                        pass
        
        # Create enhanced feedback message
        return EnhancedFeedbackMessage(
            message=selected_text,
            priority=severity_data.get('priority', FeedbackPriority.MEDIUM).value,
            timestamp=context.get('timestamp', 0) if context else 0,
            duration=self._determine_duration(severity_data),
            category=template.get('category', MessageCategory.TECHNIQUE).value,
            style=severity_data.get('style', FeedbackStyle.INSTRUCTIONAL),
            voice_message=voice_message,
            severity_level=severity,
            fault_type=fault_type,
            interrupt_allowed=severity_data.get('interrupt_allowed', False),
            user_context=context or {}
        )
    
    def _select_non_repetitive_message(self, fault_key: str, message_pool: List[str]) -> str:
        """Select a message while avoiding recent repetitions"""
        
        # Initialize history for this fault if not exists
        if fault_key not in self.usage_history:
            self.usage_history[fault_key] = []
        
        recent_messages = self.usage_history[fault_key]
        
        # Filter out recently used messages
        available_messages = [msg for msg in message_pool if msg not in recent_messages[-3:]]
        
        # If all messages were recently used, reset history and use any
        if not available_messages:
            available_messages = message_pool
            self.usage_history[fault_key] = []
        
        # Select message randomly from available pool
        selected = random.choice(available_messages)
        
        # Update usage history
        self.usage_history[fault_key].append(selected)
        
        # Trim history to prevent unlimited growth
        if len(self.usage_history[fault_key]) > self.max_history_length:
            self.usage_history[fault_key] = self.usage_history[fault_key][-self.max_history_length:]
        
        return selected
    
    def _determine_duration(self, severity_data: Dict) -> float:
        """Determine how long the message should be displayed"""
        style = severity_data.get('style', FeedbackStyle.INSTRUCTIONAL)
        
        if style == FeedbackStyle.URGENT:
            return 5.0  # Urgent messages stay longer
        elif style == FeedbackStyle.MOTIVATIONAL:
            return 2.5  # Motivational messages can be shorter
        else:
            return 3.0  # Default duration
    
    def _generate_fallback_message(self, fault_type: str, severity: str, voice_mode: bool) -> EnhancedFeedbackMessage:
        """Generate a basic fallback message for unknown fault types"""
        
        clean_fault = fault_type.replace('_', ' ').lower()
        
        if voice_mode:
            message = f"Improve {clean_fault}"
        else:
            message = f"Work on improving your {clean_fault}"
        
        return EnhancedFeedbackMessage(
            message=message,
            priority=FeedbackPriority.MEDIUM.value,
            timestamp=0,
            duration=3.0,
            category=MessageCategory.TECHNIQUE.value,
            style=FeedbackStyle.INSTRUCTIONAL,
            voice_message=f"Improve {clean_fault}" if not voice_mode else None,
            severity_level=severity,
            fault_type=fault_type
        )
    
    def get_session_message(self, message_type: str, context: Dict[str, Any] = None) -> Optional[EnhancedFeedbackMessage]:
        """Get session-level messages (start, progress, completion)"""
        
        session_templates = {
            'session_start': {
                'text': [
                    "Welcome to your squat session! Let's build some strength!",
                    "Ready to crush this workout? Form and control first!",
                    "Session starting - remember quality over quantity!",
                    "Time to get stronger! Focus on perfect form!"
                ],
                'voice': [
                    "Let's get started!",
                    "Welcome to your workout!",
                    "Time to build strength!",
                    "Session beginning!"
                ]
            },
            'session_end': {
                'text': [
                    "Session complete! {total_reps} quality reps - outstanding work!",
                    "Excellent session! Your form stayed strong throughout!",
                    "Mission accomplished! {avg_score:.0f}% average form score!",
                    "Another step stronger! Great consistency today!"
                ],
                'voice': [
                    "Session complete! Great work!",
                    "Excellent effort today!",
                    "Mission accomplished!",
                    "Outstanding session!"
                ]
            }
        }
        
        template = session_templates.get(message_type)
        if not template:
            return None
        
        # Select message
        text_msg = random.choice(template['text'])
        voice_msg = random.choice(template['voice'])
        
        # Format with context
        if context:
            try:
                text_msg = text_msg.format(**context)
                voice_msg = voice_msg.format(**context)
            except (KeyError, ValueError):
                pass
        
        return EnhancedFeedbackMessage(
            message=text_msg,
            priority=FeedbackPriority.INFO.value,
            timestamp=context.get('timestamp', 0) if context else 0,
            duration=4.0,
            category=MessageCategory.SESSION.value,
            style=FeedbackStyle.MOTIVATIONAL,
            voice_message=voice_msg,
            severity_level='info',
            fault_type=message_type
        )
