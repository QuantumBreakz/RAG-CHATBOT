"""
Cross-encoder reranking module for improved retrieval accuracy.
Uses sentence-transformers for local reranking without external dependencies.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from rag_core.config import logger
import os

try:
    from sentence_transformers import CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Reranking will be disabled.")

class Reranker:
    """Cross-encoder reranker for improving retrieval accuracy."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the reranker with a cross-encoder model.
        
        Args:
            model_name: Name of the sentence-transformers cross-encoder model
        """
        self.model = None
        self.model_name = model_name
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = CrossEncoder(model_name)
                logger.info(f"Initialized reranker with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize reranker: {str(e)}")
                self.model = None
        else:
            logger.warning("Reranker disabled - sentence-transformers not available")
    
    def rerank_chunks(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Rerank chunks using cross-encoder model.
        
        Args:
            query: User query
            chunks: List of chunk dictionaries with 'page_content' and metadata
            top_k: Number of top chunks to return
            
        Returns:
            Reranked list of chunks
        """
        if not self.model or not chunks:
            return chunks[:top_k]
        
        try:
            # Prepare pairs for cross-encoder
            pairs = [(query, chunk['page_content']) for chunk in chunks]
            
            # Get scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Add scores to chunks and sort
            for chunk, score in zip(chunks, scores):
                chunk['rerank_score'] = float(score)
            
            # Sort by rerank score (descending)
            reranked_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            logger.info(f"Reranked {len(chunks)} chunks for query: {query[:50]}...")
            return reranked_chunks[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def is_available(self) -> bool:
        """Check if reranker is available and working."""
        return self.model is not None and SENTENCE_TRANSFORMERS_AVAILABLE

# Global reranker instance
_reranker_instance = None

def get_reranker() -> Reranker:
    """Get or create the global reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    return _reranker_instance 