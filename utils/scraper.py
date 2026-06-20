import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Referer": "https://www.google.com/",
}

TIMEOUT = 15
_SUPPORTED = "cnbcindonesia.com, detik.com, idxchannel.com"

def _get_canonical_url(soup: BeautifulSoup) -> str | None:
    tag = soup.find("link", rel="canonical") or soup.find("meta", property="og:url")
    if tag:
        return (tag.get("href") or tag.get("content") or "").strip()
    return None

def _normalize(url: str) -> str:
    url = url.split("?")[0].rstrip("/")
    return url.lower()

def _validate_url_integrity(requested_url: str, resp: requests.Response, soup: BeautifulSoup) -> None:
    final_url = resp.url
    if _normalize(final_url) != _normalize(requested_url) and not final_url.startswith(requested_url):
        canonical = _get_canonical_url(soup)
        if canonical and _normalize(canonical) != _normalize(requested_url):
            raise ValueError(
                f"URL tidak lengkap/valid. Anda memasukkan:\n  {requested_url}\n"
                f"tapi server mengarahkan ke artikel lain:\n  {canonical or final_url}"
            )

    canonical = _get_canonical_url(soup)
    if canonical and _normalize(canonical) != _normalize(requested_url):
        raise ValueError(
            f"URL tidak sesuai dengan artikel aslinya. Mungkin yang anda maksud: {canonical}"
        )

def _detect_source(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "cnbcindonesia" in domain:
        return "cnbc"
    if "detik" in domain:
        return "detik"
    if "idxchannel" in domain:
        return "idx"
    return "unknown"


def _clean_basic(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _scrape_cnbc(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    _validate_url_integrity(url, resp, soup)

    for tag in soup.find_all("table", class_="linksisip"):
        tag.decompose()

    article = (
        soup.find("div", class_="detail-text")
        or soup.find("div", {"id": "detailText"})
        or soup.find("article")
    )

    paragraphs = article.find_all("p") if article else soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return _clean_basic(text)


def _scrape_detik(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    _validate_url_integrity(url, resp, soup)

    for tag in soup.find_all(["script", "style", "aside", "nav"]):
        tag.decompose()

    article = (
        soup.find("div", class_="detail__body-text")
        or soup.find("div", class_="itp_bodycontent")
        or soup.find("article")
    )

    paragraphs = article.find_all("p") if article else soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return _clean_basic(text)


def _scrape_idx(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    _validate_url_integrity(url, resp, soup)

    article = (
        soup.find("div", class_="detail-content")
        or soup.find("div", class_="entry-content")
        or soup.find("article")
    )

    paragraphs = article.find_all("p") if article else soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return _clean_basic(text)

_SCRAPERS = {
    "cnbc":  _scrape_cnbc,
    "detik": _scrape_detik,
    "idx":   _scrape_idx,
}

def scrape_article(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        raise ValueError(f"URL tidak valid: {url}")

    source = _detect_source(url)

    if source not in _SCRAPERS:
        raise ValueError(
            f"Sumber berita tidak didukung. "
            f"Gunakan salah satu dari: {_SUPPORTED}"
        )

    return _SCRAPERS[source](url)

def is_url(text: str) -> bool:
    text = text.strip()
    return text.startswith("http://") or text.startswith("https://")