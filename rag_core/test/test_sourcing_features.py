#!/usr/bin/env python3
"""
Test script for the new sourcing and document upload features.
"""

import requests
import json
import time

# Test configuration
API_BASE = "http://localhost:8000"

def test_health():
    """Test if the API is running"""
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_upload_with_document_type():
    """Test uploading a document with different document types"""
    
    # Create a simple test document
    test_content = """
    This is a test document for the RAG system.
    It contains information about artificial intelligence and machine learning.
    The document discusses various topics including:
    - Neural networks
    - Deep learning
    - Natural language processing
    - Computer vision
    """
    
    # Test default document type
    print("\n📄 Testing default document upload...")
    files = {'file': ('test_doc.txt', test_content, 'text/plain')}
    data = {'document_type': 'default'}
    
    try:
        response = requests.post(f"{API_BASE}/upload", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Default upload successful: {result.get('num_chunks')} chunks")
            print(f"   Document type: {result.get('document_type')}")
        else:
            print(f"❌ Default upload failed: {response.text}")
    except Exception as e:
        print(f"❌ Default upload error: {e}")
    
    # Test master document type
    print("\n📋 Testing master document upload...")
    files = {'file': ('test_master.txt', test_content, 'text/plain')}
    data = {'document_type': 'master_document'}
    
    try:
        response = requests.post(f"{API_BASE}/upload", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Master document upload successful: {result.get('num_chunks')} chunks")
            print(f"   Document type: {result.get('document_type')}")
        else:
            print(f"❌ Master document upload failed: {response.text}")
    except Exception as e:
        print(f"❌ Master document upload error: {e}")

def test_query_with_sources():
    """Test querying with source information"""
    
    print("\n🔍 Testing query with source information...")
    
    # Wait a moment for embeddings to be ready
    time.sleep(2)
    
    data = {
        'question': 'What topics are discussed in the documents?',
        'n_results': 3,
        'expand': 2,
        'conversation_history': '[]'
    }
    
    try:
        response = requests.post(f"{API_BASE}/query", data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful")
            print(f"   Answer length: {len(result.get('answer', ''))}")
            print(f"   Sources count: {len(result.get('sources', []))}")
            print(f"   Detailed sources count: {len(result.get('detailed_sources', []))}")
            
            # Show detailed sources
            detailed_sources = result.get('detailed_sources', [])
            if detailed_sources:
                print(f"\n📚 Detailed Sources:")
                for i, source in enumerate(detailed_sources[:2]):  # Show first 2 sources
                    print(f"   Source {i+1}:")
                    print(f"     Filename: {source.get('filename', 'Unknown')}")
                    print(f"     Document type: {source.get('document_type', 'default')}")
                    print(f"     Is master: {source.get('is_master', False)}")
                    print(f"     Confidence: {source.get('confidence', 0):.2f}")
                    print(f"     Content preview: {source.get('content', '')[:100]}...")
        else:
            print(f"❌ Query failed: {response.text}")
    except Exception as e:
        print(f"❌ Query error: {e}")

def test_documents_list():
    """Test listing documents to see document types"""
    
    print("\n📋 Testing documents list...")
    
    try:
        response = requests.get(f"{API_BASE}/documents")
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            print(f"✅ Found {len(documents)} documents:")
            for doc in documents:
                print(f"   - {doc.get('filename', 'Unknown')}: {doc.get('count', 0)} chunks")
        else:
            print(f"❌ Documents list failed: {response.text}")
    except Exception as e:
        print(f"❌ Documents list error: {e}")

def main():
    """Run all tests"""
    print("🧪 Testing RAG Sourcing and Document Upload Features")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("❌ API not available, stopping tests")
        return
    
    # Test uploads
    test_upload_with_document_type()
    
    # Test documents list
    test_documents_list()
    
    # Test querying
    test_query_with_sources()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main() 