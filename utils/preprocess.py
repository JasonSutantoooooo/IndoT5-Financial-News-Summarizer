import re


def clean_noise(text: str) -> str:
    noise_patterns = [
        r"^(?:[^,]+,?\s*)?CNBC\s*Indonesia(?:\.com)?\s*[-—–]\s*",
        r"^.*?Jakarta\s*[-—–]\s*",
        r"SCROLL TO CONTINUE WITH CONTENT",
        r"IDXChannel -\s*",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

    text = re.sub(
        r"Tonton\s+juga.*?\[Gambas:[^\]]+\]",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    text = re.sub(r"\[Gambas:[^\]]+\]", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()
