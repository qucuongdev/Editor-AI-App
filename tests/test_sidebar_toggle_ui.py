"""
UI Automation tests for MainWindow sidebar mini/collapsed mode and toggle feature.
"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from app.ui.main_window import MainWindow


class SidebarToggleUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @classmethod
    def tearDownClass(cls):
        from app.core.standalone_state import StandaloneStateStore
        StandaloneStateStore().save_sidebar_collapsed(False)

    def tearDown(self):
        from app.core.standalone_state import StandaloneStateStore
        StandaloneStateStore().save_sidebar_collapsed(False)
        self.app.processEvents()

    def test_sidebar_collapsed_mini_mode_and_navigation(self):
        window = MainWindow()
        try:
            window.show()
            self.app.processEvents()

            # 1. Ban đầu ở Expanded Mode (Mở rộng đầy đủ)
            self.assertFalse(window.is_sidebar_collapsed)
            self.assertEqual(window.sidebar.property("mini"), "false")
            self.assertEqual(window.sidebar.width(), 260)
            self.assertIn("Dự án", window.btn_nav_project.text())
            self.assertIn("Xu hướng & Ý tưởng", window.btn_nav_trending.text())
            self.assertEqual(window.btn_toggle_sidebar.text(), "◀")
            self.assertIn("Thu gọn", window.btn_toggle_sidebar.toolTip())

            # 2. Click nút toggle để chuyển sang chế độ Thu gọn (Mini Icon-only)
            QTest.mouseClick(window.btn_toggle_sidebar, Qt.MouseButton.LeftButton)
            self.app.processEvents()

            self.assertTrue(window.is_sidebar_collapsed)
            self.assertEqual(window.sidebar.property("mini"), "true")
            self.assertEqual(window.sidebar.width(), 64)
            self.assertEqual(window.btn_toggle_sidebar.text(), "▶")
            self.assertIn("Mở rộng", window.btn_toggle_sidebar.toolTip())

            # Kiểm tra text và tooltip của từng item ở chế độ Mini
            self.assertEqual(window.btn_nav_project.text(), "📁")
            self.assertIn("Dự án", window.btn_nav_project.toolTip())

            self.assertEqual(window.btn_nav_watermark.text(), "🍌")
            self.assertIn("Gỡ watermark", window.btn_nav_watermark.toolTip())

            self.assertEqual(window.btn_nav_tts.text(), "🎙")
            self.assertIn("Tạo Voice TTS", window.btn_nav_tts.toolTip())

            self.assertEqual(window.btn_nav_trending.text(), "🔥")
            self.assertIn("Xu hướng & Ý tưởng", window.btn_nav_trending.toolTip())

            self.assertEqual(window.btn_nav_settings.text(), "⚙")
            self.assertIn("Cài đặt", window.btn_nav_settings.toolTip())

            self.assertTrue(window.standalone_state.load_sidebar_collapsed())

            # 3. Kiểm tra click chuyển trang khi ở chế độ Mini
            QTest.mouseClick(window.btn_nav_trending, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            self.assertEqual(window.stack.currentIndex(), 3)
            self.assertTrue(window.btn_nav_trending.isChecked())

            QTest.mouseClick(window.btn_nav_tts, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            self.assertEqual(window.stack.currentIndex(), 2)
            self.assertTrue(window.btn_nav_tts.isChecked())

            QTest.mouseClick(window.btn_nav_project, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            self.assertEqual(window.stack.currentIndex(), 0)
            self.assertTrue(window.btn_nav_project.isChecked())

            # 4. Kiểm tra kích hoạt qua phím tắt Ctrl+B
            # Ctrl+B lần 1: Mở rộng trở lại
            window.shortcut_toggle_sidebar.activated.emit()
            self.app.processEvents()

            self.assertFalse(window.is_sidebar_collapsed)
            self.assertEqual(window.sidebar.width(), 260)
            self.assertIn("Dự án", window.btn_nav_project.text())
            self.assertEqual(window.btn_toggle_sidebar.text(), "◀")

            # Ctrl+B lần 2: Thu gọn về Mini icon
            window.shortcut_toggle_sidebar.activated.emit()
            self.app.processEvents()

            self.assertTrue(window.is_sidebar_collapsed)
            self.assertEqual(window.sidebar.width(), 64)
            self.assertEqual(window.btn_nav_project.text(), "📁")
            self.assertEqual(window.btn_toggle_sidebar.text(), "▶")

        finally:
            window.set_sidebar_collapsed(False)
            window.close()


if __name__ == "__main__":
    unittest.main()
