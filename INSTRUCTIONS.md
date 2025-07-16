# XOR RAG Chatbot – Developer Instructions (Extensive)

---

## 1. High-Level Overview

This project is a robust, production-grade, fully offline Retrieval-Augmented Generation (RAG) chatbot system for document Q&A, built with a modern React frontend, FastAPI backend, ChromaDB for vector storage, Ollama for LLM/embeddings, and Redis for caching. It is designed for secure, multi-document Q&A in sensitive environments, with persistent chat history, efficient vector storage, and a modern, user-friendly UI. All data and computation are local—no cloud dependencies after setup.

**Key Features:**
- Multi-document upload and Q&A
- Real-time, streaming LLM responses via Ollama
- Persistent, multi-chat history with context and uploads
- Efficient, cached vector storage (ChromaDB) and Redis caching for embeddings, queries, and chat history
- Per-chat and global embedding management
- Robust error handling, duplicate prevention, and UI state management
- Modern React UI/UX: error boundaries, loading spinners, banners, confirmations, and persistent status indicators
- Playwright integration tests for end-to-end verification
- Docker Compose for multi-service deployment
- Streamlit UI retained for debugging and development only
- Fully local: no internet required after setup

---

## 2. Architecture Diagram & Description

**Diagram:** See `assets/architecture.png` for a visual overview.

**Description:**
- **Frontend (React):**
  - Modern, responsive UI for chat, document upload, chat history, and admin actions
  - Real-time status indicators, error boundaries, loading spinners, banners, and confirmation dialogs
  - Communicates with backend via REST API (`/api` prefix)
- **Backend (FastAPI):**
  - **Document Processing:** Handles PDF/DOCX chunking, metadata extraction, and file hashing
  - **Vector Store (ChromaDB):** Stores and retrieves document chunks as embeddings, supports context expansion and per-file retrieval
  - **LLM (Ollama):** Local language model for answer generation, supports streaming and retry logic
  - **Cache (Redis):** Caches embeddings, query results, and chat history for performance
  - **History:** Persistent chat/context storage per chat, supports editing, deleting, and renaming
  - **Admin Endpoints:** Health checks, vectorstore management, and advanced operations
- **Integration:**
  - Frontend and backend are connected via a Vite proxy for local development (rewrites `/api` to backend root)
  - All services (Ollama, ChromaDB, Redis) run locally, orchestrated via Docker Compose for production or manual setup for development
- **Streamlit UI:**
  - Retained for debugging and development only; not used in production
- **Assets:** PITB branding, architecture diagrams
- **Logs:** All chat, context, and embedding data is stored locally for privacy and auditability

---

## 3. Folder & File Structure (Detailed)

- **backend/**: FastAPI backend application, including all API endpoints, core logic, and configuration.
- **frontend/**: React frontend application, including all UI components, state management, and API integration.
- **rag_core/**: Core logic shared by the backend (document processing, vectorstore, LLM, history, caching, config, utils).
- **assets/**: Branding images, architecture diagrams, and other static assets.
- **log/**: Stores all chat history, context, and embedding cache files (see below for details).
- **demo-rag-chroma/**: Persistent storage for ChromaDB vector database.
- **requirements.txt**: Python dependencies for the backend and core logic.
- **docker-compose.yml**: Orchestrates all services (backend, frontend, Ollama, ChromaDB, Redis) for local development and production.
- **README.md**: User-facing documentation, setup, and usage guide.
- **INSTRUCTIONS.md**: (This file) Developer-focused technical documentation and architecture notes.
- **GUIDE.md**: Advanced deployment, backup, and migration instructions.

### backend/ Directory
- **main.py**: FastAPI entrypoint, includes all API routes and startup logic.
- **api/**: API route definitions for chat, document, admin, and health endpoints.
- **dependencies/**: Dependency injection and shared backend utilities.
- **config.py**: Backend configuration and environment variable loading.
- **tests/**: Backend unit and integration tests.

### frontend/ Directory
- **src/**: All React source code (components, pages, hooks, utils, API clients). The chat UI is now fully responsive, with a collapsible sidebar, floating scroll-to-bottom button, and improved mobile experience. Users can set chunk size and overlap in the settings panel, and these are respected by the backend for new uploads. Chat rename is robust and updates everywhere in real time. Overlay blanks out the chat area while LLM is streaming. General UI/UX polish: rounded corners, shadows, smooth transitions, and better spacing.
- **public/**: Static assets for the frontend.
- **vite.config.js**: Vite configuration, including API proxy setup.
- **package.json**: Frontend dependencies and scripts.
- **tests/**: Playwright integration tests for end-to-end verification.

### rag_core/ Module Breakdown
- **ui.py**: (Streamlit UI, retained for debugging only) Chat logic, sidebar, chat management, file upload, and user interaction. Not used in production.
- **llm.py**: Handles all LLM (Ollama) interactions, including prompt construction, streaming responses, retry logic, and error/debug logging. Supports structured message history, windowing, and metadata.
- **vectorstore.py**: Manages ChromaDB vector storage, retrieval, context expansion, and collection reset. Handles batching, error handling, and contextual retrieval.
- **document.py**: Loads and chunks PDF/DOCX files, adds metadata (filename, chunk index), and supports extensible chunking logic. Can be extended for more file types.
- **cache.py**: Embedding and file hash caching utilities. Manages global and per-chat embedding caches as .pkl files. Supports cache cleanup and management.
- **redis_cache.py**: Redis-based caching for embeddings, queries, and chat history.
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

- **Local Development:**
  - Clone the repo.
  - Ensure Docker and Docker Compose are installed.
  - To start all services (backend, frontend, Ollama, ChromaDB, Redis):
    ```bash
    docker-compose up --build
    ```
  - The React frontend will be available at http://localhost:3000
  - The FastAPI backend will be available at http://localhost:8000
  - The Streamlit UI (for debugging) will be available at http://localhost:8501 (if you set `APP_MODE=debug` for the backend service)
  - Ollama (LLM) at http://localhost:11434, ChromaDB at http://localhost:8001, Redis at http://localhost:6379
  - To run the backend in debug mode (Streamlit UI):
    - Edit `docker-compose.yml` and set `APP_MODE=debug` for the backend service, then restart the containers.

- **Production Deployment:**
  - Use Docker Compose as above, but keep `APP_MODE=production` (default) for the backend.
  - Use HTTPS and authentication for sensitive environments.
  - For scaling, deploy with Docker Compose or Kubernetes as needed.

- **Rebuilding Images:**
  - If you change dependencies or code, rebuild with:
    ```bash
    docker-compose build
    docker-compose up
    ```

- **Backup & Migration:**
  - All persistent data is in `log/` and `demo-rag-chroma/`—back up these folders regularly.
  - See `GUIDE.md` for advanced migration and backup strategies.

---

## 9. Developer Workflow & Best Practices

- Use feature branches and unique commit messages for each file/change.
- Write modular, well-documented code—see module-level READMEs for guidance.
- Add type annotations and unit tests for new features.
- Use debug logging and error handling for all external calls (LLM, ChromaDB, file I/O).
- Keep requirements.txt up to date and minimal. Streamlit is included for debugging only.
- Update this file and module READMEs with any new features or design changes.
- Use Playwright for frontend integration tests (see `frontend/tests`).

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

# Running the Project Locally

## 1. Start Redis
```
sudo apt update
sudo apt install redis-server
redis-server
```

## 2. Install OCR Dependencies
```
sudo apt install tesseract-ocr poppler-utils
```

## 3. Backend Setup
```
cd /path/to/project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

## 4. Frontend Setup
```
cd frontend
npm install
npm run dev
```

## 5. Access the App
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## Notes
- Make sure your .env file is configured for the backend.
- OCR (scanned PDF) support requires Tesseract and poppler-utils.
- If you change ports, update the frontend proxy or API URLs accordingly. 