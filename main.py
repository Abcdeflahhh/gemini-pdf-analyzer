import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field
import pypdf
from google import genai
from google.genai import types


# ==========================================
# 1. Definisikan Skema Data Terstruktur (Pydantic)
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
# 2. Fungsi Ekstraksi Teks dari PDF (pypdf)
# ==========================================
def extract_text_from_pdf(pdf_path: str) -> str:
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {pdf_path}")

    reader = pypdf.PdfReader(str(path))
    pages_text = []

    print(f"📄 Membaca dokumen: {path.name} ({len(reader.pages)} halaman)...")
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(f"--- Halaman {i + 1} ---\n{text}")

    full_text = "\n\n".join(pages_text).strip()
    if not full_text:
        raise ValueError("Tidak ada teks yang dapat diekstrak dari PDF (mungkin berupa hasil scan gambar).")

    return full_text


# ==========================================
# 3. Analisis Dokumen dengan Gemini API
# ==========================================
def analyze_with_gemini(document_text: str) -> DocumentAnalysis:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY belum diatur di environment.")
        print("Setel API Key Anda di PowerShell dengan perintah:")
        print('  $env:GEMINI_API_KEY="API_KEY_ANDA"')
        sys.exit(1)

    print("🤖 Mengirim teks ke Gemini untuk analisis terstruktur...")
    client = genai.Client()

    prompt = (
        "Analisis dokumen berikut secara mendalam. Ekstrak informasi sesuai "
        "dengan skema JSON yang diminta dalam bahasa Indonesia.\n\n"
        f"Konten Dokumen:\n{document_text}"
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentAnalysis,
            temperature=0.2,
        ),
    )

    result: DocumentAnalysis = response.parsed
    return result


# ==========================================
# 4. Fungsi Penyimpanan Hasil (JSON & Markdown)
# ==========================================
def save_results(analysis: DocumentAnalysis, source_pdf_path: str) -> tuple[Path, Path]:
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
        f.write(f"- **Dianalisis Oleh**: Google Gemini (gemini-3.8-flash)\n\n")
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
# 5. Main Flow
# ==========================================
def main():
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("Masukkan path ke file PDF: ").strip().strip('"')

    if not pdf_path:
        print("Path file tidak boleh kosong.")
        return

    try:
        text = extract_text_from_pdf(pdf_path)
        analysis = analyze_with_gemini(text)

        print("\n" + "=" * 50)
        print(" HASIL ANALISIS DOKUMEN")
        print("=" * 50)
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
        json_file, md_file = save_results(analysis, pdf_path)
        print("\n" + "=" * 50)
        print("💾 HASIL BERHASIL DISIMPAN:")
        print(f"  • JSON : {json_file}")
        print(f"  • MD   : {md_file}")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Terjadi kesalahan: {e}")


if __name__ == "__main__":
    main()
