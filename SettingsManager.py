"""
SettingsManager.py
Manages application settings stored in settings.json.
Loads, saves, and provides access to user-configurable settings.
Creates default settings file if none exists.
"""

import json
import os
from pathlib import Path
from logger import log_info, log_warning, log_error


class SettingsManager:
    """
    Manages persistent application settings.
    Settings are stored in settings.json and loaded at startup.
    """
    
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.settings = {}
        self._load_settings()
    
    def _get_default_settings(self):
        """
        Get default settings from config.py values.
        These are used when settings.json doesn't exist.
        
        Returns:
            dict: Default settings dictionary
        """
        return {
            # Camera Settings
            "CAMERA_URL": 0,
            "FLIP_HORIZONTAL": 1,
            "CAPTURE_FRAME_COUNT": 3,
            "LIVE_DETECTION_FRAME_SKIP": 100,
            
            # Google Drive Settings
            "GOOGLE_DRIVE_FOLDER_URL": "https://drive.google.com/drive/folders/1pZBcKW5CpQORjYXAnPZrHHeV0MtWNTHx",
            
            # Recognition Settings
            "CONFIDENCE_THRESHOLD": 0.5,
            "MIN_FACE_SIZE": 20,
            "MTCNN_MIN_FACE_SIZE": 20,
            "MTCNN_SCALE_FACTOR": 0.709,
            
            # Attendance Settings
            "ATTENDANCE_MARK": "✓",
            
            # Directory Paths (relative to exe location)
            "FACES_DIR": "Faces",
            "MODELS_DIR": "Models",
            "DOWNLOADS_DIR": "Downloaded_Faces",
            "ATTENDANCE_DATA_DIR": "Attendance_Data",
            
            # UI Settings
            "WINDOW_WIDTH": 900,
            "WINDOW_HEIGHT": 700,
        }
    
    def _load_settings(self):
        """
        Load settings from settings.json.
        If file doesn't exist or is corrupted, create from defaults.
        """
        if not os.path.exists(self.settings_file):
            log_info(f"Settings file not found. Creating default settings...")
            self.settings = self._get_default_settings()
            self._save_settings()
        else:
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                
                # Merge with defaults to add any new settings
                defaults = self._get_default_settings()
                for key, value in defaults.items():
                    if key not in self.settings:
                        self.settings[key] = value
                
                log_info(f"Settings loaded from {self.settings_file}")
                
            except (json.JSONDecodeError, Exception) as e:
                log_error(f"Error loading settings", e)
                log_warning("Using default settings...")
                self.settings = self._get_default_settings()
                self._save_settings()
    
    def _save_settings(self):
        """
        Save current settings to settings.json.
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            log_info(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            log_error(f"Error saving settings", e)
            return False
    
    def get(self, key, default=None):
        """
        Get a setting value by key.
        
        Args:
            key: Setting key (e.g., 'CAMERA_URL')
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """
        Set a setting value.
        Does NOT save to file automatically - call save() after.
        
        Args:
            key: Setting key
            value: Setting value
        """
        old_value = self.settings.get(key)
        self.settings[key] = value
        if old_value != value:
            log_info(f"Setting changed: {key}={value}")
    
    def save(self):
        """
        Save current settings to file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self._save_settings()
    
    def reset_to_defaults(self):
        """
        Reset all settings to default values.
        Does NOT save automatically - call save() after.
        """
        log_warning("Settings reset to defaults")
        self.settings = self._get_default_settings()
    
    def get_all_settings(self):
        """
        Get all settings as a dictionary.
        
        Returns:
            dict: All settings
        """
        return self.settings.copy()
    
    def update_multiple(self, settings_dict):
        """
        Update multiple settings at once.
        Does NOT save automatically - call save() after.
        
        Args:
            settings_dict: Dictionary of settings to update
        """
        for key, value in settings_dict.items():
            old_value = self.settings.get(key)
            if old_value != value:
                log_info(f"Setting changed: {key}={value}")
        self.settings.update(settings_dict)


# Global settings manager instance
_settings_manager = None

def get_settings_manager():
    """
    Get the global SettingsManager instance.
    Creates it if it doesn't exist.
    
    Returns:
        SettingsManager: Global settings manager
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager