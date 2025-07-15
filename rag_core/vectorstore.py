from rag_core.config import OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, CACHE_TTL, logger
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from rag_core.redis_cache import redis_get, redis_set
import hashlib
import pickle

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
            'n_results': n_results,
            'include': ['documents', 'metadatas']
        }
        if filename:
            query_kwargs['where'] = {"filename": filename}
        result = collection.query(**query_kwargs)
        docs = result.get('documents', [[]])[0]
        metadatas = result.get('metadatas', [[]])[0]
        
        # Generate IDs based on metadata since we can't get them from the query
        ids = []
        for i, meta in enumerate(metadatas):
            filename_meta = meta.get('filename', 'unknown')
            chunk_idx = meta.get('chunk_index') or meta.get('row_index', i)
            ids.append(f"{filename_meta}_{chunk_idx}")

        # Expand context by including neighboring chunks
        expanded_docs, expanded_metas, expanded_ids = [], [], []
        for idx, meta in enumerate(metadatas):
            chunk_idx = meta.get('chunk_index') or meta.get('row_index')
            if chunk_idx is not None and filename:
                # Try to get neighbors
                for offset in range(-expand, expand+1):
                    neighbor_idx = chunk_idx + offset
                    if neighbor_idx < 0:
                        continue
                    # Find the neighbor in the collection (brute force, could be optimized)
                    for m, d, i in zip(metadatas, docs, ids):
                        nidx = m.get('chunk_index') or m.get('row_index')
                        if nidx == neighbor_idx:
                            if i not in expanded_ids:
                                expanded_docs.append(d)
                                expanded_metas.append(m)
                                expanded_ids.append(i)
        # Always include the last chunk(s) for 'current/latest' queries
        keywords = ["current", "latest", "now", "today", "conclusion"]
        if any(k in prompt.lower() for k in keywords):
            # Find the last chunk(s) for the file
            last_chunks = []
            max_idx = -1
            for m in metadatas:
                idx = m.get('chunk_index') or m.get('row_index')
                if idx is not None and idx > max_idx:
                    max_idx = idx
            for m, d, i in zip(metadatas, docs, ids):
                idx = m.get('chunk_index') or m.get('row_index')
                if idx is not None and idx >= max_idx - 1:  # last 2 chunks
                    if i not in expanded_ids:
                        expanded_docs.append(d)
                        expanded_metas.append(m)
                        expanded_ids.append(i)
        # Heuristic: boost inclusion of chunks with certain keywords
        boost_keywords = ["however", "in conclusion", "update", "but ", "summary"]
        for m, d, i in zip(metadatas, docs, ids):
            content = d.lower() if isinstance(d, str) else str(d).lower()
            if any(bk in content for bk in boost_keywords):
                if i not in expanded_ids:
                    expanded_docs.append(d)
                    expanded_metas.append(m)
                    expanded_ids.append(i)
        # If nothing expanded, fall back to original
        if not expanded_docs:
            expanded_docs, expanded_metas, expanded_ids = docs, metadatas, ids
        out = {
            "documents": [expanded_docs],
            "metadatas": [expanded_metas],
            "ids": [expanded_ids]
        }
        # Cache the result in Redis for 10 minutes
        try:
            redis_set(cache_key, pickle.dumps(out), ex=600)
        except Exception:
            pass
        return out

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