from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QFileDialog, QComboBox
)

from app import config
from app.core.vibi_client import VibiClient
from app.core.platform_utils import open_path

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


class AccountCheckThread(QThread):
    """Worker kiểm tra số dư và thông tin tài khoản Vibi."""
    result_ready = pyqtSignal(str, bool, dict, str)

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key

    def run(self):
        client = VibiClient(api_key=self.api_key)
        if not client.is_configured():
            self.result_ready.emit(
                self.api_key or "",
                False,
                {},
                "Vui lòng nhập Voice API Key trước khi kiểm tra!",
            )
            return

        try:
            info = client.get_account_info()
            self.result_ready.emit(self.api_key or "", True, info, "")
        except Exception as e:
            self.result_ready.emit(self.api_key or "", False, {}, str(e))


class SettingsTab(QWidget):
    """Tab quản lý API Key, kiểm tra số dư Credits và cấu hình hệ thống - Thiết kế gọn gàng, chuẩn form UX."""
    api_key_saved = pyqtSignal(str)
    gemini_key_saved = pyqtSignal(str)
    account_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_tab")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.worker: Optional[AccountCheckThread] = None
        self._pending_api_key: Optional[str] = None
        self._active_check_key: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        page_title = QLabel("Cài đặt")
        page_title.setObjectName("page_heading")
        page_subtitle = QLabel(
            "Quản lý tài khoản Voice API và thư mục lưu dự án."
        )
        page_subtitle.setObjectName("page_subtitle")
        layout.addWidget(page_title)
        layout.addWidget(page_subtitle)

        # 1. Panel Tài khoản & Vibi API Key
        acc_panel = QFrame()
        acc_panel.setProperty("class", "panel")
        acc_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        ap_layout = QVBoxLayout(acc_panel)
        ap_layout.setContentsMargins(14, 12, 14, 12)
        ap_layout.setSpacing(10)

        lbl_acc_header = QLabel("Tài Khoản Voice API")
        lbl_acc_header.setProperty("class", "panel_title")
        ap_layout.addWidget(lbl_acc_header)

        # Hàng nhập API Key
        key_row = QHBoxLayout()
        key_row.setSpacing(8)

        lbl_k = QLabel("Voice API Key:")
        lbl_k.setProperty("class", "section_label")
        lbl_k.setFixedWidth(90)

        self.edit_key = QLineEdit(config.VIBI_API_KEY)
        self.edit_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key.setPlaceholderText("Nhập Voice API Key...")

        self._eye_icon = QIcon(str(ICONS_DIR / "eye.svg"))
        self._eye_off_icon = QIcon(str(ICONS_DIR / "eye-off.svg"))
        self.btn_toggle_key = QPushButton()
        self.btn_toggle_key.setFixedSize(34, 34)
        self.btn_toggle_key.setIcon(self._eye_icon)
        self.btn_toggle_key.setIconSize(QSize(18, 18))
        self.btn_toggle_key.setToolTip("Hiện API Key")
        self.btn_toggle_key.setAccessibleName("Hiện API Key")
        self.btn_toggle_key.setObjectName("btn_subtle")
        self.btn_toggle_key.clicked.connect(self.toggle_key_visibility)

        self.btn_save_key = QPushButton("Lưu")
        self.btn_save_key.setObjectName("btn_primary")
        self.btn_save_key.clicked.connect(self.save_api_key)

        key_row.addWidget(lbl_k)
        key_row.addWidget(self.edit_key, stretch=2)
        key_row.addWidget(self.btn_toggle_key)
        key_row.addWidget(self.btn_save_key)
        ap_layout.addLayout(key_row)

        # Thông tin tài khoản (Dòng thẻ thông tin gọn gàng)
        self.info_box = QFrame()
        self.info_box.setStyleSheet("background-color: #14151b; border: 1px solid #23252d; border-radius: 6px; padding: 8px;")
        ib_layout = QHBoxLayout(self.info_box)

        self.lbl_credits = QLabel("Số dư: -- credits")
        self.lbl_credits.setStyleSheet("font-size: 14px; font-weight: 700; color: #10b981;")

        self.lbl_user = QLabel("Người dùng: --")
        self.lbl_user.setStyleSheet("color: #9ca3af; font-size: 12px;")

        self.lbl_email = QLabel("Email: --")
        self.lbl_email.setStyleSheet("color: #9ca3af; font-size: 12px;")

        ib_layout.addWidget(self.lbl_credits)
        ib_layout.addStretch()
        ib_layout.addWidget(self.lbl_user)
        ib_layout.addSpacing(15)
        ib_layout.addWidget(self.lbl_email)

        ap_layout.addWidget(self.info_box)

        self.lbl_vibi_test_key = QLabel(
            'Lấy API Key test tại đây: '
            '<a href="https://vibi.pro" '
            'style="color: #60a5fa; text-decoration: underline;">Vibi.pro</a>'
        )
        self.lbl_vibi_test_key.setOpenExternalLinks(True)
        self.lbl_vibi_test_key.setStyleSheet(
            "color: #dbeafe; background-color: #182235; "
            "border: 1px solid #2d5d94; border-radius: 6px; "
            "padding: 6px 9px; font-size: 12px; font-weight: 600;"
        )
        key_help_row = QHBoxLayout()
        key_help_row.setContentsMargins(0, 0, 0, 0)
        key_help_row.setSpacing(8)
        key_help_row.addWidget(self.lbl_vibi_test_key)
        key_help_row.addStretch()
        ap_layout.addLayout(key_help_row)

        layout.addWidget(acc_panel)

        # 2. Panel Google Gemini AI (Viết Kịch Bản & Phân Cảnh AI Thực Thụ)
        gemini_panel = QFrame()
        gemini_panel.setProperty("class", "panel")
        gemini_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        gp_layout = QVBoxLayout(gemini_panel)
        gp_layout.setContentsMargins(14, 12, 14, 12)
        gp_layout.setSpacing(10)

        lbl_gemini_header = QLabel("Google Gemini AI (Sinh Kịch Bản & Phân Cảnh Thực Thụ)")
        lbl_gemini_header.setProperty("class", "panel_title")
        gp_layout.addWidget(lbl_gemini_header)

        # Hàng nhập Gemini API Key
        gemini_key_row = QHBoxLayout()
        gemini_key_row.setSpacing(8)

        lbl_gk = QLabel("Gemini Key:")
        lbl_gk.setProperty("class", "section_label")
        lbl_gk.setFixedWidth(90)

        self.edit_gemini_key = QLineEdit(getattr(config, "GEMINI_API_KEY", ""))
        self.edit_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_gemini_key.setPlaceholderText("Nhập Google Gemini API Key (AI Studio)...")

        self.edit_gemini_key.textChanged.connect(self._on_gemini_key_text_changed)

        self.btn_toggle_gemini_key = QPushButton()
        self.btn_toggle_gemini_key.setFixedSize(34, 34)
        self.btn_toggle_gemini_key.setIcon(self._eye_icon)
        self.btn_toggle_gemini_key.setIconSize(QSize(18, 18))
        self.btn_toggle_gemini_key.setToolTip("Hiện Gemini Key")
        self.btn_toggle_gemini_key.setAccessibleName("Hiện Gemini Key")
        self.btn_toggle_gemini_key.setObjectName("btn_subtle")
        self.btn_toggle_gemini_key.clicked.connect(self.toggle_gemini_key_visibility)

        self.btn_save_gemini_key = QPushButton("Lưu")
        self.btn_save_gemini_key.setObjectName("btn_primary")
        self.btn_save_gemini_key.clicked.connect(self.save_gemini_key)

        gemini_key_row.addWidget(lbl_gk)
        gemini_key_row.addWidget(self.edit_gemini_key, stretch=2)
        gemini_key_row.addWidget(self.btn_toggle_gemini_key)
        gemini_key_row.addWidget(self.btn_save_gemini_key)
        gp_layout.addLayout(gemini_key_row)

        # Hàng Kiểm Tra Kết Nối & Trạng Thái
        gemini_status_row = QHBoxLayout()
        gemini_status_row.setSpacing(10)
        self.btn_test_gemini = QPushButton("🔌 Kiểm Tra Kết Nối")
        self.btn_test_gemini.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_gemini.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; border: 1px solid #0284c7; "
            "padding: 5px 12px; border-radius: 5px; font-weight: 600; font-size: 11px;"
        )
        self.btn_test_gemini.clicked.connect(self.test_gemini_connection)
        gemini_status_row.addWidget(self.btn_test_gemini)

        initial_connected = bool(getattr(config, "GEMINI_API_KEY", "").strip()) and bool(getattr(config, "GEMINI_CONNECTED", False))
        self.is_gemini_connected = initial_connected
        self._last_verified_gemini_key = getattr(config, "GEMINI_API_KEY", "") if initial_connected else ""
        self.lbl_gemini_status = QLabel("🟢 Đã kết nối" if initial_connected else "🔴 Chưa kết nối")
        self.lbl_gemini_status.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 700;" if initial_connected else "font-size: 11px; color: #f87171; font-weight: 600;")
        gemini_status_row.addWidget(self.lbl_gemini_status, stretch=1)
        gp_layout.addLayout(gemini_status_row)

        # Khung chọn Model (Khóa/mở khóa tùy theo kết nối)
        self.gemini_model_card = QFrame()
        self.gemini_model_card.setObjectName("gemini_model_card")
        card_layout = QVBoxLayout(self.gemini_model_card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(6)

        self.lbl_gemini_model_hint = QLabel(
            "✅ Đã kết nối thành công! Bạn có thể chọn Model bên dưới:" if initial_connected
            else "🔒 Vui lòng kiểm tra kết nối thành công để mở khóa danh sách Model."
        )
        self.lbl_gemini_model_hint.setStyleSheet(
            "font-size: 11px; color: #34d399; font-weight: 600;" if initial_connected
            else "font-size: 11px; color: #94a3b8; font-style: italic;"
        )
        card_layout.addWidget(self.lbl_gemini_model_hint)

        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        lbl_gm = QLabel("Model AI:")
        lbl_gm.setProperty("class", "section_label")
        lbl_gm.setFixedWidth(75)

        self.combo_gemini_model = QComboBox()
        self.combo_gemini_model.setObjectName("combo_gemini_model_settings")
        self.combo_gemini_model.setEditable(True)  # Cho phép tự nhập model tùy ý
        self.combo_gemini_model.setMaxVisibleItems(15)
        self.combo_gemini_model.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_gemini_model.addItem("⚡ Gemini 1.5 Flash (Nhanh & Ổn định - Miễn phí)", "gemini-1.5-flash")
        self.combo_gemini_model.addItem("🚀 Gemini 2.0 Flash (Thế hệ mới - Siêu tốc)", "gemini-2.0-flash")
        self.combo_gemini_model.addItem("🧠 Gemini 1.5 Pro (Suy luận sâu & Chi tiết)", "gemini-1.5-pro")

        if self.combo_gemini_model.lineEdit():
            orig_le_press = self.combo_gemini_model.lineEdit().mousePressEvent
            def _on_settings_le_press(event):
                orig_le_press(event)
                self.combo_gemini_model.showPopup()
            self.combo_gemini_model.lineEdit().mousePressEvent = _on_settings_le_press
            self.combo_gemini_model.lineEdit().setPlaceholderText("Click để mở danh sách hoặc gõ model...")

        current_model = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
        model_idx = self.combo_gemini_model.findData(current_model)
        if model_idx != -1:
            self.combo_gemini_model.setCurrentIndex(model_idx)
        elif current_model:
            self.combo_gemini_model.setEditText(current_model)
        self.combo_gemini_model.currentIndexChanged.connect(self._on_gemini_model_changed)

        model_row.addWidget(lbl_gm)
        model_row.addWidget(self.combo_gemini_model, stretch=1)

        self.btn_scan_gemini_models = QPushButton("🔄 Quét Models")
        self.btn_scan_gemini_models.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan_gemini_models.setToolTip("Quét danh sách các Model AI thực tế từ Google")
        self.btn_scan_gemini_models.setStyleSheet(
            "background-color: #1e293b; color: #a5b4fc; border: 1px solid #4338ca; "
            "padding: 5px 10px; border-radius: 5px; font-weight: 600; font-size: 11px;"
        )
        self.btn_scan_gemini_models.clicked.connect(self.test_gemini_connection)
        model_row.addWidget(self.btn_scan_gemini_models)

        card_layout.addLayout(model_row)
        self.gemini_model_card.setEnabled(initial_connected)
        gp_layout.addWidget(self.gemini_model_card)

        # Link hướng dẫn lấy Key miễn phí
        self.lbl_gemini_help = QLabel(
            'Lấy Google Gemini API Key MIỄN PHÍ tại: '
            '<a href="https://aistudio.google.com/app/apikey" '
            'style="color: #38bdf8; text-decoration: underline; font-weight: 700;">Google AI Studio</a> '
            '(15 requests/phút miễn phí vĩnh viễn).'
        )
        self.lbl_gemini_help.setOpenExternalLinks(True)
        self.lbl_gemini_help.setStyleSheet(
            "color: #e0f2fe; background-color: #0c4a6e; "
            "border: 1px solid #0284c7; border-radius: 6px; "
            "padding: 6px 10px; font-size: 12px; font-weight: 500;"
        )
        gp_layout.addWidget(self.lbl_gemini_help)

        layout.addWidget(gemini_panel)

        # 3. Panel thư mục dự án
        pref_panel = QFrame()
        pref_panel.setProperty("class", "panel")
        pref_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pp_layout = QVBoxLayout(pref_panel)
        pp_layout.setContentsMargins(14, 12, 14, 12)
        pp_layout.setSpacing(10)

        lbl_pref_header = QLabel("Thư Mục Dự Án")
        lbl_pref_header.setProperty("class", "panel_title")
        pp_layout.addWidget(lbl_pref_header)

        # Đường dẫn lưu Projects
        project_dir_row = QHBoxLayout()
        lbl_dir = QLabel("Đường dẫn lưu Projects:")
        lbl_dir.setProperty("class", "section_label")
        lbl_dir.setFixedWidth(160)

        self.lbl_dir_path = QLabel(str(config.PROJECTS_DIR))
        self.lbl_dir_path.setStyleSheet("color: #60a5fa; font-size: 12px;")

        self.btn_change_dir = QPushButton("Thay đổi...")
        self.btn_change_dir.clicked.connect(self.change_projects_dir)

        self.btn_open_dir = QPushButton("Mở")
        self.btn_open_dir.clicked.connect(self.open_projects_dir)

        project_dir_row.addWidget(lbl_dir)
        project_dir_row.addWidget(self.lbl_dir_path, stretch=1)
        project_dir_row.addWidget(self.btn_change_dir)
        project_dir_row.addWidget(self.btn_open_dir)
        pp_layout.addLayout(project_dir_row)

        layout.addWidget(pref_panel)
        layout.addStretch()

        if config.VIBI_API_KEY:
            self.check_account()

    def toggle_key_visibility(self):
        if self.edit_key.echoMode() == QLineEdit.EchoMode.Password:
            self.edit_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_key.setIcon(self._eye_off_icon)
            self.btn_toggle_key.setToolTip("Ẩn API Key")
            self.btn_toggle_key.setAccessibleName("Ẩn API Key")
        else:
            self.edit_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_key.setIcon(self._eye_icon)
            self.btn_toggle_key.setToolTip("Hiện API Key")
            self.btn_toggle_key.setAccessibleName("Hiện API Key")

    def save_api_key(self):
        key = self.edit_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Chưa có Key", "Vui lòng nhập Voice API Key!")
            return

        self._pending_api_key = key
        self._start_account_check(key)

    def check_account(self):
        key = self.edit_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Chưa có Key", "Vui lòng nhập Voice API Key!")
            return

        self._pending_api_key = None
        self._start_account_check(key)

    def _start_account_check(self, key: str):
        self._active_check_key = key
        self.btn_save_key.setEnabled(False)
        self.lbl_credits.setText("Đang kiểm tra...")

        self.worker = AccountCheckThread(api_key=key)
        self.worker.result_ready.connect(self.on_account_checked)
        self.worker.start()

    def on_account_checked(self, checked_key: str, success: bool, info: dict, error_msg: str):
        if checked_key != self._active_check_key:
            return

        self._active_check_key = None
        self.btn_save_key.setEnabled(True)
        pending_api_key = self._pending_api_key

        if success:
            if pending_api_key == checked_key:
                config.save_setting("VIBI_API_KEY", pending_api_key)
                config.VIBI_API_KEY = pending_api_key
                config.settings.VIBI_API_KEY = pending_api_key
                self.api_key_saved.emit(pending_api_key)
                QMessageBox.information(
                    self,
                    "Đã lưu",
                    "Đã kiểm tra và lưu Voice API Key thành công!",
                )
                self._pending_api_key = None

            self.update_account_info(info)
            self.account_updated.emit(info)
        else:
            if pending_api_key == checked_key:
                self._pending_api_key = None
            self.lbl_credits.setText("Không thể kết nối")
            self.lbl_credits.setStyleSheet("font-size: 13px; font-weight: 600; color: #f87171;")
            QMessageBox.critical(self, "Lỗi kiểm tra", error_msg)

    def update_account_info(self, info: dict):
        """Cập nhật hiển thị thông tin tài khoản và số dư credits trên giao diện Settings."""
        credits = info.get("credit_balance")
        if credits is None:
            credits = info.get("credits", 0)
        name = info.get("name") or "User"
        email = info.get("email") or "-"

        self.lbl_credits.setText(f"Số dư: {credits:,} credits")
        self.lbl_credits.setStyleSheet("font-size: 14px; font-weight: 700; color: #10b981;")
        self.lbl_user.setText(f"Người dùng: {name}")
        self.lbl_email.setText(f"Email: {email}")

    def change_projects_dir(self):
        """Cho phép user chọn thư mục lưu projects mới."""
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn đường dẫn lưu Projects", str(config.PROJECTS_DIR)
        )
        if folder:
            p = Path(folder)
            p.mkdir(parents=True, exist_ok=True)
            config.PROJECTS_DIR = p
            config.settings.PROJECTS_DIR = p
            config.save_setting("PROJECTS_DIR", str(p))
            self.lbl_dir_path.setText(str(p))

    def open_projects_dir(self):
        """Mở thư mục chứa projects trong File Explorer."""
        target = config.PROJECTS_DIR
        try:
            open_path(target)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể mở thư mục: {e}")

    def toggle_gemini_key_visibility(self):
        if self.edit_gemini_key.echoMode() == QLineEdit.EchoMode.Password:
            self.edit_gemini_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_gemini_key.setIcon(self._eye_off_icon)
            self.btn_toggle_gemini_key.setToolTip("Ẩn Gemini Key")
            self.btn_toggle_gemini_key.setAccessibleName("Ẩn Gemini Key")
        else:
            self.edit_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_gemini_key.setIcon(self._eye_icon)
            self.btn_toggle_gemini_key.setToolTip("Hiện Gemini Key")
            self.btn_toggle_gemini_key.setAccessibleName("Hiện Gemini Key")

    def _save_current_gemini_model(self):
        current_text = self.combo_gemini_model.currentText().strip()
        model_id = None
        for i in range(self.combo_gemini_model.count()):
            if self.combo_gemini_model.itemText(i) == current_text or self.combo_gemini_model.itemData(i) == current_text:
                model_id = self.combo_gemini_model.itemData(i)
                break

        if not model_id:
            curr_idx = self.combo_gemini_model.currentIndex()
            if curr_idx != -1 and self.combo_gemini_model.itemText(curr_idx) == current_text:
                model_id = self.combo_gemini_model.itemData(curr_idx) or current_text
            else:
                model_id = current_text or "gemini-1.5-flash"

        if " (" in model_id:
            model_id = model_id.split(" (")[-1].replace(")", "").strip()

        config.save_setting("GEMINI_MODEL", model_id)
        config.GEMINI_MODEL = model_id
        config.settings.GEMINI_MODEL = model_id
        return model_id

    def _on_gemini_key_text_changed(self, text: str):
        clean = text.strip()
        last = getattr(self, "_last_verified_gemini_key", "")
        if not clean or clean != last:
            self.is_gemini_connected = False
            self.lbl_gemini_status.setText("🔴 Chưa kiểm tra kết nối" if clean else "🔴 Chưa kết nối")
            self.lbl_gemini_status.setStyleSheet("font-size: 11px; color: #f87171; font-weight: 600;")
            self.gemini_model_card.setEnabled(False)

    def save_gemini_key(self):
        key = self.edit_gemini_key.text().strip()
        config.save_setting("GEMINI_API_KEY", key)
        config.GEMINI_API_KEY = key
        config.settings.GEMINI_API_KEY = key

        is_conn = bool(key) and bool(getattr(self, "is_gemini_connected", False))
        config.save_setting("GEMINI_CONNECTED", "true" if is_conn else "false")
        config.GEMINI_CONNECTED = is_conn
        config.settings.GEMINI_CONNECTED = is_conn
        self.gemini_model_card.setEnabled(is_conn)
        self.lbl_gemini_status.setText("🟢 Đã kết nối" if is_conn else ("🔴 Chưa kiểm tra kết nối" if key else "🔴 Chưa kết nối"))
        self.lbl_gemini_status.setStyleSheet(
            "font-size: 11px; color: #34d399; font-weight: 700;" if is_conn
            else "font-size: 11px; color: #f87171; font-weight: 600;"
        )
        self._save_current_gemini_model()
        self.gemini_key_saved.emit(key)
        if is_conn:
            QMessageBox.information(
                self,
                "Đã lưu",
                "Đã lưu Google Gemini API Key thành công!\nTừ bây giờ AI Storyboard Studio sẽ sử dụng Gemini AI thực thụ để sinh kịch bản."
            )
        elif key:
            QMessageBox.information(
                self,
                "Đã lưu Key",
                "Đã lưu API Key! Lưu ý: Trạng thái đang là Chưa kết nối.\nVui lòng bấm 'Kiểm Tra Kết Nối' để kích hoạt AI."
            )
        else:
            QMessageBox.information(
                self,
                "Đã xóa",
                "Đã xóa Google Gemini API Key. Hệ thống sẽ sử dụng bộ mẫu Storytelling Offline."
            )

    def _on_gemini_model_changed(self, index: int):
        self._save_current_gemini_model()

    def test_gemini_connection(self, quiet: bool = False):
        """Kiểm tra kết nối và cập nhật danh sách model từ Google trong SettingsTab."""
        key = self.edit_gemini_key.text().strip()
        if not key:
            if not quiet:
                QMessageBox.warning(self, "Chưa nhập Key", "Vui lòng nhập Google Gemini API Key để kiểm tra kết nối!")
            self.lbl_gemini_status.setText("🔴 Chưa nhập Key")
            self.lbl_gemini_status.setStyleSheet("font-size: 11px; color: #f87171;")
            self.gemini_model_card.setEnabled(False)
            return

        self.btn_test_gemini.setEnabled(False)
        self.btn_test_gemini.setText("⏳ Đang test...")
        self.lbl_gemini_status.setText("⏳ Đang kết nối tới Google Gemini API...")
        self.lbl_gemini_status.setStyleSheet("font-size: 11px; color: #38bdf8;")

        from app.ui.gemini_key_dialog import GeminiVerifyWorker
        self.gemini_worker = GeminiVerifyWorker(key, parent=self)
        self.gemini_worker.finished.connect(lambda ok, msg, models: self._on_gemini_verify_finished(ok, msg, models, quiet))
        self.gemini_worker.start()

    def _on_gemini_verify_finished(self, success: bool, message: str, models: list, quiet: bool = False):
        self.btn_test_gemini.setEnabled(True)
        self.btn_test_gemini.setText("🔌 Kiểm Tra Kết Nối")

        if success:
            self.is_gemini_connected = True
            clean_key = self.edit_gemini_key.text().strip()
            self._last_verified_gemini_key = clean_key
            model_count = len(models) if models else 0
            self.lbl_gemini_status.setText(f"🟢 Kết nối thành công! ({model_count} models)")
            self.lbl_gemini_status.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 700;")
            self.lbl_gemini_status.setToolTip(message)
            self.gemini_model_card.setEnabled(True)
            self.lbl_gemini_model_hint.setText(
                f"✅ Đã kết nối thành công! Đã nạp {model_count} models vào ComboBox từ Google:"
                if model_count > 0 else "✅ Đã kết nối thành công! Bạn có thể chọn Model bên dưới:"
            )
            self.lbl_gemini_model_hint.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 600;")
            config.save_setting("GEMINI_API_KEY", clean_key)
            config.save_setting("GEMINI_CONNECTED", "true")
            config.GEMINI_API_KEY = clean_key
            config.GEMINI_CONNECTED = True
            config.settings.GEMINI_API_KEY = clean_key
            config.settings.GEMINI_CONNECTED = True
            self.gemini_key_saved.emit(clean_key)

            if models:
                current_sel = self.combo_gemini_model.currentData() or self.combo_gemini_model.currentText()
                self.combo_gemini_model.clear()
                for item in models:
                    m_id = item.get("id", "")
                    m_name = item.get("name", m_id)
                    lbl = f"{m_name} ({m_id})" if (m_name and m_name != m_id) else m_id
                    self.combo_gemini_model.addItem(lbl, m_id)
                idx = self.combo_gemini_model.findData(current_sel)
                if idx != -1:
                    self.combo_gemini_model.setCurrentIndex(idx)
                elif current_sel:
                    self.combo_gemini_model.setEditText(str(current_sel))

            if not quiet:
                QMessageBox.information(
                    self, "Kết Nối Thành Công",
                    f"Google Gemini API Key hoàn toàn hợp lệ!\n{message}",
                )
        else:
            self.is_gemini_connected = False
            self.lbl_gemini_status.setText(f"🔴 {message[:55]}...")
            self.lbl_gemini_status.setStyleSheet("font-size: 11px; color: #f87171; font-weight: 600;")
            self.lbl_gemini_status.setToolTip(message)
            self.gemini_model_card.setEnabled(False)
            self.lbl_gemini_model_hint.setText("🔒 Vui lòng kiểm tra kết nối thành công để mở khóa danh sách Model.")
            self.lbl_gemini_model_hint.setStyleSheet("font-size: 11px; color: #94a3b8; font-style: italic;")
            config.save_setting("GEMINI_CONNECTED", "false")
            config.GEMINI_CONNECTED = False
            config.settings.GEMINI_CONNECTED = False
            if not quiet:
                QMessageBox.critical(
                    self, "Lỗi Kết Nối",
                    f"Không thể kết nối đến Google Gemini API:\n\n{message}",
                )
