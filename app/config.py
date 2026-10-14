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

def _get_default_tts_dir() -> Path:
    target = Path("D:/Work/Tool/Voices")
    if Path("D:/").exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
            return target
        except Exception:
            pass
    fallback = USER_DOWNLOADS_DIR / "tts"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

TTS_DOWNLOADS_DIR = _get_default_tts_dir()
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

    def _get_tts_dir(self) -> Path:
        tts_value = self._setting_text("TTS_DOWNLOADS_DIR", "")
        if tts_value:
            p = Path(tts_value)
            try:
                p.mkdir(parents=True, exist_ok=True)
                return p
            except Exception:
                pass
        return _get_default_tts_dir()

    def reload(self):
        projects_value = self._setting_text("PROJECTS_DIR", "")
        self.PROJECTS_DIR = Path(projects_value) if projects_value else self._get_projects_dir()
        self.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

        self.TTS_DOWNLOADS_DIR = self._get_tts_dir()
        self.TTS_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
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

# Expose module-level attributes for backward compatibility
PROJECTS_DIR = settings.PROJECTS_DIR
TTS_DOWNLOADS_DIR = settings.TTS_DOWNLOADS_DIR
ACTIVE_PROJECT = settings.ACTIVE_PROJECT
VIBI_API_BASE = settings.VIBI_API_BASE
VIBI_API_KEY = settings.VIBI_API_KEY
DEFAULT_VIBI_MODEL = settings.DEFAULT_VIBI_MODEL
DEFAULT_VIBI_LANGUAGE = settings.DEFAULT_VIBI_LANGUAGE
DEFAULT_VIBI_VOICE_ID = settings.DEFAULT_VIBI_VOICE_ID
DEFAULT_VIBI_STABILITY = settings.DEFAULT_VIBI_STABILITY
DEFAULT_VIBI_SIMILARITY = settings.DEFAULT_VIBI_SIMILARITY
DEFAULT_VIBI_SPEED = settings.DEFAULT_VIBI_SPEED

def save_setting(key: str, value: str) -> None:
    settings.save_setting(key, value)
    reload_config()

def reload_config():
    global PROJECTS_DIR, TTS_DOWNLOADS_DIR, ACTIVE_PROJECT, VIBI_API_BASE, VIBI_API_KEY
    global DEFAULT_VIBI_MODEL, DEFAULT_VIBI_LANGUAGE, DEFAULT_VIBI_VOICE_ID
    global DEFAULT_VIBI_STABILITY, DEFAULT_VIBI_SIMILARITY, DEFAULT_VIBI_SPEED
    settings.reload()
    PROJECTS_DIR = settings.PROJECTS_DIR
    TTS_DOWNLOADS_DIR = settings.TTS_DOWNLOADS_DIR
    ACTIVE_PROJECT = settings.ACTIVE_PROJECT
    VIBI_API_BASE = settings.VIBI_API_BASE
    VIBI_API_KEY = settings.VIBI_API_KEY
    DEFAULT_VIBI_MODEL = settings.DEFAULT_VIBI_MODEL
    DEFAULT_VIBI_LANGUAGE = settings.DEFAULT_VIBI_LANGUAGE
    DEFAULT_VIBI_VOICE_ID = settings.DEFAULT_VIBI_VOICE_ID
    DEFAULT_VIBI_STABILITY = settings.DEFAULT_VIBI_STABILITY
    DEFAULT_VIBI_SIMILARITY = settings.DEFAULT_VIBI_SIMILARITY
    DEFAULT_VIBI_SPEED = settings.DEFAULT_VIBI_SPEED

def __getattr__(name: str):
    if hasattr(settings, name):
        return getattr(settings, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


