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
    page_icon="�",
    layout="wide"
)

# Menambahkan CSS kustom untuk tampilan yang lebih profesional
st.markdown("""
<style>
.stApp {
    background-color: #f0f2f6;
}
.header-title {
    font-size: 2.5em;
    font-weight: 700;
    color: #0d47a1;
}
.header-subtitle {
    font-size: 1.1em;
    color: #4a4a4a;
    font-weight: 300;
}
.card-header {
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 10px;
    font-weight: bold;
    color: #1a237e;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.stExpander {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    background-color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

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

# --- Header Aplikasi ---
st.markdown("<div class='header-title'>Analisis Data Survei Shampo</div>", unsafe_allow_html=True)
st.markdown("<div class='header-subtitle'>Menganalisis data survei preferensi shampo dari Google Sheets.</div>", unsafe_allow_html=True)
st.markdown("---")

# --- Memuat Data dari Google Sheets ---
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
    
    df.columns = [col.strip() for col in df.columns]
    
    column_mapping = {}
    for sheet_col in df.columns:
        for expected_col, internal_name in EXPECTED_COLUMNS.items():
            if expected_col.strip().lower() in sheet_col.lower():
                column_mapping[sheet_col] = internal_name
    
    df = df.rename(columns=column_mapping)

    mapped_columns = set(column_mapping.values())
    if not all(col in mapped_columns for col in EXPECTED_COLUMNS.values()):
        st.error("Terjadi kesalahan saat memproses data: Tidak semua kolom survei ditemukan. Mohon periksa kembali nama kolom di Google Sheets Anda.")
        st.stop()
        
    # --- Analisis Dimulai ---
    st.markdown("---")
    
    # Bagian 1: WordCloud dan Top 10 Merek
    with st.expander("1. Merek Shampo yang Diketahui & Digunakan"):
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

    # Bagian 2: Persepsi Terkait Shampo TRESemmé
    with st.expander("2. Persepsi Terkait Shampo TRESemmé"):
        st.info("Analisis sentimen tidak dapat dilakukan karena token API untuk AI tidak valid.")
    
    # Bagian 3: Alasan Tidak Suka CLEAR
    with st.expander("3. Alasan Tidak Suka Shampo CLEAR"):
        if "tidak_suka_clear" in df.columns and not df["tidak_suka_clear"].isnull().all():
            text_dislikes = " ".join(df["tidak_suka_clear"].dropna().astype(str))
            create_wordcloud(text_dislikes, "WordCloud Alasan Tidak Suka Shampo CLEAR")
        else:
            st.info("Tidak ada data untuk analisis alasan tidak suka CLEAR.")
    
    # Bagian 4: Prioritas Saat Memilih Shampo
    with st.expander("4. Prioritas dalam Memilih Shampo"):
        if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
            keywords = ["bungkus", "wangi", "kemasan", "aroma", "tekstur", "harga"]
            priority_counts = {keyword: 0 for keyword in keywords}
            
            for alasan in df["favorit_shampo"].dropna().astype(str):
                alasan_lower = alasan.lower()
                for keyword in keywords:
                    if keyword in alasan_lower:
                        priority_counts[keyword] += 1
            
            priorities_df = pd.DataFrame(list(priority_counts.items()), columns=["Prioritas", "Frekuensi"])
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(priorities_df["Prioritas"], priorities_df["Frekuensi"], color='#64b5f6')
            ax.set_title("Prioritas dalam Memilih Shampo", fontsize=16)
            ax.set_ylabel("Frekuensi", fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            st.pyplot(fig)
        else:
            st.info("Tidak ada data untuk analisis prioritas.")

    # Bagian 5: Ringkasan Alasan Favorit Shampo
    with st.expander("5. Ringkasan Alasan Favorit Shampo"):
        if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
            all_reasons = " ".join(df["favorit_shampo"].dropna().astype(str))
            create_wordcloud(all_reasons, "WordCloud Alasan Favorit Shampo")
        else:
            st.info("Tidak ada data untuk ringkasan alasan favorit.")

except requests.exceptions.HTTPError as e:
    st.error(f"Gagal memuat data dari Google Sheets. Mohon pastikan link publik dan nama sheet sudah benar. Kesalahan: {e}")
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data: {e}. Mohon periksa kembali struktur kolom di Google Sheets Anda.")
