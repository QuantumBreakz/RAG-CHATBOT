from rag_core.config import OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, CACHE_TTL, logger
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
import streamlit as st
import time
from tenacity import retry, stop_after_attempt, wait_exponential

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
            return chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                embedding_function=ollama_ef,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            logger.error(f"Error initializing vector collection: {str(e)}")
            st.error(f"Failed to initialize vector collection: {str(e)}")
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
            st.error(f"Error adding to vector collection: {str(e)}")
            return False

    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def query_collection(prompt: str, n_results: int):
        """Query the vector collection for relevant chunks."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return {}
            return collection.query(query_texts=[prompt], n_results=n_results)
        except Exception as e:
            logger.error(f"Error querying vector collection: {str(e)}")
            st.error(f"Error querying vector collection: {str(e)}")
            return {} 

    @staticmethod
    def query_with_expanded_context(prompt: str, n_results: int, expand: int = 2, filename: str = None):
        """Query the vector collection and return just the top n_results chunks (no expansion). Optionally restrict to a specific filename."""
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
        # Just return the top n_results as context
        return {
            "documents": result.get('documents', [[]]),
            "metadatas": result.get('metadatas', [[]]),
            "ids": result.get('ids', [[]])
        } 

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
            st.error(f"Failed to clear knowledge base: {str(e)}") 