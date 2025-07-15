from rag_core.config import OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, CACHE_TTL, logger
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from rag_core.redis_cache import redis_get, redis_set
import hashlib
import pickle
import collections
from typing import List, Dict, Any
from Levenshtein import distance as levenshtein_distance

class VectorStore:
    """Handles vector collection operations for ChromaDB."""
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
    def add_to_vector_collection(all_splits, file_name):
        """Add document chunks to the vector collection with retry logic and batching."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return False
            
            # Process in smaller batches to avoid timeouts
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
    def query_with_expanded_context(prompt: str, n_results: int, expand: int = 4, filename: str = None):
        # Redis cache key based on prompt and params
        cache_key = f"query:{hashlib.sha256(f'{prompt}|{n_results}|{expand}|{filename}'.encode()).hexdigest()}"
        # Try Redis first
        try:
            cached = redis_get(cache_key)
            if cached:
                return pickle.loads(cached.encode('latin1') if isinstance(cached, str) else cached)
        except Exception:
            pass
        collection = VectorStore.get_vector_collection()
        if not collection:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]]}
        query_kwargs = {
            'query_texts': [prompt],
            'n_results': n_results * 3,  # fetch more for reranking/dedup
            'include': ['documents', 'metadatas']
        }
        if filename:
            query_kwargs['where'] = {"filename": filename}
        result = collection.query(**query_kwargs)
        docs = result.get('documents', [[]])[0]
        metadatas = result.get('metadatas', [[]])[0]
        # Build chunk dicts with similarity (if available)
        chunks = []
        for i, (doc, meta) in enumerate(zip(docs, metadatas)):
            chunk = {
                'page_content': doc,
                'metadata': meta,
                'similarity': meta.get('similarity', 1.0) if isinstance(meta, dict) else 1.0
            }
            chunks.append(chunk)
        # Rerank and deduplicate
        reranked = VectorStore._rerank_and_deduplicate(chunks, top_k=n_results)
        # Prepare return format
        docs_out = [c['page_content'] for c in reranked]
        metas_out = [c['metadata'] for c in reranked]
        ids_out = [f"{c['metadata'].get('filename','unknown')}_{c['metadata'].get('chunk_index',0)}" for c in reranked]
        return {"documents": [docs_out], "metadatas": [metas_out], "ids": [ids_out]}

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
                    files[fname] = {"filename": fname, "count": 0, "examples": []}
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