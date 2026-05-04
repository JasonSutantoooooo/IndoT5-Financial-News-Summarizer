import streamlit as st

st.set_page_config(layout="wide")

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

    all_letters = sorted(set(
        e["istilah"][0].upper() for e in kamus_list if e["istilah"]
    ))
    huruf_options = ["Semua"] + all_letters

    container = st.container(border=True)

    with container:
        st.markdown("**Filter berdasarkan huruf:**")

        cols = st.columns(10)

        for i, huruf in enumerate(huruf_options):
            col = cols[i % 10]

            with col:
                if st.button(huruf, key=f"btn_{huruf}", use_container_width=True):
                    st.session_state.sel_letter = huruf
                    st.query_params["kamus_letter"] = huruf
                    st.rerun()

    filtered = kamus_list

    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            e for e in filtered
            if q in e["istilah"].lower() or q in e["padanan"].lower()
        ]
    elif st.session_state.sel_letter != "Semua":
        filtered = [
            e for e in filtered
            if e["istilah"].upper().startswith(st.session_state.sel_letter)
        ]

    if not filtered:
        st.info("Tidak ada istilah yang ditemukan.")
    else:
        for entry in filtered:
            istilah = entry.get("istilah", "")
            padanan = entry.get("padanan", "")
            deskripsi = entry.get("deskripsi", "")
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