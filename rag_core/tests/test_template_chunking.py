"""
Test suite for Template-Based Chunking System
Tests intelligent chunking strategies, document type detection, and quality metrics
"""

import pytest
import json
from typing import List, Dict, Any

from rag_core.chunking_templates import (
    TemplateBasedChunker, ChunkingTemplate, ChunkingResult,
    ChunkingStrategy, DocumentType
)


class TestTemplateBasedChunker:
    """Test the template-based chunking system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.chunker = TemplateBasedChunker()
    
    def test_initialization(self):
        """Test TemplateBasedChunker initialization"""
        assert self.chunker is not None
        assert hasattr(self.chunker, 'templates')
        assert len(self.chunker.templates) > 0
    
    def test_detect_document_type_technical(self):
        """Test document type detection for technical documents"""
        text = """
        API Documentation
        This document describes the REST API endpoints.
        
        Function: getUser(id)
        Returns user information for the given ID.
        
        Method: POST /api/users
        Creates a new user in the system.
        """
        
        doc_type = self.chunker.detect_document_type(text, "api_docs.md")
        assert doc_type == DocumentType.TECHNICAL_DOCUMENT
    
    def test_detect_document_type_research(self):
        """Test document type detection for research papers"""
        text = """
        Abstract
        This study examines the effects of machine learning on document processing.
        
        Introduction
        Machine learning has revolutionized many fields...
        
        Methodology
        We conducted experiments using various algorithms...
        
        Conclusion
        Our results show significant improvements...
        
        References
        1. Smith, J. (2023). Machine Learning Applications.
        """
        
        doc_type = self.chunker.detect_document_type(text, "research_paper.pdf")
        assert doc_type == DocumentType.RESEARCH_PAPER
    
    def test_detect_document_type_legal(self):
        """Test document type detection for legal documents"""
        text = """
        AGREEMENT
        
        WHEREAS, Party A and Party B wish to enter into an agreement;
        
        NOW, THEREFORE, the parties hereby agree as follows:
        
        1. Definitions
        "Service" means the software platform provided by Party A.
        
        2. Terms and Conditions
        Party A shall provide the Service to Party B...
        """
        
        doc_type = self.chunker.detect_document_type(text, "contract.pdf")
        assert doc_type == DocumentType.LEGAL_DOCUMENT
    
    def test_detect_document_type_code(self):
        """Test document type detection for code files"""
        text = """
        import json
        from typing import List, Dict
        
        class UserService:
            def __init__(self):
                self.users = []
            
            def get_user(self, user_id: int) -> Dict:
                return next((u for u in self.users if u['id'] == user_id), None)
            
            def create_user(self, user_data: Dict) -> Dict:
                user = {'id': len(self.users) + 1, **user_data}
                self.users.append(user)
                return user
        """
        
        doc_type = self.chunker.detect_document_type(text, "user_service.py")
        assert doc_type == DocumentType.CODE
    
    def test_get_template_for_document(self):
        """Test getting appropriate template for document"""
        text = "This is a technical API documentation with code examples."
        
        template = self.chunker.get_template_for_document(text, "api_docs.md")
        
        assert isinstance(template, ChunkingTemplate)
        assert template.document_type == DocumentType.TECHNICAL_DOCUMENT
        assert template.name == "Technical Document"
    
    def test_chunk_with_template_technical(self):
        """Test chunking with technical document template"""
        text = """
        API Documentation
        
        ## Authentication
        All API requests require authentication using API keys.
        
        ## Endpoints
        
        ### GET /users
        Retrieves a list of users.
        
        ```json
        {
          "users": [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "Jane Smith"}
          ]
        }
        ```
        
        ### POST /users
        Creates a new user.
        
        ```json
        {
          "name": "New User",
          "email": "user@example.com"
        }
        ```
        """
        
        result = self.chunker.chunk_with_template(text, "api_docs.md")
        
        assert isinstance(result, ChunkingResult)
        assert result.template_used == "Technical Document"
        assert result.strategy_used == ChunkingStrategy.STRUCTURAL
        assert result.chunk_count > 0
        assert 0 <= result.quality_score <= 1
        assert len(result.explainable_decisions) > 0
    
    def test_chunk_with_template_research(self):
        """Test chunking with research paper template"""
        text = """
        Abstract
        This paper presents a novel approach to document processing using machine learning techniques.
        
        Introduction
        Document processing has become increasingly important in the digital age...
        
        Methodology
        We implemented a neural network architecture based on transformer models...
        
        Results
        Our experiments show a 15% improvement in accuracy compared to baseline methods...
        
        Conclusion
        The proposed approach demonstrates significant improvements in document processing tasks.
        
        References
        1. Vaswani, A. et al. (2017). Attention is all you need.
        2. Devlin, J. et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers.
        """
        
        result = self.chunker.chunk_with_template(text, "research_paper.pdf")
        
        assert isinstance(result, ChunkingResult)
        assert result.template_used == "Research Paper"
        assert result.strategy_used == ChunkingStrategy.SEMANTIC
        assert result.chunk_count > 0
        assert 0 <= result.quality_score <= 1
    
    def test_chunk_with_template_legal(self):
        """Test chunking with legal document template"""
        text = """
        SOFTWARE LICENSE AGREEMENT
        
        WHEREAS, Licensor owns certain software technology;
        WHEREAS, Licensee desires to use the software;
        
        NOW, THEREFORE, the parties agree as follows:
        
        1. Definitions
        "Software" means the computer program known as "ExampleApp".
        "License" means the right to use the Software.
        
        2. Grant of License
        Licensor hereby grants to Licensee a non-exclusive license to use the Software.
        
        3. Restrictions
        Licensee shall not reverse engineer, decompile, or disassemble the Software.
        """
        
        result = self.chunker.chunk_with_template(text, "license_agreement.pdf")
        
        assert isinstance(result, ChunkingResult)
        assert result.template_used == "Legal Document"
        assert result.strategy_used == ChunkingStrategy.STRUCTURAL
        assert result.chunk_count > 0
        assert 0 <= result.quality_score <= 1
    
    def test_chunk_with_template_code(self):
        """Test chunking with code template"""
        text = """
        import requests
        from typing import Dict, List
        
        class APIClient:
            def __init__(self, base_url: str):
                self.base_url = base_url
                self.session = requests.Session()
            
            def get_users(self) -> List[Dict]:
                response = self.session.get(f"{self.base_url}/users")
                return response.json()
            
            def create_user(self, user_data: Dict) -> Dict:
                response = self.session.post(f"{self.base_url}/users", json=user_data)
                return response.json()
        
        # Usage example
        client = APIClient("https://api.example.com")
        users = client.get_users()
        """
        
        result = self.chunker.chunk_with_template(text, "api_client.py")
        
        assert isinstance(result, ChunkingResult)
        assert result.template_used == "Code"
        assert result.strategy_used == ChunkingStrategy.STRUCTURAL
        assert result.chunk_count > 0
        assert 0 <= result.quality_score <= 1
    
    def test_preserve_technical_structure(self):
        """Test preservation of technical document structure"""
        text = """
        # API Documentation
        
        ## Authentication
        Use API keys for authentication.
        
        ```python
        import requests
        headers = {'Authorization': 'Bearer YOUR_API_KEY'}
        ```
        
        ## Endpoints
        
        1. GET /users
        Returns list of users.
        
        2. POST /users
        Creates new user.
        """
        
        processed = self.chunker._preserve_technical_structure(text)
        
        assert "CODE_BLOCK_START" in processed
        assert "SECTION_START" in processed
        assert "```python" not in processed  # Should be replaced
    
    def test_preserve_research_structure(self):
        """Test preservation of research paper structure"""
        text = """
        Abstract
        This study examines machine learning applications.
        
        Methodology
        We used neural networks for classification.
        
        Conclusion
        Results show significant improvements.
        """
        
        processed = self.chunker._preserve_research_structure(text)
        
        assert "ABSTRACT_START" in processed
        assert "METHODOLOGY_START" in processed
        assert "CONCLUSION_START" in processed
    
    def test_preserve_legal_structure(self):
        """Test preservation of legal document structure"""
        text = """
        1. Definitions
        "Service" means the software platform.
        
        2. Terms
        Party A shall provide the Service.
        
        "User" means any person using the Service.
        """
        
        processed = self.chunker._preserve_legal_structure(text)
        
        assert "CLAUSE_START" in processed
        assert "DEFINITION_START" in processed
    
    def test_preserve_code_structure(self):
        """Test preservation of code structure"""
        text = """
        import json
        
        class UserService:
            def __init__(self):
                self.users = []
            
            def get_user(self, user_id):
                return next((u for u in self.users if u['id'] == user_id), None)
        """
        
        processed = self.chunker._preserve_code_structure(text)
        
        assert "IMPORT_START" in processed
        assert "CLASS_START" in processed
        assert "FUNCTION_START" in processed
    
    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        from langchain_core.documents import Document
        
        # Create test chunks
        chunks = [
            Document(page_content="This is a test chunk with some content."),
            Document(page_content="Another test chunk with different content."),
            Document(page_content="A third chunk to test quality scoring.")
        ]
        
        template = self.chunker.templates["technical_document"]
        quality_score = self.chunker._calculate_quality_score(chunks, template)
        
        assert 0 <= quality_score <= 1
    
    def test_generate_explainable_decisions(self):
        """Test generation of explainable decisions"""
        from langchain_core.documents import Document
        
        chunks = [
            Document(page_content="Test chunk 1"),
            Document(page_content="Test chunk 2")
        ]
        
        template = self.chunker.templates["technical_document"]
        decisions = self.chunker._generate_explainable_decisions(chunks, template, "test content")
        
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert "Selected template" in decisions[0]
        assert "Strategy used" in decisions[1]
    
    def test_get_available_templates(self):
        """Test getting available templates"""
        templates = self.chunker.get_available_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check template structure
        template = templates[0]
        assert "name" in template
        assert "document_type" in template
        assert "strategy" in template
        assert "chunk_size" in template
        assert "chunk_overlap" in template
        assert "description" in template
        assert "quality_metrics" in template
    
    def test_create_custom_template(self):
        """Test creating custom template"""
        custom_template = self.chunker.create_custom_template(
            name="Custom Template",
            document_type=DocumentType.GENERAL,
            strategy=ChunkingStrategy.ADAPTIVE,
            chunk_size=1500,
            chunk_overlap=150,
            custom_rules={"preserve_sections": True},
            description="A custom template for testing"
        )
        
        assert isinstance(custom_template, ChunkingTemplate)
        assert custom_template.name == "Custom Template"
        assert custom_template.document_type == DocumentType.GENERAL
        assert custom_template.strategy == ChunkingStrategy.ADAPTIVE
        assert custom_template.chunk_size == 1500
        assert custom_template.chunk_overlap == 150
        assert "preserve_sections" in custom_template.custom_rules
    
    def test_chunk_with_specific_template(self):
        """Test chunking with a specific template name"""
        text = "This is a test document with some content to chunk."
        
        result = self.chunker.chunk_with_template(
            text=text,
            filename="test.txt",
            template_name="general"
        )
        
        assert isinstance(result, ChunkingResult)
        assert result.template_used == "General"
        assert result.chunk_count > 0
    
    def test_chunk_with_invalid_template(self):
        """Test chunking with invalid template name (should fallback to detection)"""
        text = "This is a technical API documentation with code examples."
        
        result = self.chunker.chunk_with_template(
            text=text,
            filename="api_docs.md",
            template_name="invalid_template"
        )
        
        assert isinstance(result, ChunkingResult)
        # Should detect technical document and use technical template
        assert result.template_used == "Technical Document"
    
    def test_empty_text_chunking(self):
        """Test chunking with empty text"""
        result = self.chunker.chunk_with_template("", "empty.txt")
        
        assert isinstance(result, ChunkingResult)
        assert result.chunk_count == 0
        assert result.quality_score == 0.0
    
    def test_very_long_text_chunking(self):
        """Test chunking with very long text"""
        long_text = "This is a very long text. " * 1000  # ~25,000 characters
        
        result = self.chunker.chunk_with_template(long_text, "long_document.txt")
        
        assert isinstance(result, ChunkingResult)
        assert result.chunk_count > 0
        assert result.average_chunk_size > 0
        assert 0 <= result.quality_score <= 1


class TestChunkingTemplates:
    """Test chunking template data structures"""
    
    def test_chunking_template_creation(self):
        """Test creating a chunking template"""
        template = ChunkingTemplate(
            name="Test Template",
            document_type=DocumentType.GENERAL,
            strategy=ChunkingStrategy.ADAPTIVE,
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True,
            is_recursive=True,
            custom_rules={"test_rule": True},
            quality_metrics={"coherence": 0.8},
            description="A test template"
        )
        
        assert template.name == "Test Template"
        assert template.document_type == DocumentType.GENERAL
        assert template.strategy == ChunkingStrategy.ADAPTIVE
        assert template.chunk_size == 2000
        assert template.chunk_overlap == 200
        assert "test_rule" in template.custom_rules
        assert template.quality_metrics["coherence"] == 0.8
    
    def test_chunking_result_creation(self):
        """Test creating a chunking result"""
        from langchain_core.documents import Document
        
        chunks = [
            Document(page_content="Test chunk 1"),
            Document(page_content="Test chunk 2")
        ]
        
        result = ChunkingResult(
            chunks=chunks,
            strategy_used=ChunkingStrategy.STRUCTURAL,
            template_used="Test Template",
            quality_score=0.85,
            chunk_count=2,
            average_chunk_size=12.0,
            metadata={"test": "value"},
            explainable_decisions=["Decision 1", "Decision 2"]
        )
        
        assert result.chunks == chunks
        assert result.strategy_used == ChunkingStrategy.STRUCTURAL
        assert result.template_used == "Test Template"
        assert result.quality_score == 0.85
        assert result.chunk_count == 2
        assert result.average_chunk_size == 12.0
        assert result.metadata["test"] == "value"
        assert len(result.explainable_decisions) == 2


class TestChunkingEnums:
    """Test chunking enums"""
    
    def test_chunking_strategy_enum(self):
        """Test ChunkingStrategy enum"""
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.STRUCTURAL.value == "structural"
        assert ChunkingStrategy.HYBRID.value == "hybrid"
        assert ChunkingStrategy.ADAPTIVE.value == "adaptive"
        assert ChunkingStrategy.FIXED_SIZE.value == "fixed_size"
        assert ChunkingStrategy.CONTENT_AWARE.value == "content_aware"
    
    def test_document_type_enum(self):
        """Test DocumentType enum"""
        assert DocumentType.TECHNICAL_DOCUMENT.value == "technical_document"
        assert DocumentType.RESEARCH_PAPER.value == "research_paper"
        assert DocumentType.LEGAL_DOCUMENT.value == "legal_document"
        assert DocumentType.NEWS_ARTICLE.value == "news_article"
        assert DocumentType.BLOG_POST.value == "blog_post"
        assert DocumentType.MANUAL.value == "manual"
        assert DocumentType.CODE.value == "code"
        assert DocumentType.GENERAL.value == "general"


def test_template_chunking_imports():
    """Test that all template chunking components can be imported"""
    from rag_core.chunking_templates import (
        TemplateBasedChunker, ChunkingTemplate, ChunkingResult,
        ChunkingStrategy, DocumentType, template_chunker
    )
    
    assert TemplateBasedChunker is not None
    assert ChunkingTemplate is not None
    assert ChunkingResult is not None
    assert ChunkingStrategy is not None
    assert DocumentType is not None
    assert template_chunker is not None


def test_template_chunking_integration():
    """Test integration with document processing"""
    from rag_core.document import DocumentProcessor
    
    # Test that template chunking can be used in document processing
    processor = DocumentProcessor()
    
    # Create a simple test document
    test_content = b"This is a test document with some content."
    
    # Process with template chunking enabled
    chunks = DocumentProcessor.process_document(
        file_content=test_content,
        filename="test.txt",
        use_template_chunking=True
    )
    
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    
    # Check that template chunking metadata is present
    for chunk in chunks:
        assert "template_chunking_used" in chunk.metadata
        assert chunk.metadata["template_chunking_used"] is True
        assert "template_used" in chunk.metadata
        assert "strategy_used" in chunk.metadata
        assert "quality_score" in chunk.metadata
