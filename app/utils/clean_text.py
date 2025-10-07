import re


def clean_text_fn(text: str) -> str:
    """
    Remove null bytes and control characters from text for safe DB insertion.
    """
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Remove other non-printable/control characters
    text = re.sub(r"[\x01-\x1F\x7F]", "", text)
    return text
