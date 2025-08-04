"""
RAG Core Package

This package contains the core RAG (Retrieval-Augmented Generation) functionality
including document processing, OCR, vector storage, conversation management,
and the new agentic RAG system.
"""

# Core modules
from . import config
from . import document
from . import vectorstore
from . import llm
from . import search
from . import conversation_manager
from . import context_manager
from . import cache
from . import utils
from . import ui

# OCR modules
from . import ocr
from . import multi_ocr
from . import ocr_config
from . import ocr_quality

# Agentic RAG modules
from . import agentic_rag

# Test modules (if available)
try:
    from . import tests
except ImportError:
    pass

__version__ = "2.0.0"
__author__ = "RAG Chatbot Team"

# Main exports
__all__ = [
    "config",
    "document", 
    "vectorstore",
    "llm",
    "search",
    "conversation_manager",
    "context_manager",
    "cache",
    "utils",
    "ui",
    "ocr",
    "multi_ocr",
    "ocr_config",
    "ocr_quality",
    "agentic_rag"
] 