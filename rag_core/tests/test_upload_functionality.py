#!/usr/bin/env python3
"""
Test script to diagnose upload functionality issues.
This script will test the backend API endpoints and identify why documents aren't being uploaded.
"""

import requests
import json
import time
import os

def test_backend_health():
    """Test if the backend is running and accessible"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running. Please start it with:")
        print("   python app.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False

def test_vectorstore_health():
    """Test if the vectorstore is working"""
    try:
        response = requests.get('http://localhost:8000/vectorstore/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Vectorstore is healthy: {data}")
            return True
        else:
            print(f"❌ Vectorstore health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking vectorstore health: {e}")
        return False

def test_upload_endpoint():
    """Test the upload endpoint with a simple text file"""
    try:
        # Create a test file
        test_content = "This is a test document for upload functionality testing."
        test_filename = "test_upload.txt"
        
        with open(test_filename, 'w') as f:
            f.write(test_content)
        
        # Test upload
        with open(test_filename, 'rb') as f:
            files = {'file': (test_filename, f, 'text/plain')}
            data = {
                'chunk_size': '1000',
                'chunk_overlap': '200',
                'document_type': 'default'
            }
            
            response = requests.post('http://localhost:8000/upload', files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful: {result}")
                return True
            else:
                print(f"❌ Upload failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing upload: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

def test_documents_list():
    """Test if documents are being listed correctly"""
    try:
        response = requests.get('http://localhost:8000/documents', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Documents list: {data}")
            return True
        else:
            print(f"❌ Failed to get documents list: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting documents list: {e}")
        return False

def test_frontend_proxy():
    """Test if the frontend proxy is working"""
    try:
        # Test the proxy through frontend URL
        response = requests.get('http://localhost:5173/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Frontend proxy is working")
            return True
        else:
            print(f"❌ Frontend proxy failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not running. Please start it with:")
        print("   cd frontend && npm run dev")
        return False
    except Exception as e:
        print(f"❌ Error testing frontend proxy: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing Upload Functionality")
    print("=" * 50)
    
    # Test backend health
    backend_ok = test_backend_health()
    if not backend_ok:
        print("\n❌ Backend is not accessible. Please start the backend first.")
        return
    
    # Test vectorstore health
    vectorstore_ok = test_vectorstore_health()
    if not vectorstore_ok:
        print("\n⚠️  Vectorstore may have issues. Check ChromaDB setup.")
    
    # Test upload functionality
    upload_ok = test_upload_endpoint()
    if not upload_ok:
        print("\n❌ Upload functionality is broken. Check the logs above.")
    
    # Test documents list
    documents_ok = test_documents_list()
    if not documents_ok:
        print("\n❌ Documents listing is broken.")
    
    # Test frontend proxy
    frontend_ok = test_frontend_proxy()
    if not frontend_ok:
        print("\n⚠️  Frontend proxy may have issues.")
    
    print("\n📋 Summary:")
    if backend_ok and upload_ok and documents_ok:
        print("✅ Upload functionality appears to be working")
        print("   - Backend is running")
        print("   - Upload endpoint is accessible")
        print("   - Documents can be listed")
        if vectorstore_ok:
            print("   - Vectorstore is healthy")
        else:
            print("   - ⚠️  Vectorstore may have issues")
        if frontend_ok:
            print("   - Frontend proxy is working")
        else:
            print("   - ⚠️  Frontend proxy may have issues")
    else:
        print("❌ Upload functionality has issues")
        print("   Check the specific error messages above")
    
    print("\n🔧 Troubleshooting steps:")
    print("1. Ensure backend is running: python app.py")
    print("2. Ensure frontend is running: cd frontend && npm run dev")
    print("3. Check ChromaDB is properly initialized")
    print("4. Check browser console for frontend errors")
    print("5. Check backend logs for detailed error messages")

if __name__ == "__main__":
    main() 