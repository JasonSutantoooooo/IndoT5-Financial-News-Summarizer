import streamlit as st
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.post_processing import ganti_istilah_dengan_imbuhan
from utils.preprocess import clean_noise
from utils.scraper import scrape_article, is_url
from utils.model_loader import summarize
from utils.lang_detector import is_indonesian_text


def render(kamus: dict):

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📰</div>
        <div>
            <h1>Ringkasan Artikel Berita</h1>
            <p>Masukkan URL artikel atau teks berita untuk mendapatkan ringkasan otomatis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.write("URL Artikel atau Teks Berita")

        input_text = st.text_area(
            label="",
            height=200,
            placeholder="Masukkan URL artikel (cnbcindonesia.com, detik.com, dan idxchannel.com) dawg atau teks berita langsung...",
            key="input_ringkasan",
            label_visibility="collapsed"
        )

        process = st.button(
            "Buat Ringkasan",
            icon="✨",
            use_container_width=True,
            key="btn_ringkas",
            type="primary",
        )

    st.warning(
        "⚠️ Ringkasan dihasilkan secara otomatis oleh sistem mungkin mengandung kesalahan atau ketidakakuratan informasi. "
        "Pengguna disarankan untuk tetap memverifikasi informasi dengan artikel asli. "
        "Segala kerugian finansial atau keputusan yang diambil berdasarkan hasil ringkasan bukan merupakan tanggung jawab aplikasi."
    )

    if "ringkasan_output" not in st.session_state:
        st.session_state.ringkasan_output = None
    if "ringkasan_time" not in st.session_state:
        st.session_state.ringkasan_time = None
    if "ringkasan_source_type" not in st.session_state:
        st.session_state.ringkasan_source_type = None

    if process:
        raw_input = input_text.strip()

        if not raw_input:
            st.warning("⚠️ Silakan masukkan URL artikel atau teks berita terlebih dahulu.")

        elif not is_url(raw_input) and len(raw_input) <= 10:
            st.warning("⚠️ Teks berita terlalu singkat. Masukkan teks yang lebih lengkap (lebih dari 10 karakter).")

        else:
            start = time.time()

            try:
                if is_url(raw_input):
                    status_placeholder = st.empty()
                    status_placeholder.info("🔗 Mengambil teks dari URL...")
                    article_text = scrape_article(raw_input)

                    if not article_text or len(article_text.strip()) <= 10:
                        status_placeholder.empty()
                        st.error("❌ Gagal mengambil teks dari URL. Pastikan URL valid dan dapat diakses.")
                        st.stop()

                    status_placeholder.empty()
                    source_type = "url"
                else:
                    article_text = raw_input
                    source_type = "text"

                cleaned_text = clean_noise(article_text)

                if not is_indonesian_text(cleaned_text):
                    st.error("⚠️ Link atau teks artikel berita yang dimasukkan tidak terdeteksi sebagai bahasa Indonesia. Harap masukkan teks dalam bahasa Indonesia.")
                    st.stop()

                with st.spinner("Memproses..."):
                    raw_output = summarize(cleaned_text)

                    if kamus:
                        final_output = ganti_istilah_dengan_imbuhan(raw_output, kamus)
                    else:
                        final_output = raw_output

                    elapsed = round(time.time() - start, 2)

                    st.session_state.ringkasan_output    = final_output
                    st.session_state.ringkasan_time      = elapsed
                    st.session_state.ringkasan_source_type = source_type

            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {e}")

    if st.session_state.ringkasan_output:
        source_label = (
            "🔗 Disarikan dari URL"
            if st.session_state.ringkasan_source_type == "url"
            else "📝 Disarikan dari teks"
        )

        st.markdown(f"""
        <div class="result-card">
            <div class="result-card-header">
                <span>✨</span>
                <span>Hasil Ringkasan</span>
            </div>
            <div class="result-text-box">
                {st.session_state.ringkasan_output}
            </div>
            <div class="result-meta">
                ⏱ Waktu Proses:&nbsp;<span class="time-value">{st.session_state.ringkasan_time} detik</span>
                &nbsp;·&nbsp; {source_label}
            </div>
        </div>
        """, unsafe_allow_html=True)