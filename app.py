import io
import os
from pathlib import Path
import streamlit as st
from pydantic import BaseModel, Field
import pypdf
from google import genai
from google.genai import types


# ==========================================
# 1. Definisikan Skema Data (Pydantic v2)
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


class QuizQuestion(BaseModel):
    question: str = Field(description="Pertanyaan kuis terkait materi dokumen")
    options: list[str] = Field(description="Daftar 4 pilihan ganda (A, B, C, D)")
    correct_answer: str = Field(description="Jawaban yang benar (harus sama persis dengan salah satu opsi)")
    explanation: str = Field(description="Penjelasan ringkas mengapa jawaban tersebut benar")


class QuizSet(BaseModel):
    questions: list[QuizQuestion] = Field(description="Daftar 3 pertanyaan kuis pilihan ganda")


# ==========================================
# 2. Helper Resolusi API Key & Utilitas
# ==========================================
def resolve_api_key(custom_key: str = "") -> tuple[str, str]:
    """
    Menemukan API Key dengan hierarki prioritas:
    1. User Custom Input di UI
    2. Environment Variable sistem (GEMINI_API_KEY)
    3. Streamlit Secrets (.streamlit/secrets.toml)
    4. File .env lokal
    """
    if custom_key and custom_key.strip():
        return custom_key.strip(), "custom"

    # 1. Cek Environment Variable (lokal / container)
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key, "system"

    # 2. Cek Streamlit Secrets (untuk cloud streamlit / local secrets.toml)
    try:
        if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            secret_key = str(st.secrets["GEMINI_API_KEY"]).strip()
            if secret_key:
                return secret_key, "system"
    except Exception:
        pass

    # 3. Cek file .env lokal jika ada
    env_file = Path(".env")
    if env_file.is_file():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "GEMINI_API_KEY":
                            val = v.strip().strip("'\"")
                            if val:
                                return val, "system"
        except Exception:
            pass

    return "", "none"


def format_quiz_to_markdown(quiz: QuizSet, doc_title: str) -> str:
    """Format pertanyaan kuis dan pembahasannya ke format Markdown rapi."""
    lines = [
        f"# 🎯 Kuis Pemahaman Materi: {doc_title}",
        "",
        "> Dibuat otomatis menggunakan Google Gemini 3.8 Flash & Pydantic v2.",
        "",
        "---",
        "",
    ]
    for idx, q in enumerate(quiz.questions, 1):
        lines.append(f"### Pertanyaan {idx}: {q.question}\n")
        lines.append("**Pilihan Jawaban:**")
        for opt in q.options:
            lines.append(f"- {opt}")
        lines.append(f"\n> **Kunci Jawaban:** {q.correct_answer}")
        lines.append(f"> **Penjelasan:** {q.explanation}\n")
        lines.append("---\n")
    return "\n".join(lines)


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


def analyze_with_gemini(
    document_text: str,
    api_key: str,
    model_name: str,
    mode: str,
    pdf_bytes: bytes = None,
) -> DocumentAnalysis:
    client = genai.Client(api_key=api_key)

    mode_prompts = {
        "Umum (Comprehensive)": "Berikan ringkasan komprehensif, poin penting, dan rekomendasi umum.",
        "Akademik / Mahasiswa": "Fokus pada konsep kunci, pemahaman materi perkuliahan/sekolah, definisi penting, dan kisi-kisi pemahaman ujian.",
        "Eksekutif / Bisnis": "Fokus pada ringkasan eksekutif tingkat tinggi, temuan kritis, data/fakta utama, dan rekomendasi keputusan strategis.",
    }

    selected_instruction = mode_prompts.get(mode, mode_prompts["Umum (Comprehensive)"])

    prompt = (
        f"Gaya Analisis: {selected_instruction}\n\n"
        "Analisis dokumen berikut secara mendalam. Ekstrak informasi penting sesuai "
        "dengan skema data yang diminta dalam bahasa Indonesia yang jelas dan formal.\n\n"
    )

    if document_text:
        contents = [f"{prompt}Konten Dokumen:\n{document_text}"]
    elif pdf_bytes:
        contents = [
            prompt,
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        ]
    else:
        raise ValueError("Dokumen kosong atau tidak dapat dibaca.")

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentAnalysis,
            temperature=0.2,
        ),
    )

    return response.parsed


def generate_quiz(
    document_text: str,
    api_key: str,
    model_name: str,
    pdf_bytes: bytes = None,
) -> QuizSet:
    client = genai.Client(api_key=api_key)
    prompt = (
        "Berdasarkan dokumen berikut, buatkan 3 pertanyaan kuis pilihan ganda (A, B, C, D) "
        "yang menantang dan relevan untuk menguji pemahaman materi pembaca.\n\n"
    )

    if document_text:
        contents = [f"{prompt}Konten Dokumen:\n{document_text}"]
    elif pdf_bytes:
        contents = [
            prompt,
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        ]
    else:
        raise ValueError("Dokumen tidak memiliki konten untuk dibuat kuis.")

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuizSet,
            temperature=0.3,
        ),
    )
    return response.parsed


def chat_with_document(
    query: str,
    document_text: str,
    chat_history: list,
    api_key: str,
    model_name: str,
    pdf_bytes: bytes = None,
) -> str:
    client = genai.Client(api_key=api_key)
    system_instruction = (
        "Anda adalah asisten AI profesional untuk dokumen ini. Jawablah pertanyaan pengguna "
        "dengan akurat, ramah, dan HANYA berdasarkan informasi yang ada di dalam dokumen berikut. "
        "Jika informasinya tidak ada dalam dokumen, jelaskan secara jujur bahwa dokumen tidak memuat info tersebut."
    )

    contents = []
    if document_text:
        contents.append(f"=== ISI DOKUMEN ===\n{document_text}")
    elif pdf_bytes:
        contents.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))

    formatted_history = []
    for msg in chat_history:
        formatted_history.append(f"{msg['role'].upper()}: {msg['content']}")
    formatted_history.append(f"USER: {query}")

    contents.append("\n".join(formatted_history))

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
        ),
    )
    return response.text


# ==========================================
# 4. Streamlit Application Interface
# ==========================================
def main():
    st.set_page_config(
        page_title="AI PDF Analyzer & Chat Intelligence",
        page_icon="📑",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar: Konfigurasi & Preset
    with st.sidebar:
        st.header("⚙️ Konfigurasi")

        # Periksa apakah sistem memiliki API key bawaan
        default_key, default_source = resolve_api_key("")
        user_custom_key = ""

        if default_key:
            st.success("🟢 **Sistem Siap Digunakan!**\n\nAPI Key otomatis terdeteksi. Anda dapat langsung menganalisis file.")
            with st.expander("Gunakan API Key Sendiri (Opsional)"):
                user_custom_key = st.text_input(
                    "Custom Gemini API Key:",
                    type="password",
                    help="Kosongkan jika ingin menggunakan kuota bawaan web ini.",
                )
        else:
            user_custom_key = st.text_input(
                "Gemini API Key:",
                type="password",
                help="Dapatkan kunci API gratis di https://aistudio.google.com/apikey",
            )
            if not user_custom_key:
                st.warning("⚠️ Masukkan Gemini API Key untuk memulai.")
                st.caption("[👉 Dapatkan API Key Gratis di Google AI Studio](https://aistudio.google.com/apikey)")

        active_api_key, active_source = resolve_api_key(user_custom_key)

        model_option = st.selectbox(
            "Model Gemini:",
            options=["gemini-3.8-flash", "gemini-2.5-flash"],
            index=0,
            help="gemini-3.8-flash adalah model unggulan yang cepat, hemat kuota, dan sangat akurat.",
        )

        analysis_mode = st.selectbox(
            "🎯 Mode Analisis:",
            options=["Umum (Comprehensive)", "Akademik / Mahasiswa", "Eksekutif / Bisnis"],
            index=0,
            help="Sesuaikan sudut pandang analisis ringkasan sesuai kebutuhan Anda.",
        )

        st.markdown("---")
        st.markdown("### 👨‍💻 Developer")
        st.markdown("**Aflah Athallah Tamam Kapukong**")
        st.markdown("[🌐 GitHub Repository](https://github.com/Abcdeflahhh/gemini-pdf-analyzer)")
        st.caption("Dibangun dengan Google GenAI SDK, Pydantic v2, pypdf, & Streamlit.")

    # Konten Utama
    st.title("📑 AI PDF Analyzer & Chat Intelligence")
    st.markdown(
        "Unggah dokumen PDF Anda untuk diekstrak, dianalisis intisarinya secara terstruktur, "
        "menguji pemahaman dengan kuis otomatis, atau **tanya jawab langsung (Chat with PDF)**!"
    )

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Pilih atau Drag & Drop file PDF Anda:",
        type=["pdf"],
        help="Mendukung file dokumen PDF materi kuliah, modul, jurnal, atau laporan.",
    )

    # Reset session jika user mengganti file PDF
    if uploaded_file is not None:
        current_name = uploaded_file.name
        if st.session_state.get("current_file") != current_name:
            st.session_state["current_file"] = current_name
            st.session_state.pop("analysis_result", None)
            st.session_state.pop("quiz_result", None)
            st.session_state["chat_messages"] = []

        file_bytes = uploaded_file.getvalue()
        file_size_kb = len(file_bytes) / 1024

        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📁 **File:** `{uploaded_file.name}` ({file_size_kb:.1f} KB) | Mode: **{analysis_mode}**")
        with col2:
            start_analysis = st.button("🚀 Analisis Dokumen", type="primary", use_container_width=True)

        if start_analysis:
            if not active_api_key:
                st.error("❌ API Key belum tersedia. Silakan masukkan Gemini API Key di sidebar sebelah kiri!")
            else:
                with st.spinner("⏳ Memproses PDF dan menganalisis materi dengan Gemini 3.8 Flash..."):
                    try:
                        pdf_bytes_io = io.BytesIO(file_bytes)
                        raw_text, total_pages = extract_text_from_pdf_stream(pdf_bytes_io)

                        analysis = analyze_with_gemini(
                            document_text=raw_text,
                            api_key=active_api_key,
                            model_name=model_option,
                            mode=analysis_mode,
                            pdf_bytes=file_bytes,
                        )

                        st.session_state["analysis_result"] = analysis
                        st.session_state["source_filename"] = uploaded_file.name
                        st.session_state["raw_text"] = raw_text
                        st.session_state["total_pages"] = total_pages
                        st.session_state["file_bytes"] = file_bytes
                        st.success(f"🎉 Analisis selesai untuk {uploaded_file.name} ({total_pages} halaman)!")
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan: {e}")

    # Tampilkan Tabs Hasil Analisis
    if "analysis_result" in st.session_state:
        analysis: DocumentAnalysis = st.session_state["analysis_result"]
        filename = st.session_state["source_filename"]
        total_pages = st.session_state.get("total_pages", 0)
        raw_text = st.session_state.get("raw_text", "")
        cached_bytes = st.session_state.get("file_bytes", None)

        st.markdown("---")
        st.subheader(f"📊 {analysis.title}")

        tab_summary, tab_chat, tab_quiz, tab_json, tab_raw = st.tabs([
            "📋 Ringkasan & Poin Penting",
            "💬 Tanya Jawab (Chat PDF)",
            "🎯 Kuis Pemahaman",
            "💻 Data JSON Terstruktur",
            "📄 Teks Asli Dokumen",
        ])

        # TAB 1: Ringkasan
        with tab_summary:
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

            st.markdown("---")
            st.markdown("#### 📥 Unduh Hasil Analisis")
            col_d1, col_d2 = st.columns(2)

            md_content = f"# {analysis.title}\n\n"
            md_content += f"- **Sumber Dokumen**: `{filename}`\n"
            md_content += f"- **Mode Analisis**: {analysis_mode}\n"
            md_content += f"- **Model AI**: Google Gemini ({model_option})\n\n"
            md_content += "## 📝 Ringkasan Eksekutif\n"
            md_content += f"{analysis.summary}\n\n"
            md_content += "## 🔍 Poin-Poin Penting\n"
            for idx, point in enumerate(analysis.key_points, 1):
                md_content += f"{idx}. **{point.topic}**\n   {point.details}\n"
            if analysis.action_items:
                md_content += "\n## ✅ Rekomendasi / Tindak Lanjut\n"
                for idx, item in enumerate(analysis.action_items, 1):
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

        # TAB 2: Chat with PDF
        with tab_chat:
            col_chat_title, col_chat_clear = st.columns([3, 1])
            with col_chat_title:
                st.markdown("#### 💬 Tanya Apapun Tentang Dokumen Ini")
                st.caption("AI akan menjawab pertanyaan secara spesifik berdasarkan isi dokumen yang Anda unggah.")
            with col_chat_clear:
                if st.button("🗑️ Hapus Riwayat Chat", use_container_width=True):
                    st.session_state["chat_messages"] = []
                    st.rerun()

            if "chat_messages" not in st.session_state:
                st.session_state["chat_messages"] = []

            # Tampilkan riwayat chat sebelumnya
            for msg in st.session_state["chat_messages"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            user_query = st.chat_input("Ketik pertanyaan Anda tentang dokumen ini...")
            if user_query:
                st.session_state["chat_messages"].append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)

                with st.chat_message("assistant"):
                    with st.spinner("Berpikir berdasarkan isi PDF..."):
                        try:
                            reply = chat_with_document(
                                query=user_query,
                                document_text=raw_text,
                                chat_history=st.session_state["chat_messages"][:-1],
                                api_key=active_api_key,
                                model_name=model_option,
                                pdf_bytes=cached_bytes,
                            )
                            st.markdown(reply)
                            st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
                        except Exception as e:
                            st.error(f"Gagal mendapatkan respon chat: {e}")

        # TAB 3: Kuis Otomatis
        with tab_quiz:
            col_q_title, col_q_btn = st.columns([2, 1])
            with col_q_title:
                st.markdown("#### 🎯 Uji Pemahaman Anda")
                st.caption("Buat kuis pilihan ganda otomatis dari materi dokumen untuk menguji pemahaman.")
            with col_q_btn:
                btn_gen = st.button("🎲 Generate Kuis Baru", type="primary", use_container_width=True)

            if btn_gen:
                with st.spinner("Membuat pertanyaan kuis dengan Gemini..."):
                    try:
                        quiz_set = generate_quiz(
                            document_text=raw_text,
                            api_key=active_api_key,
                            model_name=model_option,
                            pdf_bytes=cached_bytes,
                        )
                        st.session_state["quiz_result"] = quiz_set
                    except Exception as e:
                        st.error(f"Gagal membuat kuis: {e}")

        if "quiz_result" in st.session_state:
            quiz: QuizSet = st.session_state["quiz_result"]
            for idx, q in enumerate(quiz.questions, 1):
                st.markdown(f"**Soal {idx}: {q.question}**")
                user_choice = st.radio(
                    f"Pilihan Jawaban Soal {idx}:",
                    options=q.options,
                    key=f"quiz_opt_{idx}",
                    label_visibility="collapsed",
                )
                with st.expander(f"👁️ Lihat Kunci Jawaban Soal {idx}"):
                    if user_choice == q.correct_answer:
                        st.success(f"✅ Jawaban Anda Benar: **{q.correct_answer}**")
                    else:
                        st.info(f"💡 Kunci Jawaban: **{q.correct_answer}**")
                    st.write(f"*Penjelasan:* {q.explanation}")
                st.markdown("---")

            # Tombol unduh kuis
            quiz_md = format_quiz_to_markdown(quiz, analysis.title)
            st.download_button(
                label="📥 Unduh Soal & Kunci Kuis (.md)",
                data=quiz_md,
                file_name=f"{filename.replace('.pdf', '')}_quiz.md",
                mime="text/markdown",
                use_container_width=False,
            )

        # TAB 4: JSON
        with tab_json:
            st.markdown("#### 💾 Data JSON Tervalidasi (Pydantic v2)")
            st.code(analysis.model_dump_json(indent=2), language="json")

        # TAB 5: Raw Text
        with tab_raw:
            st.markdown(f"#### 📄 Teks Mentah yang Diekstrak ({total_pages} Halaman)")
            if not raw_text:
                st.info("ℹ️ Dokumen ini berupa hasil scan gambar/grafik (tidak memiliki teks mentah langsung). Analisis dilakukan langsung menggunakan kemampuan multimodal Gemini.")
            else:
                st.text_area("Konten Teks", raw_text, height=350)


if __name__ == "__main__":
    main()
