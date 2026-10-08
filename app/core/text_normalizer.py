import re

def normalize_vietnamese_text(text: str) -> str:
    """
    Normalize Vietnamese text to improve Kokoro TTS pronunciation and prevent crashes.
    """
    if not text:
        return text

    # 1. Remove emojis and unsupported special characters
    # Keep alphanumeric, basic punctuation, and Vietnamese characters
    text = re.sub(r'[^\w\s.,!?/:;"\'()-]', ' ', text)

    # 2. Convert dates like 10/08/2026 to "10 tháng 08 năm 2026"
    text = re.sub(r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\1 tháng \2 năm \3', text)
    text = re.sub(r'(\d{1,2})/(\d{1,2})', r'\1 tháng \2', text)
    
    # 3. Handle measurements and currency
    replacements = {
        r'\b(\d+)kg\b': r'\1 ki lô gam',
        r'\b(\d+)m\b': r'\1 mét',
        r'\b(\d+)km\b': r'\1 ki lô mét',
        r'\b(\d+)cm\b': r'\1 cen ti mét',
        r'\b(\d+)tr\b': r'\1 triệu',
        r'\b(\d+)k\b': r'\1 nghìn',
        r'\bvnđ\b': 'việt nam đồng',
        r'\bko\b': 'không',
        r'\bđc\b': 'được',
    }
    
    # Apply replacements case-insensitively for abbreviations
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    # 4. Handle ALL CAPS words (which Kokoro might spell letter-by-letter)
    # We find words that are fully uppercase (and at least 2 characters long)
    # and convert them to lowercase.
    def lowercase_match(match):
        return match.group(0).lower()
        
    text = re.sub(r'\b[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴÝỶỸ]{2,}\b', lowercase_match, text)

    # 5. Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
