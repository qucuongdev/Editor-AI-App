import re

def normalize_vietnamese_text(text: str) -> str:
    """
    Chuẩn hóa văn bản tiếng Việt thông minh theo ngữ cảnh:
    - Xử lý chữ 'k' thông minh: 'bệnh K' -> 'bệnh ca', 'vitamin K' -> 'vitamin ca',
      'vàng 18K' -> 'vàng 18 ca', 'video 4K' -> 'video 4 ca', 'K-pop' -> 'kê-pop',
      '50k' -> '50 nghìn', 'k biết / được k' -> 'không biết / được không'.
    - Xử lý các chữ cái y tế: vitamin C -> xê, vitamin B -> bê, viêm gan B/C.
    - Xử lý từ viết tắt công nghệ & địa danh: AI -> A.I, TP.HCM, HN, VN.
    - Xử lý từ lóng, teencode phổ biến: dc/đc -> được, vs -> với, j -> gì, mn -> mọi người, ae -> anh em, sđt -> số điện thoại, sp -> sản phẩm, ntn -> như thế nào.
    - Ký hiệu: % -> phần trăm, $ -> đô la, °C -> độ xê, vnđ -> việt nam đồng.
    - Thời gian, ngày tháng & số điện thoại ngắt nhịp.
    """
    if not text:
        return text

    # 1. Ký hiệu công nghệ, giải trí & âm nhạc
    # Chỉ áp dụng cho các thuật ngữ viết hoa chính xác (Case-sensitive), bảo toàn từ tiếng Việt viết thường
    text = re.sub(r'\bAI\b', 'ây ai', text)
    text = re.sub(r'\bIT\b', 'ai-ti', text)
    text = re.sub(r'\bUI\b', 'u-ai', text)
    text = re.sub(r'\bUX\b', 'u-ích', text)
    text = re.sub(r'\bID\b', 'ai-đi', text)
    text = re.sub(r'\bIP\b', 'ai-pi', text)
    text = re.sub(r'\bPC\b', 'pi-xi', text)
    text = re.sub(r'\bCV\b', 'xi-vi', text)
    text = re.sub(r'\bPR\b', 'pi-a', text)
    text = re.sub(r'\bCEO\b', 'xi-i-ô', text)
    text = re.sub(r'\bCTO\b', 'xi-ti-ô', text)
    text = re.sub(r'\bCFO\b', 'xi-ép-ô', text)
    text = re.sub(r'\bHR\b', 'hát-a', text)
    text = re.sub(r'\bQA\b', 'qui-ây', text)
    text = re.sub(r'\bQC\b', 'qui-xi', text)
    text = re.sub(r'\bATM\b', 'A.T.M', text)
    text = re.sub(r'\bOTP\b', 'O.T.P', text)
    text = re.sub(r'\bSMS\b', 'S.M.S', text)
    text = re.sub(r'\bwi[\-\s]?fi\b', 'oai-phai', text, flags=re.IGNORECASE)
    text = re.sub(r'\bapp\b', 'áp', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwebsite\b', 'oép-sai', text, flags=re.IGNORECASE)
    text = re.sub(r'\bweb\b', 'oép', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpodcast\b', 'pót-cát', text, flags=re.IGNORECASE)
    text = re.sub(r'\btiktok\b', 'tíc-tốc', text, flags=re.IGNORECASE)
    text = re.sub(r'\byoutube\b', 'du túp', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfacebook\b', 'phây búc', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcheck[\-\s]?in\b', 'chéc-in', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(fanpage|fan-page)\b', 'phan-pây', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(ad|admin)\b', 'át-min', text, flags=re.IGNORECASE)

    text = re.sub(r'\b[kK]\-(pop|drama|biz|net|star|show)\b', r'kê-\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[vV]\-pop\b', 'vê-pop', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[jJ]\-pop\b', 'jê-pop', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[cC]\-pop\b', 'xê-pop', text, flags=re.IGNORECASE)

    # 2. Ngữ cảnh y tế & dịch tễ cho chữ K, B, C, D (Phải xử lý TRƯỚC khi xử lý K -> không)
    text = re.sub(r'\b(bệnh|bệnh viện|viện|ung thư|khoa|chẩn đoán|điều trị|bệnh nhân|ca bệnh)\s+[kK]\b', r'\1 ca', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(bị|mắc)\s+[kK]\s+(phổi|gan|vú|dạ dày|xương|não|máu|giáp|tụy|ruột|trực tràng|vòm họng|tử cung|tiền liệt tuyến)\b', r'\1 ca \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcovid[\-\s]?19\b', 'cô-vít 19', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcovid\b', 'cô-vít', text, flags=re.IGNORECASE)
    text = re.sub(r'\bF([0123])\b', r'ép-\1', text)

    def replace_vitamins(m):
        full = m.group(0)
        full = re.sub(r'\bvitamin\b', 'vi-ta-min', full, flags=re.IGNORECASE)
        full = re.sub(r'\b[aA]\b', 'a', full)
        full = re.sub(r'\b[bB](\d+)?\b', lambda x: f'bê {x.group(1)}' if x.group(1) else 'bê', full)
        full = re.sub(r'\b[cC]\b', 'xê', full)
        full = re.sub(r'\b[dD](\d+)?\b', lambda x: f'dê {x.group(1)}' if x.group(1) else 'dê', full)
        full = re.sub(r'\b[eE]\b', 'e', full)
        full = re.sub(r'\b[kK]\b', 'ca', full)
        return full

    text = re.sub(
        r'\bvitamin\s+[a-zA-Z0-9]+(?:\s*(?:,|và|hoặc|\/)\s*[a-zA-Z0-9]+)*\b',
        replace_vitamins,
        text,
        flags=re.IGNORECASE
    )

    def replace_hepatitis(m):
        full = m.group(0)
        full = re.sub(r'\b[aA]\b', 'a', full)
        full = re.sub(r'\b[bB]\b', 'bê', full)
        full = re.sub(r'\b[cC]\b', 'xê', full)
        full = re.sub(r'\b[dD]\b', 'dê', full)
        full = re.sub(r'\b[eE]\b', 'e', full)
        return full

    text = re.sub(
        r'\bviêm gan\s+[aAbBcCdDeE](?:\s*(?:,|và|hoặc|\/)\s*[aAbBcCdDeE])*\b',
        replace_hepatitis,
        text,
        flags=re.IGNORECASE
    )

    # 3. Vàng bạc & Độ phân giải (2K, 4K, 8K, 18K, 24K) - Tránh nhầm với tiền 'k'
    text = re.sub(r'\b(vàng|nhẫn|kiềng|dây chuyền|lắc|bông tai|trang sức)\s+(\d+)\s*[kK]\b', r'\1 \2 ca', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(\d+)\s*[kK]\s*(vàng|gold|karat|trang sức|ý|tây|ta)\b', r'\1 ca \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(10|14|18|24)\s*K\b', r'\1 ca', text)
    text = re.sub(r'\b(độ phân giải|màn hình|video|chuẩn|tivi|tv|clip|phim|ảnh|camera|quay)\s+([248]|16)\s*[kK]\b', r'\1 \2 ca', text, flags=re.IGNORECASE)
    text = re.sub(r'\b([248]|16)\s*[kK]\s*(độ phân giải|màn hình|tivi|tv|video|clip|phim|ảnh|camera|fps)\b', r'\1 ca \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\b([248])K\b', r'\1 ca', text)

    # 4. Cơ quan, Tổ chức & Địa danh viết tắt
    text = re.sub(r'\bTP\.?\s*HCM\b', 'thành phố Hồ Chí Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTP\.?\s*HN\b', 'thành phố Hà Nội', text, flags=re.IGNORECASE)
    text = re.sub(r'\bHN\b', 'Hà Nội', text)
    text = re.sub(r'\bHCM\b', 'Hồ Chí Minh', text)
    text = re.sub(r'\bVN\b', 'Việt Nam', text)
    text = re.sub(r'\bUSD\b', 'đô la Mỹ', text)
    text = re.sub(r'\bUBND\b', 'Ủy ban nhân dân', text)
    text = re.sub(r'\bHĐND\b', 'Hội đồng nhân dân', text)
    text = re.sub(r'\bBCA\b', 'Bộ Công an', text)
    text = re.sub(r'\bBQP\b', 'Bộ Quốc phòng', text)
    text = re.sub(r'\bBGD\b', 'Bộ Giáo dục', text)
    text = re.sub(r'\bBYT\b', 'Bộ Y tế', text)
    text = re.sub(r'\bSYT\b', 'Sở Y tế', text)
    text = re.sub(r'\bBHYT\b', 'bảo hiểm y tế', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBHXH\b', 'bảo hiểm xã hội', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBV\b', 'bệnh viện', text)
    text = re.sub(r'\bBS\b', 'bác sĩ', text)
    text = re.sub(r'\bDS\b', 'dược sĩ', text)
    text = re.sub(r'\bCSGT\b', 'cảnh sát giao thông', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPCCC\b', 'phòng cháy chữa cháy', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTHPT\b', 'trung học phổ thông', text)
    text = re.sub(r'\bTHCS\b', 'trung học cơ sở', text)
    text = re.sub(r'\bĐH\b', 'đại học', text)
    text = re.sub(r'\bCĐ\b', 'cao đẳng', text)

    # 5. Phân số & Số thập phân
    text = re.sub(r'\b1/2\b', '1 phần 2', text)
    text = re.sub(r'\b1/4\b', '1 phần 4', text)
    text = re.sub(r'\b3/4\b', '3 phần 4', text)
    text = re.sub(r'(\d+),(\d+)', r'\1 phẩy \2', text)

    # 6. Ký hiệu phần trăm, nhiệt độ, tiền tệ & đơn vị đo lường mở rộng
    text = re.sub(r'(\d+)\s*%', r'\1 phần trăm', text)
    text = re.sub(r'(\d+)\s*°\s*[cC]\b', r'\1 độ xê', text)
    text = re.sub(r'(\d+)\s*độ\s*[cC]\b', r'\1 độ xê', text)
    text = re.sub(r'\$(\d+)', r'\1 đô la', text)
    text = re.sub(r'(\d+)\s*\$', r'\1 đô la', text)
    text = re.sub(r'(\d+)\s*vnđ\b', r'\1 việt nam đồng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvnđ\b', 'việt nam đồng', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*đ\b', r'\1 đồng', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*tr\b', r'\1 triệu', text, flags=re.IGNORECASE)

    # Đơn vị dung lượng & tần số & tốc độ
    text = re.sub(r'(\d+)\s*km/h\b', r'\1 ki lô mét trên giờ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkm/h\b', 'ki lô mét trên giờ', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*m/s\b', r'\1 mét trên giây', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*kwh\b', r'\1 ki lô oát giờ', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*gb\b', r'\1 ghi ga bai', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*mb\b', r'\1 mê ga bai', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*tb\b', r'\1 tê ra bai', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*ghz\b', r'\1 ghi ga héc', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*mhz\b', r'\1 mê ga héc', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*khz\b', r'\1 ki lô héc', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*hz\b', r'\1 héc', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*w\b', r'\1 oát', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*kw\b', r'\1 ki lô oát', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*v\b', r'\1 vôn', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*mah\b', r'\1 mi li am pe giờ', text, flags=re.IGNORECASE)

    text = re.sub(r'(\d+)\s*kg\b', r'\1 ki lô gam', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*km\b', r'\1 ki lô mét', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*cm\b', r'\1 cen ti mét', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*mm\b', r'\1 mi li mét', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*m2\b', r'\1 mét vuông', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*m3\b', r'\1 mét khối', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*m\b', r'\1 mét', text, flags=re.IGNORECASE)

    # 7. Tiền nghìn (vd: 50k, 100k, sau khi đã loại trừ 18K/24K/4K ở trên)
    text = re.sub(r'(\d+)\s*[kK]\b', r'\1 nghìn', text)

    # 8. Ngày tháng & Giờ giấc
    text = re.sub(r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\1 tháng \2 năm \3', text)
    text = re.sub(r'(\d{1,2})/(\d{1,2})', r'\1 tháng \2', text)
    text = re.sub(r'\b(\d{1,2})\s*[hH]\s*(\d{1,2})\b', r'\1 giờ \2 phút', text)
    text = re.sub(r'\b(\d{1,2})\s*[hH]\b', r'\1 giờ', text)
    text = re.sub(r'\b(\d{1,2}):(\d{2})\b', r'\1 giờ \2 phút', text)

    # 9. Số điện thoại (ngắt cụm 4-3-3 để đọc tự nhiên)
    def format_phone(m):
        raw = m.group(0)
        return f"{raw[:4]} {raw[4:7]} {raw[7:]}"
    text = re.sub(r'\b0[35789]\d{8}\b', format_phone, text)

    # 10. Quan hệ, Xưng hô mạng
    relations = [
        (r'\bny\b', 'người yêu'),
        (r'\bck\b', 'chồng'),
        (r'\bvk\b', 'vợ'),
        (r'\bcr\b', 'cờ-rút'),
        (r'\bcrush\b', 'cờ-rút'),
        (r'\bbx\b', 'bà xã'),
        (r'\box\b', 'ông xã'),
    ]
    for pattern, rep in relations:
        text = re.sub(pattern, rep, text, flags=re.IGNORECASE)

    # 11. Từ viết tắt & Teencode tiếng Việt mở rộng toàn diện
    shorthands = [
        # Cụm viết tắt có gạch chéo cần xử lý trước k đứng đơn lẻ
        (r'\bk/m\b', 'khuyến mãi'),
        (r'\bk/h\b', 'khách hàng'),
        (r'\by/c\b', 'yêu cầu'),
        (r'\byc\b', 'yêu cầu'),
        # Chữ k / K đứng độc lập biểu thị 'không'
        (r'\b[kK]\b', 'không'),
        (r'\b(ko|kh|khg|hông|hong|hem)\b', 'không'),
        (r'\b(dc|đc)\b', 'được'),
        (r'\bvs\b', 'với'),
        (r'\bj\b', 'gì'),
        (r'\b(mn|mng)\b', 'mọi người'),
        (r'\bae\b', 'anh em'),
        (r'\b(sđt|sdt)\b', 'số điện thoại'),
        (r'\bsp\b', 'sản phẩm'),
        (r'\bntn\b', 'như thế nào'),
        (r'\b(bthg)\b', 'bình thường'),
        (r'\b(bjo|bgiờ|bi giờ)\b', 'bây giờ'),
        (r'\b(bnhiu|nhiu|nhìu)\b', 'bao nhiêu'),
        (r'\bmik\b', 'mình'),
        (r'\b(ok|oki|okie|okee|oke)\b', 'ô kê'),
        (r'\bfb\b', 'phây búc'),
        (r'\byt\b', 'du túp'),
        (r'\bzalo\b', 'za-lô'),
        (r'\bcmt\b', 'bình luận'),
        (r'\bib\b', 'nhắn tin'),

        # Teencode & Viết tắt giao tiếp mở rộng
        (r'\bng\b', 'người'),
        (r'\bhnay\b', 'hôm nay'),
        (r'\bhqua\b', 'hôm qua'),
        (r'\bmmai\b', 'ngày mai'),
        (r'\b(tks|thanks)\b', 'cảm ơn'),
        (r'\b(pls|plz)\b', 'làm ơn'),
        (r'\bcx\b', 'cũng'),
        (r'\bms\b', 'mới'),
        (r'\bch\b', 'chưa'),
        (r'\btgian\b', 'thời gian'),
        (r'\bđt\b', 'điện thoại'),
        (r'\bvđ\b', 'vấn đề'),
        (r'\bhđ\b', 'hợp đồng'),
        (r'\bclb\b', 'câu lạc bộ'),
        (r'\bsv\b', 'sinh viên'),
        (r'\bhs\b', 'học sinh'),
        (r'\bgv\b', 'giáo viên'),
        (r'\bnv\b', 'nhân viên'),
        (r'\bgd\b', 'gia đình'),
        (r'\bstt\b', 'số thứ tự'),
        (r'\bstatus\b', 'dòng trạng thái'),
        (r'\b(cap|caption)\b', 'chú thích'),
        (r'\btus\b', 'bài viết'),
        (r'\bqtam\b', 'quan tâm'),
        (r'\bqtrong\b', 'quan trọng'),
        (r'\bncl\b', 'nói chung là'),
        (r'\bđv\b', 'đối với'),
        (r'\bkb\b', 'kết bạn'),
        (r'\btl\b', 'trả lời'),
        (r'\bnhg\b', 'nhưng'),
        (r'\bnt\b', 'nhắn tin'),
        (r'\b(đk|đki)\b', 'đăng ký'),
        (r'\b(sub|subscribe)\b', 'đăng ký'),
        (r'\bshare\b', 'chia sẻ'),
        (r'\blike\b', 'thích'),
        (r'\b(uk|um|uh|uhm|ừm)\b', 'ừ'),
    ]
    for pattern, rep in shorthands:
        text = re.sub(pattern, rep, text, flags=re.IGNORECASE)

    # Chữ 'r' độc lập hoặc sau động từ biểu thị 'rồi'
    text = re.sub(
        r'\b(xong|được|đi|về|ngủ|ăn|biết|hiểu|thấy|mua|bán|làm|tới|đến|ra|vào|lên|xuống|quá|hết)\s+r\b',
        r'\1 rồi',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(r'(?<=\s)r(?=[\s.,!?]|$)', 'rồi', text, flags=re.IGNORECASE)

    # 12. Chuyển chữ hoa dài thành thường (trừ từ viết hoa đã chuẩn hóa)
    def lowercase_match(match):
        word = match.group(0)
        if word in ("A.I", "C.E.O", "V.I.P", "G.D.P", "A.T.M", "O.T.P", "S.M.S"):
            return word
        return word.lower()

    text = re.sub(
        r'\b[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴÝỶỸ]{2,}\b',
        lowercase_match,
        text
    )

    # 13. Xóa ký tự rác / emoji nhưng giữ nguyên dấu câu, chữ, số và ký tự cần thiết
    text = re.sub(r'[^\w\s.,!?/:;"\'()-]', ' ', text)

    # 14. Dọn dẹp khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()

    return text
