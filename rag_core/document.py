from rag_core.config import MAX_FILE_SIZE, logger
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tempfile
import os
import pandas as pd
import io
import re
from typing import List, Dict, Any, Optional
from rag_core.utils import DocumentClassifier, sanitize_text, extract_page_numbers
# --- Add OCR import ---
from rag_core.ocr import extract_text_from_pdf, is_scanned_pdf

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 400

class DocumentProcessor:
    """Handles document loading, validation, chunking, and domain classification. Now supports OCR for scanned PDFs."""
    
    @staticmethod
    def process_document(uploaded_file, file_bytes=None, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
        """Process an uploaded file and return split document chunks with enhanced metadata. Raises exceptions for errors. Supports OCR for scanned PDFs."""
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
                os.unlink(temp_file.name)
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
            # Enhanced chunking with semantic boundaries
            splits = DocumentProcessor._semantic_chunking(docs, chunk_size, chunk_overlap)
            
            # Failsafe: if no chunks or only empty chunks, try OCR fallback
            if (not splits) or all(not getattr(s, 'page_content', '').strip() for s in splits):
                logger.warning(f"Initial chunking failed for {file_basename}, attempting OCR fallback.")
                if suffix == ".pdf":
                    text = extract_text_from_pdf(temp_file.name)
                    docs = [Document(page_content=text, metadata={"filename": file_basename})]
                    splits = DocumentProcessor._semantic_chunking(docs, chunk_size, chunk_overlap)
                    logger.info(f"OCR fallback produced {len(splits)} chunks for {file_basename}")
            
            # Enhanced metadata extraction
            DocumentProcessor._enhance_metadata(splits, file_basename)
            
            logger.info(f"Processed {len(splits)} chunks from {file_basename}")
            for i, split in enumerate(splits[:3]):
                logger.info(f"Chunk {i} metadata: {split.metadata}")
            return splits
    
    @staticmethod
    def _semantic_chunking(docs: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
        """
        Enhanced chunking that respects semantic boundaries like chapters, sections, and paragraphs.
        """
        # First, try to detect document structure
        all_text = " ".join([doc.page_content for doc in docs])
        
        # Detect if this is a structured document (has chapters, sections, etc.)
        has_structure = DocumentProcessor._detect_document_structure(all_text)
        
        if has_structure:
            # Use semantic chunking for structured documents
            return DocumentProcessor._structured_chunking(docs, chunk_size, chunk_overlap)
        else:
            # Use standard chunking for unstructured documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", " ", ""]
            )
            return text_splitter.split_documents(docs)
    
    @staticmethod
    def _detect_document_structure(text: str) -> bool:
        """Detect if document has structured elements like chapters, sections, etc."""
        structure_patterns = [
            r'chapter\s+\d+',
            r'section\s+\d+',
            r'^\d+\.\s+',  # Numbered sections
            r'^\w+\s+\d+\.',  # Chapter/Section patterns
            r'part\s+\d+',
            r'article\s+\d+',
        ]
        
        text_lower = text.lower()
        structure_count = sum(1 for pattern in structure_patterns if re.search(pattern, text_lower, re.MULTILINE))
        
        # Consider it structured if we find multiple structure indicators
        return structure_count >= 2
    
    @staticmethod
    def _structured_chunking(docs: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
        """
        Chunk documents while preserving semantic structure.
        """
        splits = []
        
        for doc in docs:
            text = doc.page_content
            lines = text.split('\n')
            current_chunk = []
            current_length = 0
            section_info = {}
            
            for line in lines:
                # Detect section boundaries
                section_match = re.match(r'^(chapter|section|part|article)\s+(\d+[\.\d]*)\s*[:\.]?\s*(.*)', line, re.IGNORECASE)
                if section_match:
                    # Save current chunk if it exists
                    if current_chunk:
                        chunk_text = '\n'.join(current_chunk)
                        if len(chunk_text.strip()) > 50:  # Minimum meaningful chunk size
                            new_doc = Document(
                                page_content=chunk_text,
                                metadata={
                                    **doc.metadata,
                                    **section_info,
                                    'chunk_type': 'semantic'
                                }
                            )
                            splits.append(new_doc)
                    
                    # Start new chunk
                    current_chunk = [line]
                    current_length = len(line)
                    section_info = {
                        'section_type': section_match.group(1).lower(),
                        'section_number': section_match.group(2),
                        'section_title': section_match.group(3).strip()
                    }
                else:
                    # Add line to current chunk
                    current_chunk.append(line)
                    current_length += len(line)
                    
                    # Split if chunk gets too large
                    if current_length > chunk_size and len(current_chunk) > 1:
                        # Find a good break point (end of sentence or paragraph)
                        break_point = DocumentProcessor._find_break_point(current_chunk)
                        
                        chunk_text = '\n'.join(current_chunk[:break_point])
                        if len(chunk_text.strip()) > 50:
                            new_doc = Document(
                                page_content=chunk_text,
                                metadata={
                                    **doc.metadata,
                                    **section_info,
                                    'chunk_type': 'semantic'
                                }
                            )
                            splits.append(new_doc)
                        
                        # Keep overlap
                        overlap_start = max(0, break_point - chunk_overlap // 100)
                        current_chunk = current_chunk[overlap_start:]
                        current_length = sum(len(line) for line in current_chunk)
            
            # Add final chunk
            if current_chunk:
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text.strip()) > 50:
                    new_doc = Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            **section_info,
                            'chunk_type': 'semantic'
                        }
                    )
                    splits.append(new_doc)
        
        return splits
    
    @staticmethod
    def _find_break_point(lines: List[str]) -> int:
        """Find a good break point in a list of lines."""
        # Prefer breaking at paragraph boundaries
        for i in range(len(lines) - 1, 0, -1):
            if not lines[i].strip():  # Empty line
                return i
            if lines[i].endswith('.') or lines[i].endswith('!') or lines[i].endswith('?'):
                return i + 1
        
        # Fallback to middle
        return len(lines) // 2
    
    @staticmethod
    def _enhance_metadata(splits: List[Document], filename: str):
        """
        Enhance document metadata with domain classification, page tracking, and source information.
        """
        # Get document classification from first chunk
        if splits:
            sample_text = splits[0].page_content[:1000]
            try:
                classification = DocumentClassifier.classify_document(sample_text, filename)
                logger.info(f"Document classified as: {classification.get('domain', 'unknown')}")
            except Exception as e:
                logger.error(f"Document classification failed: {str(e)}")
                classification = {
                    "domain": "general",
                    "title": filename.replace('.pdf', '').replace('.docx', '').replace('.txt', ''),
                    "confidence": 0.5,
                    "type": "document"
                }
        else:
            classification = {
                "domain": "general",
                "title": filename.replace('.pdf', '').replace('.docx', '').replace('.txt', ''),
                "confidence": 0.5,
                "type": "document"
            }
        
        # Enhance each chunk's metadata
        for idx, split in enumerate(splits):
            if not hasattr(split, 'metadata') or not isinstance(split.metadata, dict):
                split.metadata = {}
            
            # Basic metadata
            split.metadata.update({
                'filename': filename,
                'chunk_index': idx,
                'domain': classification.get('domain', 'general'),
                'title': classification.get('title', filename),
                'doc_type': classification.get('type', 'document'),
                'classification_confidence': classification.get('confidence', 0.5),
                'timestamp': str(pd.Timestamp.now()),
            })
            
            # Extract page numbers if present
            page_numbers = extract_page_numbers(split.page_content)
            if page_numbers:
                split.metadata['page_number'] = page_numbers[0]  # Use first page number found
            
            # Extract section information if present
            section_match = re.search(r'^(chapter|section|part|article)\s+(\d+[\.\d]*)', split.page_content, re.IGNORECASE)
            if section_match:
                split.metadata['section_type'] = section_match.group(1).lower()
                split.metadata['section_number'] = section_match.group(2)
            
            # Sanitize content
            split.page_content = sanitize_text(split.page_content)
            
            # Add content statistics
            split.metadata['word_count'] = len(split.page_content.split())
            split.metadata['char_count'] = len(split.page_content)