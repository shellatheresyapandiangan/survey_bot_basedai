# ==============================================================================
# Aplikasi Analisis Data Survei Shampo
# Menggunakan LangChain & Groq API
# Versi: Diperbaiki dan Disempurnakan
# ==============================================================================

# --- 1. Impor Library ---
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import re
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

# --- 2. Konfigurasi Halaman & Desain (CSS) ---
st.set_page_config(
    page_title="Analisis Data Survei Shampo",
    page_icon="📊",
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
/* Gaya untuk chat messages */
.st-chat-message-user {
    background-color: #e3f2fd;
    border-radius: 12px;
    padding: 10px;
}
.st-chat-message-assistant {
    background-color: #f5f5f5;
    border-radius: 12px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- 3. Konfigurasi Model AI (LLM) ---
# CATATAN: Menyimpan API key langsung di kode tidak disarankan untuk produksi.
# Sebaiknya gunakan st.secrets untuk keamanan.
GROQ_API_KEY = "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"

@st.cache_resource
def get_llm():
    """Memuat dan menyimpan instance model AI dalam cache."""
    try:
        return ChatGroq(temperature=0, model_name="llama3-8b-8192", groq_api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Gagal memuat model AI. Pastikan GROQ_API_KEY Anda sudah benar. Error: {e}")
        return None

# --- 4. Fungsi-fungsi Inti & Analisis ---

def generate_summary(text_content):
    """Membuat ringkasan dari teks menggunakan AI."""
    llm = get_llm()
    if not llm or not text_content:
        return "Gagal membuat ringkasan karena model AI tidak tersedia atau tidak ada teks."
    
    prompt = PromptTemplate.from_template(
        "Anda adalah analis riset AI. Buat ringkasan komprehensif dari teks berikut dalam format poin-poin (bullet points) dalam Bahasa Indonesia. Fokus pada ide utama dan poin-poin kunci.\n\nTeks:\n---\n{text}\n---"
    )
    chain = prompt | llm
    # Membatasi panjang teks untuk efisiensi API
    summary = chain.invoke({"text": text_content[:12000]}).content
    return summary

def analyze_sentiment(text):
    """Menganalisis sentimen teks menjadi 'Baik', 'Buruk', atau 'Netral'."""
    llm = get_llm()
    if not llm: return "Netral" # Fallback jika model gagal

    prompt = PromptTemplate.from_template(
        "Klasifikasikan sentimen dari teks berikut: '{text}'. Pilih salah satu dari kategori berikut: 'Baik', 'Buruk', atau 'Netral'. Berikan hanya satu kata dari kategori tersebut sebagai jawaban."
    )
    chain = prompt | llm
    try:
        response = chain.invoke({"text": text}).content
        sentiment = response.strip().upper()
        if "BAIK" in sentiment:
            return "Baik"
        elif "BURUK" in sentiment:
            return "Buruk"
        else:
            return "Netral"
    except Exception:
        return "Netral" # Fallback jika terjadi error pada API call

def create_wordcloud(text, title):
    """Membuat dan menampilkan WordCloud dari teks yang diberikan."""
    if not text or not text.strip():
        st.warning(f"Tidak ada data teks yang cukup untuk membuat '{title}'.")
        return

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        max_words=50,
        regexp=r"\w[\w']+" # Regex yang lebih baik untuk menangkap kata
    ).generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.subheader(title)
    st.pyplot(fig)

# --- 5. Memuat Data & Konfigurasi Kolom ---
SHEET_ID = "1Mp7KYO4w6GRUqvuTr4IRNeB7iy8SIZjSrLZmbEAm4GM"
SHEET_NAME = "Sheet1"
GOOGLE_SHEETS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# Pemetaan nama kolom dari Google Sheet ke nama internal yang lebih pendek
EXPECTED_COLUMNS = {
    "Apa merek shampo yang Anda ketahui": "merek_diketahui",
    "Apa merek shampo yang Anda gunakan": "merek_digunakan",
    "Bagaimana persepsi anda terkait shampo tresemme": "persepsi_tresemme",
    "Apa yang tidak anda sukai dari shampo clear": "tidak_suka_clear",
    "Shampo seperti apa yang anda favoritkan? Dari bungkus, wangi, dll? Dan jelaskan alasannya?": "favorit_shampo"
}

# --- 6. Inisialisasi Session State ---
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'df' not in st.session_state:
    st.session_state.df = None
if 'data_loaded_successfully' not in st.session_state:
    st.session_state.data_loaded_successfully = False

# --- 7. Logika Utama Aplikasi ---
col_chat, col_analysis = st.columns([1, 2], gap="large")

# === Kolom Analisis Data (Kanan) ===
with col_analysis:
    st.markdown("<div class='header-title'>Analisis Data Survei Shampo</div>", unsafe_allow_html=True)
    st.markdown("<div class='header-subtitle'>Menganalisis data survei preferensi shampo dari Google Sheets secara real-time.</div>", unsafe_allow_html=True)
    st.markdown("---")

    # Memuat data hanya sekali dan menyimpannya di session state
    if st.session_state.df is None:
        try:
            with st.spinner("Mengambil data dari Google Sheets..."):
                df_loaded = pd.read_csv(GOOGLE_SHEETS_URL)
                
                # Membersihkan nama kolom dari spasi ekstra
                df_loaded.columns = [col.strip() for col in df_loaded.columns]
                
                # Membuat pemetaan kolom secara dinamis dan fleksibel
                column_mapping = {}
                for sheet_col in df_loaded.columns:
                    for expected_col, internal_name in EXPECTED_COLUMNS.items():
                        if expected_col.strip().lower() in sheet_col.lower():
                            column_mapping[sheet_col] = internal_name
                
                df_loaded = df_loaded.rename(columns=column_mapping)
                st.session_state.df = df_loaded
                
                # Validasi apakah semua kolom yang diharapkan berhasil dipetakan
                mapped_columns = set(df_loaded.columns)
                if all(col in mapped_columns for col in EXPECTED_COLUMNS.values()):
                    st.session_state.data_loaded_successfully = True
                else:
                    missing_cols = [k for k, v in EXPECTED_COLUMNS.items() if v not in mapped_columns]
                    st.error(f"Gagal memetakan kolom berikut dari Google Sheets: {', '.join(missing_cols)}. Mohon periksa nama kolom di file sumber.")
                    st.stop()

        except Exception as e:
            st.error(f"Gagal memuat atau memproses data dari Google Sheets. Pastikan link bersifat publik dan nama sheet benar. Kesalahan: {e}")
            st.stop()
    
    df = st.session_state.df

    # Tampilkan analisis hanya jika data berhasil dimuat
    if st.session_state.data_loaded_successfully:
        with st.expander("1. Merek Shampo yang Paling Dikenal & Digunakan", expanded=True):
            all_brands_text = (
                ", ".join(df["merek_diketahui"].dropna().astype(str)) + ", " +
                ", ".join(df["merek_digunakan"].dropna().astype(str))
            ).lower()
            
            all_brands_list = [brand.strip() for brand in re.split(r'[,;]+', all_brands_text) if brand.strip()]
            
            if all_brands_list:
                create_wordcloud(" ".join(all_brands_list), "WordCloud Merek Shampo")
                
                brand_counts = Counter(all_brands_list)
                top_10_brands = brand_counts.most_common(10)
                
                st.subheader("Top 10 Merek Shampo Paling Populer")
                top_10_df = pd.DataFrame(top_10_brands, columns=["Merek", "Frekuensi"])
                st.dataframe(top_10_df, use_container_width=True)
            else:
                st.info("Tidak ada data merek untuk dianalisis.")

        with st.expander("2. Persepsi Terkait Shampo TRESemmé (AI-Powered)"):
            if "persepsi_tresemme" in df.columns and not df["persepsi_tresemme"].isnull().all():
                with st.spinner("Menganalisis sentimen TRESemmé..."):
                    df["sentimen_tresemme"] = df["persepsi_tresemme"].apply(lambda x: analyze_sentiment(str(x)) if pd.notna(x) else "Netral")
                
                sentiment_counts = df["sentimen_tresemme"].value_counts()
                
                fig, ax = plt.subplots()
                sentiment_counts.plot(kind='bar', ax=ax, color=['#4CAF50', '#f44336', '#9e9e9e'])
                ax.set_title("Distribusi Sentimen Terhadap TRESemmé")
                ax.set_ylabel("Jumlah Responden")
                ax.tick_params(axis='x', rotation=0)
                st.pyplot(fig)
                
                st.dataframe(sentiment_counts)
            else:
                st.info("Tidak ada data untuk analisis persepsi TRESemmé.")

        with st.expander("3. Poin Negatif Mengenai Shampo CLEAR"):
            if "tidak_suka_clear" in df.columns and not df["tidak_suka_clear"].isnull().all():
                text_dislikes = " ".join(df["tidak_suka_clear"].dropna().astype(str))
                create_wordcloud(text_dislikes, "WordCloud Alasan Tidak Suka Shampo CLEAR")
            else:
                st.info("Tidak ada data untuk analisis alasan tidak suka CLEAR.")

        with st.expander("4. Analisis Mendalam: Alasan Memilih Shampo Favorit"):
            if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
                alasan_list = df["favorit_shampo"].dropna().astype(str).tolist()
                all_reasons = " ".join(alasan_list)
                
                if len(all_reasons.split()) >= 5: # Butuh beberapa kata untuk analisis
                    with st.spinner("Membuat WordCloud dan menganalisis kata kunci..."):
                        # WordCloud
                        create_wordcloud(all_reasons, "WordCloud Faktor Penentu Shampo Favorit")

                        # Analisis Kata Kunci
                        keywords = ["wangi", "aroma", "lembut", "harga", "kemasan", "tekstur", "busa", "efektif", "alami", "rambut rontok", "ketombe"]
                        keyword_counts = {key: all_reasons.lower().count(key) for key in keywords}
                        
                        # Filter kata kunci yang muncul setidaknya sekali
                        filtered_counts = {k: v for k, v in keyword_counts.items() if v > 0}

                        if filtered_counts:
                            keyword_df = pd.DataFrame(list(filtered_counts.items()), columns=["Faktor Penentu", "Frekuensi"]).sort_values(by="Frekuensi", ascending=False)
                            st.markdown("### Frekuensi Penyebutan Faktor Penentu:")
                            st.dataframe(keyword_df, use_container_width=True)
                else:
                    st.warning("Data alasan terlalu sedikit untuk dianalisis secara mendalam.")
                    st.markdown("##### Daftar Alasan yang Diberikan:")
                    for i, alasan in enumerate(alasan_list, 1):
                        st.markdown(f"- {alasan}")
            else:
                st.info("Tidak ada data untuk analisis alasan favorit.")

# === Kolom Chatbot (Kiri) ===
with col_chat:
    st.title("Asisten Analis Pemasaran")
    st.markdown("Ajukan pertanyaan tentang data survei ini untuk mendapatkan insight.")

    # Tampilkan riwayat percakapan
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input dari pengguna
    if prompt := st.chat_input("Tanya AI tentang data survei..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Periksa sapaan sederhana terlebih dahulu
            if prompt.strip().lower() in ["hi", "halo", "hai"]:
                ai_answer = "Halo! Ada yang bisa saya bantu terkait analisis data survei ini?"
                st.markdown(ai_answer)
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            else:
                with st.spinner("AI sedang menganalisis..."):
                    llm = get_llm()
                    if llm and st.session_state.data_loaded_successfully:
                        # Menggunakan seluruh data sebagai konteks untuk AI
                        data_text = st.session_state.df.to_string()
                        
                        # Template prompt yang lebih terstruktur
                        prompt_template_qa = """
                        Anda adalah seorang analis pasar yang ahli. Berdasarkan data survei shampo berikut, jawab pertanyaan pengguna.
                        Fokuskan jawaban Anda pada insight pemasaran, persepsi konsumen, dan potensi strategi.
                        
                        DATA SURVEI:
                        ---
                        {data_text}
                        ---
                        
                        PERTANYAAN PENGGUNA:
                        "{prompt}"
                        
                        Berikan jawaban yang ringkas, jelas, dan informatif dalam Bahasa Indonesia.
                        """
                        
                        chain = PromptTemplate.from_template(prompt_template_qa) | llm
                        
                        # Memperbaiki pemanggilan invoke dengan kunci yang sesuai
                        ai_answer = chain.invoke({
                            "data_text": data_text, 
                            "prompt": prompt
                        }).content
                        
                        st.markdown(ai_answer)
                        st.session_state.messages.append({"role": "assistant", "content": ai_answer})
                    elif not st.session_state.data_loaded_successfully:
                        st.error("Tidak dapat menjawab karena data gagal dimuat. Mohon perbaiki masalah pada pemuatan data terlebih dahulu.")
                    else:
                        st.error("Gagal terhubung dengan model AI. Mohon periksa kembali API Key Anda.")
