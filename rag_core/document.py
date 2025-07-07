from rag_core.config import MAX_FILE_SIZE, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, logger
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import streamlit as st
import tempfile
import os

class DocumentProcessor:
    """Handles document loading, validation, and chunking."""
    @staticmethod
    def process_document(uploaded_file, file_bytes=None):
        """Process an uploaded file and return split document chunks."""
        try:
            # Check file size
            if uploaded_file.size > MAX_FILE_SIZE:
                st.error(f"File size exceeds limit of {MAX_FILE_SIZE / (1024 * 1024)} MB")
                logger.warning(f"File {uploaded_file.name} exceeds size limit")
                return []
            
            # Use provided file_bytes or read from uploaded_file
            if file_bytes is None:
                file_bytes = uploaded_file.read()
            
            # Save uploaded file to a temp file
            suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".docx"
            temp_file = tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False)
            temp_file.write(file_bytes)
            temp_file.close()
            
            # Load the file using the appropriate loader
            if suffix == ".pdf":
                loader = PyMuPDFLoader(temp_file.name)
            else:
                loader = UnstructuredWordDocumentLoader(temp_file.name)
            docs = loader.load()
            os.unlink(temp_file.name)
            
            # Split the document into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=st.session_state.get("chunk_size", DEFAULT_CHUNK_SIZE),
                chunk_overlap=st.session_state.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP),
                separators=["\n\n", "\n", ".", "!", "?", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            # Add filename and chunk_index to each chunk's metadata
            for idx, split in enumerate(splits):
                if not hasattr(split, 'metadata') or not isinstance(split.metadata, dict):
                    split.metadata = {}
                split.metadata['filename'] = uploaded_file.name
                split.metadata['chunk_index'] = idx
            logger.info(f"Processed {len(splits)} chunks from {uploaded_file.name}")
            # Debug: print metadata for first few chunks
            for i, split in enumerate(splits[:3]):
                logger.info(f"Chunk {i} metadata: {split.metadata}")
            return splits
        except Exception as e:
            logger.error(f"Error processing document {uploaded_file.name}: {str(e)}")
            st.error(f"Error processing document: {str(e)}")
            return [] 