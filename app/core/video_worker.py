from typing import List, Dict, Any, Optional
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from app.core import video_creator

class VideoRenderWorker(QThread):
    """Worker chạy tiến trình FFmpeg ghép video ngầm trên luồng riêng."""
    progress_updated = pyqtSignal(int, str)
    render_finished = pyqtSignal(bool, dict)

    def __init__(
        self,
        timeline: List[Dict[str, Any]],
        audio_path: Path,
        output_path: Path,
        total_audio_duration: float,
        aspect_ratio: str = "16:9",
        fps: int = 30,
        subtitles: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__()
        self.timeline = timeline
        self.audio_path = audio_path
        self.output_path = output_path
        self.total_audio_duration = total_audio_duration
        self.aspect_ratio = aspect_ratio
        self.fps = fps
        self.subtitles = subtitles
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        def on_prog(pct: int, msg: str):
            self.progress_updated.emit(pct, msg)

        render_options = dict(
            timeline=self.timeline,
            audio_path=self.audio_path,
            output_path=self.output_path,
            total_audio_duration=self.total_audio_duration,
            aspect_ratio=self.aspect_ratio,
            fps=self.fps,
            progress_callback=on_prog,
            is_cancelled=lambda: self._is_cancelled
        )
        if self.subtitles is not None:
            render_options["subtitles"] = self.subtitles
        try:
            res = video_creator.render_video(**render_options)
        except Exception as exc:
            res = {"success": False, "error": str(exc)}
        self.render_finished.emit(res.get("success", False), res)


