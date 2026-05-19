import streamlit as st
import streamlit.components.v1 as components
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.post_processing import ganti_istilah_dengan_imbuhan
from utils.preprocess      import clean_noise
from utils.scraper         import scrape_article, is_url
from utils.model_loader    import summarize
from utils.lang_detector   import is_indonesian_text
from utils.auth            import is_logged_in, current_user
from utils.riwayat         import add_history
from utils.highlight       import build_highlighted_html, inject_tooltip_css


def render(kamus: dict):

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📰</div>
        <div>
            <h1>Ringkasan Artikel Berita Finansial</h1>
            <p>Masukkan URL artikel atau teks berita untuk mendapatkan ringkasan otomatis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(inject_tooltip_css(), unsafe_allow_html=True)

    with st.container():
        st.write("URL Artikel atau Teks Berita")
        input_text = st.text_area(
            label="",
            height=200,
            placeholder="Masukkan URL artikel (cnbcindonesia.com, detik.com, dan idxchannel.com) atau teks berita langsung...",
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

    if "ringkasan_output"      not in st.session_state:
        st.session_state.ringkasan_output      = None
    if "ringkasan_time"        not in st.session_state:
        st.session_state.ringkasan_time        = None
    if "ringkasan_source_type" not in st.session_state:
        st.session_state.ringkasan_source_type = None
    if "ringkasan_input_raw"   not in st.session_state:
        st.session_state.ringkasan_input_raw   = None

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
                    source_type  = "text"

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

                    st.session_state.ringkasan_output      = final_output
                    st.session_state.ringkasan_time        = elapsed
                    st.session_state.ringkasan_source_type = source_type
                    st.session_state.ringkasan_input_raw   = raw_input

                    if is_logged_in():
                        add_history(
                            username   = current_user(),
                            input_type = source_type,
                            input_raw  = raw_input,
                            summary    = final_output,
                        )

            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {e}")

    if st.session_state.ringkasan_output:
        source_label = (
            "🔗 Disarikan dari URL"
            if st.session_state.ringkasan_source_type == "url"
            else "📝 Disarikan dari teks"
        )

        display_text = (
            build_highlighted_html(st.session_state.ringkasan_output, kamus)
            if kamus
            else st.session_state.ringkasan_output
        )

        encoded = json.dumps(st.session_state.ringkasan_output)

        components.html(f"""
        <style>
          body {{ margin:0; padding:0; font-family: sans-serif; }}
          .result-card {{
            background: #EBF4FF;
            border-radius: 16px;
            padding: 24px;
          }}
          .result-card-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: 16px;
            color: #1d293d;
          }}
          .result-text-box {{
            background: white;
            border-radius: 10px;
            padding: 16px 20px;
            font-size: 0.97rem;
            line-height: 1.8;
            color: #1a1a1a;
            margin-bottom: 12px;
          }}
          .result-meta {{
            font-size: 0.8rem;
            color: #6b7280;
            margin-bottom: 14px;
          }}
          .time-value {{
            color: #e7000b;
            font-weight: 600;
          }}
          .result-text-box {{
            overflow: visible !important;
          }}
          .kw {{
            color: #e7000b;
            font-weight: 600;
            text-decoration: underline dotted #e7000b;
            cursor: help;
            position: relative;
            display: inline;
          }}
          .kw::after {{
            content: attr(data-tip);
            display: none;
            position: absolute;
            bottom: 130%;
            left: 50%;
            transform: translateX(-50%);
            background: #1e1e1e;
            color: #fff;
            padding: 4px 10px;
            border-radius: 5px;
            font-size: 0.75rem;
            white-space: nowrap;
            z-index: 9999;
            pointer-events: none;
            font-weight: 400;
          }}
          .kw:hover::after {{
            display: block;
          }}
          #btn_copy {{
            background: #e7000b;
            color: white;
            border: none;
            padding: 7px 18px;
            border-radius: 7px;
            cursor: pointer;
            font-size: 0.85rem;
          }}
          #btn_copy:hover {{ background: #c00009; }}
        </style>

        <div class="result-card">
          <div class="result-card-header">
            <span>✨</span>
            <span>Hasil Ringkasan</span>
          </div>
          <div class="result-text-box">{display_text}</div>
          <div class="result-meta">
            ⏱ Waktu Proses:&nbsp;<span class="time-value">{st.session_state.ringkasan_time} detik</span>
            &nbsp;·&nbsp; {source_label}
          </div>
          <button id="btn_copy">📋 Salin Ringkasan</button>
        </div>

        <script>
          document.getElementById('btn_copy').addEventListener('click', function() {{
            navigator.clipboard.writeText({encoded}).then(() => {{
              this.innerText = '✅ Tersalin!';
              setTimeout(() => this.innerText = '📋 Salin Ringkasan', 2000);
            }});
          }});
        </script>
        """, height=350, scrolling=True)

        if not is_logged_in():
            st.caption("💡 Login untuk menyimpan history ringkasan Anda.")
        else:
            st.caption(f"✅ Ringkasan disimpan ke history akun **{current_user()}**.")