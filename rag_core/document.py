from rag_core.config import MAX_FILE_SIZE, logger
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tempfile
import os
import pandas as pd
import io
# --- Add OCR import ---
from rag_core.ocr import extract_text_from_pdf, is_scanned_pdf

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 400

class DocumentProcessor:
    """Handles document loading, validation, and chunking. Now supports OCR for scanned PDFs."""
    @staticmethod
    def process_document(uploaded_file, file_bytes=None, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
        """Process an uploaded file and return split document chunks. Raises exceptions for errors. Supports OCR for scanned PDFs."""
        # Check file size
        if uploaded_file.size > MAX_FILE_SIZE:
            logger.warning(f"File {uploaded_file.name} exceeds size limit")
            raise ValueError(f"File size exceeds limit of {MAX_FILE_SIZE / (1024 * 1024)} MB")
        
        # Use provided file_bytes or read from uploaded_file
        if file_bytes is None:
            file_bytes = uploaded_file.read()
        
        # Determine file type (handle both .name and .filename for compatibility)
        file_basename = getattr(uploaded_file, 'name', None) or getattr(uploaded_file, 'filename', None)
        if not file_basename:
            raise ValueError("Uploaded file object must have a .name or .filename attribute.")
        suffix = os.path.splitext(file_basename)[1].lower()

        if suffix == ".pdf":
            temp_file = tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False)
            temp_file.write(file_bytes)
            temp_file.close()
            # --- Use OCR for scanned PDFs ---
            if is_scanned_pdf(temp_file.name):
                logger.info(f"PDF {file_basename} detected as scanned. Using OCR.")
                text = extract_text_from_pdf(temp_file.name)
                docs = [Document(page_content=text, metadata={"filename": file_basename})]
            else:
                loader = PyMuPDFLoader(temp_file.name)
                docs = loader.load()
            os.unlink(temp_file.name)
        # Handle DOCX
        elif suffix == ".docx":
            temp_file = tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False)
            temp_file.write(file_bytes)
            temp_file.close()
            loader = UnstructuredWordDocumentLoader(temp_file.name)
            docs = loader.load()
            os.unlink(temp_file.name)
        # Handle CSV
        elif suffix == ".csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
            docs = []
            for idx, row in df.iterrows():
                content = row.to_json()
                docs.append(Document(page_content=content, metadata={"filename": file_basename, "row_index": idx}))
        # Handle Excel
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(io.BytesIO(file_bytes))
            docs = []
            for idx, row in df.iterrows():
                content = row.to_json()
                docs.append(Document(page_content=content, metadata={"filename": file_basename, "row_index": idx}))
        else:
            logger.warning(f"Unsupported file type: {file_basename}")
            raise ValueError(f"Unsupported file type: {suffix}")
        
        # Split the document into chunks (skip for CSV/Excel since each row is a chunk)
        if suffix in [".csv", ".xlsx", ".xls"]:
            logger.info(f"Processed {len(docs)} rows from {file_basename}")
            for i, doc in enumerate(docs[:3]):
                logger.info(f"Row {i} metadata: {doc.metadata}")
            return docs
        else:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            # Add filename and chunk_index to each chunk's metadata
            for idx, split in enumerate(splits):
                if not hasattr(split, 'metadata') or not isinstance(split.metadata, dict):
                    split.metadata = {}
                split.metadata['filename'] = file_basename
                split.metadata['chunk_index'] = idx
            logger.info(f"Processed {len(splits)} chunks from {file_basename}")
            for i, split in enumerate(splits[:3]):
                logger.info(f"Chunk {i} metadata: {split.metadata}")
            return splits