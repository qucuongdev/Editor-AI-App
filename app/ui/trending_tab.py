"""
trending_tab.py: Giao diện Khám Phá Xu Hướng Google & Sinh Ý Tưởng Video AI.
Bao gồm 3 phân hệ trực quan:
1. Bảng Google Trends thời gian thực (Việt Nam & Quốc tế)
2. Ma trận 75 - 100 ý tưởng video đa góc nhìn (Bí ẩn, Lời khuyên, Tranh cãi, Kể chuyện, Hài hước)
3. Master Prompt Studio: Tùy biến thời lượng phát, phong cách, nền tảng và xuất Master Prompt cho AI.
"""

import re
from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QDate
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.trends_collector import (
    SUPPORTED_COUNTRIES,
    SUPPORTED_PLATFORMS,
    SUPPORTED_TIME_RANGES,
    fetch_google_trends,
    fetch_platform_trends,
)
from app.core.idea_generator import (
    ANGLE_METADATA,
    generate_video_ideas,
)
from app.core.prompt_builder import (
    DURATION_PRESETS,
    LANGUAGE_PRESETS,
    PLATFORM_PRESETS,
    TONE_PRESETS,
    build_master_prompt,
    format_duration_display,
    get_language_unit,
    get_word_count_range,
)
from app.ui.storyboard_dialog import StoryboardDialog


class TrendsWorker(QThread):
    """Worker chạy ngầm để lấy dữ liệu Trends không làm đơ giao diện."""
    trends_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        geo: str = "VN",
        platform: str = "google",
        time_range: str = "day",
        start_date: str = "",
        end_date: str = "",
    ):
        super().__init__()
        self.geo = geo
        self.platform = platform
        self.time_range = time_range
        self.start_date = start_date
        self.end_date = end_date
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            results = fetch_platform_trends(
                geo=self.geo,
                platform=self.platform,
                time_range=self.time_range,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            if not self._is_cancelled:
                self.trends_ready.emit(results)
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))


class GeminiIdeasWorker(QThread):
    """Worker chạy ngầm kết nối Google Gemini AI để sinh ý tưởng video viral."""
    ideas_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, topic: str, count: int = 12):
        super().__init__()
        self.topic = topic
        self.count = count
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            from app.core.gemini_client import generate_video_ideas_with_gemini
            results = generate_video_ideas_with_gemini(topic=self.topic, count=self.count)
            if not self._is_cancelled:
                self.ideas_ready.emit(results)
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))


class TrendingTab(QWidget):
    """Tab Khám Phá Xu Hướng & Sinh Ý Tưởng Video AI."""

    request_open_tts = pyqtSignal(str)  # Gửi văn bản kịch bản sang Tab Giọng Nói

    PAGE_TRENDS = 0
    PAGE_IDEAS = 1
    PAGE_PROMPT = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("trending_tab")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.current_trends: List[Dict[str, Any]] = []
        self.current_ideas: List[Dict[str, Any]] = []
        self.filtered_ideas: List[Dict[str, Any]] = []
        self.active_topic: str = ""
        self.selected_idea: Optional[Dict[str, Any]] = None
        self.active_angle_filter: str = "all"

        self._trends_worker: Optional[TrendsWorker] = None
        self._gemini_ideas_worker: Optional[GeminiIdeasWorker] = None

        self._build_ui()
        self.load_trends(geo="VN", platform="google", time_range="day")

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(14)

        # 1. Header Bar
        header_box = QHBoxLayout()
        header_box.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        lbl_title = QLabel("🔥 Khám Phá Xu Hướng Đa Nền Tảng & Ý Tưởng Video AI")
        lbl_title.setObjectName("page_title")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")

        lbl_subtitle = QLabel(
            "Cập nhật xu hướng Google, YouTube, TikTok, Facebook, Instagram, Threads, X thời gian thực và tạo Master Prompt viết kịch bản."
        )
        lbl_subtitle.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_subtitle)
        header_box.addLayout(title_box, stretch=1)

        # Refresh button
        self.btn_refresh = QPushButton("🔄 Làm mới Trends")
        self.btn_refresh.setObjectName("btn_subtle")
        self.btn_refresh.setFixedWidth(140)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        header_box.addWidget(self.btn_refresh)

        root_layout.addLayout(header_box)

        # 2. Main Stack Container
        self.stack = QStackedWidget()
        self.stack.setObjectName("trending_stack")

        self.page_trends_widget = self._build_trends_page()
        self.page_ideas_widget = self._build_ideas_page()
        self.page_prompt_widget = self._build_prompt_page()

        self.stack.addWidget(self.page_trends_widget)  # 0
        self.stack.addWidget(self.page_ideas_widget)   # 1
        self.stack.addWidget(self.page_prompt_widget)  # 2

        root_layout.addWidget(self.stack, stretch=1)

    # ================= PAGE 0: GOOGLE TRENDS =================
    def _build_trends_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Custom Keyword Search Card & Suggested Topic ComboBox (1 hàng tinh gọn duy nhất)
        search_card = QFrame()
        search_card.setProperty("class", "panel")
        search_card.setStyleSheet(
            "background-color: #161822; border: 1px solid #2a2f42; border-radius: 10px; padding: 8px 14px;"
        )
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(8, 4, 8, 4)
        search_layout.setSpacing(10)

        lbl_or = QLabel("💡 Chủ đề:")
        lbl_or.setStyleSheet("font-weight: 600; color: #e2e8f0; font-size: 13px;")
        search_layout.addWidget(lbl_or)

        self.txt_custom_topic = QLineEdit()
        self.txt_custom_topic.setPlaceholderText(
            "Nhập từ khóa tự do (ví dụ: Sinh tồn tài chính, Mẹo tiết kiệm bão giá, Kitô giáo, AI 2026...)"
        )
        self.txt_custom_topic.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 8px; padding: 7px 12px; color: #f8fafc; font-size: 13px;"
        )
        self.txt_custom_topic.returnPressed.connect(self._on_generate_custom_clicked)
        search_layout.addWidget(self.txt_custom_topic, stretch=1)

        lbl_suggest = QLabel("🔥 Hoặc chọn gợi ý:")
        lbl_suggest.setStyleSheet("font-weight: 600; color: #f59e0b; font-size: 12px;")
        search_layout.addWidget(lbl_suggest)

        self.combo_suggested_topics = QComboBox()
        self.combo_suggested_topics.setObjectName("combo_suggested_topics")
        self.combo_suggested_topics.setFixedWidth(280)
        self.combo_suggested_topics.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 8px; padding: 6px 10px; color: #f8fafc; font-size: 12px;"
        )

        suggested_topic_items = [
            ("-- Chọn chủ đề hot có sẵn --", ""),
            # Tài chính & Sinh tồn đô thị
            ("💰 Sinh tồn tài chính thành phố", "Sinh tồn tài chính và chi tiêu thông minh tại thành phố"),
            ("📉 Tiết kiệm thời bão giá", "Mẹo tiết kiệm chi tiêu gia đình và sinh tồn thời bão giá"),
            ("🏠 Mua nhà vs Thuê nhà", "Mua nhà trả góp 25 năm hay thuê nhà trọn đời"),
            ("💳 Cạm bẫy thẻ tín dụng & BNPL", "Cạm bẫy thẻ tín dụng và mua trước trả sau"),
            ("🪙 Vàng, Tiền mặt hay BĐS", "Nên giữ tiền mặt, mua vàng hay bất động sản thời bất ổn"),
            # Tôn giáo & Triết học đức tin
            ("🏛️ Kitô giáo & Vatican", "Kitô giáo và Bí ẩn Kho lưu trữ Vatican"),
            ("🪷 Phật giáo & Thiền định", "Triết lý Phật giáo, luật nhân quả và thiền định"),
            ("🕋 Hồi giáo & Mecca", "Hồi giáo và Cuộc hành hương thánh địa Mecca"),
            ("⚡ Khoa học vs Tôn giáo", "Khoa học và Tôn giáo: Cuộc đối đầu lịch sử"),
            ("⚖️ Sùng đạo vs Cuồng tín", "Lòng sùng đạo chân chính và ranh giới cuồng tín"),
            ("🔮 Giáo phái bí ẩn (Cults)", "Góc khuất các giáo phái bí ẩn và thao túng tâm lý"),
            ("📜 Cuộn sách Biển Chết", "Bí mật Cuộn sách Biển Chết và văn tự cổ"),
            # Công nghệ
            ("🤖 Trí tuệ nhân tạo AI", "Trí tuệ nhân tạo AI 2026"),
        ]

        self.suggested_pill_buttons: List[QPushButton] = []
        for label, val in suggested_topic_items:
            self.combo_suggested_topics.addItem(label, val)

        self.combo_suggested_topics.currentIndexChanged.connect(self._on_suggested_combo_changed)
        search_layout.addWidget(self.combo_suggested_topics)

        self.btn_generate_custom = QPushButton("✨ Sinh 100 Ý Tưởng")
        self.btn_generate_custom.setObjectName("btn_primary")
        self.btn_generate_custom.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate_custom.setStyleSheet(
            "background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #7c3aed); "
            "color: #ffffff; font-weight: 700; border-radius: 8px; padding: 8px 18px; font-size: 13px; border: none;"
        )
        self.btn_generate_custom.clicked.connect(self._on_generate_custom_clicked)
        search_layout.addWidget(self.btn_generate_custom)

        layout.addWidget(search_card)

        # 2. Filter Toolbar (Platform, Time Range, Custom Date, Country)
        filter_card = QFrame()
        filter_card.setProperty("class", "panel")
        filter_card.setStyleSheet(
            "background-color: #141620; border: 1px solid #252938; border-radius: 10px; padding: 6px 12px;"
        )
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(8, 6, 8, 6)
        filter_layout.setSpacing(10)

        # Platform selector
        lbl_plat = QLabel("Nền tảng:")
        lbl_plat.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        filter_layout.addWidget(lbl_plat)

        self.combo_platform_trends = QComboBox()
        self.combo_platform_trends.setObjectName("combo_platform_trends")
        for pcode, plabel, _, _ in SUPPORTED_PLATFORMS:
            self.combo_platform_trends.addItem(plabel, pcode)
        # Default Google Search (index 1)
        self.combo_platform_trends.setCurrentIndex(1)
        self.combo_platform_trends.setFixedWidth(190)
        self.combo_platform_trends.currentIndexChanged.connect(self._on_platform_trends_changed)
        filter_layout.addWidget(self.combo_platform_trends)

        # Time Range selector
        lbl_trange = QLabel("Mốc thời gian:")
        lbl_trange.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        filter_layout.addWidget(lbl_trange)

        self.combo_time_range = QComboBox()
        self.combo_time_range.setObjectName("combo_time_range")
        for trcode, trlabel in SUPPORTED_TIME_RANGES:
            self.combo_time_range.addItem(trlabel, trcode)
        self.combo_time_range.setMinimumWidth(215)
        self.combo_time_range.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.combo_time_range.currentIndexChanged.connect(self._on_time_range_changed)
        filter_layout.addWidget(self.combo_time_range)

        # Custom Date Range Box (Hidden by default)
        self.box_custom_dates = QWidget()
        box_dates_layout = QHBoxLayout(self.box_custom_dates)
        box_dates_layout.setContentsMargins(0, 0, 0, 0)
        box_dates_layout.setSpacing(6)

        lbl_from = QLabel("Từ:")
        lbl_from.setStyleSheet("color: #94a3b8; font-size: 12px;")
        box_dates_layout.addWidget(lbl_from)

        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        self.date_start.setDisplayFormat("dd/MM/yyyy")
        self.date_start.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 4px; padding: 4px 8px; color: #f8fafc;"
        )
        box_dates_layout.addWidget(self.date_start)

        lbl_to = QLabel("Đến:")
        lbl_to.setStyleSheet("color: #94a3b8; font-size: 12px;")
        box_dates_layout.addWidget(lbl_to)

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setDisplayFormat("dd/MM/yyyy")
        self.date_end.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 4px; padding: 4px 8px; color: #f8fafc;"
        )
        box_dates_layout.addWidget(self.date_end)

        self.btn_apply_date = QPushButton("Lọc")
        self.btn_apply_date.setObjectName("btn_subtle")
        self.btn_apply_date.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply_date.setStyleSheet(
            "background-color: #4f46e5; color: #ffffff; font-weight: 600; padding: 4px 12px; border-radius: 6px; border: none;"
        )
        self.btn_apply_date.clicked.connect(self._on_apply_custom_date)
        box_dates_layout.addWidget(self.btn_apply_date)

        self.box_custom_dates.setVisible(False)
        filter_layout.addWidget(self.box_custom_dates)

        # Country selector
        lbl_country = QLabel("Khu vực:")
        lbl_country.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        filter_layout.addWidget(lbl_country)

        self.combo_country = QComboBox()
        self.combo_country.setObjectName("combo_country")
        for code, label in SUPPORTED_COUNTRIES:
            self.combo_country.addItem(label, code)
        self.combo_country.setFixedWidth(160)
        self.combo_country.currentIndexChanged.connect(self._on_country_changed)
        filter_layout.addWidget(self.combo_country)

        # Search / Scan button
        self.btn_search_trends = QPushButton("🔍 Quét Xu Hướng")
        self.btn_search_trends.setObjectName("btn_search_trends")
        self.btn_search_trends.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search_trends.setStyleSheet(
            "background-color: #4f46e5; color: #ffffff; font-weight: 700; border-radius: 8px; padding: 7px 18px; font-size: 13px; border: none;"
        )
        self.btn_search_trends.clicked.connect(self._on_search_clicked)
        filter_layout.addWidget(self.btn_search_trends)

        filter_layout.addStretch()
        layout.addWidget(filter_card)

        # 3. Status row
        status_row = QHBoxLayout()
        self.lbl_trends_status = QLabel("Đang tải dữ liệu xu hướng Google Trends...")
        self.lbl_trends_status.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 13px;")
        status_row.addWidget(self.lbl_trends_status)
        status_row.addStretch()
        layout.addLayout(status_row)

        # 4. Visual Loading Progress Bar (animated indeterminate)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #1e293b; border: none; border-radius: 1px; } "
            "QProgressBar::chunk { background-color: #38bdf8; border-radius: 1px; }"
        )
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 5. Scroll Area for Trends
        self.scroll_trends = QScrollArea()
        self.scroll_trends.setWidgetResizable(True)
        self.scroll_trends.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_trends.setStyleSheet("background: transparent;")

        self.trends_container = QWidget()
        self.trends_layout = QVBoxLayout(self.trends_container)
        self.trends_layout.setContentsMargins(0, 0, 10, 10)
        self.trends_layout.setSpacing(10)
        self.trends_layout.addStretch()

        self.scroll_trends.setWidget(self.trends_container)
        layout.addWidget(self.scroll_trends, stretch=1)
        return widget

    def load_trends(
        self,
        geo: Optional[str] = None,
        platform: Optional[str] = None,
        time_range: Optional[str] = None,
        start_date: str = "",
        end_date: str = "",
    ):
        target_geo = geo if geo is not None else (self.combo_country.currentData() or "VN")
        target_plat = platform if platform is not None else (self.combo_platform_trends.currentData() or "google")
        target_trange = time_range if time_range is not None else (self.combo_time_range.currentData() or "day")

        plat_name = self.combo_platform_trends.currentText()
        trange_name = self.combo_time_range.currentText()
        country_text = self.combo_country.currentText()

        self.lbl_trends_status.setText(
            f"⏳ Đang cập nhật xu hướng {plat_name} ({trange_name}) tại {country_text}..."
        )
        self.progress_bar.setVisible(True)
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("⏳ Đang tải...")
        if hasattr(self, "btn_search_trends"):
            self.btn_search_trends.setEnabled(False)
            self.btn_search_trends.setText("⏳ Đang quét...")

        if self._trends_worker:
            self._trends_worker.cancel()
            try:
                self._trends_worker.trends_ready.disconnect()
                self._trends_worker.error_occurred.disconnect()
            except Exception:
                pass
            if self._trends_worker.isRunning():
                self._trends_worker.wait(1000)

        self._trends_worker = TrendsWorker(
            geo=target_geo,
            platform=target_plat,
            time_range=target_trange,
            start_date=start_date,
            end_date=end_date,
        )
        self._trends_worker.trends_ready.connect(self._on_trends_loaded)
        self._trends_worker.error_occurred.connect(self._on_trends_error)
        self._trends_worker.start()

    def _on_trends_loaded(self, results: List[Dict[str, Any]]):
        self.current_trends = results
        self.progress_bar.setVisible(False)
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 Làm mới Trends")
        if hasattr(self, "btn_search_trends"):
            self.btn_search_trends.setEnabled(True)
            self.btn_search_trends.setText("🔍 Quét Xu Hướng")

        plat_name = self.combo_platform_trends.currentText()
        trange_name = self.combo_time_range.currentText()
        country_text = self.combo_country.currentText()

        self.lbl_trends_status.setText(
            f"✓ Đã tìm thấy {len(results)} chủ đề thịnh hành trên {plat_name} ({trange_name}) tại {country_text}. Nhấp vào bất kỳ chủ đề nào để sinh 100 ý tưởng video."
        )

        # Clear old items
        while self.trends_layout.count() > 1:
            child = self.trends_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for item in results:
            card = self._create_trend_card(item)
            self.trends_layout.insertWidget(self.trends_layout.count() - 1, card)

    def _on_trends_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 Làm mới Trends")
        if hasattr(self, "btn_search_trends"):
            self.btn_search_trends.setEnabled(True)
            self.btn_search_trends.setText("🔍 Quét Xu Hướng")
        self.lbl_trends_status.setText(f"⚠️ Không thể tải dữ liệu mới ({err_msg}). Đang hiển thị danh mục xu hướng mẫu.")

    def _create_trend_card(self, item: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setProperty("class", "panel")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(
            """
            QFrame {
                background-color: #141721;
                border: 1px solid #272b3a;
                border-radius: 10px;
                padding: 12px 16px;
            }
            QFrame:hover {
                background-color: #1a1e2b;
                border: 1px solid #6366f1;
            }
            """
        )

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(14)

        # Rank badge
        rank_badge = QLabel(f"#{item['rank']}")
        rank_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rank_badge.setFixedSize(42, 42)
        rank_badge.setStyleSheet(
            "background-color: #1e2230; color: #38bdf8; font-size: 15px; font-weight: 800; border-radius: 8px;"
        )
        layout.addWidget(rank_badge)

        # Topic Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Platform badge
        plat_icon = item.get("platform_icon") or "🔥"
        plat_name = item.get("platform_name") or "Xu hướng"
        plat_badge = QLabel(f"{plat_icon} {plat_name}")
        plat_badge.setStyleSheet(
            "background-color: #1e2230; color: #94a3b8; font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 4px; border: 1px solid #334155;"
        )
        top_row.addWidget(plat_badge)

        # Title
        title_lbl = QLabel(item["title"])
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        top_row.addWidget(title_lbl)

        # Traffic / metric badge
        metric = item.get("metric_label") or "lượt quan tâm"
        traffic_str = item.get("traffic") or "500+"
        traffic_badge = QLabel(f"🔥 {traffic_str} {metric}")
        traffic_badge.setStyleSheet(
            "background-color: #451a03; color: #f97316; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;"
        )
        top_row.addWidget(traffic_badge)
        top_row.addStretch()

        info_layout.addLayout(top_row)

        snippet = item.get("news_snippet") or item.get("news_title") or "Chủ đề đang nhận được lượng quan tâm lớn trên mạng xã hội."
        snippet_lbl = QLabel(snippet)
        snippet_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        snippet_lbl.setWordWrap(True)
        info_layout.addWidget(snippet_lbl)

        layout.addLayout(info_layout, stretch=1)

        # Action button
        btn_action = QPushButton("✨ Sinh 100 Ý Tưởng")
        btn_action.setObjectName("btn_subtle")
        btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_action.setStyleSheet(
            "background-color: #1e2230; color: #a5b4fc; font-weight: 700; padding: 8px 16px; border-radius: 6px; border: 1px solid #6366f1;"
        )
        topic_title = item["title"]
        btn_action.clicked.connect(lambda _, t=topic_title: self.open_ideas_for_topic(t))
        layout.addWidget(btn_action)

        # Click on card to open
        card.mousePressEvent = lambda e, t=topic_title: self.open_ideas_for_topic(t)

        return card

    def _on_platform_trends_changed(self):
        self.load_trends()

    def _on_time_range_changed(self):
        is_custom = (self.combo_time_range.currentData() == "custom")
        self.box_custom_dates.setVisible(is_custom)
        if not is_custom:
            self.load_trends()

    def _on_apply_custom_date(self):
        s_date = self.date_start.date().toString("yyyy-MM-dd")
        e_date = self.date_end.date().toString("yyyy-MM-dd")
        self.load_trends(start_date=s_date, end_date=e_date)

    def _on_country_changed(self):
        self.load_trends()

    def _on_search_clicked(self):
        self.load_trends()

    def _on_refresh_clicked(self):
        self.load_trends()

    def _on_generate_custom_clicked(self):
        topic = self.txt_custom_topic.text().strip()
        if topic:
            self.open_ideas_for_topic(topic)

    def _on_suggested_combo_changed(self, index: int):
        topic = self.combo_suggested_topics.itemData(index)
        if topic:
            self.txt_custom_topic.setText(topic)
            self.open_ideas_for_topic(topic)

    def _on_suggested_topic_clicked(self, topic: str):
        self.txt_custom_topic.setText(topic)
        self.open_ideas_for_topic(topic)

    # ================= PAGE 1: IDEA MATRIX =================
    def _build_ideas_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Nav Header Bar
        top_nav = QHBoxLayout()
        top_nav.setSpacing(10)

        self.btn_back_to_trends = QPushButton("← Trở về Xu Hướng")
        self.btn_back_to_trends.setObjectName("btn_subtle")
        self.btn_back_to_trends.setFixedWidth(150)
        self.btn_back_to_trends.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_to_trends.clicked.connect(lambda: self.stack.setCurrentIndex(self.PAGE_TRENDS))
        top_nav.addWidget(self.btn_back_to_trends)

        self.lbl_active_topic = QLabel("Chủ đề: ...")
        self.lbl_active_topic.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        top_nav.addWidget(self.lbl_active_topic, stretch=1)

        # Source badge (Gemini AI vs Offline template)
        self.lbl_ideas_source_badge = QLabel("📐 Mẫu Offline (75 ý tưởng)")
        self.lbl_ideas_source_badge.setStyleSheet(
            "background-color: #1e293b; color: #94a3b8; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid #334155;"
        )
        top_nav.addWidget(self.lbl_ideas_source_badge)

        # Regenerate / Rerun AI button
        self.btn_refresh_ideas = QPushButton("🔄 Sinh Lại Ý Tưởng")
        self.btn_refresh_ideas.setObjectName("btn_subtle")
        self.btn_refresh_ideas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_ideas.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; font-size: 12px; font-weight: 600; padding: 5px 12px; border-radius: 6px; border: 1px solid #334155;"
        )
        self.btn_refresh_ideas.clicked.connect(self._on_refresh_ideas_clicked)
        top_nav.addWidget(self.btn_refresh_ideas)

        # Fast Filter text input
        self.txt_filter_ideas = QLineEdit()
        self.txt_filter_ideas.setPlaceholderText("🔍 Lọc nhanh ý tưởng...")
        self.txt_filter_ideas.setFixedWidth(220)
        self.txt_filter_ideas.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 6px; padding: 5px 10px; color: #f8fafc; font-size: 12px;"
        )
        self.txt_filter_ideas.textChanged.connect(self._apply_ideas_filter)
        top_nav.addWidget(self.txt_filter_ideas)

        layout.addLayout(top_nav)

        # Status row & Progress bar
        self.lbl_ideas_status = QLabel("")
        self.lbl_ideas_status.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 12px;")
        layout.addWidget(self.lbl_ideas_status)

        self.progress_ideas = QProgressBar()
        self.progress_ideas.setRange(0, 0)
        self.progress_ideas.setFixedHeight(3)
        self.progress_ideas.setTextVisible(False)
        self.progress_ideas.setStyleSheet(
            "QProgressBar { background-color: #1e293b; border: none; border-radius: 1px; } "
            "QProgressBar::chunk { background-color: #a855f7; border-radius: 1px; }"
        )
        self.progress_ideas.setVisible(False)
        layout.addWidget(self.progress_ideas)

        # Angle Filter Tabs Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.filter_btn_group = QButtonGroup(self)
        self.filter_buttons: Dict[str, QPushButton] = {}

        angles = [
            ("all", "🌟 Tất cả"),
            ("mystery", "🎯 Bí ẩn"),
            ("advice", "💡 Lời khuyên"),
            ("debate", "⚡ Tranh cãi"),
            ("story", "📖 Kể chuyện"),
            ("humor", "😂 Hài hước"),
        ]

        for idx, (akey, alabel) in enumerate(angles):
            btn = QPushButton(alabel)
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #171821;
                    border: 1px solid #2d303e;
                    border-radius: 6px;
                    padding: 5px 12px;
                    color: #94a3b8;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #1d4ed8;
                    border: 1px solid #3b82f6;
                    color: #ffffff;
                }
                QPushButton:hover:!checked {
                    background-color: #262938;
                }
                """
            )
            self.filter_btn_group.addButton(btn, idx)
            btn.clicked.connect(lambda _, k=akey: self._on_angle_filter_changed(k))
            self.filter_buttons[akey] = btn
            filter_row.addWidget(btn)

        filter_row.addStretch()

        # Target duration selector for Ideas page
        lbl_dur_ideas = QLabel("⏱ Thời lượng mục tiêu:")
        lbl_dur_ideas.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        filter_row.addWidget(lbl_dur_ideas)

        self.combo_ideas_duration = QComboBox()
        self.combo_ideas_duration.setObjectName("combo_ideas_duration")
        self.combo_ideas_duration.setMinimumWidth(215)
        self.combo_ideas_duration.setStyleSheet(
            "background-color: #171821; border: 1px solid #33384c; border-radius: 6px; padding: 4px 10px; color: #f8fafc; font-size: 12px;"
        )
        for dur, label, _, _ in DURATION_PRESETS:
            self.combo_ideas_duration.addItem(label, dur)
        self.combo_ideas_duration.setCurrentIndex(1)  # Default 60s
        self.combo_ideas_duration.currentIndexChanged.connect(self._on_ideas_duration_changed)
        filter_row.addWidget(self.combo_ideas_duration)

        self.box_ideas_custom_time = QWidget()
        self.box_ideas_custom_time.setObjectName("box_ideas_custom_time")
        ideas_custom_layout = QHBoxLayout(self.box_ideas_custom_time)
        ideas_custom_layout.setContentsMargins(0, 0, 0, 0)
        ideas_custom_layout.setSpacing(4)

        self.spin_ideas_custom_min = QSpinBox()
        self.spin_ideas_custom_min.setRange(0, 180)
        self.spin_ideas_custom_min.setValue(7)
        self.spin_ideas_custom_min.setSuffix(" phút")
        self.spin_ideas_custom_min.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 5px; padding: 3px 6px; color: #f8fafc; font-size: 12px;"
        )
        ideas_custom_layout.addWidget(self.spin_ideas_custom_min)

        self.spin_ideas_custom_sec = QSpinBox()
        self.spin_ideas_custom_sec.setRange(0, 59)
        self.spin_ideas_custom_sec.setValue(0)
        self.spin_ideas_custom_sec.setSuffix(" giây")
        self.spin_ideas_custom_sec.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 5px; padding: 3px 6px; color: #f8fafc; font-size: 12px;"
        )
        ideas_custom_layout.addWidget(self.spin_ideas_custom_sec)

        self.box_ideas_custom_time.setVisible(False)
        filter_row.addWidget(self.box_ideas_custom_time)

        layout.addLayout(filter_row)

        # Idea Scroll List (Lưới 2 Cột Studio Hiện Đại)
        self.scroll_ideas = QScrollArea()
        self.scroll_ideas.setWidgetResizable(True)
        self.scroll_ideas.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_ideas.setStyleSheet("background: transparent;")

        self.ideas_container = QWidget()
        self.ideas_layout = QGridLayout(self.ideas_container)
        self.ideas_layout.setContentsMargins(0, 0, 10, 10)
        self.ideas_layout.setSpacing(14)

        self.scroll_ideas.setWidget(self.ideas_container)
        layout.addWidget(self.scroll_ideas, stretch=1)
        return widget

    def open_ideas_for_topic(self, topic: str, force_offline: bool = False):
        self.active_topic = topic.strip()
        self.txt_filter_ideas.clear()
        self.active_angle_filter = "all"
        if "all" in self.filter_buttons:
            self.filter_buttons["all"].setChecked(True)

        from app import config
        is_gemini_active = bool(
            getattr(config, "GEMINI_CONNECTED", False)
            and getattr(config, "GEMINI_API_KEY", "").strip()
            and not force_offline
        )

        if is_gemini_active:
            model_name = getattr(config, "GEMINI_MODEL", "gemini-3.5-flash")
            self.lbl_active_topic.setText(f"🎯 Ý tưởng video AI: '{self.active_topic}'")
            self.lbl_ideas_source_badge.setText(f"✨ Gemini AI ({model_name})")
            self.lbl_ideas_source_badge.setStyleSheet(
                "background-color: #064e3b; color: #34d399; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #059669;"
            )
            self.lbl_ideas_status.setText(f"⏳ Gemini AI ({model_name}) đang phân tích chủ đề và sáng tạo ý tưởng video viral...")
            self.progress_ideas.setVisible(True)
            self.btn_refresh_ideas.setEnabled(False)
            self.btn_refresh_ideas.setText("⏳ Đang sinh...")

            if self._gemini_ideas_worker:
                self._gemini_ideas_worker.cancel()
                try:
                    self._gemini_ideas_worker.ideas_ready.disconnect()
                    self._gemini_ideas_worker.error_occurred.disconnect()
                except Exception:
                    pass
                if self._gemini_ideas_worker.isRunning():
                    self._gemini_ideas_worker.wait(1000)

            # Clear danh sách cũ
            while self.ideas_layout.count() > 0:
                child = self.ideas_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            self._gemini_ideas_worker = GeminiIdeasWorker(topic=self.active_topic, count=12)
            self._gemini_ideas_worker.ideas_ready.connect(self._on_gemini_ideas_ready)
            self._gemini_ideas_worker.error_occurred.connect(self._on_gemini_ideas_error)
            self._gemini_ideas_worker.start()
        else:
            self.progress_ideas.setVisible(False)
            self.btn_refresh_ideas.setEnabled(True)
            self.btn_refresh_ideas.setText("🔄 Làm mới ý tưởng")
            self.lbl_ideas_source_badge.setText("📐 Mẫu Offline (75 ý tưởng)")
            self.lbl_ideas_source_badge.setStyleSheet(
                "background-color: #1e293b; color: #94a3b8; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid #334155;"
            )
            self.lbl_active_topic.setText(f"🎯 75 Ý tưởng độc đáo: '{self.active_topic}'")
            self.lbl_ideas_status.setText("💡 Mẹo: Kết nối Gemini AI ở góc dưới Sidebar để tự động sinh ý tưởng viral độc nhất và không bị trùng lặp.")
            self.current_ideas = generate_video_ideas(self.active_topic, max_per_angle=15)
            self._render_ideas_list(self.current_ideas)

        self.stack.setCurrentIndex(self.PAGE_IDEAS)

    def _on_gemini_ideas_ready(self, ideas: List[Dict[str, Any]]):
        self.progress_ideas.setVisible(False)
        self.btn_refresh_ideas.setEnabled(True)
        self.btn_refresh_ideas.setText("🔄 AI Sinh Lại / Thêm")
        self.current_ideas = ideas
        from app import config
        model_name = getattr(config, "GEMINI_MODEL", "gemini-3.5-flash")
        self.lbl_active_topic.setText(f"🎯 {len(ideas)} Ý Tưởng Viral Sáng Tạo Bởi Gemini AI: '{self.active_topic}'")
        self.lbl_ideas_status.setText(f"✓ Gemini AI ({model_name}) đã tạo thành công {len(ideas)} ý tưởng sắc bén. Bạn có thể bấm AI Phân Cảnh hoặc Đọc Voice ngay.")
        self._render_ideas_list(ideas)

    def _on_gemini_ideas_error(self, err_msg: str):
        self.progress_ideas.setVisible(False)
        self.btn_refresh_ideas.setEnabled(True)
        self.btn_refresh_ideas.setText("🔄 Sinh Lại Ý Tưởng")
        self.current_ideas = generate_video_ideas(self.active_topic, max_per_angle=15)
        self.lbl_active_topic.setText(f"🎯 75 Ý tưởng cho: '{self.active_topic}'")
        self.lbl_ideas_source_badge.setText("📐 Mẫu Offline (Dự phòng)")
        self.lbl_ideas_source_badge.setStyleSheet(
            "background-color: #451a03; color: #f97316; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid #ea580c;"
        )
        self.lbl_ideas_status.setText(f"⚠️ Gemini AI gặp lỗi ({err_msg}). Đã tự động kích hoạt 75 ý tưởng mẫu offline.")
        self._render_ideas_list(self.current_ideas)

    def _on_refresh_ideas_clicked(self):
        if self.active_topic:
            self.open_ideas_for_topic(self.active_topic)

    def _on_angle_filter_changed(self, angle_key: str):
        self.active_angle_filter = angle_key
        self._apply_ideas_filter()

    def _apply_ideas_filter(self):
        query = self.txt_filter_ideas.text().strip().lower()
        filtered = []
        for idea in self.current_ideas:
            if self.active_angle_filter != "all" and idea["angle"] != self.active_angle_filter:
                continue
            if query and query not in idea["title"].lower() and query not in idea["description"].lower():
                continue
            filtered.append(idea)
        self._render_ideas_list(filtered)

    def _render_ideas_list(self, ideas: List[Dict[str, Any]]):
        while self.ideas_layout.count() > 0:
            child = self.ideas_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for idx, idea in enumerate(ideas):
            card = self._create_idea_card(idea)
            row = idx // 2
            col = idx % 2
            if isinstance(self.ideas_layout, QGridLayout):
                self.ideas_layout.addWidget(card, row, col)
            else:
                self.ideas_layout.addWidget(card)

    def _create_idea_card(self, idea: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setProperty("class", "panel")
        card.setStyleSheet(
            """
            QFrame {
                background-color: #141721;
                border: 1px solid #272b3a;
                border-radius: 12px;
                padding: 14px 16px;
            }
            QFrame:hover {
                background-color: #181c28;
                border: 1px solid #6366f1;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # 1. Top Row: Index Badge, Angle Badge, AI Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        idx_str = f"#{idea.get('index', 1):02d}"
        lbl_idx = QLabel(idx_str)
        lbl_idx.setStyleSheet(
            "background-color: #1e2230; color: #94a3b8; font-size: 11px; font-weight: 700; "
            "font-family: monospace; padding: 2px 7px; border-radius: 4px;"
        )
        top_row.addWidget(lbl_idx)

        angle = idea.get("angle", "mystery")
        angle_label = idea.get("angle_label", "🎯 Ý tưởng")
        angle_styles = {
            "mystery": "background-color: #3b1118; color: #fb7185; border: 1px solid #9f1239;",
            "advice": "background-color: #064e3b; color: #34d399; border: 1px solid #059669;",
            "debate": "background-color: #431407; color: #fb923c; border: 1px solid #ea580c;",
            "story": "background-color: #1e1b4b; color: #a5b4fc; border: 1px solid #4f46e5;",
            "humor": "background-color: #3b1c54; color: #c084fc; border: 1px solid #9333ea;",
            "future": "background-color: #083344; color: #38bdf8; border: 1px solid #0284c7;",
        }
        style = angle_styles.get(angle, "background-color: #1e293b; color: #38bdf8; border: 1px solid #334155;")
        lbl_angle = QLabel(angle_label)
        lbl_angle.setStyleSheet(f"{style} font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px;")
        top_row.addWidget(lbl_angle)

        if idea.get("is_ai_generated"):
            lbl_ai = QLabel("✨ Gemini AI")
            lbl_ai.setStyleSheet(
                "background-color: rgba(16, 185, 129, 0.15); color: #10b981; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px; border: 1px solid #10b981;"
            )
            top_row.addWidget(lbl_ai)

        top_row.addStretch()
        layout.addLayout(top_row)

        # 2. Title
        title_lbl = QLabel(idea["title"])
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff; line-height: 1.3;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        # 3. Hook 3s (Nổi bật, khung vàng hổ phách)
        hook = idea.get("hook_preview") or idea.get("hook") or ""
        if hook:
            hook_frame = QFrame()
            hook_frame.setStyleSheet(
                "background-color: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; border-radius: 4px; padding: 6px 10px;"
            )
            hook_box = QHBoxLayout(hook_frame)
            hook_box.setContentsMargins(4, 2, 4, 2)
            hook_lbl = QLabel(f"🔥 Hook 3s đầu: \"{hook}\"")
            hook_lbl.setStyleSheet("color: #fef3c7; font-size: 12px; font-style: italic; line-height: 1.3;")
            hook_lbl.setWordWrap(True)
            hook_box.addWidget(hook_lbl)
            layout.addWidget(hook_frame)

        # 4. Description
        desc = idea.get("description", "")
        if desc:
            desc_lbl = QLabel(f"📝 {desc}")
            desc_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; line-height: 1.35;")
            desc_lbl.setWordWrap(True)
            layout.addWidget(desc_lbl)

        # 5. Action Row: 3 nút hành động trực tiếp khoa học
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_row.addStretch()

        btn_direct_storyboard = QPushButton("⚡ AI Phân Cảnh")
        btn_direct_storyboard.setToolTip("Mở Storyboard Studio để AI viết kịch bản chi tiết từng cảnh")
        btn_direct_storyboard.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_direct_storyboard.setStyleSheet(
            "background-color: #6366f1; color: #ffffff; font-weight: 700; font-size: 11px; border-radius: 6px; padding: 6px 12px; border: none;"
        )
        btn_direct_storyboard.clicked.connect(lambda _, idata=idea: self._on_direct_storyboard_from_idea(idata))
        action_row.addWidget(btn_direct_storyboard)

        btn_direct_tts = QPushButton("🎙 Đọc Voice")
        btn_direct_tts.setToolTip("Tự động chuyển kịch bản sang Tab Giọng Nói để đọc voice")
        btn_direct_tts.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_direct_tts.setStyleSheet(
            "background-color: #1e293b; color: #34d399; font-weight: 600; font-size: 11px; border-radius: 6px; padding: 6px 12px; border: 1px solid #10b981;"
        )
        btn_direct_tts.clicked.connect(lambda _, idata=idea: self._on_direct_tts_from_idea(idata))
        action_row.addWidget(btn_direct_tts)

        btn_select = QPushButton("🚀 Master Prompt")
        btn_select.setToolTip("Tùy biến Master Prompt chi tiết theo thời lượng và nền tảng")
        btn_select.setObjectName("btn_primary")
        btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select.setStyleSheet(
            "background-color: #1e293b; color: #cbd5e1; font-weight: 600; font-size: 11px; border-radius: 6px; padding: 6px 12px; border: 1px solid #334155;"
        )
        btn_select.clicked.connect(lambda _, idata=idea: self.open_prompt_studio(idata))
        action_row.addWidget(btn_select)

        layout.addLayout(action_row)
        return card

    def _on_ideas_duration_changed(self):
        is_custom = (self.combo_ideas_duration.currentData() == -1)
        self.box_ideas_custom_time.setVisible(is_custom)

    def get_selected_ideas_duration(self) -> int:
        dur_val = self.combo_ideas_duration.currentData()
        if dur_val == -1:
            duration = self.spin_ideas_custom_min.value() * 60 + self.spin_ideas_custom_sec.value()
            return duration if duration > 0 else 60
        return dur_val if dur_val is not None and dur_val > 0 else 60

    def _on_direct_storyboard_from_idea(self, idea: Dict[str, Any]):
        title = idea.get("title", "")
        angle = idea.get("angle", "mystery")
        tone_map = {
            "mystery": "dramatic",
            "advice": "inspirational",
            "debate": "dramatic",
            "story": "emotional",
            "humor": "humorous",
            "future": "tech",
        }
        tone = tone_map.get(angle, "dramatic")
        duration = self.get_selected_ideas_duration()
        if duration <= 35:
            scene_count = 3
        elif duration <= 75:
            scene_count = 5
        elif duration <= 150:
            scene_count = 8
        else:
            scene_count = 10

        dlg = StoryboardDialog(
            topic=title,
            duration_seconds=duration,
            scene_count=scene_count,
            tone=tone,
            aspect_ratio="9:16",
            parent=self,
        )
        dlg.send_to_tts_requested.connect(self.request_open_tts.emit)
        dlg.exec()

    def _on_direct_tts_from_idea(self, idea: Dict[str, Any]):
        from app.core.storyboard_generator import generate_full_script_for_topic
        topic = idea.get("title", "")
        angle = idea.get("angle", "mystery")
        tone_map = {
            "mystery": "mystery",
            "advice": "educational",
            "debate": "shocking",
            "story": "storytelling",
            "humor": "humorous",
            "future": "mystery",
        }
        tone = tone_map.get(angle, "mystery")
        duration = self.get_selected_ideas_duration()
        script = generate_full_script_for_topic(topic=topic, duration_seconds=duration, tone=tone)
        if script:
            clipboard = QApplication.clipboard()
            clipboard.setText(script)
        self.request_open_tts.emit(script)

    # ================= PAGE 2: MASTER PROMPT STUDIO (SPLIT VIEW) =================
    def _build_prompt_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. Header Row
        nav_row = QHBoxLayout()
        nav_row.setSpacing(12)

        self.btn_back_to_ideas = QPushButton("← Trở về danh sách ý tưởng")
        self.btn_back_to_ideas.setObjectName("btn_subtle")
        self.btn_back_to_ideas.setFixedWidth(190)
        self.btn_back_to_ideas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_to_ideas.clicked.connect(self._on_back_to_ideas_clicked)
        nav_row.addWidget(self.btn_back_to_ideas)

        self.lbl_prompt_idea_title = QLabel("Ý tưởng: ...")
        self.lbl_prompt_idea_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        nav_row.addWidget(self.lbl_prompt_idea_title, stretch=1)

        layout.addLayout(nav_row)

        # 2. Main 2-Column Split Layout
        split_layout = QHBoxLayout()
        split_layout.setSpacing(16)

        # ---------------- CỘT TRÁI: SIDEBAR CẤU HÌNH (Width: 350px) ----------------
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("prompt_sidebar_frame")
        sidebar_frame.setFixedWidth(350)
        sidebar_frame.setStyleSheet(
            "QFrame#prompt_sidebar_frame { background-color: #141721; border: 1px solid #272b3a; border-radius: 10px; }"
        )
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(10)

        lbl_cfg_title = QLabel("⚙️ THIẾT LẬP KỊCH BẢN VIDEO")
        lbl_cfg_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #f8fafc; letter-spacing: 0.5px;")
        sidebar_layout.addWidget(lbl_cfg_title)

        # Thời lượng
        lbl_dur = QLabel("⏱ Thời lượng phát mục tiêu:")
        lbl_dur.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        sidebar_layout.addWidget(lbl_dur)

        self.combo_duration = QComboBox()
        self.combo_duration.setObjectName("combo_duration")
        self.combo_duration.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 6px; padding: 6px 10px; color: #f8fafc; font-size: 12px;"
        )
        for dur, label, _, _ in DURATION_PRESETS:
            self.combo_duration.addItem(label, dur)
        self.combo_duration.setCurrentIndex(1)  # Default 60s
        self.combo_duration.currentIndexChanged.connect(self._on_duration_combo_changed)
        sidebar_layout.addWidget(self.combo_duration)

        self.box_custom_time = QWidget()
        self.box_custom_time.setObjectName("box_custom_time")
        custom_layout = QHBoxLayout(self.box_custom_time)
        custom_layout.setContentsMargins(0, 2, 0, 2)
        custom_layout.setSpacing(6)

        lbl_custom_prefix = QLabel("⏱ Tùy chỉnh:")
        lbl_custom_prefix.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        custom_layout.addWidget(lbl_custom_prefix)

        self.spin_custom_min = QSpinBox()
        self.spin_custom_min.setRange(0, 180)
        self.spin_custom_min.setValue(7)
        self.spin_custom_min.setSuffix(" phút")
        self.spin_custom_min.setToolTip("Nhập số phút tùy ý (từ 0 đến 180 phút)")
        self.spin_custom_min.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 6px; padding: 4px 8px; color: #f8fafc; font-size: 12px;"
        )
        self.spin_custom_min.valueChanged.connect(self._rebuild_prompt)
        custom_layout.addWidget(self.spin_custom_min, stretch=1)

        self.spin_custom_sec = QSpinBox()
        self.spin_custom_sec.setRange(0, 59)
        self.spin_custom_sec.setValue(0)
        self.spin_custom_sec.setSuffix(" giây")
        self.spin_custom_sec.setToolTip("Nhập số giây tùy ý (từ 0 đến 59 giây)")
        self.spin_custom_sec.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 6px; padding: 4px 8px; color: #f8fafc; font-size: 12px;"
        )
        self.spin_custom_sec.valueChanged.connect(self._rebuild_prompt)
        custom_layout.addWidget(self.spin_custom_sec, stretch=1)

        self.box_custom_time.setVisible(False)
        sidebar_layout.addWidget(self.box_custom_time)

        # Nền tảng & Tỉ lệ
        lbl_plat = QLabel("📱 Nền tảng & Tỉ lệ:")
        lbl_plat.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        sidebar_layout.addWidget(lbl_plat)

        self.combo_platform = QComboBox()
        self.combo_platform.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 6px; padding: 6px 10px; color: #f8fafc; font-size: 12px;"
        )
        for pkey, plabel in PLATFORM_PRESETS:
            self.combo_platform.addItem(plabel, pkey)
        self.combo_platform.currentIndexChanged.connect(self._rebuild_prompt)
        sidebar_layout.addWidget(self.combo_platform)

        # Phong cách & Tông giọng
        lbl_tone = QLabel("🎭 Phong cách & Tông giọng:")
        lbl_tone.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        sidebar_layout.addWidget(lbl_tone)

        self.combo_tone = QComboBox()
        self.combo_tone.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 6px; padding: 6px 10px; color: #f8fafc; font-size: 12px;"
        )
        for tkey, tlabel in TONE_PRESETS:
            self.combo_tone.addItem(tlabel, tkey)
        self.combo_tone.currentIndexChanged.connect(self._rebuild_prompt)
        sidebar_layout.addWidget(self.combo_tone)

        # Ngôn ngữ
        lbl_lang = QLabel("🌐 Ngôn ngữ kịch bản:")
        lbl_lang.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        sidebar_layout.addWidget(lbl_lang)

        self.combo_language = QComboBox()
        self.combo_language.setStyleSheet(
            "background-color: #10121a; border: 1px solid #33384c; border-radius: 6px; padding: 6px 10px; color: #f8fafc; font-size: 12px;"
        )
        for lcode, llabel in LANGUAGE_PRESETS:
            self.combo_language.addItem(llabel, lcode)
        self.combo_language.currentIndexChanged.connect(self._rebuild_prompt)
        sidebar_layout.addWidget(self.combo_language)

        # Checkbox Phân cảnh
        self.chk_scenes = QCheckBox("Kèm phân cảnh SC01, SC02... & Prompt vẽ ảnh")
        self.chk_scenes.setChecked(True)
        self.chk_scenes.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        self.chk_scenes.stateChanged.connect(self._rebuild_prompt)
        sidebar_layout.addWidget(self.chk_scenes)

        # Divider
        div_line = QFrame()
        div_line.setFrameShape(QFrame.Shape.HLine)
        div_line.setStyleSheet("background-color: #272b3a; max-height: 1px;")
        sidebar_layout.addWidget(div_line)

        # Action Buttons
        lbl_actions = QLabel("🚀 HÀNH ĐỘNG NHANH 1-CLICK:")
        lbl_actions.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8;")
        sidebar_layout.addWidget(lbl_actions)

        self.btn_open_storyboard = QPushButton("⚡ Sinh Kịch Bản Phân Cảnh (AI Storyboard)")
        self.btn_open_storyboard.setObjectName("btn_storyboard")
        self.btn_open_storyboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_storyboard.setStyleSheet(
            "background-color: #6366f1; color: #ffffff; font-weight: 700; font-size: 12px; border-radius: 6px; padding: 9px 12px; border: none;"
        )
        self.btn_open_storyboard.clicked.connect(self._on_open_storyboard_clicked)
        sidebar_layout.addWidget(self.btn_open_storyboard)

        self.btn_open_tts = QPushButton("🎙 Chuyển sang Tạo Voice TTS")
        self.btn_open_tts.setObjectName("btn_subtle")
        self.btn_open_tts.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_tts.setStyleSheet(
            "background-color: #1e293b; color: #34d399; font-weight: 600; font-size: 12px; border-radius: 6px; padding: 9px 12px; border: 1px solid #10b981;"
        )
        self.btn_open_tts.clicked.connect(self._on_open_tts_clicked)
        sidebar_layout.addWidget(self.btn_open_tts)

        sidebar_layout.addStretch()
        split_layout.addWidget(sidebar_frame)

        # ---------------- CỘT PHẢI: PROMPT PREVIEW & STUDIO ----------------
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(10)

        preview_header = QHBoxLayout()
        preview_header.setSpacing(8)
        lbl_pv = QLabel("📋 Master Prompt AI:")
        lbl_pv.setStyleSheet("font-weight: 700; color: #f8fafc; font-size: 13px;")
        preview_header.addWidget(lbl_pv)

        self.lbl_word_info = QLabel("Ước tính: ~135 - 160 từ")
        self.lbl_word_info.setStyleSheet(
            "background-color: #0f172a; color: #38bdf8; font-weight: 600; font-size: 11px; "
            "padding: 3px 8px; border-radius: 4px; border: 1px solid #1e293b;"
        )
        preview_header.addWidget(self.lbl_word_info)
        preview_header.addStretch()

        self.btn_copy_prompt = QPushButton("📋 Sao chép Master Prompt")
        self.btn_copy_prompt.setObjectName("btn_primary")
        self.btn_copy_prompt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_prompt.setStyleSheet(
            "background-color: #16a34a; color: #ffffff; font-weight: 700; font-size: 13px; border-radius: 6px; padding: 8px 18px;"
        )
        self.btn_copy_prompt.clicked.connect(self._copy_prompt_to_clipboard)
        preview_header.addWidget(self.btn_copy_prompt)

        preview_layout.addLayout(preview_header)

        # Prompt Text Area
        self.txt_prompt = QPlainTextEdit()
        self.txt_prompt.setReadOnly(True)
        self.txt_prompt.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #101116;
                border: 1px solid #282a36;
                border-radius: 8px;
                padding: 14px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                color: #e2e8f0;
                line-height: 1.5;
            }
            """
        )
        preview_layout.addWidget(self.txt_prompt, stretch=1)

        split_layout.addWidget(preview_container, stretch=1)
        layout.addLayout(split_layout, stretch=1)
        return widget

    def _on_open_storyboard_clicked(self):
        topic = ""
        if self.selected_idea:
            topic = self.selected_idea.get("title", "")
        if not topic:
            topic = self.active_topic or self.txt_custom_topic.text().strip()

        # Đồng bộ cấu hình Thời lượng, Tông điệu và Tỉ lệ khung hình từ giao diện ngoài
        dur_val = self.combo_duration.currentData()
        if dur_val == -1:
            duration = self.spin_custom_min.value() * 60 + self.spin_custom_sec.value()
            if duration <= 0:
                duration = 60
        else:
            duration = dur_val if dur_val is not None and dur_val > 0 else 60

        tone = self.combo_tone.currentData() or "dramatic"
        platform = self.combo_platform.currentData() or "shorts"
        aspect_ratio = "16:9" if platform == "youtube" else "9:16"

        if duration <= 35:
            scene_count = 3
        elif duration <= 75:
            scene_count = 5
        elif duration <= 150:
            scene_count = 8
        else:
            scene_count = 10

        dlg = StoryboardDialog(
            topic=topic,
            duration_seconds=duration,
            scene_count=scene_count,
            tone=tone,
            aspect_ratio=aspect_ratio,
            parent=self,
        )
        dlg.send_to_tts_requested.connect(self.request_open_tts.emit)
        dlg.exec()

    def open_prompt_studio(self, idea: Dict[str, Any]):
        self.selected_idea = idea
        self.lbl_prompt_idea_title.setText(f"📝 Ý tưởng: {idea['title']}")
        # Đồng bộ thời lượng từ Trang Ý Tưởng sang Trang Master Prompt
        if hasattr(self, "combo_ideas_duration"):
            dur = self.combo_ideas_duration.currentData()
            idx = self.combo_duration.findData(dur)
            if idx != -1:
                self.combo_duration.setCurrentIndex(idx)
            if dur == -1:
                self.spin_custom_min.setValue(self.spin_ideas_custom_min.value())
                self.spin_custom_sec.setValue(self.spin_ideas_custom_sec.value())
                self.box_custom_time.setVisible(True)
        self._rebuild_prompt()
        self.stack.setCurrentIndex(self.PAGE_PROMPT)

    def _on_back_to_ideas_clicked(self):
        if hasattr(self, "combo_ideas_duration") and hasattr(self, "combo_duration"):
            dur = self.combo_duration.currentData()
            idx = self.combo_ideas_duration.findData(dur)
            if idx != -1:
                self.combo_ideas_duration.setCurrentIndex(idx)
            if dur == -1:
                self.spin_ideas_custom_min.setValue(self.spin_custom_min.value())
                self.spin_ideas_custom_sec.setValue(self.spin_custom_sec.value())
                self.box_ideas_custom_time.setVisible(True)
            else:
                self.box_ideas_custom_time.setVisible(False)
        self.stack.setCurrentIndex(self.PAGE_IDEAS)

    def _on_duration_combo_changed(self):
        is_custom = (self.combo_duration.currentData() == -1)
        self.box_custom_time.setVisible(is_custom)
        self._rebuild_prompt()

    def _rebuild_prompt(self):
        if not self.selected_idea:
            return

        dur_val = self.combo_duration.currentData()
        if dur_val == -1:
            duration = self.spin_custom_min.value() * 60 + self.spin_custom_sec.value()
            if duration <= 0:
                duration = 60
        else:
            duration = dur_val if dur_val is not None and dur_val > 0 else 60

        lang_code = self.combo_language.currentData() or "vi"
        tone = self.combo_tone.currentData() or "dramatic"
        platform = self.combo_platform.currentData() or "shorts"
        include_scenes = self.chk_scenes.isChecked()

        min_w, max_w, scenes = get_word_count_range(duration, lang_code=lang_code)
        unit_name = get_language_unit(lang_code)
        disp_time = format_duration_display(duration)
        self.lbl_word_info.setText(
            f"Ước tính: ~{min_w:,} - {max_w:,} {unit_name} ({scenes} phân cảnh cho {disp_time})"
        )

        prompt = build_master_prompt(
            topic=self.selected_idea.get("topic", self.active_topic),
            title=self.selected_idea["title"],
            angle_label=self.selected_idea.get("angle_label", "Tự nhiên"),
            duration_seconds=duration,
            tone=tone,
            platform=platform,
            include_scenes=include_scenes,
            include_image_prompts=include_scenes,
            extra_notes="",
            language=lang_code,
        )
        self.txt_prompt.setPlainText(prompt)

    def _copy_prompt_to_clipboard(self):
        text = self.txt_prompt.toPlainText().strip()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.btn_copy_prompt.setText("✓ Đã sao chép vào bộ nhớ tạm!")
            self.btn_copy_prompt.setStyleSheet(
                "background-color: #059669; color: #ffffff; font-weight: 700; font-size: 14px; border-radius: 6px; padding: 10px 22px;"
            )
            QTimer.singleShot(2000, self._reset_copy_button)

    def _reset_copy_button(self):
        self.btn_copy_prompt.setText("📋 Sao chép Master Prompt")
        self.btn_copy_prompt.setStyleSheet(
            "background-color: #16a34a; color: #ffffff; font-weight: 700; font-size: 14px; border-radius: 6px; padding: 10px 22px;"
        )

    def extract_script_for_tts(self) -> str:
        """Trích xuất kịch bản / lời thoại đầy đủ (Full Script) sẵn sàng đọc cho Tab TTS."""
        from app.core.storyboard_generator import generate_full_script_for_topic

        # 1. ƯU TIÊN 1: Nếu người dùng đang bôi đen một đoạn text bất kỳ trong ô Prompt
        selected = self.txt_prompt.textCursor().selectedText().replace("\u2029", "\n").strip()
        if len(selected) > 15:
            return selected

        prompt_text = self.txt_prompt.toPlainText().strip()

        is_template = (
            not prompt_text
            or "QUY TẮC BIÊN TẬP VÀNG" in prompt_text
            or "Bạn là một Biên Kịch Gia" in prompt_text
            or "ĐỊNH DẠNG KẾT QUẢ ĐẦU RA" in prompt_text
        )

        # 2. ƯU TIÊN 2: Nếu là template Master Prompt (hoặc chưa tạo prompt), kiểm tra xem người dùng đã dán kịch bản AI vào chưa
        if is_template:
            if prompt_text and ("### PHẦN 2:" in prompt_text or "PHẦN 2:" in prompt_text):
                parts = re.split(r"PHẦN 2[^\n]*", prompt_text, flags=re.IGNORECASE)
                if len(parts) > 1:
                    p2_content = parts[1].strip()
                    lines = [l.strip() for l in p2_content.splitlines() if l.strip()]
                    real_lines = [
                        l for l in lines
                        if not (l.startswith("(") and l.endswith(")"))
                        and "để tôi sao chép trực tiếp" not in l
                        and not l.upper().startswith("TOÀN BỘ LỜI THOẠI")
                    ]
                    # Nếu có nội dung kịch bản AI thực sự
                    if len(real_lines) >= 2 and sum(len(l) for l in real_lines) > 60:
                        return "\n\n".join(real_lines)

            # Nếu chưa có kịch bản AI dán vào -> Tự động sinh KỊCH BẢN ĐẦY ĐỦ (Full Script)
            # theo đúng thời lượng (30s, 60s, 120s...) gồm đầy đủ Hook ➔ Twist ➔ CTA
            topic = ""
            if self.selected_idea:
                topic = self.selected_idea.get("title", "")
            if not topic:
                topic = self.active_topic or self.txt_custom_topic.text().strip()

            dur_val = self.combo_duration.currentData()
            if dur_val == -1:
                duration = self.spin_custom_min.value() * 60 + self.spin_custom_sec.value()
                if duration <= 0:
                    duration = 60
            else:
                duration = dur_val if dur_val is not None and dur_val > 0 else 60

            tone = self.combo_tone.currentData() or "mystery"
            full_script = generate_full_script_for_topic(
                topic=topic,
                duration_seconds=duration,
                tone=tone,
            )
            if full_script:
                return full_script

        # 3. ƯU TIÊN 3: Người dùng đã xóa template và tự gõ / dán kịch bản riêng của họ
        return prompt_text

    def _on_open_tts_clicked(self):
        """Chuyển sang Tab Tạo Voice TTS cùng kịch bản đầy đủ."""
        script = self.extract_script_for_tts()
        if script:
            clipboard = QApplication.clipboard()
            clipboard.setText(script)
            word_count = len(script.split())
            self.btn_open_tts.setText(f"✓ Đã gửi kịch bản (~{word_count} từ)!")
            self.btn_open_tts.setStyleSheet(
                "background-color: #059669; color: #ffffff; font-weight: 700; font-size: 13px; border-radius: 6px; padding: 10px 18px;"
            )
            QTimer.singleShot(2500, self._reset_open_tts_button)
        self.request_open_tts.emit(script)

    def _reset_open_tts_button(self):
        self.btn_open_tts.setText("🎙 Chuyển sang Tạo Voice TTS")
        self.btn_open_tts.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; font-weight: 600; font-size: 13px; border-radius: 6px; padding: 10px 18px; border: 1px solid #334155;"
        )

    def closeEvent(self, event):
        if self._trends_worker:
            self._trends_worker.cancel()
            try:
                self._trends_worker.trends_ready.disconnect()
                self._trends_worker.error_occurred.disconnect()
            except Exception:
                pass
            if self._trends_worker.isRunning():
                self._trends_worker.wait(1000)

        if self._gemini_ideas_worker:
            self._gemini_ideas_worker.cancel()
            try:
                self._gemini_ideas_worker.ideas_ready.disconnect()
                self._gemini_ideas_worker.error_occurred.disconnect()
            except Exception:
                pass
            if self._gemini_ideas_worker.isRunning():
                self._gemini_ideas_worker.wait(1000)

        super().closeEvent(event)

