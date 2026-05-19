import streamlit as st
from utils.auth import _get_client


# ── Public API ────────────────────────────────────────────────────────────────

def add_history(username: str, input_type: str, input_raw: str, summary: str):
    """Simpan satu entry ringkasan. input_type: 'url' | 'text'."""
    try:
        _get_client().table("history").insert({
            "username":   username,
            "input_type": input_type,
            "input_raw":  input_raw,
            "summary":    summary,
        }).execute()
    except Exception as e:
        # Gagal simpan history tidak boleh crash app utama
        st.warning(f"Gagal menyimpan history: {e}")


def load_history(username: str) -> list[dict]:
    """Ambil semua history user, diurutkan terbaru di atas."""
    try:
        res = (
            _get_client()
            .table("history")
            .select("*")
            .eq("username", username)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def delete_history(entry_id: str):
    """Hapus satu entry berdasarkan id (UUID)."""
    try:
        _get_client().table("history").delete().eq("id", entry_id).execute()
    except Exception as e:
        st.warning(f"Gagal menghapus entry: {e}")


def clear_history(username: str):
    """Hapus seluruh history milik user."""
    try:
        _get_client().table("history").delete().eq("username", username).execute()
    except Exception as e:
        st.warning(f"Gagal menghapus history: {e}")