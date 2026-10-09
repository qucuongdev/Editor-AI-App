from typing import Optional
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtWidgets import QLabel, QVBoxLayout

class PreviewImage(QLabel):
    """Show the same centered cover crop and aspect ratio as the export."""

    def __init__(self):
        super().__init__("Chọn một cảnh trên timeline để xem ảnh")
        self._source = QPixmap()
        self._gap = False
        self._aspect_ratio = 16 / 9
        self._placeholder = "Chọn một cảnh trên timeline để xem ảnh"
        self.setObjectName("video_preview_canvas")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(190)
        self.setWordWrap(True)
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setContentsMargins(18, 8, 18, 14)
        overlay_layout.addStretch()
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("video_preview_subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setTextFormat(Qt.TextFormat.PlainText)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.hide()
        overlay_layout.addWidget(self.subtitle_label)

    def set_aspect_ratio(self, value: str):
        self._aspect_ratio = {"16:9": 16 / 9, "9:16": 9 / 16, "1:1": 1}.get(value, 16 / 9)
        self._update_pixmap()

    def set_subtitle(self, text: str):
        if self.subtitle_label.text() == text:
            return
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))

    def set_image(self, path: Optional[Path]):
        self._gap = False
        self._source = QPixmap(str(path)) if path and path.is_file() else QPixmap()
        self._placeholder = ("Không tìm thấy hoặc không đọc được ảnh cảnh" if path else
                             "Chọn một cảnh trên timeline để xem ảnh")
        self._update_pixmap()

    def show_gap(self):
        self._gap = True
        self._source = QPixmap()
        self._update_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        if self._gap and self.width() > 0 and self.height() > 0:
            canvas = QPixmap(self.size())
            canvas.fill(QColor("#000000"))
            self.setPixmap(canvas)
        elif not self._source.isNull() and self.width() > 0 and self.height() > 0:
            frame_width = min(self.width(), round(self.height() * self._aspect_ratio))
            frame_height = min(self.height(), round(self.width() / self._aspect_ratio))
            frame_width = max(1, frame_width)
            frame_height = max(1, frame_height)
            scaled = self._source.scaled(
                frame_width, frame_height, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            crop = scaled.copy((scaled.width() - frame_width) // 2,
                               (scaled.height() - frame_height) // 2,
                               frame_width, frame_height)
            canvas = QPixmap(self.size())
            canvas.fill(QColor("#000000"))
            painter = QPainter(canvas)
            painter.drawPixmap((self.width() - frame_width) // 2,
                               (self.height() - frame_height) // 2, crop)
            painter.end()
            self.setPixmap(canvas)
            x_margin = (self.width() - frame_width) // 2
            bottom_margin = (self.height() - frame_height) // 2
            self.layout().setContentsMargins(x_margin + 12, 8, x_margin + 12,
                                             bottom_margin + 12)
            self.subtitle_label.setStyleSheet(
                f"font-size: {max(9, round(frame_height * 0.039))}px;"
            )
        else:
            self.clear()
            self.setText(self._placeholder)
