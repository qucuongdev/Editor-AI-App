"""
idea_generator.py: Ma trận sinh 50 - 100 ý tưởng video đa góc nhìn cho bất kỳ chủ đề/từ khóa nào.
Phân loại theo 5 góc độ tâm lý học hành vi người xem (Hooks):
1. Bí ẩn & Góc khuất
2. Lời khuyên & Sai lầm
3. Tranh cãi & Phản biện
4. Kể chuyện & Case study
5. Châm biếm & Hài hước
"""

from typing import Any, Dict, List, Optional

ANGLE_METADATA: Dict[str, Dict[str, str]] = {
    "all": {
        "label": "Tất cả ý tưởng",
        "icon": "🌟",
        "desc": "Toàn bộ danh sách ý tưởng đa góc nhìn",
    },
    "mystery": {
        "label": "Bí ẩn & Góc khuất",
        "icon": "🎯",
        "desc": "Khai thác sự thật chưa kể, thuyết âm mưu và bí mật ít người biết",
    },
    "advice": {
        "label": "Lời khuyên & Sai lầm",
        "icon": "💡",
        "desc": "Chỉ ra sai lầm chí mạng, bí quyết thực chiến và phương pháp tối ưu",
    },
    "debate": {
        "label": "Tranh cãi & Phản biện",
        "icon": "⚡",
        "desc": "Đặt câu hỏi ngược, bóc tách vấn đề và góc nhìn trái chiều",
    },
    "story": {
        "label": "Kể chuyện & Tình huống",
        "icon": "📖",
        "desc": "Kể lại câu chuyện chân thực, hành trình vượt khó và bài học cuộc đời",
    },
    "humor": {
        "label": "Châm biếm & Giải trí",
        "icon": "😂",
        "desc": "Cách tiếp cận hài hước, dí dỏm và những khoảnh khắc đời thường gần gũi",
    },
}

TEMPLATES_MYSTERY = [
    ("Sự thật chưa từng được tiết lộ đằng sau {topic}", "Bóc tách những góc khuất và thông tin bí mật mà số đông chưa từng được nghe về {topic}."),
    ("Tại sao 90% mọi người đang hiểu sai hoàn toàn về {topic}?", "Chỉ ra những ngộ nhận kinh điển khiến người xem giật mình khi biết sự thật."),
    ("Bí mật cấm kỵ về {topic} mà giới chuyên gia không muốn bạn biết", "Khám phá quy luật ngầm và cách vận hành thật sự bên trong {topic}."),
    ("Điều gì sẽ xảy ra nếu {topic} biến mất hoàn toàn vào ngày mai?", "Giả thuyết kịch tính về viễn cảnh tương lai và tác động trực tiếp đến cuộc sống."),
    ("Những dấu hiệu ngầm cho thấy {topic} đang âm thầm thay đổi thế giới", "Các chỉ báo bất ngờ chứng minh sự chuyển dịch lớn của {topic}."),
    ("Hồ sơ đen: Mặt tối của {topic} mà bạn cần phải đề phòng", "Cảnh báo những rủi ro tiềm ẩn và các chiêu trò liên quan đến {topic}."),
    ("Khám phá quy luật ngầm ít người biết bên trong {topic}", "Phân tích logic bí mật giúp bạn hiểu rõ bản chất cốt lõi của {topic}."),
    ("Sự thật gây sốc về nguồn gốc ra đời của {topic}", "Hành trình khởi đầu đầy bất ngờ và những góc khuất lịch sử của {topic}."),
    ("Tại sao người thành công không bao giờ nói cho bạn bí mật này về {topic}?", "Bài học thâm sâu về tư duy và chiến lược dài hạn xoay quanh {topic}."),
    ("Giải mã hiện tượng {topic}: Trào lưu nhất thời hay cuộc cách mạng?", "Đánh giá khách quan về tiềm năng thật sự và tương lai của {topic}."),
    ("Bí ẩn chưa có lời giải đáp về {topic} khiến nhiều người trăn trở", "Những câu hỏi hóc búa nhất và góc nhìn đa chiều về {topic}."),
    ("Góc khuất đằng sau sự bùng nổ kỳ lạ của {topic}", "Phân tích dòng tiền, động lực truyền thông và sự thật của {topic}."),
    ("Ai là người thực sự đứng sau giật dây xu hướng {topic}?", "Truy tìm những nhân tố chủ chốt và động cơ ngầm của sự việc."),
    ("Sự thật rợn người ít ai dám đối diện về {topic}", "Những góc nhìn gai góc, chân thực đến mức đáng suy ngẫm."),
    ("Điều kỳ lạ gì đang diễn ra với {topic} ngay lúc này?", "Cập nhật những diễn biến bất thường mới nhất mà bạn cần chú ý."),
]

TEMPLATES_ADVICE = [
    ("3 sai lầm chết người khi tiếp cận {topic} mà bạn phải tránh ngay", "Chỉ rõ các bẫy phổ biến nhất và hướng dẫn cách phòng tránh thiệt hại."),
    ("Bí quyết làm chủ {topic} chỉ trong 7 ngày cho người mới bắt đầu", "Lộ trình từng bước ngắn gọn, thực tế và dễ áp dụng ngay lập tức."),
    ("Đừng bao giờ dại dột làm điều này với {topic} nếu không muốn hối hận", "Lời khuyên đắt giá từ những người từng trả giá đắt trong quá khứ."),
    ("5 bước đơn giản giúp bạn nhân đôi hiệu quả từ {topic}", "Quy trình thực chiến giúp tiết kiệm thời gian và tối đa hóa kết quả."),
    ("Cách người thông minh ứng dụng {topic} để bứt phá", "Chiến lược nâng cao và tư duy khác biệt của người đi đầu."),
    ("Quy tắc vàng bạn buộc phải nhớ trước khi chi tiền cho {topic}", "Nguyên tắc bảo vệ túi tiền và tối ưu ngân sách khi liên quan đến {topic}."),
    ("Làm sao để biết bạn đã sẵn sàng bắt đầu với {topic}?", "Bộ câu hỏi kiểm tra năng lực và điều kiện cần trước khi hành động."),
    ("3 thói quen nhỏ giúp bạn vượt trội so với đối thủ trong {topic}", "Những hành động kỷ luật đơn giản tạo nên sự khác biệt khổng lồ."),
    ("Chiến lược tối ưu hóa {topic} dành cho người bận rộn", "Cách sắp xếp thông minh để đạt mục tiêu mà không bị quá tải."),
    ("Những công cụ bí mật giúp bạn làm chủ {topic} nhẹ nhàng", "Giới thiệu các tiện ích và mẹo công nghệ hỗ trợ đắc lực."),
    ("Bài học xương máu: Tôi đã mất trắng vì chủ quan với {topic}", "Chia sẻ trải nghiệm thật để người xem không lặp lại vết xe đổ."),
    ("Cách phân biệt thật - giả trong thị trường {topic}", "Kỹ năng nhận biết lừa đảo và chọn lọc thông tin đáng tin cậy."),
    ("Tư duy đúng đắn nhất về {topic} để không bao giờ bị dắt mũi", "Xây dựng lăng kính phản biện vững chắc trước mọi trào lưu."),
    ("Checklist 5 điều cần chuẩn bị kỹ lưỡng trước khi bắt tay vào {topic}", "Bảng kiểm tra chi tiết để không bỏ sót bất kỳ mắt xích nào."),
    ("Bí kíp biến {topic} thành đòn bẩy thay đổi cuộc sống", "Kế hoạch hành động cụ thể để biến kiến thức thành giá trị thực tế."),
]

TEMPLATES_DEBATE = [
    ("Liệu {topic} có đang là một cái bẫy truyền thông hoàn hảo?", "Đặt câu hỏi phản biện về việc liệu truyền thông có đang thổi phồng {topic} quá mức."),
    ("Phản biện: Tại sao lời khuyên phổ biến về {topic} lại hoàn toàn sai lầm?", "Bẻ gãy những giáo điều cũ kỹ và đưa ra góc nhìn logic hiện đại."),
    ("Tranh cãi nảy lửa: Ai đúng ai sai trong cuộc chiến về {topic}?", "Phân tích 2 luồng quan điểm đối lập và rút ra kết luận sâu sắc."),
    ("Sự thật cay đắng: {topic} đang làm hại hay giúp ích cho bạn?", "Cân nhắc giữa mặt lợi và mặt hại của vấn đề một cách công bằng."),
    ("Đừng nghe chuyên gia: Đây mới là thực tế trần trụi về {topic}", "So sánh giữa lý thuyết suông trên giấy và thực tế ngoài đời sống."),
    ("Có nên tin vào những lời hứa hẹn ngọt ngào về {topic}?", "Vạch trần những kỳ vọng hão huyền và nhìn thẳng vào thực tế."),
    ("Liệu {topic} có sớm bị đào thải trong 3 năm tới?", "Dự báo rủi ro biến mất hoặc bị công nghệ mới thay thế."),
    ("Góc nhìn trái chiều: Điều số đông ghét ở {topic} lại chính là cơ hội vàng", "Tìm kiếm viên ngọc quý trong những định kiến tiêu cực của đám đông."),
    ("Tại sao tôi quyết định dừng lại với {topic}?", "Tâm sự thẳng thắn về lý do buông bỏ một thói quen hoặc xu hướng."),
    ("Sự công bằng nằm ở đâu trong câu chuyện {topic}?", "Bàn về đạo đức, công lý và quyền lợi của các bên liên quan."),
    ("Ảo tưởng sức mạnh về {topic} và cái giá phải trả", "Cảnh tỉnh những ai đang tự mãn hoặc đánh giá quá cao tình hình."),
    ("Bức tranh hai mặt: Điều gì đang bị giấu giếm về {topic}?", "Khám phá sự thật đằng sau những con số hào nhoáng."),
    ("Có phải chúng ta đang quá cuồng nhiệt với {topic}?", "Kêu gọi một khoảng lặng suy ngẫm để lấy lại sự cân bằng."),
    ("Thách thức lớn nhất mà người theo đuổi {topic} phải đối mặt", "Vượt qua rào cản tâm lý và áp lực từ xã hội."),
    ("Ai là kẻ chiến thắng thật sự trong cơn sốt {topic}?", "Nhận diện những người âm thầm hưởng lợi đằng sau sự kiện."),
]

TEMPLATES_STORY = [
    ("Hành trình từ con số 0 đến làm chủ {topic} đầy cảm hứng", "Câu chuyện vượt khó và bài học bền bỉ của một nhân vật có thật."),
    ("Câu chuyện về người đã thay đổi cả cuộc đời nhờ hiểu đúng {topic}", "Kể lại bước ngoặt định mệnh khi một người áp dụng thành công {topic}."),
    ("Ký sự thực tế: Một ngày trải nghiệm trọn vẹn với {topic}", "Góc nhìn chân thực, gần gũi như một thước phim phóng sự ngắn."),
    ("Bài học đắt giá từ cú ngã nhớ đời liên quan đến {topic}", "Câu chuyện kịch tính về sự thất bại và nghị lực đứng dậy làm lại từ đầu."),
    ("Người đàn ông/người phụ nữ đã đánh bại cả hệ thống nhờ {topic}", "Tình tiết hấp dẫn về một cá nhân dám đương đầu với thử thách lớn."),
    ("Chuyện chưa kể về những con người thầm lặng cống hiến cho {topic}", "Tôn vinh những đóng góp không tên nhưng mang ý nghĩa to lớn."),
    ("Từ một ý tưởng điên rồ đến hiện tượng {topic} toàn cầu", "Quá trình ươm mầm và hiện thực hóa một khát vọng phi thường."),
    ("Khoảnh khắc định mệnh khiến tôi thay đổi hoàn toàn suy nghĩ về {topic}", "Một cuộc gặp gỡ bất ngờ đã mở ra tư duy mới mẻ."),
    ("Cuộc đối thoại lúc nửa đêm về {topic} đã cứu rỗi tương lai của tôi", "Những chia sẻ sâu lắng giữa hai thế hệ về giá trị cuộc sống."),
    ("Hành trình 10 năm theo đuổi {topic}: Được gì và mất gì?", "Nhìn lại chặng đường dài với những nụ cười và cả những giọt nước mắt."),
    ("Bí mật đằng sau thành công vang dội của một người bình thường nhờ {topic}", "Cách một người xuất phát điểm thấp vươn lên nhờ kiên trì."),
    ("Cú sốc đầu đời khi tôi bước chân vào thế giới của {topic}", "Những bỡ ngỡ ban đầu và bài học thích nghi nhanh chóng."),
    ("Chuyện tình cờ: Phát hiện chấn động thay đổi tương lai {topic}", "Yếu tố may mắn kết hợp cùng sự nhạy bén của người trong cuộc."),
    ("Lá thư gửi lại: Lời dặn dò quý giá cho những ai đang mê muội {topic}", "Những lời tâm can từ người đi trước dành cho thế hệ nối tiếp."),
    ("Hồi kết của một trào lưu và bài học còn mãi về {topic}", "Đúc kết kinh nghiệm sâu sắc sau khi sóng gió đã đi qua."),
]

TEMPLATES_HUMOR = [
    ("Những pha tự hủy kinh điển của người chơi hệ {topic}", "Tổng hợp những tình huống ngớ ngẩn nhưng cực kỳ phổ biến khiến ai cũng bật cười."),
    ("Kỳ vọng vs Thực tế khi bạn lần đầu thử sức với {topic}", "So sánh hài hước giữa giấc mơ màu hồng và hiện thực phũ phàng."),
    ("Khi bạn cố tỏ ra mình là chuyên gia về {topic} và cái kết", "Mô tả dí dỏm hành vi 'làm màu' của một bộ phận người dùng."),
    ("1001 lý do bao biện hài hước nhất khi thất bại với {topic}", "Điểm danh những cái cớ quen thuộc mà ai cũng từng nghe ít nhất một lần."),
    ("Phản ứng của phụ huynh khi thấy con cái cắm đầu vào {topic}", "Tái hiện khoảng cách thế hệ bằng lăng kính vui vẻ, duyên dáng."),
    ("Một ngày 'hành xác' của người nghiện {topic} sẽ như thế nào?", "Tự trào về những thói quen kỳ quặc nhưng đáng yêu."),
    ("Khi dân nghiệp dư và cao thủ cùng nói chuyện về {topic}", "Màn đối đáp lầy lội làm bật lên sự khác biệt trong tư duy."),
    ("Nếu {topic} là một con người, chắc chắn anh ấy/cô ấy sẽ rất mệt mỏi", "Nhân hóa chủ đề thành một nhân vật hài hước với nhiều nỗi niềm."),
    ("Những câu nói cửa miệng của hội mê {topic} khiến ai cũng phát ngán", "Nhặt những câu quote quen thuộc tạo cảm giác đồng cảm tức thì."),
    ("Làm sao để giải thích {topic} cho bà ngoại hiểu trong 30 giây?", "Cách diễn giải mộc mạc, hóm hỉnh không dùng thuật ngữ đao to búa lớn."),
    ("Cười ra nước mắt với những pha xử lý đi vào lòng đất trong {topic}", "Góc nhìn hài hước giúp xua tan căng thẳng mệt mỏi."),
    ("Cẩm nang 'sống ảo' cực nghệ cùng {topic} cho hội mê check-in", "Mẹo tạo nội dung bắt mắt nhưng vẫn giữ nét duyên dáng."),
    ("Khi ví tiền của bạn gào thét vì bạn lỡ đam mê {topic}", "Tình cảnh viêm màng túi được diễn tả một cách hóm hỉnh."),
    ("Đừng xem video này nếu bạn không muốn cười vỡ bụng vì {topic}", "Chuỗi khoảnh khắc giải trí đỉnh cao về chủ đề."),
    ("Tuyên ngôn bất hủ của những tín đồ trung thành với {topic}", "Những triết lý tếu táo nhưng ngẫm lại thấy vô cùng đúng."),
]

RELIGIOUS_KEYWORDS = {
    "tôn giáo", "ton giao", "đạo phật", "dao phat", "phật giáo", "phat giao",
    "công giáo", "cong giao", "kitô", "kito", "thiên chúa", "thien chua",
    "hồi giáo", "hoi giao", "islam", "ấn độ giáo", "an do giao", "hindu",
    "do thái", "do thai", "judaism", "đạo giáo", "dao giao", "tin lành", "tin lanh",
    "đức tin", "duc tin", "sùng đạo", "sung dao", "cuồng tín", "cuong tin",
    "thánh địa", "thanh dia", "vatican", "mecca", "jerusalem", "tây tạng", "tay tang",
    "kinh thánh", "kinh thanh", "kinh phật", "kinh phat", "quran", "giáo phái", "giao phai",
    "cult", "tâm linh", "tam linh", "tu sĩ", "tu si", "linh mục", "linh muc", "nhà sư", "nha su",
    "thiền định", "thien dinh", "nhân quả", "nhan qua", "nghiệp báo", "nghiep bao",
    "thần học", "than hoc", "hành hương", "hanh huong", "nghi lễ", "nghi le",
    "thánh tích", "thanh tich", "tiên tri", "tien tri", "tử đạo", "tu dao", "dị giáo", "di giao",
    "biển chết", "bien chet", "văn tự cổ", "van tu co", "bản thảo cổ", "cầu nguyện", "cau nguyen", "giác ngộ", "giac ngo",
    "religion", "religious", "faith", "buddhism", "christianity", "hinduism", "bible", "dead sea",
}

TEMPLATES_RELIGION_MYSTERY = [
    ("Bí ẩn các văn tự cổ cấm kỵ từng bị loại khỏi {topic}", "Bóc tách những trang sử bị lãng quên và những tài liệu cổ gây tranh cãi về {topic}."),
    ("Sự thật rợn người đằng sau các nghi lễ cổ xưa và mật mã ẩn giấu trong {topic}", "Khám phá quy luật ngầm và các biểu tượng huyền bí nghìn năm của {topic}."),
    ("Căn phòng bí mật và những tài liệu chưa từng công bố về {topic}", "Những tài liệu tuyệt mật trong kho lưu trữ tôn giáo hé lộ góc nhìn chấn động."),
    ("Giải mã những biểu tượng huyền bí nghìn năm tuổi trong {topic}", "Ý nghĩa thực sự đằng sau các hoa văn, dấu ấn và kiến trúc thiêng liêng của {topic}."),
    ("Phát hiện khảo cổ chấn động làm lung lay các truyền thuyết về {topic}", "Những cuộc khai quật tại thánh địa và các bằng chứng khoa học mới nhất."),
    ("Những thánh tích bí ẩn nhất của {topic} mà khoa học hiện đại chưa thể giải thích", "Các hiện tượng vật lý và sinh học kỳ lạ thách thức mọi định luật tự nhiên."),
    ("Sự thật chưa từng kể về nguồn gốc xuất hiện ban đầu của {topic}", "Hành trình khởi sinh trong gian khó và những biến cố lịch sử ít ai hay biết."),
    ("Bí ẩn cấm địa và những vùng đất linh thiêng ít ai đặt chân đến của {topic}", "Thám hiểm các tu viện cô lập trên đỉnh núi tuyết và hang động cổ xưa."),
    ("Di bản cổ và những dòng chữ bị xóa nhòa trong lịch sử hình thành {topic}", "Bản thảo Biển Chết và những di văn hé lộ sự thật nguyên bản."),
    ("Tại sao những ghi chép cổ xưa này về {topic} từng bị giấu kín hàng thế kỷ?", "Động cơ chính trị và quyền lực đằng sau việc kiểm duyệt kinh sách."),
    ("Những điềm báo và lời sấm truyền huyền bí gắn liền với tương lai {topic}", "Các lời tiên tri cổ đại về vận mệnh nhân loại qua lăng kính tôn giáo."),
    ("Cuộc sống bí ẩn bên trong những tu viện cổ kính nhất của {topic}", "Kỷ luật thép, sự khổ hạnh và thế giới nội tâm của các bậc tu hành chân chính."),
    ("Lăng mộ thất lạc và những huyền thoại chưa có lời giải về các bậc thánh của {topic}", "Hành trình truy tìm nơi an nghỉ cuối cùng của những nhân vật lịch sử vĩ đại."),
    ("Điều gì thực sự xảy ra trong các nghi thức thề nguyện tối mật của {topic}?", "Góc nhìn cận cảnh về nghi lễ tôn giáo thiêng liêng nhất."),
    ("Những sự kiện kỳ bí được ghi chép lại trong biên niên sử của {topic}", "Những hiện tượng phi thường được hàng triệu tín đồ chứng kiến qua nhiều thế hệ."),
]

TEMPLATES_RELIGION_ADVICE = [
    ("3 bài học giác ngộ giúp xoa dịu tâm hồn và giải thoát khổ đau từ {topic}", "Lời dạy cốt lõi giúp con người vượt qua khủng hoảng và tìm thấy bình an nội tại."),
    ("Hiểu đúng về quy luật nhân quả để không lầm đường lạc lối trong {topic}", "Bẻ gãy những hiểu lầm phổ biến và ứng dụng luật nghiệp báo vào đời sống thực tế."),
    ("Nghệ thuật buông bỏ và tĩnh tâm theo lời dạy cốt lõi của {topic}", "Phương pháp rèn luyện tâm trí giúp giảm bớt tham sân si và gánh nặng cuộc sống."),
    ("Cách nhận diện ranh giới giữa đức tin chân chính và sự mê tín dị đoan trong {topic}", "Xây dựng chánh tín sáng suốt, không bị dẫn dắt bởi nỗi sợ hãi mơ hồ."),
    ("Những lời răn bất hủ về lòng từ bi, sự tha thứ và tình yêu thương từ {topic}", "Sức mạnh chuyển hóa của lòng bao dung đối với những tổn thương sâu sắc nhất."),
    ("5 thói quen thiền định và cầu nguyện giúp tâm trí an yên mỗi ngày theo {topic}", "Các bước thực hành tâm linh đơn giản, khoa học dành cho người bận rộn."),
    ("Làm thế nào để giữ vững tâm bất biến giữa dòng đời vạn biến nhờ {topic}?", "Nuôi dưỡng sức mạnh nội tâm kiên cường trước sóng gió và thị phi."),
    ("Bài học sâu sắc về sự khiêm nhường và lòng biết ơn được đúc kết từ {topic}", "Chiếc chìa khóa mở ra cánh cửa hạnh phúc đích thực và các mối quan hệ hòa hợp."),
    ("Lời khuyên vàng để nuôi dưỡng nội tâm vững vàng trước cám dỗ từ {topic}", "Giữ gìn giới luật và phẩm giá trong một xã hội đầy biến động."),
    ("Cách áp dụng triết lý nhân văn của {topic} vào công việc và ứng xử gia đình", "Biến đức tin thành hành động tử tế mỗi ngày thay vì chỉ là lời nói suông."),
    ("3 sai lầm nguy hiểm khi thực hành tâm linh mà nhiều người mắc phải trong {topic}", "Cảnh báo những cái bẫy tự mãn tinh thần và chấp chước sai lệch."),
    ("Bí quyết tìm lại sự cân bằng thân - tâm - trí qua lăng kính của {topic}", "Kết hợp dinh dưỡng thanh đạm, hơi thở và suy ngẫm sâu sắc."),
    ("Đừng vội phán xét: Cách lắng nghe và tôn trọng sự khác biệt đức tin trong {topic}", "Tinh thần hòa hợp, đối thoại cởi mở và xây dựng tình bác ái đại đồng."),
    ("Hành trình tu dưỡng đạo đức và tự soi chiếu bản thân mỗi ngày cùng {topic}", "Chiêm nghiệm lỗi lầm và kiên trì hoàn thiện nhân cách."),
    ("Di sản tinh thần quý giá nhất mà các bậc tiền nhân để lại cho chúng ta qua {topic}", "Đúc kết tinh hoa trí tuệ nghìn năm soi đường cho các thế hệ tương lai."),
]

TEMPLATES_RELIGION_DEBATE = [
    ("Tôn giáo và Khoa học: Cuộc đối đầu lịch sử hay hai mặt của chân lý trong {topic}?", "Phân tích sâu sắc mối quan hệ giữa thực nghiệm khoa học và trải nghiệm tâm linh."),
    ("Lòng sùng đạo chân chính hay Cuồng tín cực đoan: Ranh giới nguy hiểm trong {topic}", "Chỉ ra dấu hiệu cảnh báo khi đức tin bị biến chất thành bạo lực và thù hận."),
    ("Tranh cãi nảy lửa: Ai là người thực sự có quyền định đoạt giáo lý {topic}?", "Cuộc đấu tranh quyền lực và sự phân hóa thành các hệ phái xuyên suốt lịch sử."),
    ("Góc khuất thương mại hóa: Khi niềm tin tâm linh bị lợi dụng để trục lợi trong {topic}", "Vạch trần nạn buôn thần bán thánh và các dịch vụ cầu tài lộc biến tướng."),
    ("Vụ án lịch sử và những cuộc xung đột giáo phái từng gây chấn động về {topic}", "Nhìn lại những vết thương quá khứ để rút ra bài học hòa giải sâu sắc."),
    ("Liệu con người càng văn minh khoa học thì có càng ít niềm tin vào {topic}?", "Góc nhìn xã hội học về tương lai của tôn giáo trong kỷ nguyên trí tuệ nhân tạo."),
    ("Sự đối kháng giữa thần học truyền thống và thuyết tiến hóa xoay quanh {topic}", "Hai hệ thống nhận thức thế giới: Đức tin vào Đấng sáng tạo vs Quy luật chọn lọc tự nhiên."),
    ("Phản biện: Những giáo điều cổ xưa có còn phù hợp với chuẩn mực hiện đại của {topic}?", "Cuộc đối thoại thẳng thắn giữa bảo thủ truyền thống và cải cách tiến bộ."),
    ("Bí ẩn các giáo phái bí mật (Cults) và chiêu bài thao túng tâm lý núp bóng {topic}", "Phân tích tâm lý học về cách các giáo chủ cực đoan tẩy não tín đồ."),
    ("Tranh cãi về quyền lực, tài sản và sự minh bạch tài chính bên trong {topic}", "Vấn đề quản trị các tổ chức tôn giáo lớn trong thế giới hiện đại."),
    ("Đức tin có thể chữa lành bệnh tật hay chỉ là hiệu ứng tâm lý giả dược trong {topic}?", "Các nghiên cứu y khoa về tác động của lời cầu nguyện đối với hệ miễn dịch."),
    ("Cuộc tranh luận không hồi kết: Định mệnh đã an bài hay ý chí tự do quyết định trong {topic}?", "Triết học về nghiệp báo, tiền định và trách nhiệm cá nhân."),
    ("Khi giáo lý truyền thống và nhân quyền hiện đại nảy sinh quan điểm trái chiều trong {topic}", "Tìm kiếm tiếng nói chung giữa đạo đức tôn giáo và tiến bộ xã hội."),
    ("Góc nhìn đa chiều: Tại sao cùng một kinh điển lại dẫn đến những cách hiểu đối lập về {topic}?", "Vấn đề diễn giải ngôn ngữ cổ và bối cảnh lịch sử thời đại."),
    ("Liệu tôn giáo là công cụ kiểm soát xã hội hay ngọn hải đăng của đạo đức trong {topic}?", "Phân tích triết học chính trị từ thời cổ đại đến đương đại."),
]

TEMPLATES_RELIGION_STORY = [
    ("Cuộc đời phi thường và những khổ nạn vượt qua thử thách của bậc sáng lập {topic}", "Thước phim ký sự xúc động về ý chí kiên định và lòng trắc ẩn vô bờ bến."),
    ("Hành trình của người từng vô thần hoài nghi trở thành tín đồ sùng đạo nhất của {topic}", "Bước ngoặt số phận sau một biến cố sinh tử mở ra đức tin sâu sắc."),
    ("Ký sự thánh địa: Những bước chân hành hương đầy xúc động về miền đất thiêng của {topic}", "Ghi lại giọt nước mắt và lòng thành kính của hàng triệu con người cùng hướng về cội nguồn."),
    ("Câu chuyện xúc động về những vị thánh tử vì đạo dám hy sinh tính mạng cho {topic}", "Lòng trung kiên bất khuất bảo vệ chân lý trước lưỡi gươm bạo tàn."),
    ("Khoảnh khắc giác ngộ dưới cội nguồn lịch sử làm thay đổi cả nhân loại của {topic}", "Tái hiện bối cảnh đêm thiêng khi chân lý tối thượng được khai mở."),
    ("Bi kịch lịch sử và sự hồi sinh kỳ diệu của cộng đồng tín đồ {topic}", "Nghị lực kiên cường vượt qua thử thách bách hại để gìn giữ ngọn lửa đức tin."),
    ("Lời trăn trối cuối cùng và di chúc tinh thần bất hủ của bậc đại sư trong {topic}", "Những lời dặn dò thiêng liêng đẫm tình yêu thương trước khi về cõi vĩnh hằng."),
    ("Người đã dùng đức tin và tình thương để cảm hóa bạo lực trong câu chuyện {topic}", "Minh chứng cho sức mạnh của sự bất bạo động và lòng vị tha tuyệt đối."),
    ("Chuyến đi định mệnh đưa một kẻ lạc lối tìm lại ánh sáng lương tri nhờ {topic}", "Sự thức tỉnh tâm can sau những năm tháng chìm đắm trong tội lỗi và tăm tối."),
    ("Những câu chuyện màu nhiệm và sự cứu rỗi kỳ diệu được lưu truyền trong {topic}", "Nhân chứng lịch sử kể lại khoảnh khắc bình yên tìm về giữa giông bão cuộc đời."),
    ("Hành trình vượt ngàn dặm sa mạc và núi tuyết để bảo tồn kinh sách cổ của {topic}", "Sự hy sinh thầm lặng của các bậc học giả để di sản tri thức không bị tro tàn vùi lấp."),
    ("Cuộc gặp gỡ định mệnh giữa hai bậc thầy tâm linh làm thay đổi diện mạo {topic}", "Những cuộc đàm đạo thâm sâu mở ra thời kỳ hưng thịnh rực rỡ."),
    ("Ký ức về cuộc cải cách tôn giáo làm rung chuyển cả thế giới liên quan đến {topic}", "Lòng dũng cảm của người dám đứng lên chống lại sự tha hóa và thối nát."),
    ("Từ một nhóm nhỏ sơ khai đến tôn giáo quy tụ hàng tỷ tín đồ toàn cầu của {topic}", "Bài học kỳ diệu về sức mạnh của một lý tưởng nhân văn cao đẹp."),
    ("Di nguyện nghìn năm và ngọn lửa niềm tin soi rọi tương lai của {topic}", "Thông điệp bất diệt về hòa bình, tình huynh đệ và sự giải thoát."),
]

TEMPLATES_RELIGION_HUMOR = [
    ("Khi Gen Z đi lễ cầu duyên và cầu may: Những tình huống dở khóc dở cười quanh {topic}", "Góc nhìn hài hước, dí dỏm về thói quen tâm linh của giới trẻ thời công nghệ."),
    ("Những ngộ nhận hài hước nhất của người ngoại đạo khi lần đầu tìm hiểu về {topic}", "Giải tỏa những định kiến sai lầm bằng nụ cười thân thiện và cởi mở."),
    ("Kỳ vọng đi lễ cầu xin giàu sang vs Thực tế luật nhân quả vận hành trong {topic}", "Tiểu phẩm hài hước châm biếm tâm lý 'mua chuộc thần linh' thực dụng."),
    ("Khi phụ huynh bắt con cái ăn chay hoặc kiêng khem nghiêm ngặt theo {topic}", "Những màn đấu trí lầy lội trong mâm cơm gia đình ngập tràn tiếng cười."),
    ("1001 câu hỏi ngây ngô nhưng hóc búa của trẻ con về những điều kỳ diệu trong {topic}", "Sự ngây thơ đáng yêu khiến các bậc phụ huynh và thầy giáo phải toát mồ hôi."),
    ("Những pha 'tự biên tự diễn' kiêng kỵ tâm linh khiến ai nghe xong cũng bật cười về {topic}", "Điểm danh những tục lệ vô căn cứ mà dân gian tự nghĩ ra rồi tự sợ."),
    ("Cách giải thích các nghi lễ trang nghiêm của {topic} bằng ngôn ngữ hài hước đời thường", "Giúp những giáo lý cao siêu trở nên gần gũi, dễ hiểu và thú vị hơn bao giờ hết."),
    ("Khi 'thầy bói dạo' đụng độ người am hiểu giáo lý chân chính của {topic}", "Màn đối đáp thông minh bóc mẽ các chiêu trò lừa đảo mê tín dị đoan."),
    ("Sự khác biệt vui nhộn giữa tín đồ mới nhập môn và các bậc tiền bối kỳ cựu trong {topic}", "Những bỡ ngỡ vụng về ban đầu được tái hiện một cách duyên dáng."),
    ("Những cuộc tranh luận bất phân thắng bại của cư dân mạng về ngày lễ của {topic}", "Tình huống dở khóc dở cười trong các hội nhóm bàn luận về nguồn gốc lễ hội."),
    ("Nỗi lòng của người thích đi lễ thanh tịnh nhưng sợ cảnh chen lấn và khói hương trong {topic}", "Nỗi niềm rất thật của người đi tìm bình yên giữa chốn đông đúc."),
    ("Khi khoa học hiện đại tình cờ chứng minh những lời dạy nghìn năm về {topic} là đúng", "Góc nhìn thú vị khi y học hiện đại xác nhận lợi ích của ăn chay và thiền định."),
    ("Điểm danh những chiêu trò 'thổi giá' đồ lễ tâm linh khiến ai cũng phải lắc đầu về {topic}", "Tiếng cười châm biếm phê phán hiện tượng thương mại hóa nơi cửa thiền."),
    ("Những khoảnh khắc ấm áp và nụ cười bình an giữa chốn thiền môn thanh tịnh của {topic}", "Ghi lại nét đẹp dung dị, hóm hỉnh của cuộc sống tu tập thường nhật."),
    ("Tuyên ngôn sống tử tế và an yên giản dị nhất được đúc kết từ {topic}", "Đúc kết triết lý nhân sinh một cách hóm hỉnh nhưng đọng lại ý nghĩa sâu xa."),
]

FINANCE_KEYWORDS = {
    "tài chính", "tai chinh", "kinh tế", "kinh te", "tiết kiệm", "tiet kiem",
    "chi tiêu", "chi tieu", "tiền bạc", "tien bac", "tiền lương", "tien luong", "đồng lương", "dong luong",
    "lương", "luong", "lạm phát", "lam phat", "bão giá", "bao gia", "sinh tồn", "sinh ton",
    "nợ", "no nan", "nợ nần", "thẻ tín dụng", "the tin dung", "tín dụng", "tin dung",
    "trả góp", "tra gop", "bnpl", "mua trước trả sau",
    "mua nhà", "mua nha", "thuê nhà", "thue nha", "bất động sản", "bat dong san",
    "đầu tư", "dau tu", "chứng khoán", "chung khoan", "cổ phiếu", "co phieu",
    "vàng", "vang", "tiền mặt", "tien mat", "ngân hàng", "ngan hang", "gửi tiết kiệm", "gui tiet kiem",
    "quỹ khẩn cấp", "quy khan cap", "tối giản", "toi gian", "frugal", "loud budgeting",
    "fire", "nghỉ hưu sớm", "nghi huu som", "tự do tài chính", "tu do tai chinh",
    "quản lý tài chính", "quan ly tai chinh", "phá sản", "pha san", "vỡ nợ", "vo no",
    "finance", "money", "saving", "investment", "wealth", "budget", "inflation",
}

TEMPLATES_FINANCE_MYSTERY = [
    ("Lương 15-20 triệu ở thành phố biến mất đi đâu? Bài học đắt giá về {topic}", "Bóc tách những khoản chi phí ngầm và cạm bẫy vô hình của lối sống đô thị khiến bạn rỗng túi về {topic}."),
    ("Cạm bẫy 'Mua trước trả sau' và thẻ tín dụng liên quan đến {topic} khiến bạn nghèo đi", "Vạch trần thuật toán tâm lý khiến bạn chi tiêu vượt khả năng chi trả liên quan đến {topic}."),
    ("5 cạm bẫy tinh vi trong siêu thị và chiêu trò rút ví người tiêu dùng về {topic}", "Cách bố trí gian hàng, ánh sáng và âm nhạc thao túng hành vi mua sắm xoay quanh {topic}."),
    ("Sự thật về lạm phát lối sống: Tại sao thu nhập tăng nhưng ví vẫn rỗng vì {topic}?", "Hiện tượng tâm lý khiến các chi phí không cần thiết tự động phình to theo {topic}."),
    ("Những khoản phí ẩn 'hút cạn máu' tài khoản mà bạn không hề hay biết về {topic}", "Điểm danh phí duy trì, phí dịch vụ và các gói thuê bao định kỳ âm thầm trừ tiền liên quan đến {topic}."),
    ("Bí mật đằng sau các chiêu trò giảm giá 'ảo' trong các ngày hội mua sắm {topic}", "Bóc trần chiêu thức nâng giá rồi gắn mác sale sốc để kích thích lòng tham về {topic}."),
    ("Tại sao 80% người trẻ ở thành phố không có nổi 50 triệu tiết kiệm vì {topic}?", "Phân tích thực trạng áp lực sinh hoạt phí và những thói quen chi tiêu sai lầm trong {topic}."),
    ("Góc khuất của những khóa học làm giàu cấp tốc và đầu tư sinh lời khủng về {topic}", "Cảnh báo những mô hình đa cấp biến tướng và chiêu bài tài chính lừa đảo về {topic}."),
    ("Bí mật dòng tiền: Người giàu thực sự giữ tiền ở đâu trong thời kỳ biến động {topic}?", "Chiến lược phân bổ danh mục tài sản kín tiếng của giới tài phiệt trước biến động {topic}."),
    ("Cú lừa tinh vi của những trào lưu tiêu dùng hào nhoáng trên mạng xã hội quanh {topic}", "Khi bạn đang phải chi tiền chỉ để chứng minh cho người khác thấy mình ổn về {topic}."),
    ("Tại sao càng kiếm được nhiều tiền bạn lại càng cảm thấy bất an trước {topic}?", "Bản chất của vòng xoay áp lực tài chính đô thị và gánh nặng trách nhiệm trong {topic}."),
    ("Sự thật về các gói tài chính: Đâu là bảo vệ thật sự và đâu là 'bẫy' trong {topic}?", "Hướng dẫn đọc hiểu hợp đồng để không mất trắng tiền tích lũy khi xảy ra rủi ro liên quan đến {topic}."),
    ("Những thứ tưởng như là tài sản nhưng thực chất đang là tiêu sản ngốn tiền trong {topic}", "Phân biệt rạch ròi giữa tài sản sinh dòng tiền và gánh nặng bảo dưỡng, khấu hao trong {topic}."),
    ("Bí ẩn tâm lý học tiền bạc: Tại sao bạn luôn hối hận sau mỗi lần chi tiền cho {topic}?", "Cơ chế giải phóng dopamine nhất thời và cảm giác trống rỗng khi mua sắm về {topic}."),
    ("Kịch bản sinh tồn: Điều gì sẽ xảy ra nếu đối mặt với khủng hoảng {topic} kéo dài?", "Dự báo các kịch bản thị trường và cách chuẩn bị phao cứu sinh cho gia đình trước nguy cơ {topic}."),
]

TEMPLATES_FINANCE_ADVICE = [
    ("Thử thách ăn uống đủ chất với 50.000đ/ngày giữa lòng thành phố đắt đỏ cùng {topic}", "Kế hoạch thực đơn khoa học, rẻ, ngon và mẹo đi chợ đầu mối cho {topic}."),
    ("Bí kíp săn thực phẩm giảm giá sau 20h tại siêu thị giúp tiết kiệm tiền triệu về {topic}", "Chiến lược đi chợ thông minh dành cho dân văn phòng và gia đình trẻ về {topic}."),
    ("Quy tắc '72 giờ đóng băng' cứu rỗi túi tiền khỏi những cơn bốc đồng xoay quanh {topic}", "Phương pháp tâm lý chặn đứng việc mua sắm không cần thiết áp dụng cho {topic}."),
    ("Cách xây dựng quỹ dự phòng khẩn cấp 6 tháng sống sót từ số vốn nhỏ trước {topic}", "Lộ trình từng bước giúp bạn an tâm trước nguy cơ mất việc hoặc khủng hoảng {topic}."),
    ("Quy tắc phân bổ thu nhập 50/30/20 phiên bản nâng cấp thời bão giá cùng {topic}", "Tối ưu hóa các nhóm chi tiêu thiết yếu, mong muốn và tích lũy dài hạn cho {topic}."),
    ("Nghệ thuật 'Loud Budgeting': Công khai từ chối chi tiêu vô bổ không chút ngại ngùng vì {topic}", "Phong cách sống bản lĩnh giúp người trẻ bảo vệ mục tiêu tài chính của mình về {topic}."),
    ("7 cách cắt giảm hóa đơn sinh hoạt đô thị từ 20-30% mà chất lượng sống không đổi nhờ {topic}", "Những mẹo tiết kiệm điện, nước, internet và dịch vụ vận chuyển cực kỳ thực tế trong {topic}."),
    ("Chiến lược trả sạch nợ thẻ tín dụng theo phương pháp Quả cầu tuyết áp dụng cho {topic}", "Quy trình xóa nợ hiệu quả nhất giúp giải phóng tâm lý căng thẳng liên quan đến {topic}."),
    ("Nấu ăn tại nhà chuẩn Meal-prep: Tiết kiệm 4 triệu mỗi tháng và tối ưu hóa {topic}", "Cách chuẩn bị sẵn khẩu phần ăn cho cả tuần trong 2 tiếng cuối tuần cho {topic}."),
    ("Tối ưu hóa thu nhập: 3 kỹ năng tay trái (side-hustle) kiếm thêm thu nhập từ {topic}", "Gợi ý các công việc làm thêm linh hoạt dựa trên thế mạnh cá nhân trong thời kỳ {topic}."),
    ("Bí quyết đàm phán giảm giá phòng trọ và chi phí sinh hoạt khôn ngoan trong {topic}", "Cách tiếp cận chủ nhà chân thành và đạt được mức giá thuê hợp lý trong bối cảnh {topic}."),
    ("Checklist 5 câu hỏi buộc phải tự vấn trước khi quyết định chi tiền cho {topic}", "Bộ lọc tư duy bảo vệ tài khoản khỏi những khoản chi lãng phí về {topic}."),
    ("Lối sống tối giản Frugal Living: Bỏ bớt 70% đồ đạc và ví tiền bất ngờ dày lên cùng {topic}", "Học cách sống đủ đầy với ít đồ đạc hơn và tìm thấy sự tự do nội tâm cùng {topic}."),
    ("Cách quản lý chi tiêu gia đình bằng ứng dụng thông minh không sót một nghìn trong {topic}", "Tự động hóa theo dõi thu chi giúp vợ chồng luôn minh bạch và hòa thuận trong {topic}."),
    ("Chiến lược phòng thủ tài chính cho người làm công ăn lương thời biến động {topic}", "Chuẩn bị sẵn sàng các phương án dự phòng để luôn chủ động trước mọi biến cố {topic}."),
]

TEMPLATES_FINANCE_DEBATE = [
    ("Mua nhà trả góp 25 năm hay thuê nhà trọn đời: Đâu là lựa chọn sáng suốt về {topic}?", "So sánh chi phí cơ hội, áp lực lãi suất thả nổi giữa mua nhà trả góp và thuê nhà trọn đời về {topic}."),
    ("Gen Z nghỉ hưu sớm trước tuổi 35 (trào lưu FIRE): Kế hoạch tự do hay ảo tưởng về {topic}?", "Bóc tách tính khả thi của phong trào FIRE trong bối cảnh lạm phát và chi phí y tế gia tăng về {topic}."),
    ("Nên giữ tiền mặt, mua vàng nhẫn hay gom đất phòng thân thời kỳ bất ổn {topic}?", "Phân tích ưu nhược điểm, tính thanh khoản và độ an toàn của các kênh tích lũy tài sản trong {topic}."),
    ("Tại sao người chăm chỉ tiết kiệm từng đồng lại khó lòng làm giàu từ {topic}?", "Cuộc đối đầu tư duy giữa cắt giảm chi tiêu hà tiện và tập trung gia tăng thu nhập đột phá về {topic}."),
    ("Có nên tiếp tục gửi tiết kiệm ngân hàng khi lãi suất giảm và lạm phát tăng vì {topic}?", "Đánh giá thực tế về việc liệu lãi suất gửi tiết kiệm có bù đắp nổi sự mất giá của đồng tiền về {topic}."),
    ("Tranh cãi nảy lửa: Đầu tư cho bản thân học tập hay chắt bóp từng đồng tích lũy {topic}?", "Ranh giới giữa việc nâng cấp giá trị cá nhân và chi tiêu lãng phí dưới danh nghĩa phát triển {topic}."),
    ("Sống hưởng thụ tuổi trẻ (YOLO) hay Khổ trước sướng sau: Đâu là lối đi đúng trong {topic}?", "Cân bằng giữa việc tận hưởng trải nghiệm hiện tại và chuẩn bị an toàn cho tương lai trong {topic}."),
    ("Đám cưới tiền trăm triệu: Khởi đầu viên mãn hay gánh nặng nợ nần khi đối mặt {topic}?", "Góc nhìn thẳng thắn về chi phí tổ chức đám cưới hoành tráng và áp lực tài chính sau hôn nhân về {topic}."),
    ("Tự kinh doanh khởi nghiệp hay làm công sở ổn định: Cái giá thực sự của tự do trong {topic}?", "So sánh rủi ro phá sản mất vốn và sự an toàn có giới hạn trong môi trường {topic}."),
    ("Có nên vay mượn người thân để làm ăn hay thà vay ngân hàng chịu lãi trong {topic}?", "Phân tích tác động của tiền bạc tới các mối quan hệ gia đình và đạo đức ứng xử trong {topic}."),
    ("Thị trường và cơ hội đầu tư: Đã chạm đáy để mua vào hay vẫn còn rủi ro trong {topic}?", "Nhận định đa chiều từ các chuyên gia kinh tế về chu kỳ biến động của {topic}."),
    ("Tiền bạc có thực sự mua được hạnh phúc hay chỉ là sự tiện nghi trong câu chuyện {topic}?", "Cuộc đối thoại triết học và tâm lý học về mối tương quan giữa sự giàu có và an lạc trong {topic}."),
    ("Nuôi một đứa con ở thành phố tốn bao nhiêu tiền và áp lực tài chính xoay quanh {topic}?", "Áp lực học phí, y tế và chi phí nuôi dạy con cái trong bối cảnh thu nhập đô thị về {topic}."),
    ("Đầu tư thụ động vào chỉ số ETF hay tự lướt sóng: Con đường nào an toàn hơn với {topic}?", "Bằng chứng thực nghiệm lịch sử về tỷ suất sinh lời dài hạn của thị trường tài chính xoay quanh {topic}."),
    ("Có nên công khai tài chính rõ ràng giữa vợ chồng hay giữ quỹ riêng vì {topic}?", "Tìm kiếm tiếng nói chung về sự minh bạch tài chính để gìn giữ hạnh phúc gia đình trong {topic}."),
]

TEMPLATES_FINANCE_STORY = [
    ("Hành trình từ đống nợ thẻ tín dụng 150 triệu đến khoản tiết kiệm nửa tỷ nhờ {topic}", "Câu chuyện có thật về cú ngã tuổi 25 và kỷ luật thép làm lại cuộc đời từ con số âm về {topic}."),
    ("Bài học xương máu mất sạch 500 triệu vì chủ quan lao vào cơn sốt FOMO về {topic}", "Ký sự chân thực về cái bẫy FOMO và bài học đắt giá về quản trị rủi ro trong {topic}."),
    ("Một ngày trải nghiệm thử sống bằng mức chi tiêu của một công nhân để thấu hiểu {topic}", "Thước phim phóng sự cảm động về nghị lực phi thường và sự chắt chiu của những người lao động về {topic}."),
    ("Lá thư gửi lại tuổi 20: 3 sai lầm tiền bạc khiến tôi phải trả giá đắt liên quan đến {topic}", "Tâm sự xúc động từ người đi trước dành cho những bạn trẻ đang bắt đầu bước vào đời cùng {topic}."),
    ("Từ người nghiện mua sắm đến người theo đuổi lối sống tối giản cực đoan nhờ {topic}", "Bước ngoặt số phận khi nhận ra đồ đạc không mang lại hạnh phúc đích thực về {topic}."),
    ("Chuyện khởi nghiệp kinh doanh thất bại và bài học xương máu quản trị dòng tiền {topic}", "Kể lại bài học đắng cay về chi phí mặt bằng, vận hành và quản lý dòng tiền trong {topic}."),
    ("Hành trình 10 năm bám trụ thành phố: Mua được căn nhà đầu tiên sau bao thử thách {topic}", "Câu chuyện vượt khó bền bỉ của một cặp vợ chồng trẻ từ vùng quê lên lập nghiệp cùng {topic}."),
    ("Cú sốc thất nghiệp tuổi 35 và bài học thức tỉnh về quỹ khẩn cấp gia đình trước {topic}", "Biến cố bất ngờ và cách một người trụ cột đứng vững giữa giông bão kinh tế về {topic}."),
    ("Người từng kiếm tiền tỷ mỗi tháng và bài học khi trắng tay vì chủ quan với {topic}", "Bi kịch của sự tự mãn tài chính và hành trình khiêm nhường tìm lại ý nghĩa cuộc sống qua {topic}."),
    ("Chuyện người mẹ một mình nuôi 2 con ăn học thành tài nhờ nghệ thuật chi tiêu {topic}", "Biểu tượng của đức hy sinh và nghệ thuật chi tiêu chắt chiu kỳ diệu của bậc làm cha mẹ về {topic}."),
    ("Bỏ phố về quê lập nghiệp: Giấc mơ màu hồng và hiện thực phũ phàng về sinh kế {topic}", "Chia sẻ thẳng thắn về những khó khăn thực tế khi rời bỏ thành phố để tìm kiếm sự bình yên cùng {topic}."),
    ("Một lần đứng tên vay tiền hộ bạn thân và bài học đắt giá đánh mất tình bạn vì {topic}", "Câu chuyện cảnh tỉnh về việc giữ ranh giới nguyên tắc tiền bạc trong các mối quan hệ xã hội về {topic}."),
    ("Hành trình cai nghiện thẻ tín dụng: Tôi đã cắt nát 4 chiếc thẻ để làm chủ {topic}", "Khoảnh khắc quyết đoán chấm dứt lối sống vay mượn tương lai để làm chủ tài chính trong {topic}."),
    ("Ký sự xóm trọ nghèo: Những ước mơ bình dị giữa guồng quay cơm áo gạo tiền và {topic}", "Ghi lại những khoảnh khắc ấm áp và tình người giữa chốn đô thị phồn hoa về {topic}."),
    ("Khoảnh khắc tôi nhận ra mình đã chính thức tự do tài chính tuổi 40 nhờ {topic}", "Cảm xúc đặc biệt khi các khoản thu nhập thụ động lần đầu tiên vượt qua toàn bộ chi phí sinh hoạt của {topic}."),
]

TEMPLATES_FINANCE_HUMOR = [
    ("Tâm lý học ngày nhận lương: Đầu tháng làm đại gia, cuối tháng ăn mì gói vì {topic}", "Tái hiện hài hước quy trình bốc hơi của đồng lương khiến ai xem cũng thấy bóng dáng mình trong {topic}."),
    ("Khi thông báo trừ tiền nợ thẻ tín dụng đến đúng vào lúc vui vẻ nhất vì {topic}", "Tiểu phẩm hài hước châm biếm nỗi sợ kinh điển của dân văn phòng đô thị về {topic}."),
    ("Kỳ vọng săn sale tiết kiệm tiền vs Hiện thực chất đống đồ vô dụng ở góc nhà về {topic}", "Màn bóc mẽ thói quen nghiện mua sắm online với những món đồ mua về chỉ để ngắm quanh {topic}."),
    ("1001 lý do bao biện hài hước khi lỡ miệng rủ bạn bè đi ăn lẩu 'tự thưởng' dù đang tiết kiệm {topic}", "Những lý do tự lừa dối bản thân kinh điển của hội người mê ẩm thực trước mục tiêu tiết kiệm {topic}."),
    ("Khi phụ huynh hỏi: 'Đi làm cả năm rồi để dành được bao nhiêu tiền hả con?' quanh câu chuyện {topic}", "Màn ứng biến toát mồ hôi hột trong mâm cơm sum họp ngày Tết khiến cư dân mạng cười nghiêng ngả về {topic}."),
    ("Cảm giác khi muốn tiết kiệm {topic} nhưng bạn bè cứ liên tục gửi link trà sữa", "Cuộc đấu tranh tư tưởng căng thẳng giữa chiếc bụng đói và chiếc ví xẹp lép liên quan đến {topic}."),
    ("Một ngày 'giả vờ làm người giàu' của sinh viên mới lên thành phố và bài học về {topic}", "Những pha check-in sang chảnh đầy hài hước và cái kết dở khóc dở cười về {topic}."),
    ("Khi bạn quyết tâm cai mua sắm và các sàn thương mại điện tử gửi thông báo sale sập sàn về {topic}", "Màn đấu trí lầy lội giữa người tiêu dùng kiên định và các chuyên gia tiếp thị về {topic}."),
    ("Chiếc ví tiền của bạn đang muốn gửi lời cầu cứu gì đến bạn ngay lúc này về {topic}?", "Nhân hóa chiếc ví thành một nhân vật hài hước với những lời than vãn bi thương về {topic}."),
    ("Những pha xử lý 'tiết kiệm đi vào lòng đất' khiến chi phí sửa chữa còn đắt gấp ba quanh {topic}", "Tổng hợp các mẹo tự sửa đồ tại nhà dở khóc dở cười của hội mê DIY quanh {topic}."),
    ("Khi dân kế toán đi ăn uống cùng bạn bè và màn tính tiền chia theo từng mililit quanh {topic}", "Góc nhìn dí dỏm về thói quen nghề nghiệp khiến buổi liên hoan trở nên cười ra nước mắt cùng {topic}."),
    ("Phản ứng của tài khoản ngân hàng khi bạn vừa hứa: 'Từ mai mình nhất định sẽ tiết kiệm {topic}'", "Tiếng thở dài hài hước của số dư tài khoản trước lời hứa suông quen thuộc về {topic}."),
    ("Khi bạn muốn sống tối giản nhưng người thân gửi lên cả một thùng đồ quê gánh vác {topic}", "Tình cảnh dở khóc dở cười khi chiếc tủ lạnh nhỏ bé phải gánh vác cả tình thương gia đình trong {topic}."),
    ("Cười ra nước mắt với những chiêu bài 'né' đi ăn cưới mùa cao điểm vì nỗi lo {topic}", "Nỗi niềm rất thật của người trẻ khi một tháng nhận cả chục tấm thiệp mời đắt đỏ liên quan đến {topic}."),
    ("Tuyên ngôn sống sót qua mùa bão giá: Tiền không tự sinh ra nhưng tự mất đi rất nhanh trong {topic}", "Đúc kết triết lý tài chính tếu táo nhưng ngẫm lại thấy thấm thía vô cùng về {topic}."),
]


def is_religious_topic(topic: str) -> bool:
    """Kiểm tra chủ đề có thuộc lĩnh vực tôn giáo, đức tin, sùng đạo hoặc tranh cãi tâm linh không."""
    if not topic:
        return False
    lower_topic = topic.lower()
    return any(k in lower_topic for k in RELIGIOUS_KEYWORDS)


def is_finance_topic(topic: str) -> bool:
    """Kiểm tra chủ đề có thuộc lĩnh vực tài chính, kinh tế, tiết kiệm hoặc sinh tồn đô thị không."""
    if not topic:
        return False
    lower_topic = topic.lower()
    return any(k in lower_topic for k in FINANCE_KEYWORDS)


def format_topic_clean(topic: str) -> str:
    """Chuẩn hóa chuỗi từ khóa chủ đề."""
    clean = (topic or "").strip()
    clean = " ".join(clean.split())
    return clean or "Chủ Đề Hot"


def generate_video_ideas(topic: str, max_per_angle: int = 15) -> List[Dict[str, Any]]:
    """
    Sinh danh sách 50 - 100 ý tưởng video xoay quanh chủ đề cho trước.
    Tự động áp dụng bộ template chuyên sâu cho tôn giáo hoặc tài chính nếu chủ đề liên quan.
    """
    clean_topic = format_topic_clean(topic)
    ideas: List[Dict[str, Any]] = []
    idea_counter = 1

    # Phân loại ngữ cảnh chuyên sâu
    if is_religious_topic(clean_topic):
        angle_packs = [
            ("mystery", "🎯 Bí ẩn & Góc khuất", TEMPLATES_RELIGION_MYSTERY),
            ("advice", "💡 Lời khuyên & Chiêm nghiệm", TEMPLATES_RELIGION_ADVICE),
            ("debate", "⚡ Tranh cãi & Phản biện", TEMPLATES_RELIGION_DEBATE),
            ("story", "📖 Kể chuyện & Thánh tích", TEMPLATES_RELIGION_STORY),
            ("humor", "😂 Góc nhìn đời thường", TEMPLATES_RELIGION_HUMOR),
        ]
    elif is_finance_topic(clean_topic):
        angle_packs = [
            ("mystery", "🎯 Cạm bẫy & Góc khuất", TEMPLATES_FINANCE_MYSTERY),
            ("advice", "💡 Mẹo sinh tồn & Tiết kiệm", TEMPLATES_FINANCE_ADVICE),
            ("debate", "⚡ Tranh luận & Phản biện", TEMPLATES_FINANCE_DEBATE),
            ("story", "📖 Câu chuyện xương máu", TEMPLATES_FINANCE_STORY),
            ("humor", "😂 Tự trào & Đời thường", TEMPLATES_FINANCE_HUMOR),
        ]
    else:
        angle_packs = [
            ("mystery", "🎯 Bí ẩn & Góc khuất", TEMPLATES_MYSTERY),
            ("advice", "💡 Lời khuyên & Sai lầm", TEMPLATES_ADVICE),
            ("debate", "⚡ Tranh cãi & Phản biện", TEMPLATES_DEBATE),
            ("story", "📖 Kể chuyện & Tình huống", TEMPLATES_STORY),
            ("humor", "😂 Châm biếm & Giải trí", TEMPLATES_HUMOR),
        ]

    for angle_key, angle_label, template_list in angle_packs:
        count = min(len(template_list), max_per_angle)
        for i in range(count):
            tpl_title, tpl_desc = template_list[i]
            title = tpl_title.format(topic=clean_topic)
            desc = tpl_desc.format(topic=clean_topic)
            hook = f"Nếu bạn nghĩ mình đã hiểu hết về {clean_topic}, hãy dừng lại 30 giây để nghe câu chuyện này!"

            ideas.append({
                "id": f"IDEA-{idea_counter:03d}",
                "index": idea_counter,
                "topic": clean_topic,
                "title": title,
                "angle": angle_key,
                "angle_label": angle_label,
                "description": desc,
                "hook_preview": hook,
            })
            idea_counter += 1

    return ideas

