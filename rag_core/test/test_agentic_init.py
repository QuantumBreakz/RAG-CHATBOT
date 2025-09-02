#!/usr/bin/env python3

import traceback
import sys

def test_agentic_init():
    try:
        from rag_core.agentic_rag import AgenticRAG
        print("AgenticRAG imported successfully")
        
        # Test initialization
        agentic = AgenticRAG()
        print("AgenticRAG initialized successfully")
        
        # Test basic functionality
        print("Testing basic methods...")
        sources = agentic._get_available_sources()
        print(f"Available sources: {sources}")
        
        return True
        
    except Exception as e:
        print("Initialization failed:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agentic_init()
    sys.exit(0 if success else 1) 