import os
import sys
import urllib.request
from pathlib import Path

editor_app_dir = Path(__file__).resolve().parent
kokoro_voices_dir = editor_app_dir / "models" / "kokoro" / "voices"
kokoro_voices_dir.mkdir(parents=True, exist_ok=True)

VOICE_FILES = [
    # American English Female voices
    "af_heart.pt", "af_alloy.pt", "af_aoede.pt", "af_bella.pt", "af_jessica.pt",
    "af_kore.pt", "af_nicole.pt", "af_nova.pt", "af_river.pt", "af_sarah.pt", "af_sky.pt",
    # American English Male voices
    "am_adam.pt", "am_echo.pt", "am_eric.pt", "am_fenrir.pt", "am_liam.pt",
    "am_michael.pt", "am_onyx.pt", "am_puck.pt", "am_santa.pt",
    # British English Female voices
    "bf_alice.pt", "bf_emma.pt", "bf_isabella.pt", "bf_lily.pt",
    # British English Male voices
    "bm_daniel.pt", "bm_fable.pt", "bm_george.pt", "bm_lewis.pt",
    # Vietnamese voices
    "vi_mai_linh.pt", "vi_ngoc_huyen.pt", "vi_diem_trinh.pt", "vi_duc_an.pt",
    "vi_duc_duy.pt", "vi_hung_thinh.pt", "vi_mai_loan.pt", "vi_manh_dung.pt",
    "vi_my_yen.pt", "vi_phat_tai.pt", "vi_storyvert.pt", "vi_thanh_dat.pt",
    "vi_thuc_trinh.pt", "vi_tuan_ngoc.pt"
]

def main():
    print(f"B?t ??u t?i {len(VOICE_FILES)} gi?ng...")
    for voice_file in VOICE_FILES:
        target_path = kokoro_voices_dir / voice_file
        if target_path.exists() and target_path.stat().st_size > 0:
            print(f"[SKIP] {voice_file} ?A t?n t?i.")
            continue
        try:
            url = f"https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/{voice_file}"
            urllib.request.urlretrieve(url, target_path)
            print(f"[OK] {voice_file}")
        except Exception as e:
            print(f"[L?I] {voice_file}: {e}")

    print("\nHoAn t?t!")

if __name__ == "__main__":
    main()
