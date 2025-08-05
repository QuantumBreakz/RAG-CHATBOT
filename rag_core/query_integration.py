"""
Integration script to use the fixed query handler with anti-hallucination measures

This replaces the problematic query endpoints with validated, safe implementations.
"""

from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse
import json
from rag_core.fixed_query_handler import process_query_fixed
import logging

logger = logging.getLogger(__name__)

def add_fixed_endpoints(app: FastAPI):
    """Add the fixed query endpoints to the FastAPI app"""
    
    @app.post("/query/fixed")
    async def query_rag_fixed(
        question: str = Form(...),
        n_results: int = Form(3),
        expand: int = Form(2),
        filename: str = Form(None),
        domain_filter: str = Form(None),
        conversation_history: str = Form("[]"),
        session_id: str = Form(None)
    ):
        """
        Fixed query endpoint with anti-hallucination measures
        
        This endpoint implements strict validation to prevent hallucinations:
        - Higher confidence thresholds (0.7 vs 0.3)
        - Relevance validation for all chunks
        - Bounded context creation
        - Response validation
        """
        
        result = await process_query_fixed(
            question=question,
            n_results=n_results,
            expand=expand,
            filename=filename,
            domain_filter=domain_filter,
            conversation_history=conversation_history,
            session_id=session_id
        )
        
        return result
    
    @app.post("/query/stream/fixed")
    async def query_rag_stream_fixed(
        question: str = Form(...),
        n_results: int = Form(3),
        expand: int = Form(2),
        filename: str = Form(None),
        domain_filter: str = Form(None),
        conversation_history: str = Form("[]"),
        session_id: str = Form(None)
    ):
        """
        Fixed streaming query endpoint with anti-hallucination measures
        """
        
        async def stream_fixed_response():
            try:
                result = await process_query_fixed(
                    question=question,
                    n_results=n_results,
                    expand=expand,
                    filename=filename,
                    domain_filter=domain_filter,
                    conversation_history=conversation_history,
                    session_id=session_id
                )
                
                # Stream the complete result
                yield json.dumps(result)
                
            except Exception as e:
                logger.error(f"Fixed streaming query failed: {str(e)}")
                error_result = {
                    "answer": f"Error processing query: {str(e)}",
                    "context": "",
                    "status": "error",
                    "sources": [],
                    "context_metadata": {"error": str(e)}
                }
                yield json.dumps(error_result)
        
        return StreamingResponse(
            stream_fixed_response(),
            media_type="application/json"
        )

# Usage example:
# from rag_core.query_integration import add_fixed_endpoints
# add_fixed_endpoints(app)
