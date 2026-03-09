# Audio-Enhanced Conversational AI Chatbot

A Streamlit app that turns YouTube video (or audio) into an interactive Q&A experience: transcribe with AssemblyAI, then ask questions and get answers grounded in the content via RAG (LangChain + FAISS).

---

## Origin & Attribution

This project is a **personal extension** of the tutorial-based implementation by [shivan118](https://github.com/Shivan118/Audio-Enhanced-Conversational-AI-Chatbot-using-RAG). The following additions and changes are my own:

- **Multilingual support** — Full UI and Q&A in English, Spanish, and Italian; language detection for transcriptions
- **Modular codebase** — Split into `app.py`, `stt_utils.py`, `qa_utils.py`, `language_config.py`, and `config.py` with shared paths and settings
- **Improved UI** — Clear layout, sidebar language selector, and user-facing error messages
- **Bug fixes & refactoring** — Correct DEBUG_MODE flow with mock data for cost-free testing; real RAG chain wired when not in debug; safe temp cleanup; timestamp display (ms → mm:ss); API key validation; centralized paths; stopword filtering for relevant timestamps; chunk overlap for better retrieval

---

## What It Does

Transcribe audio from a YouTube URL (AssemblyAI), optionally summarize it (OpenAI), and answer questions over the transcript using a vector store (FAISS) and an LLM. Supports **debug mode** with mock transcription and summaries so the full flow can be tested without API calls.

---

## Setup

### 1. Clone and enter the project
```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Virtual environment (choose one)
```bash
# Option A: venv
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux

# Option B: conda
conda create -p env python=3.10 -y
conda activate env/
```

### 3. Install dependencies
```bash
pip install -r requirements_dev.txt
```

### 4. Environment variables
Create a `.env` file in the project root:
```
ASSEMBLY_AI_KEY=your_assemblyai_key
OPENAI_API_KEY=your_openai_key
```
Required only when **not** using debug mode. In debug mode the app uses mock data and no API keys.

### 5. Run the app
```bash
streamlit run app.py
```
Open the URL shown in the terminal (e.g. http://localhost:8501). Set `DEBUG_MODE = True` in `app.py` to test without API costs.
