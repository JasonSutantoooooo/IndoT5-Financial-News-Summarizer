import re
import requests
import cloudscraper
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


def _detect_source(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "cnbcindonesia" in domain:
        return "cnbc"
    if "detik" in domain:
        return "detik"
    # if "kontan" in domain:
    #     return "kontan"
    # if "investor.id" in domain:
    #     return "investor"
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

    for tag in soup.find_all("table", class_="linksisip"):
        tag.decompose()

    article = (
        soup.find("div", class_="detail-text")
        or soup.find("div", {"id": "detailText"})
        or soup.find("article")
    )

    if article:
        paragraphs = article.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    text = " ".join(p.get_text() for p in paragraphs)
    return _clean_basic(text)


def _scrape_detik(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup.find_all(["script", "style", "aside", "nav"]):
        tag.decompose()

    article = (
        soup.find("div", class_="detail__body-text")
        or soup.find("div", class_="itp_bodycontent")
        or soup.find("article")
    )

    if article:
        paragraphs = article.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    text = " ".join(p.get_text() for p in paragraphs)
    return _clean_basic(text)


# def _scrape_kontan(url: str) -> str:
#     scraper = cloudscraper.create_scraper()
#     resp = scraper.get(url, timeout=TIMEOUT)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "lxml")

#     # Hapus elemen noise
#     for tag in soup.find_all(["script", "style", "aside", "nav", "figure"]):
#         tag.decompose()

#     article = (
#         soup.find("div", class_="tmpt-desk-kon") 
#         or soup.find("div", itemprop="articleBody") 
#         or soup.find("div", class_="detail-content")
#         or soup.find("article")
#     )

#     if article:
#         paragraphs = article.find_all("p")
#     else:
#         paragraphs = soup.find_all("p")

#     text = " ".join(p.get_text() for p in paragraphs)
#     return _clean_basic(text)

# def _scrape_investor(url: str) -> str:
#     resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "lxml")

#     article = (
#         soup.find("div", class_="detail-artikel")
#         or soup.find("div", class_="content-detail")
#         or soup.find("article")
#     )

#     if article:
#         paragraphs = article.find_all("p")
#     else:
#         paragraphs = soup.find_all("p")

#     text = " ".join(p.get_text() for p in paragraphs)
#     return _clean_basic(text)


def _scrape_idx(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    article = (
        soup.find("div", class_="detail-content")
        or soup.find("div", class_="entry-content")
        or soup.find("article")
    )

    if article:
        paragraphs = article.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    text = " ".join(p.get_text() for p in paragraphs)
    return _clean_basic(text)


def _scrape_generic(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return _clean_basic(text)


# ── Dispatcher utama ──────────────────────────────────────────────────────────

_SCRAPERS = {
    "cnbc":     _scrape_cnbc,
    "detik":    _scrape_detik,
    # "kontan":   _scrape_kontan,
    # "investor": _scrape_investor,
    "idx":      _scrape_idx,
}


def scrape_article(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        raise ValueError(f"URL tidak valid: {url}")

    source = _detect_source(url)
    scraper_fn = _SCRAPERS.get(source, _scrape_generic)

    text = scraper_fn(url)
    return text


def is_url(text: str) -> bool:
    text = text.strip()
    return text.startswith("http://") or text.startswith("https://")
