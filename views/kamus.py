import streamlit as st
import os
import sys
import pandas as pd
import requests
import base64
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth import is_logged_in, current_user, render_login_form

_BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAMUS_FILE = os.path.join(_BASE_DIR, "kamus_perbaikan.xlsx")

st.set_page_config(layout="wide")


def _github_get_file():
    token  = st.secrets["GITHUB_TOKEN"]
    repo   = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    path   = st.secrets.get("KAMUS_PATH", "kamus_perbaikan.xlsx")

    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    resp = requests.get(url, headers=headers, timeout=10)

    if resp.status_code == 404:
        df = pd.DataFrame(columns=["istilah", "padanan", "deskripsi"])
        return df, None

    resp.raise_for_status()
    data        = resp.json()
    sha         = data["sha"]
    content_b64 = data["content"]                      
    raw_bytes   = base64.b64decode(content_b64)
    df          = pd.read_excel(io.BytesIO(raw_bytes))
    df.columns  = [c.lower().strip() for c in df.columns]
    return df, sha


def _github_push_file(df: pd.DataFrame, sha: str | None, commit_message: str) -> bool:
    token  = st.secrets["GITHUB_TOKEN"]
    repo   = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    path   = st.secrets.get("KAMUS_PATH", "kamus_perbaikan.xlsx")

    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    content_b64 = base64.b64encode(buf.read()).decode()

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch":  branch,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload, timeout=15)
    if resp.status_code in (200, 201):
        return True

    st.error(f"GitHub API error {resp.status_code}: {resp.text}")
    return False

def _add_entry(istilah: str, padanan: str, deskripsi: str) -> bool:
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo  = st.secrets.get("GITHUB_REPO")

        if token and repo:
            df, sha = _github_get_file()
            for col in ["istilah", "padanan", "deskripsi"]:
                if col not in df.columns:
                    df[col] = ""
            new_row = {"istilah": istilah.strip(), "padanan": padanan.strip(), "deskripsi": deskripsi.strip()}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            user    = current_user()
            message = f"kamus: tambah '{istilah.strip()}' oleh {user}"
            success = _github_push_file(df, sha, message)
        else:
            if os.path.exists(KAMUS_FILE):
                df = pd.read_excel(KAMUS_FILE)
                df.columns = [c.lower().strip() for c in df.columns]
            else:
                df = pd.DataFrame(columns=["istilah", "padanan", "deskripsi"])
            new_row = {"istilah": istilah.strip(), "padanan": padanan.strip(), "deskripsi": deskripsi.strip()}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_excel(KAMUS_FILE, index=False)
            success = True

        if success:
            st.cache_data.clear()
        return success

    except Exception as e:
        st.error(f"Gagal menyimpan ke kamus: {e}")
        return False
    
def render(kamus_list: list):

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📚</div>
        <div>
            <h1>Kamus Padanan Kata</h1>
            <p>Temukan padanan kata Indonesia untuk istilah finansial yang muncul di berita</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not kamus_list:
        st.warning("⚠️ File kamus tidak ditemukan atau kosong. Pastikan `kamus_perbaikan.xlsx` tersedia.")
        return

    params = st.query_params
    if "kamus_letter" in params and params["kamus_letter"]:
        st.session_state.sel_letter = params["kamus_letter"]
    if "sel_letter" not in st.session_state:
        st.session_state.sel_letter = "Semua"

    search_query = st.text_input(
        label="",
        placeholder="🔍  Cari istilah atau padanan kata...",
        key="kamus_search",
        label_visibility="collapsed"
    )

    all_letters   = sorted(set(e["istilah"][0].upper() for e in kamus_list if e["istilah"]))
    huruf_options = ["Semua"] + all_letters

    container = st.container(border=True)
    with container:
        st.markdown("**Filter berdasarkan huruf:**")
        cols = st.columns(10)
        for i, huruf in enumerate(huruf_options):
            with cols[i % 10]:
                if st.button(huruf, key=f"btn_{huruf}", use_container_width=True):
                    st.session_state.sel_letter = huruf
                    st.query_params["kamus_letter"] = huruf
                    st.rerun()

    filtered = kamus_list
    if search_query.strip():
        q        = search_query.strip().lower()
        filtered = [e for e in filtered if q in e["istilah"].lower() or q in e["padanan"].lower()]
    elif st.session_state.sel_letter != "Semua":
        filtered = [e for e in filtered if e["istilah"].upper().startswith(st.session_state.sel_letter)]

    if not filtered:
        st.info("Tidak ada istilah yang ditemukan.")
    else:
        for entry in filtered:
            istilah       = entry.get("istilah", "")
            padanan       = entry.get("padanan", "")
            deskripsi     = entry.get("deskripsi", "")
            deskripsi_html = f'<div class="term-desc">{deskripsi}</div>' if deskripsi else ""

            st.markdown(
                f'<div class="term-card">'
                f'  <div class="term-icon">📖</div>'
                f'  <div style="flex:1;min-width:0;">'
                f'    <div class="term-title">{istilah}</div>'
                f'    {deskripsi_html}'
                f'    <div style="margin-top:8px;">'
                f'      <span class="padanan-label">Padanan Kata:</span>'
                f'      <span class="padanan-badge">{padanan}</span>'
                f'    </div>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown("### ➕ Tambah Padanan Kata Baru")

    if not is_logged_in():
        st.info("🔒 Login diperlukan untuk menambahkan entri baru ke kamus.")
        render_login_form(key_suffix="kamus")
        return

    st.caption(f"Menambahkan sebagai: **{current_user()}**")

    with st.form("form_tambah_kamus", clear_on_submit=True):
        istilah_baru   = st.text_input("Istilah (kata asing/teknis)", placeholder="contoh: revenue")
        padanan_baru   = st.text_input("Padanan Kata (Indonesia)", placeholder="contoh: pendapatan")
        deskripsi_baru = st.text_area("Deskripsi (opsional)", height=80,
                                      placeholder="Penjelasan singkat istilah ini...")
        submitted = st.form_submit_button("💾 Simpan ke Kamus", use_container_width=True)

    if submitted:
        if not istilah_baru.strip():
            st.error("Istilah tidak boleh kosong.")
        elif not padanan_baru.strip():
            st.error("Padanan kata tidak boleh kosong.")
        else:
            if _add_entry(istilah_baru, padanan_baru, deskripsi_baru):
                st.success(f"✅ Berhasil menambahkan: **{istilah_baru}** → **{padanan_baru}**")
                st.rerun()