import streamlit as st
import pandas as pd
import requests
import json
import base64
import io

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Aplikasi Survei Preferensi Shampo",
    page_icon="🧴",
    layout="centered"
)

# --- Token GitHub dan Detail Repositori ---
# Catatan: Ini adalah token yang Anda berikan.
GITHUB_TOKEN = "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"
CSV_FILE_PATH = "shampo_survey_responses.csv"

# Detail repositori diisi secara otomatis berdasarkan gambar yang Anda berikan.
GITHUB_OWNER = "shellatheresyapandiangan"
GITHUB_REPO = "survey_bot_basedai"
GITHUB_BRANCH = "main"

# --- Fungsi untuk berinteraksi dengan GitHub API ---
def get_github_file(owner, repo, file_path, branch):
    """Mengambil konten file dari GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content.decode('utf-8')
    return None

def push_to_github(owner, repo, file_path, branch, content, commit_message):
    """Mengunggah atau memperbarui file di GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    
    # Ambil SHA dari file yang ada jika ada
    sha = None
    try:
        response_check = requests.get(url, headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }, params={"ref": branch})
        if response_check.status_code == 200:
            sha = response_check.json().get("sha")
    except requests.exceptions.RequestException:
        pass

    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
        
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.put(url, headers=headers, data=json.dumps(payload))
    return response.status_code

# --- Judul dan Deskripsi Aplikasi ---
st.title("Formulir Survei Preferensi Shampo")
st.markdown("Silakan jawab pertanyaan di bawah ini untuk membantu kami memahami preferensi Anda.")
st.markdown("---")

# --- Form untuk Input Data Survei ---
st.header("Formulir Survei")
with st.form("shampo_survey_form"):
    st.subheader("Pertanyaan-pertanyaan")
    
    merek_diketahui = st.text_area(
        "1. Apa saja merek shampo yang Anda ketahui? (Pisahkan dengan koma)",
        key="merek_diketahui"
    )
    
    merek_digunakan = st.text_area(
        "2. Apa merek shampo yang Anda gunakan saat ini? (Jika lebih dari satu, pisahkan dengan koma)",
        key="merek_digunakan"
    )
    
    persepsi_tresemme = st.text_area(
        "3. Bagaimana persepsi Anda terkait shampo TRESemmé? Jelaskan secara singkat.",
        key="persepsi_tresemme"
    )
    
    tidak_suka_clear = st.text_area(
        "4. Apa yang tidak Anda sukai dari shampo CLEAR?",
        key="tidak_suka_clear"
    )
    
    favorit_shampo = st.text_area(
        "5. Shampo seperti apa yang Anda favoritkan? Pertimbangkan bungkus, wangi, tekstur, dll. Jelaskan alasannya.",
        key="favorit_shampo"
    )
    
    submit_button = st.form_submit_button("Kirim Jawaban dan Simpan ke GitHub")

# --- Logika Setelah Submit ---
if submit_button:
    if "YOUR_GITHUB_USERNAME" in GITHUB_OWNER or "YOUR_REPO_NAME" in GITHUB_REPO:
        st.error("Mohon ganti detail GitHub di dalam kode terlebih dahulu.")
    else:
        try:
            # Baca data yang sudah ada dari GitHub
            existing_content = get_github_file(GITHUB_OWNER, GITHUB_REPO, CSV_FILE_PATH, GITHUB_BRANCH)
            
            # Buat DataFrame baru dari input
            data_new = {
                "timestamp": [pd.to_datetime('now')],
                "merek_diketahui": [merek_diketahui],
                "merek_digunakan": [merek_digunakan],
                "persepsi_tresemme": [persepsi_tresemme],
                "tidak_suka_clear": [tidak_suka_clear],
                "favorit_shampo": [favorit_shampo]
            }
            df_new = pd.DataFrame(data_new)
            
            if existing_content:
                # Jika file sudah ada, gabungkan data
                existing_df = pd.read_csv(io.StringIO(existing_content))
                df_combined = pd.concat([existing_df, df_new], ignore_index=True)
            else:
                # Jika belum ada, gunakan data baru saja
                df_combined = df_new
                
            # Konversi DataFrame ke string CSV
            new_content = df_combined.to_csv(index=False)
            
            # Unggah ke GitHub
            commit_message = f"Menambahkan data survei pada {pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')}"
            status_code = push_to_github(GITHUB_OWNER, GITHUB_REPO, CSV_FILE_PATH, GITHUB_BRANCH, new_content, commit_message)
            
            if status_code in [200, 201]:
                st.success("🎉 Jawaban berhasil disimpan di repositori GitHub Anda!")
                github_raw_url = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{CSV_FILE_PATH}"
                st.write("URL file CSV yang akan digunakan untuk aplikasi analisis:")
                st.code(github_raw_url)
                st.dataframe(df_combined)
            else:
                st.error(f"Gagal mengunggah file. Status kode: {status_code}. Pastikan repositori dan branch valid.")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
