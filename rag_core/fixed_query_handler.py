"""
Fixed Query Handler - Anti-Hallucination Version

This module provides a clean, simplified query handler that prevents hallucinations
by implementing strict validation and context filtering.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from fastapi import Form
from rag_core.vectorstore import VectorStore
from rag_core.llm import LLMHandler
from rag_core.anti_hallucination import context_validator
from rag_core import history
from rag_core.context_manager import context_manager

logger = logging.getLogger(__name__)

async def process_query_fixed(
    question: str,
    n_results: int = 3,
    expand: int = 2,
    filename: str = None,
    domain_filter: str = None,
    conversation_history: str = "[]",
    session_id: str = None
) -> Dict[str, Any]:
    """
    Fixed query processing with anti-hallucination measures
    
    This function implements strict validation to prevent hallucinations:
    1. Validates all retrieved chunks for relevance
    2. Uses high confidence thresholds
    3. Creates bounded context for LLM
    4. Validates LLM responses
    """
    
    try:
        # Parse conversation history
        try:
            history_list = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history_list = []
        
        # Limit conversation history to prevent context pollution
        if len(history_list) > 3:  # Even more restrictive
            history_list = history_list[-3:]
        
        # Check if knowledge base is empty
        if not VectorStore.list_documents():
            return {
                "answer": "There is nothing in the knowledge base right now. Please upload a document before continuing.",
                "context": "",
                "status": "empty_kb",
                "sources": [],
                "context_metadata": {"error": "empty_kb"}
            }
        
        logger.info(f"Processing query: {question[:100]}...")
        
        # Retrieve chunks with higher confidence requirements
        results = VectorStore.query_with_expanded_context(
            question,
            n_results=n_results,
            expand=expand,
            filename=filename,
            domain_filter=domain_filter,
            session_id=session_id
        )
        
        # Process and validate chunks
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        sources = results.get('sources', [])
        
        # Convert to standardized format for validation
        raw_chunks = []
        min_length = min(len(docs), len(metas), len(sources))
        
        for i in range(min_length):
            chunk = {
                'content': docs[i],
                'metadata': metas[i],
                'source': sources[i] if i < len(sources) else {'confidence': 0.0}
            }
            raw_chunks.append(chunk)
        
        logger.info(f"Retrieved {len(raw_chunks)} raw chunks")
        
        # Apply strict validation
        validated_chunks = context_validator.validator.validate_chunks(question, raw_chunks)
        
        if not validated_chunks:
            logger.warning("No chunks passed validation")
            return {
                "answer": f"I cannot find relevant information about '{question}' in the available documents. The retrieved information doesn't appear to be directly related to your question.",
                "context": "",
                "status": "no_relevant_context",
                "sources": [],
                "context_metadata": {
                    "total_chunks_retrieved": len(raw_chunks),
                    "chunks_after_validation": 0,
                    "validation_failed": True
                }
            }
        
        # Create safe context for LLM
        context_str, context_metadata = context_validator.create_safe_context(
            question, validated_chunks, max_tokens=1500
        )
        
        logger.info(f"Created context with {context_metadata['sources_used']} sources")
        
        # Generate response using strict prompt
        strict_prompt = f"""Based STRICTLY on the provided context, answer the following question. 

CRITICAL RULES:
- ONLY use information from the provided context
- If the answer is not in the context, state this clearly
- Do not add external knowledge or make assumptions
- Cite the specific sources when possible

Context:
{context_str}

Question: {question}

Answer:"""
        
        try:
            # Generate response
            answer = ""
            for word in LLMHandler.call_llm(strict_prompt, "", []):  # No conversation history to avoid contamination
                answer += word
            
            # Validate the response doesn't contain hallucinations
            if _validate_response(answer, validated_chunks, question):
                status = "success"
            else:
                answer = f"I cannot provide a reliable answer to '{question}' based on the available documents. The information may be incomplete or unclear."
                status = "response_validation_failed"
                
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            answer = f"Error generating response: {str(e)}"
            status = "llm_error"
        
        # Add to conversation history if session provided
        if session_id:
            context_manager.add_message_to_history(
                session_id=session_id,
                role="user",
                content=question,
                sources=validated_chunks
            )
            context_manager.add_message_to_history(
                session_id=session_id,
                role="assistant",
                content=answer,
                sources=validated_chunks
            )
        
        # Prepare detailed source information
        detailed_sources = []
        for chunk in validated_chunks:
            meta = chunk.get('metadata', {})
            validation = chunk.get('validation', {})
            
            detailed_sources.append({
                "content": chunk.get('content', ''),
                "filename": meta.get('filename', 'Unknown Document'),
                "page": meta.get('page', None),
                "section": meta.get('section', None),
                "confidence": validation.get('confidence', 0.0),
                "relevance": validation.get('relevance_score', 0.0),
                "chunk_id": meta.get('chunk_id', None)
            })
        
        # Update context metadata
        context_metadata.update({
            "query": question,
            "status": status,
            "total_chunks_retrieved": len(raw_chunks),
            "chunks_after_validation": len(validated_chunks),
            "avg_confidence": sum(s['confidence'] for s in detailed_sources) / len(detailed_sources) if detailed_sources else 0,
            "avg_relevance": sum(s['relevance'] for s in detailed_sources) / len(detailed_sources) if detailed_sources else 0
        })
        
        return {
            "answer": answer,
            "context": context_str if len(validated_chunks) > 0 else "",
            "status": status,
            "sources": detailed_sources,
            "context_metadata": context_metadata
        }
        
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}", exc_info=True)
        return {
            "answer": f"I encountered an error while processing your question: {str(e)}",
            "context": "",
            "status": "error",
            "sources": [],
            "context_metadata": {"error": str(e)}
        }

def _validate_response(response: str, chunks: List[Dict], question: str) -> bool:
    """
    Validate that the response doesn't contain hallucinations
    
    This is a basic validation - more sophisticated methods could be implemented
    """
    try:
        # Check if response mentions information not in chunks
        response_lower = response.lower()
        
        # Extract key facts from chunks
        chunk_content = " ".join([chunk.get('content', '') for chunk in chunks]).lower()
        
        # Basic check: if response contains specific numbers or facts,
        # they should appear in the chunks
        import re
        
        # Extract numbers from response
        response_numbers = re.findall(r'\b\d+(?:\.\d+)?(?:%|\$|€|£)?\b', response)
        chunk_numbers = re.findall(r'\b\d+(?:\.\d+)?(?:%|\$|€|£)?\b', chunk_content)
        
        # Check if response numbers are grounded in chunks
        for num in response_numbers:
            if num not in chunk_numbers:
                logger.warning(f"Response contains ungrounded number: {num}")
                return False
        
        # Check for common hallucination phrases
        hallucination_indicators = [
            "based on my knowledge",
            "as i know",
            "generally speaking",
            "in my experience",
            "typically",
            "usually",
            "commonly"
        ]
        
        for indicator in hallucination_indicators:
            if indicator in response_lower:
                logger.warning(f"Response contains hallucination indicator: {indicator}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Response validation failed: {e}")
        return False  # Fail safe
