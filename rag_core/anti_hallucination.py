"""
Anti-Hallucination Module for RAG System

This module provides strict content validation and anti-hallucination measures
to prevent the LLM from generating information not present in the source documents.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetrievalQuality:
    """Quality metrics for retrieved chunks"""
    relevance_score: float
    confidence: float
    keyword_overlap: float
    semantic_coherence: float
    source_reliability: float

class AntiHallucinationValidator:
    """Validates retrieved context to prevent hallucinations"""
    
    def __init__(self, min_confidence: float = 0.7, min_relevance: float = 0.4):
        self.min_confidence = min_confidence
        self.min_relevance = min_relevance
    
    def validate_chunks(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate retrieved chunks for relevance and quality
        
        Args:
            query: User query
            chunks: Retrieved chunks with metadata
            
        Returns:
            Filtered list of high-quality, relevant chunks
        """
        if not chunks:
            return []
        
        validated_chunks = []
        query_terms = self._extract_key_terms(query.lower())
        
        for chunk in chunks:
            content = chunk.get('content', '')
            confidence = chunk.get('source', {}).get('confidence', 0.5)
            
            # Skip low-confidence chunks immediately
            if confidence < self.min_confidence:
                logger.debug(f"Skipping chunk due to low confidence: {confidence}")
                continue
            
            # Calculate relevance score
            relevance = self._calculate_relevance(query_terms, content.lower())
            
            if relevance < self.min_relevance:
                logger.debug(f"Skipping chunk due to low relevance: {relevance}")
                continue
            
            # Additional quality checks
            if not self._basic_quality_check(content):
                logger.debug("Skipping chunk due to failed quality check")
                continue
            
            # Add quality metadata
            chunk['validation'] = {
                'relevance_score': relevance,
                'confidence': confidence,
                'quality_passed': True
            }
            
            validated_chunks.append(chunk)
        
        # Sort by relevance and confidence
        validated_chunks.sort(
            key=lambda x: (
                x['validation']['relevance_score'] * 0.6 + 
                x['validation']['confidence'] * 0.4
            ), 
            reverse=True
        )
        
        logger.info(f"Validated {len(validated_chunks)}/{len(chunks)} chunks")
        return validated_chunks
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from query"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'}
        
        # Extract words, numbers, and phrases
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return [word for word in words if word not in stop_words]
    
    def _calculate_relevance(self, query_terms: List[str], content: str) -> float:
        """Calculate relevance score between query and content"""
        if not query_terms:
            return 0.0
        
        # Count term matches
        matches = sum(1 for term in query_terms if term in content)
        basic_relevance = matches / len(query_terms)
        
        # Boost for exact phrase matches
        query_phrases = self._extract_phrases(' '.join(query_terms))
        phrase_matches = sum(1 for phrase in query_phrases if phrase in content)
        phrase_boost = phrase_matches * 0.3
        
        # Penalize very short content
        length_penalty = 0.0 if len(content) > 100 else 0.2
        
        return min(1.0, basic_relevance + phrase_boost - length_penalty)
    
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases from text"""
        # Simple phrase extraction (2-3 word combinations)
        words = text.split()
        phrases = []
        
        for i in range(len(words) - 1):
            phrases.append(' '.join(words[i:i+2]))
            if i < len(words) - 2:
                phrases.append(' '.join(words[i:i+3]))
        
        return phrases
    
    def _basic_quality_check(self, content: str) -> bool:
        """Basic quality checks for content"""
        if not content or len(content.strip()) < 20:
            return False
        
        # Check for garbled text (too many special characters)
        special_char_ratio = len(re.findall(r'[^\w\s]', content)) / len(content)
        if special_char_ratio > 0.3:
            return False
        
        # Check for reasonable word structure
        words = content.split()
        if len(words) < 5:
            return False
        
        return True

class ContextValidator:
    """Validates the final context before sending to LLM"""
    
    def __init__(self):
        self.validator = AntiHallucinationValidator()
    
    def create_safe_context(self, query: str, chunks: List[Dict[str, Any]], max_tokens: int = 2000) -> Tuple[str, Dict[str, Any]]:
        """
        Create a safe, validated context for the LLM
        
        Args:
            query: User query
            chunks: Retrieved chunks
            max_tokens: Maximum context tokens
            
        Returns:
            Tuple of (context_string, metadata)
        """
        # Validate chunks first
        validated_chunks = self.validator.validate_chunks(query, chunks)
        
        if not validated_chunks:
            return self._create_no_context_response(query)
        
        # Build context with clear boundaries
        context_parts = []
        total_length = 0
        used_sources = []
        
        context_parts.append("=== DOCUMENT CONTEXT ===")
        context_parts.append(f"Query: {query}")
        context_parts.append("=== RELEVANT INFORMATION ===")
        
        for i, chunk in enumerate(validated_chunks):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            filename = metadata.get('filename', 'Unknown Document')
            
            # Estimate token usage (rough: 4 chars per token)
            estimated_tokens = len(content) / 4
            
            if total_length + estimated_tokens > max_tokens:
                break
            
            context_parts.append(f"\n--- Source {i+1}: {filename} ---")
            context_parts.append(content)
            context_parts.append("--- End Source ---\n")
            
            used_sources.append({
                'filename': filename,
                'relevance': chunk['validation']['relevance_score'],
                'confidence': chunk['validation']['confidence']
            })
            
            total_length += estimated_tokens
        
        context_parts.append("=== END DOCUMENT CONTEXT ===")
        context_parts.append("\nIMPORTANT: Only use information from the above context. If the answer is not in the context, state this clearly.")
        
        context_string = '\n'.join(context_parts)
        
        metadata = {
            'sources_used': len(used_sources),
            'total_sources': len(chunks),
            'validation_passed': True,
            'sources': used_sources,
            'context_length': len(context_string)
        }
        
        return context_string, metadata
    
    def _create_no_context_response(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Create response when no valid context is found"""
        context = f"""=== NO RELEVANT CONTEXT FOUND ===
Query: {query}

No relevant information was found in the document database for this query.
Respond with: "I cannot find relevant information about '{query}' in the available documents."
"""
        
        metadata = {
            'sources_used': 0,
            'total_sources': 0,
            'validation_passed': False,
            'sources': [],
            'no_context_reason': 'No chunks passed validation'
        }
        
        return context, metadata

# Global instance
context_validator = ContextValidator()
