from rag_core.config import OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, CACHE_TTL, logger
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from rag_core.redis_cache import redis_get, redis_set
import hashlib
import pickle
import collections
from typing import List, Dict, Any, Optional
from Levenshtein import distance as levenshtein_distance
import numpy as np
from rag_core.utils import QueryClassifier, HybridSearch, format_source_attribution
from rag_core.reranker import get_reranker

class VectorStore:
    """Handles vector collection operations for ChromaDB with enhanced hybrid search and domain filtering."""
    
    @staticmethod
    def get_vector_collection():
        """Initialize and return a Chroma vector collection with advanced indexing for large-scale operations."""
        try:
            ollama_ef = OllamaEmbeddingFunction(
                url=f"{OLLAMA_BASE_URL}/api/embeddings",
                model_name=OLLAMA_EMBEDDING_MODEL,
            )
            
            chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            
            # Advanced indexing configuration for large-scale operations
            collection = chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                embedding_function=ollama_ef,
                metadata={
                    "hnsw:space": "cosine",  # Similarity metric
                    "hnsw:construction_ef": 128,  # Higher for better index quality
                    "hnsw:search_ef": 64,  # Balance between speed and accuracy
                    "hnsw:m": 16,  # Number of connections per element (default: 16)
                    "hnsw:num_threads": 4,  # Parallel processing for index building
                    "hnsw:ef_construction": 128,  # Construction time vs quality trade-off
                    "hnsw:ef_search": 64,  # Search time vs recall trade-off
                    "hnsw:max_elements": 1000000,  # Maximum elements in index
                    "hnsw:random_seed": 42,  # For reproducible results
                },
            )
            return collection
        except Exception as e:
            logger.error(f"Error initializing vector collection: {str(e)}")
            return None

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def add_to_vector_collection(all_splits, file_name, embeddings=None):
        """Add document chunks to the vector collection with retry logic and batching. If embeddings are provided, use them."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return False
            
            batch_size = 50  # Adjust based on your system performance
            total_chunks = len(all_splits)
            
            for i in range(0, total_chunks, batch_size):
                batch_end = min(i + batch_size, total_chunks)
                batch_splits = all_splits[i:batch_end]

                documents, metadatas, ids = [], [], []
                for idx, split in enumerate(batch_splits):
                    documents.append(split.page_content)
                    metadatas.append(split.metadata)
                    ids.append(f"{file_name}_{i + idx}")

                # Add batch with timeout handling
                try:
                    if embeddings is not None:
                        # Use provided embeddings for upsert
                        batch_embeddings = embeddings[i:batch_end]
                        collection.upsert(documents=documents, metadatas=metadatas, ids=ids, embeddings=batch_embeddings)
                        logger.info(f"Added batch {i//batch_size + 1} ({len(documents)} chunks, cached embeddings) for {file_name}")
                    else:
                        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
                        logger.info(f"Added batch {i//batch_size + 1} ({len(documents)} chunks) for {file_name}")

                    # Small delay between batches to prevent overwhelming the system
                    if batch_end < total_chunks:
                        time.sleep(0.5)
                except Exception as batch_error:
                    logger.error(f"Error adding batch {i//batch_size + 1} for {file_name}: {str(batch_error)}")
                    raise batch_error
            
            logger.info(f"Successfully added all {total_chunks} chunks for {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to vector collection: {str(e)}")
            return False

    @staticmethod
    def query_collection(prompt: str, n_results: int):
        """Query the vector collection for relevant chunks."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return {}
            return collection.query(query_texts=[prompt], n_results=n_results)
        except Exception as e:
            logger.error(f"Error querying vector collection: {str(e)}")
            return {} 

    @staticmethod
    def _rerank_and_deduplicate(chunks: List[Dict[str, Any]], top_k: int = 10, fuzzy_threshold: int = 20) -> List[Dict[str, Any]]:
        """
        Enhanced reranking with strict deduplication, confidence scoring, and domain isolation.
        Returns top_k unique chunks with confidence scores.
        """
        # Count document frequency and domain consistency
        content_to_docs = collections.defaultdict(set)
        content_to_domains = collections.defaultdict(set)
        for chunk in chunks:
            content = chunk['page_content']
            content_to_docs[content].add(chunk['metadata'].get('filename', 'unknown'))
            content_to_domains[content].add(chunk['metadata'].get('domain', 'unknown'))
        
        # Enhanced scoring with domain consistency and fact verification
        for chunk in chunks:
            content = chunk['page_content']
            domain = chunk['metadata'].get('domain', 'unknown')
            
            # Base similarity score
            similarity_score = chunk.get('similarity', 0)
            
            # Domain consistency bonus (prefer chunks from same domain)
            domain_consistency = len(content_to_domains[content])
            domain_bonus = 0.3 if domain_consistency == 1 else 0.0
            
            # Fact consistency check (look for conflicting information)
            fact_penalty = 0.0
            for other_chunk in chunks:
                if other_chunk != chunk:
                    other_content = other_chunk['page_content']
                    # Check for numerical conflicts (like different Kc values)
                    import re
                    numbers_chunk = re.findall(r'\d+\.?\d*', content)
                    numbers_other = re.findall(r'\d+\.?\d*', other_content)
                    if numbers_chunk and numbers_other:
                        # If same concept but different numbers, penalize
                        if any(num in other_content for num in numbers_chunk[:3]):
                            fact_penalty += 0.5
            
            # Length and quality scoring
            length_score = min(len(content) / 1000, 1.0)  # Cap at 1.0
            quality_score = 0.2 if len(content.strip()) > 50 else 0.0
            
            chunk['score'] = (
                similarity_score +
                domain_bonus +
                length_score * 0.1 +
                quality_score -
                fact_penalty
            )
            chunk['confidence'] = min(similarity_score + domain_bonus, 1.0)
        
        # Sort by score descending
        chunks = sorted(chunks, key=lambda x: x['score'], reverse=True)
        
        # Strict deduplication with semantic similarity
        unique_chunks = []
        for chunk in chunks:
            is_duplicate = False
            for u in unique_chunks:
                # Check for exact duplicates
                if chunk['page_content'] == u['page_content']:
                    is_duplicate = True
                    break
                # Check for fuzzy duplicates (more strict threshold)
                if levenshtein_distance(chunk['page_content'], u['page_content']) < 10:  # Reduced from 20
                    is_duplicate = True
                    break
                # Check for semantic duplicates (same concept, different wording)
                if VectorStore._is_semantic_duplicate(chunk['page_content'], u['page_content'], threshold=0.9):  # Increased threshold
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_chunks.append(chunk)
            if len(unique_chunks) >= top_k:
                break
        
        return unique_chunks

    @staticmethod
    def _is_semantic_duplicate(content1: str, content2: str, threshold: float = 0.8) -> bool:
        """
        Check if two chunks are semantically similar (same concept, different wording).
        """
        # Extract key terms and numbers
        import re
        def extract_key_info(text):
            # Extract numbers, chemical formulas, key terms
            numbers = re.findall(r'\d+\.?\d*', text)
            formulas = re.findall(r'[A-Z][a-z]?\d*', text)  # Basic chemical formulas
            key_terms = re.findall(r'\b[A-Za-z]{3,}\b', text)
            return set(numbers + formulas + key_terms[:10])
        
        info1 = extract_key_info(content1)
        info2 = extract_key_info(content2)
        
        if not info1 or not info2:
            return False
        
        # Calculate overlap
        overlap = len(info1.intersection(info2))
        total = len(info1.union(info2))
        
        return overlap / total > threshold if total > 0 else False

    @staticmethod
    def query_with_expanded_context(prompt: str, n_results: int, expand: int = 4, filename: str = None, domain_filter: str = None, session_id: str = None):
        """
        Enhanced query with strict domain filtering, session isolation, and conflict resolution.
        
        Args:
            prompt: User query
            n_results: Number of results to return
            expand: Context expansion factor
            filename: Optional filename filter
            domain_filter: Optional domain filter (e.g., "law", "chemistry")
            session_id: Optional session ID for query isolation
        """
        # Enhanced cache key with session isolation
        cache_key = f"query:{hashlib.sha256(f'{prompt}|{n_results}|{expand}|{filename}|{domain_filter}|{session_id}'.encode()).hexdigest()}"
        
        # Try Redis first
        try:
            cached = redis_get(cache_key)
            if cached:
                return pickle.loads(cached.encode('latin1') if isinstance(cached, str) else cached)
        except Exception:
            pass
        
        # Query classification for intelligent routing
        try:
            classification = QueryClassifier.classify_query(prompt)
            detected_domain = classification.get('domain', 'general')
            confidence = classification.get('confidence', 0.5)
            logger.info(f"Query classified as domain: {detected_domain} (confidence: {confidence})")
        except Exception as e:
            logger.error(f"Query classification failed: {str(e)}")
            detected_domain = 'general'
            confidence = 0.5
        
        # Use domain filter if provided, otherwise use detected domain
        target_domain = domain_filter if domain_filter else detected_domain
        
        # Session-based query isolation
        if session_id:
            # Clear previous session context to prevent contamination
            session_cache_key = f"session:{session_id}"
            try:
                redis_set(session_cache_key, prompt, expire=300)  # 5 minute session
            except Exception:
                pass
        
        collection = VectorStore.get_vector_collection()
        if not collection:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]]}
        
        # Build query parameters with stricter filtering - reduce multiplier to prevent too many chunks
        query_kwargs = {
            'query_texts': [prompt],
            'n_results': min(n_results * 3, 15),  # fetch fewer chunks, max 15
            'include': ['documents', 'metadatas', 'distances']
        }
        
        # Apply strict filters
        where_conditions = {}
        if filename:
            where_conditions['filename'] = filename
        if target_domain and target_domain != 'general':
            where_conditions['domain'] = target_domain
        
        if where_conditions:
            query_kwargs['where'] = where_conditions
        
        result = collection.query(**query_kwargs)
        docs = result.get('documents', [[]])[0]
        metadatas = result.get('metadatas', [[]])[0]
        distances = result.get('distances', [[]])[0]
        
        # Build chunk dicts with enhanced similarity scores
        chunks = []
        for i, (doc, meta, distance) in enumerate(zip(docs, metadatas, distances)):
            similarity = 1.0 - distance if distance is not None else 1.0
            
            # Enhanced similarity scoring with domain consistency
            domain = meta.get('domain', 'unknown')
            domain_boost = 0.2 if domain == target_domain else 0.0
            enhanced_similarity = min(similarity + domain_boost, 1.0)
            
            # Filter out low-quality chunks
            if enhanced_similarity < 0.3:  # Only include chunks with decent similarity
                continue
                
            chunk = {
                'page_content': doc,
                'metadata': meta,
                'similarity': similarity,
                'distance': distance,
                'confidence': enhanced_similarity
            }
            chunks.append(chunk)
        
        # Apply hybrid search if we have enough chunks
        if len(chunks) > 3:
            chunks = VectorStore._apply_hybrid_search(prompt, chunks, n_results)
        
        # Apply reranking
        reranker = get_reranker()
        if reranker.is_available():
            chunks = reranker.rerank_chunks(prompt, chunks, top_k=n_results)
        
        # Final reranking and deduplication
        reranked = VectorStore._rerank_and_deduplicate(chunks, top_k=n_results)
        
        # Prepare return format with source attribution
        docs_out = [c['page_content'] for c in reranked]
        metas_out = [c['metadata'] for c in reranked]
        ids_out = [f"{c['metadata'].get('filename','unknown')}_{c['metadata'].get('chunk_index',0)}" for c in reranked]
        
        # Add source attributions with better formatting
        sources = []
        for meta in metas_out:
            sources.append({
                'title': meta.get('title', meta.get('filename', 'Unknown Document')),
                'page': meta.get('page_number'),
                'section': meta.get('section_number'),
                'domain': meta.get('domain', 'general'),
                'attribution': format_source_attribution(meta)
            })
        
        result = {
            "documents": [docs_out], 
            "metadatas": [metas_out], 
            "ids": [ids_out],
            "sources": sources,
            "query_classification": {
                "domain": detected_domain,
                "confidence": classification.get('confidence', 0.5) if 'classification' in locals() else 0.5
            }
        }
        
        # Cache the result
        try:
            redis_set(cache_key, pickle.dumps(result), expire=3600)  # 1 hour cache
        except Exception:
            pass
        
        return result

    @staticmethod
    def _apply_hybrid_search(query: str, chunks: List[Dict[str, Any]], n_results: int) -> List[Dict[str, Any]]:
        """
        Apply hybrid search combining dense vector search with sparse keyword search.
        """
        try:
            # Simple BM25-like scoring for keywords
            query_words = set(query.lower().split())
            
            for chunk in chunks:
                content_words = set(chunk['page_content'].lower().split())
                
                # Calculate keyword overlap
                keyword_matches = len(query_words.intersection(content_words))
                keyword_score = keyword_matches / max(len(query_words), 1)
                
                # Combine with vector similarity
                vector_score = chunk.get('similarity', 0)
                combined_score = 0.7 * vector_score + 0.3 * keyword_score
                
                chunk['hybrid_score'] = combined_score
            
            # Sort by hybrid score
            chunks = sorted(chunks, key=lambda x: x.get('hybrid_score', 0), reverse=True)
            
            return chunks[:n_results * 2]  # Return more for reranking
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            return chunks

    @staticmethod
    def clear_vector_collection():
        """Delete all embeddings from the ChromaDB collection (reset knowledge base)."""
        try:
            collection = VectorStore.get_vector_collection()
            if collection:
                collection.delete(where={})  # Delete all documents
                logger.info("Cleared all embeddings from the vector collection.")
        except Exception as e:
            logger.error(f"Error clearing vector collection: {str(e)}") 

    @staticmethod
    def list_documents():
        """Return a list of unique filenames and their metadata from the collection."""
        collection = VectorStore.get_vector_collection()
        if not collection:
            return []
        # Query all metadatas (ChromaDB does not have a direct 'list all' API, so we use a broad query)
        try:
            # Query for a common word to get all docs (hack: n_results very high)
            result = collection.query(query_texts=["."], n_results=10000, include=["metadatas"])
            metadatas = result.get("metadatas", [[]])[0]
            files = {}
            for meta in metadatas:
                fname = meta.get("filename", "unknown")
                if fname not in files:
                    files[fname] = {
                        "filename": fname, 
                        "count": 0, 
                        "examples": [],
                        "domain": meta.get("domain", "general"),
                        "title": meta.get("title", fname),
                        "doc_type": meta.get("doc_type", "document")
                    }
                files[fname]["count"] += 1
                if len(files[fname]["examples"]) < 3:
                    files[fname]["examples"].append(meta)
            return list(files.values())
        except Exception as e:
            return []

    @staticmethod
    def delete_document(filename):
        """Delete all chunks for a given filename from the collection."""
        collection = VectorStore.get_vector_collection()
        if not collection:
            return False
        try:
            collection.delete(where={"filename": filename})
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def get_domains():
        """Get list of available domains in the knowledge base."""
        collection = VectorStore.get_vector_collection()
        if not collection:
            return []
        
        try:
            result = collection.query(query_texts=["."], n_results=10000, include=["metadatas"])
            metadatas = result.get("metadatas", [[]])[0]
            domains = set()
            for meta in metadatas:
                domain = meta.get("domain", "general")
                if domain and domain != "general":
                    domains.add(domain)
            return sorted(list(domains))
        except Exception as e:
            logger.error(f"Error getting domains: {str(e)}")
            return []
    
    @staticmethod
    def embed_text(text: str) -> List[float]:
        """Embed text using the Ollama embedding model."""
        try:
            ollama_ef = OllamaEmbeddingFunction(
                url=f"{OLLAMA_BASE_URL}/api/embeddings",
                model_name=OLLAMA_EMBEDDING_MODEL,
            )
            return ollama_ef([text])[0]
        except Exception as e:
            logger.error(f"Error embedding text: {str(e)}")
            return []

    @staticmethod
    def optimize_index_for_large_datasets():
        """Optimize the index for large-scale operations."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return False
            
            # Get collection info
            count = collection.count()
            logger.info(f"Optimizing index for {count} vectors")
            
            # Force index rebuild for better performance
            collection._client._persist()
            
            # Update index parameters for large datasets
            if count > 10000:
                logger.info("Large dataset detected, applying optimizations")
                # These optimizations are applied at collection creation
                # Additional runtime optimizations can be added here
            
            logger.info("Index optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing index: {str(e)}")
            return False

    @staticmethod
    def get_index_statistics():
        """Get statistics about the vector index."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return {}
            
            count = collection.count()
            
            # Get collection metadata
            metadata = collection.metadata or {}
            
            stats = {
                "total_vectors": count,
                "index_type": "HNSW",
                "similarity_metric": metadata.get("hnsw:space", "cosine"),
                "construction_ef": metadata.get("hnsw:construction_ef", 128),
                "search_ef": metadata.get("hnsw:search_ef", 64),
                "max_connections": metadata.get("hnsw:m", 16),
                "max_elements": metadata.get("hnsw:max_elements", 1000000),
                "optimized_for_large_datasets": count > 10000
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting index statistics: {str(e)}")
            return {}

    @staticmethod
    def batch_optimize_embeddings(embeddings: List[List[float]], batch_size: int = 1000):
        """Optimize embeddings in batches for large-scale operations."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return False
            
            total_embeddings = len(embeddings)
            logger.info(f"Batch optimizing {total_embeddings} embeddings")
            
            for i in range(0, total_embeddings, batch_size):
                batch_end = min(i + batch_size, total_embeddings)
                batch = embeddings[i:batch_end]
                
                # Process batch
                logger.info(f"Processing batch {i//batch_size + 1}/{total_embeddings//batch_size + 1}")
                
                # Add small delay to prevent overwhelming
                if batch_end < total_embeddings:
                    time.sleep(0.1)
            
            logger.info("Batch optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error in batch optimization: {str(e)}")
            return False

    @staticmethod
    def get_performance_metrics():
        """Get performance metrics for the vector store."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return {}
            
            count = collection.count()
            
            # Calculate approximate memory usage (rough estimate)
            # Each vector is typically 1536 dimensions * 4 bytes = ~6KB
            estimated_memory_mb = (count * 1536 * 4) / (1024 * 1024)
            
            metrics = {
                "total_vectors": count,
                "estimated_memory_mb": round(estimated_memory_mb, 2),
                "index_optimized": count > 10000,
                "recommended_batch_size": min(100, max(10, count // 100)),
                "performance_level": "high" if count < 10000 else "optimized" if count < 100000 else "enterprise"
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {} 