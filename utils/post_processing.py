import re
import io
import os
import base64
import pandas as pd
import requests
import streamlit as st

IMBUHAN_SUFFIX = ["nya", "kan", "lah"]

_BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KAMUS_FILE = os.path.join(_BASE_DIR, "kamus_perbaikan.xlsx")


def _github_get_kamus_bytes() -> bytes | None:
    """Ambil raw bytes file kamus dari GitHub, fallback ke file lokal."""
    try:
        token  = st.secrets.get("GITHUB_TOKEN")
        repo   = st.secrets.get("GITHUB_REPO")
        branch = st.secrets.get("GITHUB_BRANCH", "main")
        path   = st.secrets.get("KAMUS_PATH", "kamus_perbaikan.xlsx")

        if token and repo:
            url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return base64.b64decode(resp.json()["content"])

        if os.path.exists(_KAMUS_FILE):
            print("Menggunakan file kamus lokal (localhost mode)")
            with open(_KAMUS_FILE, "rb") as f:
                return f.read()

        print("File kamus tidak ditemukan (GitHub maupun lokal).")
        return None

    except Exception as e:
        print(f"Error mengambil kamus: {e}")
        return None

def load_kamus(kolom_istilah="istilah", kolom_padanan="padanan") -> dict:
    try:
        raw = _github_get_kamus_bytes()
        if raw is None:
            return {}
        df = pd.read_excel(io.BytesIO(raw))
        df.columns = [c.lower().strip() for c in df.columns]
        df = df.dropna(subset=[kolom_istilah, kolom_padanan])
        kamus = dict(zip(
            df[kolom_istilah].str.strip().str.lower(),
            df[kolom_padanan].str.strip()
        ))
        print(f"Kamus dimuat: {len(kamus)} istilah")
        return kamus
    except Exception as e:
        print(f"Error memuat kamus: {e}")
        return {}


def load_kamus_for_display(kolom_istilah="istilah", kolom_padanan="padanan", kolom_deskripsi="deskripsi") -> list:
    try:
        raw = _github_get_kamus_bytes()
        if raw is None:
            return []
        df = pd.read_excel(io.BytesIO(raw))
        df.columns = [c.lower().strip() for c in df.columns]
        df = df.dropna(subset=[kolom_istilah, kolom_padanan])
        df[kolom_istilah] = df[kolom_istilah].str.strip().str.title()
        df[kolom_padanan] = df[kolom_padanan].str.strip().str.capitalize()
        has_deskripsi = kolom_deskripsi in df.columns
        result = []
        for _, row in df.iterrows():
            entry = {
                "istilah": row[kolom_istilah],
                "padanan": row[kolom_padanan],
                "deskripsi": (
                    row[kolom_deskripsi].strip().capitalize()
                    if has_deskripsi and pd.notna(row.get(kolom_deskripsi))
                    else ""
                )
            }
            result.append(entry)
        result.sort(key=lambda x: x["istilah"].lower())
        print(f"Kamus display dimuat: {len(result)} istilah")
        return result
    except Exception as e:
        print(f"Error memuat kamus display: {e}")
        return []


def ganti_istilah_dengan_imbuhan(teks: str, kamus: dict) -> str:
    hasil = teks
    kamus_terurut = sorted(kamus.items(), key=lambda x: len(x[0]), reverse=True)
    for istilah, padanan in kamus_terurut:
        hasil = re.sub(rf'\b{re.escape(istilah)}\b', padanan, hasil, flags=re.IGNORECASE)
        for suffix in IMBUHAN_SUFFIX:
            hasil = re.sub(rf'\b{re.escape(istilah)}{suffix}\b', padanan + suffix, hasil, flags=re.IGNORECASE)
    return hasil


def trim_incomplete_sentence(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return text
    last = sentences[-1].strip()
    if not re.search(r'[.!?]$', last):
        sentences = sentences[:-1]
    return ' '.join(sentences).strip()