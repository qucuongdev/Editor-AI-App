"""
UI Automation tests for TrendingTab and its integration into MainWindow.
Uses PyQt6.QtTest in offscreen mode.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtTest import QTest

from app.ui.trending_tab import TrendingTab
from app.ui.main_window import MainWindow


class TrendingUIAutomationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.mock_trends = [
            {
                "rank": 1,
                "title": "Chủ đề thử nghiệm 1",
                "traffic": "500K+",
                "metric_label": "Tìm kiếm",
                "platform": "google",
                "platform_name": "Google Search",
                "platform_icon": "🔍",
                "pub_date": "",
                "news_title": "Tin tức 1",
                "news_snippet": "Mô tả tin tức 1",
                "news_url": "",
                "news_source": "VnExpress",
                "picture_url": "",
            },
            {
                "rank": 2,
                "title": "Chủ đề thử nghiệm 2",
                "traffic": "100K+",
                "metric_label": "Lượt xem",
                "platform": "tiktok",
                "platform_name": "TikTok Viral",
                "platform_icon": "🎵",
                "pub_date": "",
                "news_title": "Tin tức 2",
                "news_snippet": "Mô tả tin tức 2",
                "news_url": "",
                "news_source": "Tuổi Trẻ",
                "picture_url": "",
            },
        ]
        cls.fetch_patcher = patch(
            "app.ui.trending_tab.fetch_platform_trends",
            return_value=cls.mock_trends
        )
        cls.fetch_patcher.start()
        cls.gemini_patcher = patch("app.config.GEMINI_CONNECTED", False)
        cls.gemini_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.fetch_patcher.stop()
        cls.gemini_patcher.stop()

    def tearDown(self):
        self.app.processEvents()

    def test_trending_tab_initial_state_and_trends_load(self):
        tab = TrendingTab()
        try:
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_TRENDS)
            self.assertEqual(tab.combo_country.currentData(), "VN")
            self.assertTrue(tab.btn_generate_custom.isEnabled())

            # Wait for thread or simulate loaded trends
            if tab._trends_worker:
                tab._trends_worker.wait(1000)
            self.app.processEvents()

            self.assertGreaterEqual(len(tab.current_trends), 2)
            self.assertIn("Chủ đề thử nghiệm 1", tab.current_trends[0]["title"])
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()

    def test_platform_and_time_range_filter_ui_controls(self):
        tab = TrendingTab()
        try:
            # Check default combos
            self.assertEqual(tab.combo_platform_trends.currentData(), "google")
            self.assertEqual(tab.combo_time_range.currentData(), "day")
            self.assertTrue(tab.box_custom_dates.isHidden())

            # Switch platform to TikTok
            idx_tt = tab.combo_platform_trends.findData("tiktok")
            tab.combo_platform_trends.setCurrentIndex(idx_tt)
            self.app.processEvents()
            self.assertEqual(tab.combo_platform_trends.currentData(), "tiktok")

            # Switch time range to custom
            idx_custom = tab.combo_time_range.findData("custom")
            tab.combo_time_range.setCurrentIndex(idx_custom)
            self.app.processEvents()
            self.assertEqual(tab.combo_time_range.currentData(), "custom")
            self.assertFalse(tab.box_custom_dates.isHidden())

            # Test apply date button
            tab.date_start.setDate(QDate(2026, 10, 1))
            tab.date_end.setDate(QDate(2026, 10, 15))
            QTest.mouseClick(tab.btn_apply_date, Qt.MouseButton.LeftButton)
            self.app.processEvents()

            # Switch time range back to month
            idx_month = tab.combo_time_range.findData("month")
            tab.combo_time_range.setCurrentIndex(idx_month)
            if tab._trends_worker:
                tab._trends_worker.wait(1000)
            self.app.processEvents()
            self.assertTrue(tab.box_custom_dates.isHidden())

            # Test Search Trends button
            self.assertTrue(tab.btn_search_trends.isEnabled())
            self.assertIn("Quét Xu Hướng", tab.btn_search_trends.text())
            QTest.mouseClick(tab.btn_search_trends, Qt.MouseButton.LeftButton)
            if tab._trends_worker:
                tab._trends_worker.wait(1000)
            self.app.processEvents()
            self.assertFalse(tab.progress_bar.isVisible())
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()

    def test_custom_keyword_generates_ideas_and_switches_page(self):
        tab = TrendingTab()
        try:
            tab.txt_custom_topic.setText("Bất động sản ven biển")
            QTest.mouseClick(tab.btn_generate_custom, Qt.MouseButton.LeftButton)
            self.app.processEvents()

            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)
            self.assertEqual(len(tab.current_ideas), 75)
            self.assertIn("Bất động sản ven biển", tab.lbl_active_topic.text())

            # Click back to trends
            QTest.mouseClick(tab.btn_back_to_trends, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_TRENDS)
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()

    def test_ideas_filtering_by_angle_and_search(self):
        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("Trí tuệ nhân tạo")
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)
            self.assertEqual(len(tab.current_ideas), 75)

            # Filter by mystery angle
            tab.filter_buttons["mystery"].click()
            self.app.processEvents()
            self.assertEqual(tab.active_angle_filter, "mystery")

            # Search within ideas
            tab.txt_filter_ideas.setText("sai lầm")
            self.app.processEvents()

            # Filter back to all
            tab.filter_buttons["all"].click()
            tab.txt_filter_ideas.clear()
            self.app.processEvents()
            self.assertEqual(tab.active_angle_filter, "all")
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()

    def test_master_prompt_studio_workflow(self):
        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("Du lịch ẩm thực")
            first_idea = tab.current_ideas[0]

            tab.open_prompt_studio(first_idea)
            self.app.processEvents()

            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_PROMPT)
            prompt_text = tab.txt_prompt.toPlainText()
            self.assertIn(first_idea["title"], prompt_text)
            self.assertIn("SC01", prompt_text)
            self.assertIn("--ar 9:16", prompt_text)  # Default shorts

            # Change to 120s
            idx_120 = tab.combo_duration.findData(120)
            tab.combo_duration.setCurrentIndex(idx_120)
            self.app.processEvents()
            prompt_120 = tab.txt_prompt.toPlainText()
            self.assertIn("120 giây", prompt_120)

            # Change to YouTube platform (16:9)
            idx_yt = tab.combo_platform.findData("youtube")
            tab.combo_platform.setCurrentIndex(idx_yt)
            self.app.processEvents()
            prompt_yt = tab.txt_prompt.toPlainText()
            self.assertIn("--ar 16:9", prompt_yt)

            # Change to Custom duration (-1) with 8 mins 30 secs
            idx_custom = tab.combo_duration.findData(-1)
            tab.combo_duration.setCurrentIndex(idx_custom)
            self.app.processEvents()
            self.assertFalse(tab.box_custom_time.isHidden())

            tab.spin_custom_min.setValue(8)
            tab.spin_custom_sec.setValue(30)
            self.app.processEvents()
            prompt_custom = tab.txt_prompt.toPlainText()
            self.assertIn("8 phút 30 giây", prompt_custom)
            self.assertIn("510 giây", prompt_custom)

            # Change language to English
            idx_en = tab.combo_language.findData("en")
            tab.combo_language.setCurrentIndex(idx_en)
            self.app.processEvents()
            prompt_en = tab.txt_prompt.toPlainText()
            self.assertIn("English", prompt_en)
            self.assertIn("words", tab.lbl_word_info.text())

            # Change language to Japanese
            idx_ja = tab.combo_language.findData("ja")
            tab.combo_language.setCurrentIndex(idx_ja)
            self.app.processEvents()
            prompt_ja = tab.txt_prompt.toPlainText()
            self.assertIn("Japanese", prompt_ja)
            self.assertIn("ký tự", tab.lbl_word_info.text())

            # Test Copy to clipboard
            QTest.mouseClick(tab.btn_copy_prompt, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            clipboard_text = self.app.clipboard().text()
            self.assertEqual(clipboard_text, prompt_ja)
            self.assertIn("Đã sao chép", tab.btn_copy_prompt.text())

            # Test back button to ideas
            QTest.mouseClick(tab.btn_back_to_ideas, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()

    def test_suggested_topic_pills_and_religious_idea_generation(self):
        tab = TrendingTab()
        try:
            # Check suggested items count in combo_suggested_topics
            self.assertGreaterEqual(tab.combo_suggested_topics.count(), 8)

            # Find item index for Kitô giáo & Vatican
            idx_kito = -1
            for i in range(tab.combo_suggested_topics.count()):
                if "Kitô giáo" in tab.combo_suggested_topics.itemText(i):
                    idx_kito = i
                    break
            self.assertNotEqual(idx_kito, -1)

            # Select Kitô giáo from combo
            tab.combo_suggested_topics.setCurrentIndex(idx_kito)
            self.app.processEvents()

            # Verify auto-filled custom topic and page transition
            self.assertEqual(tab.txt_custom_topic.text(), "Kitô giáo và Bí ẩn Kho lưu trữ Vatican")
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)
            self.assertEqual(len(tab.current_ideas), 75)
            self.assertIn("Kitô giáo và Bí ẩn Kho lưu trữ Vatican", tab.lbl_active_topic.text())

            # Verify religious idea angle labels in UI
            first_idea = tab.current_ideas[0]
            self.assertIn("Kitô giáo", first_idea["title"])

            # Test opening Prompt Studio from religious idea
            tab.open_prompt_studio(first_idea)
            self.app.processEvents()
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_PROMPT)
            prompt_content = tab.txt_prompt.toPlainText()
            self.assertIn(first_idea["title"], prompt_content)
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()

    def test_suggested_finance_topic_pill_click(self):
        tab = TrendingTab()
        try:
            self.assertGreaterEqual(tab.combo_suggested_topics.count(), 14)

            # Find item for Sinh tồn tài chính thành phố
            idx_finance = -1
            for i in range(tab.combo_suggested_topics.count()):
                if "Sinh tồn tài chính" in tab.combo_suggested_topics.itemText(i):
                    idx_finance = i
                    break
            self.assertNotEqual(idx_finance, -1)

            # Select finance item
            tab.combo_suggested_topics.setCurrentIndex(idx_finance)
            self.app.processEvents()

            # Verify auto-filled topic and page switch
            self.assertEqual(tab.txt_custom_topic.text(), "Sinh tồn tài chính và chi tiêu thông minh tại thành phố")
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)
            self.assertEqual(len(tab.current_ideas), 75)
            self.assertIn("Sinh tồn tài chính", tab.lbl_active_topic.text())

            # Verify finance-tailored angle labels in current_ideas
            angle_labels = {idea["angle"]: idea["angle_label"] for idea in tab.current_ideas}
            self.assertEqual(angle_labels["mystery"], "🎯 Cạm bẫy & Góc khuất")
            self.assertEqual(angle_labels["advice"], "💡 Mẹo sinh tồn & Tiết kiệm")
            self.assertEqual(angle_labels["debate"], "⚡ Tranh luận & Phản biện")

            # Test opening Prompt Studio from finance idea
            first_idea = tab.current_ideas[0]
            tab.open_prompt_studio(first_idea)
            self.app.processEvents()
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_PROMPT)
            self.assertIn(first_idea["title"], tab.txt_prompt.toPlainText())
        finally:
            if tab._trends_worker:
                tab._trends_worker.cancel()
                if tab._trends_worker.isRunning():
                    tab._trends_worker.wait(1000)
            tab.close()

    def test_trending_tab_integrated_in_main_window(self):
        window = MainWindow()
        try:
            # Check stack integration
            self.assertIs(window.stack.widget(3), window.trending_tab)
            self.assertIn("Xu hướng & Ý tưởng", window.btn_nav_trending.text())

            # Click trending navigation button
            window.btn_nav_trending.click()
            self.app.processEvents()
            self.assertEqual(window.stack.currentIndex(), 3)
            self.assertTrue(window.btn_nav_trending.isChecked())

            # Test request_open_tts signal switches to TTSTab (index 2) and populates script text
            test_script = "Đây là kịch bản video viral thử nghiệm nạp vào TTS"
            window.trending_tab.request_open_tts.emit(test_script)
            self.app.processEvents()
            self.assertEqual(window.stack.currentIndex(), 2)
            self.assertTrue(window.btn_nav_tts.isChecked())
            self.assertEqual(window.tts_tab.txt_input.toPlainText(), test_script)

            # Test extract_script_for_tts and _on_open_tts_clicked
            window.trending_tab.selected_idea = {
                "title": "Bí mật tài chính",
                "hook_preview": "Đừng vội mua nhà!",
                "description": "Lời khuyên sinh tồn.",
            }
            script_extracted = window.trending_tab.extract_script_for_tts()
            self.assertIn("Bí mật tài chính", script_extracted)
            self.assertGreater(len(script_extracted), 100)

            # Test text selection priority
            window.trending_tab.txt_prompt.setPlainText("Đoạn thoại đặc biệt do tôi tự bôi đen để đọc thử")
            cursor = window.trending_tab.txt_prompt.textCursor()
            cursor.select(cursor.SelectionType.Document)
            window.trending_tab.txt_prompt.setTextCursor(cursor)
            self.assertEqual(
                window.trending_tab.extract_script_for_tts(),
                "Đoạn thoại đặc biệt do tôi tự bôi đen để đọc thử",
            )
        finally:
            if hasattr(window, "trending_tab") and window.trending_tab._trends_worker:
                window.trending_tab._trends_worker.cancel()
                if window.trending_tab._trends_worker.isRunning():
                    window.trending_tab._trends_worker.wait(1000)
            window.close()


class TrendingGeminiAITests(unittest.TestCase):
    """Kiểm thử tự động cho tính năng Sinh Ý Tưởng Gemini AI & Giao diện 2 Cột của TrendingTab."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.mock_ai_ideas = [
            {
                "id": "GEMINI-001",
                "index": 1,
                "topic": "Sinh tồn tài chính",
                "title": "Bẫy thẻ tín dụng âm thầm bào mòn ví tiền",
                "angle": "mystery",
                "angle_label": "🎯 Cạm bẫy & Góc khuất",
                "description": "Bóc trần cách các ngân hàng và ứng dụng mua trước trả sau kiếm tiền từ sự bất cẩn của bạn.",
                "hook_preview": "90% người trẻ không hề biết họ đang trả gấp đôi tiền cho cốc trà sữa này!",
                "is_ai_generated": True,
            },
            {
                "id": "GEMINI-002",
                "index": 2,
                "topic": "Sinh tồn tài chính",
                "title": "Quy tắc 6 chiếc lọ đã lỗi thời trong năm 2026",
                "angle": "debate",
                "angle_label": "⚡ Tranh cãi & Phản trực giác",
                "description": "Tại sao việc chia nhỏ thu nhập kiểu truyền thống khiến bạn mãi không tích lũy được tài sản lớn.",
                "hook_preview": "Dừng ngay việc chia tiền vào 6 chiếc lọ nếu bạn không muốn mãi nghèo!",
                "is_ai_generated": True,
            },
        ]

    def tearDown(self):
        self.app.processEvents()

    @patch("app.core.gemini_client.generate_video_ideas_with_gemini")
    @patch("app.config.GEMINI_CONNECTED", True)
    @patch("app.config.GEMINI_API_KEY", "test_gemini_api_key_valid")
    def test_gemini_ai_ideas_worker_success(self, mock_gemini_call):
        mock_gemini_call.return_value = self.mock_ai_ideas

        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("Sinh tồn tài chính")
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)

            # Chờ worker hoàn thành
            if tab._gemini_ideas_worker:
                tab._gemini_ideas_worker.wait(2000)
            self.app.processEvents()

            # Xác thực danh sách ý tưởng do AI sinh ra
            self.assertEqual(len(tab.current_ideas), 2)
            self.assertTrue(tab.current_ideas[0]["is_ai_generated"])
            self.assertIn("Bẫy thẻ tín dụng", tab.current_ideas[0]["title"])
            self.assertIn("90% người trẻ", tab.current_ideas[0]["hook_preview"])

            # Xác thực hiển thị trên UI
            self.assertIn("Gemini AI", tab.lbl_active_topic.text())
            self.assertIn("Gemini AI", tab.lbl_ideas_source_badge.text())
            self.assertFalse(tab.progress_ideas.isVisible())

            # Kiểm tra thẻ ý tưởng đầu tiên được render
            card_widget = tab.ideas_layout.itemAt(0).widget()
            self.assertIsNotNone(card_widget)
            card_text = " ".join([lbl.text() for lbl in card_widget.findChildren(QLabel)])
            self.assertIn("Hook 3s đầu", card_text)
            self.assertIn("90% người trẻ", card_text)
            self.assertIn("Gemini AI", card_text)
        finally:
            if tab._gemini_ideas_worker:
                tab._gemini_ideas_worker.cancel()
                if tab._gemini_ideas_worker.isRunning():
                    tab._gemini_ideas_worker.wait(1000)
            tab.close()

    @patch("app.core.gemini_client.generate_video_ideas_with_gemini")
    @patch("app.config.GEMINI_CONNECTED", True)
    @patch("app.config.GEMINI_API_KEY", "test_gemini_api_key_valid")
    def test_gemini_ai_ideas_worker_fallback_on_error(self, mock_gemini_call):
        mock_gemini_call.side_effect = RuntimeError("Quota Exceeded 429")

        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("Bất động sản")
            if tab._gemini_ideas_worker:
                tab._gemini_ideas_worker.wait(2000)
            self.app.processEvents()

            # Khi lỗi, tự động fallback về 75 ý tưởng offline
            self.assertEqual(len(tab.current_ideas), 75)
            self.assertIn("Quota Exceeded", tab.lbl_ideas_status.text())
            self.assertIn("Mẫu Offline", tab.lbl_ideas_source_badge.text())
            self.assertFalse(tab.progress_ideas.isVisible())
        finally:
            if tab._gemini_ideas_worker:
                tab._gemini_ideas_worker.cancel()
                if tab._gemini_ideas_worker.isRunning():
                    tab._gemini_ideas_worker.wait(1000)
            tab.close()

    def test_direct_action_tts_from_idea_card(self):
        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("Tiết kiệm bão giá", force_offline=True)
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)

            tts_receiver = MagicMock()
            tab.request_open_tts.connect(tts_receiver)

            test_idea = {
                "title": "5 thói quen mua sắm ngốn sạch lương",
                "angle": "mystery",
                "description": "Những khoản chi tiêu vô hình hàng ngày.",
            }
            tab._on_direct_tts_from_idea(test_idea)
            self.app.processEvents()

            tts_receiver.assert_called_once()
            script_sent = tts_receiver.call_args[0][0]
            self.assertIn("5 thói quen", script_sent)
            self.assertGreater(len(script_sent), 60)
        finally:
            tab.close()

    def test_master_prompt_split_view_components(self):
        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("AI Video 2026", force_offline=True)
            idea = tab.current_ideas[0]
            tab.open_prompt_studio(idea)
            self.app.processEvents()

            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_PROMPT)

            # Kiểm tra các widget cấu hình ở cột trái
            self.assertTrue(hasattr(tab, "combo_duration"))
            self.assertTrue(hasattr(tab, "combo_platform"))
            self.assertTrue(hasattr(tab, "combo_tone"))
            self.assertTrue(hasattr(tab, "combo_language"))
            self.assertTrue(hasattr(tab, "chk_scenes"))
            self.assertTrue(hasattr(tab, "btn_open_storyboard"))
            self.assertTrue(hasattr(tab, "btn_open_tts"))

            # Kiểm tra các widget xem trước ở cột phải
            self.assertTrue(hasattr(tab, "txt_prompt"))
            self.assertTrue(hasattr(tab, "lbl_word_info"))
            self.assertTrue(hasattr(tab, "btn_copy_prompt"))

            self.assertIn(idea["title"], tab.txt_prompt.toPlainText())
        finally:
            tab.close()

    def test_ideas_page_duration_selector_and_sync(self):
        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("Kinh doanh online", force_offline=True)
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)

            # 1. Kiểm tra tồn tại bộ chọn thời lượng trên Trang Ý Tưởng
            self.assertTrue(hasattr(tab, "combo_ideas_duration"))
            self.assertTrue(hasattr(tab, "box_ideas_custom_time"))
            self.assertEqual(tab.combo_ideas_duration.currentData(), 60)
            self.assertEqual(tab.get_selected_ideas_duration(), 60)
            self.assertTrue(tab.box_ideas_custom_time.isHidden())

            # 2. Đổi sang 30 giây
            idx_30 = tab.combo_ideas_duration.findData(30)
            tab.combo_ideas_duration.setCurrentIndex(idx_30)
            self.app.processEvents()
            self.assertEqual(tab.get_selected_ideas_duration(), 30)

            # 3. Đổi sang Tùy chỉnh (phút / giây)
            idx_custom = tab.combo_ideas_duration.findData(-1)
            tab.combo_ideas_duration.setCurrentIndex(idx_custom)
            self.app.processEvents()
            self.assertFalse(tab.box_ideas_custom_time.isHidden())

            tab.spin_ideas_custom_min.setValue(4)
            tab.spin_ideas_custom_sec.setValue(15)
            self.assertEqual(tab.get_selected_ideas_duration(), 4 * 60 + 15)

            # 4. Chuyển sang Master Prompt Studio -> Thời lượng phải tự động đồng bộ sang
            idea = tab.current_ideas[0]
            tab.open_prompt_studio(idea)
            self.app.processEvents()
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_PROMPT)
            self.assertEqual(tab.combo_duration.currentData(), -1)
            self.assertEqual(tab.spin_custom_min.value(), 4)
            self.assertEqual(tab.spin_custom_sec.value(), 15)
            self.assertFalse(tab.box_custom_time.isHidden())

            # 5. Đổi thời lượng trên Prompt Studio sang 120s rồi quay lại Ideas page -> Tự động đồng bộ ngược lại
            idx_120 = tab.combo_duration.findData(120)
            tab.combo_duration.setCurrentIndex(idx_120)
            self.app.processEvents()

            QTest.mouseClick(tab.btn_back_to_ideas, Qt.MouseButton.LeftButton)
            self.app.processEvents()
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)
            self.assertEqual(tab.combo_ideas_duration.currentData(), 120)
            self.assertEqual(tab.get_selected_ideas_duration(), 120)
            self.assertTrue(tab.box_ideas_custom_time.isHidden())
        finally:
            tab.close()

    def test_direct_actions_use_selected_duration(self):
        tab = TrendingTab()
        try:
            tab.open_ideas_for_topic("Tài chính cá nhân", force_offline=True)
            self.assertEqual(tab.stack.currentIndex(), TrendingTab.PAGE_IDEAS)

            # Chọn thời lượng 30s
            idx_30 = tab.combo_ideas_duration.findData(30)
            tab.combo_ideas_duration.setCurrentIndex(idx_30)
            self.app.processEvents()

            test_idea = {
                "title": "3 bẫy tài chính",
                "angle": "mystery",
                "description": "Chi tiết bẫy tài chính",
            }

            # Test direct storyboard dùng đúng 30s và 3 cảnh
            with patch("app.ui.trending_tab.StoryboardDialog") as mock_storyboard_cls:
                mock_dlg = MagicMock()
                mock_storyboard_cls.return_value = mock_dlg
                tab._on_direct_storyboard_from_idea(test_idea)
                mock_storyboard_cls.assert_called_once()
                call_kwargs = mock_storyboard_cls.call_args[1]
                self.assertEqual(call_kwargs.get("duration_seconds"), 30)
                self.assertEqual(call_kwargs.get("scene_count"), 3)

            # Test direct TTS dùng đúng 30s
            with patch("app.core.storyboard_generator.generate_full_script_for_topic", return_value="Script 30s test") as mock_gen_script:
                tab._on_direct_tts_from_idea(test_idea)
                mock_gen_script.assert_called_once()
                call_kwargs = mock_gen_script.call_args[1]
                self.assertEqual(call_kwargs.get("duration_seconds"), 30)
        finally:
            tab.close()

    def test_storyboard_dialog_scene_count_changes_duration(self):
        from app.ui.storyboard_dialog import StoryboardDialog
        dlg = StoryboardDialog(topic="", duration_seconds=60)
        try:
            self.assertEqual(dlg.duration_seconds, 60)

            # Đổi sang 3 cảnh -> 30s
            idx_3 = dlg.combo_scene_count.findData(3)
            dlg.combo_scene_count.setCurrentIndex(idx_3)
            self.app.processEvents()
            self.assertEqual(dlg.duration_seconds, 30)

            # Đổi sang 8 cảnh -> 120s
            idx_8 = dlg.combo_scene_count.findData(8)
            dlg.combo_scene_count.setCurrentIndex(idx_8)
            self.app.processEvents()
            self.assertEqual(dlg.duration_seconds, 120)

            # Đổi sang 10 cảnh -> 180s
            idx_10 = dlg.combo_scene_count.findData(10)
            dlg.combo_scene_count.setCurrentIndex(idx_10)
            self.app.processEvents()
            self.assertEqual(dlg.duration_seconds, 180)
        finally:
            dlg.close()


if __name__ == "__main__":
    unittest.main()

