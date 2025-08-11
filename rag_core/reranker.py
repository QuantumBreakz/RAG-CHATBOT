"""
Advanced Reranking Module for RAG Chatbot
Implements multiple reranking strategies for improved retrieval accuracy.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import logging
from datetime import datetime
import re
from collections import defaultdict

from rag_core.config import logger

try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Advanced reranking will be disabled.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. TF-IDF reranking will be disabled.")


class RerankingStrategy(Enum):
    """Available reranking strategies"""
    CROSS_ENCODER = "cross_encoder"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    TFIDF_KEYWORD = "tfidf_keyword"
    HYBRID = "hybrid"
    CONTEXT_AWARE = "context_aware"
    PERSONALIZED = "personalized"
    DIVERSITY = "diversity"
    TEMPORAL = "temporal"


@dataclass
class RerankingMetrics:
    """Metrics for reranking performance"""
    strategy: str
    processing_time: float
    input_chunks: int
    output_chunks: int
    score_range: Tuple[float, float]
    diversity_score: float
    confidence_score: float
    timestamp: datetime


@dataclass
class RerankingResult:
    """Result of reranking operation"""
    chunks: List[Dict[str, Any]]
    metrics: RerankingMetrics
    strategy_used: str
    confidence_scores: List[float]


class AdvancedReranker:
    """Advanced reranker with multiple strategies and performance tracking"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the advanced reranker.
        
        Args:
            config: Configuration dictionary with reranking settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.cross_encoder = None
        self.semantic_model = None
        self.tfidf_vectorizer = None
        self.user_preferences = defaultdict(dict)
        
        # Performance tracking
        self.performance_history = []
        self.strategy_performance = defaultdict(list)
        
        # Initialize models based on availability
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all available reranking models"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Cross-encoder for precise reranking
                cross_encoder_model = self.config.get('cross_encoder_model', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
                self.cross_encoder = CrossEncoder(cross_encoder_model)
                self.logger.info(f"Initialized cross-encoder: {cross_encoder_model}")
                
                # Semantic similarity model
                semantic_model = self.config.get('semantic_model', 'all-MiniLM-L6-v2')
                self.semantic_model = SentenceTransformer(semantic_model)
                self.logger.info(f"Initialized semantic model: {semantic_model}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize sentence-transformers models: {str(e)}")
        
        if SKLEARN_AVAILABLE:
            try:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                self.logger.info("Initialized TF-IDF vectorizer")
            except Exception as e:
                self.logger.error(f"Failed to initialize TF-IDF vectorizer: {str(e)}")
    
    def rerank(
        self, 
        query: str, 
        chunks: List[Dict[str, Any]], 
        strategy: Union[RerankingStrategy, str] = RerankingStrategy.HYBRID,
        top_k: int = 10,
        user_id: Optional[str] = None,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> RerankingResult:
        """
        Rerank chunks using the specified strategy.
        
        Args:
            query: User query
            chunks: List of chunk dictionaries
            strategy: Reranking strategy to use
            top_k: Number of top chunks to return
            user_id: User ID for personalized reranking
            context: Conversation context for context-aware reranking
            
        Returns:
            RerankingResult with reranked chunks and metrics
        """
        start_time = time.time()
        original_count = len(chunks)
        
        # Convert string strategy to enum
        if isinstance(strategy, str):
            try:
                strategy = RerankingStrategy(strategy)
            except ValueError:
                self.logger.warning(f"Unknown strategy '{strategy}', using HYBRID")
                strategy = RerankingStrategy.HYBRID
        
        # Apply reranking strategy
        if strategy == RerankingStrategy.CROSS_ENCODER:
            reranked_chunks = self._cross_encoder_rerank(query, chunks, top_k)
        elif strategy == RerankingStrategy.SEMANTIC_SIMILARITY:
            reranked_chunks = self._semantic_similarity_rerank(query, chunks, top_k)
        elif strategy == RerankingStrategy.TFIDF_KEYWORD:
            reranked_chunks = self._tfidf_keyword_rerank(query, chunks, top_k)
        elif strategy == RerankingStrategy.HYBRID:
            reranked_chunks = self._hybrid_rerank(query, chunks, top_k)
        elif strategy == RerankingStrategy.CONTEXT_AWARE:
            reranked_chunks = self._context_aware_rerank(query, chunks, top_k, context)
        elif strategy == RerankingStrategy.PERSONALIZED:
            reranked_chunks = self._personalized_rerank(query, chunks, top_k, user_id)
        elif strategy == RerankingStrategy.DIVERSITY:
            reranked_chunks = self._diversity_rerank(query, chunks, top_k)
        elif strategy == RerankingStrategy.TEMPORAL:
            reranked_chunks = self._temporal_rerank(query, chunks, top_k)
        else:
            self.logger.warning(f"Unknown strategy {strategy}, using original order")
            reranked_chunks = chunks[:top_k]
        
        # Calculate metrics
        processing_time = time.time() - start_time
        metrics = self._calculate_metrics(
            strategy.value, processing_time, original_count, len(reranked_chunks), reranked_chunks
        )
        
        # Extract confidence scores
        confidence_scores = [chunk.get('rerank_score', 0.0) for chunk in reranked_chunks]
        
        # Update performance history
        self._update_performance_history(metrics)
        
        return RerankingResult(
            chunks=reranked_chunks,
            metrics=metrics,
            strategy_used=strategy.value,
            confidence_scores=confidence_scores
        )
    
    def _cross_encoder_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank using cross-encoder model"""
        if not self.cross_encoder or not chunks:
            return chunks[:top_k]
        
        try:
            # Prepare pairs for cross-encoder
            pairs = [(query, chunk['page_content']) for chunk in chunks]
            
            # Get scores from cross-encoder
            scores = self.cross_encoder.predict(pairs)
            
            # Add scores to chunks and sort
            for chunk, score in zip(chunks, scores):
                chunk['rerank_score'] = float(score)
                chunk['rerank_strategy'] = 'cross_encoder'
            
            # Sort by rerank score (descending)
            reranked_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            return reranked_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"Cross-encoder reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _semantic_similarity_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank using semantic similarity"""
        if not self.semantic_model or not chunks:
            return chunks[:top_k]
        
        try:
            # Encode query and chunks
            query_embedding = self.semantic_model.encode([query])
            chunk_texts = [chunk['page_content'] for chunk in chunks]
            chunk_embeddings = self.semantic_model.encode(chunk_texts)
            
            # Calculate cosine similarities
            similarities = np.dot(chunk_embeddings, query_embedding.T).flatten()
            
            # Add scores to chunks and sort
            for chunk, similarity in zip(chunks, similarities):
                chunk['rerank_score'] = float(similarity)
                chunk['rerank_strategy'] = 'semantic_similarity'
            
            # Sort by similarity score (descending)
            reranked_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            return reranked_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"Semantic similarity reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _tfidf_keyword_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank using TF-IDF keyword matching"""
        if not self.tfidf_vectorizer or not chunks:
            return chunks[:top_k]
        
        try:
            # Prepare documents for TF-IDF
            documents = [chunk['page_content'] for chunk in chunks]
            documents.append(query)  # Add query as a document
            
            # Fit and transform
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            
            # Calculate similarities between query and chunks
            query_vector = tfidf_matrix[-1]  # Last document is the query
            chunk_vectors = tfidf_matrix[:-1]  # All but last are chunks
            
            similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
            
            # Add scores to chunks and sort
            for chunk, similarity in zip(chunks, similarities):
                chunk['rerank_score'] = float(similarity)
                chunk['rerank_strategy'] = 'tfidf_keyword'
            
            # Sort by similarity score (descending)
            reranked_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            return reranked_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"TF-IDF reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _hybrid_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Hybrid reranking combining multiple strategies"""
        if not chunks:
            return []
        
        try:
            # Get results from different strategies
            strategies = []
            
            if self.cross_encoder:
                cross_encoder_result = self._cross_encoder_rerank(query, chunks.copy(), len(chunks))
                strategies.append(('cross_encoder', cross_encoder_result))
            
            if self.semantic_model:
                semantic_result = self._semantic_similarity_rerank(query, chunks.copy(), len(chunks))
                strategies.append(('semantic', semantic_result))
            
            if self.tfidf_vectorizer:
                tfidf_result = self._tfidf_keyword_rerank(query, chunks.copy(), len(chunks))
                strategies.append(('tfidf', tfidf_result))
            
            if not strategies:
                return chunks[:top_k]
            
            # Combine scores using weighted average
            combined_scores = {}
            weights = {
                'cross_encoder': 0.5,
                'semantic': 0.3,
                'tfidf': 0.2
            }
            
            for strategy_name, strategy_chunks in strategies:
                weight = weights.get(strategy_name, 0.1)
                for chunk in strategy_chunks:
                    chunk_id = chunk.get('id', chunk.get('page_content', '')[:50])
                    if chunk_id not in combined_scores:
                        combined_scores[chunk_id] = {'chunk': chunk, 'scores': {}}
                    
                    combined_scores[chunk_id]['scores'][strategy_name] = chunk.get('rerank_score', 0) * weight
            
            # Calculate weighted average scores
            for chunk_id, data in combined_scores.items():
                total_score = sum(data['scores'].values())
                data['chunk']['rerank_score'] = total_score
                data['chunk']['rerank_strategy'] = 'hybrid'
                data['chunk']['strategy_scores'] = data['scores']
            
            # Sort by combined score
            reranked_chunks = sorted(
                [data['chunk'] for data in combined_scores.values()],
                key=lambda x: x.get('rerank_score', 0),
                reverse=True
            )
            
            return reranked_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"Hybrid reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _context_aware_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int, context: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Context-aware reranking considering conversation history"""
        if not context:
            return self._semantic_similarity_rerank(query, chunks, top_k)
        
        try:
            # Extract context from recent messages
            context_text = " ".join([
                msg.get('content', '') for msg in context[-5:]  # Last 5 messages
                if msg.get('role') in ['user', 'assistant']
            ])
            
            # Combine query with context
            contextualized_query = f"{query} {context_text}"
            
            # Use semantic similarity with contextualized query
            return self._semantic_similarity_rerank(contextualized_query, chunks, top_k)
            
        except Exception as e:
            self.logger.error(f"Context-aware reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _personalized_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int, user_id: Optional[str]) -> List[Dict[str, Any]]:
        """Personalized reranking based on user preferences"""
        if not user_id or user_id not in self.user_preferences:
            return self._semantic_similarity_rerank(query, chunks, top_k)
        
        try:
            user_prefs = self.user_preferences[user_id]
            
            # Apply user preferences (domain preferences, document types, etc.)
            for chunk in chunks:
                base_score = chunk.get('rerank_score', 0)
                
                # Domain preference boost
                chunk_domain = chunk.get('metadata', {}).get('domain', '')
                if chunk_domain in user_prefs.get('preferred_domains', []):
                    base_score *= 1.2
                
                # Document type preference
                chunk_type = chunk.get('metadata', {}).get('file_type', '')
                if chunk_type in user_prefs.get('preferred_file_types', []):
                    base_score *= 1.1
                
                chunk['rerank_score'] = base_score
                chunk['rerank_strategy'] = 'personalized'
            
            # Sort by personalized score
            reranked_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            return reranked_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"Personalized reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _diversity_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Diversity-aware reranking to avoid redundant results"""
        if not chunks:
            return []
        
        try:
            # First get semantic similarity scores
            semantic_chunks = self._semantic_similarity_rerank(query, chunks, len(chunks))
            
            # Apply diversity penalty
            selected_chunks = []
            used_embeddings = []
            
            for chunk in semantic_chunks:
                if len(selected_chunks) >= top_k:
                    break
                
                # Calculate diversity penalty
                diversity_penalty = 0
                if self.semantic_model and used_embeddings:
                    chunk_embedding = self.semantic_model.encode([chunk['page_content']])
                    for used_embedding in used_embeddings:
                        similarity = np.dot(chunk_embedding, used_embedding.T).flatten()[0]
                        diversity_penalty += similarity
                    
                    diversity_penalty /= len(used_embeddings)
                
                # Apply penalty
                final_score = chunk.get('rerank_score', 0) * (1 - diversity_penalty * 0.5)
                chunk['rerank_score'] = final_score
                chunk['rerank_strategy'] = 'diversity'
                
                selected_chunks.append(chunk)
                if self.semantic_model:
                    used_embeddings.append(self.semantic_model.encode([chunk['page_content']]))
            
            return selected_chunks
            
        except Exception as e:
            self.logger.error(f"Diversity reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _temporal_rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Temporal reranking considering document age and relevance"""
        if not chunks:
            return []
        
        try:
            current_time = datetime.now()
            
            for chunk in chunks:
                base_score = chunk.get('rerank_score', 0)
                
                # Extract timestamp from metadata
                timestamp = chunk.get('metadata', {}).get('timestamp')
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            doc_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            doc_time = timestamp
                        
                        # Calculate age penalty (newer documents get slight boost)
                        age_days = (current_time - doc_time).days
                        if age_days < 30:  # Recent documents
                            base_score *= 1.05
                        elif age_days > 365:  # Old documents
                            base_score *= 0.95
                        
                    except Exception:
                        pass  # Ignore timestamp parsing errors
                
                chunk['rerank_score'] = base_score
                chunk['rerank_strategy'] = 'temporal'
            
            # Sort by temporal-adjusted score
            reranked_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            return reranked_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"Temporal reranking failed: {str(e)}")
            return chunks[:top_k]
    
    def _calculate_metrics(self, strategy: str, processing_time: float, input_count: int, 
                          output_count: int, chunks: List[Dict[str, Any]]) -> RerankingMetrics:
        """Calculate reranking performance metrics"""
        scores = [chunk.get('rerank_score', 0) for chunk in chunks]
        score_range = (min(scores), max(scores)) if scores else (0, 0)
        
        # Calculate diversity score
        diversity_score = self._calculate_diversity_score(chunks)
        
        # Calculate confidence score
        confidence_score = np.mean(scores) if scores else 0
        
        return RerankingMetrics(
            strategy=strategy,
            processing_time=processing_time,
            input_chunks=input_count,
            output_chunks=output_count,
            score_range=score_range,
            diversity_score=diversity_score,
            confidence_score=confidence_score,
            timestamp=datetime.now()
        )
    
    def _calculate_diversity_score(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate diversity score based on content similarity"""
        if len(chunks) < 2:
            return 1.0
        
        try:
            if not self.semantic_model:
                return 0.5  # Default diversity score
            
            # Get embeddings for all chunks
            texts = [chunk['page_content'] for chunk in chunks]
            embeddings = self.semantic_model.encode(texts)
            
            # Calculate pairwise similarities
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    similarity = np.dot(embeddings[i], embeddings[j])
                    similarities.append(similarity)
            
            # Diversity score is inverse of average similarity
            avg_similarity = np.mean(similarities) if similarities else 0
            diversity_score = 1 - avg_similarity
            
            return max(0, min(1, diversity_score))
            
        except Exception as e:
            self.logger.error(f"Diversity score calculation failed: {str(e)}")
            return 0.5
    
    def _update_performance_history(self, metrics: RerankingMetrics):
        """Update performance tracking history"""
        self.performance_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        # Update strategy-specific performance
        self.strategy_performance[metrics.strategy].append(metrics)
        
        # Keep only last 100 entries per strategy
        if len(self.strategy_performance[metrics.strategy]) > 100:
            self.strategy_performance[metrics.strategy] = self.strategy_performance[metrics.strategy][-100:]
    
    def get_performance_stats(self, strategy: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if strategy:
            metrics_list = self.strategy_performance.get(strategy, [])
        else:
            metrics_list = self.performance_history
        
        if not metrics_list:
            return {}
        
        processing_times = [m.processing_time for m in metrics_list]
        confidence_scores = [m.confidence_score for m in metrics_list]
        diversity_scores = [m.diversity_score for m in metrics_list]
        
        return {
            'total_operations': len(metrics_list),
            'avg_processing_time': np.mean(processing_times),
            'max_processing_time': np.max(processing_times),
            'avg_confidence_score': np.mean(confidence_scores),
            'avg_diversity_score': np.mean(diversity_scores),
            'last_operation': metrics_list[-1].timestamp.isoformat() if metrics_list else None
        }
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user preferences for personalized reranking"""
        self.user_preferences[user_id].update(preferences)
        self.logger.info(f"Updated preferences for user {user_id}")
    
    def is_available(self) -> bool:
        """Check if any reranking strategy is available"""
        return any([
            self.cross_encoder is not None,
            self.semantic_model is not None,
            self.tfidf_vectorizer is not None
        ])


# Global reranker instance
_advanced_reranker_instance = None

def get_advanced_reranker(config: Dict[str, Any] = None) -> AdvancedReranker:
    """Get or create the global advanced reranker instance"""
    global _advanced_reranker_instance
    if _advanced_reranker_instance is None:
        _advanced_reranker_instance = AdvancedReranker(config)
    return _advanced_reranker_instance


# Backward compatibility
class Reranker:
    """Legacy reranker class for backward compatibility"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.advanced_reranker = get_advanced_reranker({'cross_encoder_model': model_name})
    
    def rerank_chunks(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """Legacy method for backward compatibility"""
        result = self.advanced_reranker.rerank(query, chunks, RerankingStrategy.CROSS_ENCODER, top_k)
        return result.chunks
    
    def is_available(self) -> bool:
        """Check if reranker is available"""
        return self.advanced_reranker.is_available()


def get_reranker() -> Reranker:
    """Get or create the global reranker instance (legacy)"""
    return Reranker() 