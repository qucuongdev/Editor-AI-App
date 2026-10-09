import os
import sys
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

class VoiceCloningWorker(QThread):
    """
    Thực hiện 2 chế độ:
    - Voice Blending: Trộn 2 file .pt
    - Zero-Shot Cloning: Sinh file .pt từ audio (dùng inno-kokoro)
    """
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    task_finished = pyqtSignal(bool, str, str)  # success, output_path, message

    def __init__(self, **kwargs):
        super().__init__()
        self.mode = kwargs.get("mode", "blend")
        self.voice_name = kwargs.get("voice_name")
        self.output_dir = kwargs.get("output_dir")
        
        # Zero-shot kwargs
        self.audio_path = kwargs.get("audio_path")
        
        # Blend kwargs
        self.voice1_path = kwargs.get("voice1_path")
        self.voice2_path = kwargs.get("voice2_path")
        self.weight = kwargs.get("weight", 0.5)
        
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if self.mode == "zero_shot":
            self.run_zero_shot()
        else:
            self.run_blending()

    def run_zero_shot(self):
        self.status_updated.emit("Đang nạp thư viện inno-kokoro...")
        self.progress_updated.emit(10)
        
        try:
            import torch
            from inno_kokoro.enroll import Tuner, enroll, read
        except ImportError:
            self.task_finished.emit(False, "", "Lỗi: Không tìm thấy thư viện 'inno-kokoro'. Vui lòng chạy lệnh: pip install inno-kokoro (cần tải khoảng 2GB model).")
            return

        if self._is_cancelled: return

        self.status_updated.emit("Đang khởi tạo mô hình trích xuất (Tuner)...")
        self.progress_updated.emit(30)
        
        try:
            tuner = Tuner()
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi khởi tạo mô hình Inno-Kokoro: {e}")
            return
            
        if self._is_cancelled: return
        
        self.status_updated.emit(f"Đang phân tích file audio {Path(self.audio_path).name}...")
        self.progress_updated.emit(60)

        try:
            pack, _ = enroll(*read(self.audio_path), tuner)
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi trong quá trình trích xuất: {e}")
            return

        if self._is_cancelled: return
        
        self.status_updated.emit("Đang xuất file tensor (.pt)...")
        self.progress_updated.emit(90)
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if not self.voice_name.endswith('.pt'):
                self.voice_name += '.pt'
            output_file = self.output_dir / self.voice_name
            
            torch.save(pack, output_file)

            self.progress_updated.emit(100)
            self.status_updated.emit("Hoàn tất!")
            self.task_finished.emit(True, str(output_file), "Đã tạo giọng thành công (Zero-Shot)!")
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi lưu file: {str(e)}")

    def run_blending(self):
        self.status_updated.emit("Đang nạp thư viện PyTorch...")
        self.progress_updated.emit(10)
        
        try:
            import torch
        except ImportError:
            self.task_finished.emit(False, "", "Lỗi: Không tìm thấy thư viện 'torch'. Vui lòng cài đặt PyTorch (pip install torch) để dùng tính năng Voice Blending.")
            return

        if self._is_cancelled:
            self.task_finished.emit(False, "", "Đã hủy tác vụ.")
            return

        self.status_updated.emit(f"Đang đọc {Path(self.voice1_path).name}...")
        self.progress_updated.emit(30)
        
        try:
            v1_tensor = torch.load(self.voice1_path, map_location='cpu', weights_only=True)
            if isinstance(v1_tensor, dict):
                v1_tensor = v1_tensor.get('tensor', v1_tensor)
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi đọc Giọng 1: {e}")
            return

        if self._is_cancelled: return

        self.status_updated.emit(f"Đang đọc {Path(self.voice2_path).name}...")
        self.progress_updated.emit(50)
        
        try:
            v2_tensor = torch.load(self.voice2_path, map_location='cpu', weights_only=True)
            if isinstance(v2_tensor, dict):
                v2_tensor = v2_tensor.get('tensor', v2_tensor)
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi đọc Giọng 2: {e}")
            return

        if self._is_cancelled: return

        self.status_updated.emit("Đang tiến hành trộn giọng (Voice Blending)...")
        self.progress_updated.emit(70)
        
        try:
            if v1_tensor.shape != v2_tensor.shape:
                self.task_finished.emit(False, "", f"Lỗi: Kích thước tensor không khớp ({v1_tensor.shape} khác {v2_tensor.shape})")
                return
                
            blended_tensor = (v1_tensor * self.weight) + (v2_tensor * (1.0 - self.weight))
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi khi trộn tensor: {e}")
            return

        if self._is_cancelled: return

        self.status_updated.emit("Đang lưu giọng mới...")
        self.progress_updated.emit(90)
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if not self.voice_name.endswith('.pt'):
                self.voice_name += '.pt'
            output_file = self.output_dir / self.voice_name
            
            torch.save(blended_tensor, output_file)

            self.progress_updated.emit(100)
            self.status_updated.emit("Hoàn tất!")
            self.task_finished.emit(True, str(output_file), "Đã tạo giọng thành công (Blending)!")
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi lưu file: {str(e)}")
