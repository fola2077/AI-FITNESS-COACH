"""
Voice Feedback Engine for AI Fitness Coach

This module handles text-to-speech functionality with intelligent voice management,
queue processing, and adaptive voice settings based on feedback context.
"""

import threading
import queue
import time
from typing import Optional, Dict, Any
from .feedback_types import FeedbackStyle, EnhancedFeedbackMessage

class VoiceFeedbackEngine:
    """Voice feedback engine with intelligent TTS management"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.engine = None
        self.use_powershell = False  # Flag for PowerShell TTS
        self.speech_queue = queue.Queue(maxsize=10)  # Prevent queue overflow
        self.is_speaking = False
        self.current_priority = 999  # Lower number = higher priority
        self.speech_thread = None
        
        # Load user voice configuration
        self.voice_config = self._load_voice_config()
        
        # Voice settings for different styles
        self.voice_settings = {
            FeedbackStyle.URGENT: {"rate": self.voice_config['rate'], "volume": min(100, self.voice_config['volume'] + 5)},
            FeedbackStyle.CORRECTIVE: {"rate": self.voice_config['rate'], "volume": self.voice_config['volume']},
            FeedbackStyle.INSTRUCTIONAL: {"rate": self.voice_config['rate'], "volume": self.voice_config['volume']},
            FeedbackStyle.ENCOURAGING: {"rate": max(-2, self.voice_config['rate'] - 1), "volume": self.voice_config['volume']},
            FeedbackStyle.MOTIVATIONAL: {"rate": self.voice_config['rate'], "volume": min(100, self.voice_config['volume'] + 3)}
        }
        
        if self.enabled:
            self._initialize_engine()
    
    def _load_voice_config(self) -> dict:
        """Load voice configuration from file or use defaults"""
        default_config = {
            'voice_name': 'Microsoft Zira Desktop',
            'rate': 0,
            'volume': 90,
            'style': 'coaching'
        }
        
        try:
            import os
            config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'voice_config.txt')
            if os.path.exists(config_file):
                config = {}
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Convert numeric values
                            if key in ['rate', 'volume']:
                                try:
                                    config[key] = int(value)
                                except ValueError:
                                    config[key] = default_config[key]
                            else:
                                config[key] = value
                
                # Merge with defaults for any missing keys
                for key, default_value in default_config.items():
                    if key not in config:
                        config[key] = default_value
                
                print(f"✅ Loaded voice config: {config['voice_name']} (Rate: {config['rate']}, Volume: {config['volume']})")
                return config
            else:
                print("⚠️ No voice config found, using defaults")
                return default_config
                
        except Exception as e:
            print(f"⚠️ Error loading voice config: {e}, using defaults")
            return default_config
    
    def _initialize_engine(self):
        """Initialize the TTS engine with error handling"""
        try:
            import pyttsx3
            
            # First, try to use PowerShell TTS (our working solution)
            if self._test_powershell_tts():
                self.use_powershell = True
                print("✅ Voice feedback engine initialized with PowerShell TTS")
                self._start_speech_worker()
                return
            
            # Fallback to pyttsx3 if PowerShell fails
            self.engine = pyttsx3.init()
            
            # Set default properties
            self.engine.setProperty('rate', 145)  # Words per minute
            self.engine.setProperty('volume', 0.85)  # Volume level (0.0 to 1.0)
            
            # Try to set a pleasant voice (prefer female for fitness coaching)
            voices = self.engine.getProperty('voices')
            if voices:
                for voice in voices:
                    # Look for female voices (common names: Zira, Hazel, etc.)
                    if any(name in voice.name.lower() for name in ['female', 'zira', 'hazel', 'aria']):
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Fallback to first available voice
                    self.engine.setProperty('voice', voices[0].id)
            
            # Start the speech worker thread
            self._start_speech_worker()
            
            print("✅ Voice feedback engine initialized with pyttsx3")
            
        except ImportError:
            print("⚠️ pyttsx3 not installed. Voice feedback disabled.")
            print("   Install with: pip install pyttsx3")
            self.enabled = False
        except Exception as e:
            print(f"❌ Voice engine initialization failed: {e}")
            self.enabled = False
    
    def _test_powershell_tts(self) -> bool:
        """Test if PowerShell TTS is available"""
        try:
            import subprocess
            # Test PowerShell TTS with a quick silent test
            cmd = [
                'powershell', '-Command',
                'Add-Type -AssemblyName System.Speech; ' +
                '$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; ' +
                '$synth.SetOutputToNull(); ' +
                '$synth.Speak("test"); ' +
                '$synth.Dispose()'
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def _speak_with_powershell(self, message: str) -> bool:
        """Speak message using PowerShell TTS with user-selected voice and settings"""
        try:
            import subprocess
            voice_name = self.voice_config['voice_name']
            rate = self.voice_config['rate']
            volume = self.voice_config['volume']
            
            # Extract the key part of the voice name for matching
            voice_key = voice_name.split()[1] if len(voice_name.split()) > 1 else voice_name
            
            cmd = [
                'powershell', '-Command',
                f'Add-Type -AssemblyName System.Speech; ' +
                f'$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; ' +
                f'$voices = $synth.GetInstalledVoices(); ' +
                f'$targetVoice = $voices | Where-Object {{ $_.VoiceInfo.Name -like "*{voice_key}*" }}; ' +
                f'if ($targetVoice) {{ ' +
                f'    $synth.SelectVoice($targetVoice.VoiceInfo.Name); ' +
                f'}} else {{ ' +
                f'    Write-Host "Target voice not found, using default"; ' +
                f'}}; ' +
                f'$synth.Rate = {rate}; ' +
                f'$synth.Volume = {volume}; ' +
                f'$synth.Speak("{message}"); ' +
                f'$synth.Dispose()'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ PowerShell TTS failed: {e}")
            return False
    
    def _start_speech_worker(self):
        """Start background thread for non-blocking speech processing"""
        def speech_worker():
            """Worker thread that processes speech queue"""
            while True:
                try:
                    # Get speech item from queue (blocking with timeout)
                    speech_item = self.speech_queue.get(timeout=1.0)
                    
                    # Check for shutdown signal
                    if speech_item is None:
                        break
                    
                    message, priority, style = speech_item
                    
                    # Skip if a higher priority message is already being spoken
                    if priority > self.current_priority and self.is_speaking:
                        self.speech_queue.task_done()
                        continue
                    
                    # Update current priority and speaking status
                    self.current_priority = priority
                    self.is_speaking = True
                    
                    # Apply voice settings for the style
                    self._apply_voice_settings(style)
                    
                    # Speak the message
                    if self.use_powershell:
                        self._speak_with_powershell(message)
                    elif self.engine:
                        self.engine.say(message)
                        self.engine.runAndWait()
                    
                    # Reset speaking status
                    self.is_speaking = False
                    self.current_priority = 999
                    
                    # Mark task as done
                    self.speech_queue.task_done()
                    
                except queue.Empty:
                    # Timeout occurred, continue loop
                    continue
                except Exception as e:
                    print(f"❌ Speech worker error: {e}")
                    self.is_speaking = False
                    self.current_priority = 999
        
        if self.enabled and self.engine:
            self.speech_thread = threading.Thread(target=speech_worker, daemon=True)
            self.speech_thread.start()
    
    def _apply_voice_settings(self, style: FeedbackStyle):
        """Apply voice settings based on feedback style"""
        if not self.engine:
            return
        
        settings = self.voice_settings.get(style, self.voice_settings[FeedbackStyle.INSTRUCTIONAL])
        
        try:
            self.engine.setProperty('rate', settings['rate'])
            self.engine.setProperty('volume', settings['volume'])
        except Exception as e:
            print(f"⚠️ Failed to apply voice settings: {e}")
    
    def speak_message(self, feedback_message: EnhancedFeedbackMessage, force: bool = False):
        """Queue a feedback message for speech delivery
        
        Args:
            feedback_message: The feedback message to speak
            force: If True, interrupt current speech for urgent messages
        """
        if not self.enabled or not feedback_message.voice_message:
            return False
        
        # Clean the message for better speech synthesis
        clean_message = self._clean_message_for_speech(feedback_message.voice_message)
        
        # Handle urgent interruptions
        if force or feedback_message.interrupt_allowed:
            self._clear_queue()
        
        # Queue the message
        try:
            speech_item = (clean_message, feedback_message.priority, feedback_message.style)
            self.speech_queue.put(speech_item, timeout=0.1)
            return True
        except queue.Full:
            print("⚠️ Voice feedback queue full - message dropped")
            return False
    
    def speak_immediate(self, message: str, style: FeedbackStyle = FeedbackStyle.INSTRUCTIONAL, priority: int = 1):
        """Speak a message immediately, bypassing the queue for urgent announcements"""
        if not self.enabled:
            return False
        
        clean_message = self._clean_message_for_speech(message)
        
        # Clear queue and speak immediately
        self._clear_queue()
        
        try:
            self._apply_voice_settings(style)
            if self.use_powershell:
                self._speak_with_powershell(clean_message)
            elif self.engine:
                self.engine.say(clean_message)
                self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"❌ Immediate speech failed: {e}")
            return False
    
    def _clean_message_for_speech(self, message: str) -> str:
        """Clean message text for better speech synthesis"""
        if not message:
            return ""
        
        import re
        
        # Remove emojis and special characters that don't speak well
        clean_msg = re.sub(r'[🚨⚠️❌✅📊💪🎯🔊🔇]', '', message)
        
        # Remove excessive punctuation
        clean_msg = re.sub(r'[!]{2,}', '!', clean_msg)
        clean_msg = re.sub(r'[?]{2,}', '?', clean_msg)
        
        # Replace common abbreviations and symbols for better pronunciation
        replacements = {
            '°': ' degrees',
            '%': ' percent',
            '&': ' and',
            'vs': 'versus',
            'w/': 'with',
            'reps': 'repetitions',
            'rep': 'repetition',
            'ROM': 'range of motion',
            'TTS': 'text to speech'
        }
        
        for old, new in replacements.items():
            clean_msg = clean_msg.replace(old, new)
        
        # Normalize whitespace
        clean_msg = ' '.join(clean_msg.split())
        
        # Ensure reasonable length for speech (max ~50 characters for quick feedback)
        if len(clean_msg) > 50:
            # Try to truncate at sentence boundary
            sentences = clean_msg.split('. ')
            if len(sentences) > 1 and len(sentences[0]) <= 50:
                clean_msg = sentences[0]
            else:
                # Truncate at word boundary
                words = clean_msg.split()
                truncated = []
                char_count = 0
                for word in words:
                    if char_count + len(word) + 1 > 50:
                        break
                    truncated.append(word)
                    char_count += len(word) + 1
                clean_msg = ' '.join(truncated)
        
        return clean_msg.strip()
    
    def _clear_queue(self):
        """Clear pending speech messages for urgent interruptions"""
        try:
            while True:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
        except queue.Empty:
            pass
    
    def set_enabled(self, enabled: bool):
        """Enable or disable voice feedback"""
        if enabled and not self.engine:
            # Try to re-initialize if it was disabled due to missing dependencies
            self._initialize_engine()
        
        self.enabled = enabled and self.engine is not None
        
        if not self.enabled:
            self._clear_queue()
    
    def is_available(self) -> bool:
        """Check if voice feedback is available and working"""
        return self.enabled and (self.use_powershell or self.engine is not None)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current voice engine status for debugging"""
        return {
            'enabled': self.enabled,
            'engine_available': self.engine is not None,
            'powershell_tts': self.use_powershell,
            'is_speaking': self.is_speaking,
            'queue_size': self.speech_queue.qsize(),
            'current_priority': self.current_priority
        }
    
    def shutdown(self):
        """Shutdown the voice feedback system gracefully"""
        if self.enabled:
            # Signal shutdown to worker thread
            try:
                self.speech_queue.put(None, timeout=1.0)
            except queue.Full:
                pass
            
            # Clear remaining messages
            self._clear_queue()
            
            # Wait for thread to finish (with timeout)
            if self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=2.0)
            
            print("✅ Voice feedback engine shutdown complete")
