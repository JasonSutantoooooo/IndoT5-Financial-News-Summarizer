import re

_TOOLTIP_CSS = """
<style>
.kw {
    color: #e7000b;
    font-weight: 600;
    text-decoration: underline dotted #e7000b;
    cursor: help;
    position: relative;
}
.kw:hover::after {
    content: attr(data-tip);
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    background: #1e1e1e;
    color: #fff;
    padding: 4px 10px;
    border-radius: 5px;
    font-size: 0.78rem;
    white-space: nowrap;
    z-index: 9999;
    pointer-events: none;
    font-weight: 400;
}
</style>
"""


def build_highlighted_html(text: str, kamus_dict: dict) -> str:
    if not kamus_dict or not text:
        return text

    # Reverse map: padanan_lower → [istilah, ...]
    rev: dict[str, list[str]] = {}
    for istilah, padanan in kamus_dict.items():
        p = padanan.strip()
        if p:
            rev.setdefault(p.lower(), []).append(istilah.strip())

    # Escape HTML
    safe = (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    # Replace terpanjang dulu (hindari partial match)
    for padanan_lower in sorted(rev.keys(), key=len, reverse=True):
        tooltip = "Istilah asli: " + " / ".join(rev[padanan_lower])
        pattern = r'(?<!\w)(' + re.escape(padanan_lower) + r')(?!\w)'
        repl    = f'<span class="kw" data-tip="{tooltip}">\\1</span>'
        safe    = re.sub(pattern, repl, safe, flags=re.IGNORECASE)

    return safe


def inject_tooltip_css() -> str:
    return _TOOLTIP_CSS