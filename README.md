# IndoT5 Financial News Summarizer

Aplikasi web untuk meringkas berita keuangan berbahasa Indonesia secara otomatis menggunakan model **IndoT5-small** yang telah di-*fine-tune* khusus untuk tugas *abstractive summarization* pada domain berita finansial.

## Tentang Aplikasi

Aplikasi ini dibangun sebagai bagian dari skripsi yang membahas peringkasan teks otomatis (*automatic text summarization*) untuk berita keuangan berbahasa Indonesia. Model dasar `wikidepia/indot5-small` di-*fine-tune* menggunakan dataset berita finansial, lalu dievaluasi dengan metrik ROUGE dan BLEU untuk membandingkan performa model dasar dengan model hasil *fine-tuning*.

## Fitur

- **Ringkasan otomatis dari berita terkini** — aplikasi mengambil (*scraping*) berita terbaru dari tiga sumber tepercaya: CNBC Indonesia, Detik Finance, dan IDX Channel, lalu meringkasnya secara otomatis.
- **Ringkasan dari input teks/URL manual** — pengguna juga dapat memasukkan teks berita atau tautan berita sendiri untuk diringkas.
- **Highlight padanan kata** — kata-kata pada hasil ringkasan yang merupakan padanan/sinonim dari teks asli ditandai agar pengguna dapat menelusuri relevansi ringkasan dengan mudah.
- **Tombol salin (copy)** — hasil ringkasan dapat disalin dengan satu klik.
- **Autentikasi pengguna** — sistem login/register berbasis database (Supabase) sehingga setiap pengguna memiliki akun masing-masing.
- **Riwayat ringkasan** — setiap ringkasan yang dibuat pengguna tersimpan dalam riwayat dan dapat diakses kembali kapan saja.
- **Dashboard interaktif** — antarmuka Streamlit yang menampilkan berita terkini beserta ringkasannya dalam tampilan yang rapi dan mudah dinavigasi.

## Cara Menjalankan Aplikasi secara Lokal

1. **Clone repository**
   ```bash
   git clone <url-repository-ini>
   cd <nama-folder-repository>
   ```

2. **Buat virtual environment (opsional tapi disarankan)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Siapkan environment variables**
   Buat file `.env` atau atur *secrets* Streamlit (`.streamlit/secrets.toml`) berisi kredensial yang dibutuhkan, misalnya URL dan API key Supabase:
   ```toml
   SUPABASE_URL = "isi-url-supabase-anda"
   SUPABASE_KEY = "isi-key-supabase-anda"
   ```

5. **Jalankan aplikasi**
   ```bash
   streamlit run src/streamlit_app.py
   ```

6. Aplikasi akan terbuka otomatis di browser pada alamat `http://localhost:8501`.

> **Catatan:** Aplikasi juga dapat dijalankan menggunakan Docker, mengikuti konfigurasi `app_port: 8501` di atas:
> ```bash
> docker build -t indot5-fin-summarizer .
> docker run -p 8501:8501 indot5-fin-summarizer
> ```

## Menggunakan Aplikasi yang Sudah Di-deploy

Aplikasi ini juga sudah tersedia secara online dan dapat langsung diakses tanpa perlu instalasi apa pun melalui tautan berikut:

🔗 **[indot5-financial-news-summarizer.streamlit.app](https://indot5-financial-news-summarizer.streamlit.app/)**

Cukup buka tautan di atas, login/register jika diperlukan, lalu mulai gunakan fitur peringkasan berita secara langsung di browser.