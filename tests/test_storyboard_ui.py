"""
UI Automation tests for StoryboardDialog and its integration in SceneTab and TrendingTab.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from app import config
from app.ui.storyboard_dialog import StoryboardDialog, SceneCardWidget
from app.ui.scene_tab import SceneTab
from app.ui.trending_tab import TrendingTab
from app.core.storyboard_generator import StoryboardScene


class StoryboardUIAutomationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._key_patcher = patch.object(config, "GEMINI_API_KEY", "")
        self._key_patcher.start()

    def tearDown(self):
        self._key_patcher.stop()
        self.app.processEvents()

    def _wait_for_worker(self, dialog: StoryboardDialog, timeout_ms: int = 5000):
        if dialog.worker and dialog.worker.isRunning():
            dialog.worker.wait(timeout_ms)
        self.app.processEvents()

    def test_storyboard_dialog_generate_and_render_cards(self):
        dialog = StoryboardDialog(topic="Sinh tồn tài chính thành phố")
        try:
            self._wait_for_worker(dialog)
            dialog.show()
            self.app.processEvents()

            # Verify initialized state
            self.assertEqual(dialog.txt_topic.text(), "Sinh tồn tài chính thành phố")
            self.assertEqual(len(dialog.current_scenes), 5)
            self.assertGreaterEqual(dialog.cards_layout.count(), 5)

            # Change to 3 scenes and click Generate
            dialog.combo_scene_count.setCurrentIndex(dialog.combo_scene_count.findData(3))
            QTest.mouseClick(dialog.btn_generate, Qt.MouseButton.LeftButton)
            self._wait_for_worker(dialog)

            self.assertEqual(len(dialog.current_scenes), 3)
            self.assertIn("3 cảnh", dialog.lbl_stats.text())

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

    def test_storyboard_dialog_sync_duration_and_scene_count(self):
        # 30s -> 3 scenes
        d30 = StoryboardDialog(topic="Test 30s", duration_seconds=30)
        self._wait_for_worker(d30)
        self.assertEqual(d30.combo_scene_count.currentData(), 3)
        self.assertEqual(len(d30.current_scenes), 3)
        d30.close()

        # 60s -> 5 scenes
        d60 = StoryboardDialog(topic="Test 60s", duration_seconds=60)
        self._wait_for_worker(d60)
        self.assertEqual(d60.combo_scene_count.currentData(), 5)
        self.assertEqual(len(d60.current_scenes), 5)
        d60.close()

        # 120s -> 8 scenes
        d120 = StoryboardDialog(topic="Test 120s", duration_seconds=120)
        self._wait_for_worker(d120)
        self.assertEqual(d120.combo_scene_count.currentData(), 8)
        self.assertEqual(len(d120.current_scenes), 8)
        d120.close()

        # 180s -> 10 scenes
        d180 = StoryboardDialog(topic="Test 180s", duration_seconds=180)
        self._wait_for_worker(d180)
        self.assertEqual(d180.combo_scene_count.currentData(), 10)
        self.assertEqual(len(d180.current_scenes), 10)
        d180.close()

    def test_storyboard_dialog_sync_tone_and_aspect_ratio(self):
        dialog = StoryboardDialog(
            topic="Test Tone & AR",
            duration_seconds=60,
            tone="dramatic",
            aspect_ratio="16:9",
            visual_style="anime",
        )
        try:
            self._wait_for_worker(dialog)
            # "dramatic" maps to "shocking"
            self.assertEqual(dialog.combo_tone.currentData(), "shocking")
            self.assertEqual(dialog.combo_aspect.currentData(), "16:9")
            self.assertEqual(dialog.combo_style.currentData(), "anime")
        finally:
            dialog.close()

    def test_storyboard_dialog_ai_badge_display(self):
        # When GEMINI_API_KEY is empty
        with patch.object(config, "GEMINI_API_KEY", ""):
            d_offline = StoryboardDialog(topic="Offline Test")
            self._wait_for_worker(d_offline)
            self.assertIn("Mẫu Offline", d_offline.lbl_ai_badge.text())
            d_offline.close()

        # When GEMINI_API_KEY is provided
        with patch.object(config, "GEMINI_API_KEY", "test_gemini_key_123"):
            with patch.object(config, "GEMINI_MODEL", "gemini-2.0-flash"):
                d_gemini = StoryboardDialog(topic="Gemini Test")
                self._wait_for_worker(d_gemini)
                self.assertIn("Gemini AI", d_gemini.lbl_ai_badge.text())
                self.assertIn("gemini-2.0-flash", d_gemini.lbl_ai_badge.text())
                d_gemini.close()

    @patch("app.core.gemini_client.generate_storyboard_with_gemini")
    def test_storyboard_dialog_calls_gemini_worker_successfully(self, mock_gemini_gen):
        mock_scenes = [
            StoryboardScene("SC01", "Cảnh 1", "Thoại 1", "Prompt 1, --ar 9:16", 10.0, "SFX 1", "zoom_in"),
            StoryboardScene("SC02", "Cảnh 2", "Thoại 2", "Prompt 2, --ar 9:16", 10.0, "SFX 2", "zoom_out"),
            StoryboardScene("SC03", "Cảnh 3", "Thoại 3", "Prompt 3, --ar 9:16", 10.0, "SFX 3", "pan_right"),
        ]
        mock_gemini_gen.return_value = mock_scenes

        with patch.object(config, "GEMINI_API_KEY", "valid_key"):
            with patch.object(config, "GEMINI_MODEL", "gemini-1.5-flash"):
                dialog = StoryboardDialog(topic="Chủ đề AI thực tế", duration_seconds=30)
                try:
                    self._wait_for_worker(dialog)
                    self.assertEqual(len(dialog.current_scenes), 3)
                    self.assertIn("Gemini AI", dialog.lbl_stats.text())
                    self.assertEqual(dialog.current_scenes[0].scene_id, "SC01")
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

    def test_storyboard_add_delete_and_reorder_scenes(self):
        # Khởi tạo dialog với 3 phân cảnh (30s)
        dialog = StoryboardDialog(topic="Kiểm tra sắp xếp phân cảnh", duration_seconds=30)
        try:
            dialog.show()
            self.app.processEvents()
            self._wait_for_worker(dialog)
            self.assertEqual(len(dialog.current_scenes), 3)

            # Lấy 3 card ban đầu
            cards = [dialog.cards_layout.itemAt(i).widget() for i in range(3)]
            self.assertIsInstance(cards[0], SceneCardWidget)
            self.assertEqual(cards[0].lbl_id.text(), "SC01")
            self.assertEqual(cards[1].lbl_id.text(), "SC02")
            self.assertEqual(cards[2].lbl_id.text(), "SC03")

            # 1. Kiểm tra cấu trúc phân biệt rõ nét giữa Header Frame và Body Frame
            self.assertTrue(hasattr(cards[0], "header_frame"))
            self.assertTrue(hasattr(cards[0], "body_frame"))
            self.assertTrue(hasattr(cards[0], "drag_handle"))
            self.assertEqual(cards[0].drag_handle.text(), "⠿")

            # Không còn 2 nút mũi tên ▲ và ▼
            self.assertFalse(hasattr(cards[0], "btn_move_up"))
            self.assertFalse(hasattr(cards[0], "btn_move_down"))

            # 2. Kiểm tra Kéo Thả Trực Quan (Drag & Drop Reordering)
            old_sc01_title = cards[0].edit_title.text()
            # Giả lập kéo thả SC01 xuống vị trí SC03
            cards[0].reorder_requested.emit("SC01", "SC03")
            self.app.processEvents()

            # Sau khi kéo thả, SC01 cũ chuyển xuống vị trí thứ 3 (được đánh số SC03)
            reordered_cards = [dialog.cards_layout.itemAt(i).widget() for i in range(3)]
            self.assertEqual(reordered_cards[0].lbl_id.text(), "SC01")
            self.assertEqual(reordered_cards[1].lbl_id.text(), "SC02")
            self.assertEqual(reordered_cards[2].lbl_id.text(), "SC03")
            self.assertEqual(reordered_cards[2].edit_title.text(), old_sc01_title)
            self.assertIn("Đã đổi thứ tự phân cảnh", dialog.lbl_stats.text())

            # 3. Kiểm tra Hover-to-reveal của nút Xóa (btn_delete)
            # Mặc định nút Xóa bị ẩn để không gây rối mắt
            self.assertTrue(reordered_cards[0].btn_delete.isHidden())
            self.assertTrue(reordered_cards[1].btn_delete.isHidden())

            # Khi rê chuột vào thẻ (enterEvent): nút Xóa xuất hiện
            reordered_cards[0].enterEvent(None)
            self.assertFalse(reordered_cards[0].btn_delete.isHidden())

            # Khi rời chuột khỏi thẻ (leaveEvent): nút Xóa ẩn đi
            reordered_cards[0].leaveEvent(None)
            self.assertTrue(reordered_cards[0].btn_delete.isHidden())

            # 4. Test Xóa 1 phân cảnh (Delete SC02)
            card_to_delete = reordered_cards[1]
            QTest.mouseClick(card_to_delete.btn_delete, Qt.MouseButton.LeftButton)
            self.app.processEvents()

            # Giờ chỉ còn 2 phân cảnh, tự động đánh số lại SC01, SC02
            self.assertEqual(len(dialog.current_scenes), 2)
            cards_after_del = [dialog.cards_layout.itemAt(i).widget() for i in range(2)]
            self.assertEqual(cards_after_del[0].lbl_id.text(), "SC01")
            self.assertEqual(cards_after_del[1].lbl_id.text(), "SC02")

            # 4. Test Thêm phân cảnh mới (Add Scene)
            self.assertTrue(hasattr(dialog, "btn_add_scene"))
            QTest.mouseClick(dialog.btn_add_scene, Qt.MouseButton.LeftButton)
            self.app.processEvents()

            # Số phân cảnh tăng lên 3, card mới có ID là SC03
            self.assertEqual(len(dialog.current_scenes), 3)
            cards_after_add = [dialog.cards_layout.itemAt(i).widget() for i in range(3)]
            self.assertEqual(cards_after_add[2].lbl_id.text(), "SC03")
            self.assertIn("Phân cảnh bổ sung 3", cards_after_add[2].edit_title.text())

            # 5. Kiểm tra an toàn: khi kịch bản chỉ còn 1 cảnh duy nhất thì không cho phép xóa
            cards_after_add[2].btn_delete.click()
            self.app.processEvents()
            cards_now = [dialog.cards_layout.itemAt(i).widget() for i in range(2)]
            cards_now[1].btn_delete.click()
            self.app.processEvents()

            self.assertEqual(len(dialog.current_scenes), 1)
            single_card = dialog.cards_layout.itemAt(0).widget()
            self.assertFalse(single_card._can_delete)
            # Rê chuột vào cũng không hiện nút xóa vì _can_delete == False
            single_card.enterEvent(None)
            self.assertTrue(single_card.btn_delete.isHidden())
        finally:
            dialog.close()

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
