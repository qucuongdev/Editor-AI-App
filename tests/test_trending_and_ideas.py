"""
Unit tests for Google Trends, Idea Generator, and Master Prompt Builder.
"""

import unittest
from unittest.mock import patch, MagicMock

from app.core.trends_collector import (
    clean_html,
    parse_trends_xml,
    fetch_google_trends,
    fetch_platform_trends,
    SUPPORTED_COUNTRIES,
    SUPPORTED_PLATFORMS,
    SUPPORTED_TIME_RANGES,
    FALLBACK_TRENDS_VN,
)
from app.core.idea_generator import (
    generate_video_ideas,
    format_topic_clean,
    is_religious_topic,
    is_finance_topic,
    ANGLE_METADATA,
)
from app.core.prompt_builder import (
    build_master_prompt,
    get_word_count_range,
    DURATION_PRESETS,
    TONE_PRESETS,
    PLATFORM_PRESETS,
)


SAMPLE_TRENDS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss">
  <channel>
    <title>Daily Search Trends</title>
    <item>
      <title>Giá vàng hôm nay</title>
      <ht:approx_traffic>100K+</ht:approx_traffic>
      <description>&lt;b&gt;Tin t&#7913;c gi&#225; v&#224;ng&lt;/b&gt; m&#7899;i nh&#7845;t h&#244;m nay</description>
      <pubDate>Wed, 15 Oct 2026 08:00:00 +0700</pubDate>
      <ht:picture>https://example.com/gold.jpg</ht:picture>
      <ht:news_item>
        <ht:news_item_title>Gi&#225; v&#224;ng t&#259;ng v&#7885;t</ht:news_item_title>
        <ht:news_item_snippet>Th&#7883; tr&#434;&#7853;ng ghi nh&#7853;n m&#7913;c k&#7927; l&#7903;c m&#7899;i</ht:news_item_snippet>
        <ht:news_item_url>https://example.com/news/gold</ht:news_item_url>
        <ht:news_item_source>B&#225;o T&#224;i Ch&#237;nh</ht:news_item_source>
      </ht:news_item>
    </item>
    <item>
      <title>Trí tuệ nhân tạo</title>
      <ht:approx_traffic>50K+</ht:approx_traffic>
      <description>C&#244;ng ngh&#7879; AI</description>
      <pubDate>Wed, 15 Oct 2026 07:00:00 +0700</pubDate>
    </item>
  </channel>
</rss>
""".encode("utf-8")


class TrendsCollectorTests(unittest.TestCase):
    def test_clean_html_removes_tags_and_extra_whitespace(self):
        html = "<b>Tin tức</b> &nbsp; <i>mới</i><br>  hôm nay"
        cleaned = clean_html(html)
        self.assertNotIn("<b>", cleaned)
        self.assertNotIn("<br>", cleaned)
        self.assertIn("Tin tức", cleaned)
        self.assertIn("hôm nay", cleaned)

    def test_parse_trends_xml_extracts_correct_fields(self):
        items = parse_trends_xml(SAMPLE_TRENDS_XML)
        self.assertEqual(len(items), 2)

        first = items[0]
        self.assertEqual(first["rank"], 1)
        self.assertEqual(first["title"], "Giá vàng hôm nay")
        self.assertEqual(first["traffic"], "100K+")
        self.assertEqual(first["picture_url"], "https://example.com/gold.jpg")
        self.assertIn("Giá vàng", first["news_title"])
        self.assertEqual(first["news_source"], "Báo Tài Chính")

        second = items[1]
        self.assertEqual(second["rank"], 2)
        self.assertEqual(second["title"], "Trí tuệ nhân tạo")
        self.assertEqual(second["traffic"], "50K+")

    def test_fetch_google_trends_success_with_mock(self):
        mock_response = MagicMock()
        mock_response.read.return_value = SAMPLE_TRENDS_XML
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            results = fetch_google_trends(geo="VN")
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["title"], "Giá vàng hôm nay")

    def test_fetch_google_trends_fallback_on_network_error(self):
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            results = fetch_google_trends(geo="VN")
            self.assertGreaterEqual(len(results), 4)
            self.assertEqual(results[0]["title"], FALLBACK_TRENDS_VN[0]["title"])

    def test_supported_countries_has_vietnam_and_us(self):
        country_codes = [code for code, _ in SUPPORTED_COUNTRIES]
        self.assertIn("VN", country_codes)
        self.assertIn("US", country_codes)

    def test_supported_platforms_and_time_ranges(self):
        platform_keys = [p[0] for p in SUPPORTED_PLATFORMS]
        for expected in ("all", "google", "youtube", "tiktok", "facebook", "instagram", "threads", "x"):
            self.assertIn(expected, platform_keys)

        time_range_keys = [t[0] for t in SUPPORTED_TIME_RANGES]
        for expected in ("day", "week", "month", "year", "custom"):
            self.assertIn(expected, time_range_keys)

    def test_fetch_platform_trends_social_media(self):
        # TikTok
        tt_items = fetch_platform_trends(platform="tiktok", time_range="day")
        self.assertGreaterEqual(len(tt_items), 5)
        self.assertEqual(tt_items[0]["platform"], "tiktok")
        self.assertEqual(tt_items[0]["metric_label"], "Lượt xem")
        self.assertIn("TikTok", tt_items[0]["platform_name"])

        # YouTube
        yt_items = fetch_platform_trends(platform="youtube", time_range="week")
        self.assertGreaterEqual(len(yt_items), 5)
        self.assertEqual(yt_items[0]["platform"], "youtube")
        self.assertEqual(yt_items[0]["metric_label"], "Lượt xem")

        # Facebook
        fb_items = fetch_platform_trends(platform="facebook", time_range="month")
        self.assertGreaterEqual(len(fb_items), 5)
        self.assertEqual(fb_items[0]["platform"], "facebook")
        self.assertEqual(fb_items[0]["metric_label"], "Tương tác")

        # X (Twitter)
        x_items = fetch_platform_trends(platform="x", time_range="year")
        self.assertGreaterEqual(len(x_items), 5)
        self.assertEqual(x_items[0]["platform"], "x")
        self.assertEqual(x_items[0]["metric_label"], "Tweets")

        # Threads
        th_items = fetch_platform_trends(platform="threads", time_range="day")
        self.assertGreaterEqual(len(th_items), 5)
        self.assertEqual(th_items[0]["platform"], "threads")
        self.assertEqual(th_items[0]["metric_label"], "Bình luận")

        # Instagram
        ig_items = fetch_platform_trends(platform="instagram", time_range="week")
        self.assertGreaterEqual(len(ig_items), 5)
        self.assertEqual(ig_items[0]["platform"], "instagram")
        self.assertEqual(ig_items[0]["metric_label"], "Lượt thích")

    def test_fetch_platform_trends_aggregated_all(self):
        all_items = fetch_platform_trends(platform="all", time_range="day")
        self.assertGreaterEqual(len(all_items), 10)
        platforms_found = set(item["platform"] for item in all_items)
        self.assertIn("tiktok", platforms_found)
        self.assertIn("youtube", platforms_found)
        self.assertIn("x", platforms_found)
        # Check ranks are sequential: 1, 2, 3...
        for idx, item in enumerate(all_items, start=1):
            self.assertEqual(item["rank"], idx)

    def test_fetch_platform_trends_custom_range(self):
        custom_items = fetch_platform_trends(
            platform="youtube",
            time_range="custom",
            start_date="2026-10-01",
            end_date="2026-10-15",
        )
        self.assertGreaterEqual(len(custom_items), 4)
        self.assertEqual(custom_items[0]["platform"], "youtube")

    def test_fetch_platform_trends_geo_localization(self):
        # US: English content
        us_items = fetch_platform_trends(geo="US", platform="youtube", time_range="day")
        self.assertGreaterEqual(len(us_items), 2)
        self.assertIn("Views", us_items[0]["metric_label"])

        # VN: Vietnamese content
        vn_items = fetch_platform_trends(geo="VN", platform="youtube", time_range="day")
        self.assertGreaterEqual(len(vn_items), 2)
        self.assertIn("Lượt xem", vn_items[0]["metric_label"])

        # JP: Japanese content
        jp_items = fetch_platform_trends(geo="JP", platform="youtube", time_range="day")
        self.assertGreaterEqual(len(jp_items), 1)

        # KR: Korean content
        kr_items = fetch_platform_trends(geo="KR", platform="youtube", time_range="day")
        self.assertGreaterEqual(len(kr_items), 1)




class IdeaGeneratorTests(unittest.TestCase):
    def test_format_topic_clean(self):
        self.assertEqual(format_topic_clean("   Trí Tuệ Nhân Tạo   "), "Trí Tuệ Nhân Tạo")
        self.assertEqual(format_topic_clean(""), "Chủ Đề Hot")

    def test_generate_video_ideas_creates_75_ideas_across_5_angles(self):
        ideas = generate_video_ideas("Bất động sản 2026", max_per_angle=15)
        self.assertEqual(len(ideas), 75)

        angles = set(idea["angle"] for idea in ideas)
        expected_angles = {"mystery", "advice", "debate", "story", "humor"}
        self.assertEqual(angles, expected_angles)

        # Check fields of every idea
        for idx, idea in enumerate(ideas, 1):
            self.assertEqual(idea["index"], idx)
            self.assertIn("Bất động sản 2026", idea["title"])
            self.assertTrue(len(idea["description"]) > 10)
            self.assertTrue(idea["id"].startswith("IDEA-"))
            self.assertTrue(len(idea["hook_preview"]) > 10)

    def test_angle_metadata_covers_all_angles(self):
        for angle in ("mystery", "advice", "debate", "story", "humor"):
            self.assertIn(angle, ANGLE_METADATA)
            self.assertIn("label", ANGLE_METADATA[angle])
            self.assertIn("icon", ANGLE_METADATA[angle])

    def test_is_religious_topic_detection(self):
        # Religious keywords should return True
        self.assertTrue(is_religious_topic("Kitô giáo và Bí ẩn Kho lưu trữ Vatican"))
        self.assertTrue(is_religious_topic("Triết lý Phật giáo, luật nhân quả và thiền định"))
        self.assertTrue(is_religious_topic("Hồi giáo và Cuộc hành hương thánh địa Mecca"))
        self.assertTrue(is_religious_topic("Lòng sùng đạo chân chính và ranh giới cuồng tín"))
        self.assertTrue(is_religious_topic("Góc khuất các giáo phái bí ẩn (Cults)"))
        self.assertTrue(is_religious_topic("Bí mật Cuộn sách Biển Chết và văn tự cổ"))
        self.assertTrue(is_religious_topic("Khoa học vs Tôn giáo"))
        self.assertTrue(is_religious_topic("Christianity & Ancient Faith"))
        self.assertTrue(is_religious_topic("Hinduism and Karma"))

        # Non-religious keywords should return False
        self.assertFalse(is_religious_topic("Trí tuệ nhân tạo AI 2026"))
        self.assertFalse(is_religious_topic("Bất động sản chung cư"))
        self.assertFalse(is_religious_topic("Chế độ ăn Keto"))
        self.assertFalse(is_religious_topic(""))

    def test_generate_religious_video_ideas(self):
        topic = "Kitô giáo và Bí ẩn Kho lưu trữ Vatican"
        ideas = generate_video_ideas(topic, max_per_angle=15)
        self.assertEqual(len(ideas), 75)

        # Verify religious-tailored angle labels
        angle_labels = {idea["angle"]: idea["angle_label"] for idea in ideas}
        self.assertEqual(angle_labels["advice"], "💡 Lời khuyên & Chiêm nghiệm")
        self.assertEqual(angle_labels["story"], "📖 Kể chuyện & Thánh tích")
        self.assertEqual(angle_labels["humor"], "😂 Góc nhìn đời thường")

        # Verify religious templates content
        titles_combined = " ".join([idea["title"] for idea in ideas])
        self.assertIn("Bí ẩn các văn tự cổ", titles_combined)
        self.assertIn("giác ngộ", titles_combined)
        self.assertIn("Tôn giáo và Khoa học", titles_combined)

    def test_is_finance_topic_detection(self):
        # Finance keywords should return True
        self.assertTrue(is_finance_topic("Sinh tồn tài chính và chi tiêu thông minh tại thành phố"))
        self.assertTrue(is_finance_topic("Mẹo tiết kiệm chi tiêu gia đình và sinh tồn thời bão giá"))
        self.assertTrue(is_finance_topic("Mua nhà trả góp 25 năm hay thuê nhà trọn đời"))
        self.assertTrue(is_finance_topic("Cạm bẫy thẻ tín dụng và mua trước trả sau"))
        self.assertTrue(is_finance_topic("Nên giữ tiền mặt, mua vàng hay bất động sản thời bất ổn"))
        self.assertTrue(is_finance_topic("Lạm phát lối sống và quản lý đồng lương"))
        self.assertTrue(is_finance_topic("Quỹ khẩn cấp và phong trào FIRE"))
        self.assertTrue(is_finance_topic("Personal finance and frugal living"))

        # Non-finance keywords should return False
        self.assertFalse(is_finance_topic("Khám phá vũ trụ và thiên văn học"))
        self.assertFalse(is_finance_topic("Lịch sử La Mã cổ đại"))
        self.assertFalse(is_finance_topic(""))

    def test_generate_finance_video_ideas(self):
        topic = "Sinh tồn tài chính và chi tiêu thông minh tại thành phố"
        ideas = generate_video_ideas(topic, max_per_angle=15)
        self.assertEqual(len(ideas), 75)

        # Verify finance-tailored angle labels
        angle_labels = {idea["angle"]: idea["angle_label"] for idea in ideas}
        self.assertEqual(angle_labels["mystery"], "🎯 Cạm bẫy & Góc khuất")
        self.assertEqual(angle_labels["advice"], "💡 Mẹo sinh tồn & Tiết kiệm")
        self.assertEqual(angle_labels["debate"], "⚡ Tranh luận & Phản biện")
        self.assertEqual(angle_labels["story"], "📖 Câu chuyện xương máu")
        self.assertEqual(angle_labels["humor"], "😂 Tự trào & Đời thường")

        # Verify finance templates content
        titles_combined = " ".join([idea["title"] for idea in ideas])
        self.assertIn("Lương 15-20 triệu", titles_combined)
        self.assertIn("Mua nhà trả góp", titles_combined)
        self.assertIn("ăn uống đủ chất với 50.000đ", titles_combined)


class PromptBuilderTests(unittest.TestCase):
    def test_get_word_count_range_presets(self):
        min_30, max_30, scenes_30 = get_word_count_range(30)
        self.assertEqual((min_30, max_30), (65, 80))
        self.assertEqual(scenes_30, 3)

        min_60, max_60, scenes_60 = get_word_count_range(60)
        self.assertEqual((min_60, max_60), (135, 160))
        self.assertEqual(scenes_60, 5)

        min_120, max_120, scenes_120 = get_word_count_range(120)
        self.assertEqual((min_120, max_120), (270, 310))
        self.assertEqual(scenes_120, 8)

        # Extended 10 mins (600s)
        min_600, max_600, scenes_600 = get_word_count_range(600)
        self.assertEqual((min_600, max_600), (1350, 1500))
        self.assertEqual(scenes_600, 25)

        # Custom arbitrary duration: 450s (7m30s)
        min_cust, max_cust, scenes_cust = get_word_count_range(450)
        self.assertGreater(min_cust, 900)
        self.assertLess(max_cust, 1300)
        self.assertGreaterEqual(scenes_cust, 20)

    def test_format_duration_display(self):
        from app.core.prompt_builder import format_duration_display
        self.assertEqual(format_duration_display(30), "30 giây")
        self.assertEqual(format_duration_display(60), "1 phút (60 giây)")
        self.assertEqual(format_duration_display(600), "10 phút (600 giây)")
        self.assertEqual(format_duration_display(450), "7 phút 30 giây (450 giây)")

    def test_build_master_prompt_contains_crucial_instructions(self):
        prompt = build_master_prompt(
            topic="Trí tuệ nhân tạo",
            title="3 sai lầm chết người khi dùng AI",
            angle_label="💡 Lời khuyên & Sai lầm",
            duration_seconds=60,
            tone="dramatic",
            platform="shorts",
            include_scenes=True,
            include_image_prompts=True,
        )

        self.assertIn("Trí tuệ nhân tạo", prompt)
        self.assertIn("3 sai lầm chết người khi dùng AI", prompt)
        self.assertIn("1 phút (60 giây)", prompt)
        self.assertIn("135 đến 160 từ tiếng Việt", prompt)
        self.assertIn("Hook 3 Giây Đầu", prompt)
        self.assertIn("SC01", prompt)
        self.assertIn("--ar 9:16", prompt)
        self.assertIn("PHẦN 1: BẢNG PHÂN CẢNH CHI TIẾT", prompt)
        self.assertIn("PHẦN 2: TOÀN BỘ LỜI THOẠI ĐỌC LIÊN TỤC", prompt)

    def test_build_master_prompt_for_youtube_16_9_and_10_minutes(self):
        prompt = build_master_prompt(
            topic="Lịch sử",
            title="Bí mật hoàng gia",
            duration_seconds=600,
            platform="youtube",
            include_scenes=True,
            include_image_prompts=True,
        )
        self.assertIn("--ar 16:9", prompt)
        self.assertIn("10 phút (600 giây)", prompt)
        self.assertIn("1350 đến 1500 từ", prompt)

    def test_multilingual_master_prompt_and_units(self):
        from app.core.prompt_builder import get_language_unit, LANGUAGE_PRESETS

        self.assertIn("từ tiếng Anh", get_language_unit("en"))
        self.assertIn("tiếng Trung", get_language_unit("zh"))
        self.assertIn("tiếng Nhật", get_language_unit("ja"))
        self.assertIn("tiếng Hàn", get_language_unit("ko"))

        # English Prompt
        prompt_en = build_master_prompt(
            topic="Artificial Intelligence",
            title="3 Deadly Mistakes with AI",
            duration_seconds=60,
            language="en",
        )
        self.assertIn("English", prompt_en)
        self.assertIn("words", prompt_en)

        # Japanese Prompt
        prompt_ja = build_master_prompt(
            topic="AI技術",
            title="AIの未来",
            duration_seconds=60,
            language="ja",
        )
        self.assertIn("Japanese", prompt_ja)
        self.assertIn("ký tự", prompt_ja)

        # Chinese Prompt
        prompt_zh = build_master_prompt(
            topic="人工智能",
            title="AI新时代",
            duration_seconds=60,
            language="zh",
        )
        self.assertIn("Chinese", prompt_zh)
        self.assertIn("chữ", prompt_zh)


if __name__ == "__main__":
    unittest.main()
