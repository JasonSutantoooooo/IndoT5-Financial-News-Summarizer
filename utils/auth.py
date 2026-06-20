import hashlib
import secrets
import streamlit as st

from datetime import datetime, timedelta, timezone
from supabase import create_client, Client


# ── Supabase client ───────────────────────────────────────────────────────────

@st.cache_resource
def _get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def _get_salt() -> str:
    try:
        return st.secrets["supabase"]["salt"]
    except Exception:
        return "indot5-fallback-salt"


def _hash(password: str) -> str:
    return hashlib.sha256((_get_salt() + password).encode()).hexdigest()

def _generate_session_token():
    return secrets.token_hex(32)


def restore_login():
    if "logged_in" in st.session_state:
        return

    # Ambil token dari URL query params
    token = st.query_params.get("session")

    if not token:
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["is_admin"] = False
        return

    try:
        res = (
            _get_client()
            .table("users")
            .select("username, session_expired_at, is_admin")
            .eq("session_token", token)
            .execute()
        )

        if not res.data:
            raise Exception("Token tidak ditemukan")

        user = res.data[0]

        expired_at = datetime.fromisoformat(
            user["session_expired_at"].replace("Z", "+00:00")
        )

        if expired_at < datetime.now(timezone.utc):
            raise Exception("Token expired")

        st.session_state["logged_in"] = True
        st.session_state["username"] = user["username"]
        st.session_state["is_admin"] = bool(user.get("is_admin", False))

    except Exception:
        # Hapus token invalid dari URL
        st.query_params.clear()
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["is_admin"] = False

# ── Session helpers ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def current_user() -> str | None:
    return st.session_state.get("username", None)


def is_admin() -> bool:
    return st.session_state.get("logged_in", False) and st.session_state.get("is_admin", False)


# ── Auth logic ────────────────────────────────────────────────────────────────

def login(username: str, password: str) -> bool:
    uname = username.lower().strip()

    try:
        res = (
            _get_client()
            .table("users")
            .select("id, password_hash, is_admin")
            .eq("username", uname)
            .execute()
        )

        if not res.data:
            return False

        user = res.data[0]

        if user["password_hash"] != _hash(password):
            return False

        token = _generate_session_token()
        expired_at = (
            datetime.now(timezone.utc) + timedelta(days=30)
        ).isoformat()

        _get_client().table("users").update({
            "session_token": token,
            "session_expired_at": expired_at
        }).eq("id", user["id"]).execute()

        # Simpan token ke URL query params
        st.query_params["session"] = token

        st.session_state["logged_in"] = True
        st.session_state["username"] = uname
        st.session_state["is_admin"] = bool(user.get("is_admin", False))

        return True

    except Exception:
        return False


def register(username: str, password: str) -> tuple[bool, str]:
    uname = username.lower().strip()

    if len(uname) < 3:
        return False, "Username minimal 3 karakter."
    if not uname.replace("_", "").isalnum():
        return False, "Username hanya boleh huruf, angka, dan underscore."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."

    try:
        res = (
            _get_client()
            .table("users")
            .select("username")
            .eq("username", uname)
            .execute()
        )
        if res.data:
            return False, f"Username '{uname}' sudah digunakan."

        _get_client().table("users").insert({
            "username":      uname,
            "password_hash": _hash(password),
        }).execute()
        return True, ""
    except Exception as e:
        return False, f"Gagal mendaftar: {e}"


def logout():
    token = st.query_params.get("session")

    try:
        if token:
            _get_client().table("users").update({
                "session_token": None,
                "session_expired_at": None
            }).eq("session_token", token).execute()
    except Exception:
        pass

    # Hapus token dari URL
    st.query_params.clear()

    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["is_admin"] = False


# ── UI Components ─────────────────────────────────────────────────────────────

def render_login_form(key_suffix: str = ""):
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Daftar Akun"])

    with tab_login:
        with st.form(f"form_login_{key_suffix}", clear_on_submit=False):
            username  = st.text_input("Username", key=f"li_u_{key_suffix}")
            password  = st.text_input("Password", type="password", key=f"li_p_{key_suffix}")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            if login(username, password):
                st.success(f"Selamat datang, **{username.lower()}**!")
                st.rerun()
            else:
                st.error("Username atau password salah.")

    with tab_register:
        st.caption("Buat akun baru — gratis, tidak ada batasan.")
        with st.form(f"form_reg_{key_suffix}", clear_on_submit=True):
            new_u  = st.text_input("Username", key=f"rg_u_{key_suffix}")
            new_p  = st.text_input("Password", type="password", key=f"rg_p_{key_suffix}")
            new_p2 = st.text_input("Konfirmasi Password", type="password", key=f"rg_p2_{key_suffix}")
            submitted = st.form_submit_button("Daftar", use_container_width=True)
        if submitted:
            if new_p != new_p2:
                st.error("Password dan konfirmasi tidak sama.")
            else:
                ok, msg = register(new_u, new_p)
                if ok:
                    login(new_u, new_p)
                    st.success(f"Akun **{new_u.lower()}** berhasil dibuat!")
                    st.rerun()
                else:
                    st.error(msg)


def render_sidebar_auth():
    if is_logged_in():
        st.sidebar.markdown(f"👤 **{current_user()}**")
        if st.sidebar.button("Logout", use_container_width=True, key="btn_logout"):
            logout()
            st.rerun()
    else:
        st.sidebar.markdown("👤 Guest Mode")