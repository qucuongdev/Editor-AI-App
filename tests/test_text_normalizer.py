import unittest
from app.core.text_normalizer import normalize_vietnamese_text


class TestTextNormalizer(unittest.TestCase):
    """Test suite for context-aware Vietnamese text normalization."""

    def test_empty_and_none(self):
        self.assertEqual(normalize_vietnamese_text(""), "")
        self.assertIsNone(normalize_vietnamese_text(None))

    def test_medical_context_letter_k(self):
        """Bệnh K, viện K, ung thư K phải đọc là 'ca', không được đọc là 'không'."""
        self.assertEqual(normalize_vietnamese_text("bác tôi bị bệnh K"), "bác tôi bị bệnh ca")
        self.assertEqual(normalize_vietnamese_text("điều trị tại viện K"), "điều trị tại viện ca")
        self.assertEqual(normalize_vietnamese_text("khoa K bệnh viện K"), "khoa ca bệnh viện ca")
        self.assertEqual(normalize_vietnamese_text("bệnh nhân K ung thư K"), "bệnh nhân ca ung thư ca")
        self.assertEqual(normalize_vietnamese_text("chẩn đoán K vú"), "chẩn đoán ca vú")
        self.assertEqual(normalize_vietnamese_text("bị K phổi giai đoạn 2"), "bị ca phổi giai đoạn 2")
        self.assertEqual(normalize_vietnamese_text("mắc K gan"), "mắc ca gan")

    def test_vitamins_and_diseases(self):
        """Vitamin A, B, C, D, E, K và viêm gan B, C."""
        self.assertEqual(normalize_vietnamese_text("uống vitamin K"), "uống vi-ta-min ca")
        self.assertEqual(normalize_vietnamese_text("uống vitamin C"), "uống vi-ta-min xê")
        self.assertEqual(normalize_vietnamese_text("vitamin K và C"), "vi-ta-min ca và xê")
        self.assertEqual(normalize_vietnamese_text("vitamin B12 và D3"), "vi-ta-min bê 12 và dê 3")
        self.assertEqual(normalize_vietnamese_text("viêm gan B và C"), "viêm gan bê và xê")

    def test_karat_and_resolution(self):
        """Vàng 18K/24K và độ phân giải 2K/4K/8K phải đọc là 'ca', không phải tiền hay 'không'."""
        self.assertEqual(normalize_vietnamese_text("nhẫn vàng 18K"), "nhẫn vàng 18 ca")
        self.assertEqual(normalize_vietnamese_text("kiềng vàng 24K"), "kiềng vàng 24 ca")
        self.assertEqual(normalize_vietnamese_text("độ phân giải 4K"), "độ phân giải 4 ca")
        self.assertEqual(normalize_vietnamese_text("màn hình 2K"), "màn hình 2 ca")
        self.assertEqual(normalize_vietnamese_text("video 8K siêu nét"), "video 8 ca siêu nét")

    def test_money_and_currency(self):
        """50k, 100k -> 50 nghìn, 100 nghìn; $100 -> 100 đô la; 50vnđ -> 50 việt nam đồng."""
        self.assertEqual(normalize_vietnamese_text("cốc trà đá 5k"), "cốc trà đá 5 nghìn")
        self.assertEqual(normalize_vietnamese_text("giá 50k"), "giá 50 nghìn")
        self.assertEqual(normalize_vietnamese_text("hết 100k"), "hết 100 nghìn")
        self.assertEqual(normalize_vietnamese_text("500k vnđ"), "500 nghìn việt nam đồng")
        self.assertEqual(normalize_vietnamese_text("giá $100"), "giá 100 đô la")
        self.assertEqual(normalize_vietnamese_text("100$"), "100 đô la")

    def test_negation_shorthands(self):
        """k, ko, kh, khg độc lập -> không. Từ chứa k (kem, kẹo, khi) không bị ảnh hưởng."""
        self.assertEqual(normalize_vietnamese_text("tôi k biết"), "tôi không biết")
        self.assertEqual(normalize_vietnamese_text("làm đc k?"), "làm được không?")
        self.assertEqual(normalize_vietnamese_text("k, tôi ko đi"), "không, tôi không đi")
        self.assertEqual(normalize_vietnamese_text("k. Bạn có đi ko?"), "không. Bạn có đi không?")
        # Không được làm hỏng từ vựng tiếng Việt có chứa chữ k
        self.assertEqual(normalize_vietnamese_text("ăn kẹo kem"), "ăn kẹo kem")
        self.assertEqual(normalize_vietnamese_text("khi nào về"), "khi nào về")
        self.assertEqual(normalize_vietnamese_text("đeo kính râm"), "đeo kính râm")

    def test_music_and_entertainment(self):
        """K-pop, K-drama, V-pop."""
        self.assertEqual(normalize_vietnamese_text("nhạc K-pop"), "nhạc kê-pop")
        self.assertEqual(normalize_vietnamese_text("xem K-drama"), "xem kê-drama")
        self.assertEqual(normalize_vietnamese_text("bài hát V-pop"), "bài hát vê-pop")

    def test_teencode_and_abbreviations(self):
        """mn, ae, sđt, sp, ntn, vs, j, ib, cmt, ok."""
        self.assertEqual(normalize_vietnamese_text("chào mn và ae"), "chào mọi người và anh em")
        self.assertEqual(normalize_vietnamese_text("đi vs ai"), "đi với ai")
        self.assertEqual(normalize_vietnamese_text("làm j thế"), "làm gì thế")
        self.assertEqual(normalize_vietnamese_text("sđt của mik"), "số điện thoại của mình là".replace(" là", ""))
        self.assertEqual(normalize_vietnamese_text("ib cho shop"), "nhắn tin cho shop")
        self.assertEqual(normalize_vietnamese_text("để lại cmt"), "để lại bình luận")
        self.assertEqual(normalize_vietnamese_text("ok bạn"), "ô kê bạn")

    def test_symbols_and_numbers(self):
        """%, °C, kg, km, số điện thoại, giờ giấc, AI."""
        self.assertEqual(normalize_vietnamese_text("giảm giá 50%"), "giảm giá 50 phần trăm")
        self.assertEqual(normalize_vietnamese_text("37°C"), "37 độ xê")
        self.assertEqual(normalize_vietnamese_text("10kg gạo"), "10 ki lô gam gạo")
        self.assertEqual(normalize_vietnamese_text("10km"), "10 ki lô mét")
        self.assertEqual(normalize_vietnamese_text("lúc 8h30"), "lúc 8 giờ 30 phút")
        self.assertEqual(normalize_vietnamese_text("công nghệ AI"), "công nghệ A.I")

    def test_social_relations_and_communication_expansion(self):
        """ny, ck, vk, cr, bx, ox, ng, hnay, hqua, tks, cx, ms, ch, r."""
        self.assertEqual(normalize_vietnamese_text("đi chơi vs ny"), "đi chơi với người yêu")
        self.assertEqual(normalize_vietnamese_text("ck và vk"), "chồng và vợ")
        self.assertEqual(normalize_vietnamese_text("cr của tôi"), "cờ-rút của tôi")
        self.assertEqual(normalize_vietnamese_text("nhiều ng tham gia"), "nhiều người tham gia")
        self.assertEqual(normalize_vietnamese_text("hnay trời đẹp"), "hôm nay trời đẹp")
        self.assertEqual(normalize_vietnamese_text("hqua mới về"), "hôm qua mới về")
        self.assertEqual(normalize_vietnamese_text("tks bạn nhé"), "cảm ơn bạn nhé")
        self.assertEqual(normalize_vietnamese_text("tôi cx thế"), "tôi cũng thế")
        self.assertEqual(normalize_vietnamese_text("vừa ms tới"), "vừa mới tới")
        self.assertEqual(normalize_vietnamese_text("ch ăn cơm"), "chưa ăn cơm")
        self.assertEqual(normalize_vietnamese_text("làm xong r"), "làm xong rồi")
        self.assertEqual(normalize_vietnamese_text("về r à"), "về rồi à")

    def test_administrative_and_organizations(self):
        """UBND, HĐND, BHYT, BHXH, CSGT, PCCC, ĐH, CĐ, THPT."""
        self.assertEqual(normalize_vietnamese_text("nộp đơn tại UBND"), "nộp đơn tại Ủy ban nhân dân")
        self.assertEqual(normalize_vietnamese_text("thẻ BHYT"), "thẻ bảo hiểm y tế")
        self.assertEqual(normalize_vietnamese_text("đóng BHXH"), "đóng bảo hiểm xã hội")
        self.assertEqual(normalize_vietnamese_text("gặp CSGT"), "gặp cảnh sát giao thông")
        self.assertEqual(normalize_vietnamese_text("lực lượng PCCC"), "lực lượng phòng cháy chữa cháy")
        self.assertEqual(normalize_vietnamese_text("sinh viên ĐH"), "sinh viên đại học")

    def test_tech_and_internet_terms(self):
        """wifi, atm, otp, app, web, podcast, tiktok, check-in."""
        self.assertEqual(normalize_vietnamese_text("bắt wifi"), "bắt oai-phai")
        self.assertEqual(normalize_vietnamese_text("rút tiền tại cây ATM"), "rút tiền tại cây A.T.M")
        self.assertEqual(normalize_vietnamese_text("nhập mã OTP"), "nhập mã O.T.P")
        self.assertEqual(normalize_vietnamese_text("tải app mới"), "tải áp mới")
        self.assertEqual(normalize_vietnamese_text("nghe podcast"), "nghe pót-cát")
        self.assertEqual(normalize_vietnamese_text("video tiktok"), "video tíc-tốc")
        self.assertEqual(normalize_vietnamese_text("chụp ảnh check-in"), "chụp ảnh chéc-in")
        self.assertEqual(normalize_vietnamese_text("dân IT"), "dân ai-ti")

    def test_measurements_and_decimals_and_fractions(self):
        """km/h, kwh, gb, mb, 1/2, 2,5kg."""
        self.assertEqual(normalize_vietnamese_text("chạy 60km/h"), "chạy 60 ki lô mét trên giờ")
        self.assertEqual(normalize_vietnamese_text("hết 100kwh"), "hết 100 ki lô oát giờ")
        self.assertEqual(normalize_vietnamese_text("thẻ nhớ 64gb"), "thẻ nhớ 64 ghi ga bai")
        self.assertEqual(normalize_vietnamese_text("uống 1/2 cốc"), "uống 1 phần 2 cốc")
        self.assertEqual(normalize_vietnamese_text("nặng 2,5kg"), "nặng 2 phẩy 5 ki lô gam")

    def test_epidemic_terms(self):
        """Covid-19, F0, F1."""
        self.assertEqual(normalize_vietnamese_text("dịch Covid-19"), "dịch cô-vít 19")
        self.assertEqual(normalize_vietnamese_text("cách ly F0 và F1"), "cách ly ép-0 và ép-1")

    def test_medical_and_request_shorthands(self):
        """SYT, BV, BS, DS, y/c, k/m."""
        self.assertEqual(normalize_vietnamese_text("báo cáo SYT"), "báo cáo Sở Y tế")
        self.assertEqual(normalize_vietnamese_text("khám tại BV Bạch Mai"), "khám tại bệnh viện Bạch Mai")
        self.assertEqual(normalize_vietnamese_text("gặp BS chuyên khoa"), "gặp bác sĩ chuyên khoa")
        self.assertEqual(normalize_vietnamese_text("hỏi ý kiến DS tư vấn"), "hỏi ý kiến dược sĩ tư vấn")
        self.assertEqual(normalize_vietnamese_text("theo y/c khách hàng"), "theo yêu cầu khách hàng")
        self.assertEqual(normalize_vietnamese_text("hàng k/m đặc biệt"), "hàng khuyến mãi đặc biệt")

    def test_kokoro_vietnamese_vowel_phonemization(self):
        """Từ 'y' (y tế, đông y...), 'u' (khối u), 'e' (e ngại) không bị đọc thành tiếng Anh (/waɪ/, /juː/, /iː/)."""
        import vig2p
        from app.core.kokoro_engine import _patch_vig2p_for_vietnamese
        _patch_vig2p_for_vietnamese()

        g2p = vig2p.VietnameseG2P()

        # 1. Từ 'y' trong ngữ cảnh y tế và đời sống: phát âm /i/ (ˈi), không chứa wˈaɪ (quai)
        p_bhyt = g2p("đóng bảo hiểm y tế")
        self.assertNotIn("wˈaɪ", p_bhyt, "Từ 'y' trong 'y tế' không được đọc là /waɪ/ (quai)")
        self.assertIn("ˈi", p_bhyt, "Từ 'y' trong 'y tế' phải được phát âm là /i/")

        p_ykhoa = g2p("bác sĩ y khoa")
        self.assertNotIn("wˈaɪ", p_ykhoa)
        self.assertIn("ˈi", p_ykhoa)

        p_dongy = g2p("thuốc đông y")
        self.assertNotIn("wˈaɪ", p_dongy)
        self.assertIn("ˈi", p_dongy)

        # 2. Từ 'u' trong khối u, u xơ: phát âm /u/ (ˈu), không chứa jˈuː (diu)
        p_khoiu = g2p("khối u xơ")
        self.assertNotIn("jˈuː", p_khoiu, "Từ 'u' trong 'khối u' không được đọc là /juː/ (diu)")
        self.assertIn("ˈu", p_khoiu, "Từ 'u' trong 'khối u' phải được phát âm là /u/")

        # 3. Từ 'e' trong e ngại, e dè: phát âm /ɛ/ (ˈɛ), không chứa ˈiː (i)
        p_engai = g2p("e ngại và e dè")
        self.assertNotIn("ˈiː", p_engai, "Từ 'e' trong 'e ngại' không được đọc là /iː/")
        self.assertIn("ˈɛ", p_engai, "Từ 'e' trong 'e ngại' phải được phát âm là /ɛ/")


if __name__ == "__main__":
    unittest.main()
