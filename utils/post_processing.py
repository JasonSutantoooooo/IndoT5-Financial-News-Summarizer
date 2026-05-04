import re
import pandas as pd

IMBUHAN_SUFFIX = ["nya", "kan", "lah"]

def load_kamus(file_path, kolom_istilah="istilah", kolom_padanan="padanan"):
    try:
        df_kamus = pd.read_excel(file_path)
        df_kamus = df_kamus.dropna(subset=[kolom_istilah, kolom_padanan])
        kamus = dict(zip(
            df_kamus[kolom_istilah].str.strip().str.lower(),
            df_kamus[kolom_padanan].str.strip()
        ))
        print(f"Kamus dimuat: {len(kamus)} istilah")
        return kamus
    except FileNotFoundError:
        print(f"File kamus tidak ditemukan: {file_path}")
        return {}
    except Exception as e:
        print(f"Error memuat kamus: {e}")
        return {}


def ganti_istilah_dengan_imbuhan(teks, kamus):
    hasil = teks

    # Urutkan dari istilah terpanjang dulu untuk hindari partial match
    kamus_terurut = sorted(kamus.items(), key=lambda x: len(x[0]), reverse=True)

    for istilah, padanan in kamus_terurut:
        hasil = re.sub(
            rf'\b{re.escape(istilah)}\b',
            padanan,
            hasil,
            flags=re.IGNORECASE
        )

        for suffix in IMBUHAN_SUFFIX:
            hasil = re.sub(
                rf'\b{re.escape(istilah)}{suffix}\b',
                padanan + suffix,
                hasil,
                flags=re.IGNORECASE
            )

    return hasil


def load_kamus_for_display(file_path, kolom_istilah="istilah", kolom_padanan="padanan", kolom_deskripsi="deskripsi"):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=[kolom_istilah, kolom_padanan])
        df[kolom_istilah] = df[kolom_istilah].str.strip().str.title()
        df[kolom_padanan] = df[kolom_padanan].str.strip().str.capitalize()

        has_deskripsi = kolom_deskripsi in df.columns

        result = []
        for _, row in df.iterrows():
            entry = {
                "istilah": row[kolom_istilah],
                "padanan": row[kolom_padanan],
                "deskripsi": row[kolom_deskripsi].strip().capitalize() if has_deskripsi and pd.notna(row.get(kolom_deskripsi)) else ""
            }
            result.append(entry)

        result.sort(key=lambda x: x["istilah"].lower())
        print(f"Kamus display dimuat: {len(result)} istilah")
        return result
    except FileNotFoundError:
        print(f"File kamus tidak ditemukan: {file_path}")
        return []
    except Exception as e:
        print(f"Error memuat kamus display: {e}")
        return []
    
def trim_incomplete_sentence(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    if not sentences:
        return text
    
    last = sentences[-1].strip()
    
    if not re.search(r'[.!?]$', last):
        sentences = sentences[:-1]
    
    return ' '.join(sentences).strip()