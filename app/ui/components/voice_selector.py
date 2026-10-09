from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox

class VoiceSelectorComboBox(QComboBox):
    """A read-only voice selector that routes users to voice lookup."""
    lookup_requested = pyqtSignal()

    def showPopup(self) -> None:
        self.lookup_requested.emit()


