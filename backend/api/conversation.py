from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from rag_core.history import list_conversations, load_conversation, save_conversation, new_conversation, delete_conversation, delete_chat_context, rename_conversation
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str

class Conversation(BaseModel):
    id: str
    title: str
    created_at: str
    messages: List[dict]
    uploads: List[dict]

class CreateConversationRequest(BaseModel):
    title: Optional[str] = None

class RenameConversationRequest(BaseModel):
    title: str

@router.get("/", response_model=List[ConversationSummary])
async def list_conversations_endpoint():
    """List all conversations (summary only)."""
    try:
        conversations = list_conversations()
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/", response_model=Conversation)
async def create_conversation(req: CreateConversationRequest):
    """Create a new conversation."""
    try:
        conv = new_conversation(req.title)
        save_conversation(conv)
        return conv
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all messages."""
    try:
        conv = load_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{conversation_id}/rename")
async def rename_conversation_endpoint(conversation_id: str, req: RenameConversationRequest = Body(...)):
    """Rename a conversation by id."""
    try:
        success = rename_conversation(conversation_id, req.title)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv = load_conversation(conversation_id)
        return conv
    except Exception as e:
        logger.error(f"Error renaming conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    """Delete a conversation and its associated chat context."""
    try:
        # Delete the conversation
        success = delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Also delete the chat context
        try:
            delete_chat_context(conversation_id)
        except Exception as context_error:
            logger.warning(f"Could not delete chat context for {conversation_id}: {str(context_error)}")
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/")
async def clear_all_conversations():
    """Clear all conversations. Use with caution!"""
    try:
        # This would need to be implemented to delete all conversation files
        # For now, return a warning message
        return {"message": "This endpoint is not yet implemented. Use individual delete endpoints."}
    except Exception as e:
        logger.error(f"Error clearing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 