import os
import sys
import urllib.request
from pathlib import Path

editor_app_dir = Path(__file__).resolve().parent
kokoro_voices_dir = editor_app_dir / "models" / "kokoro" / "voices"
kokoro_voices_dir.mkdir(parents=True, exist_ok=True)

VI_VOICES = [
    "mai_linh.pt", "ngoc_huyen.pt", "diem_trinh.pt", "duc_an.pt",
    "duc_duy.pt", "hung_thinh.pt", "mai_loan.pt", "manh_dung.pt",
    "my_yen.pt", "phat_tai.pt", "storyvert.pt", "thanh_dat.pt",
    "thuc_trinh.pt", "tuan_ngoc.pt"
]

def main():
    print(f"B?t ??u t?i ti?p {len(VI_VOICES)} gi?ng Ti?ng Vi?t...")
    for voice_file in VI_VOICES:
        target_path = kokoro_voices_dir / f"vi_{voice_file}"
        if target_path.exists() and target_path.stat().st_size > 0:
            print(f"[SKIP] vi_{voice_file} ?A t?n t?i.")
            continue
        try:
            # Vietnam voices are at contextboxai/Kokoro-Vietnamese
            url = f"https://huggingface.co/contextboxai/Kokoro-Vietnamese/resolve/main/voicepacks/{voice_file}"
            urllib.request.urlretrieve(url, target_path)
            print(f"[OK] vi_{voice_file}")
        except Exception as e:
            print(f"[L?I] vi_{voice_file} (t? {url}): {e}")

    print("\nHoAn t?t!")

if __name__ == "__main__":
    main()
