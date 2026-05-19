import streamlit as st
import base64
import os

def _img_to_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(path)[1].lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{data}"
    except FileNotFoundError:
        return ""

def render():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    img_jason = _img_to_base64(os.path.join(BASE_DIR, "assets", "image", "jasonsutanto.jpg"))
    img_bagus = _img_to_base64(os.path.join(BASE_DIR, "assets", "image", "bagusmulyawan.jpg"))

    jason_avatar = (
        f'<img src="{img_jason}" class="profile-img"/>'
        if img_jason else
        '<div class="profile-avatar red">🎓</div>'
    )
    bagus_avatar = (
        f'<img src="{img_bagus}" class="profile-img"/>'
        if img_bagus else
        '<div class="profile-avatar dark">👨‍🏫</div>'
    )

    st.markdown("""
        <div class="page-header">
            <div class="page-header-icon">👨‍💻</div>
            <div>
                <h1>Tentang</h1>
                <p>Informasi mengenai pengembangan aplikasi Financial News Summarizer</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="latar-card">
        <div class="latar-header">
            <div class="latar-icon-wrap">👤</div>
            <div class="latar-title">Latar Belakang Pembuatan Aplikasi</div>
        </div>
        <div class="latar-text">
            Aplikasi ini dikembangkan sebagai salah satu kontribusi dalam membantu pembaca memahami informasi keuangan yang sering kali kompleks dan penuh istilah teknis. Banyak berita finansial sulit dipahami oleh pembaca karena penggunaan bahasa yang formal dan struktur kalimat yang panjang. Oleh karena itu, aplikasi ini memanfaatkan teknologi Natural Language Processing (NLP) berbasis model Transformer, yaitu IndoT5, untuk menghasilkan ringkasan teks secara otomatis sekaligus mengganti istilah finansial menjadi padanan yang lebih mudah dipahami. Dengan adanya aplikasi ini, diharapkan pengguna dapat memperoleh informasi yang lebih ringkas, jelas, dan tetap mempertahankan makna utama dari berita yang dibaca.
        </div>
    </div>

    <div style="margin-top: 2rem;"></div>

    <div class="pembuat-container">
        <div class="pembuat-header">
            <div class="pembuat-icon-wrap">👥</div>
            <span class="pembuat-title">Pembuat</span>
        </div>
        <div class="pembuat-grid">
            <div class="profile-card">
                <div class="profile-avatar-wrap">
                    {jason_avatar}
                </div>
                <div class="profile-name">Jason Sutanto</div>
                <div class="profile-nim">NIM: 535220052</div>
                <div class="profile-prodi">Teknik Informatika</div>
                <div class="profile-batch">Angkatan 2022</div>
                <hr class="profile-divider"/>
                <div class="profile-role">Mahasiswa Universitas Tarumanagara</div>
            </div>
            <div class="profile-card">
                <div class="profile-avatar-wrap">
                    {bagus_avatar}
                </div>
                <div class="profile-name">Dr. Bagus Mulyawan</div>
                <div class="profile-nim">S.Kom., M.M.</div>
                <div class="profile-prodi">&nbsp;</div>
                <div class="profile-batch">&nbsp;</div>
                <hr class="profile-divider"/>
                <div class="profile-role">Dosen Pembimbing</div>
            </div>
        </div>
    </div>
    """.replace("{jason_avatar}", jason_avatar).replace("{bagus_avatar}", bagus_avatar), unsafe_allow_html=True)