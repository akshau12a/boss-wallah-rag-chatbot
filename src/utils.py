# src/utils.py
from langdetect import detect, DetectorFactory
from typing import Optional, List

DetectorFactory.seed = 42

# Given mapping in the spec
LANG_CODE_TO_NAME = {
    6: "Hindi",
    7: "Kannada",
    11: "Malayalam",
    20: "Tamil",
    21: "Telugu",
    24: "English",
}
LANG_NAME_TO_CODE = {v.lower(): k for k, v in LANG_CODE_TO_NAME.items()}

# Localized “out-of-scope” messages (Bonus #1)
OUT_OF_SCOPE = {
    "Hindi": "क्षमा करें, यह जानकारी हमारे डेटा में उपलब्ध नहीं है।",
    "Kannada": "ಕ್ಷಮಿಸಿ, ಈ ಮಾಹಿತಿ ನಮ್ಮ ಡೇಟಾದಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ.",
    "Malayalam": "ക്ഷമിക്കണം, ഈ വിവരം ഞങ്ങളുടെ ഡാറ്റയിൽ ലഭ്യമല്ല.",
    "Tamil": "மன்னிக்கவும், இந்த தகவல் எங்கள் தரவுகளில் இல்லை.",
    "Telugu": "క్షమించండి, ఈ సమాచారం మా డేటాలో అందుబాటులో లేదు.",
    "English": "Sorry, this information is not available in our dataset.",
}

def detect_language_name(text: str) -> str:
    try:
        code = detect(text)
    except Exception:
        return "English"
    mapping = {
        "hi": "Hindi",
        "kn": "Kannada",
        "ml": "Malayalam",
        "ta": "Tamil",
        "te": "Telugu",
        "en": "English",
    }
    return mapping.get(code, "English")

def normalize_languages_field(raw) -> set:
    """
    Accepts 'Released Languages' values like '20,24' or 'Tamil, English'
    -> returns a set of canonical language names.
    """
    if raw is None:
        return set()
    parts = [p.strip() for p in str(raw).split(",")]
    out = set()
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            name = LANG_CODE_TO_NAME.get(int(p))
            if name:
                out.add(name)
        else:
            # treat as name
            name = p.strip().lower()
            if name in LANG_NAME_TO_CODE:
                out.add(LANG_CODE_TO_NAME[LANG_NAME_TO_CODE[name]])
            else:
                out.add(p.strip().capitalize())
    return out

def query_requests_language_filter(query: str) -> Optional[str]:

    """
    Detect if the user is asking for courses in a specific language (e.g., "in Tamil", "Tamil courses").
    Returns canonical language name or None.
    """
    q = query.lower()
    for code, name in LANG_CODE_TO_NAME.items():
        if name.lower() in q:
            return name
    # simple patterns
    tokens = q.replace("language", "").replace("languages", "")
    for key in ["tamil", "telugu", "hindi", "kannada", "malayalam", "english", "en"]:
        if key in tokens:
            # map 'en' -> English
            if key == "en":
                return "English"
            return key.capitalize()
    return None
