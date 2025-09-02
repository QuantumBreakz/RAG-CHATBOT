#!/usr/bin/env python3
"""
Test script to check OpenAI provider status
"""

import os
from rag_core.online_llm import online_llm_handler

def test_openai_status():
    """Test OpenAI provider status"""
    
    print("🔍 Testing OpenAI Provider Status")
    print("=" * 50)
    
    # Check environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"📋 OPENAI_API_KEY set: {'Yes' if openai_key else 'No'}")
    if openai_key:
        print(f"   Key length: {len(openai_key)} characters")
        print(f"   Key preview: {openai_key[:10]}...")
    else:
        print("   ⚠️  OPENAI_API_KEY not found in environment variables")
    
    # Check available providers
    available_providers = online_llm_handler.get_available_providers()
    print(f"📋 Available providers: {available_providers}")
    
    # Check if OpenAI is available
    if "openai" in available_providers:
        print("   ✅ OpenAI provider is available")
        
        # Test connection
        print("🔧 Testing OpenAI connection...")
        if online_llm_handler.test_provider("openai"):
            print("   ✅ OpenAI connection successful")
        else:
            print("   ❌ OpenAI connection failed")
    else:
        print("   ❌ OpenAI provider is NOT available")
        print("   💡 This means the OPENAI_API_KEY environment variable is not set")
    
    # Check current provider
    print(f"📋 Current provider: {online_llm_handler.current_provider}")
    
    print("\n" + "=" * 50)
    print("💡 To fix this issue:")
    print("1. Add OPENAI_API_KEY=your_api_key_here to your .env file")
    print("2. Restart the server")
    print("3. The OpenAI provider should then be available")

if __name__ == "__main__":
    test_openai_status()
