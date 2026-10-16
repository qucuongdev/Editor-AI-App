from pathlib import Path
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.core.standalone_state import StandaloneStateStore
from app.update_check import UpdateCheckerThread, UpdateDownloadThread
from app.update_install import launch_update_helper, select_download_url

from app.ui.project_workspace import ProjectWorkspace
from app.ui.settings_tab import SettingsTab
from app.ui.tts_tab import TTSTab
from app.ui.trending_tab import TrendingTab
from app.ui.update_dialog import UpdateDialog
from app.ui.gemini_key_dialog import GeminiKeyDialog
from app.ui.watermark_tab import WatermarkTab
from app.ui.video_watermark_tab import VideoWatermarkTab
from app.version import APP_VERSION


ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


def split_icon_and_title(text: str) -> tuple[str, str]:
    """Tách biểu tượng icon và tiêu đề chữ từ nhãn nút navigation."""
    parts = text.strip().split(maxsplit=1)
    if len(parts) == 2 and len(parts[0]) <= 3:
        return parts[0], parts[1].strip()
    return "", text.strip()


class MainWindow(QMainWindow):
    """Cửa sổ chính của các công cụ và không gian dự án."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Editor Video AI v{APP_VERSION}")
        self.resize(1240, 820)
        self.setMinimumSize(900, 640)

        self.nav_buttons: list[QPushButton] = []
        self.is_sidebar_collapsed: bool = False
        self._full_api_text: str = ""
        self._staged_update: Path | None = None
        self._download_thread: UpdateDownloadThread | None = None
        self._update_dialog: UpdateDialog | None = None
        self._download_error: str | None = None
        self.standalone_state = StandaloneStateStore()
        self.init_ui()
        self.update_api_status_badge()
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._check_update_automatically)
        self._update_timer.start(1500)
        if getattr(sys, "frozen", False):
            QTimer.singleShot(0, self._show_update_error)

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        central_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_title_bar())
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        self.sidebar = self._build_sidebar()
        workspace_layout.addWidget(self.sidebar)

        self.watermark_pages = QTabWidget()
        self.watermark_pages.setObjectName("workspace_pages")
        self.watermark_tab = WatermarkTab()
        self.watermark_tab.configure_standalone(
            self.standalone_state, config.WATERMARK_DOWNLOADS_DIR
        )
        self.video_watermark_tab = VideoWatermarkTab()
        self.watermark_pages.addTab(self.watermark_tab, "Gỡ watermark Ảnh")
        self.watermark_pages.addTab(self.video_watermark_tab, "Gỡ watermark Video")
        self.watermark_pages.currentChanged.connect(self._on_watermark_tab_changed)
        self.project_workspace = ProjectWorkspace()
        self.tts_tab = TTSTab()
        self.tts_tab.configure_standalone(
            self.standalone_state, config.TTS_DOWNLOADS_DIR
        )
        self.settings_tab = SettingsTab()
        self.trending_tab = TrendingTab()
        self.trending_tab.request_open_tts.connect(self.open_tts_with_script)

        self.stack = QStackedWidget()
        self.stack.setObjectName("content_container")
        self.stack.addWidget(self.project_workspace)
        self.stack.addWidget(self.watermark_pages)
        self.stack.addWidget(self.tts_tab)
        self.stack.addWidget(self.trending_tab)
        self.stack.addWidget(self.settings_tab)

        self.settings_tab.api_key_saved.connect(self.update_api_status_badge)
        self.settings_tab.gemini_key_saved.connect(self._on_gemini_key_saved_from_settings)
        self.settings_tab.account_updated.connect(self.on_account_updated)
        self.tts_tab.account_updated.connect(self.on_account_updated)
        self.project_workspace.tts_tab.account_updated.connect(self.on_account_updated)
        workspace_layout.addWidget(self.stack, stretch=1)
        root_layout.addLayout(workspace_layout, stretch=1)
        root_layout.addWidget(self._build_footer())

        # Shortcut phím tắt Ctrl+B để ẩn/hiện hoặc thu gọn/mở rộng sidebar
        self.shortcut_toggle_sidebar = QShortcut(QKeySequence("Ctrl+B"), self)
        self.shortcut_toggle_sidebar.activated.connect(self.toggle_sidebar)

        # Khôi phục trạng thái thu gọn sidebar
        is_collapsed = self.standalone_state.load_sidebar_collapsed()
        self.set_sidebar_collapsed(is_collapsed)

        last_page = self.standalone_state.load_last_page()
        self.switch_page(last_page if last_page < self.stack.count() else 0)

    def _on_watermark_tab_changed(self, index: int) -> None:
        if self.watermark_pages.widget(index) is self.video_watermark_tab:
            self.video_watermark_tab.on_tab_activated()

    def _refresh_api_chip_display(self) -> None:
        if not hasattr(self, "api_chip"):
            return
        has_voice_key = bool(config.settings.VIBI_API_KEY.strip())
        has_gemini_key = bool(getattr(config, "GEMINI_API_KEY", "").strip())
        is_gemini_connected = has_gemini_key and bool(getattr(config, "GEMINI_CONNECTED", False))
        gemini_model = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")

        if self.is_sidebar_collapsed:
            self.api_chip.setText("🔑" if has_voice_key else "⚠️")
            self.api_chip.setToolTip(self._full_api_text or ("Voice API: Đã cấu hình" if has_voice_key else "Voice API: Chưa cấu hình"))
            if hasattr(self, "btn_gemini_chip"):
                self.btn_gemini_chip.setText("🟢" if is_gemini_connected else "🔴")
                self.btn_gemini_chip.setToolTip(
                    f"Google Gemini AI: 🟢 Đã kết nối (Model: {gemini_model}) - Click để sửa"
                    if is_gemini_connected
                    else (
                        "Google Gemini AI: 🔴 Chưa kết nối (Click để kiểm tra API Key)"
                        if has_gemini_key
                        else "Google Gemini AI: 🔴 Chưa cấu hình Key (Click để nhận & nhập Key miễn phí)"
                    )
                )
        else:
            self.api_chip.setText(self._full_api_text)
            self.api_chip.setToolTip("Click để mở Cài đặt Voice API")
            if hasattr(self, "btn_gemini_chip"):
                self.btn_gemini_chip.setText("🟢 Gemini AI" if is_gemini_connected else "🔴 Gemini AI")
                self.btn_gemini_chip.setToolTip(
                    f"Google Gemini AI: 🟢 Đã kết nối (Model: {gemini_model}) - Click để sửa"
                    if is_gemini_connected
                    else (
                        "Google Gemini AI: 🔴 Chưa kết nối (Click để kiểm tra API Key)"
                        if has_gemini_key
                        else "Google Gemini AI: 🔴 Chưa cấu hình Key (Click để nhận & nhập Key miễn phí)"
                    )
                )

        if hasattr(self, "btn_gemini_chip"):
            if is_gemini_connected:
                self.btn_gemini_chip.setStyleSheet(
                    "background-color: #052e16; border: 1px solid #16a34a; "
                    "border-radius: 6px; padding: 4px 6px; color: #4ade80; "
                    "font-size: 11px; font-weight: 700; min-height: 24px;"
                )
            else:
                self.btn_gemini_chip.setStyleSheet(
                    "background-color: #450a0a; border: 1px solid #dc2626; "
                    "border-radius: 6px; padding: 4px 6px; color: #f87171; "
                    "font-size: 11px; font-weight: 700; min-height: 24px;"
                )

    def open_gemini_key_dialog(self) -> None:
        """Mở hộp thoại cấu hình Google Gemini API Key trực tiếp từ sidebar."""
        dialog = GeminiKeyDialog(self)
        dialog.key_saved.connect(self._on_gemini_key_updated)
        dialog.exec()
        self._refresh_api_chip_display()

    def _on_gemini_key_updated(self, key: str, model: str) -> None:
        """Cập nhật giao diện và đồng bộ sang SettingsTab sau khi lưu Gemini Key."""
        self._refresh_api_chip_display()
        if hasattr(self, "settings_tab"):
            self.settings_tab.edit_gemini_key.setText(key)
            idx = self.settings_tab.combo_gemini_model.findData(model)
            if idx != -1:
                self.settings_tab.combo_gemini_model.setCurrentIndex(idx)

    def _on_gemini_key_saved_from_settings(self, key: str) -> None:
        """Cập nhật trạng thái nút trên Sidebar khi user lưu key từ trang Cài đặt."""
        self._refresh_api_chip_display()

    def on_account_updated(self, info: dict) -> None:
        credits = info.get("credit_balance", info.get("credits", 0))
        self.tts_tab.set_credit_balance(credits)
        self.project_workspace.tts_tab.set_credit_balance(credits)
        self.settings_tab.update_account_info(info)
        self._full_api_text = f"● Voice API: {credits:,} credits"
        self.api_chip.setStyleSheet(
            "background-color: #064e3b; border: 1px solid #065f46; "
            "border-radius: 6px; padding: 4px 10px; color: #34d399; "
            "font-size: 11px; font-weight: 600;"
            if credits > 0 else ""
        )
        self._refresh_api_chip_display()

    def update_api_status_badge(self, *_args) -> None:
        self.api_chip.setStyleSheet("")
        self._full_api_text = (
            "Voice API\nĐã cấu hình" if config.settings.VIBI_API_KEY.strip()
            else "Voice API\nChưa cấu hình"
        )
        self._refresh_api_chip_display()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(4)

        self.btn_nav_project = self.create_nav_btn("📁  Dự án", 0)
        self.btn_nav_watermark = self.create_nav_btn("🍌  Gỡ watermark", 1)
        self.btn_nav_tts = self.create_nav_btn("🎙  Tạo Voice TTS", 2)
        self.btn_nav_trending = self.create_nav_btn("🔥  Xu hướng & Ý tưởng", 3)
        self.btn_nav_settings = self.create_nav_btn("⚙  Cài đặt", 4)
        for button in self.nav_buttons:
            layout.addWidget(button)
        layout.addStretch()

        sidebar_footer = QWidget()
        sidebar_footer.setObjectName("sidebar_footer")
        footer_layout = QHBoxLayout(sidebar_footer)
        footer_layout.setContentsMargins(10, 8, 10, 8)
        footer_layout.setSpacing(6)

        # Nút Gemini API (Bên trái nút Voice API)
        self.btn_gemini_chip = QPushButton()
        self.btn_gemini_chip.setObjectName("gemini_chip")
        self.btn_gemini_chip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gemini_chip.clicked.connect(self.open_gemini_key_dialog)
        footer_layout.addWidget(self.btn_gemini_chip, stretch=1)

        # Nút/Chip Voice API (Bên phải)
        self.api_chip = QLabel()
        self.api_chip.setObjectName("api_chip")
        self.api_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.api_chip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.api_chip.mousePressEvent = lambda _: self.switch_page(4)
        footer_layout.addWidget(self.api_chip, stretch=1)

        layout.addWidget(sidebar_footer)
        return sidebar

    def create_nav_btn(self, title: str, index: int, icon: str = "") -> QPushButton:
        if not icon:
            parsed_icon, clean_title = split_icon_and_title(title)
            icon = parsed_icon or "📌"
            full_label = title
            display_title = clean_title or title
        else:
            full_label = f"{icon}  {title}"
            display_title = title

        button = QPushButton(full_label)
        button.setObjectName("nav_btn")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setProperty("icon_text", icon)
        button.setProperty("full_title", full_label)
        button.setProperty("title_text", display_title)
        button.setToolTip(full_label)
        button.clicked.connect(lambda _, page=index: self.switch_page(page))
        self.nav_buttons.append(button)
        return button

    def switch_page(self, index: int) -> None:
        if not 0 <= index < self.stack.count():
            return
        previous_index = self.stack.currentIndex()
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        self.standalone_state.save_last_page(index)
        if index == 0 and (previous_index == 0 or not self.project_workspace.current_project):
            self.project_workspace.show_project_list()

    def open_tts_with_script(self, script: str = "") -> None:
        """Chuyển sang trang Tạo Voice TTS và nạp kịch bản vào ô nhập liệu."""
        if script and hasattr(self, "tts_tab"):
            self.tts_tab.set_script_text(script)
        self.switch_page(2)

    def closeEvent(self, event) -> None:
        if self._download_thread and self._download_thread.isRunning():
            QMessageBox.information(self, "Đang tải cập nhật", "Vui lòng đợi tải xong trước khi đóng ứng dụng.")
            event.ignore()
            return
        if self._staged_update:
            try:
                launch_update_helper(Path(sys.executable), self._staged_update)
            except (OSError, RuntimeError, ValueError) as error:
                QMessageBox.warning(self, "Không thể cài cập nhật", str(error))
                event.ignore()
        if hasattr(self, "_update_timer") and self._update_timer.isActive():
            self._update_timer.stop()
        if hasattr(self, "_update_checker") and self._update_checker and self._update_checker.isRunning():
            self._update_checker.quit()
            self._update_checker.wait(500)
        if hasattr(self, "trending_tab") and hasattr(self.trending_tab, "_trends_worker") and self.trending_tab._trends_worker and self.trending_tab._trends_worker.isRunning():
            self.trending_tab._trends_worker.terminate()
            self.trending_tab._trends_worker.wait(500)
        self.tts_tab.flush_standalone_state()
        super().closeEvent(event)

    def _build_title_bar(self) -> QFrame:
        update_bar = QFrame()
        update_bar.setObjectName("update_bar")
        update_bar.setMinimumHeight(52)
        layout = QHBoxLayout(update_bar)
        layout.setContentsMargins(14, 10, 24, 10)
        layout.setSpacing(12)

        # Nút ẩn / hiện sidebar
        self.btn_toggle_sidebar = QPushButton("☰")
        self.btn_toggle_sidebar.setObjectName("btn_toggle_sidebar")
        self.btn_toggle_sidebar.setToolTip("Ẩn/Hiện thanh điều hướng bên trái (Ctrl+B)")
        self.btn_toggle_sidebar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_sidebar.setFixedSize(34, 32)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.btn_toggle_sidebar)

        title = QLabel("Editor Video AI")
        title.setProperty("class", "app_title_text")
        layout.addWidget(title)
        layout.addStretch()

        self.update_status_label = QLabel(f"v{APP_VERSION}  •  Chưa kiểm tra")
        self.update_status_label.setProperty("class", "text_muted_12")
        layout.addWidget(self.update_status_label)
        self.update_button = QPushButton("Kiểm tra cập nhật")
        self.update_button.setObjectName("btn_subtle")
        self.update_button.clicked.connect(self._check_update_manually)
        layout.addWidget(self.update_button)
        return update_bar

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        """Thu gọn sidebar về dạng icon-only (Mini) hoặc mở rộng đầy đủ (Expanded)."""
        self.is_sidebar_collapsed = collapsed
        self.sidebar.setVisible(True)
        self.sidebar.setProperty("mini", "true" if collapsed else "false")
        self.sidebar.setFixedWidth(64 if collapsed else 260)

        for btn in self.nav_buttons:
            if collapsed:
                btn.setText(btn.property("icon_text") or "📌")
                btn.setToolTip(btn.property("full_title") or "")
            else:
                btn.setText(btn.property("full_title") or "")
                btn.setToolTip("")

        if collapsed:
            self.btn_toggle_sidebar.setToolTip("Mở rộng thanh điều hướng bên trái (Ctrl+B)")
            self.btn_toggle_sidebar.setText("▶")
        else:
            self.btn_toggle_sidebar.setToolTip("Thu gọn thanh điều hướng bên trái (Ctrl+B)")
            self.btn_toggle_sidebar.setText("◀")

        self._refresh_api_chip_display()

        self.sidebar.style().unpolish(self.sidebar)
        self.sidebar.style().polish(self.sidebar)
        for btn in self.nav_buttons:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.standalone_state.save_sidebar_collapsed(collapsed)

    def toggle_sidebar(self) -> None:
        """Bật/tắt chế độ thu gọn thanh điều hướng (Sidebar)."""
        self.set_sidebar_collapsed(not self.is_sidebar_collapsed)

    def set_sidebar_visible(self, visible: bool) -> None:
        """Tương thích ngược: visible=True là mở rộng, visible=False là thu gọn mini."""
        self.set_sidebar_collapsed(not visible)

    def _check_update_automatically(self) -> None:
        if getattr(sys, "frozen", False):
            self._start_update_check(manual=False)

    def _check_update_manually(self) -> None:
        if not getattr(sys, "frozen", False):
            QMessageBox.information(
                self, "Cập nhật ứng dụng",
                "Tự cập nhật chỉ hỗ trợ bản đóng gói. Hãy chạy EditorVideoApp để kiểm tra và cài bản mới.",
            )
            return
        self._start_update_check(manual=True)

    def _start_update_check(self, *, manual: bool) -> None:
        if getattr(self, "_update_checker", None) and self._update_checker.isRunning():
            return
        self.update_button.setEnabled(False)
        self.update_status_label.setText("Đang kiểm tra cập nhật…")
        self._update_checker = UpdateCheckerThread(self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.no_update.connect(lambda: self._on_no_update(manual))
        self._update_checker.check_failed.connect(lambda message: self._on_update_check_failed(message, manual))
        self._update_checker.finished.connect(lambda: self.update_button.setEnabled(True))
        self._update_checker.start()

    def _on_update_available(self, update_info: dict) -> None:
        self.update_status_label.setText(f"↑ Có bản mới v{update_info['version']}")
        url = select_download_url(
            update_info.get("download_links") or [], sys.platform,
        )
        dialog = UpdateDialog(str(update_info["version"]), update_info["notes"], url, self)
        self._update_dialog = dialog
        if url:
            dialog.download_requested.connect(lambda: self._start_update_download(url, str(update_info["version"])))
            dialog.restart_requested.connect(self.close)
        dialog.exec()
        self._update_dialog = None

    def _start_update_download(self, url: str, version: str) -> None:
        if self._download_thread and self._download_thread.isRunning():
            return
        self._download_error = None
        self.update_button.setEnabled(False)
        self.update_status_label.setText(f"Đang tải v{version}…")
        if self._update_dialog:
            self._update_dialog.begin_download()
        self._download_thread = UpdateDownloadThread(url, Path(sys.executable), self)
        self._download_thread.progress.connect(lambda percent: self._on_update_download_progress(percent, version))
        self._download_thread.staged.connect(lambda path: self._on_update_staged(path, version))
        self._download_thread.failed.connect(self._on_update_download_failed)
        self._download_thread.finished.connect(lambda: self._on_update_download_finished(version))
        self._download_thread.start()

    def _on_update_download_progress(self, percent: int, version: str) -> None:
        if self._update_dialog:
            self._update_dialog.set_progress(percent)
        self.update_status_label.setText(f"Đang tải v{version}: {percent}%")

    def _on_update_staged(self, path: str, version: str) -> None:
        self._staged_update = Path(path)
        self.update_status_label.setText(f"Đã tải v{version} • Đóng app để cài")

    def _on_update_download_failed(self, message: str) -> None:
        self._download_error = message
        self.update_status_label.setText("Tải bản cập nhật thất bại")

    def _on_update_download_finished(self, version: str) -> None:
        self.update_button.setEnabled(True)
        if self._download_error:
            if self._update_dialog:
                self._update_dialog.show_error(self._download_error)
            else:
                QMessageBox.warning(self, "Không thể tải cập nhật", self._download_error)
            return
        if not self._staged_update:
            return
        if self._update_dialog:
            self._update_dialog.show_ready(version)

    def _show_update_error(self) -> None:
        marker = Path(sys.executable).parent / ".editor-update-error.txt"
        try:
            message = marker.read_text(encoding="utf-8")
            marker.unlink()
        except OSError:
            return
        QMessageBox.warning(self, "Cập nhật chưa hoàn tất", message)

    def _on_no_update(self, manual: bool) -> None:
        self.update_status_label.setText(f"✓ Đã cập nhật (v{APP_VERSION})")
        if manual:
            QMessageBox.information(self, "Kiểm tra cập nhật", "Bạn đang sử dụng phiên bản mới nhất.")

    def _on_update_check_failed(self, message: str, manual: bool) -> None:
        self.update_status_label.setText("Không thể kiểm tra cập nhật")
        if manual:
            QMessageBox.warning(self, "Kiểm tra cập nhật", f"Không thể kiểm tra bản cập nhật: {message}")

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("app_footer")
        footer.setMinimumHeight(54)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(6)

        zalo_icon = QLabel()
        zalo_icon.setPixmap(
            QPixmap(str(ICONS_DIR / "zalo.svg")).scaled(
                20, 20, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(zalo_icon)
        zalo_link = QLabel(
            '<a href="https://zalo.me/0975390291" '
            'style="color: #93c5fd; text-decoration: underline;">Zalo</a>'
        )
        zalo_link.setOpenExternalLinks(True)
        zalo_link.setProperty("class", "text_link_12")
        layout.addWidget(zalo_link)

        layout.addStretch()
        website_icon = QLabel()
        website_icon.setObjectName("footer_website_icon")
        website_icon.setPixmap(
            QPixmap(str(ICONS_DIR / "globe.svg")).scaled(
                18, 18, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(website_icon)
        website_link = QLabel(
            '<a href="https://portfolio-qucuongdev.vercel.app/" '
            'style="color: #dbeafe; text-decoration: none;">portfolio-qucuongdev</a>'
        )
        website_link.setObjectName("footer_website_link")
        website_link.setOpenExternalLinks(True)
        website_link.setProperty("class", "text_link_12")
        layout.addWidget(website_link)

        layout.addSpacing(16)
        donate_link = QLabel(
            '<span style="color: #fbbf24; text-decoration: none;">'
            '<span style="color: #fb7185; font-size: 15px;">♥</span> '
            'Momo: 0975390291</span>'
        )
        donate_link.setObjectName("footer_donate_link")
        donate_link.setToolTip("Donate qua Momo")
        donate_link.setProperty("class", "text_link_12")
        layout.addWidget(donate_link)

        layout.addSpacing(16)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setProperty("class", "vertical_divider")
        layout.addWidget(divider)
        layout.addSpacing(10)

        self.footer_creator = QLabel("© Created by: qucuongdev")
        self.footer_creator.setProperty("class", "text_muted_12")
        layout.addWidget(self.footer_creator)
        return footer
