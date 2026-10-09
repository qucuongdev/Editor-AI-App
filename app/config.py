from pathlib import Path
from PyQt6.QtCore import QSettings

APP_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = APP_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_WATERMARK_DOWNLOADS_DIR = DOWNLOADS_DIR / "watermark"
LEGACY_TTS_DOWNLOADS_DIR = DOWNLOADS_DIR / "tts"

USER_DOWNLOADS_DIR = Path.home() / "Downloads"
USER_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_USER_WATERMARK_DOWNLOADS_DIR = USER_DOWNLOADS_DIR / "watermark"
WATERMARK_DOWNLOADS_DIR = USER_DOWNLOADS_DIR / "image_watermark"
VIDEO_WATERMARK_DOWNLOADS_DIR = USER_DOWNLOADS_DIR / "video_watermark"
TTS_DOWNLOADS_DIR = USER_DOWNLOADS_DIR / "tts"
WATERMARK_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_WATERMARK_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
TTS_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS = QSettings("AI Studio", "AI Media Studio")

class AppConfig:
    def __init__(self):
        self.reload()

    def _get_projects_dir(self) -> Path:
        desktop = Path.home() / "Desktop"
        projects = desktop / "Editor-AI-Projects" if desktop.exists() else Path.home() / "Editor-AI-Projects"
        projects.mkdir(parents=True, exist_ok=True)
        return projects

    def _setting_text(self, key: str, default: str) -> str:
        value = SETTINGS.value(key, default)
        return str(value) if value is not None else default

    def _setting_float(self, key: str, default: float) -> float:
        try:
            return float(SETTINGS.value(key, default))
        except (TypeError, ValueError):
            return default

    def reload(self):
        projects_value = self._setting_text("PROJECTS_DIR", "")
        self.PROJECTS_DIR = Path(projects_value) if projects_value else self._get_projects_dir()
        self.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        
        self.ACTIVE_PROJECT = self._setting_text("ACTIVE_PROJECT", "")
        self.VIBI_API_BASE = self._setting_text("VIBI_API_BASE", "https://api.vibi.pro")
        self.VIBI_API_KEY = self._setting_text("VIBI_API_KEY", "")
        self.DEFAULT_VIBI_MODEL = self._setting_text("DEFAULT_VIBI_MODEL", "eleven_v3")
        self.DEFAULT_VIBI_LANGUAGE = self._setting_text("DEFAULT_VIBI_LANGUAGE", "vi")
        self.DEFAULT_VIBI_VOICE_ID = self._setting_text("DEFAULT_VIBI_VOICE_ID", "6adFm46eyy74snVn6YrT")
        self.DEFAULT_VIBI_STABILITY = self._setting_float("DEFAULT_VIBI_STABILITY", 0.5)
        self.DEFAULT_VIBI_SIMILARITY = self._setting_float("DEFAULT_VIBI_SIMILARITY", 0.75)
        self.DEFAULT_VIBI_SPEED = self._setting_float("DEFAULT_VIBI_SPEED", 1.0)

    def save_setting(self, key: str, value: str) -> None:
        SETTINGS.setValue(key, str(value))
        SETTINGS.sync()
        self.reload()

settings = AppConfig()

def save_setting(key: str, value: str) -> None:
    settings.save_setting(key, value)

def reload_config():
    settings.reload()
