import streamlit as st
import streamlit.components.v1 as components
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth      import is_logged_in, current_user, render_login_form
from utils.history   import load_history
from utils.highlight import build_highlighted_html


def _to_wib(iso_str: str) -> str:
    """Konversi ISO timestamp dari Supabase (UTC) ke WIB (UTC+7)."""
    if not iso_str or iso_str == "-":
        return "-"
    try:
        from datetime import datetime, timezone, timedelta
        WIB = timezone(timedelta(hours=7))
        # Supabase format: 2024-01-01T10:00:00+00:00 atau 2024-01-01T10:00:00.000000+00:00
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(WIB).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Fallback: ambil string mentah + tambah 7 jam manual tidak reliable, return as-is
        return iso_str[:19].replace("T", " ")


def render(kamus: dict = None):

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📚</div>
        <div>
            <h1>History Ringkasan</h1>
            <p>Riwayat ringkasan berita yang pernah Anda proses</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not is_logged_in():
        st.info("🔒 Silakan login untuk melihat history ringkasan Anda.")
        render_login_form(key_suffix="history")
        return

    username = current_user()
    entries  = load_history(username)

    if not entries:
        st.info("Belum ada history. Coba ringkas berita terlebih dahulu!")
        return

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"**{len(entries)} ringkasan** tersimpan untuk akun **{username}**.")

    st.divider()

    # ── List entry ────────────────────────────────────────────────────────────
    for i, entry in enumerate(entries):
        input_type = entry.get("input_type", "text")
        timestamp  = _to_wib(entry.get("created_at", "-"))
        input_raw  = entry.get("input_raw", "")
        summary    = entry.get("summary", "")
        entry_id   = entry.get("id", str(i))

        icon  = "🔗" if input_type == "url" else "📝"
        label = "URL" if input_type == "url" else "Teks"

        with st.expander(f"{icon} [{timestamp} WIB]  —  {label}", expanded=(i == 0)):

            if input_type == "url":
                st.markdown(f"**🔗 URL:** [{input_raw}]({input_raw})")
            else:
                with st.expander("Lihat artikel asli"):
                    st.text_area(
                        label="Artikel asli",
                        value=input_raw,
                        height=160,
                        disabled=True,
                        key=f"orig_{entry_id}",
                        label_visibility="collapsed",
                    )

            st.markdown("**✨ Hasil Ringkasan:**")
            display_text = (
                build_highlighted_html(summary, kamus)
                if kamus else summary
            )
            encoded = json.dumps(summary)

            # Card + tombol copy dalam satu components.html
            components.html(f"""
            <style>
              body {{ margin:0; padding:0; font-family: sans-serif; }}
              .result-text-box {{
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 10px;
                padding: 14px 18px;
                font-size: 0.95rem;
                line-height: 1.8;
                color: #1a1a1a;
                margin-bottom: 10px;
                overflow: visible;
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
              .kw:hover::after {{ display: block; }}
              #btn_copy_{i} {{
                background: #e7000b;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 7px;
                cursor: pointer;
                font-size: 0.82rem;
              }}
              #btn_copy_{i}:hover {{ background: #c00009; }}
            </style>

            <div class="result-text-box">{display_text}</div>
            <button id="btn_copy_{i}">📋 Salin Ringkasan</button>

            <script>
              document.getElementById('btn_copy_{i}').addEventListener('click', function() {{
                navigator.clipboard.writeText({encoded}).then(() => {{
                  this.innerText = '✅ Tersalin!';
                  setTimeout(() => this.innerText = '📋 Salin Ringkasan', 2000);
                }});
              }});
            </script>
            """, height=200, scrolling=True)