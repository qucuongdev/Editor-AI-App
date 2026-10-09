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

GRADIO_SERVER_URL = "http://127.0.0.1:7860/"
_MODEL_CACHE = {}


def is_gradio_server_available(url: str = GRADIO_SERVER_URL) -> bool:
    """Check if Gradio TTS local server is online."""
    if not HAS_GRADIO_CLIENT:
        return False
    try:
        client = GradioClient(url, verbose=False)
        return True
    except Exception:
        return False


def get_kokoro_voices() -> List[Dict[str, Any]]:
    """Return normalized list of Kokoro voices for Editor-AI-App UI."""
    voice_names = []
    if HAS_DIRECT_KOKORO:
        try:
            voice_names = list_available_voices()
        except Exception:
            pass

    # Add cloned voices
    try:
        from app import config
        cloned_voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices"
        if cloned_voices_dir.exists():
            for pt_file in cloned_voices_dir.glob("*.pt"):
                name = pt_file.stem
                if name not in voice_names:
                    voice_names.append(name)
    except Exception:
        pass

    if not voice_names:
        # Default fallback list of common Kokoro voices
        voice_names = [
            "vi_mai_linh", "vi_ngoc_huyen", "vi_diem_trinh", "vi_duc_an",
            "vi_duc_duy", "vi_hung_thinh", "vi_mai_loan", "vi_manh_dung",
            "vi_my_yen", "vi_phat_tai", "vi_storyvert", "vi_thanh_dat",
            "vi_thuc_trinh", "vi_tuan_ngoc",
            "af_bella", "af_sarah", "am_adam", "bf_alice", "bm_george"
        ]

    results = []
    for name in voice_names:
        clean_name = name.removeprefix("vi_").replace("_", " ").title()
        if name.startswith("vi_"):
            disp_name = f"🇻🇳 {clean_name} (Tiếng Việt)"
            lang = "vi"
        elif name.startswith(("af_", "am_")):
            disp_name = f"🇺🇸 {clean_name} (Mỹ)"
            lang = "en"
        elif name.startswith(("bf_", "bm_")):
            disp_name = f"🇬🇧 {clean_name} (Anh)"
            lang = "en"
        elif name.startswith(("zf_", "zm_")):
            disp_name = f"🇨🇳 {clean_name} (Trung)"
            lang = "zh"
        else:
            disp_name = f"🎙️ {clean_name}"
            lang = "en"

        is_cloned = False
        try:
            from app import config
            cloned_path = Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices" / f"{name}.pt"
            if cloned_path.exists():
                is_cloned = True
        except:
            pass

        results.append({
            "voice_id": name,
            "name": disp_name,
            "raw_name": name,
            "provider": "kokoro",
            "provider_display": "🌸 Kokoro Local",
            "gender": "Nữ" if name.startswith(("af_", "bf_", "zf_", "vi_mai", "vi_ngoc", "vi_diem", "vi_my", "vi_thuc")) else "Nam",
            "language": lang,
            "preview_url": "",
            "description": f"Giọng Offline Kokoro Local ({name})",
            "is_cloned": is_cloned
        })

    return results


def _get_direct_model(lang_code: str = "v", device: Optional[str] = None):
    """Retrieve or build direct Python Kokoro model instance."""
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

    if voice_id.startswith("vi_"):
        try:
            from app.core.text_normalizer import normalize_vietnamese_text
            text = normalize_vietnamese_text(text)
        except ImportError:
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
        raise RuntimeError("Không thể sử dụng Kokoro Local: Cả Gradio Server (7860) và module direct đều không khả dụng!")

    if progress_callback:
        progress_callback({"status": "Đang khởi tạo model Kokoro Local..."})

    lang_code = get_language_code_from_voice(voice_id)
    model, device = _get_direct_model(lang_code=lang_code)

    from app import config
    cloned_path = Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices" / f"{voice_id}.pt"
    if cloned_path.exists():
        voice_path = cloned_path
    else:
        voice_path = get_safe_voice_path(voice_id)
        
    if not voice_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file voice pack {voice_path}")

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
