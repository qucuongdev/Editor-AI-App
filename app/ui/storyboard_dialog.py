#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storyboard_dialog.py: Giao diện AI Storyboard Studio cho phép sinh kịch bản chi tiết,
tự động phân cảnh, hiển thị lời thoại và visual prompt, và gửi trực tiếp sang TTS hoặc Dự án video.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QWidget, QFrame,
    QPlainTextEdit, QMessageBox, QFileDialog, QApplication
)

from app.core.storyboard_generator import (
    generate_storyboard,
    export_storyboard_to_scenes_json,
    export_storyboard_to_full_script,
    export_storyboard_to_markdown,
    StoryboardScene,
    VISUAL_STYLES,
    TONE_PROFILES,
)


class SceneCardWidget(QFrame):
    """Widget hiển thị một phân cảnh kịch bản chi tiết."""

    copy_prompt_requested = pyqtSignal(str)

    def __init__(self, scene: StoryboardScene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            SceneCardWidget {
                background-color: #1a1b23;
                border: 1px solid #2d303e;
                border-radius: 8px;
                padding: 10px;
            }
            SceneCardWidget:hover {
                border-color: #3b82f6;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header row: Scene ID, Title, Duration badge
        header = QHBoxLayout()
        header.setSpacing(10)

        lbl_id = QLabel(self.scene.scene_id)
        lbl_id.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; font-weight: 800; font-size: 13px; "
            "padding: 4px 10px; border-radius: 6px; border: 1px solid #0284c7;"
        )
        header.addWidget(lbl_id)

        lbl_title = QLabel(self.scene.title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc;")
        header.addWidget(lbl_title, stretch=1)

        lbl_duration = QLabel(f"⏱ ~{self.scene.duration:.1f}s")
        lbl_duration.setStyleSheet(
            "background-color: #27272a; color: #a1a1aa; font-size: 11px; font-weight: 600; "
            "padding: 3px 8px; border-radius: 4px;"
        )
        header.addWidget(lbl_duration)

        layout.addLayout(header)

        # Voiceover section
        lbl_vo = QLabel("🎙 Lời thoại đọc thuyết minh (Voiceover):")
        lbl_vo.setStyleSheet("font-size: 12px; font-weight: 600; color: #38bdf8;")
        layout.addWidget(lbl_vo)

        self.txt_voiceover = QPlainTextEdit(self.scene.voiceover)
        self.txt_voiceover.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 6px; "
            "padding: 8px; color: #f8fafc; font-size: 13px; line-height: 1.4;"
        )
        self.txt_voiceover.setFixedHeight(75)
        layout.addWidget(self.txt_voiceover)

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

        layout.addLayout(prompt_header)

        self.txt_prompt = QPlainTextEdit(self.scene.prompt)
        self.txt_prompt.setStyleSheet(
            "background-color: #121316; border: 1px solid #374151; border-radius: 6px; "
            "padding: 8px; color: #94a3b8; font-size: 12px;"
        )
        self.txt_prompt.setFixedHeight(65)
        layout.addWidget(self.txt_prompt)

        # Footer info: SFX and Motion
        info_row = QHBoxLayout()
        lbl_sfx = QLabel(f"🎵 SFX: {self.scene.sfx}")
        lbl_sfx.setStyleSheet("font-size: 11px; color: #9ca3af; font-style: italic;")
        info_row.addWidget(lbl_sfx, stretch=1)

        lbl_motion = QLabel(f"🎥 Góc máy: {self.scene.motion_type}")
        lbl_motion.setStyleSheet("font-size: 11px; color: #a1a1aa;")
        info_row.addWidget(lbl_motion)

        layout.addLayout(info_row)

    def _on_copy_prompt_clicked(self):
        text = self.txt_prompt.toPlainText().strip()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.copy_prompt_requested.emit(text)

    def get_updated_scene(self) -> StoryboardScene:
        """Lấy lại dữ liệu phân cảnh sau khi người dùng có thể đã chỉnh sửa text."""
        return StoryboardScene(
            scene_id=self.scene.scene_id,
            title=self.scene.title,
            voiceover=self.txt_voiceover.toPlainText().strip(),
            prompt=self.txt_prompt.toPlainText().strip(),
            duration=self.scene.duration,
            sfx=self.scene.sfx,
            motion_type=self.scene.motion_type,
            character=self.scene.character,
            character_info=self.scene.character_info,
        )


class StoryboardDialog(QDialog):
    """Cửa sổ AI Storyboard Studio sinh kịch bản chi tiết và phân cảnh tự động."""

    send_to_tts_requested = pyqtSignal(str)          # Gửi kịch bản lời thoại sang Tab TTS
    apply_to_project_requested = pyqtSignal(str, str) # Gửi (scenes_json, full_script) sang Dự án

    def __init__(self, topic: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚡ AI Storyboard Studio - Sinh Kịch Bản & Phân Cảnh Tự Động")
        self.resize(1050, 750)
        self.setMinimumSize(850, 600)
        self.setStyleSheet("background-color: #121316; color: #e2e8f0;")

        self.initial_topic = topic.strip()
        self.current_scenes: List[StoryboardScene] = []

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
        self.combo_scene_count.addItem("3 Cảnh (~15s-20s)", 3)
        self.combo_scene_count.addItem("5 Cảnh (~30s-45s)", 5)
        self.combo_scene_count.addItem("8 Cảnh (~60s)", 8)
        self.combo_scene_count.addItem("10 Cảnh (~90s-120s)", 10)
        self.combo_scene_count.setCurrentIndex(1)  # Default 5 scenes
        row2.addWidget(self.combo_scene_count)

        # Tone
        row2.addWidget(QLabel("Tông điệu:"))
        self.combo_tone = QComboBox()
        for key, p in TONE_PROFILES.items():
            self.combo_tone.addItem(p["label"], key)
        row2.addWidget(self.combo_tone)

        # Visual style
        row2.addWidget(QLabel("Phong cách ảnh:"))
        self.combo_style = QComboBox()
        self.combo_style.addItem("📸 Cinematic Realistic", "cinematic")
        self.combo_style.addItem("🎨 3D Animation (Pixar)", "3d_pixar")
        self.combo_style.addItem("🖌️ Anime & Manga Art", "anime")
        self.combo_style.addItem("📜 Vintage Historical", "vintage")
        self.combo_style.addItem("🌆 Cyberpunk Sci-Fi", "cyberpunk")
        row2.addWidget(self.combo_style)

        # Aspect ratio
        row2.addWidget(QLabel("Tỉ lệ:"))
        self.combo_aspect = QComboBox()
        self.combo_aspect.addItem("📱 Dọc 9:16 (Shorts/TikTok)", "9:16")
        self.combo_aspect.addItem("🖥️ Ngang 16:9 (YouTube)", "16:9")
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

    def generate_storyboard(self):
        """Kích hoạt sinh kịch bản phân cảnh từ dữ liệu cấu hình."""
        topic = self.txt_topic.text().strip()
        if not topic:
            QMessageBox.information(self, "Thông báo", "Vui lòng nhập chủ đề video trước khi sinh kịch bản.")
            return

        scene_count = self.combo_scene_count.currentData() or 5
        tone = self.combo_tone.currentData() or "mystery"
        visual_style = self.combo_style.currentData() or "cinematic"
        aspect_ratio = self.combo_aspect.currentData() or "9:16"

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("⏳ Đang viết kịch bản...")
        QApplication.processEvents()

        try:
            self.current_scenes = generate_storyboard(
                topic=topic,
                scene_count=scene_count,
                tone=tone,
                visual_style=visual_style,
                aspect_ratio=aspect_ratio,
            )
            self._render_scene_cards()
        finally:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("✨ Sinh Kịch Bản Phân Cảnh")

    def _render_scene_cards(self):
        """Vẽ lại các thẻ cảnh lên giao diện."""
        # Xóa các widget cũ trong layout
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_words = 0
        total_duration = 0.0

        for sc in self.current_scenes:
            card = SceneCardWidget(sc)
            card.copy_prompt_requested.connect(self._on_prompt_copied)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            total_words += sc.word_count
            total_duration += sc.duration

        self.lbl_stats.setText(
            f"🎬 Đã sinh {len(self.current_scenes)} phân cảnh | 📝 ~{total_words} từ | ⏱ Tổng thời lượng: ~{total_duration:.0f}s"
        )

    def _on_prompt_copied(self, prompt: str):
        self.lbl_stats.setText("✅ Đã sao chép Visual Prompt vào bộ nhớ tạm!")

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
