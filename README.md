# 📑 AI PDF Analyzer & Chat Intelligence

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.8_Flash-orange.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end intelligent document processing system and web application powered by **Google Gemini 3.8 Flash**, **Pydantic v2**, **pypdf**, and **Streamlit**. It transforms unstructured PDF documents into high-quality, validated, structured analytical reports (JSON and Markdown), provides grounded **interactive Q&A (Chat with PDF)**, and generates **customizable comprehension quizzes**.

---

## 🚀 Key Features

- **📑 Multi-Page PDF Extraction & Multimodal Fallback**: Extracts page-by-page text using `pypdf`. Automatically falls back to native **Gemini Multimodal Vision** when dealing with scanned documents, diagrams, or image-only PDFs.
- **🧠 Generative Intelligence with Gemini 3.8 Flash**: Employs deep semantic analysis rather than naive keyword search.
- **🛡️ 100% Strict Structured Output**: Enforces Pydantic v2 schemas (`response_schema`) to guarantee format compliance without hallucinations.
- **💬 Interactive Chat with PDF (Q&A)**: Ask targeted questions grounded strictly in the document content with clear conversational history and context retention.
- **🎯 Analysis Presets**:
  - **Umum (Comprehensive)**: Broad summaries, core insights, and general recommendations.
  - **Akademik / Mahasiswa**: Focuses on core theoretical concepts, key definitions, and exam study points.
  - **Eksekutif / Bisnis**: High-level executive summaries, critical findings, and strategic decision points.
- **🎲 Automatic Quiz Generator & Markdown Export**: Creates 4-option multiple-choice questions with answer keys and explanations, downloadable as `.md` files for study groups or instructors.
- **💾 Dual-Format Export**: One-click download of structured JSON and Markdown executive reports.
- **🔑 Flexible Multi-Source API Key Resolution**: Automatically checks User UI override, system environment variables (`GEMINI_API_KEY`), Streamlit Secrets (`.streamlit/secrets.toml`), and local `.env` files.
- **🖥️ Dual Interface**: Use the modern interactive **Streamlit Web Application** or the fast **CLI tool**.

---

## 🏗️ Architecture & Workflow

```text
+---------------------+       +-----------------------+       +-----------------------------+
|                     |       |                       |       |                             |
|      Input PDF      | ----> |    pypdf Extractor    | ----> |   Raw Text (Page-by-Page)   |
| (Document / Scanned)|       |                       |       |                             |
+---------------------+       +-----------------------+       +-----------------------------+
           |                              |                                  |
           | (If scanned / image-only)    v                                  v
           +----------------------> [ Multimodal PDF Bytes ]        [ Prompt & Presets ]
                                                  \                   /
                                                   v                 v
                                            +-----------------------------+
                                            |      Google Gemini API      |
                                            |     (gemini-3.8-flash)      |
                                            +-----------------------------+
                                                           |
                                                           v
                                            +-----------------------------+
                                            |         Pydantic v2         |
                                            |     (Schema Validation)     |
                                            +-----------------------------+
                                                           |
                      +------------------------------------+------------------------------------+
                      |                                    |                                    |
                      v                                    v                                    v
           +----------------------+             +----------------------+             +----------------------+
           |  Executive Summary   |             |   Chat with PDF      |             |   Quiz Generator     |
           |  & Structured JSON   |             | (Grounded Q&A Tab)   |             | (& Markdown Export)  |
           +----------------------+             +----------------------+             +----------------------+
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.10+** (Tested up to 3.13) | Core programming language |
| **Streamlit** | Interactive modern web dashboard |
| **Google GenAI SDK (`google-genai`)** | Interface for Gemini 3.8 Flash model generation |
| **Pydantic v2** | Data modeling, schema validation, and JSON output |
| **pypdf** | PDF parsing and text stream extraction |
| **pytest & unittest** | Automated test suite and continuous integration |

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Abcdeflahhh/gemini-pdf-analyzer.git
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
pip install -r requirements-dev.txt   # Optional, for running tests
```

### 4. Configure API Key
Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey).

You can supply your key via any of the following methods:
- **Environment Variable (Recommended for terminal / production):**
  ```powershell
  # Windows PowerShell
  $env:GEMINI_API_KEY="your_api_key_here"

  # Linux / macOS
  export GEMINI_API_KEY="your_api_key_here"
  ```
- **Local `.env` File:**
  Copy `.env.example` to `.env` and insert your key:
  ```ini
  GEMINI_API_KEY=your_api_key_here
  ```
- **Streamlit Secrets (`.streamlit/secrets.toml`):**
  ```toml
  GEMINI_API_KEY = "your_api_key_here"
  ```
- **Web UI Sidebar:**
  Enter your key directly in the sidebar password box.

---

## 🖥️ Usage

### Option 1: Modern Web Application (Recommended)
Launch the interactive web UI powered by Streamlit:

```bash
streamlit run app.py
```
- Open `http://localhost:8501` in your browser.
- Upload any PDF document via drag-and-drop.
- Select your analysis mode (Umum, Akademik, or Bisnis).
- Click **🚀 Analisis Dokumen**.
- Explore the interactive tabs:
  - **📋 Ringkasan & Poin Penting**: Executive summary, key points, action items, and downloads.
  - **💬 Tanya Jawab (Chat PDF)**: Ask questions grounded strictly in the document content.
  - **🎯 Kuis Pemahaman**: Practice with multiple choice questions and download quiz materials.
  - **💻 Data JSON Terstruktur**: Validated Pydantic v2 JSON schema.
  - **📄 Teks Asli Dokumen**: Page-by-page raw text preview.

### Option 2: Command Line Interface (CLI)
Run the script directly via terminal:

```bash
# Basic usage
python main.py "path/to/your/document.pdf"

# Specify analysis mode (Umum, Akademik, Bisnis)
python main.py "path/to/your/document.pdf" --mode Akademik

# Display help and options
python main.py --help
```

---

## 🧪 Testing & Verification

The project includes unit tests for Pydantic schemas, text extractors, quiz formatters, and multi-source API key resolvers.

Run the test suite using **pytest**:
```bash
pytest -v
```

Or run via Python's built-in **unittest**:
```bash
python -m unittest tests/test_analyzer.py
```

---

## 📂 Project Structure

```text
gemini-pdf-analyzer/
│
├── .streamlit/
│   └── secrets.toml             # Local Streamlit secrets (ignored in git)
├── outputs/                     # Generated analysis reports (.json & .md)
├── tests/
│   └── test_analyzer.py         # Unit tests (schemas, extraction, resolvers)
├── venv/                        # Virtual environment
├── .env.example                 # Template for environment variables
├── .gitignore                   # Git ignore configurations
├── app.py                       # Streamlit web application & chat interface
├── LICENSE                      # MIT Open-Source License
├── main.py                      # CLI application pipeline
├── pytest.ini                   # Pytest configuration
├── README.md                    # Project documentation
├── requirements.txt             # Production dependencies
└── requirements-dev.txt         # Development & testing dependencies
```

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
Copyright (c) 2026 Aflah Athallah Tamam Kapukong.
