#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storyboard_generator.py: Bộ sinh kịch bản chi tiết và tự động phân cảnh (AI Storyboard Generator).

Hỗ trợ:
- Phân tích chủ đề (Tài chính, Tôn giáo, Bí ẩn, Công nghệ, Đời sống...)
- Tự động tạo kịch bản 3 - 10 cảnh chuẩn Storytelling viral:
  Hook mở đầu ➔ Thực trạng vấn đề ➔ Điểm ngoặt / Bí ẩn ➔ Giải pháp khai sáng ➔ Kêu gọi hành động
- Tự động sinh Visual Prompt tiếng Anh chi tiết cho từng cảnh (cho Midjourney/Flux/Veo/Kling)
- Tương thích 100% với định dạng scenes.json của hệ thống Editor Video AI
"""

import json
import re
from typing import List, Dict, Any, Optional


VISUAL_STYLES: Dict[str, str] = {
    "cinematic": "cinematic lighting, ultra-realistic 8k, dramatic shadows, photorealistic, depth of field, hyper-detailed, masterpiece, film grain",
    "3d_pixar": "3D Pixar Disney style animation, vibrant colors, expressive characters, soft studio lighting, cute and detailed render, Unreal Engine 5",
    "anime": "anime dark fantasy aesthetic, Makoto Shinkai style, atmospheric lighting, high quality digital illustration, vivid details",
    "vintage": "vintage 1970s 35mm film photograph, archival historical look, sepia warm tones, film grain, authentic retro atmosphere",
    "cyberpunk": "cyberpunk neon atmosphere, futuristic volumetric fog, glowing holograms, high tech dark aesthetic, octane render",
}

TONE_PROFILES: Dict[str, Dict[str, str]] = {
    "mystery": {
        "label": "⚡ Hồi hộp & Bí ẩn",
        "hook_prefix": "Có một sự thật rùng mình mà gần như không một ai dám nói cho bạn biết về",
        "sfx": "Tiếng tim đập dồn dập, âm thanh chuông ngân rùng rợn",
        "motion": "zoom_in",
    },
    "finance": {
        "label": "💡 Chuyên gia Tài chính & Thực chiến",
        "hook_prefix": "Nếu bạn đang kiếm được dưới 20 triệu mỗi tháng, hãy dừng ngay việc",
        "sfx": "Âm thanh máy đếm tiền, tiếng chuông đồng hồ đếm ngược",
        "motion": "pan_right",
    },
    "shocking": {
        "label": "🔥 Giật gân & Gay cấn",
        "hook_prefix": "Đừng bao giờ tin vào những gì họ nói! Đây chính là cái bẫy lớn nhất trong",
        "sfx": "Tiếng sấm chớp, âm bass dồn nén cực mạnh",
        "motion": "zoom_in",
    },
    "inspirational": {
        "label": "🌟 Truyền cảm hứng & Động lực",
        "hook_prefix": "Cuộc đời bạn sẽ hoàn toàn bước sang một trang mới nếu bạn hiểu được điều này về",
        "sfx": "Giai điệu piano truyền cảm hứng, tiếng gió thổi nhẹ",
        "motion": "zoom_out",
    },
    "humor": {
        "label": "😂 Tự trào & Châm biếm",
        "hook_prefix": "Tôi cá là 99% các bạn đang mắc đúng cái lỗi ngớ ngẩn này khi nhắc đến",
        "sfx": "Tiếng kèn hài hước, tiếng cười nhẹ",
        "motion": "none",
    },
}


class StoryboardScene:
    """Đại diện cho một phân cảnh trong kịch bản Storyboard."""

    def __init__(
        self,
        scene_id: str,
        title: str,
        voiceover: str,
        prompt: str,
        duration: float = 6.0,
        sfx: str = "",
        motion_type: str = "zoom_in",
        character: str = "",
        character_info: str = "",
    ):
        self.scene_id = scene_id
        self.title = title
        self.voiceover = voiceover.strip()
        self.prompt = prompt.strip()
        self.duration = duration
        self.sfx = sfx
        self.motion_type = motion_type
        self.character = character
        self.character_info = character_info

    @property
    def word_count(self) -> int:
        return len(self.voiceover.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.scene_id,
            "title": self.title,
            "voiceover": self.voiceover,
            "prompt": self.prompt,
            "duration": round(self.duration, 1),
            "sfx": self.sfx,
            "motion": {"type": self.motion_type, "strength": "subtle"},
            "character": self.character,
            "character_info": self.character_info,
        }

    def to_project_scene_dict(self, index: int, total_scenes: int, start_sec: float) -> Dict[str, Any]:
        """Xuất ra format chuẩn 7 trường theo scenes.json của dự án."""
        end_sec = start_sec + self.duration
        start_str = format_timestamp_srt(start_sec)
        end_str = "AUDIO_END" if index == total_scenes else format_timestamp_srt(end_sec)

        return {
            "id": self.scene_id,
            "character": self.character,
            "character_info": self.character_info,
            "prompt": self.prompt,
            "subtitle_ids": [],
            "start_at": start_str,
            "end_at": end_str,
            "motion": {"type": self.motion_type, "strength": "subtle"},
        }


def format_timestamp_srt(seconds: float) -> str:
    """Định dạng giây sang HH:MM:SS,mmm cho kịch bản cảnh."""
    millis = int(round((seconds - int(seconds)) * 1000))
    total_secs = int(seconds)
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    secs = total_secs % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def detect_topic_domain(topic: str) -> str:
    """Phát hiện lĩnh vực của chủ đề để tối ưu hóa góc tiếp cận."""
    topic_lower = topic.lower()
    finance_keywords = ("tiền", "tài chính", "tiết kiệm", "chi tiêu", "lương", "lạm phát", "nợ", "thẻ", "mua nhà", "thuê nhà", "bất động sản", "vàng", "đầu tư")
    religion_keywords = ("tôn giáo", "đức tin", "chúa", "phật", "kinh thánh", "vatican", "hồi giáo", "thiền", "linh hồn", "tâm linh", "giáo phái", "mecca")
    ai_keywords = ("ai", "trí tuệ nhân tạo", "robot", "chatgpt", "công nghệ", "thuật toán", "tương lai")

    if any(k in topic_lower for k in finance_keywords):
        return "finance"
    elif any(k in topic_lower for k in religion_keywords):
        return "religion"
    elif any(k in topic_lower for k in ai_keywords):
        return "ai"
    return "general"


def generate_storyboard(
    topic: str,
    scene_count: int = 5,
    tone: str = "mystery",
    visual_style: str = "cinematic",
    aspect_ratio: str = "9:16",
) -> List[StoryboardScene]:
    """
    Sinh kịch bản phân cảnh chi tiết dựa trên chủ đề, số cảnh và phong cách mong muốn.
    Hoạt động 100% offline với cơ chế suy luận kịch bản thông minh.
    """
    topic_clean = topic.strip() or "Chủ đề xu hướng"
    domain = detect_topic_domain(topic_clean)
    style_keywords = VISUAL_STYLES.get(visual_style, VISUAL_STYLES["cinematic"])
    tone_profile = TONE_PROFILES.get(tone, TONE_PROFILES["mystery"])
    aspect_flag = f"--ar {aspect_ratio}"

    # Kẹp số lượng cảnh từ 3 đến 10
    total_scenes = max(3, min(10, scene_count))

    # Cấu trúc từng phân đoạn kịch bản theo Storytelling
    templates = _get_storyboard_templates(domain, topic_clean, tone_profile, style_keywords, aspect_flag)

    scenes: List[StoryboardScene] = []
    # Chọn mẫu phân bổ theo số cảnh
    selected_patterns = _interpolate_patterns(templates, total_scenes)

    for i, pat in enumerate(selected_patterns, start=1):
        sc_id = f"SC{i:02d}"
        scenes.append(
            StoryboardScene(
                scene_id=sc_id,
                title=pat["title"],
                voiceover=pat["voiceover"],
                prompt=pat["prompt"],
                duration=pat.get("duration", 6.0),
                sfx=pat.get("sfx", tone_profile["sfx"]),
                motion_type=pat.get("motion", tone_profile["motion"]),
            )
        )

    return scenes


def _interpolate_patterns(templates: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
    """Phân bổ các cảnh template sao cho khớp chính xác với target_count."""
    if len(templates) == target_count:
        return templates
    if target_count < len(templates):
        # Lấy cảnh đầu (Hook), cảnh cuối (CTA) và trải đều ở giữa
        indices = [0]
        step = (len(templates) - 1) / (target_count - 1)
        for i in range(1, target_count - 1):
            indices.append(round(i * step))
        indices.append(len(templates) - 1)
        return [templates[idx] for idx in sorted(list(set(indices)))]

    # Nếu target_count > len(templates): nhân bản và biến thể phân đoạn giữa
    result = list(templates)
    extra_needed = target_count - len(templates)
    for k in range(extra_needed):
        insert_pos = 2 + (k % (len(result) - 3 if len(result) > 3 else 1))
        prev_scene = result[insert_pos - 1]
        new_scene = {
            "title": f"{prev_scene['title']} (Góc nhìn sâu hơn)",
            "voiceover": f"Đi sâu vào chi tiết, bạn sẽ nhận ra một yếu tố then chốt khác thường bị bỏ qua khi nhìn nhận {prev_scene.get('keyword', '')}.",
            "prompt": f"Close-up detailed focus related to {prev_scene.get('keyword', 'subject')}, high contrast, {prev_scene.get('style', '')}",
            "duration": 5.5,
            "sfx": prev_scene.get("sfx", ""),
            "motion": "zoom_in",
        }
        result.insert(insert_pos, new_scene)
    return result[:target_count]


def _get_storyboard_templates(
    domain: str,
    topic: str,
    tone: Dict[str, str],
    style: str,
    ar_flag: str,
) -> List[Dict[str, Any]]:
    """Tạo bộ kịch bản phân cảnh mẫu 10 cảnh chuyên sâu theo từng lĩnh vực."""
    hook_prefix = tone.get("hook_prefix", "Bạn có biết")

    if domain == "finance":
        return [
            {
                "title": "Mở đầu giật gân (Viral Hook)",
                "voiceover": f"{hook_prefix} {topic}! Nhiều người tin rằng cứ cắm đầu làm việc chăm chỉ là sẽ giàu có, nhưng thực tế nghiệt ngã hơn bạn nghĩ rất nhiều. Nếu thu nhập của bạn từ 15 đến 20 triệu nhưng cuối tháng tài khoản vẫn về con số không, hãy dừng lại 60 giây vì video này là dành cho bạn.",
                "prompt": f"Dramatic cinematic shot of a young professional staring anxiously at their smartphone screen showing an empty bank balance in a bustling rainy metropolis at night, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": "tài chính",
                "style": style,
            },
            {
                "title": "Thực trạng & Cạm bẫy (The Hidden Trap)",
                "voiceover": f"Mỗi tháng nhận lương xong, tiền biến đi đâu mất? Chi phí vô hình, thẻ tín dụng, mua trước trả sau và hội chứng chi tiêu đua đòi đang âm thầm bào mòn tương lai của bạn. Những khoản chi nhỏ lẻ không tên mới chính là lỗ rò rỉ làm đắm cả con thuyền tài chính.",
                "prompt": f"A close-up shot of hands holding cut credit cards on a wooden desk surrounded by scattered unpaid utility bills, warm moody lighting, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "pan_right",
                "keyword": "chi tiêu",
                "style": style,
            },
            {
                "title": "Bóc tách tâm lý (Psychological Trigger)",
                "voiceover": f"Bộ não con người luôn bị thao túng bởi cảm giác thỏa mãn tức thì. Các thuật toán mạng xã hội và sàn thương mại điện tử được thiết kế để kích thích bạn tiêu tiền trước khi kịp suy nghĩ. Bạn đang mua những thứ mình không cần, bằng số tiền mình chưa có, chỉ để gây ấn tượng với những người mình không thích.",
                "prompt": f"Cinematic conceptual shot of glowing digital shopping notifications swirling around a thoughtful person trapped in a smartphone maze, moody neon contrast, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "zoom_in",
                "keyword": "tâm lý mua sắm",
                "style": style,
            },
            {
                "title": "Nghịch lý lớn nhất (The Shocking Paradox)",
                "voiceover": f"Nghịch lý ở chỗ: Những người nghèo nhất lại thường là những người cố tỏ ra sang chảnh nhất để tìm kiếm sự công nhận. Trong khi những người thực sự tự do tài chính lại áp dụng lối sống tối giản cực đoan và âm thầm tích lũy tài sản sinh lời.",
                "prompt": f"Split comparison image: on the left a person covered in luxury designer logos sitting alone in a cheap cafe, on the right a person dressed in a simple plain shirt peacefully enjoying a book in a modern sunny living room, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_out",
                "keyword": "nghịch lý tiền bạc",
                "style": style,
            },
            {
                "title": "Bài học xương máu (Real Lesson)",
                "voiceover": f"Kiếm được bao nhiêu tiền không quan trọng bằng giữ được bao nhiêu tiền và để số tiền đó sinh sôi thế nào. Một biến cố sức khỏe hay mất việc bất ngờ có thể đẩy một gia đình trung lưu rơi thẳng xuống đáy nợ nần nếu không có lớp đệm tài chính phòng vệ vững chắc.",
                "prompt": f"Moody cinematic portrait of an anxious family looking at unexpected financial hospital and mortgage bills on a dark table, soft rim light, emotional depth, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_left",
                "keyword": "bài học tài chính",
                "style": style,
            },
            {
                "title": "Thay đổi tư duy (Mindset Shift)",
                "voiceover": f"Hãy ngừng ngay việc coi tiết kiệm là khổ hạnh hay keo kiệt. Tiết kiệm chính là mua lại sự tự do và quyền được làm chủ tương lai của chính mình. Mỗi đồng tiền bạn giữ lại hôm nay là một chiến binh trung thành làm việc cật lực cho bạn ngày mai.",
                "prompt": f"An inspiring aesthetic shot of golden coins sprouting into lush green tree saplings on fertile rich soil, radiant morning sunlight, growth symbol, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": "tư duy tích sản",
                "style": style,
            },
            {
                "title": "Chiến lược bước 1: Cắt nợ xấu (Debt Elimination)",
                "voiceover": f"Quy tắc vàng đầu tiên: Cắt đứt ngay toàn bộ nợ thẻ tín dụng và vay tiêu dùng lãi suất cao. Hãy liệt kê tất cả các khoản nợ từ nhỏ đến lớn và xử lý dứt điểm từng khoản để giải phóng tâm trí và dòng tiền hàng tháng.",
                "prompt": f"Close-up of hands firmly stamping PAID IN FULL on credit statements, confident purposeful mood, sharp studio focus, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_right",
                "keyword": "xử lý nợ",
                "style": style,
            },
            {
                "title": "Chiến lược bước 2: Quỹ khẩn cấp (Emergency Fund)",
                "voiceover": f"Bước thứ hai: Xây dựng ngay một quỹ dự phòng khẩn cấp tương đương 3 đến 6 tháng sinh hoạt phí trong tài khoản tách biệt. Đây là tấm lá chắn sinh tử giúp bạn bình thản trước mọi biến động kinh tế bất ngờ.",
                "prompt": f"A clean aesthetic flatlay of a notebook titled Emergency Shield, a cup of coffee, a golden piggy bank and neat stacks of cash, soft natural morning sunlight, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_out",
                "keyword": "quỹ khẩn cấp",
                "style": style,
            },
            {
                "title": "Chiến lược bước 3: Tích sản tự động (Automated Wealth)",
                "voiceover": f"Bước thứ ba: Tự động trích tối thiểu 20% thu nhập ngay khi tiền lương về tài khoản để đầu tư vào tài sản dài hạn trước khi chi tiêu bất kỳ thứ gì. Hãy biến việc tích lũy tài sản thành một thói quen bắt buộc không thể trì hoãn.",
                "prompt": f"Modern sleek smartphone screen displaying automated recurring investment graph steadily climbing upward, aesthetic desk setup, blurred city lights, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_left",
                "keyword": "đầu tư tự động",
                "style": style,
            },
            {
                "title": "Kêu gọi hành động & Đúc kết (Call to Action)",
                "voiceover": f"Bạn chọn sống sang chảnh ảo trong 1 năm hay muốn tự do tài chính thực sự sau 5 năm tới? Hãy bình luận mục tiêu tiết kiệm của bạn bên dưới, bấm theo dõi kênh và bắt đầu thay đổi tương lai tài chính của bạn ngay hôm nay!",
                "prompt": f"An inspiring silhouette of a confident person standing atop a modern skyscraper looking out at the golden sunrise over a sprawling modern city skyline, cinematic atmospheric haze, {style}, {ar_flag}",
                "duration": 5.5,
                "motion": "zoom_in",
                "keyword": "tương lai tài chính",
                "style": style,
            },
        ]
    elif domain == "religion":
        return [
            {
                "title": "Hồ sơ bí ẩn (The Mystery Hook)",
                "voiceover": f"{hook_prefix} {topic}. Suốt hàng thế kỷ qua, những tài liệu cổ xưa này đã bị che giấu khỏi tầm mắt của công chúng thế giới. Những gì sắp được tiết lộ sau đây sẽ làm lung lay những điều bạn từng mặc định là chân lý.",
                "prompt": f"Mysterious ancient stone vault illuminated by flickering torchlight, massive locked wooden iron doors engraved with sacred occult symbols, volumetric smoke, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": "bí mật tôn giáo",
                "style": style,
            },
            {
                "title": "Văn tự cổ & Bằng chứng (Ancient Evidence)",
                "voiceover": f"Khi các nhà khảo cổ lần đầu tiên giải mã được những ký tự trên cuộn giấy da cổ, họ đã kinh ngạc trước những sự thật hoàn toàn trái ngược với những bản dịch phổ thông. Những mảnh ghép lịch sử bị lãng quên dần hé lộ một bức tranh chân thực đến khó tin.",
                "prompt": f"Extreme macro shot of weathered ancient papyrus scrolls with faded sacred calligraphy, glowing dust particles in the air, magnifying glass revealing hidden text, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "pan_right",
                "keyword": "văn tự cổ",
                "style": style,
            },
            {
                "title": "Sự thật lịch sử (Historical Reality)",
                "voiceover": f"Bối cảnh ra đời của những lời dạy thiêng liêng thực chất gắn liền với những cuộc đấu tranh sinh tồn và giải phóng con người khỏi ách áp bức thời cổ đại. Những thông điệp nguyên bản mang tính cách mạng xã hội sâu sắc hơn nhiều so với những hình thức nghi lễ giáo điều.",
                "prompt": f"Cinematic historical reenactment of ancient gatherings in stone courtyards, dramatic dusty desert sunlight, atmospheric period costumes, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "zoom_out",
                "keyword": "lịch sử đức tin",
                "style": style,
            },
            {
                "title": "Tranh cãi không hồi kết (The Great Debate)",
                "voiceover": f"Liệu đức tin là ngọn hải đăng soi đường cho đạo đức và lòng trắc ẩn, hay đã từng bị những thế lực cầm quyền lợi dụng như một công cụ kiểm soát tâm lý quần chúng? Câu trả lời không đơn giản là trắng hay đen.",
                "prompt": f"Two ancient scholarly monks in hooded robes passionately debating in a grand candlelit cathedral library surrounded by towering bookshelves, dramatic chiaroscuro lighting, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_left",
                "keyword": "tranh cãi lịch sử",
                "style": style,
            },
            {
                "title": "Góc khuất quyền lực (Hidden Power)",
                "voiceover": f"Lịch sử từng chứng kiến những cuộc cải cách đẫm máu chỉ vì những bất đồng trong cách diễn giải một câu chữ kinh điển. Đằng sau những cuộc thánh chiến đôi khi không phải là đức tin thuần túy, mà là dòng chảy ngầm của quyền lực và lãnh thổ.",
                "prompt": f"Epic historical painting style of medieval knights and scholars facing towering ancient stone monuments, dramatic overcast stormy sky, volumetric rays, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": "quyền lực lịch sử",
                "style": style,
            },
            {
                "title": "Sự thức tỉnh tâm can (Spiritual Awakening)",
                "voiceover": f"Tuy nhiên, vượt lên trên mọi tranh chấp trần thế, giá trị vĩnh cửu của đức tin chân chính luôn nằm ở tình yêu thương vô điều kiện và sự bao dung tuyệt đối. Đó là sức mạnh cảm hóa bạo lực và chữa lành những vết thương sâu kín nhất của tâm hồn.",
                "prompt": f"Ethereal spiritual scene of a meditating figure sitting under an ancient sacred Bodhi tree, rays of divine golden light piercing through dark clouds, transcendent peaceful atmosphere, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "zoom_out",
                "keyword": "thức tỉnh tâm linh",
                "style": style,
            },
            {
                "title": "Khoa học hội ngộ tâm linh (Science Meets Faith)",
                "voiceover": f"Điều kỳ diệu là khoa học thần kinh hiện đại đang ngày càng chứng minh những phương pháp tu tập cổ xưa như thiền định, quán chiếu và lòng biết ơn có khả năng tái cấu trúc não bộ và mang lại sự an lạc nội tại thực sự.",
                "prompt": f"Futuristic neural network brain scan harmoniously blending with sacred geometric mandala symbols, luminescent blue and gold particles, aesthetic scientific render, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_right",
                "keyword": "khoa học tâm linh",
                "style": style,
            },
            {
                "title": "Thực hành đời thường (Practical Mindfulness)",
                "voiceover": f"Đức tin không nằm ở những bức tường tu viện hay những lời cầu nguyện sáo rỗng, mà hiển hiện trong từng hành động tử tế nhỏ bé bạn dành cho người xung quanh mỗi ngày. Sống tỉnh thức chính là hình thức tu tập cao quý nhất.",
                "prompt": f"Warm heartfelt cinematic moment of a compassionate person gently helping an elderly stranger in a sunlit cobblestone alley, authentic human emotion, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": "thực hành yêu thương",
                "style": style,
            },
            {
                "title": "Chân lý cốt lõi (Core Truth)",
                "voiceover": f"Bản chất của sự giải thoát chưa bao giờ là trốn chạy cuộc đời, mà là nhìn thẳng vào vô thường và khổ đau để tìm thấy sự bình yên bất biến ngay giữa tâm bão giông cuộc sống.",
                "prompt": f"A serene tranquil zen garden with smooth water ripples reflecting a majestic mountain at sunset, golden mist, peaceful stillness, {style}, {ar_flag}",
                "duration": 5.5,
                "motion": "pan_left",
                "keyword": "chân lý vô thường",
                "style": style,
            },
            {
                "title": "Câu hỏi bỏ ngỏ (Call to Action)",
                "voiceover": f"Nếu mọi điều bạn từng nghe đều chỉ là một phần của sự thật, bạn có đủ dũng cảm để tự mình đi tìm câu trả lời không? Hãy chia sẻ suy ngẫm chân thành của bạn bên dưới và cùng thảo luận nhé!",
                "prompt": f"Cinematic atmospheric wide shot of ancient stone monoliths standing beneath a breathtaking starry galaxy Milky Way night sky, mystical fog swirling around the ground, {style}, {ar_flag}",
                "duration": 5.5,
                "motion": "zoom_in",
                "keyword": "vũ trụ bí ẩn",
                "style": style,
            },
        ]
    elif domain == "ai":
        return [
            {
                "title": "Cảnh báo tương lai (AI Warning Hook)",
                "voiceover": f"{hook_prefix} {topic}! Những gì đang diễn ra trong các phòng thí nghiệm bí mật lúc này vượt xa trí tưởng tượng của 99% mọi người. Một bước nhảy vọt công nghệ đang âm thầm tái định hình lại toàn bộ nền văn minh nhân loại.",
                "prompt": f"Futuristic dark laboratory where a glowing humanoid artificial intelligence cyborg looks at a holographic stream of quantum data lines, cinematic sci-fi neon lighting, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": "trí tuệ nhân tạo",
                "style": style,
            },
            {
                "title": "Sự thay đổi tàn khốc (The Disruption)",
                "voiceover": f"Hàng triệu công việc truyền thống đang biến mất chỉ sau một đêm. Những kỹ năng bạn mất 5 đến 10 năm mài giũa giờ đây có thể được một mô hình AI thực hiện trong vài giây với chi phí gần như bằng không. Không một ngành nghề nào là hoàn toàn an toàn.",
                "prompt": f"An empty modern corporate office with rows of glowing unattended computers and holographic charts, dusk lighting through floor-to-ceiling windows, desolate tech atmosphere, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "pan_right",
                "keyword": "tự động hóa",
                "style": style,
            },
            {
                "title": "Góc khuất thuật toán (Algorithmic Control)",
                "voiceover": f"Thuật toán không chỉ gợi ý nội dung, mà đang âm thầm thao túng hành vi, cảm xúc và quyết định của hàng tỷ người mỗi ngày. Chúng ta đang vô tình trao quyền lực tối cao cho những cỗ máy thông minh mà chính người tạo ra chúng cũng chưa hiểu hết.",
                "prompt": f"Surreal visualization of human silhouettes walking on glowing circuit board pathways, massive holographic eye watching from above, cyberpunk dystopian tone, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "zoom_out",
                "keyword": "kiểm soát thuật toán",
                "style": style,
            },
            {
                "title": "Nghịch lý công nghệ (Tech Paradox)",
                "voiceover": f"Công nghệ giúp chúng ta kết nối toàn cầu trong tích tắc, nhưng lại khiến con người cô đơn và kiệt sức hơn bao giờ hết. Sự tiện nghi tột bậc đang đổi lấy sự phụ thuộc nguy hiểm vào màn hình và thế giới ảo.",
                "prompt": f"Lone person sitting in a neon-lit futuristic apartment surrounded by multiple floating social media feeds, blue melancholy light on face, cinematic contrast, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_left",
                "keyword": "nghịch lý công nghệ",
                "style": style,
            },
            {
                "title": "Cơ hội thế kỷ (The Golden Opportunity)",
                "voiceover": f"Nhưng đừng hoảng loạn! Lịch sử đã chứng minh: AI sẽ không thay thế con người, mà những người biết làm chủ AI sẽ thay thế những người đứng ngoài cuộc. Đây là cuộc đại dịch chuyển của cải và cơ hội lớn nhất trong vòng 100 năm qua.",
                "prompt": f"A confident creator operating multiple floating holographic screens, creating digital worlds with ease, triumphant futuristic atmosphere, cinematic warm backlight, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": "làm chủ công nghệ",
                "style": style,
            },
            {
                "title": "Thay đổi tư duy dẫn đầu (Mastery Mindset)",
                "voiceover": f"Thay vì sợ hãi bị thay thế, hãy biến AI thành trợ lý đắc lực siêu đẳng của bạn. Một cá nhân am hiểu công nghệ giờ đây có thể sở hữu năng suất và sức mạnh sáng tạo tương đương một đội ngũ hàng chục người.",
                "prompt": f"Close-up of human and robot robotic hands touching in a spark of creative energy, symbolic union of human creativity and synthetic power, hyper-detailed, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_right",
                "keyword": "sức mạnh kết hợp",
                "style": style,
            },
            {
                "title": "Chiến lược bước 1: Nắm bắt công cụ (Tool Adoption)",
                "voiceover": f"Bước đầu tiên: Hãy bắt tay vào sử dụng các công cụ AI hàng đầu ngay từ hôm nay. Đừng chỉ dùng để hỏi đáp cơ bản, mà hãy tích hợp sâu vào quy trình làm việc, nghiên cứu và sản xuất nội dung của bạn.",
                "prompt": f"Aesthetic high-tech desk setup with glowing keyboard and multiple monitors displaying advanced AI workflow pipelines, clean productive atmosphere, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_out",
                "keyword": "ứng dụng thực tế",
                "style": style,
            },
            {
                "title": "Chiến lược bước 2: Nâng cấp kỹ năng người (Human Uniqueness)",
                "voiceover": f"Bước thứ hai: Tập trung rèn luyện những giá trị mà máy móc không bao giờ có được: Tư duy phản biện sắc bén, khả năng đồng cảm sâu sắc, trí tưởng tượng độc bản và kỹ năng kết nối con người với con người.",
                "prompt": f"Dynamic artistic shot of an artist sculpting a luminous sculpture with bare hands amidst digital wireframes, celebration of human creative soul, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_left",
                "keyword": "kỹ năng độc bản",
                "style": style,
            },
            {
                "title": "Chiến lược bước 3: Xây dựng đòn bẩy (Leverage Building)",
                "voiceover": f"Bước thứ ba: Tận dụng AI để tự động hóa tối đa các công việc lặp lại, giải phóng thời gian quý báu để tập trung vào các chiến lược cấp cao và xây dựng thương hiệu cá nhân bền vững.",
                "prompt": f"High altitude drone shot of futuristic skyscrapers connected by luminescent skybridges, bright blue skies, optimistic cyber future, {style}, {ar_flag}",
                "duration": 5.5,
                "motion": "zoom_in",
                "keyword": "xây dựng đòn bẩy",
                "style": style,
            },
            {
                "title": "Kêu gọi hành động (Call to Action)",
                "voiceover": f"Bạn chọn đứng nhìn làn sóng công nghệ cuốn phăng mình đi, hay trở thành người tiên phong cưỡi trên ngọn sóng? Bấm theo dõi kênh ngay hôm nay để không bao giờ bị bỏ lại phía sau trong kỷ nguyên mới!",
                "prompt": f"A solitary traveler standing on a cliff edge looking towards a futuristic utopian mega-city bathed in golden sunrise, dramatic inspiring epic horizon, {style}, {ar_flag}",
                "duration": 5.5,
                "motion": "zoom_out",
                "keyword": "tương lai",
                "style": style,
            },
        ]
    else:
        # General domain
        return [
            {
                "title": "Mở đầu tò mò (Intrigue Hook)",
                "voiceover": f"{hook_prefix} {topic}! 99% mọi người tiếp cận vấn đề này hoàn toàn sai lầm vì bị chi phối bởi những định kiến truyền đời. Nếu bạn muốn bứt phá khỏi số đông, đây là lúc bạn cần nhìn thẳng vào sự thật.",
                "prompt": f"Striking cinematic visual representation of {topic}, dramatic lighting, highly expressive subject, stunning depth of field, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Bóc tách thực trạng (Unveiling Reality)",
                "voiceover": f"Đằng sau vẻ bề ngoài tưởng như bình thường là cả một mạng lưới các quy luật tâm lý vô hình đang âm thầm định hình số phận của bạn. Chúng ta thường tưởng mình đưa ra quyết định dựa trên lý trí, nhưng thực chất 95% hành vi lại bị điều khiển bởi tiềm thức và thói quen.",
                "prompt": f"Detailed cinematic documentary scene exploring {topic}, authentic environment, moody atmosphere, rich textures and lighting, {style}, {ar_flag}",
                "duration": 6.5,
                "motion": "pan_right",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Cạm bẫy của sự trì hoãn (The Comfort Trap)",
                "voiceover": f"Vùng an toàn chính là nấm mồ chôn vùi tiềm năng lớn nhất của con người. Cảm giác thoải mái giả tạo mỗi ngày khiến bạn trì hoãn những mục tiêu lớn, để rồi giật mình nhận ra năm tháng đã trôi qua mà bản thân vẫn dậm chân tại chỗ.",
                "prompt": f"Conceptual visual of a person trapped inside an elegant glass cage in a lavish room, dramatic symbolic shadows, cinematic lighting, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_out",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Nghịch lý thành công (Counter-intuitive Truth)",
                "voiceover": f"Điều bất ngờ nhất là con đường dẫn đến thành công thực chất không nằm ở những bước nhảy vọt vĩ đại, mà được tạo nên từ những hành động nhỏ bé, nhàm chán nhưng được lặp đi lặp lại với tính kỷ luật thép mỗi ngày.",
                "prompt": f"A lone individual boldly walking against a blurred rushing crowd in a dramatic cinematic setting, symbolic contrast lighting, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_left",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Cái giá của sự kiên trì (The Compound Effect)",
                "voiceover": f"Quy luật lãi kép không chỉ áp dụng cho tiền bạc, mà áp dụng cho mọi khía cạnh: Tri thức, sức khỏe, mối quan hệ và kỹ năng. Cải thiện 1% mỗi ngày sẽ giúp bạn tiến bộ gấp 37 lần chỉ sau một năm.",
                "prompt": f"Time-lapse style image of a small sapling growing through cracked concrete into a mighty towering oak tree under radiant sunlight, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Điểm xoay tư duy (Mindset Breakthrough)",
                "voiceover": f"Đừng chờ đợi cảm hứng mới bắt đầu hành động. Hành động mới chính là thứ tạo ra cảm hứng. Khi bạn dám bước bước chân đầu tiên vượt qua nỗi sợ hãi, con đường phía trước sẽ tự khắc hiện rõ.",
                "prompt": f"Dramatic silhouette of an athlete breaking through heavy dark chains into radiant morning sunlight, dynamic motion, inspirational mood, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_right",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Hành động bước 1: Loại bỏ nhiễu loạn (Decluttering)",
                "voiceover": f"Bước thứ nhất: Dũng cảm cắt bỏ những mối quan hệ độc hại, những thói quen tiêu tốn thời gian vô bổ và thông tin rác trên mạng xã hội. Hãy bảo vệ năng lượng và sự tập trung của bạn như bảo vệ tài sản quý giá nhất.",
                "prompt": f"Minimalist aesthetic room with a lone organized wooden desk, soft morning sunlight, peaceful clean aura, distraction-free environment, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_out",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Hành động bước 2: Thiết lập hệ thống (System Building)",
                "voiceover": f"Bước thứ hai: Đừng chỉ đặt mục tiêu suông, hãy xây dựng một hệ thống thói quen bất khả bại. Bạn không vươn lên bằng mức độ của mục tiêu, mà bạn rơi xuống bằng mức độ của hệ thống thói quen bạn xây dựng.",
                "prompt": f"Close-up of hands writing organized daily habit checklist in a leather-bound notebook, fountain pen, golden warm hour lighting, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "pan_left",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Hành động bước 3: Giữ vững cam kết (Unwavering Focus)",
                "voiceover": f"Bước thứ ba: Kiên định với con đường đã chọn ngay cả khi chưa thấy kết quả tức thì. Những cây tre mất 4 năm chỉ để mọc được 3 centimet, nhưng đến năm thứ năm sẽ vươn cao 30 mét chỉ trong vài tuần.",
                "prompt": f"Serene bamboo grove swaying in gentle morning wind, shafts of emerald green sunlight piercing through dense leaves, resilient natural strength, {style}, {ar_flag}",
                "duration": 6.0,
                "motion": "zoom_in",
                "keyword": topic,
                "style": style,
            },
            {
                "title": "Kết luận & Kêu gọi (Final Call to Action)",
                "voiceover": f"Cuộc đời bạn là do chính bạn viết nên từng trang mỗi ngày. Hãy để lại một bình luận cam kết thay đổi của bạn ngay bên dưới, bấm thích video và bắt đầu hành trình bứt phá ngay từ giây phút này!",
                "prompt": f"Cinematic wide angle golden hour shot looking out towards a beautiful horizon, uplifting atmosphere, crystal clear details, {style}, {ar_flag}",
                "duration": 5.5,
                "motion": "zoom_out",
                "keyword": topic,
                "style": style,
            },
        ]


def generate_full_script_for_topic(
    topic: str,
    duration_seconds: int = 60,
    tone: str = "mystery",
    visual_style: str = "cinematic",
) -> str:
    """
    Sinh một bài kịch bản hoàn chỉnh (Full Script) liền mạch cho video,
    độ dài khớp chuẩn xác với thời lượng phát (30s, 60s, 120s, 180s...).
    """
    topic_clean = topic.strip() or "Chủ đề video"
    # Xác định số lượng phân cảnh để khớp thời lượng
    if duration_seconds <= 35:
        target_scenes = 3
    elif duration_seconds <= 75:
        target_scenes = 5
    elif duration_seconds <= 150:
        target_scenes = 8
    else:
        target_scenes = 10

    scenes = generate_storyboard(
        topic=topic_clean,
        scene_count=target_scenes,
        tone=tone,
        visual_style=visual_style,
    )
    return export_storyboard_to_full_script(scenes)


def export_storyboard_to_scenes_json(scenes: List[StoryboardScene]) -> str:
    """Xuất danh sách phân cảnh ra chuỗi JSON chuẩn kịch bản scenes.json."""
    data = []
    current_time = 0.0
    total = len(scenes)
    for idx, sc in enumerate(scenes, start=1):
        data.append(sc.to_project_scene_dict(idx, total, current_time))
        current_time += sc.duration
    return json.dumps(data, ensure_ascii=False, indent=2)


def export_storyboard_to_full_script(scenes: List[StoryboardScene]) -> str:
    """Ghép toàn bộ lời thoại voiceover của các cảnh thành một kịch bản đọc liền mạch."""
    lines = [sc.voiceover for sc in scenes if sc.voiceover]
    return "\n\n".join(lines)


def export_storyboard_to_markdown(topic: str, scenes: List[StoryboardScene]) -> str:
    """Xuất kịch bản phân cảnh ra tài liệu Markdown chi tiết để chia sẻ hoặc lưu trữ."""
    lines = [
        f"# KỊCH BẢN PHÂN CẢNH VIDEO: {topic.upper()}",
        f"*Tổng số phân cảnh: {len(scenes)} cảnh | Thời lượng ước tính: ~{sum(s.duration for s in scenes):.0f} giây*",
        "",
        "---",
        "",
    ]
    for sc in scenes:
        lines.append(f"### 🎬 {sc.scene_id}: {sc.title} (~{sc.duration:.1f}s)")
        lines.append(f"**🎙 Lời thoại (Voiceover):**")
        lines.append(f"> {sc.voiceover}")
        lines.append("")
        lines.append(f"**🎨 Visual Prompt (Midjourney / Flux / Veo):**")
        lines.append(f"```")
        lines.append(f"{sc.prompt}")
        lines.append(f"```")
        lines.append(f"*Hiệu ứng âm thanh (SFX):* {sc.sfx} | *Chuyển động:* `{sc.motion_type}`")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)
