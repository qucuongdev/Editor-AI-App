#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini_client.py: Client gọi Google Gemini API để sinh kịch bản và phân cảnh video AI thực thụ.
Sử dụng thư viện chuẩn urllib của Python, không phụ thuộc package bên ngoài, tốc độ cực nhanh.
Hỗ trợ các model: gemini-1.5-flash, gemini-2.0-flash, gemini-2.5-flash.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from app.core.storyboard_generator import StoryboardScene, TONE_PROFILES, VISUAL_STYLES


GEMINI_MODELS = [
    ("gemini-3.5-flash", "⚡ Gemini 3.5 Flash (Nhanh, Ổn định & Thông minh)"),
    ("gemini-3.8-flash", "🚀 Gemini 3.8 Flash (Thế hệ mới nhất)"),
    ("gemini-2.0-flash", "🚀 Gemini 2.0 Flash (Thế hệ 2.0)"),
    ("gemini-1.5-flash", "⚡ Gemini 1.5 Flash (Mặc định)"),
    ("gemini-1.5-pro", "🧠 Gemini 1.5 Pro (Suy luận sâu & Chi tiết)"),
    ("gemini-3.1-flash-lite", "💨 Gemini 3.1 Flash-Lite (Siêu tốc & Tiết kiệm)"),
    ("gemini-2.5-flash-lite", "⚡ Gemini 2.5 Flash-Lite (Nhẹ & Nhanh)"),
    ("gemini-3.1-pro-preview", "🧠 Gemini 3.1 Pro (Suy luận sâu & Chi tiết)"),
]

FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
]


class GeminiAPIError(Exception):
    """Lỗi phát sinh khi gọi Google Gemini API."""
    pass


def fetch_gemini_models(api_key: str, timeout: int = 15) -> List[Dict[str, str]]:
    """
    Quét danh sách các model thực tế từ tài khoản Google Gemini qua API.
    Đồng thời xác thực API Key có hợp lệ và hoạt động hay không.
    Trả về danh sách dict: [{'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash', 'description': '...'}]
    """
    clean_key = (api_key or "").strip()
    if not clean_key:
        raise GeminiAPIError("Vui lòng nhập Google Gemini API Key để kiểm tra!")

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
    req = urllib.request.Request(
        url,
        headers={"Content-Type": "application/json"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)

            raw_models = res_json.get("models", [])
            valid_models = []
            for item in raw_models:
                methods = item.get("supportedGenerationMethods", [])
                name = item.get("name", "")
                model_id = name.replace("models/", "").strip()
                display_name = item.get("displayName") or model_id

                # Chỉ lấy các model hỗ trợ generateContent hoặc có tên gemini
                if "generateContent" in methods or "gemini" in model_id.lower():
                    desc = item.get("description", "")
                    valid_models.append({
                        "id": model_id,
                        "name": display_name,
                        "description": desc,
                    })

            if not valid_models:
                return [{"id": m[0], "name": m[1], "description": ""} for m in GEMINI_MODELS]

            # Sắp xếp ưu tiên các model mới nhất và ổn định lên đầu
            def model_sort_key(m):
                mid = m["id"].lower()
                if "3.5-flash" in mid and "lite" not in mid:
                    return 0
                elif "3.8-flash" in mid and "tts" not in mid and "lite" not in mid:
                    return 1
                elif "3.1-flash-lite" in mid:
                    return 2
                elif "2.5-flash-lite" in mid:
                    return 3
                elif "3.1-pro" in mid:
                    return 4
                elif "flash" in mid:
                    return 5
                elif "pro" in mid:
                    return 6
                return 7

            valid_models.sort(key=model_sort_key)
            return valid_models

    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_msg)
            msg = err_json.get("error", {}).get("message", err_msg)
        except Exception:
            msg = err_msg or str(e)
        raise GeminiAPIError(f"API Key không hợp lệ hoặc lỗi Google API ({e.code}): {msg}")
    except urllib.error.URLError as e:
        raise GeminiAPIError(f"Không thể kết nối đến Google Gemini API: {e.reason}")
    except Exception as e:
        raise GeminiAPIError(f"Lỗi kiểm tra kết nối: {str(e)}")


def verify_gemini_connection(api_key: str, timeout: int = 15) -> Tuple[bool, str, List[Dict[str, str]]]:
    """
    Hàm kiểm tra kết nối nhanh tới Gemini API.
    Trả về: (success: bool, message: str, models: list)
    """
    try:
        models = fetch_gemini_models(api_key, timeout=timeout)
        return True, f"Kết nối thành công! Đã nạp {len(models)} model khả dụng từ Google.", models
    except GeminiAPIError as e:
        return False, str(e), []
    except Exception as e:
        return False, f"Lỗi không xác định: {str(e)}", []


def call_gemini_generate_content(
    prompt: str,
    api_key: str,
    model: str = "gemini-3.5-flash",
    timeout: int = 30,
) -> str:
    """
    Gọi trực tiếp API Google Gemini generateContent bằng HTTP POST.
    Hỗ trợ Smart Auto-Fallback: Tự động chuyển model dự phòng nếu model đang dùng bị 503 (quá tải) hoặc 404 (deprecated).
    Trả về nội dung văn bản phản hồi từ model.
    """
    clean_key = (api_key or "").strip()
    if not clean_key:
        raise GeminiAPIError("Chưa cấu hình Google Gemini API Key. Vui lòng nhập key trong Cài đặt.")

    initial_model = (model or "gemini-3.5-flash").strip()
    candidate_models = [initial_model]
    for fb in FALLBACK_MODELS:
        if fb not in candidate_models:
            candidate_models.append(fb)

    last_error = None
    for target_model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={clean_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 4096,
            }
        }

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)

                candidates = res_json.get("candidates", [])
                if not candidates:
                    raise GeminiAPIError("Gemini API không trả về kết quả nào (candidates rỗng).")

                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise GeminiAPIError("Gemini API trả về nội dung rỗng.")

                return parts[0].get("text", "").strip()

        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_msg)
                msg = err_json.get("error", {}).get("message", err_msg)
            except Exception:
                msg = err_msg or str(e)
            last_error = GeminiAPIError(f"Lỗi Gemini API ({e.code}) trên model '{target_model}': {msg}")
            # Nếu 503 (quá tải), 404 (model cũ), 429 (rate limit), tiếp tục thử model dự phòng tiếp theo
            if e.code in (503, 404, 429):
                continue
            raise last_error
        except urllib.error.URLError as e:
            raise GeminiAPIError(f"Không thể kết nối đến Google Gemini API: {e.reason}")
        except Exception as e:
            last_error = GeminiAPIError(f"Lỗi không xác định khi gọi Gemini API ({target_model}): {str(e)}")
            continue

    if last_error:
        raise last_error
    raise GeminiAPIError("Không thể hoàn tất phản hồi từ Google Gemini API qua các model dự phòng.")


def extract_json_array_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Trích xuất mảng JSON từ phản hồi văn bản của LLM (loại bỏ markdown block nếu có).
    """
    clean_text = text.strip()
    # 1. Tìm trong block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```", clean_text, re.DOTALL)
    if match:
        clean_text = match.group(1).strip()
    else:
        # 2. Tìm mảng JSON bắt đầu bằng [ và kết thúc bằng ]
        first_bracket = clean_text.find("[")
        last_bracket = clean_text.rfind("]")
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            clean_text = clean_text[first_bracket : last_bracket + 1].strip()

    try:
        data = json.loads(clean_text)
        if isinstance(data, list):
            return data
    except Exception as exc:
        raise GeminiAPIError(f"Không thể phân tích dữ liệu JSON từ phản hồi của AI: {str(exc)}\nNội dung AI trả về:\n{text[:300]}")

    raise GeminiAPIError("Dữ liệu AI trả về không phải là một mảng JSON hợp lệ.")


def generate_storyboard_with_gemini(
    topic: str,
    scene_count: int = 5,
    duration_seconds: int = 60,
    tone: str = "mystery",
    visual_style: str = "cinematic",
    aspect_ratio: str = "9:16",
    api_key: str = "",
    model: str = "gemini-1.5-flash",
) -> List[StoryboardScene]:
    """
    Sử dụng Google Gemini AI thực thụ để sinh kịch bản phân cảnh chi tiết, độc nhất cho chủ đề.
    """
    total_scenes = max(3, min(10, scene_count))
    style_desc = VISUAL_STYLES.get(visual_style, VISUAL_STYLES["cinematic"])
    tone_profile = TONE_PROFILES.get(tone, TONE_PROFILES["mystery"])
    tone_label = tone_profile.get("label", tone)
    per_scene_sec = round(duration_seconds / total_scenes, 1)

    system_prompt = f"""Bạn là Đạo diễn Video & Biên Kịch Gia hàng đầu thế giới về video ngắn triệu view (TikTok, Shorts, Reels, YouTube).
Nhiệm vụ của bạn là viết một Kịch Bản Phân Cảnh (Storyboard) hoàn chỉnh, độc nhất vô nhị cho chủ đề sau:

- Chủ đề video: "{topic}"
- Tổng thời lượng dự kiến: ~{duration_seconds} giây
- Số lượng phân cảnh bắt buộc: đúng {total_scenes} cảnh (từ SC01 đến SC{total_scenes:02d})
- Thời lượng mỗi cảnh: ~{per_scene_sec} giây
- Tông điệu cảm xúc: {tone_label}
- Phong cách hình ảnh: {visual_style} ({style_desc})
- Tỉ lệ khung hình ảnh: {aspect_ratio}

QUY TẮC BẮT BUỘC:
1. Cấu trúc kịch bản phải chuẩn Storytelling giữ chân người xem đỉnh cao:
   - Cảnh đầu (SC01): Phải là Hook gây sốc hoặc nghịch lý giật gân, cuốn hút người xem ngay trong 3 giây đầu.
   - Các cảnh thân bài: Khai thác thực trạng, cạm bẫy tâm lý, góc nhìn phản trực giác và giải pháp hành động cụ thể.
   - Cảnh cuối (SC{total_scenes:02d}): Kêu gọi hành động (Call To Action) và đúc kết triết lý sâu sắc.
2. "voiceover": Lời thoại đọc thuyết minh hoàn toàn bằng TIẾNG VIỆT tự nhiên, văn phong sắc bén, mượt mà (khoảng 25 - 45 từ mỗi cảnh), không dùng ký tự lạ hay ngoặc chú thích.
3. "prompt": Mô tả hình ảnh chi tiết BẮT BUỘC BẰNG TIẾNG ANH (English) dành cho Midjourney/Flux/Veo/Kling, kèm theo style `{style_desc}` và flag `--ar {aspect_ratio}`.
4. "motion": Chọn 1 trong các góc máy: "zoom_in", "zoom_out", "pan_left", "pan_right", "none".
5. "sfx": Gợi ý hiệu ứng âm thanh sống động bằng tiếng Việt ngắn gọn.

BẮT BUỘC TRẢ VỀ DUY NHẤT MỘT MẢNG JSON HỢP LỆ (không kèm bất kỳ lời dẫn giải nào ngoài mảng JSON), định dạng:
[
  {{
    "id": "SC01",
    "title": "Tiêu đề phân đoạn",
    "voiceover": "Lời thoại đọc tiếng Việt...",
    "prompt": "Detailed cinematic prompt in English, {style_desc}, --ar {aspect_ratio}",
    "duration": {per_scene_sec},
    "sfx": "Mô tả âm thanh",
    "motion": "zoom_in"
  }}
]
"""

    raw_response = call_gemini_generate_content(
        prompt=system_prompt,
        api_key=api_key,
        model=model,
    )

    json_scenes = extract_json_array_from_text(raw_response)

    scenes: List[StoryboardScene] = []
    for idx, item in enumerate(json_scenes, start=1):
        sc_id = item.get("id") or f"SC{idx:02d}"
        title = item.get("title") or f"Phân cảnh {idx}"
        voiceover = str(item.get("voiceover", "")).strip()
        prompt_text = str(item.get("prompt", "")).strip()
        dur = float(item.get("duration", per_scene_sec))
        sfx = str(item.get("sfx", "")).strip()
        motion = str(item.get("motion", "zoom_in")).strip()

        # Đảm bảo có flag tỉ lệ khung hình
        if f"--ar {aspect_ratio}" not in prompt_text:
            prompt_text = f"{prompt_text}, --ar {aspect_ratio}"

        scenes.append(
            StoryboardScene(
                scene_id=sc_id,
                title=title,
                voiceover=voiceover,
                prompt=prompt_text,
                duration=dur,
                sfx=sfx,
                motion_type=motion,
            )
        )

    return scenes


def generate_video_ideas_with_gemini(
    topic: str,
    api_key: str = "",
    model: str = "",
    count: int = 8,
    timeout: int = 25,
) -> List[Dict[str, Any]]:
    """
    Sử dụng Google Gemini AI thực thụ để phân tích chủ đề và sáng tạo danh sách
    các ý tưởng video viral sắc bén, hấp dẫn, câu từ tự nhiên và độc nhất vô nhị.
    """
    clean_topic = (topic or "").strip()
    if not clean_topic:
        return []

    from app import config
    key = api_key or getattr(config, "GEMINI_API_KEY", "")
    use_model = model or getattr(config, "GEMINI_MODEL", "gemini-3.5-flash")

    if not key:
        raise GeminiAPIError("Chưa có Google Gemini API Key để sinh ý tưởng AI.")

    system_prompt = f"""Bạn là Chuyên gia Chiến lược Nội dung & Đạo diễn Video Ngắn Triệu View (TikTok, Reels, YouTube Shorts).
Nhiệm vụ của bạn là phân tích sâu chủ đề sau và sáng tạo đúng {count} ý tưởng video viral độc nhất vô nhị:

- Chủ đề video: "{clean_topic}"

YÊU CẦU NỘI DUNG VÀ GÓC NHÌN:
Hãy phân bổ {count} ý tưởng trải đều các góc tiếp cận tâm lý khán giả:
1. "mystery" (🎯 Cạm bẫy & Góc khuất): Bóc trần sự thật, bí mật ít ai nói ra.
2. "advice" (💡 Mẹo sinh tồn & Giải pháp): Sai lầm chí mạng cần tránh và cách khắc phục thiết thực.
3. "debate" (⚡ Tranh cãi & Phản trực giác): Nghịch lý đi ngược số đông, kích thích thảo luận.
4. "story" (📖 Câu chuyện thực tế): Tình huống kịch tính, bài học xương máu có thật.
5. "humor" (😂 Châm biếm đời thường): Góc nhìn hài hước, tự trào dí dỏm.
6. "future" (🚀 Xu hướng & Tương lai): Cơ hội mới hoặc dự báo thay đổi quan trọng.

QUY TẮC CÂU CHỮ BẮT BUỘC:
1. "title": Tiêu đề video ngắn gọn, giật gân, cuốn hút (10 - 15 từ). TUYỆT ĐỐI KHÔNG lặp lại nguyên văn cụm từ dài của chủ đề một cách máy móc, phải biến tấu câu từ tự nhiên, sắc bén.
2. "hook": Câu mở đầu 3 giây đầu tiên (Hook) kích thích người xem không lướt qua (ngắn gọn, giật gân, khơi gợi tò mò).
3. "description": Tóm tắt cốt truyện / diễn biến chính của video (2 câu cô đọng, cuốn hút).
4. "angle": mã góc nhìn tương ứng (mystery, advice, debate, story, humor, future).
5. "angle_label": nhãn tiếng Việt có icon tương ứng.

BẮT BUỘC TRẢ VỀ DUY NHẤT MỘT MẢNG JSON HỢP LỆ (không kèm bất kỳ lời dẫn giải nào):
[
  {{
    "title": "Tiêu đề video cuốn hút",
    "hook": "Câu mở đầu giật gân trong 3 giây...",
    "description": "Tóm tắt ngắn gọn nội dung và bài học...",
    "angle": "mystery",
    "angle_label": "🎯 Cạm bẫy & Góc khuất"
  }}
]
"""

    raw_response = call_gemini_generate_content(
        prompt=system_prompt,
        api_key=key,
        model=use_model,
        timeout=timeout,
    )

    json_ideas = extract_json_array_from_text(raw_response)

    results: List[Dict[str, Any]] = []
    for idx, item in enumerate(json_ideas, start=1):
        title = str(item.get("title", "")).strip() or f"Ý tưởng video #{idx}"
        hook = str(item.get("hook", "")).strip()
        desc = str(item.get("description", "")).strip()
        angle = str(item.get("angle", "mystery")).strip()
        angle_label = str(item.get("angle_label", "🎯 Ý tưởng độc đáo")).strip()

        results.append({
            "id": f"GEMINI-{idx:03d}",
            "index": idx,
            "topic": clean_topic,
            "title": title,
            "angle": angle,
            "angle_label": angle_label,
            "description": desc,
            "hook_preview": hook,
            "is_ai_generated": True,
        })

    return results

