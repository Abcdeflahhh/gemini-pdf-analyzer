import io
import os
import streamlit as st
from pydantic import BaseModel, Field
import pypdf
from google import genai
from google.genai import types


# ==========================================
# 1. Konfigurasi Halaman Streamlit
# ==========================================
st.set_page_config(
    page_title="AI PDF Analyzer & Summarizer",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# 2. Definisikan Skema Data (Pydantic v2)
# ==========================================
class KeyPoint(BaseModel):
    topic: str = Field(description="Topik atau sub-bahasan utama")
    details: str = Field(description="Penjelasan ringkas mengenai topik tersebut")


class DocumentAnalysis(BaseModel):
    title: str = Field(description="Judul atau topik sentral dari dokumen")
    summary: str = Field(description="Ringkasan eksekutif isi dokumen dalam 2-3 kalimat")
    key_points: list[KeyPoint] = Field(description="Daftar poin-poin penting dalam dokumen")
    action_items: list[str] = Field(
        default_factory=list,
        description="Daftar tindak lanjut, rekomendasi, atau action items jika ada"
    )


# ==========================================
# 3. Helper Ekstraksi & Analisis AI
# ==========================================
def extract_text_from_pdf_stream(pdf_file) -> tuple[str, int]:
    reader = pypdf.PdfReader(pdf_file)
    pages_text = []
    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(f"--- Halaman {i + 1} ---\n{text}")

    full_text = "\n\n".join(pages_text).strip()
    return full_text, total_pages


def analyze_with_gemini(document_text: str, api_key: str, model_name: str) -> DocumentAnalysis:
    client = genai.Client(api_key=api_key)

    prompt = (
        "Analisis dokumen berikut secara mendalam. Ekstrak informasi penting sesuai "
        "dengan skema data yang diminta dalam bahasa Indonesia yang formal dan jelas.\n\n"
        f"Konten Dokumen:\n{document_text}"
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentAnalysis,
            temperature=0.2,
        ),
    )

    return response.parsed


# ==========================================
# 4. Sidebar: Pengaturan & Profil
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfigurasi")

    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Gemini API Key:",
        value=env_api_key,
        type="password",
        help="Dapatkan kunci API gratis Anda di https://aistudio.google.com/apikey",
    )

    if not api_key:
        st.warning("⚠️ Masukkan Gemini API Key Anda untuk melanjutkan.")
        st.caption("[👉 Dapatkan API Key Gratis di Google AI Studio](https://aistudio.google.com/apikey)")
    else:
        st.success("✅ API Key siap digunakan!")

    model_option = st.selectbox(
        "Pilih Model Gemini:",
        options=["gemini-3.8-flash", "gemini-2.5-flash"],
        index=0,
        help="gemini-3.8-flash adalah model generasi terbaru yang cepat dan akurat.",
    )

    st.markdown("---")
    st.markdown("### 👨‍💻 Developer")
    st.markdown("**Aflah Athallah Tamam Kapukong**")
    st.markdown("[🌐 GitHub Repository](https://github.com/Abcdeflahhh/gemini-pdf-analyzer)")
    st.caption("Dibangun dengan Google GenAI SDK, Pydantic v2, pypdf, & Streamlit.")


# ==========================================
# 5. Konten Utama
# ==========================================
st.title("📑 AI PDF Analyzer & Structured Summarizer")
st.markdown(
    "Unggah dokumen PDF (materi kuliah, modul, jurnal, atau laporan kerja) untuk diekstrak "
    "dan dianalisis intisarinya secara otomatis menjadi **data terstruktur** dengan bantuan AI."
)

st.markdown("---")

uploaded_file = st.file_uploader(
    "Pilih atau Drag & Drop file PDF Anda ke kotak ini:",
    type=["pdf"],
    help="Hanya file dengan ekstensi .pdf yang didukung.",
)

if uploaded_file is not None:
    file_size_kb = len(uploaded_file.getvalue()) / 1024
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📁 **File:** `{uploaded_file.name}` ({file_size_kb:.1f} KB)")
    with col2:
        start_analysis = st.button("🚀 Analisis Dokumen", type="primary", use_container_width=True)

    if start_analysis:
        if not api_key:
            st.error("❌ Silakan masukkan Gemini API Key di menu sebelah kiri terlebih dahulu!")
        else:
            with st.spinner("⏳ Membaca isi PDF dan menganalisis teks dengan Gemini AI..."):
                try:
                    pdf_bytes = io.BytesIO(uploaded_file.getvalue())
                    raw_text, total_pages = extract_text_from_pdf_stream(pdf_bytes)

                    if not raw_text:
                        st.error("❌ Dokumen tidak mengandung teks terbaca (mungkin berupa hasil scan gambar).")
                    else:
                        analysis: DocumentAnalysis = analyze_with_gemini(
                            document_text=raw_text,
                            api_key=api_key,
                            model_name=model_option,
                        )

                        st.session_state["analysis_result"] = analysis
                        st.session_state["source_filename"] = uploaded_file.name
                        st.session_state["raw_text"] = raw_text
                        st.session_state["total_pages"] = total_pages
                        st.success(f"🎉 Dokumen ({total_pages} halaman) berhasil dianalisis dengan sempurna!")
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan saat analisis: {e}")

# Tampilkan Hasil Analisis jika sudah ada di session
if "analysis_result" in st.session_state:
    analysis: DocumentAnalysis = st.session_state["analysis_result"]
    filename = st.session_state["source_filename"]
    total_pages = st.session_state.get("total_pages", 0)

    st.markdown("---")
    st.subheader(f"📊 Hasil Analisis: {analysis.title}")

    tab1, tab2, tab3 = st.tabs(["📋 Ringkasan & Poin Penting", "💻 Format JSON Terstruktur", "📄 Teks Asli PDF"])

    with tab1:
        st.markdown("#### 📝 Ringkasan Eksekutif")
        st.write(analysis.summary)

        st.markdown("#### 🔍 Poin-Poin Pembahasan Utama")
        for idx, point in enumerate(analysis.key_points, 1):
            with st.expander(f"**{idx}. {point.topic}**", expanded=True):
                st.write(point.details)

        if analysis.action_items:
            st.markdown("#### ✅ Rekomendasi & Tindak Lanjut")
            for item in analysis.action_items:
                st.markdown(f"- {item}")

    with tab2:
        st.markdown("#### 💾 Data JSON Tervalidasi (Pydantic v2)")
        json_str = analysis.model_dump_json(indent=2)
        st.code(json_str, language="json")

    with tab3:
        st.markdown(f"#### 📄 Teks Mentah yang Diekstrak ({total_pages} Halaman)")
        st.text_area("Konten Teks", st.session_state.get("raw_text", ""), height=350)

    # Tombol Unduh / Export
    st.markdown("---")
    st.subheader("📥 Unduh Hasil Analisis")

    col_d1, col_d2 = st.columns(2)

    # Siapkan konten Markdown
    md_content = f"# {analysis.title}\n\n"
    md_content += f"- **Sumber Dokumen**: `{filename}`\n"
    md_content += f"- **Dianalisis Oleh**: Google Gemini ({model_option})\n\n"
    md_content += "## 📝 Ringkasan Eksekutif\n"
    md_content += f"{analysis.summary}\n\n"
    md_content += "## 🔍 Poin-Poin Penting\n"
    for idx, point in enumerate(analysis.key_points, 1):
        md_content += f"{idx}. **{point.topic}**\n   {point.details}\n"
    if analysis.action_items:
        md_content += "\n## ✅ Rekomendasi / Tindak Lanjut\n"
        for item in analysis.action_items:
            md_content += f"- {item}\n"

    with col_d1:
        st.download_button(
            label="📄 Unduh Ringkasan (.md)",
            data=md_content,
            file_name=f"{filename.replace('.pdf', '')}_summary.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_d2:
        st.download_button(
            label="💾 Unduh Data JSON (.json)",
            data=analysis.model_dump_json(indent=2),
            file_name=f"{filename.replace('.pdf', '')}_analysis.json",
            mime="application/json",
            use_container_width=True,
        )
