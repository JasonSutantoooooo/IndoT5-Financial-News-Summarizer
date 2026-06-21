import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

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


def _meta_og_image(soup: BeautifulSoup) -> str:
    """Fallback umum: ambil gambar dari meta og:image, dipakai kalau selector
    spesifik per-situs tidak menemukan apa-apa."""
    tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
    if tag:
        val = (tag.get("content") or "").strip()
        if val and not val.startswith("data:"):
            return val
    return ""


def _scrape_cnbc(url: str) -> dict:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    _validate_url_integrity(url, resp, soup)

    cover_image = (
        _first_image(soup.find("div", class_="detail_image"))
        or _first_image(soup.find("figure", class_="detail_media-image"))
        or _meta_og_image(soup)
    )

    for tag in soup.find_all("table", class_="linksisip"):
        tag.decompose()

    article = (
        soup.find("div", class_="detail-text")
        or soup.find("div", {"id": "detailText"})
        or soup.find("article")
    )

    paragraphs = article.find_all("p") if article else soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return {"text": _clean_basic(text), "image": cover_image}


def _scrape_detik(url: str) -> dict:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    _validate_url_integrity(url, resp, soup)

    # Cover image artikel ada di:
    #   <div class="detail_media"><figure class="detail_media-image"><img src="..."></figure></div>
    # Diambil sebelum tag2 lain di-decompose, dan dipakai sbg fallback ketika
    # gambar dari halaman listing (get_latest_articles) tidak ketemu.
    cover_image = (
        _first_image(soup.select_one("div.detail_media figure.detail_media-image"))
        or _first_image(soup.select_one("figure.detail_media-image"))
        or _meta_og_image(soup)
    )

    for tag in soup.find_all(["script", "style", "aside", "nav"]):
        tag.decompose()

    article = (
        soup.find("div", class_="detail__body-text")
        or soup.find("div", class_="itp_bodycontent")
        or soup.find("article")
    )

    paragraphs = article.find_all("p") if article else soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return {"text": _clean_basic(text), "image": cover_image}


def _scrape_idx(url: str) -> dict:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    _validate_url_integrity(url, resp, soup)

    cover_image = (
        _first_image(soup.find("div", class_="detail-content"))
        or _meta_og_image(soup)
    )

    article = (
        soup.find("div", class_="detail-content")
        or soup.find("div", class_="entry-content")
        or soup.find("article")
    )

    paragraphs = article.find_all("p") if article else soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return {"text": _clean_basic(text), "image": cover_image}

_SCRAPERS = {
    "cnbc":  _scrape_cnbc,
    "detik": _scrape_detik,
    "idx":   _scrape_idx,
}

def scrape_article_full(url: str) -> dict:
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


def scrape_article(url: str) -> str:
    """Kompatibel dgn pemanggil lama: hanya mengembalikan teks artikel.
    Kalau butuh gambar cover juga, pakai scrape_article_full()."""
    return scrape_article_full(url)["text"]

def is_url(text: str) -> bool:
    text = text.strip()
    return text.startswith("http://") or text.startswith("https://")

_CHANNEL_LIST_URLS = {
    "cnbc":  "https://www.cnbcindonesia.com/market",
    "detik": "https://finance.detik.com/bursa-dan-valas",
    "idx":   "https://www.idxchannel.com/market-news",
}

_CHANNEL_LABELS = {
    "cnbc":  "CNBC Indonesia – Berita Market",
    "detik": "Detik Finance – Bursa & Valas",
    "idx":   "IDX Channel – Market News",
}

def _abs_url(base: str, link: str) -> str:
    if not link:
        return ""
    if link.startswith("http"):
        return link
    return urljoin(base, link)


def _first_image(tag) -> str:
    if tag is None:
        return ""
    img = tag if getattr(tag, "name", None) == "img" else tag.find("img")
    if img is None:
        return ""
    for attr in ("data-src", "data-lazy", "data-original", "src"):
        val = img.get(attr)
        if val and not val.startswith("data:"):
            return val.strip()
    srcset = img.get("srcset") or img.get("data-srcset")
    if srcset:
        return srcset.split(",")[0].strip().split(" ")[0]
    return ""


def _list_cnbc(limit: int) -> list[dict]:
    url = _CHANNEL_LIST_URLS["cnbc"]
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    results, seen = [], set()
    fallback_results, fallback_seen = [], set()

    candidates = soup.select("article") or soup.select(
        ".list-article article, .articleList article"
    )

    for art in candidates:
        a_tag = art.find("a", href=True)
        if not a_tag:
            continue
        link = _abs_url(url, a_tag["href"])
        if "cnbcindonesia.com" not in link or link in seen:
            continue

        if "/video/" in link or "cnbcindonesia.com/video" in link:
            continue
        if "/market/" not in link:
            continue

        title_tag = art.find(["h2", "h3", "h1"])
        title = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)
        if not title or title.lower().startswith("video"):
            continue

        m = re.search(r"/market/\d+-(\d+)-\d+/", link)
        is_berita_market = bool(m and m.group(1) == "17")

        item = {
            "title": title,
            "url": link,
            "image": _first_image(art),
            "source": "cnbc",
            "source_label": _CHANNEL_LABELS["cnbc"],
        }

        if is_berita_market and link not in seen:
            seen.add(link)
            results.append(item)
        elif link not in fallback_seen:
            fallback_seen.add(link)
            fallback_results.append(item)

        if len(results) >= limit:
            break

    if results:
        return results[:limit]
    return fallback_results[:limit]


def _list_detik(limit: int) -> list[dict]:
    url = _CHANNEL_LIST_URLS["detik"]
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    candidates = soup.select(
        "article.list-content__item, .media__link, .grid-row > article"
    ) or soup.select("article")

    # Detik me-render tiap artikel sbg lebih dari satu elemen di halaman
    # listing (mis. satu <a> pembungkus gambar tanpa judul, satu lagi <a>
    # judul tanpa gambar). Karena itu kita kumpulkan dulu per-link, ambil
    # judul terbaik & gambar pertama yang ditemukan dari kandidat manapun,
    # baru dibentuk jadi hasil akhir — bukan berhenti di kandidat pertama
    # yang cocok seperti sebelumnya.
    found: dict[str, dict] = {}
    order: list[str] = []

    for art in candidates:
        a_tag = art if art.name == "a" else art.find("a", href=True)
        if not a_tag or not a_tag.get("href"):
            continue
        link = _abs_url(url, a_tag["href"])
        if "detik.com" not in link:
            continue

        if any(x in link for x in (
            "/tag/", "/indeks", "20.detik.com", "video.detik.com",
            "/foto-news/", "/visual/", "kanal.detik.com",
        )):
            continue

        label_tag = art.find(class_="media__label") or art.find(class_="label")
        if label_tag and "video" in label_tag.get_text(strip=True).lower():
            continue

        title_tag = art.find(class_="media__title") or art.find(["h2", "h3"])
        title_candidate = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)
        image_candidate = _first_image(art)

        if link not in found:
            found[link] = {"title": "", "image": ""}
            order.append(link)

        if (
            title_candidate
            and not title_candidate.lower().startswith("video")
            and len(title_candidate) > len(found[link]["title"])
        ):
            found[link]["title"] = title_candidate
        if image_candidate and not found[link]["image"]:
            found[link]["image"] = image_candidate

    results = []
    for link in order:
        title = found[link]["title"].strip()
        if not title:
            continue
        results.append({
            "title": title,
            "url": link,
            "image": found[link]["image"],
            "source": "detik",
            "source_label": _CHANNEL_LABELS["detik"],
        })
        if len(results) >= limit:
            break

    return results


def _list_idx(limit: int) -> list[dict]:
    url = _CHANNEL_LIST_URLS["idx"]
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    found: dict[str, dict] = {}
    order: list[str] = []  

    for a_tag in soup.select("a[href]"):
        href = a_tag.get("href", "")
        if "/market-news/" not in href:
            continue

        link = _abs_url(url, href)
        if "idxchannel.com" not in link:
            continue
        if "/tag/" in link or "/video/" in link:
            continue

        text_candidate = a_tag.get_text(strip=True)
        attr_candidate = (a_tag.get("title") or a_tag.get("aria-label") or "").strip()
        candidate = text_candidate if len(text_candidate) >= len(attr_candidate) else attr_candidate

        image = _first_image(a_tag)

        if link not in found:
            found[link] = {"title": "", "image": ""}
            order.append(link)

        if len(candidate) > len(found[link]["title"]):
            found[link]["title"] = candidate
        if image and not found[link]["image"]:
            found[link]["image"] = image

    results = []
    for link in order:
        title = found[link]["title"].strip()
        if not title or len(title) < 8 or title.lower() in ("baca selengkapnya", "market news"):
            continue

        results.append({
            "title": title,
            "url": link,
            "image": found[link]["image"],
            "source": "idx",
            "source_label": _CHANNEL_LABELS["idx"],
        })
        if len(results) >= limit:
            break

    return results


_LIST_SCRAPERS = {
    "cnbc":  _list_cnbc,
    "detik": _list_detik,
    "idx":   _list_idx,
}


def get_latest_articles(source: str, limit: int = 5) -> list[dict]:
    scraper_fn = _LIST_SCRAPERS.get(source)
    if not scraper_fn:
        return []
    try:
        return scraper_fn(limit)
    except Exception:
        return []


def get_all_latest_articles(limit_per_channel: int = 5) -> list[dict]:
    """Gabungan berita terbaru dari semua kanal yang didukung saat ini."""
    all_articles = []
    for source in _LIST_SCRAPERS:
        all_articles.extend(get_latest_articles(source, limit_per_channel))
    return all_articles