import os
import sys
import io
import json
import unittest
from pathlib import Path

# Pastikan root direktori proyek masuk ke sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
import pypdf

from main import DocumentAnalysis, KeyPoint, save_results, resolve_gemini_api_key
from app import (
    QuizQuestion,
    QuizSet,
    resolve_api_key,
    format_quiz_to_markdown,
    extract_text_from_pdf_stream,
)


class TestDocumentAnalysisSchemas(unittest.TestCase):
    def test_keypoint_valid(self):
        kp = KeyPoint(topic="Pengenalan", details="Penjelasan awal topik.")
        self.assertEqual(kp.topic, "Pengenalan")
        self.assertEqual(kp.details, "Penjelasan awal topik.")

    def test_document_analysis_valid(self):
        analysis = DocumentAnalysis(
            title="Laporan Tahunan 2026",
            summary="Ini adalah ringkasan singkat dokumen laporan.",
            key_points=[
                KeyPoint(topic="Finansial", details="Kenaikan laba 20%."),
                KeyPoint(topic="Operasional", details="Efisiensi meningkat."),
            ],
            action_items=["Evaluasi Q1", "Rekrut talenta baru"]
        )
        self.assertEqual(analysis.title, "Laporan Tahunan 2026")
        self.assertEqual(len(analysis.key_points), 2)
        self.assertEqual(len(analysis.action_items), 2)

        # Test serialisasi JSON Pydantic v2
        json_str = analysis.model_dump_json()
        data = json.loads(json_str)
        self.assertEqual(data["title"], "Laporan Tahunan 2026")
        self.assertEqual(len(data["key_points"]), 2)

    def test_document_analysis_missing_field(self):
        with self.assertRaises(ValidationError):
            # Missing summary and key_points
            DocumentAnalysis(title="Dokumen Tidak Lengkap")


class TestQuizSchemasAndFormat(unittest.TestCase):
    def test_quiz_question_and_set(self):
        q = QuizQuestion(
            question="Apa fungsi utama Gemini 3.8 Flash?",
            options=["Pengolah Teks & Multimodal Cepat", "Sistem Operasi", "Database SQL", "Antivirus"],
            correct_answer="Pengolah Teks & Multimodal Cepat",
            explanation="Gemini 3.8 Flash adalah model multimodal berkecepatan tinggi."
        )
        quiz_set = QuizSet(questions=[q])
        self.assertEqual(len(quiz_set.questions), 1)
        self.assertIn(q.correct_answer, q.options)

    def test_format_quiz_to_markdown(self):
        q = QuizQuestion(
            question="Berapa hasil 2 + 2?",
            options=["3", "4", "5", "6"],
            correct_answer="4",
            explanation="2 ditambah 2 adalah 4."
        )
        quiz_set = QuizSet(questions=[q])
        md = format_quiz_to_markdown(quiz_set, "Tes Matematika")
        self.assertIn("# 🎯 Kuis Pemahaman Materi: Tes Matematika", md)
        self.assertIn("Berapa hasil 2 + 2?", md)
        self.assertIn("> **Kunci Jawaban:** 4", md)


class TestApiKeyResolution(unittest.TestCase):
    def test_custom_key_priority(self):
        key, source = resolve_api_key("custom-secret-key-123")
        self.assertEqual(key, "custom-secret-key-123")
        self.assertEqual(source, "custom")

    def test_env_var_resolution(self):
        old_val = os.environ.get("GEMINI_API_KEY")
        try:
            os.environ["GEMINI_API_KEY"] = "mock-env-api-key"
            key, source = resolve_api_key("")
            self.assertEqual(key, "mock-env-api-key")
            self.assertEqual(source, "system")

            cli_key = resolve_gemini_api_key()
            self.assertEqual(cli_key, "mock-env-api-key")
        finally:
            if old_val is not None:
                os.environ["GEMINI_API_KEY"] = old_val
            else:
                os.environ.pop("GEMINI_API_KEY", None)


class TestTextExtractionAndExport(unittest.TestCase):
    def test_pdf_stream_extraction_empty_or_minimal(self):
        # Buat PDF kosong menggunakan pypdf writer
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=100, height=100)
        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        text, total_pages = extract_text_from_pdf_stream(buffer)
        self.assertEqual(total_pages, 1)
        self.assertEqual(text, "")

    def test_save_results_output(self):
        analysis = DocumentAnalysis(
            title="Uji Simpan",
            summary="Ringkasan uji simpan dokumen.",
            key_points=[KeyPoint(topic="Topik Uji", details="Detail uji simpan.")],
            action_items=["Tindakan 1"]
        )
        json_path, md_path = save_results(analysis, "sample_test_doc.pdf", mode="Akademik")
        try:
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            # Validasi isi file JSON
            with open(json_path, "r", encoding="utf-8") as f:
                saved_json = json.load(f)
                self.assertEqual(saved_json["title"], "Uji Simpan")

            # Validasi isi file MD
            with open(md_path, "r", encoding="utf-8") as f:
                saved_md = f.read()
                self.assertIn("# Uji Simpan", saved_md)
                self.assertIn("Mode Analisis**: Akademik", saved_md)
                self.assertIn("Ringkasan uji simpan dokumen.", saved_md)
        finally:
            # Cleanup test files
            if json_path.exists():
                json_path.unlink()
            if md_path.exists():
                md_path.unlink()


if __name__ == "__main__":
    unittest.main()
