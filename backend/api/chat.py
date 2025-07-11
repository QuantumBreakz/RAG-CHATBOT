from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from rag_core.llm import LLMHandler
from rag_core.vectorstore import VectorStore
from rag_core.history import load_conversation, save_conversation, load_chat_context, save_chat_context
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    n_results: Optional[int] = 3

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    context_preview: Optional[str] = None
    conversation_id: str

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        # Load conversation
        conv = load_conversation(req.conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Load chat context (conversation history)
        chat_context = load_chat_context(req.conversation_id)
        if chat_context is None:
            # Initialize with conversation messages if no context exists
            chat_context = conv.get('messages', [])
        
        # Retrieve context from vectorstore
        results = VectorStore.query_with_expanded_context(
            req.message,
            n_results=req.n_results or 3,
            expand=2,
            filename=None  # Search all documents
        )
        
        context = results.get("documents", [[]])[0] if results.get("documents") else []
        context_str = " ".join(context) if context else ""
        
        if not context_str.strip():
            # No relevant context found
            response = "I don't have enough context to answer your question. Please try uploading some documents first or rephrasing your question."
        else:
            # Call LLM with context and history (stateless)
            try:
                response = LLMHandler.call_llm(req.message, context_str, chat_context)
            except Exception as llm_error:
                logger.error(f"LLM error: {str(llm_error)}")
                response = f"Sorry, I encountered an error while processing your request: {str(llm_error)}"
        
        # Save messages to conversation
        now = datetime.now().isoformat(timespec='seconds')
        
        # Add user message
        user_message = {
            "role": "user", 
            "content": req.message, 
            "timestamp": now
        }
        
        # Add assistant message
        assistant_message = {
            "role": "ai", 
            "content": response, 
            "timestamp": now,
            "context_preview": context_str[:200] + "..." if len(context_str) > 200 else context_str
        }
        
        # Update conversation
        conv["messages"].append(user_message)
        conv["messages"].append(assistant_message)
        save_conversation(conv)
        
        # Save updated chat context
        save_chat_context(req.conversation_id, conv["messages"])
        
        return ChatResponse(
            response=response,
            timestamp=now,
            context_preview=context_str[:200] + "..." if len(context_str) > 200 else context_str,
            conversation_id=req.conversation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 