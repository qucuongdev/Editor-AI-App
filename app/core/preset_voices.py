"""
Preset voices for TTS providers (ElevenLabs, Kokoro Local, MiniMax, CapCut).
Provides built-in voices so users can immediately choose without needing to search.
"""
from typing import List, Dict, Tuple, Optional
from app import config

KOKORO_PRESETS: List[Dict[str, str]] = [
    {"voice_id": "vi_mai_linh", "name": "🇻🇳 Mai Linh (Nữ - Truyền cảm)", "lang": "vi", "gender": "Nữ"},
    {"voice_id": "vi_ngoc_huyen", "name": "🇻🇳 Ngọc Huyền (Nữ - Miền Bắc)", "lang": "vi", "gender": "Nữ"},
    {"voice_id": "vi_diem_trinh", "name": "🇻🇳 Diễm Trinh (Nữ - Nhẹ nhàng)", "lang": "vi", "gender": "Nữ"},
    {"voice_id": "vi_mai_loan", "name": "🇻🇳 Mai Loan (Nữ - Ấm áp)", "lang": "vi", "gender": "Nữ"},
    {"voice_id": "vi_my_yen", "name": "🇻🇳 Mỹ Yến (Nữ - Trong trẻo)", "lang": "vi", "gender": "Nữ"},
    {"voice_id": "vi_thuc_trinh", "name": "🇻🇳 Thục Trinh (Nữ - Trẻ trung)", "lang": "vi", "gender": "Nữ"},
    {"voice_id": "vi_duc_an", "name": "🇻🇳 Đức An (Nam - Trầm ấm)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "vi_duc_duy", "name": "🇻🇳 Đức Duy (Nam - Tự nhiên)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "vi_hung_thinh", "name": "🇻🇳 Hùng Thịnh (Nam - Truyền cảm)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "vi_manh_dung", "name": "🇻🇳 Mạnh Dũng (Nam - Mạnh mẽ)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "vi_phat_tai", "name": "🇻🇳 Phát Tài (Nam - Hào sảng)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "vi_storyvert", "name": "🇻🇳 Storyvert (Nam - Kể chuyện)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "vi_thanh_dat", "name": "🇻🇳 Thành Đạt (Nam - Chuyên nghiệp)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "vi_tuan_ngoc", "name": "🇻🇳 Tuấn Ngọc (Nam - Sang trọng)", "lang": "vi", "gender": "Nam"},
    {"voice_id": "af_bella", "name": "🇺🇸 Bella (Nữ - Mỹ)", "lang": "en", "gender": "Nữ"},
    {"voice_id": "af_sarah", "name": "🇺🇸 Sarah (Nữ - Mỹ)", "lang": "en", "gender": "Nữ"},
    {"voice_id": "am_adam", "name": "🇺🇸 Adam (Nam - Mỹ)", "lang": "en", "gender": "Nam"},
    {"voice_id": "bf_alice", "name": "🇬🇧 Alice (Nữ - Anh)", "lang": "en", "gender": "Nữ"},
    {"voice_id": "bm_george", "name": "🇬🇧 George (Nam - Anh)", "lang": "en", "gender": "Nam"},
]

STATIC_PRESETS: Dict[str, List[Dict[str, str]]] = {
    "kokoro": KOKORO_PRESETS,
    "elevenlabs": [
        {"voice_id": "6adFm46eyy74snVn6YrT", "name": "🇻🇳 Mai Anh (Nữ - Truyền cảm)", "lang": "vi", "gender": "Nữ"},
        {"voice_id": "ErXwobaYiN019PkySvjV", "name": "🇻🇳 Minh Phong (Nam - Trầm ấm)", "lang": "vi", "gender": "Nam"},
        {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "🇺🇸 Rachel (Nữ - Calm)", "lang": "en", "gender": "Nữ"},
        {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "🇺🇸 Adam (Nam - Narrative)", "lang": "en", "gender": "Nam"},
        {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "🇺🇸 Bella (Nữ - Soft)", "lang": "en", "gender": "Nữ"},
        {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "🇺🇸 Domi (Nữ - Strong)", "lang": "en", "gender": "Nữ"},
        {"voice_id": "MF3mGyEYCl7XYWbqtJJX", "name": "🇺🇸 Elli (Nữ - Emotional)", "lang": "en", "gender": "Nữ"},
        {"voice_id": "TxGEqnHWrfWFTfGW9XjX", "name": "🇺🇸 Josh (Nam - Deep)", "lang": "en", "gender": "Nam"},
        {"voice_id": "VR6AewLTigWG4ivSOKoG", "name": "🇺🇸 Arnold (Nam - Crisp)", "lang": "en", "gender": "Nam"},
        {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "name": "🇺🇸 Sam (Nam - Dynamic)", "lang": "en", "gender": "Nam"},
    ],
    "minimax": [
        {"voice_id": "moss_audio_01", "name": "🇻🇳 Nam Trầm Ấm (MiniMax)", "lang": "vi", "gender": "Nam"},
        {"voice_id": "moss_audio_02", "name": "🇻🇳 Nữ Dịu Dàng (MiniMax)", "lang": "vi", "gender": "Nữ"},
        {"voice_id": "moss_audio_03", "name": "🇻🇳 Nam Năng Động (MiniMax)", "lang": "vi", "gender": "Nam"},
        {"voice_id": "moss_audio_04", "name": "🇻🇳 Nữ Truyền Cảm (MiniMax)", "lang": "vi", "gender": "Nữ"},
        {"voice_id": "presenter_male", "name": "🎙️ MC Nam (MiniMax)", "lang": "vi", "gender": "Nam"},
        {"voice_id": "presenter_female", "name": "🎙️ MC Nữ (MiniMax)", "lang": "vi", "gender": "Nữ"},
        {"voice_id": "male-qn-qingse", "name": "🎙️ Thanh Niên (Nam)", "lang": "zh", "gender": "Nam"},
        {"voice_id": "female-shaonv", "name": "🎙️ Thiếu Nữ (Nữ)", "lang": "zh", "gender": "Nữ"},
        {"voice_id": "female-yujie", "name": "🎙️ Ngự Tỷ (Nữ)", "lang": "zh", "gender": "Nữ"},
        {"voice_id": "audiobook_male_1", "name": "🎙️ Đọc Sách Nam 1", "lang": "vi", "gender": "Nam"},
        {"voice_id": "audiobook_male_2", "name": "🎙️ Đọc Sách Nam 2", "lang": "vi", "gender": "Nam"},
        {"voice_id": "audiobook_female_1", "name": "🎙️ Đọc Sách Nữ 1", "lang": "vi", "gender": "Nữ"},
        {"voice_id": "audiobook_female_2", "name": "🎙️ Đọc Sách Nữ 2", "lang": "vi", "gender": "Nữ"},
    ],
    "capcut": [
        {"voice_id": "vi_female_1", "name": "🇻🇳 Nữ Miền Bắc (CapCut)", "lang": "vi", "gender": "Nữ"},
        {"voice_id": "vi_female_2", "name": "🇻🇳 Nữ Miền Nam (CapCut)", "lang": "vi", "gender": "Nữ"},
        {"voice_id": "vi_male_1", "name": "🇻🇳 Nam Miền Bắc (CapCut)", "lang": "vi", "gender": "Nam"},
        {"voice_id": "vi_male_2", "name": "🇻🇳 Nam Miền Nam (CapCut)", "lang": "vi", "gender": "Nam"},
        {"voice_id": "en_female_1", "name": "🇺🇸 Jessie (Nữ - CapCut)", "lang": "en", "gender": "Nữ"},
        {"voice_id": "en_male_1", "name": "🇺🇸 Joey (Nam - CapCut)", "lang": "en", "gender": "Nam"},
        {"voice_id": "cute_boy", "name": "👶 Em Bé Đáng Yêu (CapCut)", "lang": "vi", "gender": "Nam"},
    ]
}


def get_preset_voices(provider: str) -> List[Dict[str, str]]:
    """Return available preset voices for the given provider."""
    prov = (provider or "elevenlabs").lower()
    base_list = [dict(v) for v in STATIC_PRESETS.get(prov, [])]

    if prov == "kokoro":
        try:
            from app.core.kokoro_engine import get_kokoro_voices
            kokoro_list = get_kokoro_voices()
            if kokoro_list:
                return [
                    {
                        "voice_id": item["voice_id"],
                        "name": item["name"],
                        "lang": item.get("language", "vi"),
                        "gender": item.get("gender", "")
                    }
                    for item in kokoro_list
                ]
        except Exception:
            pass
        if kokoro_list:
            return kokoro_list

    return base_list


def get_default_voice_for_provider(provider: str) -> Tuple[str, str]:
    """Return (voice_id, voice_name) default for the given provider."""
    prov = (provider or "elevenlabs").lower()
    if prov == "kokoro":
        return ("vi_mai_linh", "🇻🇳 Mai Linh (Nữ - Truyền cảm)")
    elif prov == "minimax":
        return ("moss_audio_01", "🇻🇳 Nam Trầm Ấm (MiniMax)")
    elif prov == "capcut":
        return ("vi_female_1", "🇻🇳 Nữ Miền Bắc (CapCut)")
    else:
        # ElevenLabs
        default_id = getattr(config.settings, "DEFAULT_VIBI_VOICE_ID", None) or "6adFm46eyy74snVn6YrT"
        name = "🇻🇳 Mai Anh (Nữ - Truyền cảm)"
        if default_id != "6adFm46eyy74snVn6YrT":
            name = find_voice_name("elevenlabs", default_id) or "Giọng Mặc Định (ElevenLabs)"
        return (default_id, name)


def find_voice_name(provider: str, voice_id: str) -> Optional[str]:
    """Lookup display name of a voice ID in presets."""
    if not voice_id:
        return None
    for voice in get_preset_voices(provider):
        if voice["voice_id"] == voice_id:
            return voice["name"]
    return None
