from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from rag_core.document import DocumentProcessor, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from rag_core.vectorstore import VectorStore
from rag_core.llm import LLMHandler
from rag_core import history
import json
from fastapi.middleware.cors import CORSMiddleware
from rag_core import cache

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
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(DEFAULT_CHUNK_SIZE),
    chunk_overlap: int = Form(DEFAULT_CHUNK_OVERLAP)
):
    file_bytes = await file.read()
    file_hash = cache.get_file_hash(file_bytes)
    docs = DocumentProcessor.process_document(file, file_bytes, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # Check if embeddings already exist for this file
    if cache.global_embeddings_exist(file_hash):
        embeddings = cache.load_global_embeddings(file_hash)
        if embeddings is not None:
            # Use cached embeddings for upsert
            from rag_core.vectorstore import VectorStore
            VectorStore.add_to_vector_collection(docs, file.filename, embeddings=embeddings)
            return {"num_chunks": len(docs), "status": "embeddings already exist for this file (reused from cache)"}
    # Otherwise, create embeddings as usual
    try:
        from rag_core.vectorstore import VectorStore
        success = VectorStore.add_to_vector_collection(docs, file.filename)
        if success:
            # Save new embeddings to cache (if possible to retrieve them)
            # (Assume you can get embeddings from the vector store or from docs if needed)
            return {"num_chunks": len(docs), "status": "uploaded and embedded"}
        else:
            return {"num_chunks": len(docs), "status": "uploaded but embedding failed"}
    except Exception as e:
        return {"num_chunks": len(docs), "status": f"uploaded but embedding error: {str(e)}"}

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
        # Limit context to 3000 characters (adjust as needed)
        context_str = "\n---\n".join(context_docs)
        if len(context_str) > 3000:
            context_str = context_str[:3000]
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
            got_any = False
            for word in LLMHandler.call_llm(question, context_str, conversation_history=history_list):
                got_any = True
                answer_accum += word
                yield json.dumps({"answer": word, "context": "", "status": "streaming"}) + "\n"
            # If nothing was yielded, return a fallback message
            if not got_any or not answer_accum.strip():
                answer_accum = "[No answer could be generated. Please try rephrasing your question or uploading more documents.]"
            yield json.dumps({"answer": answer_accum, "context": "", "status": "success"}) + "\n"
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
