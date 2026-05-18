from langdetect import detect

def is_indonesian_text(text: str) -> bool:
    try:
        return detect(text) == "id"
    except:
        return False