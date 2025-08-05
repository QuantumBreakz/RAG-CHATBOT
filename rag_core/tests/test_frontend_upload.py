#!/usr/bin/env python3
"""
Test script to simulate frontend upload process and identify issues.
"""

import requests
import os

def test_frontend_upload_simulation():
    """Simulate the exact frontend upload process"""
    try:
        # Create a test file like the frontend would
        test_content = "This is a test document for frontend upload simulation."
        test_filename = "frontend_test.txt"
        
        with open(test_filename, 'w') as f:
            f.write(test_content)
        
        # Simulate the exact frontend upload process
        with open(test_filename, 'rb') as f:
            files = {'file': (test_filename, f, 'text/plain')}
            data = {
                'chunk_size': '1000',
                'chunk_overlap': '200',
                'document_type': 'default'
            }
            
            # Test both endpoints: direct backend and through frontend proxy
            print("🔍 Testing direct backend upload...")
            response = requests.post('http://localhost:8000/upload', files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Direct backend upload successful: {result}")
            else:
                print(f"❌ Direct backend upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        
        # Test through frontend proxy
        print("\n🔍 Testing frontend proxy upload...")
        with open(test_filename, 'rb') as f:
            files = {'file': (test_filename, f, 'text/plain')}
            data = {
                'chunk_size': '1000',
                'chunk_overlap': '200',
                'document_type': 'default'
            }
            
            response = requests.post('http://localhost:5173/api/upload', files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Frontend proxy upload successful: {result}")
            else:
                print(f"❌ Frontend proxy upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        
        # Check if documents are now listed
        print("\n🔍 Checking documents list after upload...")
        response = requests.get('http://localhost:8000/documents', timeout=5)
        if response.status_code == 200:
            docs = response.json()
            print(f"📄 Documents after upload: {docs}")
            
            if docs.get('documents') and len(docs['documents']) > 0:
                print("✅ Documents are now listed!")
                return True
            else:
                print("❌ Documents still not listed after upload")
                return False
        else:
            print(f"❌ Failed to get documents list: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in frontend upload simulation: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

def test_browser_console_errors():
    """Check for common browser console errors"""
    print("\n🔍 Common browser console errors to check:")
    print("1. CORS errors - Check if frontend can access backend")
    print("2. Network errors - Check if upload requests are being sent")
    print("3. JavaScript errors - Check for syntax errors in frontend")
    print("4. Proxy errors - Check if Vite proxy is working")
    
    # Test CORS
    try:
        response = requests.get('http://localhost:8000/health', headers={'Origin': 'http://localhost:5173'})
        if response.status_code == 200:
            print("✅ CORS appears to be working")
        else:
            print("❌ CORS may have issues")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")

def main():
    """Run frontend upload tests"""
    print("🔍 Testing Frontend Upload Process")
    print("=" * 50)
    
    success = test_frontend_upload_simulation()
    
    if success:
        print("\n✅ Frontend upload process is working!")
        print("   The issue might be in the browser or frontend JavaScript.")
    else:
        print("\n❌ Frontend upload process has issues")
        print("   Check the specific error messages above.")
    
    test_browser_console_errors()
    
    print("\n🔧 Next steps:")
    print("1. Open browser developer tools (F12)")
    print("2. Go to Console tab")
    print("3. Try uploading a document through the frontend")
    print("4. Check for any error messages in the console")
    print("5. Go to Network tab to see if upload requests are being sent")

if __name__ == "__main__":
    main() 