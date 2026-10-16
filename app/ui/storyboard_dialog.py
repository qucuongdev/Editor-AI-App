#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storyboard_dialog.py: Giao diện AI Storyboard Studio cho phép sinh kịch bản chi tiết,
tự động phân cảnh, hiển thị lời thoại và visual prompt, và gửi trực tiếp sang TTS hoặc Dự án video.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QWidget, QFrame,
    QPlainTextEdit, QMessageBox, QFileDialog, QApplication
)

from app import config
from app.core.storyboard_generator import (
    generate_storyboard,
    export_storyboard_to_scenes_json,
    export_storyboard_to_full_script,
    export_storyboard_to_markdown,
    StoryboardScene,
    VISUAL_STYLES,
    TONE_PROFILES,
)


class DragHandle(QLabel):
    """Nút biểu tượng ⠿ cho phép người dùng giữ và kéo thả để thay đổi vị trí phân cảnh."""

    def __init__(self, parent_card: "SceneCardWidget"):
        super().__init__("⠿", parent_card)
        self.parent_card = parent_card
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Giữ và kéo để đổi thứ tự phân cảnh (Drag & Drop)")
        self.setStyleSheet(
            "background-color: #273043; color: #94a3b8; font-size: 15px; font-weight: 800; "
            "padding: 3px 8px; border-radius: 4px; border: 1px solid #38455e;"
        )
        self._drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            distance = (event.pos() - self._drag_start_pos).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self.parent_card.start_drag()
                self._drag_start_pos = None
                self.setCursor(Qt.CursorShape.OpenHandCursor)
                return
        super().mouseMoveEvent(event)


class SceneCardWidget(QFrame):
    """Widget hiển thị một phân cảnh kịch bản chi tiết với header tách biệt rõ ràng và hỗ trợ kéo thả."""

    copy_prompt_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(object)
    reorder_requested = pyqtSignal(str, str)  # (source_scene_id, target_scene_id)

    def __init__(self, scene: StoryboardScene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self._can_delete = True
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("scene_card")
        self.setStyleSheet(
            """
            QFrame#scene_card {
                background-color: #141620;
                border: 1px solid #2a3142;
                border-radius: 8px;
            }
            QFrame#scene_card:hover {
                border-color: #475569;
            }
            QFrame#scene_card[isDropTarget="true"] {
                border: 2px dashed #3b82f6;
                background-color: #1e293b;
            }
            QFrame#scene_header_frame {
                background-color: #1e2434;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                border-bottom: 1px solid #2e384d;
            }
            """
        )

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # --- 1. HEADER FRAME (Phần Đầu Thẻ Tách Biệt Rõ Ràng) ---
        self.header_frame = QFrame()
        self.header_frame.setObjectName("scene_header_frame")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(10)

        # Biểu tượng kéo thả ⠿
        self.drag_handle = DragHandle(self)
        header_layout.addWidget(self.drag_handle)

        # Mã cảnh SC01, SC02...
        self.lbl_id = QLabel(self.scene.scene_id)
        self.lbl_id.setStyleSheet(
            "background-color: #0c4a6e; color: #38bdf8; font-weight: 800; font-size: 13px; "
            "padding: 4px 10px; border-radius: 6px; border: 1px solid #0284c7;"
        )
        header_layout.addWidget(self.lbl_id)

        # Tiêu đề phân đoạn có thể chỉnh sửa
        self.edit_title = QLineEdit(self.scene.title)
        self.edit_title.setPlaceholderText("Tiêu đề phân đoạn...")
        self.edit_title.setStyleSheet(
            "background-color: rgba(15, 23, 42, 0.6); border: 1px solid #334155; border-radius: 5px; "
            "padding: 4px 8px; font-size: 13px; font-weight: 700; color: #f8fafc;"
        )
        header_layout.addWidget(self.edit_title, stretch=1)

        # Thời lượng ước tính
        self.lbl_duration = QLabel(f"⏱ ~{self.scene.duration:.1f}s")
        self.lbl_duration.setStyleSheet(
            "background-color: #27272a; color: #a1a1aa; font-size: 11px; font-weight: 600; "
            "padding: 4px 8px; border-radius: 4px;"
        )
        header_layout.addWidget(self.lbl_duration)

        # Nút Xóa cảnh 🗑 (Hover-to-reveal)
        self.btn_delete = QPushButton("🗑 Xóa cảnh")
        self.btn_delete.setToolTip("Xóa phân cảnh này")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet(
            "background-color: #2a1215; color: #f87171; border: 1px solid #7f1d1d; "
            "border-radius: 4px; font-size: 11px; font-weight: 600; padding: 4px 10px;"
        )
        self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self))
        self.btn_delete.setVisible(False)
        header_layout.addWidget(self.btn_delete)

        card_layout.addWidget(self.header_frame)

        # --- 2. BODY FRAME (Nội Dung Phân Cảnh Bên Dưới) ---
        self.body_frame = QFrame()
        self.body_frame.setObjectName("scene_body_frame")
        body_layout = QVBoxLayout(self.body_frame)
        body_layout.setContentsMargins(14, 12, 14, 12)
        body_layout.setSpacing(10)

        # Voiceover section
        lbl_vo = QLabel("🎙 Lời thoại đọc thuyết minh (Voiceover):")
        lbl_vo.setStyleSheet("font-size: 12px; font-weight: 600; color: #38bdf8;")
        body_layout.addWidget(lbl_vo)

        self.txt_voiceover = QPlainTextEdit(self.scene.voiceover)
        self.txt_voiceover.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 6px; "
            "padding: 8px; color: #f8fafc; font-size: 13px; line-height: 1.4;"
        )
        self.txt_voiceover.setFixedHeight(75)
        body_layout.addWidget(self.txt_voiceover)

        # Visual prompt section
        prompt_header = QHBoxLayout()
        lbl_prompt = QLabel("🎨 Mô tả hình ảnh (Visual Prompt cho Midjourney/Flux/Veo):")
        lbl_prompt.setStyleSheet("font-size: 12px; font-weight: 600; color: #f59e0b;")
        prompt_header.addWidget(lbl_prompt, stretch=1)

        btn_copy_prompt = QPushButton("📋 Copy Prompt")
        btn_copy_prompt.setObjectName("btn_subtle")
        btn_copy_prompt.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_prompt.setStyleSheet(
            "background-color: #1e293b; color: #e2e8f0; font-size: 11px; padding: 3px 8px; border-radius: 4px;"
        )
        btn_copy_prompt.clicked.connect(self._on_copy_prompt_clicked)
        prompt_header.addWidget(btn_copy_prompt)

        body_layout.addLayout(prompt_header)

        self.txt_prompt = QPlainTextEdit(self.scene.prompt)
        self.txt_prompt.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 6px; "
            "padding: 8px; color: #94a3b8; font-size: 12px;"
        )
        self.txt_prompt.setFixedHeight(65)
        body_layout.addWidget(self.txt_prompt)

        # Footer info: SFX and Motion
        info_row = QHBoxLayout()
        lbl_sfx = QLabel(f"🎵 SFX: {self.scene.sfx}")
        lbl_sfx.setStyleSheet("font-size: 11px; color: #9ca3af; font-style: italic;")
        info_row.addWidget(lbl_sfx, stretch=1)

        lbl_motion = QLabel(f"🎥 Góc máy: {self.scene.motion_type}")
        lbl_motion.setStyleSheet("font-size: 11px; color: #a1a1aa;")
        info_row.addWidget(lbl_motion)

        body_layout.addLayout(info_row)

        card_layout.addWidget(self.body_frame)

    def start_drag(self):
        """Bắt đầu thao tác kéo thả thẻ phân cảnh với thumbnail xem trước."""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-storyboard-scene-id", self.scene.scene_id.encode("utf-8"))
        drag.setMimeData(mime_data)

        pixmap = self.grab()
        if not pixmap.isNull():
            scaled = pixmap.scaledToWidth(360, Qt.TransformationMode.SmoothTransformation)
            drag.setPixmap(scaled)
            drag.setHotSpot(QPoint(180, 20))

        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-storyboard-scene-id"):
            src_id = bytes(event.mimeData().data("application/x-storyboard-scene-id")).decode("utf-8")
            if src_id != self.lbl_id.text().strip():
                self.setProperty("isDropTarget", True)
                self.style().unpolish(self)
                self.style().polish(self)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("isDropTarget", False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event):
        self.setProperty("isDropTarget", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if event.mimeData().hasFormat("application/x-storyboard-scene-id"):
            src_id = bytes(event.mimeData().data("application/x-storyboard-scene-id")).decode("utf-8")
            target_id = self.lbl_id.text().strip()
            if src_id and target_id and src_id != target_id:
                self.reorder_requested.emit(src_id, target_id)
                event.acceptProposedAction()
                return
        event.ignore()

    def enterEvent(self, event):
        if event is not None:
            super().enterEvent(event)
        if getattr(self, "_can_delete", True):
            self.btn_delete.setVisible(True)

    def leaveEvent(self, event):
        if event is not None:
            super().leaveEvent(event)
        self.btn_delete.setVisible(False)

    def _on_copy_prompt_clicked(self):
        text = self.txt_prompt.toPlainText().strip()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.copy_prompt_requested.emit(text)

    def get_updated_scene(self) -> StoryboardScene:
        """Lấy lại dữ liệu phân cảnh sau khi người dùng có thể đã chỉnh sửa text."""
        return StoryboardScene(
            scene_id=self.lbl_id.text().strip(),
            title=self.edit_title.text().strip() or self.scene.title,
            voiceover=self.txt_voiceover.toPlainText().strip(),
            prompt=self.txt_prompt.toPlainText().strip(),
            duration=self.scene.duration,
            sfx=self.scene.sfx,
            motion_type=self.scene.motion_type,
            character=self.scene.character,
            character_info=self.scene.character_info,
        )


class StoryboardWorker(QThread):
    """Luồng nền gọi Gemini AI hoặc Fallback offline để sinh kịch bản mà không làm đơ giao diện."""
    finished = pyqtSignal(list, str)  # (scenes: List[StoryboardScene], engine_info: str)
    error = pyqtSignal(str)

    def __init__(
        self,
        topic: str,
        scene_count: int,
        duration_seconds: int,
        tone: str,
        visual_style: str,
        aspect_ratio: str,
        api_key: str = "",
        model: str = "gemini-1.5-flash",
        parent=None,
    ):
        super().__init__(parent)
        self.topic = topic
        self.scene_count = scene_count
        self.duration_seconds = duration_seconds
        self.tone = tone
        self.visual_style = visual_style
        self.aspect_ratio = aspect_ratio
        self.api_key = (api_key or "").strip()
        self.model = model or "gemini-1.5-flash"

    def run(self):
        if self.api_key:
            try:
                from app.core.gemini_client import generate_storyboard_with_gemini
                scenes = generate_storyboard_with_gemini(
                    topic=self.topic,
                    scene_count=self.scene_count,
                    duration_seconds=self.duration_seconds,
                    tone=self.tone,
                    visual_style=self.visual_style,
                    aspect_ratio=self.aspect_ratio,
                    api_key=self.api_key,
                    model=self.model,
                )
                self.finished.emit(scenes, f"gemini:{self.model}")
                return
            except Exception as e:
                # Nếu Gemini API lỗi (key sai, timeout, mất mạng...), fallback an toàn về offline
                try:
                    scenes = generate_storyboard(
                        topic=self.topic,
                        scene_count=self.scene_count,
                        tone=self.tone,
                        visual_style=self.visual_style,
                        aspect_ratio=self.aspect_ratio,
                        duration_seconds=self.duration_seconds,
                    )
                    self.finished.emit(scenes, f"fallback:{str(e)}")
                    return
                except Exception as inner_e:
                    self.error.emit(f"Lỗi tạo kịch bản: {inner_e}")
                    return

        # Không có API key -> Dùng bộ kịch bản Storytelling Offline
        try:
            scenes = generate_storyboard(
                topic=self.topic,
                scene_count=self.scene_count,
                tone=self.tone,
                visual_style=self.visual_style,
                aspect_ratio=self.aspect_ratio,
                duration_seconds=self.duration_seconds,
            )
            self.finished.emit(scenes, "offline")
        except Exception as e:
            self.error.emit(f"Lỗi tạo kịch bản: {e}")


class StoryboardDialog(QDialog):
    """Cửa sổ AI Storyboard Studio sinh kịch bản chi tiết và phân cảnh tự động."""

    send_to_tts_requested = pyqtSignal(str)          # Gửi kịch bản lời thoại sang Tab TTS
    apply_to_project_requested = pyqtSignal(str, str) # Gửi (scenes_json, full_script) sang Dự án

    def __init__(
        self,
        topic: str = "",
        duration_seconds: int = 60,
        scene_count: Optional[int] = None,
        tone: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        visual_style: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("⚡ AI Storyboard Studio - Sinh Kịch Bản & Phân Cảnh Tự Động")
        self.resize(1050, 750)
        self.setMinimumSize(850, 600)
        self.setStyleSheet("background-color: #121316; color: #e2e8f0;")

        self.initial_topic = topic.strip()
        self.duration_seconds = max(10, duration_seconds)

        # Tính target_scene_count theo duration_seconds hoặc scene_count chỉ định
        if scene_count is not None and scene_count > 0:
            self.target_scene_count = max(3, min(10, scene_count))
        else:
            if self.duration_seconds <= 35:
                self.target_scene_count = 3
            elif self.duration_seconds <= 75:
                self.target_scene_count = 5
            elif self.duration_seconds <= 150:
                self.target_scene_count = 8
            else:
                self.target_scene_count = 10

        # Mapping tone phù hợp
        if tone == "dramatic":
            self.initial_tone = "shocking"
        elif tone in TONE_PROFILES:
            self.initial_tone = tone
        else:
            self.initial_tone = "mystery"

        self.initial_aspect_ratio = aspect_ratio if aspect_ratio in ("9:16", "16:9") else "9:16"
        self.initial_visual_style = visual_style if visual_style in VISUAL_STYLES else "cinematic"

        self.current_scenes: List[StoryboardScene] = []
        self.worker: Optional[StoryboardWorker] = None

        self._build_ui()
        if self.initial_topic:
            self.txt_topic.setText(self.initial_topic)
            self.generate_storyboard()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        # 1. Header Bar
        header = QHBoxLayout()
        header.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        lbl_title = QLabel("🎬 AI Storyboard Studio")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")
        lbl_sub = QLabel(
            "Tự động viết kịch bản chi tiết, phân cảnh Hook ➔ Twist ➔ Call to Action và sinh Visual Prompt cho từng cảnh."
        )
        lbl_sub.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        header.addLayout(title_box, stretch=1)

        # AI Badge thể hiện minh bạch nguồn động lực AI
        has_gemini = bool(getattr(config, "GEMINI_API_KEY", "").strip())
        current_model = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
        self.lbl_ai_badge = QLabel()
        if has_gemini:
            self.lbl_ai_badge.setText(f"🤖 Gemini AI ({current_model})")
            self.lbl_ai_badge.setStyleSheet(
                "background-color: #064e3b; color: #34d399; border: 1px solid #059669; "
                "font-size: 11px; font-weight: 700; border-radius: 6px; padding: 5px 12px;"
            )
            self.lbl_ai_badge.setToolTip("Google Gemini AI đang sẵn sàng sinh kịch bản độc nhất 100%.")
        else:
            self.lbl_ai_badge.setText("⚡ Mẫu Offline (Chưa có Gemini Key)")
            self.lbl_ai_badge.setStyleSheet(
                "background-color: #1e293b; color: #94a3b8; border: 1px solid #475569; "
                "font-size: 11px; font-weight: 600; border-radius: 6px; padding: 5px 12px;"
            )
            self.lbl_ai_badge.setToolTip("Hệ thống dùng bộ mẫu Storytelling offline. Bạn có thể nhập Gemini Key trong Cài đặt để kích hoạt AI thật.")
        header.addWidget(self.lbl_ai_badge)

        root.addLayout(header)

        # 2. Config Toolbar
        config_frame = QFrame()
        config_frame.setStyleSheet(
            "background-color: #171821; border: 1px solid #282a36; border-radius: 8px; padding: 10px;"
        )
        cfg_layout = QVBoxLayout(config_frame)
        cfg_layout.setContentsMargins(12, 10, 12, 10)
        cfg_layout.setSpacing(10)

        # Row 1: Topic Input & Generate Button
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        lbl_t = QLabel("💡 Chủ đề / Ý tưởng:")
        lbl_t.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 13px;")
        row1.addWidget(lbl_t)

        self.txt_topic = QLineEdit()
        self.txt_topic.setPlaceholderText("Nhập chủ đề video (ví dụ: Sinh tồn tài chính, Bí mật Vatican, Trí tuệ nhân tạo...)")
        self.txt_topic.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 6px; padding: 7px 12px; color: #f8fafc; font-size: 13px;"
        )
        self.txt_topic.returnPressed.connect(self.generate_storyboard)
        row1.addWidget(self.txt_topic, stretch=1)

        self.btn_generate = QPushButton("✨ Sinh Kịch Bản Phân Cảnh")
        self.btn_generate.setObjectName("btn_primary")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setStyleSheet(
            "background-color: #2563eb; color: #ffffff; font-weight: 700; border-radius: 6px; padding: 7px 18px; font-size: 13px;"
        )
        self.btn_generate.clicked.connect(self.generate_storyboard)
        row1.addWidget(self.btn_generate)

        cfg_layout.addLayout(row1)

        # Row 2: Selectors (Scenes count, Tone, Visual Style, Aspect Ratio)
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # Scene count
        row2.addWidget(QLabel("Số phân cảnh:"))
        self.combo_scene_count = QComboBox()
        self.combo_scene_count.addItem("3 Cảnh (~30s)", 3)
        self.combo_scene_count.addItem("5 Cảnh (~60s)", 5)
        self.combo_scene_count.addItem("8 Cảnh (~120s)", 8)
        self.combo_scene_count.addItem("10 Cảnh (~180s+)", 10)
        idx_count = self.combo_scene_count.findData(self.target_scene_count)
        if idx_count != -1:
            self.combo_scene_count.setCurrentIndex(idx_count)
        else:
            self.combo_scene_count.setCurrentIndex(1)
        self.combo_scene_count.currentIndexChanged.connect(self._on_scene_count_changed)
        row2.addWidget(self.combo_scene_count)

        # Tone
        row2.addWidget(QLabel("Tông điệu:"))
        self.combo_tone = QComboBox()
        for key, p in TONE_PROFILES.items():
            self.combo_tone.addItem(p["label"], key)
        idx_tone = self.combo_tone.findData(self.initial_tone)
        if idx_tone != -1:
            self.combo_tone.setCurrentIndex(idx_tone)
        row2.addWidget(self.combo_tone)

        # Visual style
        row2.addWidget(QLabel("Phong cách ảnh:"))
        self.combo_style = QComboBox()
        self.combo_style.addItem("📸 Cinematic Realistic", "cinematic")
        self.combo_style.addItem("🎨 3D Animation (Pixar)", "3d_pixar")
        self.combo_style.addItem("🖌️ Anime & Manga Art", "anime")
        self.combo_style.addItem("📜 Vintage Historical", "vintage")
        self.combo_style.addItem("🌆 Cyberpunk Sci-Fi", "cyberpunk")
        idx_style = self.combo_style.findData(self.initial_visual_style)
        if idx_style != -1:
            self.combo_style.setCurrentIndex(idx_style)
        row2.addWidget(self.combo_style)

        # Aspect ratio
        row2.addWidget(QLabel("Tỉ lệ:"))
        self.combo_aspect = QComboBox()
        self.combo_aspect.addItem("📱 Dọc 9:16 (Shorts/TikTok)", "9:16")
        self.combo_aspect.addItem("🖥️ Ngang 16:9 (YouTube)", "16:9")
        idx_aspect = self.combo_aspect.findData(self.initial_aspect_ratio)
        if idx_aspect != -1:
            self.combo_aspect.setCurrentIndex(idx_aspect)
        row2.addWidget(self.combo_aspect)

        row2.addStretch()
        cfg_layout.addLayout(row2)

        root.addWidget(config_frame)

        # 3. Main Scenes Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 4, 10, 4)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        root.addWidget(self.scroll_area, stretch=1)

        # 4. Footer Action Toolbar
        footer = QHBoxLayout()
        footer.setSpacing(10)

        self.lbl_stats = QLabel("Chưa có kịch bản")
        self.lbl_stats.setStyleSheet("font-size: 12px; color: #94a3b8; font-weight: 500;")
        footer.addWidget(self.lbl_stats, stretch=1)

        # Copy Full Script
        self.btn_copy_script = QPushButton("📋 Copy Lời Thoại")
        self.btn_copy_script.setObjectName("btn_subtle")
        self.btn_copy_script.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_script.clicked.connect(self._on_copy_script_clicked)
        footer.addWidget(self.btn_copy_script)

        # Copy scenes.json
        self.btn_copy_json = QPushButton("📋 Copy scenes.json")
        self.btn_copy_json.setObjectName("btn_subtle")
        self.btn_copy_json.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_json.clicked.connect(self._on_copy_json_clicked)
        footer.addWidget(self.btn_copy_json)

        # Send to TTS Tab
        self.btn_send_tts = QPushButton("🎙 Gửi sang Tab TTS")
        self.btn_send_tts.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_tts.setStyleSheet(
            "background-color: #10b981; color: #ffffff; font-weight: 600; padding: 6px 14px; border-radius: 6px;"
        )
        self.btn_send_tts.clicked.connect(self._on_send_to_tts_clicked)
        footer.addWidget(self.btn_send_tts)

        # Apply to Project
        self.btn_apply_project = QPushButton("📁 Nạp vào Dự Án")
        self.btn_apply_project.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply_project.setStyleSheet(
            "background-color: #3b82f6; color: #ffffff; font-weight: 600; padding: 6px 14px; border-radius: 6px;"
        )
        self.btn_apply_project.clicked.connect(self._on_apply_to_project_clicked)
        footer.addWidget(self.btn_apply_project)

        # Close
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        footer.addWidget(btn_close)

        root.addLayout(footer)

    def _on_scene_count_changed(self):
        count = self.combo_scene_count.currentData() or 5
        duration_map = {3: 30, 5: 60, 8: 120, 10: 180}
        self.duration_seconds = duration_map.get(count, 60)

    def generate_storyboard(self):
        """Kích hoạt sinh kịch bản phân cảnh qua StoryboardWorker (Gemini AI hoặc Offline)."""
        topic = self.txt_topic.text().strip()
        if not topic:
            QMessageBox.information(self, "Thông báo", "Vui lòng nhập chủ đề video trước khi sinh kịch bản.")
            return

        if self.worker and self.worker.isRunning():
            return

        scene_count = self.combo_scene_count.currentData() or 5
        tone = self.combo_tone.currentData() or "mystery"
        visual_style = self.combo_style.currentData() or "cinematic"
        aspect_ratio = self.combo_aspect.currentData() or "9:16"

        api_key = getattr(config, "GEMINI_API_KEY", "").strip()
        model = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("⏳ Đang viết kịch bản...")
        self.lbl_stats.setText("⏳ Đang phân tích chủ đề và phân cảnh kịch bản...")
        QApplication.processEvents()

        self.worker = StoryboardWorker(
            topic=topic,
            scene_count=scene_count,
            duration_seconds=self.duration_seconds,
            tone=tone,
            visual_style=visual_style,
            aspect_ratio=aspect_ratio,
            api_key=api_key,
            model=model,
            parent=self,
        )
        self.worker.finished.connect(self._on_storyboard_worker_finished)
        self.worker.error.connect(self._on_storyboard_worker_error)
        self.worker.start()

    def _on_storyboard_worker_finished(self, scenes: List[StoryboardScene], engine_info: str):
        self.current_scenes = scenes
        self._render_scene_cards()
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("✨ Sinh Kịch Bản Phân Cảnh")

        total_words = sum(s.word_count for s in scenes)
        total_duration = sum(s.duration for s in scenes)

        if engine_info.startswith("gemini:"):
            model_used = engine_info.split(":", 1)[1]
            self.lbl_stats.setText(
                f"🤖 Sinh bằng Gemini AI ({model_used}) | {len(scenes)} cảnh | 📝 ~{total_words} từ | ⏱ ~{total_duration:.0f}s"
            )
        elif engine_info.startswith("fallback:"):
            err_msg = engine_info.split(":", 1)[1]
            self.lbl_stats.setText(
                f"⚠️ Gemini lỗi ({err_msg[:35]}...), chuyển Mẫu Offline | {len(scenes)} cảnh | ⏱ ~{total_duration:.0f}s"
            )
        else:
            self.lbl_stats.setText(
                f"⚡ Sinh bằng Mẫu Offline | {len(scenes)} cảnh | 📝 ~{total_words} từ | ⏱ ~{total_duration:.0f}s"
            )

    def _on_storyboard_worker_error(self, err_msg: str):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("✨ Sinh Kịch Bản Phân Cảnh")
        self.lbl_stats.setText(f"❌ {err_msg}")
        QMessageBox.warning(self, "Lỗi sinh kịch bản", err_msg)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)
        super().closeEvent(event)

    def _render_scene_cards(self):
        """Vẽ lại các thẻ cảnh lên giao diện và cấu hình nút di chuyển, xóa, thêm cảnh."""
        # Dọn sạch các widget cũ trong layout
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_words = 0
        total_duration = 0.0
        total_count = len(self.current_scenes)

        for idx, sc in enumerate(self.current_scenes, start=1):
            sc.scene_id = f"SC{idx:02d}"
            card = SceneCardWidget(sc, parent=self)
            card.copy_prompt_requested.connect(self._on_prompt_copied)
            card.delete_requested.connect(self._on_delete_scene)
            card.reorder_requested.connect(self._on_reorder_scenes)

            # Cấu hình quyền xóa: không cho xóa nếu kịch bản chỉ có 1 cảnh
            card._can_delete = (total_count > 1)
            card.btn_delete.setEnabled(total_count > 1)

            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            total_words += sc.word_count
            total_duration += sc.duration

        # Thêm nút ➕ Thêm Phân Cảnh Mới vào cuối danh sách các card
        if not hasattr(self, "btn_add_scene") or self.btn_add_scene is None:
            self.btn_add_scene = QPushButton("➕ Thêm Phân Cảnh Mới")
            self.btn_add_scene.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_add_scene.setStyleSheet(
                "background-color: #181b26; color: #60a5fa; border: 1px dashed #3b82f6; "
                "border-radius: 8px; padding: 12px; font-size: 13px; font-weight: 700;"
            )
            self.btn_add_scene.clicked.connect(self._on_add_scene_clicked)

        self.cards_layout.insertWidget(self.cards_layout.count() - 1, self.btn_add_scene)

        self.lbl_stats.setText(
            f"🎬 Đã sinh {total_count} phân cảnh | 📝 ~{total_words} từ | ⏱ Tổng thời lượng: ~{total_duration:.0f}s"
        )

    def _on_reorder_scenes(self, src_id: str, target_id: str):
        """Hoán đổi / Di chuyển phân cảnh từ vị trí src_id sang vị trí target_id (Kéo thả)."""
        scenes = self.get_latest_scenes()
        src_idx = next((i for i, s in enumerate(scenes) if s.scene_id == src_id), -1)
        dst_idx = next((i for i, s in enumerate(scenes) if s.scene_id == target_id), -1)

        if src_idx != -1 and dst_idx != -1 and src_idx != dst_idx:
            moving_scene = scenes.pop(src_idx)
            scenes.insert(dst_idx, moving_scene)

            for idx, sc in enumerate(scenes, start=1):
                sc.scene_id = f"SC{idx:02d}"

            self.current_scenes = scenes
            self._render_scene_cards()
            self.lbl_stats.setText(f"✓ Đã đổi thứ tự phân cảnh: chuyển {src_id} đến {target_id}!")

    def _on_prompt_copied(self, prompt: str):
        self.lbl_stats.setText("✅ Đã sao chép Visual Prompt vào bộ nhớ tạm!")

    def _on_delete_scene(self, card_widget: SceneCardWidget):
        """Xóa phân cảnh được chỉ định và tự động đánh số lại ID."""
        scenes = self.get_latest_scenes()
        if len(scenes) <= 1:
            QMessageBox.warning(self, "Không thể xóa", "Kịch bản cần có tối thiểu 1 phân cảnh!")
            return

        target_idx = -1
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() == card_widget:
                target_idx = i
                break

        if target_idx != -1 and target_idx < len(scenes):
            deleted_id = scenes[target_idx].scene_id
            del scenes[target_idx]
            for i, sc in enumerate(scenes, start=1):
                sc.scene_id = f"SC{i:02d}"
            self.current_scenes = scenes
            self._render_scene_cards()
            self.lbl_stats.setText(f"✓ Đã xóa {deleted_id}! Kịch bản còn lại {len(scenes)} phân cảnh.")

    def _on_move_up_scene(self, card_widget: SceneCardWidget):
        """Đổi vị trí cảnh hiện tại lên trên 1 bậc và đánh số lại ID."""
        scenes = self.get_latest_scenes()
        target_idx = -1
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() == card_widget:
                target_idx = i
                break

        if target_idx > 0 and target_idx < len(scenes):
            scenes[target_idx - 1], scenes[target_idx] = scenes[target_idx], scenes[target_idx - 1]
            for i, sc in enumerate(scenes, start=1):
                sc.scene_id = f"SC{i:02d}"
            self.current_scenes = scenes
            self._render_scene_cards()
            self.lbl_stats.setText(f"✓ Đã di chuyển cảnh lên vị trí SC{target_idx:02d}!")

    def _on_move_down_scene(self, card_widget: SceneCardWidget):
        """Đổi vị trí cảnh hiện tại xuống dưới 1 bậc và đánh số lại ID."""
        scenes = self.get_latest_scenes()
        target_idx = -1
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() == card_widget:
                target_idx = i
                break

        if target_idx != -1 and target_idx < len(scenes) - 1:
            scenes[target_idx], scenes[target_idx + 1] = scenes[target_idx + 1], scenes[target_idx]
            for i, sc in enumerate(scenes, start=1):
                sc.scene_id = f"SC{i:02d}"
            self.current_scenes = scenes
            self._render_scene_cards()
            self.lbl_stats.setText(f"✓ Đã di chuyển cảnh xuống vị trí SC{target_idx + 2:02d}!")

    def _on_add_scene_clicked(self):
        """Thêm phân cảnh mới vào cuối kịch bản."""
        scenes = self.get_latest_scenes()
        if len(scenes) >= 30:
            QMessageBox.information(self, "Giới hạn phân cảnh", "Một video ngắn tối đa nên có 30 phân cảnh.")
            return

        next_idx = len(scenes) + 1
        aspect = self.combo_aspect.currentData() or "9:16"
        style = self.combo_style.currentData() or "cinematic"
        tone = self.combo_tone.currentData() or "mystery"
        tone_profile = TONE_PROFILES.get(tone, TONE_PROFILES["mystery"])

        new_scene = StoryboardScene(
            scene_id=f"SC{next_idx:02d}",
            title=f"Phân cảnh bổ sung {next_idx}",
            voiceover="Nhập lời thoại đọc thuyết minh cho phân cảnh mới này...",
            prompt=f"Detailed cinematic view, {style}, --ar {aspect}",
            duration=6.0,
            sfx=tone_profile.get("sfx", "Âm thanh tự nhiên"),
            motion_type=tone_profile.get("motion", "zoom_in"),
        )
        scenes.append(new_scene)
        self.current_scenes = scenes
        self._render_scene_cards()
        self.lbl_stats.setText(f"✓ Đã thêm phân cảnh mới (SC{next_idx:02d})! Tổng cộng: {len(scenes)} cảnh.")

    def get_latest_scenes(self) -> List[StoryboardScene]:
        """Thu thập danh sách phân cảnh cập nhật từ các card widget."""
        scenes = []
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and isinstance(item.widget(), SceneCardWidget):
                scenes.append(item.widget().get_updated_scene())
        return scenes or self.current_scenes

    def _on_copy_script_clicked(self):
        scenes = self.get_latest_scenes()
        if not scenes:
            return
        script = export_storyboard_to_full_script(scenes)
        QApplication.clipboard().setText(script)
        self.lbl_stats.setText("✅ Đã sao chép toàn bộ lời thoại thuyết minh vào clipboard!")

    def _on_copy_json_clicked(self):
        scenes = self.get_latest_scenes()
        if not scenes:
            return
        scenes_json = export_storyboard_to_scenes_json(scenes)
        QApplication.clipboard().setText(scenes_json)
        self.lbl_stats.setText("✅ Đã sao chép định dạng scenes.json vào clipboard!")

    def _on_send_to_tts_clicked(self):
        scenes = self.get_latest_scenes()
        if not scenes:
            return
        script = export_storyboard_to_full_script(scenes)
        if script:
            QApplication.clipboard().setText(script)
        self.send_to_tts_requested.emit(script)
        self.lbl_stats.setText("✅ Đã gửi kịch bản lời thoại sang Tab TTS!")
        self.accept()

    def _on_apply_to_project_clicked(self):
        scenes = self.get_latest_scenes()
        if not scenes:
            return
        scenes_json = export_storyboard_to_scenes_json(scenes)
        script = export_storyboard_to_full_script(scenes)
        self.apply_to_project_requested.emit(scenes_json, script)
        self.lbl_stats.setText("✅ Đã gửi phân cảnh sang Dự án video!")
        self.accept()

    def closeEvent(self, event):
        if self.worker:
            try:
                self.worker.finished.disconnect()
                self.worker.error.disconnect()
            except Exception:
                pass
            if self.worker.isRunning():
                self.worker.wait(1000)
        super().closeEvent(event)
