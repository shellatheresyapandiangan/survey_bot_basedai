import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import requests
import re
import io
import time

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Analisis Data Survei Shampo",
    page_icon="📊",
    layout="wide"
)

# --- Fungsi untuk membuat WordCloud ---
def create_wordcloud(text, title):
    """
    Membuat dan menampilkan WordCloud dari teks yang diberikan.
    """
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color="white", 
        max_words=50,
        regexp=r"\w+"
    ).generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.subheader(title)
    st.pyplot(fig)

# --- Judul Aplikasi ---
st.title("Analisis Data Survei Shampo")
st.markdown("Aplikasi ini menganalisis data survei yang diambil langsung dari Google Sheets.")
st.markdown("---")

# --- Memuat Data dari Google Sheets ---
# Ganti 'SHEET_ID' dengan ID dari URL Google Sheets Anda
# Ganti 'SHEET_NAME' jika nama sheet Anda berbeda
SHEET_ID = "1Mp7KYO4w6GRUqvuTr4IRNeB7iy8SIZjSrLZmbEAm4GM"
SHEET_NAME = "Sheet1"
google_sheets_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# Mengubah nama kolom agar sesuai dengan data Google Sheets
EXPECTED_COLUMNS = {
    "Apa merek shampo yang Anda ketahui": "merek_diketahui",
    "Apa merek shampo yang Anda gunakan": "merek_digunakan",
    "Bagaimana persepsi anda terkait shampo tresemme": "persepsi_tresemme",
    "Apa yang tidak anda sukai dari shampo clear": "tidak_suka_clear",
    "Shampo seperti apa yang anda favoritkan? Dari bungkus, wangi, dll? Dan jelaskan alasannya?": "favorit_shampo"
}

try:
    with st.spinner("Mengambil data dari Google Sheets..."):
        df = pd.read_csv(google_sheets_url)
    
    # Normalisasi nama kolom untuk menghindari kesalahan spasi atau karakter tak terlihat
    df.columns = [col.strip() for col in df.columns]
    
    # Mencari nama kolom yang cocok dari EXPECTED_COLUMNS
    column_mapping = {}
    for sheet_col in df.columns:
        for expected_col, internal_name in EXPECTED_COLUMNS.items():
            if expected_col.strip().lower() in sheet_col.lower():
                column_mapping[sheet_col] = internal_name
    
    # Mengubah nama kolom agar mudah diakses
    df = df.rename(columns=column_mapping)

    # Memeriksa apakah semua kolom yang diharapkan berhasil dipetakan
    mapped_columns = set(column_mapping.values())
    if not all(col in mapped_columns for col in EXPECTED_COLUMNS.values()):
        st.error("Terjadi kesalahan saat memproses data: Tidak semua kolom survei ditemukan. Mohon periksa kembali nama kolom di Google Sheets Anda.")
        st.stop()
        
    # --- Analisis Dimulai ---
    st.markdown("---")
    st.header("Hasil Analisis")

    # 1. WordCloud dan Top 10 Merek
    st.markdown("### 1. Merek Shampo yang Diketahui & Digunakan")
    
    all_brands = (
        ", ".join(df["merek_diketahui"].dropna().astype(str)) + ", " +
        ", ".join(df["merek_digunakan"].dropna().astype(str))
    ).lower()
    all_brands_list = [brand.strip() for brand in re.split(r'[,;]+', all_brands) if brand.strip()]
    
    if all_brands_list:
        create_wordcloud(" ".join(all_brands_list), "WordCloud Merek Shampo Terkenal")
        brand_counts = Counter(all_brands_list)
        top_10_brands = brand_counts.most_common(10)
        st.subheader("Top 10 Merek Shampo")
        top_10_df = pd.DataFrame(top_10_brands, columns=["Merek", "Frekuensi"])
        st.dataframe(top_10_df)
    else:
        st.info("Tidak ada data merek untuk dianalisis.")

    st.markdown("---")

    # 2. Persepsi Terkait Shampo TRESemmé
    st.markdown("### 2. Persepsi Terkait Shampo TRESemmé")
    st.info("Analisis sentimen tidak dapat dilakukan karena token API untuk AI tidak valid.")
    
    st.markdown("---")

    # 3. Alasan Tidak Suka CLEAR
    st.markdown("### 3. Alasan Tidak Suka Shampo CLEAR")
    if "tidak_suka_clear" in df.columns and not df["tidak_suka_clear"].isnull().all():
        text_dislikes = " ".join(df["tidak_suka_clear"].dropna().astype(str))
        create_wordcloud(text_dislikes, "WordCloud Alasan Tidak Suka Shampo CLEAR")
    else:
        st.info("Tidak ada data untuk analisis alasan tidak suka CLEAR.")
    
    st.markdown("---")

    # 4. Prioritas Saat Memilih Shampo
    st.markdown("### 4. Prioritas dalam Memilih Shampo")
    if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
        # Memetakan kata kunci dengan prioritas
        keywords = ["bungkus", "wangi", "kemasan", "aroma", "tekstur", "harga"]
        priority_counts = {keyword: 0 for keyword in keywords}
        
        for alasan in df["favorit_shampo"].dropna().astype(str):
            alasan_lower = alasan.lower()
            for keyword in keywords:
                if keyword in alasan_lower:
                    priority_counts[keyword] += 1
        
        priorities_df = pd.DataFrame(list(priority_counts.items()), columns=["Prioritas", "Frekuensi"])
        st.bar_chart(priorities_df, x="Prioritas", y="Frekuensi")
    else:
        st.info("Tidak ada data untuk analisis prioritas.")

    st.markdown("---")

    # 5. Ringkasan Alasan Favorit Shampo (WordCloud)
    st.markdown("### 5. Ringkasan Alasan Favorit Shampo (WordCloud)")
    if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
        all_reasons = " ".join(df["favorit_shampo"].dropna().astype(str))
        create_wordcloud(all_reasons, "WordCloud Alasan Favorit Shampo")
    else:
        st.info("Tidak ada data untuk ringkasan alasan favorit.")

except requests.exceptions.HTTPError as e:
    st.error(f"Gagal memuat data dari Google Sheets. Mohon pastikan link publik dan nama sheet sudah benar. Kesalahan: {e}")
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data: {e}. Mohon periksa kembali struktur kolom di Google Sheets Anda.")
