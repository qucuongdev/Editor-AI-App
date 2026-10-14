import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtWidgets import QApplication

from app.core.standalone_state import StandaloneStateStore
from app.ui.tts_tab import TTSTab
from app.core.tts_worker import TTSWorker


class _SilentMediaPlayer(QObject):
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    playbackStateChanged = pyqtSignal(object)

    def setAudioOutput(self, _output):
        pass

    def setSource(self, _source):
        pass

    def stop(self):
        pass


class _SilentAudioOutput:
    def setVolume(self, _volume):
        pass


class TestTTSNormalizationUI(unittest.TestCase):
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

    def test_tts_worker_normalizes_vietnamese_text(self):
        """Kiểm thử TTSWorker chuẩn hóa văn bản tiếng Việt đúng ngữ cảnh."""
        raw_text = "bác tôi bị bệnh K ở viện K, uống vitamin C, đeo vàng 18K xem video 4K giá 50k k thích mn"
        worker = TTSWorker(
            text=raw_text,
            voice_id="vi_mai_linh",
            model_id="kokoro_v1",
            lang_code="vi",
            voice_settings={},
            export_srt=False,
            provider="kokoro",
        )

        with patch("app.core.tts_worker.VibiClient") as mock_vibi:
            mock_client = MagicMock()
            mock_vibi.return_value = mock_client
            mock_client.generate_and_download.return_value = (None, None)

            worker.run()

            self.assertEqual(mock_client.generate_and_download.call_count, 1)
            called_text = mock_client.generate_and_download.call_args[1]["text"]

            self.assertIn("bệnh ca", called_text)
            self.assertIn("viện ca", called_text)
            self.assertNotIn("bệnh không", called_text)
            self.assertIn("vi-ta-min xê", called_text)
            self.assertIn("vàng 18 ca", called_text)
            self.assertIn("video 4 ca", called_text)
            self.assertIn("50 nghìn", called_text)
            self.assertIn("không thích mọi người", called_text)

    def test_tts_tab_ui_flow_with_normalization(self):
        """Kiểm thử luồng giao diện TTSTab khi kích hoạt tạo giọng nói với văn bản thông minh."""
        output_dir = Path(self.temp_dir.name) / "tts_out"
        output_dir.mkdir(parents=True, exist_ok=True)

        with patch("app.ui.tts_tab.QMediaPlayer", _SilentMediaPlayer), patch(
            "app.ui.tts_tab.QAudioOutput", _SilentAudioOutput
        ), patch(
            "app.ui.voice_lookup_tab.QMediaPlayer", _SilentMediaPlayer
        ), patch(
            "app.ui.voice_lookup_tab.QAudioOutput", _SilentAudioOutput
        ):
            tab = TTSTab()
            tab.configure_standalone(self.store, output_dir)

            # 1. Nhập văn bản & voice
            raw_text = "bác tôi bị bệnh K ở viện K, uống vitamin C, đeo vàng 18K xem video 4K giá 50k k thích mn"
            tab.txt_input.setPlainText(raw_text)
            tab.edit_output_name.setText("test_run_1")
            tab.set_selected_voice_id("vi_mai_linh")

            # 2. Mock TTSWorker.start để kiểm soát luồng giao diện
            with patch.object(TTSWorker, "start", return_value=None):
                tab.start_tts()

                # Kiểm tra trạng thái widget UI trong quá trình tạo
                self.assertFalse(tab.btn_start.isEnabled())
                self.assertTrue(tab.btn_cancel.isEnabled())
                self.assertIn("Đang kết nối", tab.lbl_status.text())

                # Lấy worker được tạo bởi TTSTab
                worker = tab.worker
                self.assertIsNotNone(worker)
                self.assertEqual(worker.voice_id, "vi_mai_linh")
                self.assertEqual(worker.text, raw_text)

            # 3. Giả lập tín hiệu worker hoàn thành tác vụ
            mock_audio = output_dir / "test_run_1" / "test_run_1.mp3"
            mock_audio.parent.mkdir(parents=True, exist_ok=True)
            mock_audio.write_bytes(b"dummy_mp3")

            tab.on_tts_finished(True, str(mock_audio), "", "")

            # Kiểm tra UI sau khi hoàn tất: nút start mở lại, trạng thái thành công
            self.assertTrue(tab.btn_start.isEnabled())
            self.assertIn("thành công", tab.lbl_status.text().lower())


if __name__ == "__main__":
    unittest.main()
