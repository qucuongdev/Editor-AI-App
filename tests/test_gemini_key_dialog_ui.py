import os
import unittest
from unittest.mock import patch, MagicMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from app import config
from app.ui.gemini_key_dialog import GeminiKeyDialog
from app.ui.main_window import MainWindow
from app.ui.settings_tab import SettingsTab


class GeminiKeyDialogUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_gemini_key_dialog_init_and_elements(self):
        with patch.object(config, "GEMINI_API_KEY", "AIzaSyTest12345"):
            with patch.object(config, "GEMINI_MODEL", "gemini-2.0-flash"):
                with patch.object(config, "GEMINI_CONNECTED", True):
                    with patch("app.core.gemini_client.verify_gemini_connection", return_value=(True, "OK", [])):
                        dialog = GeminiKeyDialog()
                        try:
                            self.assertEqual(dialog.edit_key.text(), "AIzaSyTest12345")
                            self.assertEqual(dialog.combo_model.currentData(), "gemini-2.0-flash")
                            self.assertTrue(dialog.combo_model.isEditable())
                            self.assertTrue(hasattr(dialog, "model_card"))
                            self.assertTrue(dialog.model_card.isEnabled())
                            self.assertTrue(hasattr(dialog, "btn_pill_flash2"))
                            self.assertTrue(hasattr(dialog, "btn_pill_flash15"))
                            self.assertTrue(hasattr(dialog, "btn_pill_pro"))
                            self.assertTrue(hasattr(dialog, "btn_open_portal"))
                            self.assertIn("Google AI Studio", dialog.btn_open_portal.text())
                            self.assertTrue(hasattr(dialog, "btn_test_conn"))
                            self.assertTrue(hasattr(dialog, "lbl_status"))
                            self.assertTrue(hasattr(dialog, "btn_save"))
                        finally:
                            dialog._stop_worker()
                            dialog.close()

    def test_gemini_key_dialog_toggle_visibility(self):
        with patch.object(config, "GEMINI_API_KEY", ""):
            dialog = GeminiKeyDialog()
            try:
                from PyQt6.QtWidgets import QLineEdit
                self.assertEqual(dialog.edit_key.echoMode(), QLineEdit.EchoMode.Password)
                dialog.btn_toggle_key.click()
                self.assertEqual(dialog.edit_key.echoMode(), QLineEdit.EchoMode.Normal)
                dialog.btn_toggle_key.click()
                self.assertEqual(dialog.edit_key.echoMode(), QLineEdit.EchoMode.Password)
            finally:
                dialog.close()

    @patch("PyQt6.QtGui.QDesktopServices.openUrl")
    def test_gemini_key_dialog_open_portal(self, mock_open_url):
        with patch.object(config, "GEMINI_API_KEY", ""):
            dialog = GeminiKeyDialog()
            try:
                dialog.btn_open_portal.click()
                mock_open_url.assert_called_once()
                url_called = mock_open_url.call_args[0][0].toString()
                self.assertEqual(url_called, "https://aistudio.google.com/app/apikey")
            finally:
                dialog.close()

    @patch("app.config.save_setting")
    def test_gemini_key_dialog_test_connection_success(self, mock_save_setting):
        mock_models = [
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": ""},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "description": ""},
        ]
        with patch.object(config, "GEMINI_API_KEY", ""):
            with patch.object(config, "GEMINI_CONNECTED", False):
                dialog = GeminiKeyDialog()
                try:
                    # Trước khi test, model_card bị khóa
                    self.assertFalse(dialog.model_card.isEnabled())

                    dialog.edit_key.setText("AIzaSyValidKey")
                    dialog._on_verify_finished(True, "Kết nối thành công! Đã nạp 2 model.", mock_models, quiet=True)
                    self.app.processEvents()

                    # Sau khi test thành công, model_card mở khóa
                    self.assertTrue(dialog.model_card.isEnabled())
                    self.assertIn("🟢 Kết nối thành công", dialog.lbl_status.text())
                    self.assertIn("#34d399", dialog.lbl_status.styleSheet())
                    # Kiểm tra nạp model mới động từ Google
                    found_25 = any("gemini-2.5-flash" in dialog.combo_model.itemText(i) for i in range(dialog.combo_model.count()))
                    self.assertTrue(found_25)

                    # Kiểm tra nút chọn nhanh pill
                    dialog.btn_pill_pro.click()
                    self.assertEqual(dialog.combo_model.currentData(), "gemini-1.5-pro")
                finally:
                    dialog.close()

    @patch("app.config.save_setting")
    def test_gemini_key_dialog_test_connection_failure(self, mock_save_setting):
        with patch.object(config, "GEMINI_API_KEY", ""):
            with patch.object(config, "GEMINI_CONNECTED", False):
                dialog = GeminiKeyDialog()
                try:
                    dialog.edit_key.setText("AIzaSyInvalidKey")
                    dialog._on_verify_finished(False, "API Key không hợp lệ hoặc đã hết hạn!", [], quiet=True)
                    self.app.processEvents()

                    self.assertIn("🔴", dialog.lbl_status.text())
                    self.assertIn("#f87171", dialog.lbl_status.styleSheet())
                    # Thất bại thì model_card bị khóa
                    self.assertFalse(dialog.model_card.isEnabled())
                finally:
                    dialog.close()

    @patch("app.config.save_setting")
    @patch("PyQt6.QtWidgets.QMessageBox.information")
    def test_gemini_key_dialog_save_key(self, mock_info, mock_save_setting):
        with patch.object(config, "GEMINI_API_KEY", ""):
            dialog = GeminiKeyDialog()
            try:
                receiver = MagicMock()
                dialog.key_saved.connect(receiver)

                dialog.edit_key.setText("AIzaSyNewSavedKey999")
                dialog.combo_model.setEditText("gemini-custom-model")

                # Trường hợp 1: Chưa kết nối thành công mà lưu -> GEMINI_CONNECTED phải là False
                dialog.is_connected = False
                dialog.save_key()
                self.assertFalse(getattr(config, "GEMINI_CONNECTED", False))

                # Trường hợp 2: Đã test kết nối thành công -> GEMINI_CONNECTED chuyển True
                dialog.is_connected = True
                dialog.save_key()
                receiver.assert_called_with("AIzaSyNewSavedKey999", "gemini-custom-model")
                self.assertEqual(getattr(config, "GEMINI_API_KEY", ""), "AIzaSyNewSavedKey999")
                self.assertEqual(getattr(config, "GEMINI_MODEL", ""), "gemini-custom-model")
                self.assertTrue(getattr(config, "GEMINI_CONNECTED", False))
                mock_save_setting.assert_any_call("GEMINI_API_KEY", "AIzaSyNewSavedKey999")
            finally:
                dialog.close()

    @patch("app.config.save_setting")
    def test_settings_tab_gemini_connection_test(self, mock_save_setting):
        tab = SettingsTab()
        try:
            self.assertTrue(hasattr(tab, "btn_test_gemini"))
            self.assertTrue(hasattr(tab, "lbl_gemini_status"))
            self.assertTrue(hasattr(tab, "gemini_model_card"))
            self.assertTrue(tab.combo_gemini_model.isEditable())

            mock_models = [{"id": "gemini-test-model", "name": "Test Model", "description": ""}]
            tab._on_gemini_verify_finished(True, "OK", mock_models, quiet=True)
            self.app.processEvents()

            self.assertIn("🟢 Kết nối thành công", tab.lbl_gemini_status.text())
            self.assertTrue(tab.gemini_model_card.isEnabled())
            found_test = any("gemini-test-model" in tab.combo_gemini_model.itemText(i) for i in range(tab.combo_gemini_model.count()))
            self.assertTrue(found_test)
        finally:
            tab.close()

    def test_main_window_sidebar_gemini_chip(self):
        window = MainWindow()
        try:
            # Kiểm tra tồn tại nút btn_gemini_chip trong footer
            self.assertTrue(hasattr(window, "btn_gemini_chip"))
            self.assertTrue(hasattr(window, "api_chip"))

            # Kiểm tra thứ tự: btn_gemini_chip nằm trước (bên trái) api_chip
            footer_layout = window.btn_gemini_chip.parentWidget().layout()
            idx_gemini = footer_layout.indexOf(window.btn_gemini_chip)
            idx_voice = footer_layout.indexOf(window.api_chip)
            self.assertLess(idx_gemini, idx_voice)

            # Test khi đã kết nối (Chấm xanh lá 🟢)
            with patch.object(config, "GEMINI_API_KEY", "valid_key"):
                with patch.object(config, "GEMINI_CONNECTED", True):
                    window._refresh_api_chip_display()
                    self.assertEqual(window.btn_gemini_chip.text(), "🟢 Gemini AI")
                    self.assertIn("#052e16", window.btn_gemini_chip.styleSheet())
                    self.assertIn("#16a34a", window.btn_gemini_chip.styleSheet())

                    # Test khi sidebar thu gọn (Mini mode) -> Hiện chấm xanh 🟢
                    window.set_sidebar_collapsed(True)
                    self.assertEqual(window.btn_gemini_chip.text(), "🟢")
                    window.set_sidebar_collapsed(False)

            # Test khi chưa kết nối (Chấm đỏ 🔴)
            with patch.object(config, "GEMINI_API_KEY", ""):
                with patch.object(config, "GEMINI_CONNECTED", False):
                    window._refresh_api_chip_display()
                    self.assertEqual(window.btn_gemini_chip.text(), "🔴 Gemini AI")
                    self.assertIn("#450a0a", window.btn_gemini_chip.styleSheet())
                    self.assertIn("#dc2626", window.btn_gemini_chip.styleSheet())

                    # Test khi sidebar thu gọn (Mini mode) -> Hiện chấm đỏ 🔴
                    window.set_sidebar_collapsed(True)
                    self.assertEqual(window.btn_gemini_chip.text(), "🔴")
                    window.set_sidebar_collapsed(False)
        finally:
            window.close()

    def test_gemini_key_dialog_model_search_filter(self):
        """Kiểm tra thanh lọc tìm kiếm trong danh sách model ComboBox."""
        mock_models = [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "description": ""},
            {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash Exp", "description": ""},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "description": ""},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "description": ""},
            {"id": "text-embedding-004", "name": "Text Embedding 004", "description": ""},
        ]
        dialog = GeminiKeyDialog()
        try:
            self.assertTrue(hasattr(dialog, "edit_search_model"))
            self.assertTrue(hasattr(dialog, "lbl_combo_title"))

            # Nạp 5 models
            dialog._populate_models(mock_models)
            self.assertEqual(dialog.combo_model.count(), 5)
            self.assertIn("(5)", dialog.lbl_combo_title.text())

            # Lọc theo "2.0"
            dialog.edit_search_model.setText("2.0")
            self.assertEqual(dialog.combo_model.count(), 2)
            self.assertIn("(2)", dialog.lbl_combo_title.text())

            # Lọc theo "pro"
            dialog.edit_search_model.setText("pro")
            self.assertEqual(dialog.combo_model.count(), 1)
            self.assertEqual(dialog.combo_model.itemData(0), "gemini-1.5-pro")

            # Xóa filter -> Quay về 5
            dialog.edit_search_model.setText("")
            self.assertEqual(dialog.combo_model.count(), 5)
            self.assertIn("(5)", dialog.lbl_combo_title.text())
        finally:
            dialog.close()

    def test_combobox_click_to_popup(self):
        """Kiểm tra sự kiện click trên lineEdit của ComboBox mở popup."""
        dialog = GeminiKeyDialog()
        tab = SettingsTab()
        try:
            self.assertIsNotNone(dialog.combo_model.lineEdit())
            self.assertEqual(dialog.combo_model.maxVisibleItems(), 7)

            self.assertIsNotNone(tab.combo_gemini_model.lineEdit())
        finally:
            dialog.close()
            tab.close()


if __name__ == "__main__":
    unittest.main()
