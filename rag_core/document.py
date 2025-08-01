from rag_core.config import MAX_FILE_SIZE, logger
import hashlib
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import pickle
from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tempfile
import pandas as pd
import io
import re
import xml.etree.ElementTree as ET
from rag_core.utils import DocumentClassifier, sanitize_text, extract_page_numbers
# --- Add OCR import ---
from rag_core.ocr import extract_text_from_pdf, is_scanned_pdf
import time

# Enhanced Document Processing Classes
class DocumentStatus(Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

class AnnotationType(Enum):
    """Types of annotations"""
    HIGHLIGHT = "highlight"
    COMMENT = "comment"
    TAG = "tag"
    RELATIONSHIP = "relationship"
    METADATA = "metadata"

@dataclass
class DocumentVersion:
    """Document version information"""
    version_id: str
    timestamp: datetime
    file_hash: str
    file_size: int
    changes_summary: str
    author: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class DocumentAnnotation:
    """Document annotation"""
    annotation_id: str
    annotation_type: AnnotationType
    content: str
    position: Dict[str, Any]  # Page, line, character positions
    timestamp: datetime
    author: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class DocumentRelationship:
    """Document relationship"""
    relationship_id: str
    source_doc_id: str
    target_doc_id: str
    relationship_type: str  # "references", "similar_to", "part_of", "version_of"
    strength: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = None

@dataclass
class EnhancedDocument:
    """Enhanced document with versioning, annotations, and relationships"""
    doc_id: str
    filename: str
    file_hash: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    versions: List[DocumentVersion]
    annotations: List[DocumentAnnotation]
    relationships: List[DocumentRelationship]
    metadata: Dict[str, Any]
    content_hash: str
    domain: str
    file_type: str
    chunk_count: int
    processing_time: float
    error_log: List[str] = None

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 400

# Supported file types mapping
SUPPORTED_EXTENSIONS = {
    '.pdf': 'PDF Document',
    '.docx': 'Word Document', 
    '.doc': 'Word Document',
    '.csv': 'CSV Data',
    '.xlsx': 'Excel Spreadsheet',
    '.xls': 'Excel Spreadsheet',
    '.txt': 'Text File',
    '.html': 'HTML Document',
    '.htm': 'HTML Document',
    '.json': 'JSON Data',
    '.xml': 'XML Document',
    '.md': 'Markdown Document'
}

class DocumentProcessor:
    """Enhanced document processor with versioning, annotations, and relationships."""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'PDF Document',
        '.docx': 'Word Document',
        '.doc': 'Word Document (Legacy)',
        '.txt': 'Text File',
        '.csv': 'CSV File',
        '.xlsx': 'Excel Spreadsheet',
        '.xls': 'Excel Spreadsheet (Legacy)',
        '.html': 'HTML File',
        '.htm': 'HTML File',
        '.json': 'JSON File',
        '.xml': 'XML File',
        '.md': 'Markdown File',
        '.jpg': 'JPEG Image',
        '.jpeg': 'JPEG Image',
        '.png': 'PNG Image',
        '.tiff': 'TIFF Image',
        '.bmp': 'BMP Image'
    }
    
    def __init__(self):
        self.documents_db = {}  # In-memory document storage
        self.relationships_db = {}  # Document relationships
        self.annotations_db = {}  # Document annotations
        self.versions_db = {}  # Document versions
        self._load_persistent_data()
    
    def _load_persistent_data(self):
        """Load persistent data from disk"""
        try:
            data_dir = Path("data/documents")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Load documents
            docs_file = data_dir / "documents.pkl"
            if docs_file.exists():
                with open(docs_file, 'rb') as f:
                    self.documents_db = pickle.load(f)
            
            # Load relationships
            rels_file = data_dir / "relationships.pkl"
            if rels_file.exists():
                with open(rels_file, 'rb') as f:
                    self.relationships_db = pickle.load(f)
            
            # Load annotations
            anns_file = data_dir / "annotations.pkl"
            if anns_file.exists():
                with open(anns_file, 'rb') as f:
                    self.annotations_db = pickle.load(f)
            
            # Load versions
            vers_file = data_dir / "versions.pkl"
            if vers_file.exists():
                with open(vers_file, 'rb') as f:
                    self.versions_db = pickle.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading persistent data: {str(e)}")
    
    def _save_persistent_data(self):
        """Save persistent data to disk"""
        try:
            data_dir = Path("data/documents")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Save documents
            with open(data_dir / "documents.pkl", 'wb') as f:
                pickle.dump(self.documents_db, f)
            
            # Save relationships
            with open(data_dir / "relationships.pkl", 'wb') as f:
                pickle.dump(self.relationships_db, f)
            
            # Save annotations
            with open(data_dir / "annotations.pkl", 'wb') as f:
                pickle.dump(self.annotations_db, f)
            
            # Save versions
            with open(data_dir / "versions.pkl", 'wb') as f:
                pickle.dump(self.versions_db, f)
                
        except Exception as e:
            logger.error(f"Error saving persistent data: {str(e)}")
    
    def _generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash for file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _generate_content_hash(self, text: str) -> str:
        """Generate SHA-256 hash for text content"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _create_document_version(self, filename: str, file_content: bytes, 
                                changes_summary: str = "Initial version", 
                                author: str = None) -> DocumentVersion:
        """Create a new document version"""
        file_hash = self._generate_file_hash(file_content)
        version_id = str(uuid.uuid4())
        
        version = DocumentVersion(
            version_id=version_id,
            timestamp=datetime.now(),
            file_hash=file_hash,
            file_size=len(file_content),
            changes_summary=changes_summary,
            author=author,
            metadata={}
        )
        
        return version
    
    def _detect_document_changes(self, filename: str, file_content: bytes) -> bool:
        """Detect if document has changed since last version"""
        if filename not in self.documents_db:
            return True
        
        doc = self.documents_db[filename]
        if not doc.versions:
            return True
        
        current_hash = self._generate_file_hash(file_content)
        latest_version = doc.versions[-1]
        
        return current_hash != latest_version.file_hash
    
    def _create_enhanced_document(self, filename: str, file_content: bytes, 
                                 chunks: List[Document], processing_time: float,
                                 domain: str, file_type: str) -> EnhancedDocument:
        """Create an enhanced document with all metadata"""
        doc_id = str(uuid.uuid4())
        file_hash = self._generate_file_hash(file_content)
        content_text = "\n".join([chunk.page_content for chunk in chunks])
        content_hash = self._generate_content_hash(content_text)
        
        # Create initial version
        version = self._create_document_version(filename, file_content)
        
        doc = EnhancedDocument(
            doc_id=doc_id,
            filename=filename,
            file_hash=file_hash,
            file_size=len(file_content),
            status=DocumentStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            versions=[version],
            annotations=[],
            relationships=[],
            metadata={
                'file_type': file_type,
                'domain': domain,
                'chunk_count': len(chunks),
                'processing_time': processing_time,
                'content_hash': content_hash
            },
            content_hash=content_hash,
            domain=domain,
            file_type=file_type,
            chunk_count=len(chunks),
            processing_time=processing_time,
            error_log=[]
        )
        
        return doc
    
    @staticmethod
    def get_supported_extensions() -> Dict[str, str]:
        """Return supported file extensions and their descriptions."""
        return SUPPORTED_EXTENSIONS.copy()
    
    @staticmethod
    def is_supported_file(filename: str) -> bool:
        """Check if file type is supported."""
        if not filename:
            return False
        suffix = os.path.splitext(filename)[1].lower()
        return suffix in SUPPORTED_EXTENSIONS
    
    @staticmethod
    def process_document(file_content: bytes, filename: str, chunk_size: int = DEFAULT_CHUNK_SIZE, 
                        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[Document]:
        """
        Enhanced document processing with versioning, annotations, and relationships support.
        Returns processed document chunks with enhanced metadata.
        """
        start_time = time.time()
        
        try:
            # Validate file size
            if len(file_content) > MAX_FILE_SIZE:
                raise ValueError(f"File size {len(file_content)} exceeds maximum allowed size {MAX_FILE_SIZE}")
            
            # Get file extension and validate
            file_ext = os.path.splitext(filename)[1].lower()
            if not DocumentProcessor.is_supported_file(filename):
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Check for document changes
            processor = DocumentProcessor()
            has_changes = processor._detect_document_changes(filename, file_content)
            
            if not has_changes:
                logger.info(f"Document {filename} unchanged, skipping reprocessing")
                # Return existing chunks if available
                if filename in processor.documents_db:
                    doc = processor.documents_db[filename]
                    # Reconstruct chunks from metadata (simplified)
                    chunks = []
                    for i in range(doc.chunk_count):
                        chunk = Document(
                            page_content=f"Chunk {i+1} of {filename}",
                            metadata={
                                'filename': filename,
                                'chunk_index': i,
                                'file_type': doc.file_type,
                                'domain': doc.domain
                            }
                        )
                        chunks.append(chunk)
                    return chunks
            
            # Process document based on file type
            documents = []
            
            if file_ext == '.pdf':
                documents = DocumentProcessor._process_pdf(file_content, filename)
            elif file_ext in ['.docx', '.doc']:
                documents = DocumentProcessor._process_word(file_content, filename)
            elif file_ext == '.txt':
                documents = DocumentProcessor._process_text(file_content, filename)
            elif file_ext == '.csv':
                documents = DocumentProcessor._process_csv(file_content, filename)
            elif file_ext in ['.xlsx', '.xls']:
                documents = DocumentProcessor._process_excel(file_content, filename)
            elif file_ext in ['.html', '.htm']:
                documents = DocumentProcessor._process_html(file_content, filename)
            elif file_ext == '.json':
                documents = DocumentProcessor._process_json(file_content, filename)
            elif file_ext == '.xml':
                documents = DocumentProcessor._process_xml(file_content, filename)
            elif file_ext == '.md':
                documents = DocumentProcessor._process_markdown(file_content, filename)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                documents = DocumentProcessor._process_image(file_content, filename)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            if not documents:
                raise ValueError("No content extracted from document")
            
            # Combine all text content for domain classification
            all_text = " ".join([doc.page_content for doc in documents])
            all_text = sanitize_text(all_text)
            
            if not all_text.strip():
                raise ValueError("No text content extracted from document")
            
            # Classify domain
            classifier = DocumentClassifier()
            classification_result = classifier.classify_document(all_text[:1000], filename)
            domain = classification_result.get('domain', 'general')
            
            # Enhance metadata for all documents
            for idx, doc in enumerate(documents):
                doc.metadata.update({
                    'filename': filename,
                    'chunk_index': idx,
                    'file_type': file_ext[1:],  # Remove the dot
                    'domain': domain,
                    'word_count': len(doc.page_content.split()),
                    'char_count': len(doc.page_content),
                    'chunk_id': f"{filename}_{idx}",
                    'processing_timestamp': datetime.now().isoformat()
                })
            
            # Create enhanced document record
            processing_time = time.time() - start_time
            enhanced_doc = processor._create_enhanced_document(
                filename, file_content, documents, processing_time, domain, file_ext[1:]
            )
            
            # Store enhanced document
            processor.documents_db[filename] = enhanced_doc
            processor._save_persistent_data()
            
            logger.info(f"Enhanced document processing completed for {filename}: "
                       f"{len(documents)} chunks, {processing_time:.2f}s, domain: {domain}")
            
            return documents
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing document {filename}: {str(e)}")
            
            # Create error record
            processor = DocumentProcessor()
            if filename not in processor.documents_db:
                error_doc = EnhancedDocument(
                    doc_id=str(uuid.uuid4()),
                    filename=filename,
                    file_hash=processor._generate_file_hash(file_content),
                    file_size=len(file_content),
                    status=DocumentStatus.FAILED,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    versions=[],
                    annotations=[],
                    relationships=[],
                    metadata={'error': str(e)},
                    content_hash="",
                    domain="unknown",
                    file_type=os.path.splitext(filename)[1][1:],
                    chunk_count=0,
                    processing_time=processing_time,
                    error_log=[str(e)]
                )
                processor.documents_db[filename] = error_doc
                processor._save_persistent_data()
            
            raise

    @staticmethod
    def _process_pdf(file_bytes: bytes, filename: str) -> List[Document]:
        """Process PDF files with OCR support for scanned documents."""
        temp_file = tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False)
        temp_file.write(file_bytes)
        temp_file.close()
        
        try:
            # Check if it's a scanned PDF
            if is_scanned_pdf(temp_file.name):
                logger.info(f"PDF {filename} detected as scanned. Using OCR.")
                text = extract_text_from_pdf(temp_file.name)
                docs = [Document(page_content=text, metadata={"filename": filename, "file_type": "pdf", "processing": "ocr"})]
            else:
                loader = PyMuPDFLoader(temp_file.name)
                docs = loader.load()
                # Add file type metadata
                for doc in docs:
                    doc.metadata["file_type"] = "pdf"
                    doc.metadata["processing"] = "native"
        finally:
            os.unlink(temp_file.name)
        
        return docs

    @staticmethod
    def _process_word(file_bytes: bytes, filename: str) -> List[Document]:
        """Process Word documents."""
        temp_file = tempfile.NamedTemporaryFile("wb", suffix=".docx", delete=False)
        temp_file.write(file_bytes)
        temp_file.close()
        
        try:
            loader = UnstructuredWordDocumentLoader(temp_file.name)
            docs = loader.load()
            # Add file type metadata
            for doc in docs:
                doc.metadata["file_type"] = "word"
        finally:
            os.unlink(temp_file.name)
        
        return docs

    @staticmethod
    def _process_csv(file_bytes: bytes, filename: str) -> List[Document]:
        """Process CSV files with enhanced metadata."""
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
            docs = []
            
            # Add document-level metadata
            doc_metadata = {
                "filename": filename,
                "file_type": "csv",
                "total_rows": len(df),
                "columns": list(df.columns),
                "data_type": "tabular"
            }
            
            for idx, row in df.iterrows():
                content = row.to_json()
                row_metadata = doc_metadata.copy()
                row_metadata.update({
                    "row_index": idx,
                    "chunk_type": "table_row"
                })
                docs.append(Document(page_content=content, metadata=row_metadata))
            
            return docs
        except Exception as e:
            logger.error(f"Error processing CSV file {filename}: {str(e)}")
            raise ValueError(f"Failed to process CSV file: {str(e)}")

    @staticmethod
    def _process_excel(file_bytes: bytes, filename: str) -> List[Document]:
        """Process Excel files with sheet support."""
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
            docs = []
            
            for sheet_name, sheet_df in df.items():
                # Add document-level metadata
                doc_metadata = {
                    "filename": filename,
                    "file_type": "excel",
                    "sheet_name": sheet_name,
                    "total_rows": len(sheet_df),
                    "columns": list(sheet_df.columns),
                    "data_type": "tabular"
                }
                
                for idx, row in sheet_df.iterrows():
                    content = row.to_json()
                    row_metadata = doc_metadata.copy()
                    row_metadata.update({
                        "row_index": idx,
                        "chunk_type": "table_row"
                    })
                    docs.append(Document(page_content=content, metadata=row_metadata))
            
            return docs
        except Exception as e:
            logger.error(f"Error processing Excel file {filename}: {str(e)}")
            raise ValueError(f"Failed to process Excel file: {str(e)}")

    @staticmethod
    def _process_text(file_bytes: bytes, filename: str) -> List[Document]:
        """Process plain text files."""
        try:
            text = file_bytes.decode('utf-8')
            # Clean and sanitize text
            text = sanitize_text(text)
            
            return [Document(
                page_content=text,
                metadata={
                    "filename": filename,
                    "file_type": "text",
                    "chunk_type": "full_document"
                }
            )]
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    text = file_bytes.decode(encoding)
                    text = sanitize_text(text)
                    return [Document(
                        page_content=text,
                        metadata={
                            "filename": filename,
                            "file_type": "text",
                            "encoding": encoding,
                            "chunk_type": "full_document"
                        }
                    )]
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not decode text file {filename} with any supported encoding")

    @staticmethod
    def _process_html(file_bytes: bytes, filename: str) -> List[Document]:
        """Process HTML files with basic tag cleaning."""
        try:
            from bs4 import BeautifulSoup
            
            html_content = file_bytes.decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return [Document(
                page_content=text,
                metadata={
                    "filename": filename,
                    "file_type": "html",
                    "title": soup.title.string if soup.title else None,
                    "chunk_type": "full_document"
                }
            )]
        except ImportError:
            logger.warning("BeautifulSoup not available, processing HTML as plain text")
            return DocumentProcessor._process_text(file_bytes, filename)
        except Exception as e:
            logger.error(f"Error processing HTML file {filename}: {str(e)}")
            raise ValueError(f"Failed to process HTML file: {str(e)}")

    @staticmethod
    def _process_json(file_bytes: bytes, filename: str) -> List[Document]:
        """Process JSON files with structured data support."""
        try:
            data = json.loads(file_bytes.decode('utf-8'))
            docs = []
            
            def process_json_item(item, path="", parent_metadata=None):
                """Recursively process JSON items."""
                if isinstance(item, dict):
                    for key, value in item.items():
                        current_path = f"{path}.{key}" if path else key
                        process_json_item(value, current_path, parent_metadata)
                elif isinstance(item, list):
                    for idx, value in enumerate(item):
                        current_path = f"{path}[{idx}]" if path else f"[{idx}]"
                        process_json_item(value, current_path, parent_metadata)
                else:
                    # Leaf node - create document
                    content = json.dumps({path: item})
                    metadata = {
                        "filename": filename,
                        "file_type": "json",
                        "json_path": path,
                        "data_type": "structured",
                        "chunk_type": "json_item"
                    }
                    if parent_metadata:
                        metadata.update(parent_metadata)
                    docs.append(Document(page_content=content, metadata=metadata))
            
            # Add document-level metadata
            doc_metadata = {
                "filename": filename,
                "file_type": "json",
                "data_type": "structured"
            }
            
            process_json_item(data, parent_metadata=doc_metadata)
            
            # If no items were processed (empty or simple JSON), create a single document
            if not docs:
                docs.append(Document(
                    page_content=json.dumps(data, indent=2),
                    metadata={
                        "filename": filename,
                        "file_type": "json",
                        "data_type": "structured",
                        "chunk_type": "full_document"
                    }
                ))
            
            return docs
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file {filename}: {str(e)}")
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing JSON file {filename}: {str(e)}")
            raise ValueError(f"Failed to process JSON file: {str(e)}")

    @staticmethod
    def _process_xml(file_bytes: bytes, filename: str) -> List[Document]:
        """Process XML files with element-based chunking."""
        try:
            xml_content = file_bytes.decode('utf-8')
            root = ET.fromstring(xml_content)
            docs = []
            
            def process_xml_element(element, path="", parent_metadata=None):
                """Recursively process XML elements."""
                current_path = f"{path}/{element.tag}" if path else element.tag
                
                # Create metadata for this element
                element_metadata = {
                    "filename": filename,
                    "file_type": "xml",
                    "xml_path": current_path,
                    "tag_name": element.tag,
                    "data_type": "structured",
                    "chunk_type": "xml_element"
                }
                
                if parent_metadata:
                    element_metadata.update(parent_metadata)
                
                # Add attributes to metadata
                if element.attrib:
                    element_metadata["attributes"] = element.attrib
                
                # Process text content
                if element.text and element.text.strip():
                    content = element.text.strip()
                    docs.append(Document(
                        page_content=content,
                        metadata=element_metadata.copy()
                    ))
                
                # Process child elements
                for child in element:
                    process_xml_element(child, current_path, element_metadata)
            
            # Add document-level metadata
            doc_metadata = {
                "filename": filename,
                "file_type": "xml",
                "root_tag": root.tag,
                "data_type": "structured"
            }
            
            process_xml_element(root, parent_metadata=doc_metadata)
            
            # If no elements were processed, create a single document
            if not docs:
                docs.append(Document(
                    page_content=xml_content,
                    metadata={
                        "filename": filename,
                        "file_type": "xml",
                        "data_type": "structured",
                        "chunk_type": "full_document"
                    }
                ))
            
            return docs
        except ET.ParseError as e:
            logger.error(f"Error parsing XML file {filename}: {str(e)}")
            raise ValueError(f"Invalid XML format: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing XML file {filename}: {str(e)}")
            raise ValueError(f"Failed to process XML file: {str(e)}")

    @staticmethod
    def _process_markdown(file_bytes: bytes, filename: str) -> List[Document]:
        """Process Markdown files with structure preservation."""
        try:
            text = file_bytes.decode('utf-8')
            
            return [Document(
                page_content=text,
                metadata={
                    "filename": filename,
                    "file_type": "markdown",
                    "chunk_type": "full_document"
                }
            )]
        except Exception as e:
            logger.error(f"Error processing Markdown file {filename}: {str(e)}")
            raise ValueError(f"Failed to process Markdown file: {str(e)}")
    
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

    def add_annotation(self, filename: str, annotation_type: AnnotationType, 
                      content: str, position: Dict[str, Any], author: str = None) -> str:
        """Add annotation to a document"""
        if filename not in self.documents_db:
            raise ValueError(f"Document {filename} not found")
        
        annotation_id = str(uuid.uuid4())
        annotation = DocumentAnnotation(
            annotation_id=annotation_id,
            annotation_type=annotation_type,
            content=content,
            position=position,
            timestamp=datetime.now(),
            author=author,
            metadata={}
        )
        
        # Add to document
        doc = self.documents_db[filename]
        doc.annotations.append(annotation)
        doc.updated_at = datetime.now()
        
        # Store in annotations database
        if filename not in self.annotations_db:
            self.annotations_db[filename] = []
        self.annotations_db[filename].append(annotation)
        
        self._save_persistent_data()
        return annotation_id
    
    def get_annotations(self, filename: str, annotation_type: AnnotationType = None) -> List[DocumentAnnotation]:
        """Get annotations for a document"""
        if filename not in self.documents_db:
            return []
        
        doc = self.documents_db[filename]
        if annotation_type:
            return [ann for ann in doc.annotations if ann.annotation_type == annotation_type]
        return doc.annotations
    
    def remove_annotation(self, filename: str, annotation_id: str) -> bool:
        """Remove annotation from a document"""
        if filename not in self.documents_db:
            return False
        
        doc = self.documents_db[filename]
        doc.annotations = [ann for ann in doc.annotations if ann.annotation_id != annotation_id]
        doc.updated_at = datetime.now()
        
        # Remove from annotations database
        if filename in self.annotations_db:
            self.annotations_db[filename] = [ann for ann in self.annotations_db[filename] 
                                           if ann.annotation_id != annotation_id]
        
        self._save_persistent_data()
        return True
    
    def add_relationship(self, source_filename: str, target_filename: str, 
                        relationship_type: str, strength: float = 1.0) -> str:
        """Add relationship between two documents"""
        if source_filename not in self.documents_db or target_filename not in self.documents_db:
            raise ValueError("One or both documents not found")
        
        relationship_id = str(uuid.uuid4())
        relationship = DocumentRelationship(
            relationship_id=relationship_id,
            source_doc_id=self.documents_db[source_filename].doc_id,
            target_doc_id=self.documents_db[target_filename].doc_id,
            relationship_type=relationship_type,
            strength=strength,
            metadata={}
        )
        
        # Add to both documents
        source_doc = self.documents_db[source_filename]
        target_doc = self.documents_db[target_filename]
        
        source_doc.relationships.append(relationship)
        target_doc.relationships.append(relationship)
        
        source_doc.updated_at = datetime.now()
        target_doc.updated_at = datetime.now()
        
        # Store in relationships database
        if source_filename not in self.relationships_db:
            self.relationships_db[source_filename] = []
        self.relationships_db[source_filename].append(relationship)
        
        self._save_persistent_data()
        return relationship_id
    
    def get_relationships(self, filename: str, relationship_type: str = None) -> List[DocumentRelationship]:
        """Get relationships for a document"""
        if filename not in self.documents_db:
            return []
        
        doc = self.documents_db[filename]
        if relationship_type:
            return [rel for rel in doc.relationships if rel.relationship_type == relationship_type]
        return doc.relationships
    
    def find_related_documents(self, filename: str, relationship_type: str = None) -> List[str]:
        """Find documents related to the given document"""
        relationships = self.get_relationships(filename, relationship_type)
        related_filenames = []
        
        for rel in relationships:
            if rel.source_doc_id == self.documents_db[filename].doc_id:
                # Find target document
                for doc_filename, doc in self.documents_db.items():
                    if doc.doc_id == rel.target_doc_id:
                        related_filenames.append(doc_filename)
                        break
            elif rel.target_doc_id == self.documents_db[filename].doc_id:
                # Find source document
                for doc_filename, doc in self.documents_db.items():
                    if doc.doc_id == rel.source_doc_id:
                        related_filenames.append(doc_filename)
                        break
        
        return list(set(related_filenames))
    
    def get_document_versions(self, filename: str) -> List[DocumentVersion]:
        """Get all versions of a document"""
        if filename not in self.documents_db:
            return []
        
        return self.documents_db[filename].versions
    
    def create_new_version(self, filename: str, file_content: bytes, 
                          changes_summary: str, author: str = None) -> str:
        """Create a new version of a document"""
        if filename not in self.documents_db:
            raise ValueError(f"Document {filename} not found")
        
        version = self._create_document_version(filename, file_content, changes_summary, author)
        
        doc = self.documents_db[filename]
        doc.versions.append(version)
        doc.updated_at = datetime.now()
        
        # Store in versions database
        if filename not in self.versions_db:
            self.versions_db[filename] = []
        self.versions_db[filename].append(version)
        
        self._save_persistent_data()
        return version.version_id
    
    def get_document_info(self, filename: str) -> Dict[str, Any]:
        """Get comprehensive information about a document"""
        if filename not in self.documents_db:
            return {}
        
        doc = self.documents_db[filename]
        return {
            'doc_id': doc.doc_id,
            'filename': doc.filename,
            'status': doc.status.value,
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat(),
            'file_size': doc.file_size,
            'file_type': doc.file_type,
            'domain': doc.domain,
            'chunk_count': doc.chunk_count,
            'processing_time': doc.processing_time,
            'version_count': len(doc.versions),
            'annotation_count': len(doc.annotations),
            'relationship_count': len(doc.relationships),
            'error_count': len(doc.error_log) if doc.error_log else 0,
            'metadata': doc.metadata
        }
    
    def get_all_documents_info(self) -> List[Dict[str, Any]]:
        """Get information about all documents"""
        return [self.get_document_info(filename) for filename in self.documents_db.keys()]
    
    def search_documents_by_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents by content similarity"""
        results = []
        
        for filename, doc in self.documents_db.items():
            # Simple text search in metadata and content hash
            if query.lower() in filename.lower() or query.lower() in doc.domain.lower():
                results.append({
                    'filename': filename,
                    'score': 1.0,
                    'domain': doc.domain,
                    'file_type': doc.file_type,
                    'updated_at': doc.updated_at.isoformat()
                })
        
        # Sort by updated_at (most recent first)
        results.sort(key=lambda x: x['updated_at'], reverse=True)
        return results[:limit]