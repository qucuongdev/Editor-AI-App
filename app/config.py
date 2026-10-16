import json
from pathlib import Path
from PyQt6.QtCore import QSettings

APP_DIR = Path(__file__).resolve().parent.parent
LOCAL_SETTINGS_FILE = APP_DIR / "local_settings.json"


def _load_local_json_settings() -> dict:
    if LOCAL_SETTINGS_FILE.exists():
        try:
            with open(LOCAL_SETTINGS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                return json.loads(content) if content.strip() else {}
        except Exception:
            return {}
    return {}


def _save_local_json_settings(data: dict) -> None:
    try:
        with open(LOCAL_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


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
        value = SETTINGS.value(key, None)
        local_data = _load_local_json_settings()
        if value is not None and str(value).strip():
            str_val = str(value)
            if local_data.get(key) != str_val:
                local_data[key] = str_val
                _save_local_json_settings(local_data)
            return str_val
        if key in local_data and str(local_data[key]).strip():
            val_str = str(local_data[key])
            SETTINGS.setValue(key, val_str)
            SETTINGS.sync()
            return val_str
        return default

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
        self.GEMINI_API_KEY = self._setting_text("GEMINI_API_KEY", "")
        loaded_model = self._setting_text("GEMINI_MODEL", "gemini-3.5-flash")
        if loaded_model in ("gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"):
            loaded_model = "gemini-3.5-flash"
        self.GEMINI_MODEL = loaded_model
        conn_setting = self._setting_text("GEMINI_CONNECTED", "")
        if conn_setting and conn_setting.lower() in ("true", "1") and bool(self.GEMINI_API_KEY.strip()):
            self.GEMINI_CONNECTED = True
        else:
            self.GEMINI_CONNECTED = False
        self.DEFAULT_VIBI_MODEL = self._setting_text("DEFAULT_VIBI_MODEL", "eleven_v3")
        self.DEFAULT_VIBI_LANGUAGE = self._setting_text("DEFAULT_VIBI_LANGUAGE", "vi")
        self.DEFAULT_VIBI_VOICE_ID = self._setting_text("DEFAULT_VIBI_VOICE_ID", "6adFm46eyy74snVn6YrT")
        self.DEFAULT_VIBI_STABILITY = self._setting_float("DEFAULT_VIBI_STABILITY", 0.5)
        self.DEFAULT_VIBI_SIMILARITY = self._setting_float("DEFAULT_VIBI_SIMILARITY", 0.75)
        self.DEFAULT_VIBI_SPEED = self._setting_float("DEFAULT_VIBI_SPEED", 1.0)

    def save_setting(self, key: str, value: str) -> None:
        val_str = str(value)
        SETTINGS.setValue(key, val_str)
        SETTINGS.sync()
        local_data = _load_local_json_settings()
        local_data[key] = val_str
        _save_local_json_settings(local_data)
        self.reload()

settings = AppConfig()

# Expose module-level attributes for backward compatibility
PROJECTS_DIR = settings.PROJECTS_DIR
TTS_DOWNLOADS_DIR = settings.TTS_DOWNLOADS_DIR
ACTIVE_PROJECT = settings.ACTIVE_PROJECT
VIBI_API_BASE = settings.VIBI_API_BASE
VIBI_API_KEY = settings.VIBI_API_KEY
GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL
GEMINI_CONNECTED = settings.GEMINI_CONNECTED
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
    global GEMINI_API_KEY, GEMINI_MODEL, GEMINI_CONNECTED
    global DEFAULT_VIBI_MODEL, DEFAULT_VIBI_LANGUAGE, DEFAULT_VIBI_VOICE_ID
    global DEFAULT_VIBI_STABILITY, DEFAULT_VIBI_SIMILARITY, DEFAULT_VIBI_SPEED
    settings.reload()
    PROJECTS_DIR = settings.PROJECTS_DIR
    TTS_DOWNLOADS_DIR = settings.TTS_DOWNLOADS_DIR
    ACTIVE_PROJECT = settings.ACTIVE_PROJECT
    VIBI_API_BASE = settings.VIBI_API_BASE
    VIBI_API_KEY = settings.VIBI_API_KEY
    GEMINI_API_KEY = settings.GEMINI_API_KEY
    GEMINI_MODEL = settings.GEMINI_MODEL
    GEMINI_CONNECTED = settings.GEMINI_CONNECTED
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


