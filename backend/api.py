from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from rag_core.document import DocumentProcessor, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from rag_core.vectorstore import VectorStore
from rag_core.llm import LLMHandler
from rag_core import history
import json
from fastapi.middleware.cors import CORSMiddleware
from rag_core import cache
import tempfile
import mimetypes
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import logging
from rag_core.whisper_asr import transcribe_audio_with_ollama
import os
import psutil
import time

app = FastAPI()

# Enable CORS for frontend
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "timestamp": time.time()}

@app.get("/health/detailed")
def detailed_health_check():
    """Detailed health check with system metrics."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Service health checks
        vectorstore_healthy = False
        ollama_healthy = False
        redis_healthy = False
        
        try:
            collection = VectorStore.get_vector_collection()
            vectorstore_healthy = collection is not None
        except:
            pass
        
        try:
            import ollama
            response = ollama.chat(
                model="llama3.2:3b",
                messages=[{"role": "user", "content": "test"}],
                options={"base_url": "http://localhost:11434"}
            )
            ollama_healthy = True
        except:
            pass
        
        try:
            from rag_core.redis_cache import redis_client
            redis_client.ping()
            redis_healthy = True
        except:
            pass
        
        return {
            "status": "ok",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_available_gb": memory.available / (1024**3)
            },
            "services": {
                "vectorstore": vectorstore_healthy,
                "ollama": ollama_healthy,
                "redis": redis_healthy
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/test_vectorstore")
def test_vectorstore():
    """Test if vector store can be initialized and Ollama is working."""
    try:
        collection = VectorStore.get_vector_collection()
        if collection:
            return {"status": "ok", "message": "Vector store initialized successfully"}
        else:
            return {"status": "error", "message": "Failed to initialize vector store"}
    except Exception as e:
        return {"status": "error", "message": f"Vector store error: {str(e)}"}

@app.get("/domains")
def get_domains():
    """Get available domains in the knowledge base."""
    try:
        domains = VectorStore.get_domains()
        return {"domains": domains}
    except Exception as e:
        return {"domains": [], "error": str(e)}

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(DEFAULT_CHUNK_SIZE),
    chunk_overlap: int = Form(DEFAULT_CHUNK_OVERLAP)
):
    file_bytes = await file.read()
    file_hash = cache.get_file_hash(file_bytes)
    docs = DocumentProcessor.process_document(file, file_bytes, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not docs or all(not getattr(doc, 'page_content', '').strip() for doc in docs):
        return JSONResponse(status_code=400, content={'error': 'No text could be extracted from the document. If this is a scanned PDF, ensure OCR is working and Tesseract is installed.'})
    # Check if embeddings already exist for this file
    if cache.global_embeddings_exist(file_hash):
        embeddings = cache.load_global_embeddings(file_hash)
        if embeddings is not None:
            # Use cached embeddings for upsert
            VectorStore.add_to_vector_collection(docs, file.filename, embeddings=embeddings)
            return {"num_chunks": len(docs), "status": "embeddings already exist for this file (reused from cache)"}
    # Otherwise, create embeddings as usual
    try:
        success = VectorStore.add_to_vector_collection(docs, file.filename)
        if success:
            # Save new embeddings to cache (if possible to retrieve them)
            # (Assume you can get embeddings from the vector store or from docs if needed)
            return {"num_chunks": len(docs), "status": "uploaded and embedded"}
        else:
            return {"num_chunks": len(docs), "status": "uploaded but embedding failed"}
    except Exception as e:
        return {"num_chunks": len(docs), "status": f"uploaded but embedding error: {str(e)}"}

def is_mcq_question(question):
    q = question.lower()
    return 'option' in q or 'mcq' in q or 'a)' in q or 'b)' in q or 'c)' in q or 'd)' in q

def get_source_filename():
    # Heuristic: pick the first non-quiz/non-mcq document as the source
    docs = VectorStore.list_documents()
    for doc in docs:
        fname = doc['filename'].lower()
        if not ('mcq' in fname or 'quiz' in fname or 'question' in fname):
            return doc['filename']
    # Fallback: just use the first document
    if docs:
        return docs[0]['filename']
    return None

@app.post("/query")
async def query_rag(
    question: str = Form(...),
    n_results: int = Form(3),
    expand: int = Form(2),
    filename: str = Form(None),
    domain_filter: str = Form(None),
    conversation_history: str = Form("[]"),
    session_id: str = Form(None)
):
    try:
        try:
            history_list = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history_list = []
        # Check if knowledge base is empty
        if not VectorStore.list_documents():
            return {
                "answer": "There is nothing in the knowledge base right now. Please upload a document before continuing.",
                "context": "",
                "status": "empty_kb",
                "sources": []
            }
        
        # Enhanced query with domain filtering, source attribution, and session isolation
        results = VectorStore.query_with_expanded_context(
            question,
            n_results=n_results,
            expand=expand,
            filename=filename,
            domain_filter=domain_filter,
            session_id=session_id
        )
        
        # Group context by document with source attribution and confidence scoring
        context_by_doc = {}
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        sources = results.get('sources', [])
        
        # Filter out low-confidence sources and conflicting information
        filtered_chunks = []
        for chunk, meta, source in zip(docs, metas, sources):
            confidence = source.get('confidence', 0.5)
            if confidence > 0.3:  # Only include high-confidence sources
                filtered_chunks.append((chunk, meta, source))
        
        for chunk, meta, source in filtered_chunks:
            fname = meta.get('filename', 'unknown')
            context_by_doc.setdefault(fname, []).append({
                'content': chunk,
                'source': source,
                'confidence': source.get('confidence', 0.5)
            })
        
        # Build a prompt that shows context grouped by document with sources and confidence
        context_str = ''
        for fname, chunks in context_by_doc.items():
            context_str += f'Context from {fname}:\n'
            for chunk_info in chunks:
                confidence = chunk_info.get('confidence', 0.5)
                context_str += f'[Confidence: {confidence:.2f}] [{chunk_info["source"]["attribution"]}]\n{chunk_info["content"]}\n\n'
        
        if not context_str.strip():
            return {
                "answer": "[No relevant context found for your query. Please try rephrasing or uploading more documents.]",
                "context": "",
                "status": "no_context",
                "sources": []
            }
        
        # Enhanced LLM call with strict fact verification
        answer = LLMHandler.call_llm(
            question,
            context_str,
            conversation_history=history_list
        )
        
        return {
            "answer": answer,
            "context": context_str,
            "status": "success",
            "sources": sources,
            "query_classification": results.get('query_classification', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/query/stream")
async def query_rag_stream(
    question: str = Form(...),
    n_results: int = Form(3),
    expand: int = Form(2),
    filename: str = Form(None),
    domain_filter: str = Form(None),
    conversation_history: str = Form("[]"),
    session_id: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        try:
            history_list = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history_list = []
        # Check if knowledge base is empty
        if not VectorStore.list_documents():
            def empty_kb_stream():
                yield json.dumps({
                    "answer": "There is nothing in the knowledge base right now. Please upload a document before continuing.",
                    "context": "",
                    "status": "empty_kb",
                    "sources": []
                })
            return StreamingResponse(empty_kb_stream(), media_type="application/json")
        
        # Enhanced query with domain filtering and source attribution
        results = VectorStore.query_with_expanded_context(
            question,
            n_results=n_results,
            expand=expand,
            filename=filename,
            domain_filter=domain_filter
        )
        
        # Group context by document with source attribution
        context_by_doc = {}
        docs = results.get('documents', [[]])[0]
        metas = results.get('metadatas', [[]])[0]
        sources = results.get('sources', [])
        
        for chunk, meta, source in zip(docs, metas, sources):
            fname = meta.get('filename', 'unknown')
            context_by_doc.setdefault(fname, []).append({
                'content': chunk,
                'source': source
            })
        
        # Build a prompt that shows context grouped by document with sources
        context_str = ''
        for fname, chunks in context_by_doc.items():
            context_str += f'Context from {fname}:\n'
            for chunk_info in chunks:
                context_str += f'[{chunk_info["source"]["attribution"]}]\n{chunk_info["content"]}\n\n'
        
        # --- NEW: Handle attached file (PDF/image) ---
        temp_chunks = []
        temp_filename = None
        MAX_FILE_SIZE_MB = 150  # Increased to 150MB
        SUPPORTED_TYPES = ['application/pdf', 'image/png', 'image/jpeg']
        def clean_text_for_rag(text):
            text = re.sub(r'Page \\d+ of \\d+', '', text)
            text = re.sub(r'Confidential', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        def smart_chunk(text, max_words=300):
            paras = [p.strip() for p in text.split('\n\n') if p.strip()]
            chunks = []
            current = []
            word_count = 0
            for para in paras:
                words = para.split()
                if word_count + len(words) > max_words and current:
                    chunks.append(' '.join(current))
                    current = []
                    word_count = 0
                current.append(para)
                word_count += len(words)
            if current:
                chunks.append(' '.join(current))
            return chunks
        if file is not None:
            temp_filename = file.filename
            file_bytes = await file.read()
            mime_type, _ = mimetypes.guess_type(file.filename)
            # File type/size validation
            if mime_type not in SUPPORTED_TYPES:
                return JSONResponse(status_code=400, content={'error': 'Unsupported file type.'})
            if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
                return JSONResponse(status_code=400, content={'error': 'File too large.'})
            try:
                # If PDF
                if file.filename.lower().endswith('.pdf') or (mime_type and 'pdf' in mime_type):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                        tmp_pdf.write(file_bytes)
                        tmp_pdf.flush()
                        doc = fitz.open(tmp_pdf.name)
                        for page in doc:
                            text = page.get_text()
                            if text.strip():
                                temp_chunks.append(text)
                            else:
                                pix = page.get_pixmap()
                                img = Image.open(io.BytesIO(pix.tobytes()))
                                ocr_text = pytesseract.image_to_string(img)
                                if ocr_text.strip():
                                    temp_chunks.append(ocr_text)
                        doc.close()
                # If image
                elif mime_type and mime_type.startswith('image'):
                    img = Image.open(io.BytesIO(file_bytes))
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text.strip():
                        temp_chunks.append(ocr_text)
                # Clean and chunk
                clean_text = '\n'.join([c.strip() for c in temp_chunks if c.strip()])
                cleaned_text = clean_text_for_rag(clean_text)
                temp_doc_chunks = smart_chunk(cleaned_text)
                if not temp_doc_chunks:
                    return JSONResponse(status_code=400, content={'error': 'No text could be extracted from the file.'})
                # Generate embeddings for these chunks (use same model as KB)
                temp_vectors = []
                for chunk in temp_doc_chunks:
                    emb = VectorStore.embed_text(chunk)
                    temp_vectors.append((chunk, emb))
                # Retrieve top-k from temp_vectors
                import numpy as np
                if temp_vectors:
                    q_emb = VectorStore.embed_text(question)
                    sims = [float(np.dot(q_emb, emb)) for _, emb in temp_vectors]
                    topk = np.argsort(sims)[-n_results:][::-1]
                    temp_context = [temp_doc_chunks[i] for i in topk]
                    context_str += f'Context from {temp_filename} (attached):\n' + '\n'.join(temp_context) + '\n\n'
            except Exception as e:
                logging.error(f'OCR or file processing failed: {e}')
                return JSONResponse(status_code=500, content={'error': 'OCR or file processing failed. Please try a different file.'})
        
        if len(context_str) > 3000:
            context_str = context_str[:3000]
        if not context_str.strip():
            def empty_stream():
                yield json.dumps({
                "answer": "[No relevant context found for your query. Please try rephrasing or uploading more documents.]",
                "context": "",
                "status": "no_context",
                "sources": []
                })
            return StreamingResponse(empty_stream(), media_type="application/json")
        def word_stream():
            answer_accum = ""
            got_any = False
            for word in LLMHandler.call_llm(question, context_str, conversation_history=history_list):
                got_any = True
                answer_accum += word
                yield json.dumps({
                    "answer": word, 
                    "context": "", 
                    "status": "streaming",
                    "sources": sources,
                    "query_classification": results.get('query_classification', {})
                }) + "\n"
            if not got_any or not answer_accum.strip():
                answer_accum = "[No answer could be generated. Please try rephrasing your question or uploading more documents.]"
            # Only yield the final status, not the complete answer again
            yield json.dumps({
                "answer": "", 
                "context": "", 
                "status": "success",
                "sources": sources,
                "query_classification": results.get('query_classification', {})
            }) + "\n"
        return StreamingResponse(word_stream(), media_type="application/json")
    except Exception as e:
        def error_stream(e=e):
            yield json.dumps({
                "answer": f"[Error: {str(e)}]", 
                "context": "", 
                "status": "error",
                "sources": []
            })
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

@app.get("/api/history/file/{conv_id}")
def get_history_file(conv_id: str):
    import os
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log', 'conversations', f"{conv_id}.json")
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "Conversation file not found"})
    with open(file_path, 'r') as f:
        data = f.read()
    return JSONResponse(content={"conversation": json.loads(data)})

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

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    audio_format = file.filename.split('.')[-1].lower()
    try:
        text = transcribe_audio_with_ollama(audio_bytes, audio_format=audio_format)
        return {"text": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Transcription failed: {str(e)}"}) 
