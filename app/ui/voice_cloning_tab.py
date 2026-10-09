import os
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QMessageBox, QProgressBar, QFrame, QSizePolicy,
    QComboBox, QSlider
)
from app.core.kokoro_voice_cloner import VoiceCloningWorker
from app import config

class VoiceCloningTab(QWidget):
    voice_cloned_success = pyqtSignal(str, str)  # voice_name, voice_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("voice_cloning_tab")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Hướng dẫn
        info_label = QLabel(
            "<b>Tạo giọng nói mới (Voice Blending) cho Kokoro</b><br>"
            "Kokoro gốc không hỗ trợ tạo file .pt trực tiếp từ audio (Zero-shot cloning). "
            "Vì vậy, công cụ này sử dụng phương pháp <b>Voice Blending</b>: kết hợp 2 giọng có sẵn "
            "với tỉ lệ trộn do bạn tùy chỉnh để tạo ra một giọng đọc độc nhất!"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(info_label)

        # Panel nhập liệu
        panel = QFrame()
        panel.setProperty("class", "panel")
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(15, 15, 15, 15)
        p_layout.setSpacing(15)

        # Chọn giọng 1
        row_voice1 = QHBoxLayout()
        lbl_v1 = QLabel("Chọn Giọng 1:")
        lbl_v1.setFixedWidth(150)
        self.cbo_voice1 = QComboBox()
        row_voice1.addWidget(lbl_v1)
        row_voice1.addWidget(self.cbo_voice1)
        p_layout.addLayout(row_voice1)

        # Chọn giọng 2
        row_voice2 = QHBoxLayout()
        lbl_v2 = QLabel("Chọn Giọng 2:")
        lbl_v2.setFixedWidth(150)
        self.cbo_voice2 = QComboBox()
        row_voice2.addWidget(lbl_v2)
        row_voice2.addWidget(self.cbo_voice2)
        p_layout.addLayout(row_voice2)

        # Thanh trượt tỉ lệ trộn
        row_slider = QHBoxLayout()
        lbl_slider = QLabel("Tỉ lệ trộn (Giọng 1):")
        lbl_slider.setFixedWidth(150)
        
        self.slider_weight = QSlider(Qt.Orientation.Horizontal)
        self.slider_weight.setRange(0, 100)
        self.slider_weight.setValue(50)
        self.slider_weight.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_weight.setTickInterval(10)
        
        self.lbl_weight_val = QLabel("50%")
        self.lbl_weight_val.setFixedWidth(40)
        self.slider_weight.valueChanged.connect(lambda v: self.lbl_weight_val.setText(f"{v}%"))
        
        row_slider.addWidget(lbl_slider)
        row_slider.addWidget(self.slider_weight)
        row_slider.addWidget(self.lbl_weight_val)
        p_layout.addLayout(row_slider)

        # Tên giọng mới
        row_name = QHBoxLayout()
        lbl_name = QLabel("Tên giọng mới (.pt):")
        lbl_name.setFixedWidth(150)
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("VD: vi_blend_giong_moi")
        
        row_name.addWidget(lbl_name)
        row_name.addWidget(self.txt_name)
        p_layout.addLayout(row_name)

        layout.addWidget(panel)

        # Nút thực thi
        action_layout = QHBoxLayout()
        self.btn_clone = QPushButton("Bắt đầu Tạo Giọng")
        self.btn_clone.setObjectName("btn_primary")
        self.btn_clone.setMinimumHeight(40)
        self.btn_clone.clicked.connect(self.start_cloning)
        
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setObjectName("btn_danger")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.cancel_cloning)

        action_layout.addStretch()
        action_layout.addWidget(self.btn_clone, stretch=2)
        action_layout.addWidget(self.btn_cancel, stretch=1)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Progress & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Sẵn sàng.")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #6b7280; font-style: italic;")
        layout.addWidget(self.lbl_status)

        self.btn_save_voice = QPushButton("Lưu vào danh sách giọng chính thức")
        self.btn_save_voice.setObjectName("btn_secondary")
        self.btn_save_voice.setMinimumHeight(40)
        self.btn_save_voice.setVisible(False)
        self.btn_save_voice.clicked.connect(self.save_cloned_voice)
        layout.addWidget(self.btn_save_voice)

        layout.addStretch()
        
        self.load_available_voices()

    def load_available_voices(self):
        voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "voices"
        if voices_dir.exists():
            voices = [f.name for f in voices_dir.glob("*.pt")]
            self.cbo_voice1.addItems(voices)
            self.cbo_voice2.addItems(voices)
            
            # Select second item for voice 2 if available
            if len(voices) > 1:
                self.cbo_voice2.setCurrentIndex(1)

    def start_cloning(self):
        voice1 = self.cbo_voice1.currentText()
        voice2 = self.cbo_voice2.currentText()
        weight = self.slider_weight.value() / 100.0
        voice_name = self.txt_name.text().strip()

        if not voice1 or not voice2:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn đủ 2 giọng để trộn.")
            return
            
        if voice1 == voice2 and weight != 1.0 and weight != 0.0:
            QMessageBox.warning(self, "Lỗi", "Trộn 2 giọng giống nhau sẽ không tạo ra sự khác biệt. Hãy chọn 2 giọng khác nhau.")
            return
        
        if not voice_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên cho giọng nói mới.")
            return

        voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "voices"
        v1_path = str(voices_dir / voice1)
        v2_path = str(voices_dir / voice2)

        # Disable UI
        self.btn_clone.setVisible(False)
        self.btn_cancel.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Determine output directory (voices dir of kokoro-tts)
        try:
            _kokoro_src_path = Path(config.APP_DIR).parent / "kokoro-tts" / "src"
            import sys
            if str(_kokoro_src_path) not in sys.path:
                sys.path.insert(0, str(_kokoro_src_path))
            from kokoro_tts_local.paths import get_voices_dir
            kokoro_voices_dir = get_voices_dir()
        except ImportError:
            import os
            kokoro_voices_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "kokoro-tts-local" / "voices"

        # Clone vAo th mc nhAp (cloned_voices)
        cloned_voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices"
        cloned_voices_dir.mkdir(parents=True, exist_ok=True)

        self.worker = VoiceCloningWorker(v1_path, v2_path, weight, voice_name, cloned_voices_dir)
        self.worker.status_updated.connect(self.lbl_status.setText)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.task_finished.connect(self.on_cloning_finished)
        self.worker.start()

    def cancel_cloning(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.lbl_status.setText("Đang hủy...")
            self.btn_cancel.setEnabled(False)

    def on_cloning_finished(self, success: bool, output_path: str, msg: str):
        self.btn_clone.setVisible(True)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.setEnabled(True)
        
        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText(msg)
            QMessageBox.information(self, "Thành công", f"Đã lưu giọng mới tại:\n{output_path}")
            self.voice_cloned_success.emit(self.txt_name.text().strip(), output_path)
            # Reset UI
            self.txt_name.clear()
            self.cloned_temp_path = output_path
            self.btn_save_voice.setVisible(True)
            self.progress_bar.setVisible(False)
        else:
            self.progress_bar.setVisible(False)
            self.lbl_status.setText(msg)
            if "hủy" not in msg.lower():
                QMessageBox.critical(self, "Lỗi", msg)

    def save_cloned_voice(self):
        if not hasattr(self, 'cloned_temp_path') or not self.cloned_temp_path:
            return
            
        import shutil
        from app import config
        
        try:
            # Thu mc chInh
            main_voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "voices"
            main_voices_dir.mkdir(parents=True, exist_ok=True)
            
            src_path = Path(self.cloned_temp_path)
            dst_path = main_voices_dir / src_path.name
            
            shutil.copy2(src_path, dst_path)
            
            QMessageBox.information(self, "ThAnh cAng", f"DA lu {src_path.stem} vAo danh sAch gi?ng chInh th-c!")
            self.btn_save_voice.setVisible(False)
        except Exception as e:
            QMessageBox.critical(self, "L-i", f"KhAng th lu gi?ng: {e}")
