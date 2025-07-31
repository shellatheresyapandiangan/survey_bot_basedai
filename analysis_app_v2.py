import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import json
import requests
import re
import io
import time

# Token API dari user (digunakan untuk panggilan AI)
#
# PENTING: Anda harus mengganti nilai ini dengan token Groq API yang valid dari akun Anda.
# Token ini adalah token Groq.
API_KEY = "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"
# URL API Groq yang kompatibel dengan format OpenAI
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Analisis Data Surveai Shampo",
    page_icon="�",
    layout="wide"
)

# --- Fungsi untuk memanggil model AI (Groq API) ---
def call_llm(prompt, api_key):
    """
    Memanggil Groq API untuk mendapatkan ringkasan atau analisis.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gemma-7b-it", # Menggunakan model yang tersedia di Groq
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Kesalahan HTTP: {http_err} - Pastikan token API valid dan memiliki akses ke Groq API.")
    except (requests.exceptions.RequestException, KeyError, IndexError) as err:
        st.error(f"Terjadi kesalahan saat memproses respons API: {err}")
    return "Respons tidak dapat diproses."

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

# --- Fungsi untuk menganalisis sentimen ---
def analyze_sentiment(text, api_key):
    """
    Menggunakan LLM untuk mengkategorikan sentimen.
    """
    prompt = f"""
    Klasifikasikan sentimen dari teks berikut:
    "{text}"
    
    Pilih salah satu dari kategori berikut: 'Baik', 'Buruk', atau 'Netral'.
    Berikan hanya satu kata dari kategori tersebut sebagai jawaban.
    """
    response = call_llm(prompt, api_key)
    
    if response:
        sentiment = response.strip().upper()
        if "BAIK" in sentiment:
            return "Baik"
        elif "BURUK" in sentiment:
            return "Buruk"
        elif "NETRAL" in sentiment:
            return "Netral"
    return "Netral"

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

    # 2. Analisis Persepsi TRESemmé
    st.markdown("### 2. Persepsi Terkait Shampo TRESemmé (AI-Powered)")
    if "persepsi_tresemme" in df.columns and not df["persepsi_tresemme"].isnull().all():
        with st.spinner("Menganalisis sentimen..."):
            df["sentimen_tresemme"] = df["persepsi_tresemme"].apply(lambda x: analyze_sentiment(str(x), API_KEY) if pd.notna(x) else "Netral")
        sentiment_counts = df["sentimen_tresemme"].value_counts()
        st.bar_chart(sentiment_counts)
        st.dataframe(sentiment_counts)
    else:
        st.info("Tidak ada data untuk analisis persepsi TRESemmé.")

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

    # 5. Ringkasan Alasan Favorit Shampo (AI-Powered)
    st.markdown("### 5. Ringkasan Alasan Favorit Shampo (AI-Powered)")
    if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
        all_reasons = " ".join(df["favorit_shampo"].dropna().astype(str))
        with st.spinner("Meringkas alasan-alasan favorit dengan AI..."):
            prompt_summary = f"""
            Berikut adalah kumpulan alasan orang memilih shampo favorit mereka:
            "{all_reasons}"
            
            Buatlah ringkasan singkat dalam bahasa Indonesia mengenai alasan-alasan utama yang sering disebutkan.
            """
            summary_text = call_llm(prompt_summary, API_KEY)
            if summary_text:
                st.info(summary_text)
    else:
        st.info("Tidak ada data untuk ringkasan alasan favorit.")

except requests.exceptions.HTTPError as e:
    st.error(f"Gagal memuat data dari Google Sheets. Mohon pastikan link publik dan nama sheet sudah benar. Kesalahan: {e}")
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data: {e}. Mohon periksa kembali struktur kolom di Google Sheets Anda.")
�
