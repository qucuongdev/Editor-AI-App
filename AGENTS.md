# QUY TẮC PHÁT TRIỂN & ĐIỀU PHỐI SUBAGENT (AGENTS.md)
*Tài liệu này được Antigravity tự động nạp vào mọi phiên làm việc (session / context) mới.*

---

## 1. Cơ Chế Khôi Phục Bối Cảnh Phiên Làm Việc (Context Continuity)

Để không bao giờ bị quên tiến độ hoặc bối cảnh khi mở một hội thoại mới:
1. **Bắt đầu phiên làm việc**: Khi nhận bất kỳ yêu cầu mới nào từ người dùng, Agent **BẮT BUỘC** đọc file [`docs/WORKFLOW_LOG.md`](file:///D:/Work/Tool/Editor-AI-App/docs/WORKFLOW_LOG.md) đầu tiên để khôi phục toàn bộ ngữ cảnh, quyết định kiến trúc và các việc đang làm dở từ các phiên trước.
2. **Kết thúc phiên làm việc**: Sau khi hoàn thành yêu cầu và kiểm thử thành công, Agent **BẮT BUỘC** ghi lại tóm tắt (Ngày giờ, thay đổi, kết quả test, checklist) vào [`docs/WORKFLOW_LOG.md`](file:///D:/Work/Tool/Editor-AI-App/docs/WORKFLOW_LOG.md).

---

## 2. Chu Trình 4 Bước Phân Chia Công Việc Chặt Chẽ (Subagent QA Workflow)

Mỗi khi nhận một yêu cầu phát triển / sửa lỗi từ người dùng, Agent phải tuân thủ nghiêm ngặt chu trình 4 bước:

```
[1. Developer] ➔ [2. Unit Tester] ➔ [3. UI Tester] ➔ [4. User UAT Hand-off]
```

### Bước 1: Subagent Developer (Mã nguồn chức năng)
- Viết code đúng kiến trúc mô-đun hóa, dễ đọc, clean code.
- **Bắt buộc tương thích ngược (Backward Compatibility)**:
  - Khi sửa `app/config.py`, luôn hỗ trợ cả `config.settings.KEY` lẫn module-level `config.KEY`.
  - Mọi hàm đọc/ghi file text phải chỉ định rõ `encoding="utf-8"`.
  - Không xóa bỏ hoặc đổi tên component khi chưa cập nhật toàn bộ nơi phụ thuộc.

### Bước 2: Subagent Unit Tester (Kiểm thử logic tự động)
- Viết mới hoặc cập nhật unit test cho các hàm xử lý trong `tests/`.
- Chạy lệnh kiểm thử toàn diện:
  ```powershell
  python -m unittest discover -s tests -p "test_*.py"
  ```
- **Quy tắc chặn lỗi (Gatekeeper)**: Bắt buộc **100% test case phải PASS (0 Failures, 0 Errors)** mới được phép chuyển sang bước tiếp theo.

### Bước 3: Subagent UI Automation Tester (Kiểm thử giao diện)
- Sử dụng `PyQt6.QtTest` và chạy ở chế độ headless/offscreen (`$env:QT_QPA_PLATFORM="offscreen"`).
- Giả lập hành động người dùng: Click nút, nhập dữ liệu, kiểm tra trạng thái widget (`btn.isEnabled()`, `progress_bar.isVisible()`, `status_label.text()`).
- Đảm bảo các luồng giao diện chạy mượt mà, không đóng băng UI thread (dùng QThread cho tác vụ nặng).

### Bước 4: User Acceptance Hand-off (Bàn giao người dùng nghiệm thu)
- Báo cáo rõ ràng kết quả kiểm thử tự động của Bước 2 và Bước 3.
- Cung cấp **Checklist kịch bản kiểm thử thực tế (Manual UAT Checklist)**:
  - Lệnh khởi động app (`python start_app.py`).
  - Các bước thao tác click trực tiếp trên GUI thật để người dùng tự tay kiểm chứng.
- Đợi phản hồi / xác nhận nghiệm thu từ người dùng trước khi đóng task.

---

## 3. Kiến Trúc Cốt Lõi Dự Án
- **Framework GUI**: PyQt6, QSS theme tách biệt tại `app/assets/theme.qss`.
- **Cấu hình**: `app/config.py` quản lý qua QSettings (`AI Studio / AI Media Studio`).
- **Core Engines**:
  - TTS: Vibi API Client & Kokoro Local Engine (`app/core/kokoro_engine.py`).
  - Voice Cloning: `VoiceCloningWorker` trong `app/core/kokoro_voice_cloner.py` (hỗ trợ Blending và Zero-Shot).
  - Video Creator & Watermark Remover: Xử lý frame bằng FFmpeg & Pillow.
