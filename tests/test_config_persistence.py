import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import QSettings

from app import config


class ConfigPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_json = Path(self.temp_dir.name) / "test_settings.json"
        self.settings_ini = Path(self.temp_dir.name) / "test_settings.ini"
        self.mock_qsettings = QSettings(str(self.settings_ini), QSettings.Format.IniFormat)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_setting_persists_to_both_qsettings_and_json(self):
        with patch("app.config.LOCAL_SETTINGS_FILE", self.temp_json):
            with patch("app.config.SETTINGS", self.mock_qsettings):
                config.save_setting("TEST_PERSIST_KEY", "SecretValue123")
                
                # Check QSettings
                self.assertEqual(self.mock_qsettings.value("TEST_PERSIST_KEY"), "SecretValue123")
                
                # Check JSON file
                self.assertTrue(self.temp_json.exists())
                with open(self.temp_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.assertEqual(data.get("TEST_PERSIST_KEY"), "SecretValue123")

    def test_setting_text_recovers_from_json_when_qsettings_is_empty(self):
        # Prepare json with key
        initial_data = {"GEMINI_API_KEY": "AQ.Ab8RecoveredKey999"}
        with open(self.temp_json, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False)

        with patch("app.config.LOCAL_SETTINGS_FILE", self.temp_json):
            with patch("app.config.SETTINGS", self.mock_qsettings):
                # QSettings is empty
                self.assertIsNone(self.mock_qsettings.value("GEMINI_API_KEY"))
                
                # _setting_text should recover from JSON
                val = config.settings._setting_text("GEMINI_API_KEY", "")
                self.assertEqual(val, "AQ.Ab8RecoveredKey999")
                
                # And it should have synced back into QSettings
                self.assertEqual(self.mock_qsettings.value("GEMINI_API_KEY"), "AQ.Ab8RecoveredKey999")

    def test_gemini_settings_preserved_across_reload(self):
        with patch("app.config.LOCAL_SETTINGS_FILE", self.temp_json):
            with patch("app.config.SETTINGS", self.mock_qsettings):
                config.save_setting("GEMINI_API_KEY", "AQ.RealKey456")
                config.save_setting("GEMINI_MODEL", "gemini-3.5-flash")
                config.save_setting("GEMINI_CONNECTED", "true")
                
                # Trigger reload
                config.reload_config()
                
                self.assertEqual(config.GEMINI_API_KEY, "AQ.RealKey456")
                self.assertEqual(config.GEMINI_MODEL, "gemini-3.5-flash")
                self.assertTrue(config.GEMINI_CONNECTED)


if __name__ == "__main__":
    unittest.main()
