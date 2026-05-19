import streamlit as st

def render():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">ℹ️</div>
        <div>
            <h1>Panduan Penggunaan</h1>
            <p>Cara menggunakan aplikasi Financial News Summarizer</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Meringkas Berita Finansial", expanded=True):

        st.markdown("""
        1. Buka halaman **Ringkasan Berita** pada sidebar.

        2. Masukkan URL berita atau tempel teks berita.

        3. Tekan tombol **Buat Ringkasan**.

        4. Sistem akan memproses berita dan menampilkan hasil ringkasan.

        5. Ringkasan otomatis tersimpan jika sudah login.
        """)

    with st.expander("Menggunakan Kamus Padanan"):

        st.markdown("""
        1. Buka halaman **Kamus Padanan**.

        2. Masukkan istilah finansial pada kolom pencarian.

        3. Gunakan filter huruf A-Z.

        4. Sistem akan menampilkan padanan kata dan deskripsinya.
        """)

    with st.expander("Riwayat Ringkasan"):

        st.markdown("""
        1. Login atau register terlebih dahulu.

        2. Buka halaman **Riwayat Ringkasan**.

        3. Semua ringkasan yang pernah dibuat akan tampil.
        """)

    with st.expander("Login dan Registrasi"):

        st.markdown("""
        1. Untuk login atau membuat akun baru, buka halaman
        **Riwayat Ringkasan** atau scroll ke bagian bawah
        halaman **Kamus Padanan**.

        2. Pada bagian login dan registrasi,
        akan muncul form autentikasi jika pengguna
        belum login.

        3. Gunakan tab **Login** untuk masuk menggunakan
        username dan password.

        4. Jika belum memiliki akun, pilih tab
        **Daftar Akun** lalu lakukan registrasi akun baru.

        5. Setelah berhasil login, sesi akan tersimpan
        otomatis meskipun halaman di-refresh.

        6. Gunakan tombol **Logout** pada sidebar
        untuk keluar dari akun.
        """)

    with st.expander("Menambahkan Entri Kamus"):

        st.markdown("""
        1. Login terlebih dahulu menggunakan akun Anda.

        2. Buka halaman **Kamus Padanan** pada sidebar.

        3. Scroll ke bagian paling bawah halaman.

        4. Isi formulir penambahan entri:
        - **Istilah Finansial**
        - **Padanan Kata**
        - **Deskripsi**

        5. Tekan tombol **Simpan ke kamus** untuk menyimpan data.

        6. Entri yang berhasil ditambahkan akan langsung muncul pada daftar kamus.
        """)