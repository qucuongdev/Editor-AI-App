import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QLabel, QPushButton

from app.ui.main_window import MainWindow
from app.ui.project_workspace import ProjectWorkspace
from app.ui.tts_tab import TTSTab


class RestoredFeaturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_project_tts_and_settings_are_reachable_from_sidebar(self):
        window = MainWindow()
        try:
            labels = [button.text() for button in window.nav_buttons]
            for label in ("Dự án", "Tạo Voice TTS", "Cài đặt"):
                self.assertTrue(any(label in text for text in labels), label)

            self.assertIsInstance(window.project_workspace, ProjectWorkspace)
            self.assertIsInstance(window.tts_tab, TTSTab)
            self.assertIs(window.stack.widget(0), window.project_workspace)
            self.assertIs(window.stack.widget(2), window.tts_tab)
            self.assertIsNotNone(window.tts_tab.standalone_store)
            self.assertFalse(any(
                "Kịch Bản Cảnh" in button.text()
                for button in window.project_workspace.tts_tab.findChildren(QPushButton)
            ))

            for index, button in enumerate(window.nav_buttons):
                button.click()
                self.assertEqual(window.stack.currentIndex(), index)
                self.assertTrue(button.isChecked())

            window.on_account_updated({"credit_balance": 1200})
            self.assertEqual(window.tts_tab.credit_balance, 1200)
            self.assertEqual(window.project_workspace.tts_tab.credit_balance, 1200)
            self.assertIn("1,200", window.api_chip.text())
            self.assertIn("#34d399", window.api_chip.styleSheet())
            self.assertIn("#064e3b", window.api_chip.styleSheet())

            window.on_account_updated({"credit_balance": 0})
            self.assertNotIn("#34d399", window.api_chip.styleSheet())
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()

