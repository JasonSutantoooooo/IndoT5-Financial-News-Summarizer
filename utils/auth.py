import hashlib
import streamlit as st
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


# ── Session helpers ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def current_user() -> str | None:
    return st.session_state.get("username", None)


# ── Auth logic ────────────────────────────────────────────────────────────────

def login(username: str, password: str) -> bool:
    uname = username.lower().strip()
    try:
        res = (
            _get_client()
            .table("users")
            .select("password_hash")
            .eq("username", uname)
            .execute()
        )
        if not res.data:
            return False
        if res.data[0]["password_hash"] != _hash(password):
            return False
        st.session_state["logged_in"] = True
        st.session_state["username"]  = uname
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
        # Cek duplikat
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
    st.session_state["logged_in"] = False
    st.session_state["username"]  = None


# ── UI Components ─────────────────────────────────────────────────────────────

def render_login_form(key_suffix: str = ""):
    """Form login + register dalam tab. Dipanggil di halaman yang butuh auth."""
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
                    st.success(f"Akun **{new_u.lower()}** berhasil dibuat! Silakan login.")
                else:
                    st.error(msg)


def render_sidebar_auth():
    """Info user + tombol logout di sidebar."""
    if is_logged_in():
        st.sidebar.markdown(f"👤 **{current_user()}**")
        if st.sidebar.button("Logout", use_container_width=True, key="btn_logout"):
            logout()
            st.rerun()
    else:
        st.sidebar.markdown("👤 *Belum login*")