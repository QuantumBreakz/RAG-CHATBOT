#!/usr/bin/env python3
"""
Test to debug the reset KB functionality
"""

import requests
import json

def test_reset_kb():
    """Test the reset KB functionality"""
    print("🔍 Testing Reset KB Functionality")
    print("=" * 40)
    
    # Check if backend is running
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend is not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Check current documents
    try:
        response = requests.get('http://localhost:8000/documents', timeout=10)
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            print(f"📋 Current documents: {len(documents)}")
            for doc in documents:
                print(f"   - {doc.get('filename', 'unknown')}")
        else:
            print(f"❌ Failed to get documents: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
    
    # Test reset KB endpoint
    print("\n🔄 Testing Reset KB Endpoint")
    try:
        response = requests.post('http://localhost:8000/reset_kb', timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Reset KB successful")
        else:
            print("❌ Reset KB failed")
            
    except Exception as e:
        print(f"❌ Error calling reset KB: {e}")
    
    # Check documents after reset
    print("\n📋 Checking documents after reset")
    try:
        response = requests.get('http://localhost:8000/documents', timeout=10)
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            print(f"   Documents after reset: {len(documents)}")
            if len(documents) == 0:
                print("✅ Knowledge base successfully cleared")
            else:
                print("❌ Knowledge base not cleared")
                for doc in documents:
                    print(f"   - {doc.get('filename', 'unknown')}")
        else:
            print(f"❌ Failed to get documents after reset: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting documents after reset: {e}")

def test_vectorstore_health():
    """Test vectorstore health"""
    print("\n🔍 Testing Vectorstore Health")
    print("=" * 40)
    
    try:
        response = requests.get('http://localhost:8000/vectorstore/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Collection exists: {data.get('collection_exists', False)}")
            print(f"   Document count: {data.get('document_count', 0)}")
        else:
            print(f"❌ Vectorstore health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking vectorstore health: {e}")

def test_reset_kb_with_error_handling():
    """Test reset KB with detailed error handling"""
    print("\n🔍 Testing Reset KB with Error Handling")
    print("=" * 40)
    
    try:
        # Test the exact endpoint the frontend calls
        response = requests.post('http://localhost:8000/reset_kb', timeout=30)
        
        print(f"   Request URL: http://localhost:8000/reset_kb")
        print(f"   Method: POST")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response JSON: {json.dumps(data, indent=2)}")
            except:
                print("   Response is not JSON")
        else:
            print("   Request failed")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Run all tests"""
    print("🔍 Reset KB Debugging Test")
    print("=" * 50)
    
    test_reset_kb()
    test_vectorstore_health()
    test_reset_kb_with_error_handling()
    
    print("\n📋 Summary:")
    print("✅ Backend connectivity test")
    print("✅ Document listing test")
    print("✅ Reset KB endpoint test")
    print("✅ Vectorstore health test")
    print("✅ Error handling test")

if __name__ == "__main__":
    main() 