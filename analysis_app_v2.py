# ==============================================================================
# Aplikasi Analisis Data Survei Shampo
# Menggunakan LangChain & Groq API
# ==============================================================================

# --- 1. Impor Library ---
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import requests
import re
import io
import time
import json
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

# --- 2. Konfigurasi Halaman & Desain (CSS) ---
st.set_page_config(
    page_title="Analisis Data Survei Shampo",
    page_icon="�",
    layout="wide"
)

# CSS Kustom untuk tampilan yang lebih profesional
st.markdown("""
<style>
.stApp {
    background-color: #f0f2f6;
    color: #333333;
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
.stExpander {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    background-color: #ffffff;
    transition: box-shadow 0.3s ease-in-out;
}
.stExpander:hover {
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}
.stButton>button {
    background-color: #4CAF50;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px 20px;
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    transition: background-color 0.3s ease, transform 0.3s ease;
}
.stButton>button:hover {
    background-color: #45a049;
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

# Token API Groq yang Anda berikan
GROQ_API_KEY = "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"

# --- 3. Fungsi Inti ---
@st.cache_resource
def get_llm():
    try:
        return ChatGroq(temperature=0, model_name="llama3-8b-8192", groq_api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Gagal memuat model AI. Pastikan GROQ_API_KEY Anda sudah benar. Error: {e}")
        return None

def generate_summary(text_content):
    llm = get_llm()
    if not llm or not text_content: return "Gagal membuat ringkasan."
    
    prompt = PromptTemplate.from_template(
        "Anda adalah analis riset AI. Buat ringkasan komprehensif dari teks berikut dalam format poin-poin (bullet points) dalam Bahasa Indonesia. Fokus pada ide utama dan poin-poin kunci.\n\nTeks:\n---\n{{text}}\n---"
    )
    chain = prompt | llm
    summary = chain.invoke({"text": text_content[:12000]}).content
    return summary

def analyze_sentiment(text):
    llm = get_llm()
    if not llm: return "Model AI tidak tersedia."

    prompt = PromptTemplate.from_template(
        "Klasifikasikan sentimen dari teks berikut: '{text}'. Pilih salah satu dari kategori berikut: 'Baik', 'Buruk', atau 'Netral'. Berikan hanya satu kata dari kategori tersebut sebagai jawaban."
    )
    chain = prompt | llm
    response = chain.invoke({"text": text}).content

    if response:
        sentiment = response.strip().upper()
        if "BAIK" in sentiment:
            return "Baik"
        elif "BURUK" in sentiment:
            return "Buruk"
        elif "NETRAL" in sentiment:
            return "Netral"
    return "Netral"

# --- Fungsi-fungsi Visualisasi ---
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

    # Bagian 2: Persepsi Terkait Shampo TRESemmé (AI-Powered)
    with st.expander("2. Persepsi Terkait Shampo TRESemmé (AI-Powered)"):
        if "persepsi_tresemme" in df.columns and not df["persepsi_tresemme"].isnull().all():
            with st.spinner("Menganalisis sentimen..."):
                df["sentimen_tresemme"] = df["persepsi_tresemme"].apply(lambda x: analyze_sentiment(str(x)) if pd.notna(x) else "Netral")
            sentiment_counts = df["sentimen_tresemme"].value_counts()
            
            fig, ax = plt.subplots()
            sentiment_counts.plot(kind='bar', color=['#4CAF50', '#f44336', '#9e9e9e'])
            ax.set_title("Analisis Sentimen TRESemmé")
            ax.set_ylabel("Jumlah Responden")
            ax.tick_params(axis='x', rotation=0)
            st.pyplot(fig)
            
            st.dataframe(sentiment_counts)
        else:
            st.info("Tidak ada data untuk analisis persepsi TRESemmé.")
    
    # Bagian 3: Alasan Tidak Suka CLEAR
    with st.expander("3. Alasan Tidak Suka Shampo CLEAR"):
        if "tidak_suka_clear" in df.columns and not df["tidak_suka_clear"].isnull().all():
            text_dislikes = " ".join(df["tidak_suka_clear"].dropna().astype(str))
            create_wordcloud(text_dislikes, "WordCloud Alasan Tidak Suka Shampo CLEAR")
        else:
            st.info("Tidak ada data untuk analisis alasan tidak suka CLEAR.")
    
    # Bagian 4: Prioritas dalam Memilih Shampo
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

    # Bagian 5: Ringkasan Alasan Favorit Shampo (AI-Powered)
    with st.expander("5. Ringkasan Alasan Favorit Shampo (AI-Powered)"):
        if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
            all_reasons = " ".join(df["favorit_shampo"].dropna().astype(str))
            with st.spinner("Meringkas alasan-alasan favorit dengan AI..."):
                summary_text = generate_summary(all_reasons)
                if summary_text:
                    st.info(summary_text)
        else:
            st.info("Tidak ada data untuk ringkasan alasan favorit.")
            
    # Bagian 6: Tanya AI tentang Data Survei (Fitur GPT)
    with st.expander("6. Tanya AI tentang Data Survei"):
        st.markdown("Masukkan pertanyaan spesifik Anda terkait data survei ini.")
        user_question = st.text_area("Pertanyaan Anda:")
        if st.button("Tanyakan ke AI"):
            if user_question:
                with st.spinner("AI sedang memproses pertanyaan Anda..."):
                    llm = get_llm()
                    if llm:
                        if user_question.strip().lower() in ["hi", "halo", "hai"]:
                            ai_answer = "Hi, ada yang bisa saya bantu? Anda bisa bertanya tentang analisis data survei shampo ini."
                        else:
                            data_text = df.to_string()
                            prompt_qa = f"""
                            Anda adalah seorang analis pasar yang ahli. Berdasarkan data survei shampo berikut:
                            
                            {data_text}
                            
                            Jawab pertanyaan berikut dari sudut pandang analisis pasar, potensi market, dan persepsi konsumen.
                            
                            Pertanyaan: "{user_question}"
                            
                            Berikan jawaban yang ringkas dan informatif dalam Bahasa Indonesia.
                            
                            ---
                            
                            Contoh Jawaban:
                            Berdasarkan data, TRESemmé memiliki persepsi yang bervariasi. Responden menganggapnya "Mahal, ngak bagus, kasar" namun di sisi lain ada yang "oke". Ini mengindikasikan adanya segmen pasar yang berbeda. Untuk TRESemmé, strategi pemasaran bisa difokuskan pada peningkatan kualitas produk atau menargetkan segmen yang lebih sensitif terhadap harga.
                            
                            ---
                            
                            Jawaban Anda:
                            """
                            chain = PromptTemplate.from_template(prompt_qa) | llm
                            ai_answer = chain.invoke({"context": data_text, "question": user_question}).content
                        
                        if ai_answer:
                            st.info(ai_answer)
                    else:
                        st.error("Gagal memuat model AI.")
            else:
                st.warning("Mohon masukkan pertanyaan terlebih dahulu.")

except requests.exceptions.HTTPError as e:
    st.error(f"Gagal memuat data dari Google Sheets. Mohon pastikan link publik dan nama sheet sudah benar. Kesalahan: {e}")
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data: {e}. Mohon periksa kembali struktur kolom di Google Sheets Anda.")
