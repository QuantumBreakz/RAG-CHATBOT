# XOR RAG Chatbot

A production-grade, offline-first Retrieval-Augmented Generation (RAG) chatbot built for secure multi-document Q&A in high-stakes environments.

## 🚀 Features

- **Offline-First**: Complete privacy with no external API dependencies
- **Multi-Document Support**: PDF, DOCX, and text file processing
- **Real-time Streaming**: Natural conversation flow with word-by-word responses
- **Vector Search**: ChromaDB integration for semantic document retrieval
- **Modern UI**: Futuristic dark theme with smooth animations
- **Responsive Design**: Optimized for all devices and screen sizes
- **Persistent History**: Local storage for conversation continuity
- **Security-First**: Built for government, healthcare, and finance sectors

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Lucide React** for icons
- **React Router** for navigation

### Backend (Ready for Integration)
- **FastAPI** (Python) or **Express** (Node.js)
- **ChromaDB** for vector storage
- **Ollama** for offline LLM inference
- **Docker** for containerization

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Vector DB     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (ChromaDB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │   LLM Engine    │
                        │   (Ollama)      │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/xor-rag-chatbot.git
cd xor-rag-chatbot
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:5173`

### Production Build

```bash
npm run build
npm run preview
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000
VITE_MAX_FILE_SIZE=157286400
VITE_SUPPORTED_FORMATS=pdf,docx,txt
VITE_CHUNK_SIZE=1000
VITE_CHUNK_OVERLAP=200
```

### Model Configuration
Available models through Ollama:
- `llama2` (7B)
- `llama2:13b` (13B)
- `codellama` (Code specialized)
- `mistral` (7B)
- `neural-chat` (7B)

## 📱 Usage

### Document Upload
1. Navigate to the Chat interface
2. Click the upload button or drag & drop files
3. Supported formats: PDF, DOCX, TXT
4. Wait for processing and indexing

### Chat Interface
- Type questions naturally
- View streaming responses in real-time
- Access conversation history in the sidebar
- Manage document context per conversation

### Settings
- Configure model parameters
- Adjust chunk sizes and overlap
- Set cache preferences
- Toggle dark/light theme

## 🔒 Security Features

- **100% Offline Processing**: No external API calls
- **Local Data Storage**: All data remains on your infrastructure
- **End-to-End Encryption**: Secure data transmission
- **HIPAA Compliant**: Ready for healthcare environments
- **SOC 2 Ready**: Enterprise security standards
- **GDPR Compliant**: Privacy regulation adherence

## 🎨 UI/UX Features

- **Futuristic Dark Theme**: Grok-inspired design
- **Smooth Animations**: Micro-interactions and transitions
- **Responsive Layout**: Mobile-first approach
- **Accessibility**: WCAG compliant design
- **Loading States**: Engaging progress indicators
- **Error Handling**: Graceful error recovery

## 📊 Performance

- **Fast Document Processing**: Efficient chunking and indexing
- **Optimized Vector Search**: Quick semantic retrieval
- **Streaming Responses**: Reduced perceived latency
- **Memory Efficient**: Optimized for large document sets
- **Caching Layer**: Improved response times

## 🧪 Testing

```bash
# Run tests
npm test

# Run linting
npm run lint

# Type checking
npm run type-check
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t xor-rag-chatbot .

# Run container
docker run -p 3000:3000 xor-rag-chatbot
```

### Docker Compose

```yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend
      - chromadb
  
  backend:
    image: xor-rag-backend:latest
    ports:
      - "8000:8000"
    depends_on:
      - chromadb
  
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
      
volumes:
  chroma_data:
```

## 📝 API Documentation

### Endpoints

#### Chat
- `POST /api/chat` - Send message and get response
- `GET /api/chat/history` - Retrieve conversation history
- `DELETE /api/chat/history` - Clear conversation history

#### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List uploaded documents
- `DELETE /api/documents/{id}` - Delete document

#### Models
- `GET /api/models` - List available models
- `POST /api/models/load` - Load specific model

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** for offline LLM capabilities
- **ChromaDB** for vector storage
- **Tailwind CSS** for styling framework
- **Lucide** for beautiful icons
- **React Router** for navigation

## 📞 Support

For enterprise support and custom deployments, contact:
- Email: support@xor-rag.com
- Documentation: https://docs.xor-rag.com
- Issues: https://github.com/your-org/xor-rag-chatbot/issues

## 🔮 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Custom model fine-tuning
- [ ] Advanced document preprocessing
- [ ] Real-time collaboration features
- [ ] Mobile app version
- [ ] API rate limiting
- [ ] Advanced security features

---

**XOR RAG Chatbot** - Secure, Offline, Intelligent Document Processing

## Deployment Environment Variables

Create a `.env` file in the `frontend/` directory with:

```
VITE_API_URL=https://your-backend-domain.com
```

For local development, use:
```
VITE_API_URL=http://localhost:8000
```

Make sure to restart the frontend dev server after changing `.env`.