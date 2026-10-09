from typing import Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

class LoadingSpinner(QWidget):
    """Spinner tròn nhỏ cho các tác vụ đang xử lý."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(18, 18)
        self.setVisible(False)

    def start(self):
        self._step = 0
        self.setVisible(True)
        self._timer.start(80)
        self.update()

    def stop(self):
        self._timer.stop()
        self.setVisible(False)

    def _advance(self):
        self._step = (self._step + 1) % 12
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        for index in range(12):
            alpha = max(45, 255 - ((index - self._step) % 12) * 18)
            painter.setPen(QPen(QColor(59, 130, 246, alpha), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(0, -7, 0, -4)
            painter.rotate(30)

