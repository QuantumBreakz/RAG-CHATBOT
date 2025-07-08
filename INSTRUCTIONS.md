# PITB RAG Chatbot – Developer Instructions (Extensive)

---

## 1. High-Level Overview

This project is a robust, production-grade, fully offline Retrieval-Augmented Generation (RAG) chatbot for document Q&A, built with Streamlit, ChromaDB, and Ollama. It is designed for secure, multi-document Q&A in sensitive environments, with persistent chat history, efficient vector storage, and a modern, user-friendly UI. All data and computation are local—no cloud dependencies after setup.

**Key Features:**
- Multi-document upload and Q&A
- Real-time, streaming LLM responses
- Persistent, multi-chat history with context and uploads
- Efficient, cached vector storage (ChromaDB)
- Per-chat and global embedding management
- Robust error handling, duplicate prevention, and UI state management
- PITB branding, dark/light theme, and modern UX
- Fully local: no internet required after setup

---

## 2. Architecture Diagram & Description

**Diagram:** See `assets/architecture.png` for a visual overview.

**Description:**
- **Frontend (Streamlit):**
  - Sidebar: Chat management, file upload, settings, and knowledge base reset
  - Main Area: Chat bubbles, context preview, conversation history navigation, and chat input
- **Backend:**
  - **Document Processing:** Handles PDF/DOCX chunking, metadata extraction, and file hashing
  - **Vector Store (ChromaDB):** Stores and retrieves document chunks as embeddings, supports context expansion and per-file retrieval
  - **LLM (Ollama):** Local language model for answer generation, supports streaming and retry logic
  - **Cache:** Global and per-chat embedding cache, avoids recomputation
  - **History:** Persistent chat/context storage per chat, supports editing, deleting, and renaming
- **Assets:** PITB branding, architecture diagrams
- **Logs:** All chat, context, and embedding data is stored locally for privacy and auditability

---

## 3. Folder & File Structure (Detailed)

- **app.py**: Entrypoint for the Streamlit app. Handles startup checks (Ollama health, env vars) and launches the UI.
- **rag_core/**: All core logic for the RAG system (see below for module breakdown).
- **assets/**: Branding images, architecture diagrams, and other static assets.
- **log/**: Stores all chat history, context, and embedding cache files (see below for details).
- **demo-rag-chroma/**: Persistent storage for ChromaDB vector database.
- **requirements.txt**: Python dependencies for the project.
- **README.md**: User-facing documentation, setup, and usage guide.
- **INSTRUCTIONS.md**: (This file) Developer-focused technical documentation and architecture notes.
- **GUIDE.md**: Advanced deployment, backup, and migration instructions.

### rag_core/ Module Breakdown
- **ui.py**: Streamlit UI, chat logic, sidebar, chat management, file upload, and all user interaction. Handles chat rendering, context preview, history navigation, and error display. Implements visual threading, context preview, and message-level actions.
- **llm.py**: Handles all LLM (Ollama) interactions, including prompt construction, streaming responses, retry logic, and error/debug logging. Supports structured message history, windowing, and metadata.
- **vectorstore.py**: Manages ChromaDB vector storage, retrieval, context expansion, and collection reset. Handles batching, error handling, and contextual retrieval.
- **document.py**: Loads and chunks PDF/DOCX files, adds metadata (filename, chunk index), and supports extensible chunking logic. Can be extended for more file types.
- **cache.py**: Embedding and file hash caching utilities. Manages global and per-chat embedding caches as .pkl files. Supports cache cleanup and management.
- **history.py**: Persistent chat and context storage per chat. Handles saving/loading chat history, context, and uploads. Supports message threads and summarization.
- **config.py**: Loads environment variables, sets up logging, and defines system-wide constants (chunk size, model names, etc.).
- **utils.py**: Miscellaneous helpers (e.g., input sanitization, future: summarization/context formatting).

### log/ Directory
- **log/conversations/**: Stores all chat histories as JSON files (one per chat) and context as `context.pkl` (pickled Python objects). Each chat has its own subfolder for embeddings.
- **log/global_embeddings/**: Stores global embedding cache files as .pkl, keyed by file hash.
- **log/pitb_rag_app.log**: Main application log file for debugging and error tracking.

### demo-rag-chroma/
- Persistent storage for ChromaDB vector database. All document embeddings and metadata are stored here for fast retrieval and offline use.

### assets/
- Contains branding images (e.g., PITB logo), architecture diagrams, and any other static assets used in the UI or documentation.

---

## 4. API/Data Flow & Example Structures

### Session State Example (Streamlit)
```python
st.session_state = {
    'conversation_id': 'uuid',
    'conversation_history': [
        {'role': 'user', 'content': '...', 'timestamp': '...', 'followup_to': None},
        {'role': 'ai', 'content': '...', 'timestamp': '...', 'context_preview': '...'},
        ...
    ],
    'uploads': [
        {'filename': '...', 'file_hash': '...', 'metadata': {...}},
        ...
    ],
    'conversation_title': '...',
    'chat_input_value': '',
    'is_processing': False,
    ...
}
```

### File/Cache Example
- **log/conversations/<chat_id>.json**: Full chat history, uploads, and metadata
- **log/conversations/<chat_id>/context.pkl**: Pickled context for the chat
- **log/conversations/<chat_id>/embeddings/<file_hash>.pkl**: Per-chat embedding cache
- **log/global_embeddings/<file_hash>.pkl**: Global embedding cache

---

## 5. Error Handling & Troubleshooting

- All errors are logged to `log/pitb_rag_app.log` and surfaced in the UI.
- LLM errors are categorized:
  - **Connection issues:** Ollama server not running or wrong URL
  - **Memory issues:** System out of RAM or model too large
  - **Other errors:** Full traceback is logged
- UI displays actionable error messages for users and developers.
- Use the debug print/logs in `llm.py` for prompt/context/response inspection.
- If embeddings or context are missing, the UI will prompt the user to upload more documents or rephrase the query.

---

## 6. Security & Privacy

- All data, embeddings, and chat logs are stored locally—no cloud or external API calls after setup.
- No telemetry or analytics are sent externally.
- For production, use HTTPS and add authentication as needed.
- Review and secure the `.env` file for sensitive deployments.
- Regularly clean up old logs and embedding caches if needed.

---

## 7. Extensibility & Customization

- **Add new file types:** Extend `DocumentProcessor` in `rag_core/document.py`.
- **Add new vector backends:** Implement a new `VectorStore` in `rag_core/vectorstore.py`.
- **Add new LLMs:** Update `rag_core/llm.py` with new API logic.
- **Change chunking or retrieval:** Adjust `CHUNK_SIZE`, `CHUNK_OVERLAP`, and `N_RESULTS` in `.env` or via the UI settings.
- **Branding:** Replace images in `assets/` for your organization’s branding.
- **UI/UX:** All UI logic is in `ui.py`—add new features, themes, or accessibility improvements as needed.

---

## 8. Deployment, Scaling, and Operations

- **Local Deployment:**
  - Clone repo, set up Python venv, install requirements, run `streamlit run app.py`.
  - Ensure Ollama and ChromaDB are running locally.
- **Production Deployment:**
  - Use a process manager (e.g., systemd, supervisor) to keep the app running.
  - Use HTTPS and authentication for sensitive environments.
  - For scaling, containerize with Docker and orchestrate with Kubernetes if needed.
- **Backup & Migration:**
  - All persistent data is in `log/` and `demo-rag-chroma/`—back up these folders regularly.
  - See `GUIDE.md` for advanced migration and backup strategies.

---

## 9. Developer Workflow & Best Practices

- Use feature branches and unique commit messages for each file/change.
- Write modular, well-documented code—see module-level READMEs for guidance.
- Add type annotations and unit tests for new features.
- Use debug logging and error handling for all external calls (LLM, ChromaDB, file I/O).
- Keep requirements.txt up to date and minimal.
- Update this file and module READMEs with any new features or design changes.

---

## 10. Glossary of Terms

- **RAG (Retrieval-Augmented Generation):** Combines document retrieval with LLM-based answer generation.
- **Chunk:** A segment of a document, typically 600 characters with 200 overlap, used for embedding and retrieval.
- **Embedding:** A vector representation of a chunk, used for similarity search in ChromaDB.
- **ChromaDB:** Local vector database for storing and searching embeddings.
- **Ollama:** Local LLM server for running language models offline.
- **Session State:** Streamlit’s mechanism for storing per-user, per-session data.
- **Context Expansion:** Fetching neighboring chunks to provide more context for the LLM.
- **Cache:** Stores computed embeddings to avoid recomputation.
- **.pkl File:** Pickled Python object, used for storing embeddings and context.

---

## 11. Example End-to-End Flow

1. **User uploads a document.**
2. **Document is chunked and embedded.**
3. **Embeddings are stored in ChromaDB and cached as .pkl files.**
4. **User asks a question.**
5. **Relevant chunks are retrieved from ChromaDB.**
6. **Prompt is constructed with context and conversation history.**
7. **LLM (Ollama) generates a streaming response.**
8. **Response and context are saved to chat history.**
9. **User can edit, delete, or navigate messages and chats.**

---

## 12. Contact & Support
- For questions, see code comments, module READMEs, or contact the maintainers listed in the repo.
- For advanced deployment, see `GUIDE.md`.
- For bug reports or feature requests, open an issue or pull request on GitHub.

--- 