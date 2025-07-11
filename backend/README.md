# Backend API

This is the FastAPI backend for the RAG chatbot, providing robust REST API endpoints for the React frontend.

## Features

- **Robust Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Logging**: Detailed logging for debugging and monitoring
- **CORS Support**: Configured for frontend development
- **Documentation**: Auto-generated API docs with Swagger/ReDoc
- **Type Safety**: Pydantic models for request/response validation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
- `GET /api/health` - Check if the server is running

### Chat
- `POST /api/chat` - Send a message and get a response
  - Body: `{"conversation_id": "string", "message": "string", "n_results": 3}`
  - Returns: `{"response": "string", "timestamp": "string", "context_preview": "string", "conversation_id": "string"}`

### File Upload
- `POST /api/upload` - Upload and process a file (PDF/DOCX)
  - Body: Form data with file
  - Returns: `{"filename": "string", "file_hash": "string", "status": "string", "chunks": int, "uploaded_at": "string", "message": "string"}`
- `GET /api/upload/files` - List uploaded files
- `DELETE /api/upload/files/{file_hash}` - Delete a specific file

### Conversations
- `GET /api/conversation` - List all conversations (summary)
- `POST /api/conversation` - Create a new conversation
  - Body: `{"title": "string"}` (optional)
- `GET /api/conversation/{id}` - Get a specific conversation with messages
- `PUT /api/conversation/{id}/rename` - Rename a conversation
  - Body: `{"title": "string"}`
- `DELETE /api/conversation/{id}` - Delete a conversation and its context

## Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (conversation/file not found)
- `500` - Internal Server Error

## Logging

Logs are written to both console and `backend.log` file with:
- Request/response logging
- Error details with stack traces
- Performance metrics

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Integration with rag_core

All business logic is handled by the existing `rag_core` modules:
- `rag_core.llm` - Language model interactions
- `rag_core.vectorstore` - Vector search and document storage
- `rag_core.document` - Document processing and chunking
- `rag_core.history` - Conversation and context management
- `rag_core.cache` - File hashing and caching

## Development

The backend is designed to work alongside the existing Streamlit frontend:
- Both use the same `rag_core` logic
- Shared persistent data (conversations, embeddings, etc.)
- No conflicts between API and Streamlit usage 