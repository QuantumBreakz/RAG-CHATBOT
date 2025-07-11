import sys
import os
# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api import chat, upload, conversation
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Chatbot API",
    description="API for RAG-based chatbot with document processing and conversation management",
    version="1.0.0"
)

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])

@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "rag-chatbot-api"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    logger.info("RAG Chatbot API starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    logger.info("RAG Chatbot API shutting down...") 