# app.py
"""
Entry point for the PITB RAG Application.
Delegates all UI and workflow logic to rag_core.ui.main().
"""

from rag_core.ui import main
import sys

# --- Startup Health Checks ---
def check_ollama_model():
    try:
        import requests
        from rag_core.config import OLLAMA_BASE_URL, OLLAMA_LLM_MODEL
        # Check Ollama server health
        health_url = f"{OLLAMA_BASE_URL}/api/tags"
        resp = requests.get(health_url, timeout=5)
        if resp.status_code != 200:
            print(f"[ERROR] Ollama server not healthy at {OLLAMA_BASE_URL}")
            sys.exit(1)
        # Check if model is available
        tags = resp.json().get("models", [])
        if not any(m.get("name", "") == OLLAMA_LLM_MODEL for m in tags):
            print(f"[ERROR] Ollama model '{OLLAMA_LLM_MODEL}' not found on server {OLLAMA_BASE_URL}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Could not connect to Ollama server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_ollama_model()
    main()