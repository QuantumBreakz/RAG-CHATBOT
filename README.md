# PITB RAG Model - Government Edition

A fully offline, secure Streamlit app for Retrieval-Augmented Generation (RAG) that allows you to upload multiple PDF or DOCX files, ask questions, and get the most relevant document chunks using local language models and vector search. Designed for governmental and sensitive environments—no internet required.

## Features
- Upload and process multiple PDF or DOCX files
- Automatic document chunking for semantic search
- Query interface for asking questions about your documents
- All AI inference and vector search runs locally (Ollama + ChromaDB)
- Clean, modern Streamlit UI with PITB branding
- Telemetry and usage stats are disabled by default

## Requirements
- Python 3.9+
- See `requirements.txt` for all dependencies

## Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/QuantumBreakz/PITB-RAG.git
   cd PITB-RAG
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your preferred settings
   ```

## Usage
1. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```
2. **Open your browser** to the local Streamlit URL (usually http://localhost:8501).
3. **Upload one or more PDF or DOCX files** using the sidebar.
4. **Enter your question/query** in the chat interface and click "Send".
5. **View the top relevant chunks** as retrieved by the local vector search.

## How It Works
- Uploaded documents are split into semantic chunks using `langchain_text_splitters`.
- Chunks are embedded and stored locally in ChromaDB.
- When you enter a query, relevant chunks are retrieved using vector similarity.
- The answer is generated using a local LLM via Ollama.

## Security & Offline Operation
- **No internet connection required** after initial setup and model download.
- **Streamlit telemetry is disabled** via `.streamlit/config.toml`.
- For production, run the app behind a secure reverse proxy (e.g., NGINX).
- Add authentication if required for sensitive deployments.

## Environment Variables
The application uses environment variables for configuration. Copy `.env.example` to `.env` and modify as needed:

- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_EMBEDDING_MODEL`: Embedding model name (default: nomic-embed-text:latest)
- `OLLAMA_LLM_MODEL`: LLM model name (default: llama3.2:3b)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10485760 = 10MB)
- `CHUNK_SIZE`: Document chunk size (default: 400)
- `CHUNK_OVERLAP`: Chunk overlap (default: 100)
- `N_RESULTS`: Number of results to retrieve (default: 10)
- `CHROMA_DB_PATH`: ChromaDB storage path (default: ./demo-rag-chroma)
- `CHROMA_COLLECTION_NAME`: Collection name (default: pitb_rag_app_demo)

## Customization
- To support additional file types, extend the `process_documents` function.
- Modify environment variables in `.env` file for different configurations.

## Troubleshooting
- **Imports not resolved in IDE:**
  - Ensure your IDE is using the correct Python interpreter from your virtual environment.
  - Restart your IDE after installing dependencies.
- **CUDA/torch errors:**
  - If you have a GPU, install the appropriate torch version for CUDA. Otherwise, use CPU-only mode.
- **Large PDF files:**
  - Processing very large PDFs may be slow or memory-intensive. Consider splitting them before upload.

## License
MIT License

## Acknowledgements
- [Streamlit](https://streamlit.io/)
- [LangChain](https://www.langchain.com/)
- [Ollama](https://ollama.com/)
- [ChromaDB](https://www.trychroma.com/) 