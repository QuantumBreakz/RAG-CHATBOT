"""
Advanced Context Management for RAG conversations.
Handles context windowing, summarization, and conversation threading.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from rag_core.config import logger
from rag_core.utils import sanitize_text

class ContextManager:
    """Manages conversation context with advanced features like windowing and summarization."""
    
    def __init__(self, max_context_length: int = 4000, max_history_length: int = 10):
        self.max_context_length = max_context_length
        self.max_history_length = max_history_length
        self.conversation_summaries = {}
    
    def create_context_window(self, 
                            current_question: str,
                            conversation_history: List[Dict],
                            retrieved_chunks: List[Dict],
                            session_id: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Create an optimized context window for the current query.
        
        Args:
            current_question: The current user question
            conversation_history: Previous conversation messages
            retrieved_chunks: Retrieved document chunks
            session_id: Optional session identifier
            
        Returns:
            Tuple of (context_string, context_metadata)
        """
        try:
            # Step 1: Analyze conversation history for relevance
            relevant_history = self._filter_relevant_history(current_question, conversation_history)
            
            # Step 2: Create conversation summary if needed
            summary = self._create_conversation_summary(conversation_history, session_id)
            
            # Step 3: Prioritize retrieved chunks
            prioritized_chunks = self._prioritize_chunks(current_question, retrieved_chunks)
            
            # Step 4: Build context string
            context_parts = []
            context_metadata = {
                "total_chunks": len(retrieved_chunks),
                "used_chunks": len(prioritized_chunks),
                "history_messages": len(relevant_history),
                "has_summary": bool(summary),
                "context_length": 0
            }
            
            # Add conversation summary if available
            if summary:
                context_parts.append(f"Conversation Summary: {summary}\n")
            
            # Add relevant conversation history
            if relevant_history:
                context_parts.append("Recent Conversation Context:")
                for msg in relevant_history[-3:]:  # Last 3 relevant messages
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    content = msg.get("content", "")[:200]  # Truncate long messages
                    context_parts.append(f"{role}: {content}")
                context_parts.append("")
            
            # Add document chunks with source attribution
            context_parts.append("Document Context:")
            for i, chunk in enumerate(prioritized_chunks):
                source_info = chunk.get("source", {})
                attribution = source_info.get("attribution", f"Document {i+1}")
                content = chunk.get("content", "")
                context_parts.append(f"[{attribution}]\n{content}\n")
            
            context_string = "\n".join(context_parts)
            context_metadata["context_length"] = len(context_string)
            
            # Truncate if too long
            if len(context_string) > self.max_context_length:
                context_string = context_string[:self.max_context_length] + "..."
                context_metadata["truncated"] = True
            
            return context_string, context_metadata
            
        except Exception as e:
            logger.error(f"Error creating context window: {str(e)}")
            # Fallback to simple context
            return self._create_simple_context(retrieved_chunks), {"error": str(e)}
    
    def _filter_relevant_history(self, current_question: str, history: List[Dict]) -> List[Dict]:
        """Filter conversation history for messages relevant to current question."""
        if not history:
            return []
        
        # Simple relevance scoring based on keyword overlap
        relevant_messages = []
        current_keywords = set(current_question.lower().split())
        
        for msg in history[-self.max_history_length:]:  # Consider last N messages
            if msg.get("role") != "user":
                continue
                
            msg_content = msg.get("content", "").lower()
            msg_keywords = set(msg_content.split())
            
            # Calculate simple overlap
            overlap = len(current_keywords.intersection(msg_keywords))
            if overlap > 0:
                relevant_messages.append(msg)
        
        return relevant_messages
    
    def _create_conversation_summary(self, history: List[Dict], session_id: Optional[str] = None) -> Optional[str]:
        """Create a summary of the conversation if it's getting long."""
        if len(history) < 6:  # Only summarize if conversation is long
            return None
        
        # Check if we have a cached summary
        if session_id and session_id in self.conversation_summaries:
            return self.conversation_summaries[session_id]
        
        # Create a simple summary
        user_messages = [msg for msg in history if msg.get("role") == "user"]
        if len(user_messages) < 3:
            return None
        
        # Extract key topics from user messages
        topics = []
        for msg in user_messages[-5:]:  # Last 5 user messages
            content = msg.get("content", "")
            # Simple topic extraction (first few words)
            words = content.split()[:5]
            if words:
                topics.append(" ".join(words))
        
        if topics:
            summary = f"Previous topics discussed: {'; '.join(topics)}"
            
            # Cache the summary
            if session_id:
                self.conversation_summaries[session_id] = summary
            
            return summary
        
        return None
    
    def _prioritize_chunks(self, question: str, chunks: List[Dict]) -> List[Dict]:
        """Prioritize chunks based on relevance to the current question."""
        if not chunks:
            return []
        
        # Simple prioritization based on keyword matching
        question_keywords = set(question.lower().split())
        
        def score_chunk(chunk):
            content = chunk.get("content", "").lower()
            chunk_keywords = set(content.split())
            overlap = len(question_keywords.intersection(chunk_keywords))
            return overlap
        
        # Score and sort chunks
        scored_chunks = [(chunk, score_chunk(chunk)) for chunk in chunks]
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # Return top chunks (limit to prevent context overflow)
        max_chunks = min(5, len(scored_chunks))
        return [chunk for chunk, score in scored_chunks[:max_chunks]]
    
    def _create_simple_context(self, chunks: List[Dict]) -> str:
        """Create a simple context string as fallback."""
        if not chunks:
            return ""
        
        context_parts = ["Document Context:"]
        for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
            source_info = chunk.get("source", {})
            attribution = source_info.get("attribution", f"Document {i+1}")
            content = chunk.get("content", "")
            context_parts.append(f"[{attribution}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def add_message_to_history(self, 
                             session_id: str,
                             role: str,
                             content: str,
                             sources: Optional[List[Dict]] = None,
                             metadata: Optional[Dict] = None) -> Dict:
        """Add a message to conversation history with metadata."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "sources": sources or [],
            "metadata": metadata or {}
        }
        
        # Store in session (this would typically be persisted)
        # For now, we'll just return the message
        return message
    
    def get_conversation_thread(self, session_id: str) -> List[Dict]:
        """Get the conversation thread for a session."""
        # This would typically load from persistent storage
        # For now, return empty list
        return []
    
    def clear_session_summary(self, session_id: str):
        """Clear cached summary for a session."""
        if session_id in self.conversation_summaries:
            del self.conversation_summaries[session_id]

# Global context manager instance
context_manager = ContextManager() 