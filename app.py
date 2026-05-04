import streamlit as st
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from utils.post_processing import load_kamus, load_kamus_for_display
from views import ringkasan, kamus, tentang
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="News Summarizer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None,
)

def load_css():
    css_file = os.path.join(BASE_DIR, "assets", "styles.css")
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ File CSS tidak ditemukan. Pastikan `assets/styles.css` tersedia.")

load_css()

KAMUS_FILE = os.path.join(BASE_DIR, "kamus_perbaikan.xlsx")

@st.cache_data
def get_kamus_dict():
    return load_kamus(KAMUS_FILE)

@st.cache_data
def get_kamus_list():
    return load_kamus_for_display(KAMUS_FILE)

kamus_dict = get_kamus_dict()
kamus_list = get_kamus_list()

with st.sidebar:
    st.markdown("## 📰 Financial News Summarizer")

    selected_menu = option_menu(
        menu_title=None,
        options=["Ringkasan Berita", "Kamus Padanan", "Tentang Pembuat"],
        icons=['file-text', 'book', 'person'],
        default_index=0,
        styles={
            "container": {
                "padding": "0!important",
                "background-color": "transparent",
                "border": "none",
            },
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "6px 0",
                "padding": "12px 16px",
                "border-radius": "10px",
                "color": "white",
            },
            "nav-link-selected": {
                "background-color": "#e7000b",
                "color": "white",
                "font-weight": "600",
            },
            "icon": {
                "color": "white",
                "font-size": "16px"
            },
            "icon-selected": {
                "color": "white"
            }
        }
    )

if selected_menu == "Ringkasan Berita":
    ringkasan.render(kamus=kamus_dict)

elif selected_menu == "Kamus Padanan":
    kamus.render(kamus_list=kamus_list)

elif selected_menu == "Tentang Pembuat":
    tentang.render()