"""
Kokoro Local TTS Engine for Editor-AI-App.
Supports hybrid execution:
1. Gradio API (http://127.0.0.1:7860/) if local web server is running.
2. Direct Python import fallback (kokoro_tts_local) if web server is offline.
"""

import os
import re
import time
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Callable

# Inject kokoro-tts/src into sys.path to enable direct mode
_kokoro_src_path = Path(__file__).resolve().parents[3] / "kokoro-tts" / "src"
if _kokoro_src_path.exists() and str(_kokoro_src_path) not in sys.path:
    sys.path.insert(0, str(_kokoro_src_path))

# Configure KOKORO_VOICES_DIR to point to Editor-AI-App's built-in models/kokoro/voices
_app_voices_dir = Path(__file__).resolve().parents[2] / "models" / "kokoro" / "voices"
if _app_voices_dir.exists() and "KOKORO_VOICES_DIR" not in os.environ:
    os.environ["KOKORO_VOICES_DIR"] = str(_app_voices_dir)

# Try importing gradio_client
try:
    from gradio_client import Client as GradioClient
    HAS_GRADIO_CLIENT = True
except ImportError:
    HAS_GRADIO_CLIENT = False

# Try importing local Kokoro module directly
try:
    from kokoro_tts_local.models import (
        build_model, list_available_voices, get_safe_voice_path, get_language_code_from_voice
    )
    HAS_DIRECT_KOKORO = True
except ImportError:
    HAS_DIRECT_KOKORO = False

# Patch vig2p phonemization for single Vietnamese vowel words ('y', 'u', 'e')
# By default sea_g2p treats isolated 'y' as English letter Y (/waɪ/ -> 'quai')
# causing "y tế" to sound like "quai tế", 'u' as /juː/ ('diu'), 'e' as /iː/.
def _patch_vig2p_for_vietnamese():
    try:
        import vig2p.core
        if not getattr(vig2p.core, "_editor_ai_patched", False):
            _orig_vig2p_fix_phonemes = vig2p.core.fix_phonemes

            def _safe_vietnamese_fix_phonemes(phonemes: str, source_text: Optional[str] = None, **kwargs) -> str:
                if source_text:
                    st = source_text.strip().lower()
                    if st == "y":
                        return "ˈi"
                    elif st == "u":
                        return "ˈu"
                    elif st == "e":
                        return "ˈɛ"
                return _orig_vig2p_fix_phonemes(phonemes, source_text=source_text, **kwargs)

            vig2p.core.fix_phonemes = _safe_vietnamese_fix_phonemes
            vig2p.core._editor_ai_patched = True
    except Exception:
        pass

_patch_vig2p_for_vietnamese()

GRADIO_SERVER_URL = "http://127.0.0.1:7860/"
_MODEL_CACHE = {}


def is_gradio_server_available(url: str = GRADIO_SERVER_URL) -> bool:
    """Check if Gradio TTS local server is online."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        res = s.connect_ex(("127.0.0.1", 7860))
        s.close()
        if res != 0:
            return False
    except Exception:
        return False

    if not HAS_GRADIO_CLIENT:
        return False
    try:
        client = GradioClient(url, verbose=False)
        return True
    except Exception:
        return False


VI_KOKORO_NAMES = {
    "vi_mai_linh": "🇻🇳 Mai Linh (Nữ - Truyền cảm)",
    "vi_ngoc_huyen": "🇻🇳 Ngọc Huyền (Nữ - Miền Bắc)",
    "vi_diem_trinh": "🇻🇳 Diễm Trinh (Nữ - Nhẹ nhàng)",
    "vi_mai_loan": "🇻🇳 Mai Loan (Nữ - Ấm áp)",
    "vi_my_yen": "🇻🇳 Mỹ Yến (Nữ - Trong trẻo)",
    "vi_thuc_trinh": "🇻🇳 Thục Trinh (Nữ - Trẻ trung)",
    "vi_duc_an": "🇻🇳 Đức An (Nam - Trầm ấm)",
    "vi_duc_duy": "🇻🇳 Đức Duy (Nam - Tự nhiên)",
    "vi_hung_thinh": "🇻🇳 Hùng Thịnh (Nam - Truyền cảm)",
    "vi_manh_dung": "🇻🇳 Mạnh Dũng (Nam - Mạnh mẽ)",
    "vi_phat_tai": "🇻🇳 Phát Tài (Nam - Hào sảng)",
    "vi_storyvert": "🇻🇳 Storyvert (Nam - Kể chuyện)",
    "vi_thanh_dat": "🇻🇳 Thành Đạt (Nam - Chuyên nghiệp)",
    "vi_tuan_ngoc": "🇻🇳 Tuấn Ngọc (Nam - Sang trọng)",
}


def _format_kokoro_voice_info(name: str, is_cloned: bool = False) -> Tuple[str, str, str]:
    """Return (display_name, gender, lang) for a Kokoro voice ID."""
    if is_cloned:
        clean = name.removeprefix("vi_").replace("_", " ").title()
        return f"✨ {clean} (Cloned)", "Tuỳ chỉnh", "vi" if name.startswith("vi_") else "en"

    if name in VI_KOKORO_NAMES:
        gender = "Nữ" if any(name.startswith(p) for p in ("vi_mai", "vi_ngoc", "vi_diem", "vi_my", "vi_thuc")) else "Nam"
        return VI_KOKORO_NAMES[name], gender, "vi"

    if name.startswith("vi_"):
        clean = name.removeprefix("vi_").replace("_", " ").title()
        gender = "Nữ" if any(name.startswith(p) for p in ("vi_mai", "vi_ngoc", "vi_diem", "vi_my", "vi_thuc")) else "Nam"
        return f"🇻🇳 {clean} (Tiếng Việt)", gender, "vi"

    gender = "Nữ" if len(name) > 1 and name[1] == "f" else "Nam"
    clean = name[3:].replace("_", " ").title() if len(name) > 3 and name[2] == "_" else name.replace("_", " ").title()

    prefix_map = {
        "af_": ("🇺🇸", "Mỹ", "en"),
        "am_": ("🇺🇸", "Mỹ", "en"),
        "bf_": ("🇬🇧", "Anh", "en"),
        "bm_": ("🇬🇧", "Anh", "en"),
        "zf_": ("🇨🇳", "Trung", "zh"),
        "zm_": ("🇨🇳", "Trung", "zh"),
        "jf_": ("🇯🇵", "Nhật", "ja"),
        "jm_": ("🇯🇵", "Nhật", "ja"),
        "ef_": ("🇪🇸", "Tây Ban Nha", "es"),
        "em_": ("🇪🇸", "Tây Ban Nha", "es"),
        "ff_": ("🇫🇷", "Pháp", "fr"),
        "if_": ("🇮🇹", "Ý", "it"),
        "im_": ("🇮🇹", "Ý", "it"),
        "pf_": ("🇵🇹", "Bồ Đào Nha", "pt"),
        "pm_": ("🇵🇹", "Bồ Đào Nha", "pt"),
        "hf_": ("🇮🇳", "Hindi", "hi"),
        "hm_": ("🇮🇳", "Hindi", "hi"),
    }
    for pfx, (flag, country, lang) in prefix_map.items():
        if name.startswith(pfx):
            return f"{flag} {clean} ({gender} - {country})", gender, lang

    return f"🎙️ {clean}", gender, "en"


def get_kokoro_voices() -> List[Dict[str, Any]]:
    """Scan and return all Kokoro voices from models/kokoro/voices and cloned_voices."""
    from app import config
    kokoro_voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "voices"
    cloned_voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices"

    discovered: Dict[str, bool] = {}

    # 1. Quét toàn bộ file .pt từ thư mục voices chính
    if kokoro_voices_dir.exists():
        for pt_file in sorted(kokoro_voices_dir.glob("*.pt")):
            discovered[pt_file.stem] = False

    # 2. Quét toàn bộ file .pt từ thư mục cloned_voices
    if cloned_voices_dir.exists():
        for pt_file in sorted(cloned_voices_dir.glob("*.pt")):
            discovered[pt_file.stem] = True

    # 3. Đảm bảo 14 giọng tiếng Việt chuẩn luôn có mặt
    for vid in VI_KOKORO_NAMES:
        if vid not in discovered:
            discovered[vid] = False

    # Sắp xếp theo nhóm ưu tiên: 1. Tiếng Việt, 2. Cloned, 3. US/UK, 4. Quốc tế khác
    def sort_key(item: Tuple[str, bool]):
        vid, is_cloned = item
        if vid.startswith("vi_") and not is_cloned:
            return (0, vid)
        if is_cloned:
            return (1, vid)
        if vid.startswith(("af_", "am_")):
            return (2, vid)
        if vid.startswith(("bf_", "bm_")):
            return (3, vid)
        return (4, vid)

    sorted_voices = sorted(discovered.items(), key=sort_key)

    results = []
    for name, is_cloned in sorted_voices:
        disp_name, gender, lang = _format_kokoro_voice_info(name, is_cloned)
        results.append({
            "voice_id": name,
            "name": disp_name,
            "raw_name": name,
            "provider": "kokoro",
            "provider_display": "🌸 Kokoro Local",
            "gender": gender,
            "language": lang,
            "preview_url": "",
            "description": f"Giọng Offline Kokoro Local ({name})",
            "is_cloned": is_cloned,
        })

    return results


def get_kokoro_voice_path(voice_id: str) -> Path:
    """Find voice pack path for voice_id in cloned_voices, voices, or localappdata fallback."""
    from app import config
    v_stem = Path(voice_id).stem
    candidates = [
        Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices" / f"{v_stem}.pt",
        Path(config.APP_DIR) / "models" / "kokoro" / "voices" / f"{v_stem}.pt",
    ]
    # Thêm biến thể vi_ hoặc bỏ vi_
    if v_stem.startswith("vi_"):
        raw_name = v_stem[3:]
        candidates.extend([
            Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices" / f"{raw_name}.pt",
            Path(config.APP_DIR) / "models" / "kokoro" / "voices" / f"{raw_name}.pt",
        ])
    else:
        vi_name = f"vi_{v_stem}"
        candidates.extend([
            Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices" / f"{vi_name}.pt",
            Path(config.APP_DIR) / "models" / "kokoro" / "voices" / f"{vi_name}.pt",
        ])

    for c in candidates:
        if c.exists() and c.is_file():
            return c

    # Fallback to get_safe_voice_path if available
    if HAS_DIRECT_KOKORO:
        try:
            safe_p = get_safe_voice_path(voice_id)
            if safe_p.exists() and safe_p.is_file():
                return safe_p
        except Exception:
            pass

    return Path(config.APP_DIR) / "models" / "kokoro" / "voices" / f"{v_stem}.pt"


def get_kokoro_language_code(voice_id: str) -> str:
    """Detect language code for Kokoro pipeline ('vi', 'a', 'b', 'z', 'j', 'e', 'f', 'h', 'i', 'p')."""
    name = Path(voice_id).stem.lower()
    if name.startswith("vi_") or name in VI_KOKORO_NAMES:
        return "vi"
    if HAS_DIRECT_KOKORO:
        try:
            code = get_language_code_from_voice(name)
            if code == "v":
                return "vi"
            return code
        except Exception:
            pass
    prefix = name[:2]
    prefix_to_lang = {
        "af": "a", "am": "a",
        "bf": "b", "bm": "b",
        "zf": "z", "zm": "z",
        "jf": "j", "jm": "j",
        "ef": "e", "em": "e",
        "ff": "f",
        "hf": "h", "hm": "h",
        "if": "i", "im": "i",
        "pf": "p", "pm": "p",
        "vi": "vi",
    }
    return prefix_to_lang.get(prefix, "a")


def _get_direct_model(lang_code: str = "vi", device: Optional[str] = None):
    """Retrieve or build direct Python Kokoro model instance."""
    if lang_code == "v":
        lang_code = "vi"
    import torch
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    key = (lang_code, device)
    if key not in _MODEL_CACHE:
        _MODEL_CACHE[key] = build_model(None, device=device, lang_code=lang_code)
    return _MODEL_CACHE[key], device


def _format_srt_time(seconds: float) -> str:
    millis = int(round((seconds % 1) * 1000))
    total_seconds = int(seconds)
    if millis >= 1000:
        total_seconds += 1
        millis -= 1000
    secs = total_seconds % 60
    mins = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_kokoro_tts(
    text: str,
    voice_id: str = "vi_mai_linh",
    output_path: Optional[Path] = None,
    speed: float = 1.0,
    export_srt: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None
) -> Tuple[Path, Optional[Path]]:
    """Generate audio using local Gradio server or direct Python fallback, with optional SRT generation."""

    if is_cancelled and is_cancelled():
        raise RuntimeError("Tác vụ đã bị người dùng hủy.")

    if not text or not text.strip():
        raise ValueError("Văn bản truyền vào rỗng!")

    is_vietnamese = voice_id.startswith("vi_")
    if not is_vietnamese and HAS_DIRECT_KOKORO:
        try:
            is_vietnamese = (get_language_code_from_voice(voice_id) == "v")
        except Exception:
            pass
    if is_vietnamese:
        try:
            from app.core.text_normalizer import normalize_vietnamese_text
            text = normalize_vietnamese_text(text)
        except Exception:
            pass

    if output_path is None:
        from app import config
        target_dir = config.TTS_DOWNLOADS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = target_dir / f"kokoro_{voice_id}_{timestamp}.mp3"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Try Gradio API if server at http://127.0.0.1:7860/ is running
    if is_gradio_server_available(GRADIO_SERVER_URL):
        try:
            if progress_callback:
                progress_callback({"status": "Đang gọi Kokoro Web API (7860)..."})

            client = GradioClient(GRADIO_SERVER_URL, verbose=False)
            fmt = "mp3" if output_path.suffix.lower() == ".mp3" else "wav"
            res = client.predict(
                voice_id,
                text,
                fmt,
                float(speed),
                api_name="/generate_tts_with_logs"
            )
            # res can be a tuple (file_path, log_str) or single path string
            temp_file_path = res[0] if isinstance(res, (tuple, list)) else res
            if temp_file_path and Path(temp_file_path).exists():
                shutil.copy2(str(temp_file_path), str(output_path))
                # Return immediately if Gradio succeeds
                srt_path = None
                if export_srt:
                    try:
                        import soundfile as sf
                        info = sf.info(str(output_path))
                        dur = info.duration
                        srt_path = output_path.with_suffix(".srt")
                        start_str = _format_srt_time(0.0)
                        end_str = _format_srt_time(dur)
                        srt_path.write_text(f"1\n{start_str} --> {end_str}\n{text}\n", encoding="utf-8")
                    except Exception as e:
                        print(f"[Kokoro Engine] Warning: Could not generate dummy SRT: {e}")
                        srt_path = None
                return output_path, srt_path
        except Exception as e:
            print(f"[Kokoro Engine] Gradio API note ({e}), using direct local model execution.")

    # 2. Direct Python execution
    if not HAS_DIRECT_KOKORO:
        if output_path.exists():
            return output_path, None
        raise RuntimeError(
            "Kokoro Local chưa sẵn sàng: Cần khởi động Server Kokoro (cổng 7860) "
            "hoặc cài đặt gói kokoro (pip install kokoro soundfile).\n\n"
            "👉 Hãy chạy file 'CHAY_TTS.cmd' trong thư mục 'kokoro-tts' để bật Server Kokoro Local,\n"
            "hoặc chuyển sang nền tảng '⚡ ElevenLabs', '🤖 MiniMax' hoặc '🎬 CapCut' để tạo giọng online ngay!"
        )

    if progress_callback:
        progress_callback({"status": "Đang khởi tạo model Kokoro Local..."})

    lang_code = get_kokoro_language_code(voice_id)
    model, device = _get_direct_model(lang_code=lang_code)

    voice_path = get_kokoro_voice_path(voice_id)
    if not voice_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file voice pack cho giọng '{voice_id}' tại {voice_path}")

    if progress_callback:
        progress_callback({"status": "Đang tổng hợp giọng nói & phụ đề..."})

    generator = model.iter_speech(text, voice=str(voice_path), speed=float(speed), split_pattern=r'\n+')
    audio_chunks = []
    srt_entries = []
    current_time = 0.0
    sub_index = 1

    for graphemes, phonemes, audio in generator:
        if is_cancelled and is_cancelled():
            raise RuntimeError("Tác vụ đã bị người dùng hủy.")
        audio_chunks.append(audio)

        duration = len(audio) / 24000.0
        start_time = current_time
        end_time = start_time + duration
        current_time = end_time

        segment_text = str(graphemes).strip()
        if segment_text:
            start_str = _format_srt_time(start_time)
            end_str = _format_srt_time(end_time)
            srt_entries.append(f"{sub_index}\n{start_str} --> {end_str}\n{segment_text}\n")
            sub_index += 1

    if not audio_chunks:
        raise RuntimeError("Kokoro không tạo ra dữ liệu âm thanh nào!")

    import numpy as np
    full_audio = np.concatenate(audio_chunks)

    if progress_callback:
        progress_callback({"status": "Đang ghi file audio & srt..."})

    import soundfile as sf
    # Save audio
    if output_path.suffix.lower() == ".mp3":
        try:
            from pydub import AudioSegment
            temp_wav = output_path.with_suffix(".temp.wav")
            sf.write(str(temp_wav), full_audio, 24000)
            sound = AudioSegment.from_wav(str(temp_wav))
            sound.export(str(output_path), format="mp3", bitrate="192k")
            if temp_wav.exists():
                temp_wav.unlink()
        except Exception:
            output_path = output_path.with_suffix(".wav")
            sf.write(str(output_path), full_audio, 24000)
    else:
        sf.write(str(output_path), full_audio, 24000)

    # Save SRT file if requested
    srt_path: Optional[Path] = None
    if export_srt and srt_entries:
        srt_path = output_path.with_suffix(".srt")
        try:
            srt_path.write_text("\n".join(srt_entries), encoding="utf-8")
        except Exception as e:
            print(f"[Kokoro Engine] Warning: Could not write SRT file: {e}")
            srt_path = None

    return output_path, srt_path
