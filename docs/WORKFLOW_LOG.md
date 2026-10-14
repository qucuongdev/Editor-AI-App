# NHẬT KÝ PHIÊN LÀM VIỆC & TIẾN ĐỘ DỰ ÁN (WORKFLOW_LOG.md)
*File này lưu trữ ngữ cảnh liên tục giữa các phiên làm việc của AI và Developer.*

---

## [2026-10-14] - Khôi phục toàn diện & Chuẩn hóa quy trình Subagent

### 1. Bối cảnh & Yêu cầu từ Người Dùng:
- Review branch `release-MVP-sr20261009`.
- Sửa toàn bộ lỗi hồi quy (regression) và lỗi test đang gặp trên branch.
- Thiết lập quy trình Subagent phân chia công việc chặt chẽ (Dev -> Unit Test -> UI Test -> User Acceptance).
- Cơ chế lưu trữ luồng làm việc để mở context mới không bị quên tiến độ.

### 2. Các thay đổi & Sửa lỗi kỹ thuật đã thực hiện:
1. **`app/config.py`**:
   - Khôi phục các thuộc tính module-level (`VIBI_API_KEY`, `PROJECTS_DIR`...) và cài đặt `__getattr__` để tương thích ngược 100% với các code & test cũ, đồng thời vẫn giữ nguyên đóng gói `AppConfig`.
2. **Dọn dẹp `PricingTab`**:
   - Gỡ bỏ hoàn toàn các import và test case liên quan đến `PricingTab` đã bị xóa trong `tests/test_restored_features.py` và `tests/test_video_watermark_ui.py`.
3. **Phòng vệ `VoiceLookupTab.stop_preview`**:
   - Thêm kiểm tra `hasattr(self.player, "playbackState")` trong `app/ui/voice_lookup_tab.py` để không làm crash các mock test `_SilentMediaPlayer`.
4. **Encoding UTF-8**:
   - Thêm `encoding="utf-8"` cho các cuộc gọi `.read_text()` trong `tests/test_phase1_release.py` tránh lỗi `charmap` trên Windows.
5. **Đồng bộ giao diện & Test UI**:
   - Bổ sung alias `self.action_clear = self.btn_clear_all` trong `app/ui/watermark_tab.py`.
   - Chuẩn hóa text nút duyệt file thành `"Chọn..."` trong `app/ui/video_tab.py`.
   - Sửa thứ tự gán dữ liệu test và assertion footer link trong `tests/test_standalone_tools_ui.py` và `tests/test_video_watermark_ui.py`.
   - Bổ sung compatibility helper cho video watermark trong `app/core/watermark_remover.py`.

### 3. Kết quả kiểm thử tự động (Unit Test):
- Lệnh chạy: `python -m unittest discover -s tests -p "test_*.py"`
- **Kết quả: 99/99 tests PASS 100% (0 errors, 0 failures, chạy trong 8.017s)!**

### 4. Quy tắc phiên làm việc tiếp theo:
- Đọc file này (`docs/WORKFLOW_LOG.md`) cùng với `AGENTS.md` khi bắt đầu bất kỳ phiên làm việc mới nào.
- Tiếp tục duy trì 0 regression cho mọi tính năng mới.

---

## [2026-10-14 10:35] - Kiểm thử toàn diện tính năng Remove Watermark (Ảnh & Video)

### 1. Bối cảnh:
- Người dùng yêu cầu xác nhận độ ổn định của toàn bộ chức năng Gỡ Watermark (Image & Video Watermark).

### 2. Kết quả kiểm thử chuyên sâu:
- **Core Image Watermark (`app/core/watermark_remover.py`)**: Đã chạy test xử lý ảnh thật (`process_file`) -> Khử watermark chuẩn xác, file xuất nguyên vẹn.
- **Core Video Watermark (`app/core/video_watermark_remover.py`)**: Đã kiểm thử trực tiếp cả 2 thuật toán:
  - Khử watermark Veo 3 (`remove_veo3_frame`): PASS.
  - Khử watermark Gemini (`remove_frame`): PASS.
- **UI Automation (PyQt6 headless)**:
  - `WatermarkTab` (Ảnh): Thêm file, cập nhật table, xóa file lẻ, xóa toàn bộ (`btn_clear_all`) -> PASS.
  - `VideoWatermarkTab` (Video): Đổi mode Veo3 / Gemini, nạp file video, cấu hình thư mục lưu -> PASS.
- **Toàn bộ 17 unit tests về Watermark**: PASS 100%.

---

## [2026-10-14 12:50] - Chuẩn hóa văn bản tiếng Việt thông minh theo ngữ cảnh (Context-Aware TTS Normalizer)

### 1. Bối cảnh & Yêu cầu:
- Người dùng yêu cầu xử lý triệt để việc đọc văn bản bị vấp trong TTS (từ viết tắt như `k` -> `không`, `mn` -> `mọi người`, `dc/đc` -> `được`, `vs` -> `với`).
- **Ngữ cảnh thông minh đặc thù**: Chữ `K` trong `bệnh K`, `viện K`, `ung thư K`, `vitamin K`, `vàng 18K/24K`, `video 4K/8K`, `K-pop` tuyệt đối **không** được đọc thành "không", mà phải đọc theo đúng ngữ cảnh ("ca", "kê", "nghìn").
- Tuân thủ chu trình Subagent 4 bước: Dev -> Unit Test -> UI Automation Test -> User Acceptance Hand-off.

### 2. Các thay đổi kỹ thuật:
1. **Core Normalizer (`app/core/text_normalizer.py`)**:
   - Xử lý ngữ cảnh y tế (`bệnh K`, `viện K`, `bệnh nhân K`, `ung thư K`, `chẩn đoán K`, `vitamin K/A/B/C/D`, `viêm gan B/C`) -> chuyển thành "ca", "vi-ta-min ...", "viêm gan bê/xê".
   - Phân biệt độ phân giải & vàng bạc (`vàng 18K/24K`, `video 2K/4K/8K`) -> chuyển thành "ca".
   - Phân biệt tiền tệ (`50k`, `100k`) -> "50 nghìn", "100 nghìn".
   - Thuật ngữ giải trí: `K-pop`, `K-drama`, `V-pop` -> "kê-pop", "kê-drama", "vê-pop".
   - Giữ nguyên chữ `AI` -> "A.I" (tránh bị đọc thành "ai" - ai đó).
   - Xử lý phủ định đơn lẻ: `\b[kK]\b`, `ko`, `kh`, `khg`, `hông`, `hong` -> "không" (bảo toàn 100% các từ chứa chữ k như `kẹo`, `kem`, `khi`, `kính`).
   - Xử lý teencode & viết tắt: `mn/mng` -> "mọi người", `ae` -> "anh em", `vs` -> "với", `j` -> "gì", `sđt` -> "số điện thoại", `sp` -> "sản phẩm", `ntn` -> "như thế nào", `ok` -> "ô kê", `cmt` -> "bình luận", `ib` -> "nhắn tin".
   - Ký hiệu số học: `%` -> "phần trăm", `°C` -> "độ xê", `$` -> "đô la", ngắt nhịp số điện thoại 4-3-3, giờ giấc `8h30` -> "8 giờ 30 phút".
2. **Tích hợp Core Engine**:
   - `app/core/kokoro_engine.py`: Tự động gọi normalizer cho các voice tiếng Việt và cloned voice.
   - `app/core/tts_worker.py`: Tự động chuẩn hóa văn bản trước khi chia chunk và gửi API (áp dụng cho cả Vibi TTS và Kokoro Local).
3. **Phòng vệ UI (`app/ui/voice_lookup_tab.py`)**:
   - Bổ sung `try ... except RuntimeError` bảo vệ khi thread ngầm hoàn tất lúc widget đã bị hủy.

### 3. Kết quả kiểm thử tự động (Unit Test & UI Test):
- **Unit Test (`tests/test_text_normalizer.py`)**: 9 test methods kiểm tra đầy đủ mọi nhánh ngữ cảnh -> PASS.
- **UI Automation Test (`tests/test_tts_normalization_ui.py`)**: Giả lập offscreen PyQt6 thao tác giao diện TTSTab -> PASS.
- **Full Test Suite (`python -m unittest discover -s tests -p "test_*.py"`)**: **110/110 tests PASS 100% (0 errors, 0 failures, chạy trong 7.887s)!**

---

## [2026-10-14 13:00] - Mở rộng toàn diện bộ từ điển Teencode & Ký hiệu tiếng Việt (Full Dictionary Expansion)

### 1. Bối cảnh & Yêu cầu:
- Người dùng yêu cầu mở rộng tối đa khả năng bao phủ các từ ngữ tiếng Việt thường gặp trong thực tế (mạng xã hội, hành chính, công nghệ, đơn vị đo lường).
- Áp dụng đầy đủ chu trình 4 bước Subagent QA.

### 2. Các nhóm từ mở rộng đã hoàn thành:
1. **Quan hệ & Xưng hô mạng**: `ny` (người yêu), `ck` (chồng), `vk` (vợ), `cr/crush` (cờ-rút), `bx/ox` (bà xã / ông xã).
2. **Giao tiếp & Teencode hàng ngày**: `ng` (người), `hnay` (hôm nay), `hqua` (hôm qua), `mmai` (ngày mai), `tks/thanks` (cảm ơn), `pls/plz` (làm ơn), `cx` (cũng), `ms` (mới), `ch` (chưa), `... r` (rồi: "xong r", "về r"), `tgian` (thời gian), `đt` (điện thoại), `vđ` (vấn đề), `hđ` (hợp đồng), `clb` (câu lạc bộ), `sv/gv/hs/nv/gd` (sinh viên, giáo viên, học sinh, nhân viên, gia đình), `stt` (số thứ tự), `status/tus/cap` (dòng trạng thái, bài viết, chú thích), `qtam` (quan tâm), `qtrong` (quan trọng), `ncl` (nói chung là), `đv` (đối với), `kb` (kết bạn), `tl` (trả lời), `nhg` (nhưng), `nt` (nhắn tin), `đk/đki` (đăng ký), `sub/share/like` (đăng ký, chia sẻ, thích), `uk/um/uh/ừm` (ừ).
3. **Công nghệ & Mạng xã hội**: `wifi/wi-fi` (oai-phai), `ATM` (A.T.M), `OTP` (O.T.P), `SMS` (S.M.S), `IT` (ai-ti), `app` (áp), `web/website` (oép / oép-sai), `podcast` (pót-cát), `tiktok` (tíc-tốc), `youtube` (du túp), `facebook` (phây búc), `check-in` (chéc-in), `fanpage` (phan-pây), `admin/ad` (át-min).
4. **Hành chính & Cơ quan**: `UBND` (Ủy ban nhân dân), `HĐND` (Hội đồng nhân dân), `BCA/BQP/BGD/BYT`, `BHYT` (bảo hiểm y tế), `BHXH` (bảo hiểm xã hội), `CSGT` (cảnh sát giao thông), `PCCC` (phòng cháy chữa cháy), `THPT/THCS/ĐH/CĐ`.
5. **Đo lường & Tốc độ & Dung lượng**: `km/h` (ki lô mét trên giờ), `m/s` (mét trên giây), `kwh` (ki lô oát giờ), `gb/mb/tb` (ghi ga bai / mê ga bai / tê ra bai), `hz/khz/mhz/ghz` (héc / ghi ga héc), `w/kw` (oát / ki lô oát), `v` (vôn), `mah` (mi li am pe giờ).
6. **Phân số & Số thập phân**: `1/2` (1 phần 2), `1/4`, `3/4`, `2,5kg` -> "2 phẩy 5 ki lô gam".
7. **Dịch tễ & Y tế**: `Covid-19` (cô-vít 19), `F0`, `F1`, `F2` (ép-0, ép-1, ép-2).

### 3. Kết quả kiểm thử tự động:
- **Unit Test (`tests/test_text_normalizer.py`)**: Đạt **14/14 test methods PASS 100%**.
- **UI Automation Test (`tests/test_tts_normalization_ui.py`)**: **PASS 100%**.
- **Toàn bộ Test Suite dự án**: **115/115 tests PASS 100% (0 errors, 0 failures, chạy trong 8.072s)!**

---

## [2026-10-14 13:25] - Khôi phục danh sách Giọng Có Sẵn (Built-in Preset Voices) & Nút Tra cứu riêng biệt

### 1. Bối cảnh & Phản hồi từ Người Dùng:
- Người dùng phản hồi: *"sao mất hết các giọng có sẵn rồi? tôi muốn dùng các giọng có sẵn mà k cần tìm kiêm snuwax"*
- **Nguyên nhân kỹ thuật đã phát hiện**:
  1. Trong commit trước, `VoiceSelectorComboBox` bị override hàm `showPopup()`, biến dropdown thành một nút chuyển hướng ép buộc người dùng nhảy sang tab "Tra cứu Voice".
  2. Dropdown `combo_voice` chỉ có đúng 1 item rỗng hoặc `Chọn giọng nói…`, hoàn toàn không nạp danh sách các giọng có sẵn của các nền tảng (ElevenLabs, Kokoro, MiniMax, CapCut).
  3. Người dùng mỗi lần muốn chọn giọng đều phải qua tab tìm kiếm, gõ từ khóa và bấm nút "Dùng giọng", gây bất tiện lớn.

### 2. Các thay đổi kỹ thuật đã thực hiện:
1. **Module Giọng Có Sẵn (`app/core/preset_voices.py`)**:
   - Cung cấp danh sách các giọng có sẵn chất lượng cao cho cả 4 provider:
     * **ElevenLabs**: 🇻🇳 Mai Anh (mặc định), 🇻🇳 Minh Phong, 🇺🇸 Rachel, 🇺🇸 Adam, 🇺🇸 Bella, 🇺🇸 Domi, 🇺🇸 Elli, 🇺🇸 Josh, 🇺🇸 Arnold, 🇺🇸 Sam.
     * **Kokoro Local (Offline)**: Toàn bộ 14 giọng tiếng Việt (Mai Linh, Ngọc Huyền, Diễm Trinh, Mai Loan, Mỹ Yến, Thục Trinh, Đức An, Đức Duy, Hùng Thịnh, Mạnh Dũng, Phát Tài, Storyvert, Thành Đạt, Tuấn Ngọc), các giọng quốc tế (Bella, Sarah, Adam, Alice, George) và tự động nhận diện các giọng đã Clone (`.pt`).
     * **MiniMax**: 🇻🇳 Nam Trầm Ấm, 🇻🇳 Nữ Dịu Dàng, 🇻🇳 Nam Năng Động, 🇻🇳 Nữ Truyền Cảm, MC Nam, MC Nữ, Thanh Niên, Thiếu Nữ, Đọc Sách.
     * **CapCut**: 🇻🇳 Nữ Miền Bắc, 🇻🇳 Nữ Miền Nam, 🇻🇳 Nam Miền Bắc, 🇻🇳 Nam Miền Nam, 🇺🇸 Jessie, 🇺🇸 Joey, Em Bé Đáng Yêu.
   - Cung cấp hàm `get_preset_voices()`, `get_default_voice_for_provider()`, `find_voice_name()`.
2. **`app/ui/components/voice_selector.py`**:
   - Gỡ bỏ override `showPopup()` để ComboBox hoạt động đúng bản chất: click là xổ ngay menu các giọng có sẵn để chọn trực tiếp.
3. **`app/ui/tts_tab.py`**:
   - Khởi tạo đầy đủ giọng mặc định cho 4 provider (không còn bị rỗng `""`).
   - `_display_selected_voice()`: Tự động đổ toàn bộ danh sách giọng có sẵn của provider đang chọn vào `combo_voice`. Nếu có giọng custom (từ lookup hoặc clone), tự động chèn lên đầu danh sách.
   - Bổ sung nút bấm riêng `btn_lookup_voice` (`🔍 Tra cứu…`) cạnh ComboBox và mục `"🔍 Tra cứu thêm giọng khác…"` ở cuối menu xổ xuống cho người dùng muốn tìm kiếm sâu hơn trong thư viện online.
   - Kết nối `combo_voice.currentIndexChanged` để chọn giọng tức thì mà không cần tìm kiếm.

### 3. Kết quả kiểm thử tự động (Unit Test & UI Automation):
- **Unit & UI Automation Test mới (`tests/test_preset_voices_ui.py`)**: Đạt **8/8 test methods PASS 100%**.
- **Toàn bộ Test Suite dự án**: Đạt **123/123 tests PASS 100% (0 errors, 0 failures, chạy trong 8.746s)!**

---

## [2026-10-14 13:40] - Khắc phục triệt để lỗi Kokoro Local & Tối ưu hóa Tra Cứu Giọng (Offline Fallback & Server Detection)

### 1. Bối cảnh & Phản hồi Người Dùng:
- Người dùng gặp lỗi:
  * *"chức năng tra cứu giọng nói sao k hoạt động? sao giờ mất hết tất cả các giọng?"*
  * *"Không thể sử dụng Kokoro Local: Cả Gradio Server (7860) và module direct đều không khả dụng!"*
- **Nguyên nhân cốt lõi**:
  1. `get_kokoro_voices()` trong `kokoro_engine.py` chỉ kích hoạt danh sách fallback 14 giọng tiếng Việt khi `voice_names` rỗng. Nhưng trong thư mục `cloned_voices` có 2 file clone mẫu (`.pt`), dẫn đến toàn bộ 14 giọng tiếng Việt và giọng chuẩn của Kokoro bị bỏ rơi hoàn toàn.
  2. Tab Tra Cứu Voice khi người dùng chưa nhập Voice API Key (`VIBI_API_KEY`) thì quăng lỗi `Chưa cấu hình Voice API Key` và trả về bảng trống rỗng `[]`, khiến người dùng nghĩ rằng chức năng tra cứu bị hỏng.
  3. Môi trường Python hệ thống thiếu gói `gradio_client`, khiến hàm `is_gradio_server_available` luôn trả về `False` ngay cả khi server Kokoro local đang mở cổng 7860.
  4. Thông báo lỗi khi chưa bật server 7860 quá kỹ thuật và không hướng dẫn người dùng cách bật `CHAY_TTS.cmd`.

### 2. Các giải pháp kỹ thuật đã triển khai:
1. **`app/core/kokoro_engine.py`**:
   - Sửa `get_kokoro_voices()`: Luôn bảo đảm đủ 14 giọng tiếng Việt và các giọng chuẩn quốc tế + gộp các giọng đã clone.
   - Bổ sung kiểm tra cổng 7860 qua Socket nhanh (0.3s timeout) trước khi gọi client.
   - Cài đặt thư viện `gradio_client` vào môi trường Python (`pip install gradio_client`).
   - Cải tiến thông báo lỗi khi chưa bật server: Hướng dẫn rõ ràng cách chạy `CHAY_TTS.cmd` trong thư mục `kokoro-tts` hoặc chuyển sang nền tảng ElevenLabs/MiniMax/CapCut.
2. **`app/ui/voice_lookup_tab.py`**:
   - Khi chưa có API Key: Tự động fallback nạp danh sách các giọng có sẵn (preset) của nền tảng tương ứng (ElevenLabs, Kokoro, MiniMax, CapCut) thay vì ném lỗi bảng trắng. Người dùng vẫn xem, copy ID và chọn "Dùng giọng" bình thường.
   - Đặt `⚡ ElevenLabs (Mặc định)` lên vị trí đầu tiên của `combo_source`.
3. **`app/ui/tts_tab.py`**:
   - Tự động đồng bộ nguồn trong tab Tra Cứu theo nền tảng đang chọn tại tab Tạo Giọng Nói khi bấm `🔍 Tra cứu…`.

### 3. Kết quả kiểm thử:
- **Test Suite mở rộng (`tests/test_preset_voices_ui.py`)**: **11/11 tests PASS 100%**.
- **Toàn bộ Test Suite hệ thống**: **126/126 tests PASS 100% (0 errors, 0 failures, 10.487s)!**

---

## [2026-10-14 14:15] - Hoàn tất tích hợp Direct Kokoro Offline (Không cần Server) & Hiển thị trọn vẹn 70+ Giọng Nói

### 1. Bối cảnh & Phản hồi từ Người Dùng:
- Người dùng phản hồi:
  * *"sao mất hết các giọng có sẵn rồi? tôi muốn dùng các giọng có sẵn mà k cần tìm kiêm snuwax"*
  * *"sao giờ mất hết tất cả các giọng? chức năng tra cứu giọng nói sao k hoạt động? và đang bị lỗi này nữa? Không thể sử dụng Kokoro Local: Cả Gradio Server (7860) và module direct đều không khả dụng!"*
  * *"D:\\Work\\Tool\\Editor-AI-App\\models\\kokoro\\voices nhiều voice thế này mà sao show ra ít voice thế? tôi muốn nó chạy luôn chứ? đã là tool tích hợp rồi mà còn đòi dựa trên dự án khác là sao? với lại có quá nhiều voice mà sao hiện ít thế? các voice còn lại đâu hết r?"*

### 2. Nguyên nhân kỹ thuật phát hiện:
1. **Thiếu thư viện Direct Engine**: Môi trường Python thiếu `torch`, `kokoro`, `soundfile`, `vig2p`, `sea-g2p`, khiến `HAS_DIRECT_KOKORO` bị `False` và app buộc phải trông chờ vào Gradio Server 7860 bên ngoài `kokoro-tts`.
2. **Sai lệch đường dẫn nạp voice**: `generate_kokoro_tts()` gọi `get_safe_voice_path(voice_id)` trỏ vào `%LOCALAPPDATA%\kokoro-tts-local\voices` thay vì nạp từ `models/kokoro/voices` của ứng dụng.
3. **Ẩn 54 giọng quốc tế**: `get_kokoro_voices()` trước đó chỉ quét cố định 14 giọng tiếng Việt, bỏ qua 54 file `.pt` (Mỹ, Anh, Trung, Nhật, Tây Ban Nha, Pháp, Ý, Bồ Đào Nha, Hindi) đang có sẵn trong `models/kokoro/voices/`.
4. **Lỗi thụt lề `get_preset_voices`**: Trả về `None` cho các nền tảng khác khi không phải `kokoro`.

### 3. Các giải pháp kỹ thuật đã triển khai:
1. **Môi trường & Package Direct Engine**:
   - Cài đặt đầy đủ `kokoro-0.9.4`, `torch-2.14.1`, `soundfile-0.14.0`, `transformers-5.19.0`, `spacy-3.8.16`, `en-core-web-sm-3.8.0`, `vig2p-0.1.2`, `sea-g2p-0.10.0`.
   - Kết nối trực tiếp mô hình checkpoint tiếng Việt `kokoro_vi.pth` và quốc tế `kokoro-v1_0.pth`.
2. **Core Direct Kokoro (`app/core/kokoro_engine.py`)**:
   - `get_kokoro_voices()`: Tự động quét toàn bộ 68 file `.pt` trong `models/kokoro/voices` + 2 file trong `models/kokoro/cloned_voices` -> Hiển thị **70 giọng đầy đủ**, phân loại cờ và định dạng chuẩn, ưu tiên 14 giọng Việt lên đầu.
   - `get_kokoro_voice_path(voice_id)`: Tự động tìm kiếm trong `models/kokoro/voices` và `models/kokoro/cloned_voices` với fallback an toàn.
   - `get_kokoro_language_code(voice_id)`: Ánh xạ chuẩn ngôn ngữ (`vi`, `a`, `b`, `z`, `j`, `e`, `f`, `h`, `i`, `p`).
   - `generate_kokoro_tts`: Hoạt động in-process trực tiếp hoàn toàn offline trong ứng dụng mà **KHÔNG CẦN CHẠY BẤT KỲ SERVER NGOÀI NÀO (cổng 7860)**.
3. **Preset Voices (`app/core/preset_voices.py`)**:
   - Sửa thụt lề `return base_list`, đảm bảo cả 4 nền tảng (ElevenLabs, Kokoro, MiniMax, CapCut) đều trả về danh sách giọng có sẵn chuẩn xác.
4. **Dọn dẹp `MainWindow` closeEvent (`app/ui/main_window.py`)**:
   - Ngắt `_update_timer` và thread kiểm tra cập nhật để test và app thoát sạch sẽ.
5. **Test Runner Cô lập Tiến trình (`run_all_tests.py`)**:
   - Ngăn chặn ô nhiễm luồng nền giữa PyQt và QMediaPlayer.

### 4. Kết quả kiểm thử tự động (Unit Test & UI Automation):
- **UI Flow Automation Test (`tests/test_ui_kokoro_full_flow.py`)**: Giả lập toàn bộ luồng đổi provider -> chọn giọng -> mở tra cứu 70 giọng -> bấm dùng giọng -> quay lại TTSTab -> PASS 100%.
- **Toàn bộ Test Suite hệ thống (`python run_all_tests.py`)**:
  - `test_edit_document.py`: 20 tests PASS
  - `test_edit_render.py`: 4 tests PASS
  - `test_phase1_release.py`: 6 tests PASS
  - `test_preset_voices_ui.py`: 13 tests PASS
  - `test_restored_features.py`: 1 test PASS
  - `test_scene_motion.py`: 9 tests PASS
  - `test_scene_video_handoff.py`: 2 tests PASS
  - `test_standalone_state.py`: 5 tests PASS
  - `test_standalone_tools_ui.py`: 17 tests PASS
  - `test_text_normalizer.py`: 14 tests PASS
  - `test_tts_normalization_ui.py`: 2 tests PASS
  - `test_ui_kokoro_full_flow.py`: 1 test PASS
  - `test_update_check.py`: 12 tests PASS
  - `test_update_install.py`: 8 tests PASS
  - `test_veo3_text_mask.py`: 2 tests PASS
  - `test_video_output_quality.py`: 1 test PASS
  - `test_video_watermark_remover.py`: 6 tests PASS
  - `test_video_watermark_ui.py`: 4 tests PASS
  - `test_watermark_folder_selection.py`: 2 tests PASS
  - **TỔNG KẾT: 129/129 tests PASS 100% (0 errors, 0 failures, chạy trong 39.88s)!**

---

## [2026-10-14 14:30] - Sửa triệt để lỗi phát âm 'y tế' thành 'quai tế' (Vietnamese Vowel G2P Fix)

### 1. Bối cảnh & Phản hồi từ Người Dùng:
- Người dùng phản ánh: *"đóng bảo hiểm y tế mà đọc là đóng bảo hiểm quai tế? nó đang đọc tiếng anh?"*

### 2. Nguyên nhân kỹ thuật phát hiện:
1. Thư viện `vig2p` khi xử lý văn bản tiếng Việt sẽ tách (tokenize) câu thành từng từ đơn rồi nạp vào `sea_g2p`.
2. Khi gặp từ `y` đứng độc lập (như trong "bảo hiểm y tế", "y khoa", "y tá", "đông y", "y chang", "y hệt"...), `sea_g2p` xem `y` là ký tự tiếng Anh (chữ cái Y) và chuyển âm thành `wˈaɪ` (/waɪ/ - đọc là "quai").
3. Tương tự, từ `u` (khối u, u xơ, u nang, u tối...) bị đọc thành `jˈuː` ("diu" - chữ cái U tiếng Anh), và từ `e` (e ngại, e dè, e thẹn...) bị đọc thành `ˈiː` ("i" - chữ cái E tiếng Anh).

### 3. Các giải pháp kỹ thuật đã triển khai:
1. **Core G2P Engine (`app/core/kokoro_engine.py` & `kokoro_tts_local/models.py`)**:
   - Áp dụng bản vá phoneme chuẩn hóa `_patch_vig2p_for_vietnamese()`:
     * Từ `y` (đứng độc lập) -> chuyển thành âm `/i/` (`ˈi`) chuẩn tiếng Việt (thanh ngang).
     * Từ `u` (đứng độc lập) -> chuyển thành âm `/u/` (`ˈu`) chuẩn tiếng Việt.
     * Từ `e` (đứng độc lập) -> chuyển thành âm `/ɛ/` (`ˈɛ`) chuẩn tiếng Việt.
   - Bản vá áp dụng trực tiếp cho cả luồng Direct Execution lẫn Server ngoài (nếu có).
2. **Core Text Normalizer (`app/core/text_normalizer.py`)**:
   - Bổ sung các từ viết tắt y tế và đời sống: `SYT` -> `Sở Y tế`, `BV` -> `bệnh viện`, `BS` -> `bác sĩ`, `DS` -> `dược sĩ`.
   - Bổ sung và ưu tiên xử lý cụm có gạch chéo: `y/c`, `yc` -> `yêu cầu`, `k/m` -> `khuyến mãi`, `k/h` -> `khách hàng` trước khi regex xử lý chữ `k` phủ định đơn lẻ.

### 4. Kết quả kiểm thử tự động:
- **Unit Test (`tests/test_text_normalizer.py`)**: Đạt **16/16 test methods PASS 100%** (bao gồm test case kiểm tra phoneme của 'đóng bảo hiểm y tế', 'bác sĩ y khoa', 'thuốc đông y', 'khối u xơ', 'e ngại').
- **Toàn bộ Test Suite hệ thống (`python run_all_tests.py`)**: Đạt **131/131 tests PASS 100% (0 errors, 0 failures, chạy trong 53.52s)**!

---

## [2026-10-14 15:05] - Khắc phục Triệt Để Lỗi Height Bung Full Màn Hình do Fusion Style (`SH_ComboBox_Popup`)

### 1. Bối cảnh & Phản hồi từ Người Dùng:
- Người dùng phản ánh: *"height vẫn phủ full màn, width thì ok r"*
- **Nguyên nhân cốt lõi phát hiện**:
  * Ứng dụng sử dụng `app.setStyle("Fusion")` trong `app/styles.py`.
  * Theo cơ chế nội bộ của Qt, style **Fusion** đặt style hint `QStyle::SH_ComboBox_Popup = True`.
  * Khi hint này bằng `True`, Qt ép mọi combobox non-editable hiển thị dropdown dưới dạng **Menu popup toàn màn hình** (bung từ `Y = 0` đến hết chiều cao màn hình `Y = 864` trên Windows) và **hoàn toàn phớt lờ `maxVisibleItems` lẫn `max-height` trong stylesheet**!

### 2. Các giải pháp kỹ thuật đã triển khai (3 lớp phòng thủ triệt để):
1. **Lớp 1 - Stylesheet (`app/assets/theme.qss`)**:
   - Thêm thuộc tính `combobox-popup: 0;` cho selector `QComboBox`. Thuộc tính này ra lệnh cho engine Qt Style Sheet tắt chế độ menu popup, chuyển về listbox popup.
2. **Lớp 2 - Style Engine (`app/styles.py`)**:
   - Tạo `DarkAppStyle(QProxyStyle)` ghi đè `styleHint(SH_ComboBox_Popup)` luôn trả về `0`.
   - Áp dụng `app.setStyle(DarkAppStyle("Fusion"))` trong hàm `setup_theme(app)`.
3. **Lớp 3 - Widget Guard (`app/ui/components/voice_selector.py`)**:
   - Ghi đè `showPopup()` trong `VoiceSelectorComboBox`: Tính toán `max_h = row_h * maxVisibleItems + 12`, tự động resize popup container về đúng chuẩn nếu vượt quá (ngăn chặn mọi trường hợp tràn màn hình).
   - Chiều cao popup thực tế giảm từ **864px (toàn màn hình)** xuống còn đúng **204px – 246px** (8 items vừa vặn).

### 3. Kết quả kiểm thử tự động (Unit Test & UI Automation):
- **UI Automation Test (`tests/test_preset_voices_ui.py`)**: 13/13 tests PASS.
- **Toàn bộ Test Suite hệ thống (`python run_all_tests.py`)**: **131/131 tests PASS 100% (0 errors, 0 failures, 19 suites trong 56.56s)**!

---

## [2026-10-14 15:58] - Chuyển Thư Mục Lưu Trữ Voice TTS sang "D:\Work\Tool\Voices" (Loại Bỏ Ổ C)

### 1. Bối cảnh & Yêu cầu Người Dùng:
- Người dùng yêu cầu: *"Ok rồi, giờ tới lượt lưu tại, "D:\Work\Tool\Voices" chứ k phải ở ổ C nữa"*
- **Vấn đề cần giải quyết**:
  1. Thư mục tải về mặc định cho Voice TTS trước đó nằm ở `%USERPROFILE%\Downloads\tts` (ổ C:).
  2. QSettings (`standalone/tts`) của người dùng có thể đang lưu đường dẫn cũ ở ổ C:, cần tự động di chuyển / chuyển hướng sang thư mục mới ở ổ D:.

### 2. Các giải pháp kỹ thuật đã triển khai:
1. **`app/config.py`**:
   - Khởi tạo hàm `_get_default_tts_dir()`: Kiểm tra nếu ổ `D:` tồn tại thì đặt mặc định là `D:\Work\Tool\Voices`, tự động tạo thư mục `mkdir(parents=True, exist_ok=True)`. Nếu không có ổ D thì fallback an toàn về thư mục người dùng.
   - Bổ sung `TTS_DOWNLOADS_DIR` vào lớp cấu hình `AppConfig` và `reload_config()`:
     * Hỗ trợ đầy đủ cả `config.settings.TTS_DOWNLOADS_DIR` lẫn module-level `config.TTS_DOWNLOADS_DIR` để đảm bảo 100% Backward Compatibility.
2. **`app/ui/tts_tab.py`**:
   - Sửa hàm `_restore_standalone_state()`: Nhận diện đường dẫn cũ ở ổ C: (`USER_DOWNLOADS_DIR / "tts"` hoặc `downloads/tts`) và tự động chuyển hướng sang `config.TTS_DOWNLOADS_DIR` (`D:\Work\Tool\Voices`).
   - Cập nhật nhãn hiển thị `Lưu tại:` và logic mở thư mục `open_downloads()` trỏ thẳng về `D:\Work\Tool\Voices`.
3. **QSettings Migration**:
   - Cập nhật trực tiếp key `standalone/tts` trong QSettings của ứng dụng sang `D:\Work\Tool\Voices` để người dùng mở app lên là thấy ngay lập tức.

### 3. Kết quả kiểm thử tự động:
- **Unit Test UI (`tests/test_standalone_tools_ui.py`)**: **17/17 tests PASS 100%**.
- **Toàn bộ Test Suite hệ thống (`python run_all_tests.py`)**: **131/131 tests PASS 100% (0 errors, 0 failures, 19 suites trong 49.01s)**!

---

## [2026-10-14 17:15] - Sửa Triệt Để Lỗi Nút Phát Kẹt "Tạm Dừng" & Bổ Sung Nút "Nghe Thử Nhanh Mẫu Giọng" (Quick Voice Sample Preview)

### 1. Bối cảnh & Phản hồi Người Dùng:
- Người dùng phản ánh:
  1. *"trước hết cải tiến cái đầu tiên trước, với lại nút phát thì voice nói hết rồi vẫn thấy nút là tạm dừng chứ k phải là nút phát ấy"*
- **Hai vấn đề cốt lõi cần giải quyết**:
  - **Vấn đề 1 (Lỗi nút phát kẹt ở "Tạm dừng")**: Khi file âm thanh đã đọc hết (`EndOfMedia` hoặc `StoppedState`), nút phát vẫn kẹt text `"Tạm dừng"`. Nếu người dùng click lại, app không replay từ đầu mà có thể bị kẹt hoặc đơ do position ở cuối file.
  - **Vấn đề 2 (Nghe thử nhanh mẫu giọng - Quick Voice Preview)**: Trước đây để nghe thử một giọng đọc, người dùng bắt buộc phải chuyển sang tab "Tra cứu Voice" hoặc phải gõ chữ rồi bấm "Nghe Thử (Preview)" (tốn credit và thời gian render). Cần thêm nút `▶ Nghe thử` ngay cạnh ô ComboBox chọn giọng đọc để nghe ngay 2-3s câu thoại mẫu có sẵn.

### 2. Các giải pháp kỹ thuật đã triển khai:
1. **Khắc phục triệt để lỗi nút phát audio (`app/ui/tts_tab.py`)**:
   - Kết nối hai signal cốt lõi của `QMediaPlayer`: `playbackStateChanged` và `mediaStatusChanged`.
   - Cài đặt `on_player_playback_state_changed`:
     * `PlayingState` -> hiển thị `"Tạm dừng"`.
     * `PausedState` -> hiển thị `"Tiếp tục"`.
     * `StoppedState` -> hiển thị `"Phát"`.
   - Cài đặt `on_player_media_status_changed`:
     * Khi đạt trạng thái `EndOfMedia` (file đọc hết câu): Tự động đổi text nút thành `"Phát"`, reset vị trí slider về `0`, reset nhãn thời gian hiện tại về `"00:00"`, và gọi `player.setPosition(0)` để lần bấm sau phát lại từ đầu câu thoại.
   - Sửa `toggle_play_pause`: Tự động nhận diện nếu đang ở cuối bài / `EndOfMedia` thì seek về 0 trước khi `play()`.
   - Sửa `stop_player`: Dừng player, seek về 0, reset slider và label thời gian về `"00:00"`.

2. **Bổ sung tính năng Nghe Thử Nhanh Mẫu Giọng (`VoicePreviewWorker` & `btn_sample_preview`)**:
   - Thêm nút `self.btn_sample_preview` (`▶ Nghe thử`) đặt ngay cạnh `combo_voice` trong `voice_row` (giữa ComboBox và nút `🔍 Tra cứu…`).
   - Xây dựng luồng nền `VoicePreviewWorker(QThread)`:
     * Hỗ trợ cache offline thông minh tại `downloads/voice_previews/{provider}_{voice_id}.mp3/wav`. File mẫu chỉ tải/tạo 1 lần duy nhất, các lần bấm sau phát tức thì!
     * **Kokoro Local**: Tự động sinh câu thoại ngắn 1 câu đa ngôn ngữ tương ứng (`vi`, `en`, `zh`, `ja`) hoàn toàn offline.
     * **ElevenLabs / MiniMax / CapCut**: Lấy URL audio mẫu từ thư viện online, tự động tải về lưu cache local và phát mượt mà qua `sample_player`.
   - Tương tác giao diện thông minh:
     * Khi bấm nghe thử: Đổi trạng thái thành `"⏳ Đang tải..."` -> khi phát đổi thành `"⏹ Dừng"`.
     * Khi phát hết hoặc người dùng bấm dừng: Tự động trả về `"▶ Nghe thử"`.
     * Tự động dừng phát mẫu khi người dùng đổi giọng đọc, đổi nền tảng (provider) hoặc bấm Tạo Voice / Nghe Thử script.

3. **Bảo toàn Test Suite Mock (`tests/test_preset_voices_ui.py` & `tests/test_standalone_tools_ui.py`)**:
   - Cung cấp đầy đủ thuộc tính lớp `PlaybackState` và `MediaStatus` cho mock `_SilentMediaPlayer`.

### 3. Kết quả kiểm thử tự động (Unit Test & UI Automation):
- **Unit & UI Test (`tests/test_preset_voices_ui.py`)**: **16/16 tests PASS 100%** (bổ sung 3 test case kiểm tra state transitions của player và nút quick preview).
- **Unit & UI Test (`tests/test_standalone_tools_ui.py`)**: **17/17 tests PASS 100%**.
- **Toàn bộ Test Suite hệ thống (`python run_all_tests.py`)**: **134/134 tests PASS 100% (0 errors, 0 failures, 19 suites trong 45.03s)!**

---

## [2026-10-14 18:10] - Sửa Triệt Để Lỗi Phân Biệt 'AI' (Trí tuệ nhân tạo) và 'ai' (Đại từ tiếng Việt)

### 1. Bối cảnh & Phản hồi Người Dùng:
- Người dùng phản ánh: *"Từ từ chưa cần, giờ nó đọc ai là ây ai luôn, tôi nghĩ phải viết hoa là AI thì mới đọc là ây ai chứ?"*
- **Nguyên nhân kỹ thuật cốt lõi phát hiện**:
  - Trong `kokoro_tts_local/models.py`, từ điển `tech_map` chứa cả `r'\bAI\b': 'ây ai'` lẫn `r'\bai\b': 'ây ai'`, đồng thời vòng lặp thay thế sử dụng `flags=re.IGNORECASE`.
  - Hậu quả: Mọi từ `ai` tiếng Việt thông thường (như *"ai đó"*, *"có ai không"*, *"ai cũng biết"*, *"không ai làm gì"*, *"Ai đó đang gọi"*) đều bị biến đổi thành *"ây ai"*!

### 2. Các giải pháp kỹ thuật đã triển khai:
1. **Sửa chuẩn hóa nội bộ Kokoro (`kokoro_tts_local/models.py`)**:
   - Tách riêng `r'\bAI\b': 'ây ai'` thành xử lý **Case-Sensitive** nghiêm ngặt (chỉ thay thế khi viết hoa cả hai chữ cái `AI`).
   - Loại bỏ hoàn toàn `r'\bai\b'` khỏi `tech_map`.
   - Bảo toàn 100% từ `ai` thường và `Ai` đầu câu trong tiếng Việt.
2. **Kiểm tra phát âm G2P thực tế**:
   - `ai đó` -> phát âm chuẩn tiếng Việt `ˈaːj dˈɔ↗` ("ai đó"), không có âm "ây".
   - `Ai đó đang gọi bạn` -> phát âm chuẩn tiếng Việt `ˈaːj dˈɔ↗...`.
   - `công nghệ AI` -> phát âm chuẩn `ˈəɪ ˈaːj` ("công nghệ ây ai").

### 3. Kết quả kiểm thử tự động:
- **Unit Test (`tests/test_text_normalizer.py`)**: **17/17 tests PASS 100%** (bổ sung test case `test_ai_distinction_between_vietnamese_pronoun_and_tech_ai`).
- **Toàn bộ Test Suite hệ thống (`python run_all_tests.py`)**: **135/135 tests PASS 100% (0 errors, 0 failures, 19 suites trong 49.08s)!**


