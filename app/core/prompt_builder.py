"""
prompt_builder.py: Xây dựng Master Prompt chuyên sâu cho các AI LLM (ChatGPT, Claude, Gemini, DeepSeek).
Tự động tính toán chuẩn xác số từ theo thời lượng phát (30s, 60s, 2p, 5p), tối ưu cho Text-to-Speech
và định dạng phân cảnh SC01, SC02... tương thích 100% với Editor-AI-App.
"""

from typing import Any, Dict, Optional, Tuple

DURATION_PRESETS = [
    (30, "⏱️ 30 Giây (Shorts / TikTok ngắn)", (65, 80), 3),
    (60, "⏱️ 60 Giây (1 Phút TikTok / Reels)", (135, 160), 5),
    (120, "⏱️ 2 Phút (Video trung bình)", (270, 310), 8),
    (180, "⏱️ 3 Phút (Video phân tích)", (410, 470), 10),
    (300, "⏱️ 5 Phút (Phim ngắn / Tin tức)", (680, 750), 15),
    (480, "⏱️ 8 Phút (YouTube bật kiếm tiền)", (1080, 1200), 20),
    (600, "⏱️ 10 Phút (YouTube chuyên sâu)", (1350, 1500), 25),
    (900, "⏱️ 15 Phút (Phóng sự / Tài liệu)", (2000, 2250), 30),
    (1200, "⏱️ 20 Phút (Kể chuyện / Podcast)", (2700, 3000), 40),
    (1800, "⏱️ 30 Phút (Chuyên đề dài)", (4000, 4500), 50),
    (-1, "⚙️ Tùy chỉnh (Nhập phút/giây tùy ý...)", (0, 0), 0),
]

TONE_PRESETS = [
    ("dramatic", "🔥 Kịch tính / Cuốn hút / Hồi hộp"),
    ("narrative", "🎙️ Trầm ấm / Kể chuyện / Tâm sự"),
    ("news", "📰 Bản tin / Thời sự / Đanh thép"),
    ("humor", "😂 Hài hước / Châm biếm / Dí dỏm"),
    ("inspiring", "🌟 Truyền cảm hứng / Động lực / Triết lý"),
    ("analytical", "🧠 Chuyên gia / Phân tích / Khách quan"),
]

PLATFORM_PRESETS = [
    ("shorts", "📱 TikTok / Reels / Shorts (Khung dọc 9:16)"),
    ("youtube", "🖥️ YouTube Video (Khung ngang 16:9)"),
    ("podcast", "🎧 Podcast / Radio Audio"),
]


LANGUAGE_PRESETS = [
    ("vi", "🇻🇳 Tiếng Việt (Vietnamese)"),
    ("en", "🇺🇸 Tiếng Anh (English)"),
    ("zh", "🇨🇳 Tiếng Trung (中文 - Chinese)"),
    ("ja", "🇯🇵 Tiếng Nhật (日本語 - Japanese)"),
    ("ko", "🇰🇷 Tiếng Hàn (한국어 - Korean)"),
    ("fr", "🇫🇷 Tiếng Pháp (Français)"),
    ("es", "🇪🇸 Tiếng Tây Ban Nha (Español)"),
    ("de", "🇩🇪 Tiếng Đức (Deutsch)"),
    ("ru", "🇷🇺 Tiếng Nga (Русский)"),
]

LANGUAGE_NAMES = {
    "vi": "Tiếng Việt",
    "en": "Tiếng Anh (English)",
    "zh": "Tiếng Trung (Chinese - 普通话)",
    "ja": "Tiếng Nhật (Japanese - 日本語)",
    "ko": "Tiếng Hàn (Korean - 한국어)",
    "fr": "Tiếng Pháp (French - Français)",
    "es": "Tiếng Tây Ban Nha (Spanish - Español)",
    "de": "Tiếng Đức (German - Deutsch)",
    "ru": "Tiếng Nga (Russian - Русский)",
}


def get_language_unit(lang_code: str = "vi") -> str:
    """Trả về đơn vị đo độ dài văn bản phù hợp với từng ngôn ngữ."""
    code = (lang_code or "vi").lower()
    if code in ("zh", "cn"):
        return "chữ (ký tự tiếng Trung - 字)"
    elif code == "ja":
        return "ký tự (tiếng Nhật - 文字)"
    elif code == "ko":
        return "từ / âm tiết (tiếng Hàn - 단어)"
    elif code == "en":
        return "từ tiếng Anh (words)"
    elif code == "vi":
        return "từ tiếng Việt"
    return "từ"


def format_duration_display(duration_seconds: int) -> str:
    """Định dạng thời lượng thành chuỗi hiển thị tiếng Việt rõ ràng."""
    if duration_seconds < 60:
        return f"{duration_seconds} giây"
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    if seconds == 0:
        return f"{minutes} phút ({duration_seconds} giây)"
    return f"{minutes} phút {seconds} giây ({duration_seconds} giây)"


def get_word_count_range(duration_seconds: int, lang_code: str = "vi") -> Tuple[int, int, int]:
    """
    Trả về (word_min, word_max, recommended_scenes) cho thời lượng phát và ngôn ngữ tương ứng.
    Tự động hiệu chỉnh tốc độ phát âm theo đặc thù ngôn ngữ:
    - Tiếng Việt / Tiếng Anh / Âu: ~2.5 từ/giây (150 từ/phút).
    - Tiếng Trung: ~3.6 ký tự/giây (215 chữ/phút).
    - Tiếng Nhật: ~5.0 ký tự/giây (300 ký tự/phút).
    - Tiếng Hàn: ~3.3 âm tiết/giây (200 âm tiết/phút).
    """
    code = (lang_code or "vi").lower()
    valid_seconds = max(10, int(duration_seconds))

    if code in ("vi", "en", "fr", "es", "de", "ru"):
        for dur, _, words, scenes in DURATION_PRESETS:
            if dur > 0 and dur == valid_seconds:
                return words[0], words[1], scenes
        rate = 2.5
    elif code in ("zh", "cn"):
        rate = 3.6
    elif code == "ja":
        rate = 5.0
    elif code == "ko":
        rate = 3.3
    else:
        rate = 2.5

    center = int(valid_seconds * rate)
    min_w = max(25, int(center * 0.9))
    max_w = int(center * 1.1)
    scenes = max(3, min(60, int(valid_seconds / 20)))
    return min_w, max_w, scenes


def build_master_prompt(
    topic: str,
    title: str,
    angle_label: str = "Tự nhiên / Đa chiều",
    duration_seconds: int = 60,
    tone: str = "dramatic",
    platform: str = "shorts",
    include_scenes: bool = True,
    include_image_prompts: bool = True,
    extra_notes: str = "",
    language: str = "vi",
) -> str:
    """
    Xây dựng văn bản Master Prompt chuẩn mực cho AI với ngôn ngữ kịch bản tùy chọn.
    """
    lang_code = (language or "vi").lower()
    min_words, max_words, num_scenes = get_word_count_range(duration_seconds, lang_code=lang_code)
    unit_name = get_language_unit(lang_code)
    lang_name = LANGUAGE_NAMES.get(lang_code, lang_code)
    lang_display = dict(LANGUAGE_PRESETS).get(lang_code, lang_name)
    ar_tag = "--ar 9:16" if "shorts" in platform.lower() else "--ar 16:9"

    tone_desc = dict(TONE_PRESETS).get(tone, tone)
    platform_desc = dict(PLATFORM_PRESETS).get(platform, platform)

    prompt = f"""# VAI TRÒ CHUYÊN GIA:
Bạn là một Biên Kịch Gia & Chuyên Gia Sáng Tạo Nội Dung Video Ngắn triệu view hàng đầu trên TikTok và YouTube. Nhiệm vụ của bạn là viết một kịch bản video viral hoàn hảo dựa trên chủ đề và các thông số kỹ thuật bên dưới.

---

## THÔNG TIN DỰ ÁN:
- **Chủ đề chính:** {topic}
- **Tiêu đề video đề xuất:** {title}
- **Góc tiếp cận:** {angle_label}
- **Nền tảng phát hành:** {platform_desc}
- **Ngôn ngữ kịch bản bài đọc:** {lang_display}
- **Thời lượng đọc dự kiến:** {format_duration_display(duration_seconds)}
- **GIỚI HẠN ĐỘ DÀI CHẶT CHẼ:** Đúng từ {min_words} đến {max_words} {unit_name} (BẮT BUỘC tuân thủ để khi đọc bằng công cụ Text-To-Speech vừa khít {format_duration_display(duration_seconds)}, không quá nhanh, không quá chậm).
- **Tông giọng & Phong cách:** {tone_desc}
{f'- **Ghi chú bổ sung từ đạo diễn:** {extra_notes}' if extra_notes.strip() else ''}

---

## QUY TẮC BIÊN TẬP VÀNG:
1. **Yêu Cầu Ngôn Ngữ Bắt Buộc:** Toàn bộ Lời thoại đọc (Voice Script) BẮT BUỘC phải viết hoàn toàn bằng **{lang_name}** chuẩn bản ngữ, tự nhiên, văn phong cuốn hút, lưu loát của người bản xứ.
2. **Hook 3 Giây Đầu:** Câu mở đầu bằng {lang_name} phải gây sốc, đánh trúng sự tò mò hoặc nghịch lý của vấn đề. Tuyệt đối KHÔNG chào hỏi rườm rà (không nói "Xin chào các bạn...", "Hello everyone...").
3. **Nhịp Điệu & Câu Chữ:**
   - Sử dụng các câu đơn, câu ngắn (dưới 15-20 từ hoặc cụm từ ngắn) để bộ chuyển âm Text-To-Speech (AI Voice) đọc mượt mà, không bị hụt hơi.
   - Lối hành văn sắc sảo, cô đọng, giàu hình ảnh gợi cảm xúc.
4. **Phần Kết (CTA):** Câu kết đọng lại suy ngẫm hoặc kêu gọi bình luận một cách tự nhiên.
5. **Prompt Vẽ Ảnh (Midjourney/Flux):** BẮT BUỘC viết bằng **Tiếng Anh (English)** để các công cụ AI tạo ảnh (Midjourney, Flux, Stable Diffusion) sinh ảnh đạt độ phân giải và chi tiết tối đa.
6. **Không Dùng Ký Tự Lạ:** Trong phần lời thoại đọc (Voice Text), KHÔNG để emoji, KHÔNG để dấu gạch đầu dòng, không để chú thích trong ngoặc kép (như cười, nhạc nền...) để tránh làm công cụ đọc đọc nhầm thành chữ.

---

## ĐỊNH DẠNG KẾT QUẢ ĐẦU RA BẮT BUỘC:

Vui lòng xuất ra kết quả rõ ràng theo đúng 2 phần sau:

### PHẦN 1: BẢNG PHÂN CẢNH CHI TIẾT (Dành cho dựng video)
Chia kịch bản thành {num_scenes} phân cảnh (SC01 đến SC{num_scenes:02d}):
"""

    if include_scenes:
        prompt += f"""
Cho mỗi cảnh, định dạng như sau:
**[SC01]**
- **Lời thoại đọc ({lang_name}):** (Viết 1-2 câu ngắn gọn cho cảnh này bằng {lang_name})
- **Mô tả hình ảnh (Tiếng Việt hoặc Tiếng Anh):** (Mô tả bối cảnh trực quan)
{f'- **Prompt vẽ ảnh (Midjourney/Flux bằng Tiếng Anh):** (Prompt chi tiết, phong cách cinematic, photorealistic, 8k, dramatic lighting {ar_tag})' if include_image_prompts else ''}
- **Chuyển động camera gợi ý:** (Zoom In / Zoom Out / Pan Left / Pan Right)

*(Làm tương tự cho đến SC{num_scenes:02d})*
"""

    prompt += f"""
### PHẦN 2: TOÀN BỘ LỜI THOẠI ĐỌC LIÊN TỤC (Bằng {lang_name} - Dành cho Text-to-Speech)
(Nối toàn bộ lời thoại của các cảnh thành một đoạn văn hoàn chỉnh duy nhất bằng {lang_name}, đảm bảo đúng {min_words} - {max_words} {unit_name} để tôi sao chép trực tiếp vào phần mềm lồng tiếng TTS).
"""

    return prompt.strip()
