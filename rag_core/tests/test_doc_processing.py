#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from rag_core.document import DocumentProcessor

def test_document_processing():
    """Test document processing with the test PDF"""
    try:
        # Read the test document
        with open('test_document.pdf', 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Process the document
        docs = DocumentProcessor.process_document(file_content, 'test_document.pdf')
        
        print(f"Processed {len(docs)} documents")
        
        for i, doc in enumerate(docs):
            print(f"Document {i}:")
            print(f"  Content length: {len(doc.page_content)} chars")
            print(f"  Content preview: {doc.page_content[:200]}...")
            print(f"  Metadata: {doc.metadata}")
            print()
        
        return docs
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_document_processing() 