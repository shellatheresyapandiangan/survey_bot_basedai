# ==============================================================================
# Aplikasi Analisis Data Survei Shampo
# Menggunakan LangChain & Groq API
# Versi: Desain Profesional
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
    page_icon="📊",
    layout="wide"
)

# --- Desain UI/UX Profesional dengan CSS ---
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
        font-size: 2.5em;
        font-weight: 700;
        color: #1E293B; /* Biru tua keabu-abuan */
        padding-bottom: 0.1rem;
    }
    .header-subtitle {
        font-size: 1.1em;
        color: #64748B; /* Abu-abu netral */
        font-weight: 400;
        padding-bottom: 2rem;
    }
    h3 {
        color: #334155;
        font-weight: 600;
    }

    /* --- Kartu KPI --- */
    .kpi-card {
        background: #F8FAFC;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        border: 1px solid #E2E8F0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.07);
    }
    .kpi-value {
        font-size: 2.5em;
        font-weight: 700;
        color: #10B981; /* Hijau cerah */
    }
    .kpi-value.blue { color: #3B82F6; } /* Biru */
    .kpi-value.yellow { color: #F59E0B; } /* Kuning/Amber */
    .kpi-label {
        font-size: 1em;
        font-weight: 400;
        color: #64748B;
        margin-top: 0.5rem;
    }
    .kpi-icon {
        font-size: 1.8em;
        margin-bottom: 0.8rem;
        color: #94A3B8;
    }

    /* --- Expander / Kartu Analisis --- */
    .stExpander {
        border: none;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        background-color: #F8FAFC;
        margin-top: 1.5rem;
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
        background-color: #E0F2FE;
        border-radius: 15px;
        padding: 12px;
    }
    .st-chat-message-assistant {
        background-color: #F1F5F9;
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
    .stDataFrame { border: none; }
    .stDataFrame a { color: #2563EB; }
</style>
""", unsafe_allow_html=True)

# --- 3. Konfigurasi Model AI (LLM) ---
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
    llm = get_llm()
    if not llm: return "Netral"
    prompt = PromptTemplate.from_template("Klasifikasikan sentimen dari teks berikut: '{text}'. Pilih salah satu dari: 'Baik', 'Buruk', atau 'Netral'. Berikan hanya satu kata.")
    chain = prompt | llm
    try:
        response = chain.invoke({"text": text}).content.strip().upper()
        if "BAIK" in response: return "Baik"
        elif "BURUK" in response: return "Buruk"
        else: return "Netral"
    except Exception:
        return "Netral"

def create_wordcloud(text, title):
    if not text or not text.strip():
        st.warning(f"Tidak ada data untuk membuat '{title}'.")
        return
    wordcloud = WordCloud(width=800, height=400, background_color="white", max_words=50, regexp=r"\w[\w']+", colormap='viridis').generate(text)
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
if 'messages' not in st.session_state: st.session_state.messages = []
if 'df' not in st.session_state: st.session_state.df = None
if 'data_loaded_successfully' not in st.session_state: st.session_state.data_loaded_successfully = False

# --- 7. Logika Utama Aplikasi ---
col_chat, col_analysis = st.columns([1, 2], gap="large")

# === Kolom Asisten AI (Kiri) ===
with col_chat:
    st.markdown("<div class='chat-column'>", unsafe_allow_html=True)
    st.title("Asisten Analis")
    st.markdown("Ajukan pertanyaan untuk mendapatkan insight dari data survei.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Tanya tentang data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            if prompt.strip().lower() in ["hi", "halo", "hai"]:
                ai_answer = "Halo! Saya siap membantu Anda menganalisis data survei ini. Silakan ajukan pertanyaan."
                st.markdown(ai_answer)
            else:
                with st.spinner("Menganalisis..."):
                    llm = get_llm()
                    if llm and st.session_state.data_loaded_successfully:
                        data_text = st.session_state.df.to_string()
                        prompt_template_qa = "Anda adalah analis pasar ahli. Berdasarkan data survei ini: --- {data_text} --- Jawab pertanyaan ini: '{prompt}'. Berikan jawaban ringkas, jelas, dan informatif dalam Bahasa Indonesia."
                        chain = PromptTemplate.from_template(prompt_template_qa) | llm
                        ai_answer = chain.invoke({"data_text": data_text, "prompt": prompt}).content
                        st.markdown(ai_answer)
                    elif not st.session_state.data_loaded_successfully:
                        ai_answer = "Data gagal dimuat. Tidak dapat menjawab."
                        st.error(ai_answer)
                    else:
                        ai_answer = "Gagal terhubung dengan model AI."
                        st.error(ai_answer)
            st.session_state.messages.append({"role": "assistant", "content": ai_answer})
    st.markdown("</div>", unsafe_allow_html=True)

# === Kolom Dashboard Analisis (Kanan) ===
with col_analysis:
    st.markdown("<div class='main-column'>", unsafe_allow_html=True)

    if st.session_state.df is None:
        try:
            with st.spinner("Mengambil data dari Google Sheets..."):
                df_loaded = pd.read_csv(GOOGLE_SHEETS_URL)
                df_loaded.columns = [col.strip() for col in df_loaded.columns]
                column_mapping = {sheet_col: internal_name for sheet_col in df_loaded.columns for expected_col, internal_name in EXPECTED_COLUMNS.items() if expected_col.strip().lower() in sheet_col.lower()}
                df_loaded = df_loaded.rename(columns=column_mapping)
                st.session_state.df = df_loaded
                if all(col in set(df_loaded.columns) for col in EXPECTED_COLUMNS.values()):
                    st.session_state.data_loaded_successfully = True
                else:
                    missing_cols = [k for k, v in EXPECTED_COLUMNS.items() if v not in set(df_loaded.columns)]
                    st.error(f"Gagal memetakan kolom: {', '.join(missing_cols)}. Periksa nama kolom.")
                    st.stop()
        except Exception as e:
            st.error(f"Gagal memuat data dari Google Sheets. Error: {e}")
            st.stop()
    
    df = st.session_state.df

    if st.session_state.data_loaded_successfully:
        # --- Judul Utama ---
        st.markdown("<div class='header-title'>Dashboard Analisis Survei Shampo</div>", unsafe_allow_html=True)
        st.markdown("<div class='header-subtitle'>Ringkasan Eksekutif dari Preferensi Konsumen</div>", unsafe_allow_html=True)

        # --- Bagian Kartu KPI ---
        kpi1, kpi2, kpi3 = st.columns(3)
        
        # KPI 1: Total Responden
        total_responden = len(df)
        kpi1.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div class="kpi-value blue">{total_responden}</div>
            <div class="kpi-label">Total Responden</div>
        </div>
        """, unsafe_allow_html=True)

        # KPI 2: Merek Teratas
        all_brands_list = [brand.strip() for brand in re.split(r'[,;]+', ", ".join(df["merek_diketahui"].dropna().astype(str)) + ", " + ", ".join(df["merek_digunakan"].dropna().astype(str)).lower()) if brand.strip()]
        merek_teratas = Counter(all_brands_list).most_common(1)[0][0].title() if all_brands_list else "N/A"
        kpi2.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🏆</div>
            <div class="kpi-value yellow">{merek_teratas}</div>
            <div class="kpi-label">Merek Terpopuler</div>
        </div>
        """, unsafe_allow_html=True)

        # KPI 3: Sentimen Positif TRESemmé
        if "persepsi_tresemme" in df.columns:
            if "sentimen_tresemme" not in df.columns:
                 df["sentimen_tresemme"] = df["persepsi_tresemme"].apply(lambda x: analyze_sentiment(str(x)) if pd.notna(x) else "Netral")
            sentimen_baik = df["sentimen_tresemme"].value_counts().get('Baik', 0)
        else:
            sentimen_baik = 0
        kpi3.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">👍</div>
            <div class="kpi-value">{sentimen_baik}</div>
            <div class="kpi-label">Sentimen Baik TRESemmé</div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- Bagian Analisis Detail ---
        st.header("Analisis Mendalam", anchor=False, divider="rainbow")
        
        with st.expander("⭐ Merek Terpopuler: Dikenal vs Digunakan", expanded=True):
            if all_brands_list:
                create_wordcloud(" ".join(all_brands_list), "Peta Popularitas Merek Shampo")
                st.subheader("Top 10 Merek Paling Sering Disebut")
                st.dataframe(pd.DataFrame(Counter(all_brands_list).most_common(10), columns=["Merek", "Frekuensi"]), use_container_width=True)
            else:
                st.info("Tidak ada data merek untuk dianalisis.")

        with st.expander("💡 Persepsi Terhadap TRESemmé (Analisis Sentimen AI)"):
            if "persepsi_tresemme" in df.columns and not df["persepsi_tresemme"].isnull().all():
                sentiment_counts = df["sentimen_tresemme"].value_counts()
                fig, ax = plt.subplots()
                sentiment_counts.plot(kind='bar', ax=ax, color=['#22C55E', '#EF4444', '#94A3B8'])
                ax.set_title("Distribusi Sentimen Terhadap TRESemmé", fontsize=14, fontweight='bold', color='#334155')
                ax.set_ylabel("Jumlah Responden", fontsize=12, color='#475569')
                ax.tick_params(axis='x', rotation=0, colors='#475569')
                ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
                st.pyplot(fig)
            else:
                st.info("Tidak ada data persepsi TRESemmé untuk dianalisis.")

        with st.expander("👎 Poin Negatif Mengenai Shampo CLEAR"):
            if "tidak_suka_clear" in df.columns and not df["tidak_suka_clear"].isnull().all():
                create_wordcloud(" ".join(df["tidak_suka_clear"].dropna().astype(str)), "Kata Kunci Keluhan Terhadap CLEAR")
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
                        st.subheader("Faktor yang Paling Sering Disebut")
                        st.dataframe(pd.DataFrame(list(filtered_counts.items()), columns=["Faktor", "Frekuensi"]).sort_values(by="Frekuensi", ascending=False), use_container_width=True)
                else:
                    st.warning("Data alasan favorit terlalu sedikit untuk dianalisis.")
            else:
                st.info("Tidak ada data alasan favorit untuk dianalisis.")
    st.markdown("</div>", unsafe_allow_html=True)
