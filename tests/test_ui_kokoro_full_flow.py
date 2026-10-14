"""
UI Automation Test for Full Kokoro Offline & Preset Voices Flow.
Simulates user interaction on TTSTab & VoiceLookupTab in headless mode.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtWidgets import QApplication, QPushButton

from app.core.standalone_state import StandaloneStateStore
from app.ui.tts_tab import TTSTab


class _SilentMediaPlayer(QObject):
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    playbackStateChanged = pyqtSignal(object)

    def setAudioOutput(self, _output): pass
    def setSource(self, _source): pass
    def stop(self): pass


class _SilentAudioOutput:
    def setVolume(self, _volume): pass


class TestKokoroFullFlowUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        settings = QSettings(
            str(Path(self.temp_dir.name) / "settings.ini"),
            QSettings.Format.IniFormat,
        )
        self.store = StandaloneStateStore(settings)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_tab(self) -> TTSTab:
        with patch("app.ui.tts_tab.QMediaPlayer", _SilentMediaPlayer), patch(
            "app.ui.tts_tab.QAudioOutput", _SilentAudioOutput
        ), patch(
            "app.ui.voice_lookup_tab.QMediaPlayer", _SilentMediaPlayer
        ), patch(
            "app.ui.voice_lookup_tab.QAudioOutput", _SilentAudioOutput
        ):
            tab = TTSTab()
            tab.configure_standalone(self.store, Path(self.temp_dir.name))
            return tab

    def test_full_kokoro_voice_selection_and_lookup_flow(self):
        """Giả lập toàn bộ luồng tương tác người dùng: Chọn Kokoro -> Xem danh sách giọng -> Tra cứu -> Dùng giọng."""
        tab = self._create_tab()

        # 1. Chuyển sang nền tảng Kokoro Local
        kokoro_idx = tab.combo_provider.findData("kokoro")
        self.assertGreaterEqual(kokoro_idx, 0, "Phải tìm thấy nền tảng Kokoro trong combo_provider")
        tab.combo_provider.setCurrentIndex(kokoro_idx)
        self.app.processEvents()

        # 2. Kiểm tra combo_voice nạp đầy đủ 70+ giọng có sẵn
        # (Số item = 70 giọng + 1 dòng 'Tra cứu thêm giọng khác…')
        self.assertGreaterEqual(tab.combo_voice.count(), 71)

        # 3. Kiểm tra giọng mặc định là vi_mai_linh (tiếng Việt ưu tiên lên đầu)
        self.assertEqual(tab.current_voice_id(), "vi_mai_linh")
        self.assertIn("Mai Linh", tab.combo_voice.currentText())

        # 4. Người dùng click chọn trực tiếp giọng 'af_bella' trong ComboBox
        bella_idx = tab.combo_voice.findData("af_bella")
        self.assertGreaterEqual(bella_idx, 0, "Phải tìm thấy giọng af_bella trong combo_voice")
        tab.combo_voice.setCurrentIndex(bella_idx)
        self.app.processEvents()
        self.assertEqual(tab.current_voice_id(), "af_bella")

        # 5. Người dùng bấm nút '🔍 Tra cứu…' bên cạnh ComboBox
        tab.btn_lookup_voice.click()
        self.app.processEvents()
        self.assertEqual(tab.tab_widget.currentIndex(), 1, "Giao diện phải chuyển sang tab Tra cứu Voice")

        lookup = tab.voice_lookup_tab
        self.assertEqual(lookup.combo_source.currentData(), "kokoro_local", "Nguồn tra cứu phải đồng bộ sang kokoro_local")

        # Nạp bảng tra cứu
        lookup.load_voices()
        if lookup.worker:
            lookup.worker.wait()
        self.app.processEvents()

        self.assertGreaterEqual(lookup.total_count, 70, "Tổng số giọng Kokoro phải đạt ít nhất 70")
        self.assertEqual(lookup.table.rowCount(), 30, "Trang 1 bảng tra cứu hiển thị 30 giọng (phân trang)")
        self.assertTrue(lookup.has_more, "Phải có trang tiếp theo cho các giọng còn lại")

        # 6. Người dùng chọn một giọng khác từ bảng tra cứu và bấm 'Dùng giọng'
        # Chọn hàng chứa giọng 'vi_ngoc_huyen' (nằm trong 14 giọng tiếng Việt trang 1)
        target_row = -1
        for row in range(lookup.table.rowCount()):
            if lookup.table.item(row, 2).text() == "vi_ngoc_huyen":
                target_row = row
                break
        self.assertGreaterEqual(target_row, 0, "Phải tìm thấy giọng vi_ngoc_huyen trong trang 1 bảng tra cứu")

        # Kích hoạt hành động dùng giọng
        action_widget = lookup.table.cellWidget(target_row, 5)
        self.assertIsNotNone(action_widget, "Hàng phải có widget thao tác")
        use_buttons = [b for b in action_widget.findChildren(QPushButton) if "Dùng" in b.text()]
        self.assertTrue(len(use_buttons) > 0, "Widget thao tác phải chứa nút 'Dùng'")
        use_buttons[0].click()
        self.app.processEvents()

        # 7. Kiểm tra UI tự động quay về tab Tạo giọng nói và chọn đúng 'vi_ngoc_huyen'
        self.assertEqual(tab.tab_widget.currentIndex(), 0, "Phải tự động quay lại tab Tạo Giọng Nói")
        self.assertEqual(tab.current_voice_id(), "vi_ngoc_huyen", "Giọng được chọn phải là vi_ngoc_huyen")
        self.assertIn("Ngọc Huyền", tab.combo_voice.currentText())


if __name__ == "__main__":
    unittest.main()
