from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox


class VoiceSelectorComboBox(QComboBox):
    """Voice selector dropdown with preset voices and lookup shortcut."""
    lookup_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Giới hạn kích thước combobox chuẩn, tránh bị co giãn quá khổ
        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        # Giới hạn hiển thị 8 tùy chọn vừa vặn, cuộn chuột mượt mà (tránh bung to toàn màn hình)
        self.setMaxVisibleItems(8)
        view = self.view()
        if view:
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def showPopup(self):
        super().showPopup()
        popup = self.view().parentWidget()
        if popup:
            row_h = self.view().sizeHintForRow(0) or 26
            max_h = row_h * self.maxVisibleItems() + 12
            if popup.height() > max_h:
                popup.resize(popup.width(), max_h)
