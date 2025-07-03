import json
import os
from pathlib import Path

class ConfigManager:
    """Manages application configuration and user preferences"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".ai_fitness_coach"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "analysis_settings": {
                "confidence_threshold": 0.7,
                "back_angle_threshold": 25,
                "knee_depth_threshold": 90,
                "symmetry_threshold": 15,
                "feedback_frequency": "Medium",
                "show_angles": True,
                "show_skeleton": True,
                "smoothing_frames": 5,
                "min_frames_for_fault": 3
            },
            "ui_settings": {
                "window_width": 1600,
                "window_height": 1000,
                "auto_save_sessions": True,
                "show_tips": True
            },
            "session_settings": {
                "auto_export": False,
                "export_format": "json",
                "save_video_recordings": False
            }
        }
        
        self.ensure_config_exists()
    
    def ensure_config_exists(self):
        """Ensure config directory and file exist"""
        self.config_dir.mkdir(exist_ok=True)
        
        if not self.config_file.exists():
            self.save_config(self.default_config)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            merged_config = self._merge_configs(self.default_config, config)
            return merged_config
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading config: {e}. Using defaults.")
            return self.default_config.copy()
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _merge_configs(self, default, user):
        """Recursively merge user config with defaults"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_analysis_settings(self):
        """Get analysis settings"""
        config = self.load_config()
        return config.get("analysis_settings", self.default_config["analysis_settings"])
    
    def update_analysis_settings(self, settings):
        """Update analysis settings"""
        config = self.load_config()
        config["analysis_settings"].update(settings)
        return self.save_config(config)
    
    def get_ui_settings(self):
        """Get UI settings"""
        config = self.load_config()
        return config.get("ui_settings", self.default_config["ui_settings"])
    
    def update_ui_settings(self, settings):
        """Update UI settings"""
        config = self.load_config()
        config["ui_settings"].update(settings)
        return self.save_config(config)
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        return self.save_config(self.default_config.copy())
