#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini_key_dialog.py: Hộp thoại cấu hình Google Gemini API Key.
Cung cấp nút mở trực tiếp trang lấy API Key miễn phí từ Google AI Studio (1-Click),
tính năng kiểm tra kết nối (Ping/Verify API Key) thực tế, và tự động quét
danh sách Model khả dụng từ Google (không hardcode).
"""

from pathlib import Path
from typing import List, Dict, Any, Union
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QSize, QThread
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QMessageBox, QApplication
)

from app import config
from app.core.gemini_client import GEMINI_MODELS, verify_gemini_connection

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


class GeminiVerifyWorker(QThread):
    """Luồng nền kiểm tra kết nối tới Google Gemini API và lấy danh sách model."""
    finished = pyqtSignal(bool, str, list)  # (success, message, models)

    def __init__(self, api_key: str, parent=None):
        super().__init__(parent)
        self.api_key = api_key

    def run(self):
        success, msg, models = verify_gemini_connection(self.api_key)
        self.finished.emit(success, msg, models)


class GeminiKeyDialog(QDialog):
    """Hộp thoại cấu hình Google Gemini API Key trực tiếp từ thanh Sidebar."""

    key_saved = pyqtSignal(str, str)  # (api_key, model_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cấu Hình Google Gemini AI")
        self.setFixedWidth(580)
        self.setModal(True)
        self.worker: GeminiVerifyWorker | None = None
        self._last_verified_key = getattr(config, "GEMINI_API_KEY", "") if getattr(config, "GEMINI_CONNECTED", False) else ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        # Header Title
        title_row = QHBoxLayout()
        lbl_icon = QLabel("🤖")
        lbl_icon.setStyleSheet("font-size: 24px;")
        title_row.addWidget(lbl_icon)

        title_info = QVBoxLayout()
        title_info.setSpacing(2)
        lbl_title = QLabel("Google Gemini AI Studio")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        lbl_sub = QLabel("Sử dụng AI thực thụ để tự động sáng tạo kịch bản và phân cảnh video độc nhất.")
        lbl_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_info.addWidget(lbl_title)
        title_info.addWidget(lbl_sub)
        title_row.addLayout(title_info, stretch=1)
        layout.addLayout(title_row)

        # 1. Hộp hướng dẫn & Nút mở trực tiếp trang lấy Key (Tinh gọn 1 hàng)
        guide_box = QFrame()
        guide_box.setObjectName("gemini_guide_banner")
        guide_box.setStyleSheet(
            "QFrame#gemini_guide_banner {"
            "  background-color: #082f49; border: 1px solid #0284c7; "
            "  border-radius: 8px;"
            "}"
        )
        guide_layout = QHBoxLayout(guide_box)
        guide_layout.setContentsMargins(12, 8, 12, 8)
        guide_layout.setSpacing(10)

        lbl_guide_text = QLabel("🎁 <b>Google AI Studio:</b> Cấp miễn phí 15 lượt gọi/phút (~1.500 lượt/ngày).")
        lbl_guide_text.setStyleSheet("font-size: 11px; color: #e0f2fe;")
        guide_layout.addWidget(lbl_guide_text, stretch=1)

        self.btn_open_portal = QPushButton("🌐 Nhận Key (Google AI Studio)")
        self.btn_open_portal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_portal.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; font-weight: 700; "
            "font-size: 11px; padding: 5px 12px; border-radius: 5px; border: none;"
        )
        self.btn_open_portal.setToolTip("Mở trình duyệt web đến: https://aistudio.google.com/app/apikey")
        self.btn_open_portal.clicked.connect(self.open_google_ai_studio)
        guide_layout.addWidget(self.btn_open_portal)

        layout.addWidget(guide_box)

        # 2. Ô nhập Gemini API Key
        lbl_key = QLabel("🔑 Dán Gemini API Key vào đây:")
        lbl_key.setStyleSheet("font-size: 12px; font-weight: 600; color: #f1f5f9;")
        layout.addWidget(lbl_key)

        key_input_row = QHBoxLayout()
        key_input_row.setSpacing(6)

        current_key = getattr(config, "GEMINI_API_KEY", "")
        self.edit_key = QLineEdit(current_key)
        self.edit_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key.setPlaceholderText("Dán API Key (bắt đầu bằng AIzaSy...)...")
        self.edit_key.setStyleSheet(
            "background-color: #11151d; border: 1px solid #334155; border-radius: 6px; "
            "padding: 7px 10px; color: #f8fafc; font-size: 12px;"
        )
        self.edit_key.textChanged.connect(self._on_key_text_changed)
        key_input_row.addWidget(self.edit_key, stretch=1)

        # Nút ẩn/hiện mật khẩu
        self._eye_icon = QIcon(str(ICONS_DIR / "eye.svg"))
        self._eye_off_icon = QIcon(str(ICONS_DIR / "eye-off.svg"))
        self.btn_toggle_key = QPushButton()
        self.btn_toggle_key.setFixedSize(36, 36)
        self.btn_toggle_key.setIcon(self._eye_icon)
        self.btn_toggle_key.setIconSize(QSize(18, 18))
        self.btn_toggle_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_key.setToolTip("Hiện / Ẩn Key")
        self.btn_toggle_key.setStyleSheet(
            "background-color: #1e293b; border: 1px solid #334155; border-radius: 6px;"
        )
        self.btn_toggle_key.clicked.connect(self._toggle_key_visibility)
        key_input_row.addWidget(self.btn_toggle_key)

        layout.addLayout(key_input_row)

        # Hàng Kiểm Tra Kết Nối & Trạng Thái
        status_row = QHBoxLayout()
        status_row.setSpacing(10)

        self.btn_test_conn = QPushButton("🔌 Kiểm Tra Kết Nối")
        self.btn_test_conn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_conn.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; border: 1px solid #0284c7; "
            "padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 11px;"
        )
        self.btn_test_conn.clicked.connect(lambda: self.test_connection(quiet=False))
        status_row.addWidget(self.btn_test_conn)

        initial_connected = bool(current_key.strip()) and bool(getattr(config, "GEMINI_CONNECTED", False))
        self.is_connected = initial_connected
        self.lbl_status = QLabel("🟢 Đã kết nối" if initial_connected else "🔴 Chưa kết nối")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 700;" if initial_connected else "font-size: 11px; color: #f87171; font-weight: 600;")
        status_row.addWidget(self.lbl_status, stretch=1)

        layout.addLayout(status_row)

        # 3. Box Chọn Model AI (Chỉ kích hoạt / mở khóa khi đã kết nối thành công)
        self.model_card = QFrame()
        self.model_card.setObjectName("gemini_model_card")
        card_layout = QVBoxLayout(self.model_card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        # Tiêu đề box model + Nút quét lại
        model_title_row = QHBoxLayout()
        lbl_model_title = QLabel("🎯 Lựa Chọn Mô Hình AI (Model):")
        lbl_model_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #f1f5f9;")
        model_title_row.addWidget(lbl_model_title, stretch=1)

        self.btn_refresh_models = QPushButton("🔄 Quét Models Mới")
        self.btn_refresh_models.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_models.setToolTip("Quét danh sách các Model AI thực tế từ tài khoản Google Gemini")
        self.btn_refresh_models.setStyleSheet(
            "background-color: #1e293b; color: #a5b4fc; border: 1px solid #4338ca; "
            "padding: 4px 10px; border-radius: 5px; font-weight: 600; font-size: 11px;"
        )
        self.btn_refresh_models.clicked.connect(lambda: self.test_connection(quiet=False))
        model_title_row.addWidget(self.btn_refresh_models)
        card_layout.addLayout(model_title_row)

        # Nhãn hướng dẫn / trạng thái của Box Model
        self.lbl_model_hint = QLabel()
        card_layout.addWidget(self.lbl_model_hint)

        # Hàng nút chọn nhanh (Quick Preset Pills)
        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        lbl_quick = QLabel("Chọn nhanh:")
        lbl_quick.setStyleSheet("font-size: 11px; color: #94a3b8;")
        quick_row.addWidget(lbl_quick)

        self.btn_pill_flash2 = QPushButton("⚡ 2.0 Flash")
        self.btn_pill_flash2.setToolTip("Model thế hệ 2.0, phản hồi siêu tốc")
        self.btn_pill_flash2.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pill_flash2.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; border: 1px solid #0284c7; "
            "padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: 600;"
        )
        self.btn_pill_flash2.clicked.connect(lambda: self._select_model_id("gemini-2.0-flash"))
        quick_row.addWidget(self.btn_pill_flash2)

        self.btn_pill_flash15 = QPushButton("⚡ 1.5 Flash")
        self.btn_pill_flash15.setToolTip("Model mặc định ổn định")
        self.btn_pill_flash15.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pill_flash15.setStyleSheet(
            "background-color: #1e293b; color: #34d399; border: 1px solid #059669; "
            "padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: 600;"
        )
        self.btn_pill_flash15.clicked.connect(lambda: self._select_model_id("gemini-1.5-flash"))
        quick_row.addWidget(self.btn_pill_flash15)

        self.btn_pill_pro = QPushButton("🧠 1.5 Pro")
        self.btn_pill_pro.setToolTip("Khả năng suy luận chi tiết, sáng tạo nội dung sâu")
        self.btn_pill_pro.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pill_pro.setStyleSheet(
            "background-color: #1e293b; color: #c084fc; border: 1px solid #7e22ce; "
            "padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: 600;"
        )
        self.btn_pill_pro.clicked.connect(lambda: self._select_model_id("gemini-1.5-pro"))
        quick_row.addWidget(self.btn_pill_pro)

        quick_row.addStretch()
        card_layout.addLayout(quick_row)

        # Thanh tìm kiếm nhanh trong danh sách model
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        lbl_search = QLabel("🔍 Lọc:")
        lbl_search.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        lbl_search.setFixedWidth(45)
        search_row.addWidget(lbl_search)

        self.edit_search_model = QLineEdit()
        self.edit_search_model.setPlaceholderText("Gõ để lọc model (vd: 2.0, flash, pro, exp...)...")
        self.edit_search_model.setStyleSheet(
            "background-color: #0b0f19; border: 1px solid #1e293b; border-radius: 5px; "
            "padding: 5px 8px; color: #cbd5e1; font-size: 11px;"
        )
        self.edit_search_model.textChanged.connect(self._filter_models)
        search_row.addWidget(self.edit_search_model, stretch=1)
        card_layout.addLayout(search_row)

        # Dropdown ComboBox chọn chi tiết (Thiết kế thanh lịch, mũi tên chevron SVG, max 7 dòng)
        model_dropdown_row = QHBoxLayout()
        model_dropdown_row.setSpacing(8)
        self.lbl_combo_title = QLabel("Model:")
        self.lbl_combo_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.lbl_combo_title.setFixedWidth(45)
        model_dropdown_row.addWidget(self.lbl_combo_title)

        chevron_down_path = str(ICONS_DIR / "chevron-down.svg").replace("\\", "/")
        chevron_hover_path = str(ICONS_DIR / "chevron-down-hover.svg").replace("\\", "/")

        self.combo_model = QComboBox()
        self.combo_model.setObjectName("combo_gemini_models")
        self.combo_model.setEditable(True)  # Cho phép người dùng tự gõ model tùy ý
        self.combo_model.setMaxVisibleItems(7)  # Giới hạn 7 dòng giúp dropdown luôn xổ xuống mượt mà, không che dialog
        self.combo_model.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_model.setStyleSheet(f"""
            QComboBox#combo_gemini_models {{
                background-color: #0b0f19;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 30px 6px 10px;
                color: #f8fafc;
                font-size: 12px;
                font-weight: 500;
                min-height: 28px;
            }}
            QComboBox#combo_gemini_models:hover {{
                border-color: #38bdf8;
                background-color: #111827;
            }}
            QComboBox#combo_gemini_models:focus {{
                border-color: #0284c7;
            }}
            QComboBox#combo_gemini_models::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border: none;
                background-color: transparent;
            }}
            QComboBox#combo_gemini_models::down-arrow {{
                image: url("{chevron_down_path}");
                width: 14px;
                height: 14px;
            }}
            QComboBox#combo_gemini_models:hover::down-arrow {{
                image: url("{chevron_hover_path}");
            }}
            QComboBox#combo_gemini_models QAbstractItemView {{
                background-color: #0f172a;
                border: 1px solid #0284c7;
                border-radius: 6px;
                selection-background-color: #1d4ed8;
                selection-color: #ffffff;
                padding: 4px;
                outline: none;
            }}
            QComboBox#combo_gemini_models QAbstractItemView::item {{
                min-height: 28px;
                padding: 4px 8px;
                color: #e2e8f0;
                border-radius: 4px;
            }}
            QComboBox#combo_gemini_models QAbstractItemView::item:hover {{
                background-color: #1e293b;
                color: #38bdf8;
            }}
            QComboBox#combo_gemini_models QAbstractItemView::item:selected {{
                background-color: #1d4ed8;
                color: #ffffff;
                font-weight: 600;
            }}
        """)

        # Click vào bất kỳ đâu trên ô text của ComboBox cũng mở dropdown popup ngay lập tức
        if self.combo_model.lineEdit():
            orig_mouse_press = self.combo_model.lineEdit().mousePressEvent
            def _on_line_edit_press(event):
                orig_mouse_press(event)
                self.combo_model.showPopup()
            self.combo_model.lineEdit().mousePressEvent = _on_line_edit_press
            self.combo_model.lineEdit().setPlaceholderText("Click để mở danh sách hoặc gõ model...")

        self._all_models_cache: List[Union[tuple, Dict[str, Any]]] = list(GEMINI_MODELS)
        self._populate_models(GEMINI_MODELS)

        current_model = getattr(config, "GEMINI_MODEL", "gemini-3.5-flash")
        idx = self.combo_model.findData(current_model)
        if idx != -1:
            self.combo_model.setCurrentIndex(idx)
        elif current_model:
            self.combo_model.addItem(current_model, current_model)
            self.combo_model.setCurrentIndex(self.combo_model.count() - 1)

        model_dropdown_row.addWidget(self.combo_model, stretch=1)
        card_layout.addLayout(model_dropdown_row)

        layout.addWidget(self.model_card)

        # Cài đặt trạng thái hiển thị của model_card
        self._update_model_card_state(initial_connected)

        # 4. Buttons Footer
        layout.addSpacing(6)
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Đóng")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(
            "background-color: #1e293b; color: #cbd5e1; border: 1px solid #334155; "
            "padding: 8px 16px; border-radius: 6px; font-weight: 600;"
        )
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("💾 Lưu Cấu Hình")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet(
            "background-color: #2563eb; color: #ffffff; border: none; "
            "padding: 8px 20px; border-radius: 6px; font-weight: 700; font-size: 13px;"
        )
        self.btn_save.clicked.connect(self.save_key)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

    def _on_key_text_changed(self, text: str):
        """Khi người dùng sửa key, reset trạng thái kết nối nếu key chưa được kiểm tra."""
        clean_key = text.strip()
        last_key = getattr(self, "_last_verified_key", "")
        if not clean_key or clean_key != last_key:
            self.is_connected = False
            self.lbl_status.setText("🔴 Chưa kiểm tra kết nối" if clean_key else "🔴 Chưa nhập Key")
            self.lbl_status.setStyleSheet("font-size: 11px; color: #f87171; font-weight: 600;")
            self._update_model_card_state(False)

    def _select_model_id(self, model_id: str):
        """Hỗ trợ chọn nhanh Model bằng các nút pill."""
        idx = self.combo_model.findData(model_id)
        if idx != -1:
            self.combo_model.setCurrentIndex(idx)
        else:
            self.combo_model.addItem(model_id, model_id)
            self.combo_model.setCurrentIndex(self.combo_model.count() - 1)

    def _update_model_card_state(self, connected: bool, message: str = "", model_count: int = 0):
        """Khóa hoặc mở khóa box lựa chọn Model tùy theo trạng thái kết nối."""
        self.is_connected = connected
        self.model_card.setEnabled(connected)
        if connected:
            self.model_card.setStyleSheet(
                "QFrame#gemini_model_card { background-color: #0b1e16; "
                "border: 1px solid #10b981; border-radius: 8px; }"
            )
            count_str = f"Đã nạp {model_count} models từ Google." if model_count > 0 else "Đã kết nối thành công."
            self.lbl_model_hint.setText(f"✅ {count_str} Bạn có thể chọn nhanh hoặc chọn trong danh sách bên dưới:")
            self.lbl_model_hint.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 600;")
        else:
            self.model_card.setStyleSheet(
                "QFrame#gemini_model_card { background-color: #0f131a; "
                "border: 1px solid #27303f; border-radius: 8px; }"
            )
            self.lbl_model_hint.setText("🔒 Vui lòng bấm 'Kiểm Tra Kết Nối' thành công để mở khóa danh sách Model.")
            self.lbl_model_hint.setStyleSheet("font-size: 11px; color: #94a3b8; font-style: italic;")

    def _filter_models(self, query: str):
        """Lọc danh sách models trong ComboBox theo từ khóa tìm kiếm."""
        q = (query or "").strip().lower()
        if not hasattr(self, "_all_models_cache") or not self._all_models_cache:
            return

        if not q:
            filtered = self._all_models_cache
        else:
            filtered = []
            for item in self._all_models_cache:
                if isinstance(item, tuple):
                    m_id, m_name = item
                    if q in m_id.lower() or q in m_name.lower():
                        filtered.append(item)
                elif isinstance(item, dict):
                    m_id = item.get("id", "").lower()
                    m_name = item.get("name", "").lower()
                    m_desc = item.get("description", "").lower()
                    if q in m_id or q in m_name or q in m_desc:
                        filtered.append(item)

        self._populate_models(filtered, is_filtering=True)
        if q and filtered:
            self.combo_model.showPopup()

    def _populate_models(self, models_data: Union[List[tuple], List[Dict[str, Any]]], is_filtering: bool = False):
        """Nạp danh sách models vào ComboBox."""
        if not is_filtering:
            self._all_models_cache = list(models_data)

        current_selection = self.combo_model.currentData() or self.combo_model.currentText()
        self.combo_model.clear()

        count = len(models_data)
        if hasattr(self, "lbl_combo_title"):
            total_count = len(getattr(self, "_all_models_cache", models_data))
            if is_filtering and count != total_count:
                self.lbl_combo_title.setText(f"Lọc ({count}):")
            else:
                self.lbl_combo_title.setText(f"Model ({count}):")

        for item in models_data:
            if isinstance(item, tuple):
                m_id, m_name = item
                self.combo_model.addItem(m_name, m_id)
            elif isinstance(item, dict):
                m_id = item.get("id", "")
                m_name = item.get("name", m_id)
                display_label = f"{m_name} ({m_id})" if (m_name and m_name != m_id) else m_id
                self.combo_model.addItem(display_label, m_id)

        # Khôi phục lựa chọn
        idx = self.combo_model.findData(current_selection)
        if idx != -1:
            self.combo_model.setCurrentIndex(idx)
        elif current_selection:
            self.combo_model.setEditText(str(current_selection))

    def test_connection(self, quiet: bool = False):
        """Thực hiện gọi API kiểm tra tính hợp lệ của API Key và quét danh sách model."""
        key = self.edit_key.text().strip()
        if not key:
            if not quiet:
                QMessageBox.warning(self, "Chưa nhập Key", "Vui lòng nhập Google Gemini API Key để kiểm tra!")
            self.lbl_status.setText("🔴 Chưa nhập Key")
            self.lbl_status.setStyleSheet("font-size: 11px; color: #f87171;")
            self._update_model_card_state(False)
            return

        if self.worker and self.worker.isRunning():
            return

        self.btn_test_conn.setEnabled(False)
        self.btn_test_conn.setText("⏳ Đang test...")
        self.lbl_status.setText("⏳ Đang kết nối tới Google Gemini API...")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #38bdf8;")

        self.worker = GeminiVerifyWorker(key, parent=self)
        self.worker.finished.connect(lambda ok, msg, models: self._on_verify_finished(ok, msg, models, quiet))
        self.worker.start()

    def _on_verify_finished(self, success: bool, message: str, models: list, quiet: bool):
        self.btn_test_conn.setEnabled(True)
        self.btn_test_conn.setText("🔌 Kiểm Tra Kết Nối")

        if success:
            clean_key = self.edit_key.text().strip()
            self._last_verified_key = clean_key
            self.is_connected = True
            model_count = len(models) if models else 0
            self.lbl_status.setText(f"🟢 Kết nối thành công! ({model_count} models)")
            self.lbl_status.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 700;")
            self.lbl_status.setToolTip(message)
            if models:
                self._populate_models(models)
            self._update_model_card_state(True, message=message, model_count=model_count)
            # Tự động lưu cấu hình key và trạng thái kết nối ngay lập tức để không bao giờ bị mất
            config.save_setting("GEMINI_API_KEY", clean_key)
            config.save_setting("GEMINI_CONNECTED", "true")
            config.GEMINI_API_KEY = clean_key
            config.GEMINI_CONNECTED = True
            config.settings.GEMINI_API_KEY = clean_key
            config.settings.GEMINI_CONNECTED = True

            curr_model = self.combo_model.currentData() or self.combo_model.currentText()
            if curr_model:
                curr_model_str = str(curr_model)
                if " (" in curr_model_str:
                    curr_model_str = curr_model_str.split(" (")[-1].replace(")", "").strip()
                config.save_setting("GEMINI_MODEL", curr_model_str)
                config.GEMINI_MODEL = curr_model_str
                config.settings.GEMINI_MODEL = curr_model_str

            if not quiet:
                QMessageBox.information(
                    self,
                    "Kết Nối Thành Công",
                    f"Google Gemini API Key hoàn toàn hợp lệ và đã được tự động lưu!\n{message}\n\nDanh sách Model AI đã được mở khóa để bạn lựa chọn.",
                )
        else:
            self.is_connected = False
            self.lbl_status.setText(f"🔴 {message[:55]}...")
            self.lbl_status.setStyleSheet("font-size: 11px; color: #f87171; font-weight: 600;")
            self.lbl_status.setToolTip(message)
            self._update_model_card_state(False)
            config.save_setting("GEMINI_CONNECTED", "false")
            config.GEMINI_CONNECTED = False
            config.settings.GEMINI_CONNECTED = False
            if not quiet:
                QMessageBox.critical(
                    self,
                    "Lỗi Kết Nối",
                    f"Không thể kết nối đến Google Gemini API:\n\n{message}\n\nVui lòng kiểm tra lại API Key hoặc mạng internet.",
                )

    def open_google_ai_studio(self):
        """Mở trình duyệt mặc định đến trang quản lý API Key của Google AI Studio."""
        url = QUrl("https://aistudio.google.com/app/apikey")
        QDesktopServices.openUrl(url)

    def _toggle_key_visibility(self):
        if self.edit_key.echoMode() == QLineEdit.EchoMode.Password:
            self.edit_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_key.setIcon(self._eye_off_icon)
        else:
            self.edit_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_key.setIcon(self._eye_icon)

    def save_key(self):
        """Lưu API Key và Model đã chọn vào cấu hình ứng dụng."""
        key = self.edit_key.text().strip()

        current_text = self.combo_model.currentText().strip()
        model_id = None
        for i in range(self.combo_model.count()):
            if self.combo_model.itemText(i) == current_text or self.combo_model.itemData(i) == current_text:
                model_id = self.combo_model.itemData(i)
                break

        if not model_id:
            curr_idx = self.combo_model.currentIndex()
            if curr_idx != -1 and self.combo_model.itemText(curr_idx) == current_text:
                model_id = self.combo_model.currentData() or current_text
            else:
                model_id = current_text or "gemini-1.5-flash"

        # Bỏ prefix nếu có
        if " (" in model_id:
            model_id = model_id.split(" (")[-1].replace(")", "").strip()

        config.save_setting("GEMINI_API_KEY", key)
        config.save_setting("GEMINI_MODEL", model_id)
        config.GEMINI_API_KEY = key
        config.GEMINI_MODEL = model_id
        config.settings.GEMINI_API_KEY = key
        config.settings.GEMINI_MODEL = model_id

        is_conn = bool(key) and bool(getattr(self, "is_connected", False))
        if is_conn:
            config.save_setting("GEMINI_CONNECTED", "true")
            config.GEMINI_CONNECTED = True
            config.settings.GEMINI_CONNECTED = True
            self.lbl_status.setText("🟢 Đã kết nối")
            self.lbl_status.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 700;")
        else:
            config.save_setting("GEMINI_CONNECTED", "false")
            config.GEMINI_CONNECTED = False
            config.settings.GEMINI_CONNECTED = False
            self.is_connected = False
            self._update_model_card_state(False)
            self.lbl_status.setText("🔴 Chưa kết nối" if not key else "🔴 Chưa kiểm tra kết nối")
            self.lbl_status.setStyleSheet("font-size: 11px; color: #f87171; font-weight: 600;")

        self.key_saved.emit(key, model_id)

        if is_conn:
            QMessageBox.information(
                self,
                "Đã lưu",
                f"Đã lưu Google Gemini API Key thành công!\nModel đang chọn: {model_id}\n"
                "Từ bây giờ Storyboard Studio sẽ sử dụng trí tuệ nhân tạo Gemini để sinh kịch bản."
            )
        elif key:
            QMessageBox.information(
                self,
                "Đã lưu Key",
                f"Đã lưu API Key! Lưu ý: Trạng thái đang là Chưa kết nối.\n"
                "Vui lòng bấm 'Kiểm Tra Kết Nối' để kích hoạt AI."
            )
        else:
            QMessageBox.information(
                self,
                "Đã xóa Key",
                "Đã xóa API Key. Ứng dụng sẽ sử dụng bộ Mẫu Storytelling Offline."
            )
        self._stop_worker()
        self.accept()

    def _stop_worker(self):
        if getattr(self, "worker", None) and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(500)

    def closeEvent(self, event):
        self._stop_worker()
        super().closeEvent(event)

    def reject(self):
        self._stop_worker()
        super().reject()


