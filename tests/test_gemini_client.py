"""
test_gemini_client.py: Unit tests for Google Gemini AI Client integration.
Covers HTTP calls, JSON extraction, error handling, and StoryboardScene generation.
"""

import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from app.core.gemini_client import (
    call_gemini_generate_content,
    extract_json_array_from_text,
    generate_storyboard_with_gemini,
    GeminiAPIError,
)


class GeminiClientUnitTests(unittest.TestCase):
    def test_call_gemini_missing_api_key_raises_error(self):
        with self.assertRaises(GeminiAPIError) as ctx:
            call_gemini_generate_content("Viết kịch bản", api_key="")
        self.assertIn("Chưa cấu hình Google Gemini API Key", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_call_gemini_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": '[{"id": "SC01", "title": "Hook", "voiceover": "Xin chào", "prompt": "Cinematic shot", "duration": 6.0}]'}
                        ]
                    }
                }
            ]
        }
        mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res_text = call_gemini_generate_content("Test prompt", api_key="test_key_123")
        self.assertIn("SC01", res_text)

    @patch("urllib.request.urlopen")
    def test_call_gemini_http_error(self, mock_urlopen):
        error_body = json.dumps({"error": {"message": "API key not valid. Please pass a valid API key."}}).encode("utf-8")
        mock_err = urllib.error.HTTPError(
            url="https://generativelanguage.googleapis.com",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=MagicMock(read=MagicMock(return_value=error_body)),
        )
        mock_urlopen.side_effect = mock_err

        with self.assertRaises(GeminiAPIError) as ctx:
            call_gemini_generate_content("Test", api_key="bad_key")
        self.assertIn("API key not valid", str(ctx.exception))

    def test_extract_json_array_from_markdown_code_block(self):
        sample_output = """
Dưới đây là kịch bản phân cảnh hoàn chỉnh cho video của bạn:

```json
[
  {
    "id": "SC01",
    "title": "Mở đầu kịch tính",
    "voiceover": "Bạn có chắc chắn mình đang kiểm soát tài chính?",
    "prompt": "Dramatic view of a person looking at bank statement, --ar 9:16",
    "duration": 6.0,
    "sfx": "Dramatic bass drop",
    "motion": "zoom_in"
  }
]
```

Hy vọng kịch bản này giúp bạn có video triệu view!
"""
        scenes = extract_json_array_from_text(sample_output)
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["id"], "SC01")
        self.assertEqual(scenes[0]["title"], "Mở đầu kịch tính")

    def test_extract_json_array_from_raw_brackets(self):
        raw_text = 'Phân cảnh video: [{"id": "SC01", "title": "Cảnh 1", "voiceover": "Thoại 1"}] kết thúc.'
        scenes = extract_json_array_from_text(raw_text)
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["id"], "SC01")

    def test_extract_json_array_invalid_format_raises_error(self):
        invalid_text = "Không có bất kỳ mảng JSON nào ở đây."
        with self.assertRaises(GeminiAPIError):
            extract_json_array_from_text(invalid_text)

    @patch("app.core.gemini_client.call_gemini_generate_content")
    def test_generate_storyboard_with_gemini_success(self, mock_call):
        ai_mock_response = json.dumps([
            {
                "id": "SC01",
                "title": "Cú sốc đầu tiên",
                "voiceover": "Đừng bao giờ để tiền nằm yên một chỗ.",
                "prompt": "Cinematic shot of stacks of money evaporating into thin air",
                "duration": 6.0,
                "sfx": "Tiếng gió rít",
                "motion": "zoom_in"
            },
            {
                "id": "SC02",
                "title": "Giải pháp khai sáng",
                "voiceover": "Hãy bắt đầu kế hoạch phân bổ tài sản 3 giỏ ngay hôm nay.",
                "prompt": "Modern smart investment dashboard glowing in dark room",
                "duration": 6.0,
                "sfx": "Tiếng chuông ngân vang",
                "motion": "pan_right"
            },
            {
                "id": "SC03",
                "title": "Kêu gọi hành động",
                "voiceover": "Nhấn theo dõi để nhận bản đồ tài chính miễn phí.",
                "prompt": "Inspiring shot of rising financial charts on mobile",
                "duration": 6.0,
                "sfx": "Tiếng click nhẹ",
                "motion": "none"
            }
        ])
        mock_call.return_value = ai_mock_response

        scenes = generate_storyboard_with_gemini(
            topic="Bí mật đầu tư tài chính",
            scene_count=3,
            duration_seconds=30,
            tone="finance",
            visual_style="cinematic",
            aspect_ratio="9:16",
            api_key="valid_key",
            model="gemini-1.5-flash",
        )

        self.assertEqual(len(scenes), 3)
        self.assertEqual(scenes[0].scene_id, "SC01")
        self.assertEqual(scenes[0].title, "Cú sốc đầu tiên")
        self.assertIn("--ar 9:16", scenes[0].prompt)
        self.assertEqual(scenes[1].scene_id, "SC02")
        self.assertEqual(scenes[2].scene_id, "SC03")


if __name__ == "__main__":
    unittest.main()
