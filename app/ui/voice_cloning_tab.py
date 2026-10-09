import os
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QMessageBox, QProgressBar, QFrame, QSizePolicy,
    QComboBox, QSlider, QRadioButton, QButtonGroup
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
            "<b>Tạo giọng nói mới cho Kokoro (.pt)</b><br>"
            "Bạn có 2 lựa chọn: <b>Zero-shot Cloning</b> (trích xuất từ 1 đoạn âm thanh mẫu 3-10 giây) "
            "hoặc <b>Voice Blending</b> (trộn 2 giọng có sẵn). <br>"
            "<i>Lưu ý: Zero-shot Cloning yêu cầu tải thêm thư viện inno-kokoro (khoảng 2GB).</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(info_label)

        # Lựa chọn chế độ
        mode_layout = QHBoxLayout()
        self.rb_zero_shot = QRadioButton("Zero-shot Cloning (Từ File Audio)")
        self.rb_blend = QRadioButton("Voice Blending (Trộn 2 giọng có sẵn)")
        self.rb_zero_shot.setChecked(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_zero_shot)
        self.mode_group.addButton(self.rb_blend)
        mode_layout.addWidget(self.rb_zero_shot)
        mode_layout.addWidget(self.rb_blend)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Panel nhập liệu
        panel = QFrame()
        panel.setProperty("class", "panel")
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(15, 15, 15, 15)
        p_layout.setSpacing(15)

        # WIDGETS CHO ZERO-SHOT
        self.w_zero_shot = QWidget()
        zs_layout = QVBoxLayout(self.w_zero_shot)
        zs_layout.setContentsMargins(0, 0, 0, 0)
        
        row_file = QHBoxLayout()
        lbl_file = QLabel("File âm thanh (.wav, .mp3):")
        lbl_file.setFixedWidth(150)
        self.txt_file = QLineEdit()
        self.txt_file.setReadOnly(True)
        self.txt_file.setPlaceholderText("Chọn file audio 3-30s...")
        btn_browse = QPushButton("Chọn File")
        btn_browse.setObjectName("btn_secondary")
        btn_browse.clicked.connect(self.browse_audio_file)
        
        row_file.addWidget(lbl_file)
        row_file.addWidget(self.txt_file)
        row_file.addWidget(btn_browse)
        zs_layout.addLayout(row_file)
        p_layout.addWidget(self.w_zero_shot)

        # WIDGETS CHO BLENDING
        self.w_blend = QWidget()
        b_layout = QVBoxLayout(self.w_blend)
        b_layout.setContentsMargins(0, 0, 0, 0)
        
        row_voice1 = QHBoxLayout()
        lbl_v1 = QLabel("Chọn Giọng 1:")
        lbl_v1.setFixedWidth(150)
        self.cbo_voice1 = QComboBox()
        row_voice1.addWidget(lbl_v1)
        row_voice1.addWidget(self.cbo_voice1)
        b_layout.addLayout(row_voice1)

        row_voice2 = QHBoxLayout()
        lbl_v2 = QLabel("Chọn Giọng 2:")
        lbl_v2.setFixedWidth(150)
        self.cbo_voice2 = QComboBox()
        row_voice2.addWidget(lbl_v2)
        row_voice2.addWidget(self.cbo_voice2)
        b_layout.addLayout(row_voice2)

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
        b_layout.addLayout(row_slider)
        p_layout.addWidget(self.w_blend)
        
        self.w_blend.setVisible(False)

        # Tên giọng mới (dùng chung)
        row_name = QHBoxLayout()
        lbl_name = QLabel("Tên giọng mới (.pt):")
        lbl_name.setFixedWidth(150)
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("VD: vi_giong_cua_toi")
        row_name.addWidget(lbl_name)
        row_name.addWidget(self.txt_name)
        p_layout.addLayout(row_name)

        layout.addWidget(panel)

        self.rb_zero_shot.toggled.connect(lambda checked: self.w_zero_shot.setVisible(checked))
        self.rb_blend.toggled.connect(lambda checked: self.w_blend.setVisible(checked))

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

    def browse_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file âm thanh", "", "Audio Files (*.wav *.mp3 *.m4a *.flac)"
        )
        if file_path:
            self.txt_file.setText(file_path)
            if not self.txt_name.text():
                base_name = Path(file_path).stem
                clean_name = "".join(c if c.isalnum() else "_" for c in base_name).strip("_")
                self.txt_name.setText(f"vi_clone_{clean_name}")

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
        voice_name = self.txt_name.text().strip()
        if not voice_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên cho giọng nói mới.")
            return

        voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "voices"
        
        # Lấy thông số tuỳ theo chế độ
        mode = "zero_shot" if self.rb_zero_shot.isChecked() else "blend"
        kwargs = {"mode": mode, "voice_name": voice_name}
        
        if mode == "zero_shot":
            audio_path = self.txt_file.text().strip()
            if not audio_path or not os.path.exists(audio_path):
                QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một file âm thanh hợp lệ.")
                return
            kwargs["audio_path"] = audio_path
        else:
            voice1 = self.cbo_voice1.currentText()
            voice2 = self.cbo_voice2.currentText()
            weight = self.slider_weight.value() / 100.0
            
            if not voice1 or not voice2:
                QMessageBox.warning(self, "Lỗi", "Vui lòng chọn đủ 2 giọng để trộn.")
                return
                
            if voice1 == voice2 and weight != 1.0 and weight != 0.0:
                QMessageBox.warning(self, "Lỗi", "Trộn 2 giọng giống nhau sẽ không tạo ra sự khác biệt.")
                return
                
            kwargs["voice1_path"] = str(voices_dir / voice1)
            kwargs["voice2_path"] = str(voices_dir / voice2)
            kwargs["weight"] = weight

        # Disable UI
        self.btn_clone.setVisible(False)
        self.btn_cancel.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        cloned_voices_dir = Path(config.APP_DIR) / "models" / "kokoro" / "cloned_voices"
        cloned_voices_dir.mkdir(parents=True, exist_ok=True)
        kwargs["output_dir"] = cloned_voices_dir

        self.worker = VoiceCloningWorker(**kwargs)
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
