# ==============================================================================
# Aplikasi Analisis Data Survei Shampo
# Menggunakan LangChain & Groq API
# Versi: Desain UI/UX Premium
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
    page_title="Dashboard Analisis Shampo",
    page_icon="✨",
    layout="wide"
)

# --- Desain UI/UX Premium dengan CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    /* --- Global Styles --- */
    .stApp {
        background-color: #F0F4F8; /* Latar belakang abu-abu lembut */
        font-family: 'Poppins', sans-serif;
    }

    /* --- Kolom Utama --- */
    .main-column {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }
    
    .chat-column {
        padding-right: 1rem;
    }

    /* --- Tipografi --- */
    .header-title {
        font-size: 2.8em;
        font-weight: 700;
        color: #1E293B; /* Biru tua keabu-abuan */
        padding-bottom: 0.2rem;
    }
    .header-subtitle {
        font-size: 1.2em;
        color: #64748B; /* Abu-abu netral */
        font-weight: 400;
        padding-bottom: 1.5rem;
    }
    h3 {
        color: #334155;
        font-weight: 600;
    }

    /* --- Expander / Kartu Analisis --- */
    .stExpander {
        border: none;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        background-color: #F8FAFC; /* Warna kartu sedikit berbeda */
        margin-bottom: 1.5rem;
    }
    .stExpander [data-testid="stExpanderHeader"] {
        font-size: 1.1em;
        font-weight: 600;
        color: #334155;
    }
    .stExpander [data-testid="stExpanderContent"] {
        padding-top: 1.5rem;
    }

    /* --- Chat Interface --- */
    .st-chat-message-user {
        background-color: #E0F2FE; /* Biru muda untuk user */
        border-radius: 15px;
        padding: 12px;
    }
    .st-chat-message-assistant {
        background-color: #F1F5F9; /* Abu-abu sangat muda untuk asisten */
        border-radius: 15px;
        padding: 12px;
    }
    .stChatInput {
        background-color: #FFFFFF;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
    }
    
    /* --- Visualisasi --- */
    .stDataFrame {
        border: none;
    }
    .stDataFrame a {
        color: #2563EB;
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

def analyze_sentiment(text):
    """Menganalisis sentimen teks menjadi 'Baik', 'Buruk', atau 'Netral'."""
    llm = get_llm()
    if not llm: return "Netral"

    prompt = PromptTemplate.from_template(
        "Klasifikasikan sentimen dari teks berikut: '{text}'. Pilih salah satu dari kategori berikut: 'Baik', 'Buruk', atau 'Netral'. Berikan hanya satu kata dari kategori tersebut sebagai jawaban."
    )
    chain = prompt | llm
    try:
        response = chain.invoke({"text": text}).content
        sentiment = response.strip().upper()
        if "BAIK" in sentiment: return "Baik"
        elif "BURUK" in sentiment: return "Buruk"
        else: return "Netral"
    except Exception:
        return "Netral"

def create_wordcloud(text, title):
    """Membuat dan menampilkan WordCloud dari teks yang diberikan."""
    if not text or not text.strip():
        st.warning(f"Tidak ada data teks yang cukup untuk membuat '{title}'.")
        return

    wordcloud = WordCloud(
        width=800, height=400, background_color="white",
        max_words=50, regexp=r"\w[\w']+",
        font_path=None, colormap='viridis' # Menggunakan colormap yang lebih modern
    ).generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.subheader(title)
    st.pyplot(fig, use_container_width=True)

# --- 5. Memuat Data & Konfigurasi Kolom ---
SHEET_ID = "1Mp7KYO4w6GRUqvuTr4IRNeB7iy8SIZjSrLZmbEAm4GM"
SHEET_NAME = "Sheet1"
GOOGLE_SHEETS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

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

# === Kolom Asisten AI (Kiri) ===
with col_chat:
    st.markdown("<div class='chat-column'>", unsafe_allow_html=True)
    st.title("Asisten Analis")
    st.markdown("Ajukan pertanyaan untuk mendapatkan insight dari data survei.")

    # Tampilkan riwayat percakapan
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input dari pengguna
    if prompt := st.chat_input("Tanya tentang data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if prompt.strip().lower() in ["hi", "halo", "hai"]:
                ai_answer = "Halo! Saya siap membantu Anda menganalisis data survei ini. Silakan ajukan pertanyaan."
                st.markdown(ai_answer)
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            else:
                with st.spinner("Menganalisis..."):
                    llm = get_llm()
                    if llm and st.session_state.data_loaded_successfully:
                        data_text = st.session_state.df.to_string()
                        prompt_template_qa = """
                        Anda adalah seorang analis pasar ahli. Berdasarkan data survei shampo berikut, jawab pertanyaan pengguna.
                        Fokuskan jawaban Anda pada insight pemasaran, persepsi konsumen, dan potensi strategi.
                        DATA SURVEI: --- {data_text} ---
                        PERTANYAAN PENGGUNA: "{prompt}"
                        Berikan jawaban yang ringkas, jelas, dan informatif dalam Bahasa Indonesia.
                        """
                        chain = PromptTemplate.from_template(prompt_template_qa) | llm
                        ai_answer = chain.invoke({"data_text": data_text, "prompt": prompt}).content
                        st.markdown(ai_answer)
                        st.session_state.messages.append({"role": "assistant", "content": ai_answer})
                    elif not st.session_state.data_loaded_successfully:
                        st.error("Data gagal dimuat. Tidak dapat menjawab.")
                    else:
                        st.error("Gagal terhubung dengan model AI.")
    st.markdown("</div>", unsafe_allow_html=True)


# === Kolom Dashboard Analisis (Kanan) ===
with col_analysis:
    st.markdown("<div class='main-column'>", unsafe_allow_html=True)
    st.markdown("<div class='header-title'>Dashboard Analisis Survei Shampo</div>", unsafe_allow_html=True)
    st.markdown("<div class='header-subtitle'>Insight dari Konsumen Mengenai Preferensi Shampo</div>", unsafe_allow_html=True)

    if st.session_state.df is None:
        try:
            with st.spinner("Mengambil data dari Google Sheets..."):
                df_loaded = pd.read_csv(GOOGLE_SHEETS_URL)
                df_loaded.columns = [col.strip() for col in df_loaded.columns]
                column_mapping = {sheet_col: internal_name for sheet_col in df_loaded.columns for expected_col, internal_name in EXPECTED_COLUMNS.items() if expected_col.strip().lower() in sheet_col.lower()}
                df_loaded = df_loaded.rename(columns=column_mapping)
                st.session_state.df = df_loaded
                
                mapped_columns = set(df_loaded.columns)
                if all(col in mapped_columns for col in EXPECTED_COLUMNS.values()):
                    st.session_state.data_loaded_successfully = True
                else:
                    missing_cols = [k for k, v in EXPECTED_COLUMNS.items() if v not in mapped_columns]
                    st.error(f"Gagal memetakan kolom: {', '.join(missing_cols)}. Periksa nama kolom di Google Sheets.")
                    st.stop()
        except Exception as e:
            st.error(f"Gagal memuat data dari Google Sheets. Pastikan link publik dan nama sheet benar. Error: {e}")
            st.stop()
    
    df = st.session_state.df

    if st.session_state.data_loaded_successfully:
        with st.expander("⭐ Merek Terpopuler: Dikenal vs Digunakan", expanded=True):
            all_brands_text = ", ".join(df["merek_diketahui"].dropna().astype(str)) + ", " + ", ".join(df["merek_digunakan"].dropna().astype(str))
            all_brands_list = [brand.strip() for brand in re.split(r'[,;]+', all_brands_text.lower()) if brand.strip()]
            if all_brands_list:
                create_wordcloud(" ".join(all_brands_list), "Peta Popularitas Merek Shampo")
                top_10_brands = Counter(all_brands_list).most_common(10)
                st.subheader("Top 10 Merek Paling Sering Disebut")
                st.dataframe(pd.DataFrame(top_10_brands, columns=["Merek", "Frekuensi"]), use_container_width=True)
            else:
                st.info("Tidak ada data merek untuk dianalisis.")

        with st.expander("💡 Persepsi Terhadap TRESemmé (Analisis Sentimen AI)"):
            if "persepsi_tresemme" in df.columns and not df["persepsi_tresemme"].isnull().all():
                with st.spinner("Menganalisis sentimen TRESemmé..."):
                    df["sentimen_tresemme"] = df["persepsi_tresemme"].apply(lambda x: analyze_sentiment(str(x)) if pd.notna(x) else "Netral")
                sentiment_counts = df["sentimen_tresemme"].value_counts()
                
                fig, ax = plt.subplots()
                sentiment_counts.plot(kind='bar', ax=ax, color=['#22C55E', '#EF4444', '#94A3B8'])
                ax.set_title("Distribusi Sentimen Terhadap TRESemmé", fontsize=14, fontweight='bold', color='#334155')
                ax.set_ylabel("Jumlah Responden", fontsize=12, color='#475569')
                ax.tick_params(axis='x', rotation=0, colors='#475569')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                st.pyplot(fig)
            else:
                st.info("Tidak ada data persepsi TRESemmé untuk dianalisis.")

        with st.expander("👎 Poin Negatif Mengenai Shampo CLEAR"):
            if "tidak_suka_clear" in df.columns and not df["tidak_suka_clear"].isnull().all():
                text_dislikes = " ".join(df["tidak_suka_clear"].dropna().astype(str))
                create_wordcloud(text_dislikes, "Kata Kunci Keluhan Terhadap CLEAR")
            else:
                st.info("Tidak ada data keluhan mengenai CLEAR.")

        with st.expander("💖 Faktor Penentu dalam Memilih Shampo"):
            if "favorit_shampo" in df.columns and not df["favorit_shampo"].isnull().all():
                all_reasons = " ".join(df["favorit_shampo"].dropna().astype(str))
                if len(all_reasons.split()) >= 5:
                    create_wordcloud(all_reasons, "Peta Alasan Konsumen Memilih Shampo")
                    keywords = ["wangi", "aroma", "lembut", "harga", "kemasan", "tekstur", "busa", "efektif", "alami", "rambut rontok", "ketombe"]
                    keyword_counts = {key: all_reasons.lower().count(key) for key in keywords}
                    filtered_counts = {k: v for k, v in keyword_counts.items() if v > 0}
                    if filtered_counts:
                        keyword_df = pd.DataFrame(list(filtered_counts.items()), columns=["Faktor", "Frekuensi"]).sort_values(by="Frekuensi", ascending=False)
                        st.subheader("Faktor yang Paling Sering Disebut")
                        st.dataframe(keyword_df, use_container_width=True)
                else:
                    st.warning("Data alasan favorit terlalu sedikit untuk dianalisis.")
            else:
                st.info("Tidak ada data alasan favorit untuk dianalisis.")
    st.markdown("</div>", unsafe_allow_html=True)
