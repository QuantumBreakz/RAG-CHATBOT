"""
Simplified RAG System - Clean Implementation

This module provides a clean, working RAG system that focuses on:
1. Accurate document retrieval
2. Anti-hallucination measures
3. Simple, reliable API
4. Clean UI integration

Removes all the complex, overlapping systems and focuses on what works.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import requests
import time

logger = logging.getLogger(__name__)

@dataclass
class SimpleRAGResponse:
    """Simple response structure"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    status: str
    metadata: Dict[str, Any]

class SimpleVectorStore:
    """Simplified vector store with basic operations"""
    
    def __init__(self, collection_name: str = "simple_rag"):
        self.collection_name = collection_name
        self.base_url = "http://localhost:8001"  # ChromaDB default port
    
    def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Simple query with validation"""
        try:
            # Use ChromaDB REST API directly for simplicity
            response = requests.post(
                f"{self.base_url}/api/v1/collections/{self.collection_name}/query",
                json={
                    "query_texts": [query_text],
                    "n_results": n_results,
                    "include": ["documents", "metadatas", "distances"]
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"ChromaDB query failed: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            documents = data.get("documents", [[]])[0]
            metadatas = data.get("metadatas", [[]])[0]
            distances = data.get("distances", [[]])[0]
            
            for i, doc in enumerate(documents):
                # Convert distance to confidence (lower distance = higher confidence)
                confidence = max(0.0, 1.0 - (distances[i] if i < len(distances) else 1.0))
                
                # Only include high-confidence results
                if confidence > 0.6:  # High threshold
                    results.append({
                        "content": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "confidence": confidence,
                        "distance": distances[i] if i < len(distances) else 1.0
                    })
            
            # Sort by confidence
            results.sort(key=lambda x: x["confidence"], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Vector query failed: {e}")
            return []
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add document to vector store"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/collections/{self.collection_name}/add",
                json={
                    "documents": [content],
                    "metadatas": [metadata],
                    "ids": [f"doc_{int(time.time() * 1000)}_{hash(content) % 10000}"]
                },
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

class SimpleLLM:
    """Simplified LLM handler with strict prompting"""
    
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer with strict anti-hallucination prompt"""
        
        strict_prompt = f"""You are a helpful assistant that ONLY answers based on the provided context.

CRITICAL RULES:
- ONLY use information from the context below
- If the answer is not in the context, say "I cannot find this information in the provided documents"
- Do not add external knowledge or assumptions
- Be concise and accurate

CONTEXT:
{context}

QUESTION: {query}

ANSWER (based only on the context above):"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": strict_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Error: No response generated")
            else:
                return f"Error: LLM request failed with status {response.status_code}"
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error generating response: {str(e)}"

class SimpleRAGSystem:
    """Clean, simple RAG system implementation"""
    
    def __init__(self):
        self.vector_store = SimpleVectorStore()
        self.llm = SimpleLLM()
        self.min_confidence = 0.6
        self.max_context_length = 2000
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """Basic query validation"""
        if not query or len(query.strip()) < 3:
            return False, "Query too short"
        
        if len(query) > 500:
            return False, "Query too long"
        
        return True, "Valid"
    
    def validate_chunks(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate retrieved chunks for relevance"""
        if not chunks:
            return []
        
        query_words = set(query.lower().split())
        validated = []
        
        for chunk in chunks:
            content = chunk.get("content", "").lower()
            confidence = chunk.get("confidence", 0.0)
            
            # Check confidence threshold
            if confidence < self.min_confidence:
                continue
            
            # Check for keyword overlap
            content_words = set(content.split())
            overlap = len(query_words.intersection(content_words))
            relevance = overlap / len(query_words) if query_words else 0
            
            # Only include relevant chunks
            if relevance > 0.2:  # At least 20% keyword overlap
                chunk["relevance"] = relevance
                validated.append(chunk)
        
        # Sort by combined confidence and relevance
        validated.sort(
            key=lambda x: x["confidence"] * 0.7 + x.get("relevance", 0) * 0.3,
            reverse=True
        )
        
        return validated[:3]  # Max 3 chunks
    
    def create_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Create clean context from validated chunks"""
        if not chunks:
            return "No relevant information found."
        
        context_parts = ["=== RELEVANT INFORMATION ==="]
        current_length = 0
        
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown Document")
            
            if current_length + len(content) > self.max_context_length:
                break
            
            context_parts.append(f"\nSource {i+1} ({filename}):")
            context_parts.append(content)
            context_parts.append("---")
            
            current_length += len(content)
        
        context_parts.append("=== END OF INFORMATION ===")
        return "\n".join(context_parts)
    
    def process_query(self, query: str) -> SimpleRAGResponse:
        """Main query processing function"""
        start_time = time.time()
        
        # Validate query
        is_valid, validation_msg = self.validate_query(query)
        if not is_valid:
            return SimpleRAGResponse(
                answer=f"Invalid query: {validation_msg}",
                sources=[],
                confidence=0.0,
                status="invalid_query",
                metadata={"error": validation_msg}
            )
        
        logger.info(f"Processing query: {query[:100]}")
        
        # Retrieve chunks
        raw_chunks = self.vector_store.query(query, n_results=5)
        
        if not raw_chunks:
            return SimpleRAGResponse(
                answer="I cannot find any relevant information in the knowledge base for your question.",
                sources=[],
                confidence=0.0,
                status="no_results",
                metadata={"total_chunks": 0}
            )
        
        # Validate chunks
        validated_chunks = self.validate_chunks(query, raw_chunks)
        
        if not validated_chunks:
            return SimpleRAGResponse(
                answer="I found some documents but they don't seem directly relevant to your question. Please try rephrasing your query.",
                sources=[],
                confidence=0.0,
                status="low_relevance",
                metadata={"total_chunks": len(raw_chunks), "validated_chunks": 0}
            )
        
        # Create context
        context = self.create_context(validated_chunks)
        
        # Generate answer
        answer = self.llm.generate_answer(query, context)
        
        # Calculate overall confidence
        avg_confidence = sum(chunk["confidence"] for chunk in validated_chunks) / len(validated_chunks)
        
        # Prepare sources
        sources = []
        for chunk in validated_chunks:
            metadata = chunk.get("metadata", {})
            sources.append({
                "filename": metadata.get("filename", "Unknown"),
                "content_preview": chunk.get("content", "")[:200] + "...",
                "confidence": chunk["confidence"],
                "relevance": chunk.get("relevance", 0.0)
            })
        
        processing_time = time.time() - start_time
        
        return SimpleRAGResponse(
            answer=answer,
            sources=sources,
            confidence=avg_confidence,
            status="success",
            metadata={
                "total_chunks": len(raw_chunks),
                "validated_chunks": len(validated_chunks),
                "processing_time": processing_time,
                "context_length": len(context)
            }
        )

# Global instance
simple_rag = SimpleRAGSystem()
