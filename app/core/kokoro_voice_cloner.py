import os
import sys
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

class VoiceCloningWorker(QThread):
    """
    Thực hiện Voice Blending: Trộn 2 file .pt của Kokoro để tạo ra một giọng mới.
    Đây là cách duy nhất để tạo file .pt chuẩn native cho Kokoro mà không cần train lại.
    """
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    task_finished = pyqtSignal(bool, str, str)  # success, output_path, message

    def __init__(self, voice1_path: str, voice2_path: str, weight: float, voice_name: str, output_dir: Path):
        super().__init__()
        self.voice1_path = voice1_path
        self.voice2_path = voice2_path
        self.weight = weight  # 0.0 to 1.0 (trọng số của voice1)
        self.voice_name = voice_name
        self.output_dir = output_dir
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
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
                # Kokoro voice tensors are often direct tensors, but handle if it's a dict
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
            # Chắc chắn cùng kích thước
            if v1_tensor.shape != v2_tensor.shape:
                self.task_finished.emit(False, "", f"Lỗi: Kích thước tensor không khớp ({v1_tensor.shape} khác {v2_tensor.shape})")
                return
                
            # Trộn theo trọng số (weight = tỷ lệ của giọng 1)
            blended_tensor = (v1_tensor * self.weight) + (v2_tensor * (1.0 - self.weight))
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi khi trộn tensor: {e}")
            return

        if self._is_cancelled: return

        self.status_updated.emit("Đang lưu giọng mới...")
        self.progress_updated.emit(90)
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            # Ensure name ends with .pt
            if not self.voice_name.endswith('.pt'):
                self.voice_name += '.pt'
            output_file = self.output_dir / self.voice_name
            
            torch.save(blended_tensor, output_file)

            self.progress_updated.emit(100)
            self.status_updated.emit("Hoàn tất!")
            self.task_finished.emit(True, str(output_file), "Đã tạo giọng thành công!")
        except Exception as e:
            self.task_finished.emit(False, "", f"Lỗi lưu file: {str(e)}")
