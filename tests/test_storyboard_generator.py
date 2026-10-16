"""
Unit tests for storyboard_generator.py core engine.
"""

import json
import unittest
from app.core.storyboard_generator import (
    detect_topic_domain,
    generate_storyboard,
    export_storyboard_to_scenes_json,
    export_storyboard_to_full_script,
    export_storyboard_to_markdown,
    StoryboardScene,
    VISUAL_STYLES,
    TONE_PROFILES,
)
from app.core.video_creator import parse_json_data


class StoryboardGeneratorTests(unittest.TestCase):
    def test_detect_topic_domain(self):
        self.assertEqual(detect_topic_domain("Sinh tồn tài chính thành phố"), "finance")
        self.assertEqual(detect_topic_domain("Mẹo tiết kiệm thời bão giá"), "finance")
        self.assertEqual(detect_topic_domain("Cạm bẫy thẻ tín dụng & trả góp"), "finance")
        self.assertEqual(detect_topic_domain("Bí mật kho lưu trữ Vatican"), "religion")
        self.assertEqual(detect_topic_domain("Triết lý Phật giáo và thiền định"), "religion")
        self.assertEqual(detect_topic_domain("Trí tuệ nhân tạo AI 2026"), "ai")
        self.assertEqual(detect_topic_domain("Du lịch ẩm thực đường phố"), "general")

    def test_generate_storyboard_scene_counts(self):
        # 3 scenes
        scenes_3 = generate_storyboard("Đầu tư thông minh", scene_count=3)
        self.assertEqual(len(scenes_3), 3)
        self.assertEqual(scenes_3[0].scene_id, "SC01")
        self.assertEqual(scenes_3[2].scene_id, "SC03")

        # 5 scenes
        scenes_5 = generate_storyboard("Bí mật cuộn sách biển chết", scene_count=5)
        self.assertEqual(len(scenes_5), 5)
        self.assertEqual(scenes_5[4].scene_id, "SC05")

        # 8 scenes
        scenes_8 = generate_storyboard("Tương lai của AI", scene_count=8)
        self.assertEqual(len(scenes_8), 8)
        self.assertEqual(scenes_8[7].scene_id, "SC08")

        # Bounds: Clamping to 3 min, 10 max
        scenes_min = generate_storyboard("Test min", scene_count=1)
        self.assertEqual(len(scenes_min), 3)

        scenes_max = generate_storyboard("Test max", scene_count=20)
        self.assertEqual(len(scenes_max), 10)

    def test_storyboard_scene_attributes_and_tones(self):
        scenes = generate_storyboard("Mua nhà vs Thuê nhà", scene_count=5, tone="finance", visual_style="cinematic")
        for sc in scenes:
            self.assertTrue(sc.scene_id.startswith("SC"))
            self.assertGreater(len(sc.voiceover), 10)
            self.assertGreater(len(sc.prompt), 20)
            self.assertGreater(sc.duration, 0)
            self.assertIn("cinematic", sc.prompt.lower())

    def test_export_to_scenes_json_and_video_creator_compatibility(self):
        scenes = generate_storyboard("Thao túng tâm lý", scene_count=5, tone="mystery")
        scenes_json = export_storyboard_to_scenes_json(scenes)

        # Parse JSON check
        raw_data = json.loads(scenes_json)
        self.assertEqual(len(raw_data), 5)

        # Compatibility with video_creator.parse_json_data
        parsed = parse_json_data(raw_data, [1, 2, 3, 4, 5])
        self.assertEqual(len(parsed), 5)
        self.assertEqual(parsed[0]["id"], "SC01")
        self.assertEqual(parsed[4]["id"], "SC05")
        self.assertEqual(parsed[4]["end_at"], "AUDIO_END")

    def test_export_full_script_and_markdown(self):
        scenes = generate_storyboard("Khoa học vs Tôn giáo", scene_count=4)
        script = export_storyboard_to_full_script(scenes)
        self.assertIn(scenes[0].voiceover, script)
        self.assertIn(scenes[3].voiceover, script)
        self.assertGreater(len(script.split()), 80)

        md = export_storyboard_to_markdown("Khoa học vs Tôn giáo", scenes)
        self.assertIn("# KỊCH BẢN PHÂN CẢNH VIDEO", md)
        self.assertIn("SC01", md)

    def test_generate_full_script_for_topic(self):
        from app.core.storyboard_generator import generate_full_script_for_topic

        # Test 30s (~3 scenes)
        script_30s = generate_full_script_for_topic("Bí mật tài chính", duration_seconds=30)
        self.assertGreater(len(script_30s.split()), 60)

        # Test 60s (~5 scenes)
        script_60s = generate_full_script_for_topic("Bí mật tài chính", duration_seconds=60)
        self.assertGreater(len(script_60s.split()), 130)

        # Test 120s (~8 scenes)
        script_120s = generate_full_script_for_topic("Bí mật tài chính", duration_seconds=120)
        self.assertGreater(len(script_120s.split()), 200)

    def test_generate_storyboard_with_duration_seconds(self):
        # 60s with 5 scenes -> each scene ~12.0s
        scenes_60s = generate_storyboard("Sinh tồn tài chính", scene_count=5, duration_seconds=60)
        self.assertEqual(len(scenes_60s), 5)
        for sc in scenes_60s:
            self.assertEqual(sc.duration, 12.0)

        # 30s with 3 scenes -> each scene ~10.0s
        scenes_30s = generate_storyboard("Sinh tồn tài chính", scene_count=3, duration_seconds=30)
        self.assertEqual(len(scenes_30s), 3)
        for sc in scenes_30s:
            self.assertEqual(sc.duration, 10.0)


if __name__ == "__main__":
    unittest.main()
