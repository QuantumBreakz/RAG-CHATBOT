# PITB RAG Chatbot – Secure, Offline, Multi-Document Q&A

A robust, production-ready, fully offline RAG (Retrieval-Augmented Generation) chatbot for document Q&A, built with Streamlit, ChromaDB, and Ollama. Designed for governmental and sensitive environments—no internet required after setup.

---

## Features

- Upload and query multiple PDF/DOCX files in a single chat
- Real-time, streaming LLM responses (word-by-word)
- Persistent, multi-chat history with context and uploads
- Efficient, cached vector storage (ChromaDB)
- Per-chat and global embedding management
- Robust error handling, duplicate prevention, and UI state management
- PITB branding, dark/light theme, and modern UX
- Fully local: no internet required after setup

---

## Architecture

![Architecture Diagram](assets/architecture.png)

- **Frontend:** Streamlit app with sidebar, chat, upload, and settings UI
- **Backend:**
  - **Document Processing:** PDF/DOCX chunking, metadata, and hashing
  - **Vector Store:** ChromaDB for persistent, local vector search
  - **LLM:** Ollama for local language model inference and embeddings
  - **Cache:** Per-chat and global embedding cache (by file hash)
  - **History:** Persistent chat/context storage per chat
- **Assets:** PITB branding, architecture diagrams
- **Logs:** All chat, context, and embedding data is stored locally

---

## Directory Structure

```
.
├── app.py                  # Streamlit entrypoint
├── rag_core/               # Core RAG logic (vectorstore, LLM, document, cache, UI)
├── assets/                 # Branding and architecture images
├── log/                    # Chat history, embeddings, and logs
├── demo-rag-chroma/        # ChromaDB persistent storage
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── LICENSE
├── README.md
├── GUIDE.md
└── ...
```

---

## Quickstart

1. **Clone and setup:**
   ```bash
   git clone https://github.com/QuantumBreakz/PITB-RAG.git
   cd PITB-RAG
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env as needed
   ```

2. **Run the app:**
   ```bash
   streamlit run app.py
   ```

3. **Upload documents, chat, and manage knowledge base via the sidebar.**

---

## Configuration

All settings are via `.env` (see `.env.example`).

### Key Environment Variables

| Variable                  | Description                                      | Default                        |
|--------------------------|--------------------------------------------------|--------------------------------|
| OLLAMA_BASE_URL          | Ollama server URL                                | http://localhost:11434         |
| OLLAMA_EMBEDDING_MODEL   | Embedding model name                             | nomic-embed-text:latest        |
| OLLAMA_LLM_MODEL         | LLM model name                                   | llama3.2:3b                    |
| MAX_FILE_SIZE            | Max file size in bytes                           | 10485760 (10MB)                |
| CHUNK_SIZE               | Document chunk size                              | 600                            |
| CHUNK_OVERLAP            | Chunk overlap                                    | 200                            |
| N_RESULTS                | Number of results to retrieve                    | 10                             |
| CHROMA_DB_PATH           | ChromaDB storage path                            | ./demo-rag-chroma              |
| CHROMA_COLLECTION_NAME   | ChromaDB collection name                         | pitb_rag_app_demo              |
| CACHE_TTL                | Embedding cache time-to-live (seconds)           | 86400                          |
| EMBEDDINGS_CACHE_PATH    | Path for embedding cache                         | ./log/global_embeddings        |
| LOG_FILE                 | Log file path                                    | ./log/pitb_rag_app.log         |
| LOG_LEVEL                | Logging level (DEBUG, INFO, etc.)                | INFO                           |

---

## Advanced Usage

### Streaming LLM Output
- Answers appear word-by-word in the chat for fast, interactive feedback.
- Uses Ollama’s streaming API and Streamlit’s dynamic UI updates.

### Multi-Document Q&A
- Upload multiple documents; queries search all by default.
- If only one document is uploaded, retrieval is restricted to that document.
- All document chunks are stored with metadata for precise filtering.

### Knowledge Base Reset
- Use the sidebar “Reset Knowledge Base” button to clear all embeddings and uploads.
- Ensures no cross-document contamination between sessions.

### Persistent Chat History
- All chats, uploads, and context are saved per chat in `log/conversations/`.
- Reload any chat, edit user messages, and manage uploads per chat.

### Robust Error Handling
- User-friendly error messages for missing context, LLM errors, or file issues.
- Debug logs are written to `log/pitb_rag_app.log` for troubleshooting.

---

## Troubleshooting

- **No response or slow answers:**
  - Ensure Ollama and ChromaDB are running and accessible.
  - Check logs in `log/pitb_rag_app.log` for errors.
- **CUDA/torch errors:**
  - If you have a GPU, install the appropriate torch version for CUDA. Otherwise, use CPU-only mode.
- **Large PDF files:**
  - Processing very large PDFs may be slow or memory-intensive. Consider splitting them before upload.
- **Streamlit widget errors:**
  - Ensure all widget keys are unique. If you see duplicate key errors, clear browser cache or reset the app.
- **Session state errors:**
  - The app auto-initializes session state, but if you see missing key errors, restart the app.

---

## Customization & Extension

- **Add new file types:**
  - Extend `DocumentProcessor` in `rag_core/document.py`.
- **Add new vector backends:**
  - Implement a new `VectorStore` in `rag_core/vectorstore.py`.
- **Add new LLMs:**
  - Update `rag_core/llm.py` with new API logic.
- **Change chunking or retrieval:**
  - Adjust `CHUNK_SIZE`, `CHUNK_OVERLAP`, and `N_RESULTS` in `.env` or via the UI settings.
- **Branding:**
  - Replace images in `assets/` for your organization’s branding.

---

## For Developers & Contributors

- All core logic is in `rag_core/` (see its README for details).
- Code is modular and extensible for new file types, LLMs, or vector stores.
- All persistent data is stored in `log/` and `demo-rag-chroma/`.
- Use `GUIDE.md` for advanced deployment, backup, and migration instructions.
- PRs and issues are welcome! Please follow the contribution guidelines in `GUIDE.md`.

---

## Security & Privacy

- All data, embeddings, and chat logs are stored locally.
- No telemetry, no external API calls after setup.
- For production, use HTTPS and add authentication as needed.
- Review and secure the `.env` file for sensitive deployments.

---

## License
MIT License

## Acknowledgements
- [Streamlit](https://streamlit.io/)
- [LangChain](https://www.langchain.com/)
- [Ollama](https://ollama.com/)
- [ChromaDB](https://www.trychroma.com/) 