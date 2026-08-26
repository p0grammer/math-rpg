"""
Mathpal — Settings Manager
===========================
Handles persistent application configuration saved to a JSON file.
Automatically creates data directory and falls back safely to defaults.
"""

import json
import os

from config import AUDIO_BGM_VOLUME, AUDIO_SFX_VOLUME, CRT_ENABLED_DEFAULT

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")


class SettingsManager:
    """Singleton for loading, saving, and syncing player settings."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.bgm_volume = AUDIO_BGM_VOLUME
        self.sfx_volume = AUDIO_SFX_VOLUME
        self.crt_enabled = CRT_ENABLED_DEFAULT
        self.unlocked_level = 1
        self.total_xp = 0

        self.load()

    def load(self):
        """Load settings from JSON file if available."""
        if not os.path.isfile(SETTINGS_FILE):
            return

        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.bgm_volume = float(data.get("bgm_volume", self.bgm_volume))
                self.sfx_volume = float(data.get("sfx_volume", self.sfx_volume))
                self.crt_enabled = bool(data.get("crt_enabled", self.crt_enabled))
                self.unlocked_level = int(data.get("unlocked_level", self.unlocked_level))
                self.total_xp = int(data.get("total_xp", self.total_xp))
        except Exception:
            # Fall back gracefully to in-memory defaults
            pass

    def save(self):
        """Save current settings to JSON file."""
        try:
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            data = {
                "bgm_volume": round(self.bgm_volume, 2),
                "sfx_volume": round(self.sfx_volume, 2),
                "crt_enabled": self.crt_enabled,
                "unlocked_level": self.unlocked_level,
                "total_xp": self.total_xp,
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass
