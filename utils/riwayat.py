import streamlit as st
from utils.auth import _get_client

def add_history(username: str, input_type: str, input_raw: str, summary: str):
    try:
        _get_client().table("history").insert({
            "username":   username,
            "input_type": input_type,
            "input_raw":  input_raw,
            "summary":    summary,
        }).execute()
    except Exception as e:
        st.warning(f"Gagal menyimpan history: {e}")


def load_history(username: str) -> list[dict]:
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