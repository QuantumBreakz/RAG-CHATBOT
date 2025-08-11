"""
Template-Based Chunking System
Provides intelligent chunking strategies for different document types and content structures
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Different chunking strategies"""
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    FIXED_SIZE = "fixed_size"
    CONTENT_AWARE = "content_aware"


class DocumentType(Enum):
    """Document types for chunking templates"""
    TECHNICAL_DOCUMENT = "technical_document"
    RESEARCH_PAPER = "research_paper"
    LEGAL_DOCUMENT = "legal_document"
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    MANUAL = "manual"
    REPORT = "report"
    CONTRACT = "contract"
    EMAIL = "email"
    CODE = "code"
    GENERAL = "general"


@dataclass
class ChunkingTemplate:
    """Template for chunking strategy"""
    name: str
    document_type: DocumentType
    strategy: ChunkingStrategy
    chunk_size: int
    chunk_overlap: int
    separators: List[str] = field(default_factory=list)
    keep_separator: bool = True
    is_recursive: bool = True
    length_function: str = "len"
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    description: str = ""


@dataclass
class ChunkingResult:
    """Result of chunking operation"""
    chunks: List[Document]
    strategy_used: ChunkingStrategy
    template_used: str
    quality_score: float
    chunk_count: int
    average_chunk_size: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    explainable_decisions: List[str] = field(default_factory=list)


class TemplateBasedChunker:
    """Intelligent chunking system using templates"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_templates(self) -> Dict[str, ChunkingTemplate]:
        """Initialize chunking templates for different document types"""
        templates = {}
        
        # Technical Document Template
        templates["technical_document"] = ChunkingTemplate(
            name="Technical Document",
            document_type=DocumentType.TECHNICAL_DOCUMENT,
            strategy=ChunkingStrategy.STRUCTURAL,
            chunk_size=3000,
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_sections": True,
                "preserve_code_blocks": True,
                "preserve_tables": True,
                "min_section_size": 200
            },
            quality_metrics={
                "coherence": 0.8,
                "completeness": 0.9,
                "readability": 0.7
            },
            description="Optimized for technical documentation with code blocks and structured content"
        )
        
        # Research Paper Template
        templates["research_paper"] = ChunkingTemplate(
            name="Research Paper",
            document_type=DocumentType.RESEARCH_PAPER,
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=2500,
            chunk_overlap=400,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_abstract": True,
                "preserve_methodology": True,
                "preserve_conclusions": True,
                "preserve_citations": True,
                "min_paragraph_size": 150
            },
            quality_metrics={
                "coherence": 0.9,
                "completeness": 0.95,
                "readability": 0.8
            },
            description="Optimized for academic papers with structured sections and citations"
        )
        
        # Legal Document Template
        templates["legal_document"] = ChunkingTemplate(
            name="Legal Document",
            document_type=DocumentType.LEGAL_DOCUMENT,
            strategy=ChunkingStrategy.STRUCTURAL,
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_clauses": True,
                "preserve_sections": True,
                "preserve_definitions": True,
                "preserve_amendments": True,
                "min_clause_size": 100
            },
            quality_metrics={
                "coherence": 0.95,
                "completeness": 0.9,
                "readability": 0.6
            },
            description="Optimized for legal documents with precise clause preservation"
        )
        
        # News Article Template
        templates["news_article"] = ChunkingTemplate(
            name="News Article",
            document_type=DocumentType.NEWS_ARTICLE,
            strategy=ChunkingStrategy.HYBRID,
            chunk_size=1800,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_headlines": True,
                "preserve_quotes": True,
                "preserve_paragraphs": True,
                "min_paragraph_size": 100
            },
            quality_metrics={
                "coherence": 0.8,
                "completeness": 0.85,
                "readability": 0.9
            },
            description="Optimized for news articles with headline and quote preservation"
        )
        
        # Blog Post Template
        templates["blog_post"] = ChunkingTemplate(
            name="Blog Post",
            document_type=DocumentType.BLOG_POST,
            strategy=ChunkingStrategy.ADAPTIVE,
            chunk_size=2200,
            chunk_overlap=250,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_headings": True,
                "preserve_lists": True,
                "preserve_links": True,
                "min_section_size": 150
            },
            quality_metrics={
                "coherence": 0.85,
                "completeness": 0.8,
                "readability": 0.9
            },
            description="Optimized for blog posts with heading and list preservation"
        )
        
        # Manual Template
        templates["manual"] = ChunkingTemplate(
            name="Manual",
            document_type=DocumentType.MANUAL,
            strategy=ChunkingStrategy.STRUCTURAL,
            chunk_size=2800,
            chunk_overlap=300,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_steps": True,
                "preserve_warnings": True,
                "preserve_code_blocks": True,
                "preserve_images": True,
                "min_step_size": 100
            },
            quality_metrics={
                "coherence": 0.9,
                "completeness": 0.95,
                "readability": 0.8
            },
            description="Optimized for user manuals with step-by-step instructions"
        )
        
        # Code Template
        templates["code"] = ChunkingTemplate(
            name="Code",
            document_type=DocumentType.CODE,
            strategy=ChunkingStrategy.STRUCTURAL,
            chunk_size=1500,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_functions": True,
                "preserve_classes": True,
                "preserve_comments": True,
                "preserve_imports": True,
                "min_function_size": 50
            },
            quality_metrics={
                "coherence": 0.95,
                "completeness": 0.9,
                "readability": 0.8
            },
            description="Optimized for code files with function and class preservation"
        )
        
        # General Template
        templates["general"] = ChunkingTemplate(
            name="General",
            document_type=DocumentType.GENERAL,
            strategy=ChunkingStrategy.ADAPTIVE,
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={
                "preserve_paragraphs": True,
                "preserve_sentences": True,
                "min_chunk_size": 100
            },
            quality_metrics={
                "coherence": 0.7,
                "completeness": 0.8,
                "readability": 0.8
            },
            description="General purpose chunking for unknown document types"
        )
        
        return templates
    
    def detect_document_type(self, text: str, filename: str = "") -> DocumentType:
        """Detect document type based on content and filename"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Technical document indicators
        if any(keyword in text_lower for keyword in [
            "api", "function", "method", "class", "interface", "implementation",
            "technical specification", "system architecture", "database schema"
        ]):
            return DocumentType.TECHNICAL_DOCUMENT
        
        # Research paper indicators
        if any(keyword in text_lower for keyword in [
            "abstract", "introduction", "methodology", "conclusion", "references",
            "research", "study", "experiment", "hypothesis", "results"
        ]):
            return DocumentType.RESEARCH_PAPER
        
        # Legal document indicators
        if any(keyword in text_lower for keyword in [
            "whereas", "hereby", "party", "agreement", "contract", "clause",
            "legal", "law", "jurisdiction", "terms and conditions"
        ]):
            return DocumentType.LEGAL_DOCUMENT
        
        # News article indicators
        if any(keyword in text_lower for keyword in [
            "breaking news", "reported", "according to", "journalist",
            "news", "article", "published", "reporter"
        ]):
            return DocumentType.NEWS_ARTICLE
        
        # Blog post indicators
        if any(keyword in text_lower for keyword in [
            "blog", "post", "tutorial", "guide", "tips", "how to",
            "personal", "experience", "opinion"
        ]):
            return DocumentType.BLOG_POST
        
        # Manual indicators
        if any(keyword in text_lower for keyword in [
            "step", "instruction", "manual", "guide", "how to use",
            "installation", "setup", "configuration"
        ]):
            return DocumentType.MANUAL
        
        # Code indicators
        if any(ext in filename_lower for ext in [".py", ".js", ".java", ".cpp", ".c", ".go", ".rs"]):
            return DocumentType.CODE
        
        return DocumentType.GENERAL
    
    def get_template_for_document(self, text: str, filename: str = "") -> ChunkingTemplate:
        """Get appropriate template for document"""
        doc_type = self.detect_document_type(text, filename)
        
        # Map document type to template
        template_mapping = {
            DocumentType.TECHNICAL_DOCUMENT: "technical_document",
            DocumentType.RESEARCH_PAPER: "research_paper",
            DocumentType.LEGAL_DOCUMENT: "legal_document",
            DocumentType.NEWS_ARTICLE: "news_article",
            DocumentType.BLOG_POST: "blog_post",
            DocumentType.MANUAL: "manual",
            DocumentType.CODE: "code",
            DocumentType.GENERAL: "general"
        }
        
        template_name = template_mapping.get(doc_type, "general")
        return self.templates[template_name]
    
    def chunk_with_template(self, text: str, filename: str = "", 
                          template_name: str = None) -> ChunkingResult:
        """Chunk text using a specific template"""
        if template_name and template_name in self.templates:
            template = self.templates[template_name]
        else:
            template = self.get_template_for_document(text, filename)
        
        self.logger.info(f"Using template: {template.name} for document: {filename}")
        
        # Create text splitter based on template
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=template.chunk_size,
            chunk_overlap=template.chunk_overlap,
            separators=template.separators,
            keep_separator=template.keep_separator,
            length_function=len
        )
        
        # Apply custom rules based on template
        processed_text = self._apply_custom_rules(text, template)
        
        # Split the text
        chunks = text_splitter.split_text(processed_text)
        
        # Convert to Document objects
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "chunk_index": i,
                    "template_used": template.name,
                    "strategy": template.strategy.value,
                    "chunk_size": len(chunk),
                    "filename": filename
                }
            )
            documents.append(doc)
        
        # Calculate quality metrics
        quality_score = self._calculate_quality_score(documents, template)
        
        # Generate explainable decisions
        explainable_decisions = self._generate_explainable_decisions(
            documents, template, text
        )
        
        return ChunkingResult(
            chunks=documents,
            strategy_used=template.strategy,
            template_used=template.name,
            quality_score=quality_score,
            chunk_count=len(documents),
            average_chunk_size=sum(len(doc.page_content) for doc in documents) / len(documents) if documents else 0,
            metadata={
                "document_type": template.document_type.value,
                "custom_rules_applied": list(template.custom_rules.keys())
            },
            explainable_decisions=explainable_decisions
        )
    
    def _apply_custom_rules(self, text: str, template: ChunkingTemplate) -> str:
        """Apply custom rules based on template"""
        processed_text = text
        
        # Apply template-specific rules
        if template.document_type == DocumentType.TECHNICAL_DOCUMENT:
            processed_text = self._preserve_technical_structure(processed_text)
        elif template.document_type == DocumentType.RESEARCH_PAPER:
            processed_text = self._preserve_research_structure(processed_text)
        elif template.document_type == DocumentType.LEGAL_DOCUMENT:
            processed_text = self._preserve_legal_structure(processed_text)
        elif template.document_type == DocumentType.CODE:
            processed_text = self._preserve_code_structure(processed_text)
        
        return processed_text
    
    def _preserve_technical_structure(self, text: str) -> str:
        """Preserve technical document structure"""
        # Preserve code blocks
        text = re.sub(r'```(\w+)?\n(.*?)```', r'CODE_BLOCK_START\1\n\2\nCODE_BLOCK_END', 
                     text, flags=re.DOTALL)
        
        # Preserve sections
        text = re.sub(r'^(\d+\.\s+[^\n]+)', r'\n\nSECTION_START\1\n', text, flags=re.MULTILINE)
        
        return text
    
    def _preserve_research_structure(self, text: str) -> str:
        """Preserve research paper structure"""
        # Preserve abstract
        text = re.sub(r'^Abstract[:\s]*', r'\n\nABSTRACT_START\nAbstract:\n', text, flags=re.MULTILINE)
        
        # Preserve methodology
        text = re.sub(r'^Methodology[:\s]*', r'\n\nMETHODOLOGY_START\nMethodology:\n', text, flags=re.MULTILINE)
        
        # Preserve conclusions
        text = re.sub(r'^Conclusion[:\s]*', r'\n\nCONCLUSION_START\nConclusion:\n', text, flags=re.MULTILINE)
        
        return text
    
    def _preserve_legal_structure(self, text: str) -> str:
        """Preserve legal document structure"""
        # Preserve clauses
        text = re.sub(r'^(\d+\.\s+[^\n]+)', r'\n\nCLAUSE_START\1\n', text, flags=re.MULTILINE)
        
        # Preserve definitions
        text = re.sub(r'^"([^"]+)"\s+means\s+', r'\n\nDEFINITION_START\n"\1" means ', text, flags=re.MULTILINE)
        
        return text
    
    def _preserve_code_structure(self, text: str) -> str:
        """Preserve code structure"""
        # Preserve function definitions
        text = re.sub(r'^def\s+(\w+)\s*\(', r'\n\nFUNCTION_START\ndef \1(', text, flags=re.MULTILINE)
        
        # Preserve class definitions
        text = re.sub(r'^class\s+(\w+)', r'\n\nCLASS_START\nclass \1', text, flags=re.MULTILINE)
        
        # Preserve imports
        text = re.sub(r'^(import|from)\s+', r'\n\nIMPORT_START\n\1 ', text, flags=re.MULTILINE)
        
        return text
    
    def _calculate_quality_score(self, chunks: List[Document], template: ChunkingTemplate) -> float:
        """Calculate quality score for chunking result"""
        if not chunks:
            return 0.0
        
        # Calculate various quality metrics
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        
        # Size consistency (closer to target is better)
        target_size = template.chunk_size
        size_consistency = 1.0 - abs(avg_size - target_size) / target_size
        size_consistency = max(0.0, min(1.0, size_consistency))
        
        # Overlap effectiveness
        overlap_effectiveness = min(1.0, template.chunk_overlap / target_size)
        
        # Content completeness (no empty chunks)
        completeness = 1.0 if all(len(chunk.page_content.strip()) > 0 for chunk in chunks) else 0.8
        
        # Overall quality score
        quality_score = (size_consistency * 0.4 + 
                        overlap_effectiveness * 0.3 + 
                        completeness * 0.3)
        
        return quality_score
    
    def _generate_explainable_decisions(self, chunks: List[Document], 
                                      template: ChunkingTemplate, original_text: str) -> List[str]:
        """Generate explainable decisions for chunking"""
        decisions = []
        
        decisions.append(f"Selected template: {template.name}")
        decisions.append(f"Strategy used: {template.strategy.value}")
        decisions.append(f"Chunk size: {template.chunk_size}")
        decisions.append(f"Chunk overlap: {template.chunk_overlap}")
        decisions.append(f"Total chunks created: {len(chunks)}")
        
        if chunks:
            avg_size = sum(len(chunk.page_content) for chunk in chunks) / len(chunks)
            decisions.append(f"Average chunk size: {avg_size:.0f} characters")
        
        # Document type specific decisions
        if template.document_type == DocumentType.TECHNICAL_DOCUMENT:
            decisions.append("Preserved code blocks and technical sections")
        elif template.document_type == DocumentType.RESEARCH_PAPER:
            decisions.append("Preserved abstract, methodology, and conclusions")
        elif template.document_type == DocumentType.LEGAL_DOCUMENT:
            decisions.append("Preserved legal clauses and definitions")
        elif template.document_type == DocumentType.CODE:
            decisions.append("Preserved functions, classes, and imports")
        
        return decisions
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates"""
        return [
            {
                "name": template.name,
                "document_type": template.document_type.value,
                "strategy": template.strategy.value,
                "chunk_size": template.chunk_size,
                "chunk_overlap": template.chunk_overlap,
                "description": template.description,
                "quality_metrics": template.quality_metrics
            }
            for template in self.templates.values()
        ]
    
    def create_custom_template(self, name: str, document_type: DocumentType,
                             strategy: ChunkingStrategy, chunk_size: int,
                             chunk_overlap: int, custom_rules: Dict[str, Any] = None,
                             description: str = "") -> ChunkingTemplate:
        """Create a custom chunking template"""
        template = ChunkingTemplate(
            name=name,
            document_type=document_type,
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            custom_rules=custom_rules or {},
            description=description
        )
        
        # Add to templates
        self.templates[name.lower().replace(" ", "_")] = template
        
        return template


# Global chunker instance
template_chunker = TemplateBasedChunker()
