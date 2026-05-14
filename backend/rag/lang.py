from langdetect import detect, LangDetectException

_LANG_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ru": "Russian",
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "hi": "Hindi",
    "tr": "Turkish", "pl": "Polish", "sv": "Swedish", "da": "Danish",
    "fi": "Finnish", "nb": "Norwegian", "cs": "Czech", "sk": "Slovak",
    "ro": "Romanian", "hu": "Hungarian", "uk": "Ukrainian", "vi": "Vietnamese",
    "th": "Thai", "id": "Indonesian", "ms": "Malay",
}


def detect_language(text: str) -> str:
    """Return ISO 639-1 language code. Falls back to 'en' on short/ambiguous text."""
    if not text or len(text.strip()) < 20:
        return "en"
    try:
        return detect(text[:500])
    except (LangDetectException, Exception):
        return "en"


def lang_name(code: str) -> str:
    """Return human-readable name for a language code."""
    return _LANG_NAMES.get(code, "English")
