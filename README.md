# 📑 AI PDF Analyzer & Structured Summarizer

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.8_Flash-orange.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent document processing CLI tool powered by **Google Gemini 3.8 Flash**, **Pydantic**, and **pypdf**. It transforms unstructured PDF documents into high-quality, validated, structured analytical reports (JSON and Markdown) in seconds.

---

## 🚀 Key Features

- **📑 Multi-Page PDF Extraction**: Extracts and organizes text across all document pages using `pypdf`.
- **🧠 Generative Intelligence with Gemini 3.8 Flash**: Analyzes deep semantic context rather than just keyword matching.
- **🛡️ Strict Structured Outputs**: Leverages Pydantic v2 schemas (`response_schema`) to guarantee 100% compliant JSON data without formatting hallucinations.
- **💾 Dual-Format Export**: Automatically saves results into:
  - `outputs/<filename>_analysis.json` (Structured data ready for APIs, databases, or downstream applications).
  - `outputs/<filename>_summary.md` (Clean, human-readable executive summary and action items).
- **⚡ Fast & Lightweight**: Uses Gemini's fastest and most cost-effective reasoning model.

---

## 🏗️ Architecture & Workflow

```text
+------------------+       +------------------+       +----------------------------+
|                  |       |                  |       |                            |
|    Input PDF     | ----> |  pypdf Extractor | ----> |  Raw Text (Page-by-Page)   |
|                  |       |                  |       |                            |
+------------------+       +------------------+       +----------------------------+
                                                                     |
                                                                     v
+------------------+       +------------------+       +----------------------------+
|  Saved Outputs   |       |   Pydantic v2    |       |     Google Gemini API      |
|  (.json & .md)   | <---- | Schema Validation| <---- |    (gemini-3.8-flash)      |
+------------------+       +------------------+       +----------------------------+
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.13** | Core programming language |
| **Google GenAI SDK (`google-genai`)** | Interface for Gemini 3.8 Flash model generation |
| **Pydantic v2** | Data modeling, validation, and JSON schema enforcement |
| **pypdf** | PDF document parsing and text extraction |

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/gemini-pdf-analyzer.git
cd gemini-pdf-analyzer
```

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key
Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey).

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**Linux / macOS:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

---

## 🖥️ Usage

Run the script by providing the path to any PDF file:

```bash
python main.py "path/to/your/document.pdf"
```

Or run interactively:
```bash
python main.py
# The program will prompt:
# Masukkan path ke file PDF:
```

---

## 📊 Sample Output

### Terminal Output:
```text
📄 Membaca dokumen: PAI 5 PERTEMUAN 6.pdf (7 halaman)...
🤖 Mengirim teks ke Gemini untuk analisis terstruktur...

==================================================
 HASIL ANALISIS DOKUMEN
==================================================

📌 Judul  : Problematika Pernikahan dan Upaya Penanganannya

📝 Ringkasan:
Pernikahan merupakan sarana ibadah yang mulia, namun tidak terlepas dari dinamika 
dan potensi konflik. Dokumen ini mengkaji sumber-sumber permasalahan dalam rumah 
tangga serta pendekatan berbasis nilai-nilai Islam untuk menjaga keutuhan keluarga.

🔍 Poin Penting:
  1. [Hakikat dan Realitas Pernikahan] Sarana ibadah mulia dengan potensi tantangan internal dan eksternal.
  2. [Sumber Problematika] Bersumber dari faktor komunikasi, kepribadian, hingga tekanan finansial.
  3. [Dampak Masalah] Mengakibatkan ketidakharmonisan, pertengkaran, KDRT, hingga perceraian bila diabaikan.
  4. [Upaya Penanganan] Menjaga komunikasi terbuka, saling memaafkan, dan melibatkan konselor bila perlu.

✅ Tindakan / Rekomendasi:
  1. Berpegang teguh pada nilai-nilai Islam dalam kehidupan berkeluarga.
  2. Membangun komunikasi yang efektif dan terbuka antara pasangan.
  3. Melakukan evaluasi rutin sebelum konflik membesar.

==================================================
💾 HASIL BERHASIL DISIMPAN:
  • JSON : outputs/PAI_5_PERTEMUAN_6_analysis.json
  • MD   : outputs/PAI_5_PERTEMUAN_6_summary.md
==================================================
```

---

## 📂 Project Structure

```text
gemini-pdf-analyzer/
│
├── outputs/                 # Auto-generated analysis results (.json & .md)
├── venv/                    # Virtual environment (ignored in git)
├── .env.example             # Example environment file
├── .gitignore               # Git ignore rules
├── main.py                  # Core application pipeline
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
