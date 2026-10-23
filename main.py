import os
import sys
import argparse
from pathlib import Path

# Pastikan UTF-8 encoding di Windows console agar aman mencetak karakter non-ASCII/emoji
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pydantic import BaseModel, Field
import pypdf
from google import genai
from google.genai import types


# ==========================================
# 1. Definisikan Skema Data Terstruktur (Pydantic v2)
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
# 2. Resolusi API Key (Multi-Source Fallback)
# ==========================================
def resolve_gemini_api_key() -> str:
    """Mencari GEMINI_API_KEY dari environment variable, .env, atau .streamlit/secrets.toml."""
    # 1. Cek Environment Variable langsung
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        return api_key

    # 2. Cek file .env lokal
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
                                return val
        except Exception:
            pass

    # 3. Cek .streamlit/secrets.toml lokal jika ada
    secrets_file = Path(".streamlit/secrets.toml")
    if secrets_file.is_file():
        try:
            with open(secrets_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "GEMINI_API_KEY":
                            val = v.strip().strip("'\"")
                            if val:
                                return val
        except Exception:
            pass

    return ""


# ==========================================
# 3. Fungsi Ekstraksi Teks dari PDF (pypdf)
# ==========================================
def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {pdf_path}")

    reader = pypdf.PdfReader(str(path))
    pages_text = []
    total_pages = len(reader.pages)

    print(f"📄 Membaca dokumen: {path.name} ({total_pages} halaman)...")
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(f"--- Halaman {i + 1} ---\n{text}")

    full_text = "\n\n".join(pages_text).strip()
    return full_text, total_pages


# ==========================================
# 4. Analisis Dokumen dengan Gemini API (Multimodal Support)
# ==========================================
def analyze_with_gemini(
    document_text: str,
    pdf_path: str = None,
    mode: str = "Umum",
    model_name: str = "gemini-3.8-flash",
) -> DocumentAnalysis:
    api_key = resolve_gemini_api_key()
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY belum diatur di environment, .env, maupun .streamlit/secrets.toml.")
        print("Setel API Key Anda di PowerShell dengan perintah:")
        print('  $env:GEMINI_API_KEY="API_KEY_ANDA"')
        print("Atau buat file .env dengan isi:")
        print('  GEMINI_API_KEY="API_KEY_ANDA"')
        sys.exit(1)

    mode_instructions = {
        "Umum": "Berikan ringkasan komprehensif, poin penting, dan rekomendasi umum.",
        "Akademik": "Fokus pada konsep kunci, materi pokok, definisi ilmiah, dan pemahaman ujian/akademik.",
        "Bisnis": "Fokus pada ringkasan eksekutif tingkat tinggi, temuan kritis, data/fakta utama, dan rekomendasi keputusan strategis.",
    }
    instruction = mode_instructions.get(mode, mode_instructions["Umum"])

    client = genai.Client(api_key=api_key)

    prompt = (
        f"Gaya Analisis: {instruction}\n\n"
        "Analisis dokumen berikut secara mendalam. Ekstrak informasi sesuai "
        "dengan skema JSON yang diminta dalam bahasa Indonesia yang baku dan jelas.\n\n"
    )

    if document_text:
        contents = [f"{prompt}Konten Dokumen:\n{document_text}"]
    elif pdf_path and Path(pdf_path).is_file():
        print("⚠️ Teks mentah tidak ditemukan. Menggunakan analisis multimodal (gambar/scan) Gemini...")
        pdf_bytes = Path(pdf_path).read_bytes()
        contents = [
            prompt,
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        ]
    else:
        raise ValueError("Tidak ada teks maupun file PDF valid yang dapat dianalisis.")

    print(f"🤖 Mengirim ke {model_name} (Mode: {mode}) untuk analisis terstruktur...")
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentAnalysis,
            temperature=0.2,
        ),
    )

    result: DocumentAnalysis = response.parsed
    return result


# ==========================================
# 5. Fungsi Penyimpanan Hasil (JSON & Markdown)
# ==========================================
def save_results(
    analysis: DocumentAnalysis,
    source_pdf_path: str,
    mode: str = "Umum",
    model_name: str = "gemini-3.8-flash",
) -> tuple[Path, Path]:
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    # Bersihkan nama file agar aman digunakan sebagai nama file keluaran
    raw_stem = Path(source_pdf_path).stem
    safe_stem = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in raw_stem)

    # 1. Simpan format JSON terstruktur
    json_path = output_dir / f"{safe_stem}_analysis.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(analysis.model_dump_json(indent=2))

    # 2. Simpan format Markdown ringkasan manusia
    md_path = output_dir / f"{safe_stem}_summary.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {analysis.title}\n\n")
        f.write(f"- **Sumber Dokumen**: `{Path(source_pdf_path).name}`\n")
        f.write(f"- **Mode Analisis**: {mode}\n")
        f.write(f"- **Dianalisis Oleh**: Google Gemini ({model_name})\n\n")
        f.write("## 📝 Ringkasan Eksekutif\n")
        f.write(f"{analysis.summary}\n\n")
        f.write("## 🔍 Poin-Poin Penting\n")
        for idx, point in enumerate(analysis.key_points, 1):
            f.write(f"{idx}. **{point.topic}**\n   {point.details}\n")
        if analysis.action_items:
            f.write("\n## ✅ Rekomendasi / Tindak Lanjut\n")
            for idx, item in enumerate(analysis.action_items, 1):
                f.write(f"- {item}\n")

    return json_path, md_path


# ==========================================
# 6. Main Flow (CLI Entrypoint)
# ==========================================
def main():
    parser = argparse.ArgumentParser(
        description="AI PDF Analyzer & Structured Summarizer powered by Google Gemini"
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        help="Path ke file PDF dokumen yang ingin dianalisis"
    )
    parser.add_argument(
        "--mode",
        choices=["Umum", "Akademik", "Bisnis"],
        default="Umum",
        help="Mode gaya analisis: Umum, Akademik, atau Bisnis (default: Umum)"
    )
    parser.add_argument(
        "--model",
        default="gemini-3.8-flash",
        help="Model Gemini yang digunakan (default: gemini-3.8-flash)"
    )

    args = parser.parse_args()

    pdf_path = args.pdf_path
    if not pdf_path:
        pdf_path = input("Masukkan path ke file PDF: ").strip().strip('"')

    if not pdf_path:
        print("Path file tidak boleh kosong.")
        return

    try:
        text, total_pages = extract_text_from_pdf(pdf_path)
        analysis = analyze_with_gemini(
            document_text=text,
            pdf_path=pdf_path,
            mode=args.mode,
            model_name=args.model,
        )

        print("\n" + "=" * 55)
        print("📑 HASIL ANALISIS DOKUMEN")
        print("=" * 55)
        print(f"\n📌 Judul  : {analysis.title}")
        print(f"\n📝 Ringkasan:\n{analysis.summary}")

        print("\n🔍 Poin Penting:")
        for idx, point in enumerate(analysis.key_points, 1):
            print(f"  {idx}. [{point.topic}] {point.details}")

        if analysis.action_items:
            print("\n✅ Tindakan / Rekomendasi:")
            for idx, item in enumerate(analysis.action_items, 1):
                print(f"  {idx}. {item}")

        # Simpan hasil secara otomatis
        json_file, md_file = save_results(analysis, pdf_path, mode=args.mode, model_name=args.model)
        print("\n" + "=" * 55)
        print("💾 HASIL BERHASIL DISIMPAN:")
        print(f"  • JSON : {json_file}")
        print(f"  • MD   : {md_file}")
        print("=" * 55)

    except Exception as e:
        print(f"\n❌ Terjadi kesalahan: {e}")


if __name__ == "__main__":
    main()
