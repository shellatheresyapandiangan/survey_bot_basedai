import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import json
import requests
import re
import io

# Token API dari user (digunakan untuk panggilan AI)
API_KEY = "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"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Analisis Data Survei Shampo",
    page_icon="📊",
    layout="wide"
)

# --- Fungsi untuk memanggil model AI ---
def call_llm(prompt, api_key):
    """
    Memanggil Gemini API untuk mendapatkan ringkasan atau analisis.
    """
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(f"{API_URL}?key={api_key}", headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Angkat pengecualian untuk status kode error (4xx atau 5xx)
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Kesalahan HTTP: {http_err} - Pastikan token API valid.")
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
        regexp=r"\w+" # Memastikan hanya kata-kata yang dihitung
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
st.title("Analisis Hasil Survei Shampo")
st.markdown("Aplikasi ini menganalisis data survei yang diambil langsung dari repositori GitHub.")
st.markdown("---")

# --- Memuat Data dari GitHub ---
st.subheader("Muat Data Survei dari GitHub")
github_csv_url = st.text_input(
    "Masukkan URL file CSV mentah dari GitHub:",
    value="https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/main/shampo_survey_responses.csv"
)

if st.button("Mulai Analisis"):
    if "YOUR_GITHUB_USERNAME" in github_csv_url:
        st.warning("Mohon masukkan URL file CSV GitHub yang valid.")
    else:
        try:
            st.info("Mengambil data dari GitHub...")
            response = requests.get(github_csv_url)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
            st.success("File berhasil dimuat!")
            st.dataframe(df)

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

            st.markdown("---")

            # 2. Analisis Persepsi TRESemmé
            st.markdown("### 2. Persepsi Terkait Shampo TRESemmé")
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
            keywords = ["bungkus", "wangi", "kemasan", "aroma", "tekstur", "harga"]
            priority_counts = {keyword: 0 for keyword in keywords}
            if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
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

            # 5. Ringkasan Alasan Favorit Shampo dengan LLM
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
            st.error(f"Gagal memuat file dari GitHub. Mohon periksa URL dan pastikan file ada. Kesalahan: {e}")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")
