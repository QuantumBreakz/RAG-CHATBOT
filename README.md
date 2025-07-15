# XOR RAG Chatbot – Secure, Offline, Multi-Document Q&A

A robust, production-ready, fully offline RAG (Retrieval-Augmented Generation) chatbot for document Q&A, built with **React frontend**, **FastAPI backend**, **ChromaDB**, **Ollama**, and **Redis caching**. Designed for governmental and sensitive environments—no internet required after setup.

---

## 🚀 Features

### Core RAG Capabilities
- **Multi-format Document Support**: Upload and query PDF, DOCX, CSV, and Excel files
- **Real-time Embedding Generation**: Instant vector embeddings using Ollama's nomic-embed-text model
- **Intelligent Context Retrieval**: Advanced semantic search with context expansion
- **Conversation Memory**: Persistent chat history with context preservation
- **Knowledge Base Management**: Add, remove, and manage documents dynamically

### Modern Web Interface
- **React Frontend**: Modern, responsive UI built with TypeScript and Tailwind CSS
- **Real-time Chat Interface**: Streaming responses with typing indicators
- **Document Upload**: Drag-and-drop file upload with progress tracking
- **Conversation Management**: Save, load, export, and delete chat histories
- **Settings Panel**: Configure chunk sizes, overlap, and retrieval parameters
- **Dark/Light Theme**: Toggle between themes with persistent preferences

### Performance & Scalability
- **Redis Caching**: High-performance caching for embeddings, queries, and chat history
- **FastAPI Backend**: High-performance async API with automatic documentation
- **Docker Support**: Containerized deployment with docker-compose
- **Real-time Processing**: Streaming responses and live status updates
- **Error Handling**: Comprehensive error boundaries and user feedback

### Security & Privacy
- **Fully Offline**: No internet required after initial setup
- **Local Data Storage**: All data stored locally in ChromaDB and file system
- **CORS Protection**: Secure cross-origin request handling
- **Input Validation**: Comprehensive file and input validation

---

## 🏗️ Architecture

<p align="center">
  <img src="assets/architecture.png" alt="System Architecture Diagram" width="600"/>
</p>

**Figure:** Modern architecture with React frontend, FastAPI backend, Redis caching, ChromaDB vector store, and Ollama LLM.

### System Components

- **Frontend (React + TypeScript)**:
  - Modern UI with Tailwind CSS
  - Real-time chat interface
  - Document upload and management
  - Conversation history
  - Settings and configuration

- **Backend (FastAPI)**:
  - RESTful API endpoints
  - Document processing and chunking
  - Vector store operations
  - LLM integration
  - Redis caching layer

- **Data Layer**:
  - **ChromaDB**: Persistent vector storage
  - **Redis**: High-performance caching
  - **File System**: Document storage and chat logs

- **AI/ML Layer**:
  - **Ollama**: Local LLM inference and embeddings
  - **nomic-embed-text**: High-quality embeddings
  - **llama3.2:3b**: Fast, efficient language model

---

## 📁 Directory Structure

```
.
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── contexts/        # React contexts
│   │   └── main.tsx         # App entry point
│   ├── package.json         # Frontend dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── Dockerfile           # Frontend container
├── backend/                 # FastAPI backend
│   └── api.py              # Main API endpoints
├── rag_core/               # Core RAG logic
│   ├── vectorstore.py      # ChromaDB operations
│   ├── document.py         # Document processing
│   ├── llm.py             # LLM integration
│   ├── redis_cache.py     # Redis caching
│   ├── history.py         # Chat history management
│   └── config.py          # Configuration management
├── demo-rag-chroma/        # ChromaDB persistent storage
├── log/                    # Chat history and logs
├── assets/                 # Branding and architecture images
├── docker-compose.yml      # Multi-service deployment
├── Dockerfile              # Backend container
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
└── README.md
```

---

## 🚀 Quickstart

### Option 1: Docker Compose (Recommended)

1. **Clone and setup:**
   ```bash
   git clone https://github.com/QuantumBreakz/PITB-RAG.git
   cd PITB-RAG
   cp .env.example .env
   # Edit .env as needed
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development

1. **Backend Setup:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env configuration
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```

3. **Start Services:**
   ```bash
   # Terminal 1: Backend
   cd backend && uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   
   # Terminal 3: Redis (if not using Docker)
   redis-server
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

---

## ⚙️ Configuration

### Environment Variables (.env)

| Variable                  | Description                                      | Default                        |
|--------------------------|--------------------------------------------------|--------------------------------|
| **Ollama Configuration** |                                                  |                                |
| OLLAMA_BASE_URL          | Ollama server URL                                | http://localhost:11434         |
| OLLAMA_EMBEDDING_MODEL   | Embedding model name                             | nomic-embed-text:latest        |
| OLLAMA_LLM_MODEL         | LLM model name                                   | llama3.2:3b                    |
| **Application Settings** |                                                  |                                |
| MAX_FILE_SIZE            | Max file size in bytes                           | 10485760 (10MB)                |
| CHUNK_SIZE               | Document chunk size                              | 400                            |
| CHUNK_OVERLAP            | Chunk overlap                                    | 100                            |
| N_RESULTS                | Number of results to retrieve                    | 10                             |
| **Database Configuration** |                                              |                                |
| CHROMA_DB_PATH           | ChromaDB storage path                            | ./demo-rag-chroma              |
| CHROMA_COLLECTION_NAME   | ChromaDB collection name                         | pitb_rag_app_demo              |
| **Redis Configuration**  |                                                  |                                |
| REDIS_HOST               | Redis server host                                | localhost                      |
| REDIS_PORT               | Redis server port                                | 6379                           |
| REDIS_DB                 | Redis database number                            | 0                              |
| CACHE_TTL                | Cache time-to-live (seconds)                     | 3600                           |
| **Logging**              |                                                  |                                |
| LOG_LEVEL                | Logging level (DEBUG, INFO, etc.)                | INFO                           |
| LOG_FILE                 | Log file path                                    | pitb_rag_app.log               |

---

## 🔧 API Endpoints

### Document Management
- `POST /upload` - Upload and process documents
- `GET /documents` - List all documents in knowledge base
- `DELETE /documents/{filename}` - Remove specific document

### Chat & Query
- `POST /query` - Standard RAG query with context
- `POST /query/stream` - Streaming query response
- `GET /health` - Health check endpoint
- `GET /test_vectorstore` - Test vector store connectivity

### Chat History
- `GET /history/list` - List all conversations
- `GET /history/get/{conv_id}` - Get specific conversation
- `POST /history/save` - Save conversation
- `DELETE /history/delete/{conv_id}` - Delete conversation
- `GET /history/export/{conv_id}` - Export conversation as JSON

### System Management
- `POST /reset_kb` - Clear entire knowledge base

---

## 🎯 Advanced Features

### Real-time Embedding Generation
- **Instant Processing**: Documents are chunked and embedded immediately upon upload
- **Batch Processing**: Efficient handling of large documents with configurable batch sizes
- **Retry Logic**: Automatic retry with exponential backoff for failed operations
- **Progress Tracking**: Real-time feedback during document processing

### Intelligent Context Retrieval
- **Semantic Search**: Advanced vector similarity search using nomic-embed-text
- **Context Expansion**: Automatically includes neighboring chunks for better context
- **Keyword Boosting**: Prioritizes chunks containing important keywords
- **File Filtering**: Query specific documents or search across all

### Redis Caching Layer
- **Embedding Cache**: Caches document embeddings to avoid reprocessing
- **Query Cache**: Caches query results for improved response times
- **Chat History Cache**: Fast access to conversation data
- **Configurable TTL**: Adjustable cache expiration times

### Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Updates**: Live status indicators and progress bars
- **Error Boundaries**: Graceful error handling with user-friendly messages
- **Loading States**: Smooth loading animations and feedback
- **Theme Support**: Dark/light mode with persistent preferences

---

## 🐳 Docker Deployment

### Production Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Service Architecture
- **Frontend**: React app served by Vite dev server
- **Backend**: FastAPI with uvicorn ASGI server
- **Ollama**: Local LLM and embedding service
- **Redis**: Caching and session storage
- **ChromaDB**: Persistent vector storage

### Volume Mounts
- `./log` → Chat history and application logs
- `./demo-rag-chroma` → ChromaDB data persistence
- `./assets` → Static assets and branding

---

## 🔍 Troubleshooting

### Common Issues

**Frontend not connecting to backend:**
- Check if backend is running on port 8000
- Verify CORS settings in backend/api.py
- Check browser console for network errors

**Embedding generation fails:**
- Ensure Ollama is running and accessible
- Verify embedding model is installed: `ollama pull nomic-embed-text:latest`
- Check Ollama logs for errors

**Redis connection issues:**
- Verify Redis server is running: `redis-cli ping`
- Check Redis host/port configuration in .env
- Ensure Redis is accessible from backend container

**Document upload fails:**
- Check file size limits in .env
- Verify supported file types (PDF, DOCX, CSV, Excel)
- Check backend logs for processing errors

### Performance Optimization

**Slow response times:**
- Increase Redis cache TTL
- Optimize chunk size and overlap settings
- Use smaller embedding model for faster processing

**Memory issues:**
- Reduce batch size in vectorstore.py
- Limit concurrent document processing
- Monitor system resources during large uploads

---

## 🛠️ Development

### Adding New Features

**New File Types:**
1. Extend `DocumentProcessor` in `rag_core/document.py`
2. Add file type detection and processing logic
3. Update frontend file type validation

**New Vector Stores:**
1. Implement new `VectorStore` class in `rag_core/vectorstore.py`
2. Add configuration options in `rag_core/config.py`
3. Update API endpoints to use new store

**New LLM Providers:**
1. Extend `LLMHandler` in `rag_core/llm.py`
2. Add provider-specific API integration
3. Update configuration and environment variables

### Code Structure

- **Frontend**: React with TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI with async/await, Pydantic models
- **Core Logic**: Modular Python packages in `rag_core/`
- **Data Layer**: ChromaDB for vectors, Redis for caching, file system for storage

---

## 🔒 Security & Privacy

- **Fully Offline**: No internet required after initial setup
- **Local Data**: All embeddings, documents, and chat history stored locally
- **No Telemetry**: No data sent to external services
- **Input Validation**: Comprehensive validation of all inputs
- **CORS Protection**: Secure cross-origin request handling
- **Environment Variables**: Sensitive configuration via .env files

---

## 📄 License
MIT License

## 🙏 Acknowledgements
- [React](https://reactjs.org/) - Frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Ollama](https://ollama.com/) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Redis](https://redis.io/) - Caching layer
- [Tailwind CSS](https://tailwindcss.com/) - Styling framework
- [Vite](https://vitejs.dev/) - Build tool 
