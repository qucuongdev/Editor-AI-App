"""
UI Automation tests for TrendingTab and its integration into MainWindow.
Uses PyQt6.QtTest in offscreen mode.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtWidgets import QApplication
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

    @classmethod
    def tearDownClass(cls):
        cls.fetch_patcher.stop()

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


if __name__ == "__main__":
    unittest.main()
