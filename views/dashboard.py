import streamlit as st
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.scraper      import get_latest_articles, scrape_article, scrape_article_full
from utils.preprocess   import clean_noise
from utils.model_loader import summarize
from utils.lang_detector import is_indonesian_text
from utils.post_processing import ganti_istilah_dengan_imbuhan
from utils.highlight     import build_highlighted_html, inject_tooltip_css

WIB = timezone(timedelta(hours=7))

ARTICLES_PER_CHANNEL = 5

_CHANNEL_META = {
    "cnbc":  {"label": "CNBC Indonesia", "color": "#0E4DA4", "icon": "🟦"},
    "detik": {"label": "Detik Finance",  "color": "#0073E6", "icon": "🔵"},
    "idx":   {"label": "IDX Channel",    "color": "#e7000b", "icon": "🟥"},
}

_PLACEHOLDER_IMG = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='400' height='240'>"
    "<rect width='100%25' height='100%25' fill='%23e2e8f0'/>"
    "<text x='50%25' y='50%25' font-size='40' text-anchor='middle' "
    "fill='%2394a3b8' dy='.3em'>📰</text></svg>"
)


_HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_BULAN_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def _format_tanggal_indo(dt: datetime) -> str:
    """Format tanggal manual ke Bahasa Indonesia, tidak gantung ke locale
    sistem (banyak server hosting tidak punya locale id_ID ter-install)."""
    hari  = _HARI_ID[dt.weekday()]
    bulan = _BULAN_ID[dt.month - 1]
    return f"{hari}, {dt.day:02d} {bulan} {dt.year}"


def _today_key() -> str:
    return datetime.now(WIB).strftime("%Y-%m-%d")


@st.cache_data(ttl=86400, show_spinner=False)
def _build_daily_digest(cache_date: str, per_channel: int, _kamus_dict: dict | None) -> dict:
    digest = {"items": [], "failed_channels": [], "generated_at": datetime.now(WIB).isoformat()}

    for source in ("cnbc", "detik", "idx"):
        meta = _CHANNEL_META[source]
        try:
            articles = get_latest_articles(source, limit=per_channel)
        except Exception:
            articles = []

        if not articles:
            digest["failed_channels"].append(meta["label"])
            continue

        for art in articles:
            try:
                scraped   = scrape_article_full(art["url"])
                raw_text  = scraped["text"]

                if not raw_text or len(raw_text.strip()) <= 10:
                    continue

                cleaned = clean_noise(raw_text)

                if not is_indonesian_text(cleaned):
                    continue

                summary = summarize(cleaned)

                if _kamus_dict:
                    summary = ganti_istilah_dengan_imbuhan(summary, _kamus_dict)
                    summary = build_highlighted_html(summary, _kamus_dict)

                image = art.get("image") or scraped.get("image") or ""

                digest["items"].append({
                    "title":        art["title"],
                    "url":          art["url"],
                    "image":        image,
                    "summary":      summary,
                    "source":       source,
                    "source_label": meta["label"],
                })
            except Exception:
                continue

    return digest


def _render_card(item: dict):
    meta  = _CHANNEL_META.get(item["source"], {"label": item["source_label"], "color": "#64748b", "icon": "📰"})
    image = item["image"] if item["image"] else _PLACEHOLDER_IMG

    st.markdown(f"""
    <div class="dash-card">
        <div class="dash-card-img-wrap">
            <img src="{image}" class="dash-card-img" onerror="this.src='{_PLACEHOLDER_IMG}'"/>
        </div>
        <div class="dash-card-body">
            <span class="dash-card-badge" style="background:{meta['color']};">{meta['icon']} {meta['label']}</span>
            <div class="dash-card-title">{item['title']}</div>
            <div class="dash-card-summary">{item['summary']}</div>
            <a href="{item['url']}" target="_blank" class="dash-card-link">Baca artikel asli ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _inject_css():
    st.markdown("""
    <style>
    .dash-meta-bar {
        display:flex;
        align-items:center;
        justify-content:space-between;
        flex-wrap:wrap;
        gap:10px;
        margin-bottom:18px;
    }
    .dash-meta-bar .dash-date {
        font-size:0.92rem;
        color:#475569;
    }

    div[data-testid="stMarkdown"]:has(div.dash-card) {
        margin-bottom:16px;
    }

    .dash-card {
        background:white;
        border:1px solid #e5e7eb;
        border-radius:14px;
        overflow:hidden;
        display:flex;
        flex-direction:row;
        align-items:stretch;
        transition:box-shadow 0.15s ease;
    }
    .dash-card:hover {
        box-shadow:0 6px 18px rgba(0,0,0,0.08);
    }
    .dash-card-img-wrap {
        flex:0 0 220px;
        max-width:220px;
        background:#e2e8f0;
        overflow:hidden;
    }
    .dash-card-img {
        width:100%;
        height:100%;
        object-fit:cover;
        display:block;
        min-height:160px;
    }
    .dash-card-badge {
        display:inline-block;
        color:white;
        font-size:0.72rem;
        font-weight:600;
        padding:4px 10px;
        border-radius:999px;
        margin-bottom:10px;
    }
    .dash-card-body {
        padding:18px 22px;
        display:flex;
        flex-direction:column;
        flex:1;
        min-width:0;
    }
    .dash-card-title {
        font-weight:700;
        font-size:1.08rem;
        line-height:1.4;
        color:#1d293d;
        margin-bottom:10px;
    }
    .dash-card-summary {
        font-size:0.92rem;
        line-height:1.7;
        color:#475569;
        margin-bottom:14px;
        white-space:pre-line;
    }
    .dash-card-link {
        font-size:0.84rem;
        font-weight:600;
        color:#e7000b;
        text-decoration:none;
        align-self:flex-start;
        margin-top:auto;
    }
    .dash-card-link:hover {
        text-decoration:underline;
    }
    .dash-empty-channel {
        font-size:0.85rem;
        color:#94a3b8;
        font-style:italic;
        margin-top:-8px;
        margin-bottom:18px;
    }

    @media (max-width: 640px) {
        .dash-card {
            flex-direction:column;
        }
        .dash-card-img-wrap {
            flex:0 0 auto;
            max-width:100%;
            width:100%;
        }
        .dash-card-img {
            min-height:180px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render(kamus: dict = None):
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🗞️</div>
        <div>
            <h1>Dashboard Berita Hari Ini</h1>
            <p>Ringkasan otomatis berita finansial terbaru dari 3 kanal berita</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _inject_css()
    st.markdown(inject_tooltip_css(), unsafe_allow_html=True)

    st.warning(
        "⚠️ Ringkasan dihasilkan secara otomatis oleh sistem mungkin mengandung kesalahan atau ketidakakuratan informasi. "
        "Pengguna disarankan untuk tetap memverifikasi informasi dengan artikel asli. "
        "Segala kerugian finansial atau keputusan yang diambil berdasarkan hasil ringkasan bukan merupakan tanggung jawab aplikasi."
    )

    today_str = _format_tanggal_indo(datetime.now(WIB))

    col_meta, col_btn = st.columns([4, 1])
    with col_meta:
        st.markdown(f'<div class="dash-date">📅 {today_str} · WIB</div>', unsafe_allow_html=True)
    with col_btn:
        refresh = st.button("🔄 Perbarui", use_container_width=True, help="Ambil ulang berita & ringkasan hari ini")

    if refresh:
        _build_daily_digest.clear()

    with st.spinner("Mengambil & meringkas berita hari ini... (proses ini hanya berjalan sekali per hari)"):
        digest = _build_daily_digest(_today_key(), ARTICLES_PER_CHANNEL, kamus)

    if digest["failed_channels"]:
        st.warning(
            "⚠️ Gagal mengambil berita dari: "
            + ", ".join(digest["failed_channels"])
            + ". Kanal lain tetap ditampilkan."
        )

    items = digest["items"]

    if not items:
        st.info("Belum ada ringkasan berita yang berhasil diproses hari ini. Coba tekan **🔄 Perbarui**.")
        return

    st.caption(f"✅ {len(items)} berita berhasil diringkas · diperbarui {datetime.fromisoformat(digest['generated_at']).strftime('%H:%M')} WIB")

    tab_all, tab_cnbc, tab_detik, tab_idx = st.tabs([
        "🗂️ Semua", "🟦 CNBC – Berita Market", "🔵 Detik – Bursa & Valas", "🟥 IDX – Market News"
    ])

    def _list(filtered_items):
        if not filtered_items:
            st.markdown('<div class="dash-empty-channel">Tidak ada berita yang berhasil diringkas dari kanal ini hari ini.</div>', unsafe_allow_html=True)
            return
        for item in filtered_items:
            _render_card(item)

    with tab_all:
        _list(items)
    with tab_cnbc:
        _list([i for i in items if i["source"] == "cnbc"])
    with tab_detik:
        _list([i for i in items if i["source"] == "detik"])
    with tab_idx:
        _list([i for i in items if i["source"] == "idx"])