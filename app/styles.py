"""
Minimalist & Professional Dark Theme for PyQt6.
Design Principles:
- High contrast, clean hierarchy, neutral dark tones.
- No flashy gradients or redundant nested borders.
- Crisp typography, consistent spacing, intuitive controls.
"""

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication

import os
from pathlib import Path

def _get_qss_path():
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "app" / "assets" / "theme.qss"

def load_qss():
    qss_file = _get_qss_path()
    if qss_file.exists():
        return qss_file.read_text(encoding="utf-8")
    return ""


def setup_theme(app: QApplication):
    """Áp dụng theme gọn gàng, tối ưu thị giác và hiệu năng."""
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0e1014"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f3f5f7"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#101319"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#151922"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#151922"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f3f5f7"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f3f5f7"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#151922"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f3f5f7"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#4f7cff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#4f7cff"))

    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#4b5563"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#4b5563"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#4b5563"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor("#14151a"))

    app.setPalette(palette)
    app.setStyleSheet(load_qss())
