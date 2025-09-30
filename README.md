# XOR RAG Chatbot – Secure, Fully Offline, Multi-Document Q&A with Advanced AI Features

A robust, production-ready, **completely offline** RAG (Retrieval-Augmented Generation) chatbot for document Q&A, built with **React frontend**, **FastAPI backend**, **ChromaDB**, **Ollama with Mistral**, and **Redis caching**. Designed for governmental and sensitive environments—**zero internet required after initial setup**.

**🚀 Now featuring advanced AI capabilities from RAGFlow integration including Agentic RAG, Multi-OCR with Layout Analysis, Web Search, Anti-Hallucination, and Cross-Language Support.**

---

## 🚀 Features

### 🧠 Advanced AI Capabilities (RAGFlow Integration)
- **Agentic RAG System**: Multi-agent architecture with query analysis, search, reasoning, and synthesis agents
  - Intelligent query classification and routing
  - Advanced reasoning with confidence scoring
  - Tool calling capabilities for complex operations
  - Performance tracking and metrics
- **Enhanced Multi-OCR with Layout Analysis**: Advanced document processing pipeline
  - Layout-aware text extraction with table detection
  - Form field recognition and document structure analysis
  - Multi-engine OCR with consensus validation
  - Quality scoring for layout elements
- **Web Search Integration**: Real-time web search capabilities via Tavily API
  - Hybrid search combining local documents with web results
  - News and academic search capabilities
  - Source attribution for web results
  - Intelligent caching for web search results
- **Advanced Anti-Hallucination System**: Comprehensive fact verification
  - Multi-type hallucination detection
  - Source consistency checking
  - Confidence scoring and validation
  - Automatic correction suggestions
- **Cross-Language Query Support**: Multi-language processing for 11+ languages
  - Intelligent language detection
  - Query translation and processing
  - Multi-language embedding models
  - Cross-language search capabilities
- **Template-Based Chunking**: Intelligent document processing
  - Semantic and structural chunking strategies
  - Document-type specific templates
  - Explainable chunking decisions
  - Quality metrics and visualization

### Production-Ready Enhancements
- **Dynamic Query Routing**: Queries are automatically classified and routed to relevant documents
  - "Section 304" → Law documents
  - "Electronegativity of chlorine" → Chemistry documents
  - "Prayer times" → Religious documents
- **Hybrid Search**: Combines vector similarity with keyword matching for better results
- **Cross-encoder Reranking**: Advanced reranking using sentence-transformers for improved accuracy
- **Source Attribution**: Every response includes source information (document, page, section)
- **Domain Filtering**: UI allows filtering queries by specific domains
- **Health Monitoring**: Real-time system metrics and service status
- **Complete Offline Operation**: All AI models and services run locally with zero external dependencies
- **Multi-Document Conflict Resolution**: Detects and handles conflicting information across documents
- **Session Isolation**: Prevents context contamination between different queries
- **Anti-Hallucination**: Strict fact verification and source citation
- **Confidence Scoring**: Ranks sources by relevance and reliability

### Core RAG Capabilities
- **Multi-format Document Support**: Upload and query PDF, DOCX, CSV, and Excel files
- **Dynamic Query Routing**: Automatically route queries to relevant documents based on domain classification
- **Hybrid Search**: Combines dense vector search with sparse keyword matching for improved accuracy
- **Cross-encoder Reranking**: Uses sentence-transformers for advanced result reranking
- **Source Attribution**: Display sources with page numbers, sections, and document titles
- **Domain Filtering**: Filter queries by domain (law, chemistry, physics, etc.) for targeted results
- **Real-time Embedding Generation**: Instant vector embeddings using Ollama's nomic-embed-text model
- **Intelligent Context Retrieval**: Advanced semantic search with context expansion
- **Conversation Memory**: Persistent chat history with context preservation
- **Knowledge Base Management**: Add, remove, and manage documents dynamically

### Modern Web Interface
- **React Frontend**: Modern, responsive UI built with TypeScript and Tailwind CSS
- **Real-time Chat Interface**: Streaming responses with typing indicators
- **Responsive Design**: Sidebar is collapsible on mobile, chat bubbles and input area adapt to all screen sizes, and a floating scroll-to-bottom button appears when needed.
- **Document Upload**: Drag-and-drop file upload with progress tracking
- **Conversation Management**: Save, load, export, delete, and robustly rename chat histories (renames update everywhere in real time)
- **Settings Panel**: Configure chunk sizes and overlap in the frontend, which are respected by the backend for new uploads
- **Overlay During Streaming**: The chat area is blanked out with a loading overlay while the LLM is generating a response
- **UI/UX Polish**: Rounded corners, subtle shadows, smooth transitions, and improved spacing throughout
- **Dark/Light Theme**: Toggle between themes with persistent preferences

### Performance & Scalability
- **Redis Caching**: High-performance caching for embeddings, queries, and chat history
- **FastAPI Backend**: High-performance async API with automatic documentation
- **Health Monitoring**: Real-time system metrics and service health checks
- **Docker Support**: Containerized deployment with docker-compose
- **Real-time Processing**: Streaming responses and live status updates
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Production Ready**: Supports 100-1,000+ documents with intelligent routing

### Security & Privacy
- **Completely Offline**: Zero internet required after initial setup
- **Local Data Storage**: All data stored locally in ChromaDB and file system
- **Local AI Models**: All LLM, embedding, and reranking models run locally
- **No External APIs**: No cloud services or external dependencies (except optional web search)
- **Large File Support**: Up to 150MB file uploads
- **CORS Protection**: Secure cross-origin request handling
- **Input Validation**: Comprehensive file and input validation

---

## 🔌 Offline Setup & Deployment

### Prerequisites
- **Docker and Docker Compose** (for containerized deployment)
- **16-32GB RAM** (recommended for large document collections)
- **50GB+ disk space** (for models and data)
- **NVIDIA GPU** (optional, for faster LLM inference)

### Step 1: Initial Setup (Internet Required)
```bash
# Clone the repository
git clone <repository-url>
cd RAG-CHATBOT-XOR

# Create environment file
cp .env.example .env
```

### Step 2: Download All Dependencies (Internet Required)
```bash
# Install Python dependencies (all local, no external APIs)
pip install -r requirements.txt

# Pre-download sentence-transformers model (recommended for full offline use)
python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Pull Ollama models (stored locally in Docker volumes)
docker run --rm -v ollama_data:/root/.ollama ollama/ollama:latest ollama pull mistral:latest
docker run --rm -v ollama_data:/root/.ollama ollama/ollama:latest ollama pull nomic-embed-text
```

### Step 3: Deploy (Fully Offline)
```bash
# Build and start all services
docker-compose up --build -d

# Verify deployment
curl http://localhost:8000/health/detailed
```

### Step 4: Verify Offline Operation
```bash
# Disconnect from internet (optional test)
# All features should work without any external dependencies

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/domains
```

### ✅ Offline Operation Confirmation
After setup, the system runs **completely offline** with:
- ✅ **Local LLM**: Mistral 7B via Ollama (default)
- ✅ **Local Embeddings**: nomic-embed-text via Ollama  
- ✅ **Local Reranking**: sentence-transformers cross-encoder
- ✅ **Local Vector DB**: ChromaDB with persistent storage
- ✅ **Local Caching**: Redis with persistent storage
- ✅ **No External APIs**: Zero cloud dependencies (except optional web search)
- ✅ **No Internet Required**: All models and services local
- ✅ **Robust Error Handling**: Graceful fallbacks for document processing issues

---

## 🏗️ Architecture

**Figure:** Modern architecture with React frontend, FastAPI backend, Redis caching, ChromaDB vector store, and Ollama LLM with advanced AI features.

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
  - Advanced AI features (Agentic RAG, Multi-OCR, Web Search, etc.)

- **Data Layer**:
  - **ChromaDB**: Persistent vector storage
  - **Redis**: High-performance caching
  - **File System**: Document storage and chat logs

- **AI/ML Layer**:
  - **Ollama**: Local LLM inference and embeddings
  - **Mistral 7B**: Advanced language model (default)
  - **nomic-embed-text**: High-quality embeddings
  - **Agentic RAG**: Multi-agent architecture
  - **Multi-OCR**: Advanced document processing
  - **Web Search**: Real-time information retrieval
  - **Anti-Hallucination**: Fact verification system
  - **Cross-Language**: Multi-language support

---

## 📁 Directory Structure

```
.
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   │   ├── SourceDisplay.tsx  # Source attribution UI
│   │   │   └── DomainFilter.tsx   # Domain filtering UI
│   │   ├── pages/           # Page components
│   │   ├── contexts/        # React contexts
│   │   └── main.tsx         # App entry point
│   ├── package.json         # Frontend dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── Dockerfile           # Frontend container
├── backend/                 # FastAPI backend
│   └── api.py              # Main API endpoints with health monitoring
├── rag_core/               # Core RAG logic with advanced features
│   ├── agentic_rag.py      # Multi-agent RAG system
│   ├── multi_ocr.py        # Advanced OCR with layout analysis
│   ├── web_search.py       # Web search integration
│   ├── anti_hallucination.py # Fact verification system
│   ├── language_processor.py # Cross-language support
│   ├── chunking_templates.py # Intelligent document chunking
│   ├── conversation_manager.py # Advanced conversation management
│   ├── vectorstore.py      # ChromaDB operations with hybrid search
│   ├── document.py         # Document processing with semantic chunking
│   ├── llm.py             # LLM integration with Mistral
│   ├── reranker.py         # Cross-encoder reranking
│   ├── utils.py            # Query/document classification
│   ├── redis_cache.py     # Redis caching
│   ├── history.py         # Chat history management
│   └── config.py          # Configuration management
├── demo-rag-chroma/        # ChromaDB persistent storage
├── log/                    # Application logs and chat history
├── requirements.txt         # Python dependencies (all local)
├── docker-compose.yml      # Complete offline deployment
└── .env                    # Environment configuration
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
   - **Note:** The chat UI is now fully responsive and beautiful, with a collapsible sidebar, floating scroll-to-bottom button, and real-time chunk size/overlap settings.

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
| OLLAMA_LLM_MODEL         | LLM model name                                   | mistral:latest                 |
| **Application Settings** |                                                  |                                |
| MAX_FILE_SIZE            | Max file size in bytes                           | 157286400 (150MB)              |
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

### Advanced AI Features
- `POST /agentic/query` - Agentic RAG query with multi-agent processing
- `POST /agentic/stream` - Streaming agentic RAG response
- `POST /ocr/process` - Multi-OCR document processing
- `POST /ocr/layout` - Layout analysis for documents
- `POST /web/search` - Web search integration
- `POST /anti-hallucination/validate` - Fact verification
- `POST /language/detect` - Language detection
- `POST /language/translate` - Text translation
- `POST /chunking/template` - Template-based chunking

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

### Agentic RAG System
- **Multi-Agent Architecture**: Query analyzer, search agent, reasoning agent, and synthesis agent
- **Intelligent Query Classification**: Automatic routing to appropriate data sources
- **Advanced Reasoning**: Complex problem-solving with confidence scoring
- **Tool Calling**: Execute specific operations based on query requirements
- **Performance Tracking**: Real-time metrics and optimization

### Enhanced Multi-OCR with Layout Analysis
- **Layout-Aware Processing**: Document structure detection and analysis
- **Table Detection**: Automatic identification and extraction of tabular data
- **Form Field Recognition**: Intelligent form processing and field extraction
- **Multi-Engine Consensus**: Multiple OCR engines with validation
- **Quality Scoring**: Confidence metrics for extracted content

### Web Search Integration
- **Real-time Information**: Access to current web data via Tavily API
- **Hybrid Search**: Combine local documents with web results
- **News Search**: Latest news and current events
- **Academic Search**: Research papers and scholarly content
- **Source Attribution**: Proper citation of web sources

### Anti-Hallucination System
- **Fact Verification**: Comprehensive validation of generated responses
- **Source Consistency**: Cross-reference information across sources
- **Confidence Scoring**: Reliability metrics for responses
- **Contradiction Detection**: Identify conflicting information
- **Automatic Correction**: Suggest improvements for uncertain responses

### Cross-Language Support
- **Multi-Language Detection**: Support for 11+ languages
- **Query Translation**: Automatic translation of queries
- **Cross-Language Search**: Search across documents in different languages
- **Language-Specific Processing**: Optimized handling for each language
- **Translation Caching**: Performance optimization for repeated translations

### Template-Based Chunking
- **Intelligent Chunking**: Document-type specific processing strategies
- **Semantic Chunking**: Context-aware text segmentation
- **Structural Chunking**: Layout-based document organization
- **Quality Metrics**: Chunking effectiveness evaluation
- **Visualization**: Chunking decision explanations

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

--- Live stream: cd deployment && docker compose logs -f backend
Recent only: cd deployment && docker compose logs --tail=200 backend


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
- [Mistral AI](https://mistral.ai/) - Advanced language model
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Redis](https://redis.io/) - Caching layer
- [Tailwind CSS](https://tailwindcss.com/) - Styling framework
- [Vite](https://vitejs.dev/) - Build tool 

## Deployment Guide

### Environment Variables
- **Frontend:** Set `VITE_API_URL` in `frontend/.env` to your backend URL (e.g., `https://your-backend-domain.com`).
- **Backend:** Set `FRONTEND_ORIGIN` in the backend environment (or Dockerfile) to your frontend URL (e.g., `https://your-frontend-domain.com`).

### Docker
- Both frontend and backend Dockerfiles support these environment variables for deployment.
- See each Dockerfile for usage and example ENV lines.

### Steps
1. Build and run backend with correct `FRONTEND_ORIGIN`.
2. Build and run frontend with correct `VITE_API_URL`.
3. Ensure Ollama and ChromaDB are running and accessible.
4. Access the app via your frontend URL.

See `frontend/README.md` and `backend/Dockerfile` for more details. 

### Model Configuration
Available models through Ollama:
- `mistral:latest` (7B) - **Default** - Advanced reasoning and instruction following
- `llama3.2:3b` (3B) - Fast and efficient
- `llama2` (7B) - Balanced performance
- `llama2:13b` (13B) - Higher quality, more resource intensive
- `codellama` (Code specialized) - Programming and technical tasks
- `neural-chat` (7B) - Conversational AI optimized

### Advanced Features Status
- ✅ **Agentic RAG**: Multi-agent architecture with intelligent query processing
- ✅ **Multi-OCR**: Advanced document processing with layout analysis
- ✅ **Web Search**: Real-time information retrieval via Tavily API
- ✅ **Anti-Hallucination**: Comprehensive fact verification system
- ✅ **Cross-Language**: Multi-language support for 11+ languages
- ✅ **Template Chunking**: Intelligent document processing strategies
- ✅ **Conversation Management**: Advanced analytics and insights
- 🟡 **Advanced Reranking**: Enhanced result ranking (partially implemented)
- 🟡 **Performance Monitoring**: Comprehensive analytics (partially implemented)
- 🔴 **MCP Support**: Model Context Protocol (planned) 
