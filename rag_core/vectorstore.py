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
        """Initialize and return a Chroma vector collection."""
        try:
            ollama_ef = OllamaEmbeddingFunction(
                url=f"{OLLAMA_BASE_URL}/api/embeddings",
                model_name=OLLAMA_EMBEDDING_MODEL,
            )
            
            chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            
            collection = chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                embedding_function=ollama_ef,
                metadata={"hnsw:space": "cosine"},
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
        Rerank chunks by similarity, document frequency, and length. Deduplicate using Levenshtein distance.
        Returns top_k unique chunks.
        """
        # Count document frequency for each chunk content
        content_to_docs = collections.defaultdict(set)
        for chunk in chunks:
            content_to_docs[chunk['page_content']].add(chunk['metadata'].get('filename', 'unknown'))
        
        # Score each chunk
        for chunk in chunks:
            content = chunk['page_content']
            chunk['score'] = (
                chunk.get('similarity', 0) +
                0.2 * len(content_to_docs[content]) +  # document frequency boost
                0.1 * len(content) / 1000  # length boost
            )
        # Sort by score descending
        chunks = sorted(chunks, key=lambda x: x['score'], reverse=True)
        # Fuzzy deduplication
        unique_chunks = []
        for chunk in chunks:
            is_duplicate = False
            for u in unique_chunks:
                if levenshtein_distance(chunk['page_content'], u['page_content']) < fuzzy_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_chunks.append(chunk)
            if len(unique_chunks) >= top_k:
                break
        return unique_chunks

    @staticmethod
    def query_with_expanded_context(prompt: str, n_results: int, expand: int = 4, filename: str = None, domain_filter: str = None):
        """
        Enhanced query with domain filtering, hybrid search, and reranking.
        
        Args:
            prompt: User query
            n_results: Number of results to return
            expand: Context expansion factor
            filename: Optional filename filter
            domain_filter: Optional domain filter (e.g., "law", "chemistry")
        """
        # Redis cache key based on prompt and params
        cache_key = f"query:{hashlib.sha256(f'{prompt}|{n_results}|{expand}|{filename}|{domain_filter}'.encode()).hexdigest()}"
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
            logger.info(f"Query classified as domain: {detected_domain}")
        except Exception as e:
            logger.error(f"Query classification failed: {str(e)}")
            detected_domain = 'general'
        
        # Use domain filter if provided, otherwise use detected domain
        target_domain = domain_filter if domain_filter else detected_domain
        
        collection = VectorStore.get_vector_collection()
        if not collection:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]]}
        
        # Build query parameters
        query_kwargs = {
            'query_texts': [prompt],
            'n_results': n_results * 3,  # fetch more for reranking/dedup
            'include': ['documents', 'metadatas', 'distances']
        }
        
        # Apply filters
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
        
        # Build chunk dicts with similarity scores
        chunks = []
        for i, (doc, meta, distance) in enumerate(zip(docs, metadatas, distances)):
            similarity = 1.0 - distance if distance is not None else 1.0
            chunk = {
                'page_content': doc,
                'metadata': meta,
                'similarity': similarity,
                'distance': distance
            }
            chunks.append(chunk)
        
        # Apply hybrid search if we have enough chunks
        if len(chunks) > 5:
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
        
        # Add source attributions
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
        """Generate embeddings for text using Ollama."""
        try:
            import ollama
            response = ollama.embeddings(
                model=OLLAMA_EMBEDDING_MODEL,
                prompt=text,
                options={"base_url": OLLAMA_BASE_URL}
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            return [] 