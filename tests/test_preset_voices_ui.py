import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtWidgets import QApplication

from app.core.standalone_state import StandaloneStateStore
from app.core.preset_voices import (
    get_preset_voices,
    get_default_voice_for_provider,
    find_voice_name,
)
from app.ui.tts_tab import TTSTab


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


class TestPresetVoicesUI(unittest.TestCase):
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

    def test_preset_voices_core_definitions(self):
        """Kiểm thử core preset_voices cung cấp đầy đủ giọng cho cả 4 provider."""
        for provider in ("kokoro", "elevenlabs", "minimax", "capcut"):
            presets = get_preset_voices(provider)
            self.assertGreater(len(presets), 0, f"Provider {provider} phải có ít nhất 1 preset voice")
            def_id, def_name = get_default_voice_for_provider(provider)
            self.assertTrue(bool(def_id), f"Provider {provider} phải có default voice_id")
            self.assertTrue(bool(def_name), f"Provider {provider} phải có default voice_name")

        # Kiểm tra một số giọng tiếng Việt quan trọng
        self.assertIsNotNone(find_voice_name("elevenlabs", "6adFm46eyy74snVn6YrT"))
        self.assertIsNotNone(find_voice_name("kokoro", "vi_mai_linh"))
        self.assertIsNotNone(find_voice_name("minimax", "moss_audio_01"))
        self.assertIsNotNone(find_voice_name("capcut", "vi_female_1"))

    def test_tts_tab_loads_built_in_presets_on_startup(self):
        """Kiểm thử khi mở TTSTab, ComboBox đã nạp sẵn danh sách giọng ElevenLabs."""
        tab = self._create_tab()

        # ComboBox phải có nhiều hơn 2 items (nhiều preset + dòng tra cứu)
        self.assertGreater(tab.combo_voice.count(), 2)

        # Giọng hiện tại không được rỗng
        self.assertTrue(bool(tab.current_voice_id()))

        # Dropdown chỉ hiện 8 items một lúc, có thanh cuộn mượt mà
        self.assertEqual(tab.combo_voice.maxVisibleItems(), 8)

        # Item cuối cùng phải là mục tra cứu thêm
        last_idx = tab.combo_voice.count() - 1
        self.assertEqual(tab.combo_voice.itemData(last_idx), "__LOOKUP__")
        self.assertIn("Tra cứu", tab.combo_voice.itemText(last_idx))

    def test_switching_provider_loads_matching_presets(self):
        """Kiểm thử khi đổi nền tảng, ComboBox tự động nạp các giọng có sẵn của nền tảng đó."""
        tab = self._create_tab()

        # 1. Kokoro
        kokoro_idx = tab.combo_provider.findData("kokoro")
        tab.combo_provider.setCurrentIndex(kokoro_idx)
        self.assertEqual(tab.current_voice_id(), "vi_mai_linh")
        kokoro_voice_ids = [tab.combo_voice.itemData(i) for i in range(tab.combo_voice.count())]
        self.assertIn("vi_mai_linh", kokoro_voice_ids)
        self.assertIn("vi_ngoc_huyen", kokoro_voice_ids)
        self.assertIn("vi_duc_an", kokoro_voice_ids)

        # 2. MiniMax
        minimax_idx = tab.combo_provider.findData("minimax")
        tab.combo_provider.setCurrentIndex(minimax_idx)
        self.assertEqual(tab.current_voice_id(), "moss_audio_01")
        minimax_voice_ids = [tab.combo_voice.itemData(i) for i in range(tab.combo_voice.count())]
        self.assertIn("moss_audio_01", minimax_voice_ids)

        # 3. CapCut
        capcut_idx = tab.combo_provider.findData("capcut")
        tab.combo_provider.setCurrentIndex(capcut_idx)
        self.assertEqual(tab.current_voice_id(), "vi_female_1")
        capcut_voice_ids = [tab.combo_voice.itemData(i) for i in range(tab.combo_voice.count())]
        self.assertIn("vi_female_1", capcut_voice_ids)

    def test_user_can_select_preset_directly_without_searching(self):
        """Người dùng có thể bấm chọn ngay một giọng có sẵn trong ComboBox mà không cần tìm kiếm."""
        tab = self._create_tab()

        # Chọn giọng thứ 2 trong ElevenLabs
        tab.combo_voice.setCurrentIndex(1)
        picked_id = tab.combo_voice.currentData()
        self.assertEqual(tab.current_voice_id(), picked_id)
        # Vẫn ở tab Tạo giọng, không bị đá sang tab Tra cứu
        self.assertEqual(tab.tab_widget.currentIndex(), 0)

    def test_lookup_option_in_combobox_triggers_lookup_tab(self):
        """Khi chọn dòng 'Tra cứu thêm...' ở cuối ComboBox, app chuyển sang tab Tra cứu."""
        tab = self._create_tab()
        last_idx = tab.combo_voice.count() - 1
        self.assertEqual(tab.combo_voice.itemData(last_idx), "__LOOKUP__")

        # Kích hoạt dòng Tra cứu
        tab.combo_voice.setCurrentIndex(last_idx)

        # Tab widget phải chuyển sang Subtab 1 (Tra cứu Voice)
        self.assertEqual(tab.tab_widget.currentIndex(), 1)
        # ComboBox không bị kẹt ở dòng __LOOKUP__
        self.assertNotEqual(tab.combo_voice.currentData(), "__LOOKUP__")

    def test_lookup_button_opens_lookup_tab(self):
        """Bấm nút 'Tra cứu...' bên cạnh ComboBox chuyển sang tab Tra cứu."""
        tab = self._create_tab()
        self.assertEqual(tab.tab_widget.currentIndex(), 0)

        tab.btn_lookup_voice.click()
        self.assertEqual(tab.tab_widget.currentIndex(), 1)

    def test_custom_voice_picked_from_lookup_is_selected_and_prepended(self):
        """Khi chọn dùng một giọng từ tab Tra cứu, giọng đó tự động thêm vào ComboBox và được chọn."""
        tab = self._create_tab()

        tab.on_voice_picked_from_lookup("custom_voice_123", "Giọng Sơn Tùng", "elevenlabs", "vi")

        self.assertEqual(tab.current_voice_id(), "custom_voice_123")
        self.assertEqual(tab.combo_voice.currentText(), "Giọng Sơn Tùng")
        self.assertEqual(tab.tab_widget.currentIndex(), 0)

    def test_cloned_voice_success_selects_and_switches_to_kokoro(self):
        """Khi clone giọng thành công từ subtab 3, app chuyển sang Kokoro và chọn giọng clone."""
        tab = self._create_tab()

        tab.on_voice_cloned_success("giong_doc_dac_biet", "/dummy/path.pt")

        self.assertEqual(tab.combo_provider.currentData(), "kokoro")
        self.assertEqual(tab.current_voice_id(), "giong_doc_dac_biet")
        self.assertIn("giong_doc_dac_biet", tab.combo_voice.currentText())
        self.assertEqual(tab.tab_widget.currentIndex(), 0)


    def test_kokoro_voices_always_contains_all_14_vietnamese_voices(self):
        """get_kokoro_voices luôn trả về đủ 14 giọng tiếng Việt kể cả khi có cloned voices."""
        from app.core.kokoro_engine import get_kokoro_voices
        voices = get_kokoro_voices()
        v_ids = [v["voice_id"] for v in voices]
        expected_vi = [
            "vi_mai_linh", "vi_ngoc_huyen", "vi_diem_trinh", "vi_duc_an",
            "vi_duc_duy", "vi_hung_thinh", "vi_mai_loan", "vi_manh_dung",
            "vi_my_yen", "vi_phat_tai", "vi_storyvert", "vi_thanh_dat",
            "vi_thuc_trinh", "vi_tuan_ngoc"
        ]
        for vid in expected_vi:
            self.assertIn(vid, v_ids, f"Giọng {vid} phải có trong get_kokoro_voices")

    def test_voice_lookup_unconfigured_api_key_shows_presets(self):
        """Khi chưa cấu hình API Key, tab Tra cứu vẫn hiển thị danh sách giọng có sẵn thay vì báo lỗi trống trơn."""
        tab = self._create_tab()
        lookup = tab.voice_lookup_tab

        # Test với nguồn ElevenLabs
        lookup.combo_source.setCurrentIndex(lookup.combo_source.findData("elevenlabs_default"))
        lookup.load_voices()
        if lookup.worker:
            lookup.worker.wait()
        self.app.processEvents()

        self.assertGreater(lookup.table.rowCount(), 0, "Bảng tra cứu phải hiển thị các giọng có sẵn")
        first_voice_id = lookup.table.item(0, 2).text()
        self.assertTrue(bool(first_voice_id))

    def test_open_voice_lookup_syncs_source_with_active_provider(self):
        """Khi bấm Tra cứu từ tab Tạo giọng, nguồn trong tab Tra cứu tự động đồng bộ theo nền tảng đang chọn."""
        tab = self._create_tab()

        # Chọn CapCut
        tab.combo_provider.setCurrentIndex(tab.combo_provider.findData("capcut"))
        tab.open_voice_lookup()
        self.assertEqual(tab.voice_lookup_tab.combo_source.currentData(), "capcut_system")

    def test_kokoro_scans_all_70_voices_from_disk(self):
        """get_kokoro_voices phải quét toàn bộ 70+ giọng (68 file trong voices + cloned voices)."""
        from app.core.kokoro_engine import get_kokoro_voices
        voices = get_kokoro_voices()
        v_ids = [v["voice_id"] for v in voices]

        # Phải có ít nhất 70 giọng
        self.assertGreaterEqual(len(voices), 70, f"Kokoro phải có ít nhất 70 giọng, thực tế có: {len(voices)}")

        # Kiểm tra sự có mặt của các nhóm ngôn ngữ khác nhau
        self.assertIn("af_bella", v_ids)
        self.assertIn("am_adam", v_ids)
        self.assertIn("bf_alice", v_ids)
        self.assertIn("bm_george", v_ids)
        self.assertIn("zf_xiaobei", v_ids)
        self.assertIn("jf_alpha", v_ids)
        self.assertIn("ef_dora", v_ids)
        self.assertIn("ff_siwis", v_ids)
        self.assertIn("if_sara", v_ids)
        self.assertIn("vi_clone_sample_voice_jane", v_ids)

    def test_kokoro_voice_path_and_language_detection(self):
        """get_kokoro_voice_path và get_kokoro_language_code phải hoạt động chính xác."""
        from app.core.kokoro_engine import get_kokoro_voice_path, get_kokoro_language_code

        # 1. Voice path
        vi_path = get_kokoro_voice_path("vi_mai_linh")
        self.assertTrue(vi_path.exists(), f"File {vi_path} phải tồn tại")
        self.assertTrue(vi_path.name.endswith(".pt"))

        bella_path = get_kokoro_voice_path("af_bella")
        self.assertTrue(bella_path.exists(), f"File {bella_path} phải tồn tại")

        # 2. Language detection
        self.assertEqual(get_kokoro_language_code("vi_mai_linh"), "vi")
        self.assertEqual(get_kokoro_language_code("vi_ngoc_huyen"), "vi")
        self.assertEqual(get_kokoro_language_code("af_bella"), "a")
        self.assertEqual(get_kokoro_language_code("am_adam"), "a")
        self.assertEqual(get_kokoro_language_code("bf_alice"), "b")
        self.assertEqual(get_kokoro_language_code("zf_xiaobei"), "z")
        self.assertEqual(get_kokoro_language_code("jf_alpha"), "j")


if __name__ == "__main__":
    unittest.main()
