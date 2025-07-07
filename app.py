# app.py
"""
Entry point for the PITB RAG Application.
Delegates all UI and workflow logic to rag_core.ui.main().
"""

from rag_core.ui import main

if __name__ == "__main__":
    main()