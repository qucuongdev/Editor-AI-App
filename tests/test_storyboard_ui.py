"""
UI Automation tests for StoryboardDialog and its integration in SceneTab and TrendingTab.
"""

import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from app.ui.storyboard_dialog import StoryboardDialog, SceneCardWidget
from app.ui.scene_tab import SceneTab
from app.ui.trending_tab import TrendingTab


class StoryboardUIAutomationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        self.app.processEvents()

    def test_storyboard_dialog_generate_and_render_cards(self):
        dialog = StoryboardDialog(topic="Sinh tồn tài chính thành phố")
        try:
            dialog.show()
            self.app.processEvents()

            # Verify initialized state
            self.assertEqual(dialog.txt_topic.text(), "Sinh tồn tài chính thành phố")
            self.assertEqual(len(dialog.current_scenes), 5)
            self.assertGreaterEqual(dialog.cards_layout.count(), 5)

            # Change to 3 scenes and click Generate
            dialog.combo_scene_count.setCurrentIndex(dialog.combo_scene_count.findData(3))
            QTest.mouseClick(dialog.btn_generate, Qt.MouseButton.LeftButton)
            self.app.processEvents()

            self.assertEqual(len(dialog.current_scenes), 3)
            self.assertIn("3 phân cảnh", dialog.lbl_stats.text())

            # Test Copy Script button
            QTest.mouseClick(dialog.btn_copy_script, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            clip_text = self.app.clipboard().text()
            self.assertIn(dialog.current_scenes[0].voiceover, clip_text)

            # Test Copy JSON button
            QTest.mouseClick(dialog.btn_copy_json, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            clip_json = self.app.clipboard().text()
            self.assertIn("SC01", clip_json)

            # Test Send to TTS signal
            tts_receiver = MagicMock()
            dialog.send_to_tts_requested.connect(tts_receiver)
            QTest.mouseClick(dialog.btn_send_tts, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            tts_receiver.assert_called_once()
            clip_script = self.app.clipboard().text()
            self.assertTrue(len(clip_script) > 0)
        finally:
            dialog.close()

    def test_storyboard_integration_in_scene_tab(self):
        scene_tab = SceneTab()
        try:
            self.assertTrue(hasattr(scene_tab, "btn_ai_storyboard"))
            self.assertTrue(scene_tab.btn_ai_storyboard.isEnabled())
            self.assertIn("AI Sinh Phân Cảnh", scene_tab.btn_ai_storyboard.text())

            # Test applying storyboard directly to scene_tab
            mock_json = '[{"id": "SC01", "character": "", "character_info": "", "prompt": "Test prompt", "subtitle_ids": [], "start_at": "00:00:00,000", "end_at": "AUDIO_END"}]'
            scene_tab._on_storyboard_applied(mock_json, "Lời thoại kiểm thử")
            self.app.processEvents()

            self.assertEqual(scene_tab.combo_mode.currentData(), SceneTab.TEXT_MODE)
            self.assertIn("SC01", scene_tab.txt_scene_content.toPlainText())

            # Test request_open_tts signal from scene_tab
            tts_mock = MagicMock()
            scene_tab.request_open_tts.connect(tts_mock)
            scene_tab._on_storyboard_send_to_tts("Kịch bản thoại phân cảnh nạp vào dự án")
            tts_mock.assert_called_once_with("Kịch bản thoại phân cảnh nạp vào dự án")
        finally:
            scene_tab.close()

    def test_storyboard_button_in_trending_tab_prompt_page(self):
        tab = TrendingTab()
        try:
            self.assertTrue(hasattr(tab, "btn_open_storyboard"))
            self.assertTrue(tab.btn_open_storyboard.isEnabled())
            self.assertIn("Sinh Kịch Bản", tab.btn_open_storyboard.text())

            # Open prompt studio for an idea
            tab.open_prompt_studio({"title": "Bí mật kho lưu trữ Vatican", "angle": "mystery"})
            self.app.processEvents()
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_PROMPT)
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()


if __name__ == "__main__":
    unittest.main()
