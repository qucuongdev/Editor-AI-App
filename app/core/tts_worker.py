from typing import Optional, Dict, Any
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from app.core.vibi_client import VibiClient

class TTSWorker(QThread):
    """Worker tạo giọng nói qua Vibi API."""
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    task_finished = pyqtSignal(bool, str, str, str)
    account_updated = pyqtSignal(dict)

    def __init__(
        self,
        text: str,
        voice_id: str,
        model_id: str,
        lang_code: str,
        voice_settings: Dict[str, Any],
        export_srt: bool,
        provider: str = "elevenlabs",
        output_filename: Optional[str] = None,
        output_dir: Optional[Path] = None
    ):
        super().__init__()
        self.text = text
        self.voice_id = voice_id
        self.model_id = model_id
        self.lang_code = lang_code
        self.voice_settings = voice_settings
        self.export_srt = export_srt
        self.provider = provider
        self.output_filename = output_filename
        self.output_dir = output_dir
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def _refresh_credits_safely(self, client: VibiClient):
        try:
            info = client.get_account_info()
            self.account_updated.emit(info)
        except Exception:
            pass

    def run(self):
        client = VibiClient()
        if self.provider != "kokoro":
            if not client.is_configured():
                self.task_finished.emit(False, "", "", "Chưa có Voice API Key! Vào Cài đặt để nhập Key.")
                return

            self.status_updated.emit("Đang kiểm tra tài khoản và số dư...")
            self.progress_updated.emit(10)

            try:
                acc_info = client.get_account_info()
                self.account_updated.emit(acc_info)
            except Exception as e:
                self.task_finished.emit(False, "", "", f"Lỗi xác thực Voice API: {e}")
                return

        self.status_updated.emit("Đang khởi tạo tạo giọng nói...")
        self.progress_updated.emit(20)

        if self.provider == "kokoro":
            chunks = [self.text]
        else:
            chunks = VibiClient.split_long_text(self.text, max_chars=3500)
        total_chunks = len(chunks)

        last_audio = None
        last_srt = None

        try:
            for idx, chunk in enumerate(chunks, 1):
                if self._is_cancelled:
                    self._refresh_credits_safely(client)
                    self.task_finished.emit(False, "", "", "Tác vụ đã bị hủy.")
                    return

                chunk_filename = self.output_filename
                if total_chunks > 1 and chunk_filename:
                    stem = Path(chunk_filename).stem
                    chunk_filename = f"{stem}_part_{idx}.mp3"

                def on_prog(task_dict):
                    status = task_dict.get("status", "pending")
                    chunk_info = f"Đoạn {idx}/{total_chunks}: " if total_chunks > 1 else ""
                    self.status_updated.emit(f"{chunk_info}Đang tạo giọng ({status})...")

                audio_p, srt_p = client.generate_and_download(
                    text=chunk,
                    voice_id=self.voice_id,
                    output_filename=chunk_filename,
                    output_dir=self.output_dir,
                    model_id=self.model_id,
                    language_code=self.lang_code,
                    provider=self.provider,
                    voice_settings=self.voice_settings,
                    export_transcript=self.export_srt,
                    progress_callback=on_prog,
                    is_cancelled=lambda: self._is_cancelled
                )

                last_audio = audio_p
                last_srt = srt_p

            self.progress_updated.emit(100)
            self.status_updated.emit("Hoàn tất tạo giọng nói.")
            self._refresh_credits_safely(client)
            self.task_finished.emit(
                True,
                str(last_audio) if last_audio else "",
                str(last_srt) if last_srt else "",
                "Thành công!"
            )
        except Exception as e:
            self._refresh_credits_safely(client)
            self.task_finished.emit(False, "", "", str(e))


