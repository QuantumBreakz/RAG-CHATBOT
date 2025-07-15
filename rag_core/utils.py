# Utility functions for the RAG app

def sanitize_input(text: str) -> str:
    """Sanitize input to prevent injection attacks and strip whitespace."""
    return text.replace("<", "&lt;").replace(">", "&gt;").strip() 