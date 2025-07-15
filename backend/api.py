from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from rag_core.document import DocumentProcessor
from rag_core.vectorstore import VectorStore
from rag_core.llm import LLMHandler
from rag_core import history
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/test_vectorstore")
def test_vectorstore():
    """Test if vector stosre can be initialized and Ollama is working."""
    try:
        collection = VectorStore.get_vector_collection()
        if collection:
            return {"status": "ok", "message": "Vector store initialized successfully"}
        else:
            return {"status": "error", "message": "Failed to initialize vector store"}
    except Exception as e:
        return {"status": "error", "message": f"Vector store error: {str(e)}"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_bytes = await file.read()
    docs = DocumentProcessor.process_document(file, file_bytes)
    
    # Add documents to vector store with embeddings
    if docs:
        try:
            success = VectorStore.add_to_vector_collection(docs, file.filename)
            if success:
                return {"num_chunks": len(docs), "status": "uploaded and embedded"}
            else:
                return {"num_chunks": len(docs), "status": "uploaded but embedding failed"}
        except Exception as e:
            return {"num_chunks": len(docs), "status": f"uploaded but embedding error: {str(e)}"}
    else:
        return {"num_chunks": 0, "status": "no documents processed"}

@app.post("/query")
async def query_rag(
    question: str = Form(...),
    n_results: int = Form(3),
    expand: int = Form(2),
    filename: str = Form(None),
    conversation_history: str = Form("[]")
):
    """Enhanced query endpoint with streaming support and conversation history."""
    try:
        # Parse conversation history
        try:
            history_list = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history_list = []
        
        # Query vector store
        results = VectorStore.query_with_expanded_context(
            question, 
            n_results=n_results, 
            expand=expand,
            filename=filename
        )
        
        context_docs = results.get("documents", [[]])[0] if results.get("documents") else []
        context_str = " ".join(context_docs)
        
        if not context_str.strip():
            return {
                "answer": "[No relevant context found for your query. Please try rephrasing or uploading more documents.]",
                "context": "",
                "status": "no_context"
            }
        
        # Call LLM with conversation history
        answer = LLMHandler.call_llm(
            question, 
            context_str, 
            conversation_history=history_list
        )
        
        return {
            "answer": answer,
            "context": context_str,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/query/stream")
async def query_rag_stream(
    question: str = Form(...),
    n_results: int = Form(3),
    expand: int = Form(2),
    filename: str = Form(None),
    conversation_history: str = Form("[]")
):
    """Streaming query endpoint for real-time responses."""
    try:
        # Parse conversation history
        try:
            history_list = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history_list = []
        # Query vector store
        results = VectorStore.query_with_expanded_context(
            question, 
            n_results=n_results, 
            expand=expand,
            filename=filename
        )
        context_docs = results.get("documents", [[]])[0] if results.get("documents") else []
        context_str = " ".join(context_docs)
        if not context_str.strip():
            def empty_stream():
                yield json.dumps({
                "answer": "[No relevant context found for your query. Please try rephrasing or uploading more documents.]",
                "context": "",
                "status": "no_context"
                })
            return StreamingResponse(empty_stream(), media_type="application/json")
        def word_stream():
            answer_accum = ""
            def stream_callback(word):
                nonlocal answer_accum
                answer_accum += word
                yield_word = json.dumps({"answer": word, "context": context_str, "status": "streaming"})
                yield yield_word + "\n"
            # Use a generator to yield words as they are produced
            for _ in LLMHandler.call_llm(question, context_str, conversation_history=history_list, stream_callback=None):
                # This loop is just to trigger the streaming, actual streaming is handled in stream_callback
                pass
            # At the end, yield the full answer
            yield json.dumps({"answer": answer_accum, "context": context_str, "status": "success"}) + "\n"
        return StreamingResponse(word_stream(), media_type="application/json")
    except Exception as e:
        def error_stream():
            yield json.dumps({"answer": f"[Error: {str(e)}]", "context": "", "status": "error"})
        return StreamingResponse(error_stream(), media_type="application/json")

# --- Chat History Endpoints ---
@app.get("/history/list")
def list_histories():
    return {"conversations": history.list_conversations()}

@app.get("/history/get/{conv_id}")
def get_history(conv_id: str):
    conv = history.load_conversation(conv_id)
    return {"conversation": conv}

@app.post("/history/save")
def save_history(conv: dict):
    history.save_conversation(conv)
    return {"status": "saved"}

@app.delete("/history/delete/{conv_id}")
def delete_history(conv_id: str):
    history.delete_conversation(conv_id)
    history.delete_chat_context(conv_id)
    return {"status": "deleted"}

@app.get("/history/export/{conv_id}")
def export_history(conv_id: str):
    """Export a conversation as a downloadable JSON file."""
    import os
    from rag_core import history
    conv = history.load_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log', 'conversations', f"{conv_id}.json")
    return FileResponse(file_path, media_type='application/json', filename=f"conversation_{conv_id}.json")

# --- Knowledge Base Reset Endpoint ---
@app.post("/reset_kb")
def reset_knowledge_base():
    VectorStore.clear_vector_collection()
    return {"status": "knowledge base reset"} 
@app.get("/documents")
def list_documents():
    docs = VectorStore.list_documents()
    return {"documents": docs}

@app.delete("/documents/{filename}")
def delete_document(filename: str):
    success = VectorStore.delete_document(filename)
    if success:
        return {"status": "deleted", "filename": filename}
    else:
        raise HTTPException(status_code=404, detail="Document not found or could not be deleted") 
