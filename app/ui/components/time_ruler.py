from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget
from app.core import video_creator

class TimeRuler(QWidget):
    """Paint a time ruler and let users seek at its exact timeline position."""

    seek_requested = pyqtSignal(int)
    PIXELS_PER_SECOND = 65
    TRACK_OFFSET = 58

    def __init__(self):
        super().__init__()
        self.duration = 0.0
        self.position = 0.0
        self.setFixedHeight(27)
        self.setMinimumWidth(self.TRACK_OFFSET + 1)
        self.setMouseTracking(True)

    def set_duration(self, duration: float):
        self.duration = max(0.0, duration)
        self.setMinimumWidth(self.TRACK_OFFSET + round(self.duration * self.PIXELS_PER_SECOND))
        self.update()

    def set_position(self, position: float):
        self.position = position
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#171b24"))
        painter.setPen(QPen(QColor("#64748b")))
        painter.drawText(4, 20, "GIÂY")
        if self.duration <= 0:
            return
        interval = next((step for step in (1, 2, 5, 10, 15, 30, 60, 120, 300, 600)
                         if step * self.PIXELS_PER_SECOND >= 62), 600)
        tick = 0
        while tick <= self.duration:
            x = self.TRACK_OFFSET + round(tick * self.PIXELS_PER_SECOND)
            painter.drawLine(x, 19, x, 30)
            painter.drawText(x + 3, 15, video_creator.format_time(tick).split(".")[0])
            tick += interval
        x = self.TRACK_OFFSET + round(self.position * self.PIXELS_PER_SECOND)
        painter.setPen(QPen(QColor("#7397ec"), 2))
        painter.drawLine(x, 0, x, self.height())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._seek_at(event.position().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._seek_at(event.position().x())

    def _seek_at(self, x: float):
        position = max(0.0, min(self.duration, (x - self.TRACK_OFFSET) / self.PIXELS_PER_SECOND))
        self.seek_requested.emit(round(position * 1000))


