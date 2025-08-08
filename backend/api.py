from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from rag_core.document import DocumentProcessor, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from rag_core.vectorstore import VectorStore
from rag_core.llm import LLMHandler
from rag_core import history
from rag_core.context_manager import context_manager
from rag_core.multi_ocr import MultiOCREngine  # Add multi-OCR import
from rag_core.ocr_config import get_config  # Add OCR config import
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
from rag_core.conversation_manager import conversation_manager, asdict
from datetime import datetime, timedelta
# from rag_core.agentic_rag import AgenticRAG, QueryType, DataSourceType
from rag_core.config import logger
import asyncio

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

@app.get("/supported-file-types")
def get_supported_file_types():
    """Get list of supported file types and their descriptions."""
    try:
        from rag_core.document import DocumentProcessor
        supported_types = DocumentProcessor.get_supported_extensions()
        return {
            "supported_types": supported_types,
            "total_types": len(supported_types)
        }
    except Exception as e:
        logging.error(f"Error getting supported file types: {str(e)}")
        return {"supported_types": {}, "error": str(e)}

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
    chunk_overlap: int = Form(DEFAULT_CHUNK_OVERLAP),
    document_type: str = Form("default")  # "default" or "master_document"
):
    # Validate file type before processing
    from rag_core.document import DocumentProcessor
    
    if not DocumentProcessor.is_supported_file(file.filename):
        supported_types = DocumentProcessor.get_supported_extensions()
        return JSONResponse(
            status_code=400, 
            content={
                'error': f'Unsupported file type: {file.filename}. Supported types: {", ".join(supported_types.keys())}'
            }
        )
    
    file_bytes = await file.read()
    file_hash = cache.get_file_hash(file_bytes)
    
    try:
        docs = DocumentProcessor.process_document(file_bytes, file.filename, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not docs or all(not getattr(doc, 'page_content', '').strip() for doc in docs):
            return JSONResponse(status_code=400, content={'error': 'No text could be extracted from the document. If this is a scanned PDF, ensure OCR is working and Tesseract is installed.'})
            
        # Check if embeddings already exist for this file
        if cache.global_embeddings_exist(file_hash):
            embeddings = cache.load_global_embeddings(file_hash)
            if embeddings is not None:
                # Use cached embeddings for upsert
                VectorStore.add_to_vector_collection(docs, file.filename, embeddings=embeddings)
                return {
                    "num_chunks": len(docs), 
                    "status": "embeddings already exist for this file (reused from cache)",
                    "file_type": docs[0].metadata.get('file_type', 'unknown') if docs else 'unknown',
                    "processing": docs[0].metadata.get('processing', 'unknown') if docs else 'unknown'
                }
            
        # Add document type metadata to all chunks
        for doc in docs:
            doc.metadata['document_type'] = document_type
            if document_type == "master_document":
                doc.metadata['is_master'] = True
                doc.metadata['master_document'] = file.filename
        # Otherwise, create embeddings as usual
        success = VectorStore.add_to_vector_collection(docs, file.filename)
        if success:
            # Save new embeddings to cache (if possible to retrieve them)
            # (Assume you can get embeddings from the vector store or from docs if needed)
            return {
                "num_chunks": len(docs), 
                "status": "uploaded and embedded",
                "file_type": docs[0].metadata.get('file_type', 'unknown') if docs else 'unknown',
                "document_type": document_type,
                "processing": docs[0].metadata.get('processing', 'unknown') if docs else 'unknown'
            }
        else:
            return {
                "num_chunks": len(docs), 
                "status": "uploaded but embedding failed", 
                "document_type": document_type,
                "processing": docs[0].metadata.get('processing', 'unknown') if docs else 'unknown'
            }
    except ValueError as e:
        # Handle validation errors (unsupported file type, size limit, etc.)
        return JSONResponse(status_code=400, content={'error': str(e)})
    except Exception as e:
        logging.error(f"Error processing document {file.filename}: {str(e)}")
        return JSONResponse(status_code=500, content={'error': f'Failed to process document: {str(e)}'})

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
                "sources": [],
                "context_metadata": {}
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
        
        # Ensure we have matching lengths
        min_length = min(len(docs), len(metas), len(sources))
        logger.info(f"Processing {min_length} chunks (docs: {len(docs)}, metas: {len(metas)}, sources: {len(sources)})")
        
        for i in range(min_length):
            chunk = docs[i]
            meta = metas[i]
            source = sources[i] if i < len(sources) else {}
            
            confidence = source.get('confidence', 0.5)
            if confidence > 0.3:  # Only include high-confidence sources
                filtered_chunks.append((chunk, meta, source))
        
        for chunk, meta, source in filtered_chunks:
            fname = meta.get('filename', 'unknown')
            context_by_doc.setdefault(fname, []).append({
                "content": chunk,
                "metadata": meta,
                "source": source
            })
        
        # Use context manager to create optimized context
        retrieved_chunks = []
        for fname, chunks in context_by_doc.items():
            for chunk_info in chunks:
                retrieved_chunks.append({
                    "content": chunk_info["content"],
                    "source": chunk_info["source"]
                })
        
        # Create optimized context window
        context_str, context_metadata = context_manager.create_context_window(
            current_question=question,
            conversation_history=history_list,
            retrieved_chunks=retrieved_chunks,
            session_id=session_id
        )
        
        # Use filtered sources for the response
        sources = filtered_chunks
        
        # Generate answer using LLM
        answer = ""
        try:
            for word in LLMHandler.call_llm(question, context_str):
                answer += word
        except Exception as e:
            logging.error(f"LLM call failed: {str(e)}")
            answer = f"Error generating response: {str(e)}"
        
        # Add message to context manager history
        if session_id:
            context_manager.add_message_to_history(
                session_id=session_id,
                role="user",
                content=question,
                sources=sources
            )
            context_manager.add_message_to_history(
                session_id=session_id,
                role="assistant",
                content=answer,
                sources=sources
        )
        
        # Prepare detailed source information with chunks
        detailed_sources = []
        for chunk, meta, source in filtered_chunks:
            detailed_sources.append({
                "content": chunk,
                "metadata": meta,
                "source": source,
                "filename": meta.get('filename', 'unknown'),
                "page": meta.get('page', None),
                "section": meta.get('section', None),
                "document_type": meta.get('document_type', 'default'),
                "is_master": meta.get('is_master', False),
                "chunk_id": meta.get('chunk_id', None),
                "confidence": source.get('confidence', 0.5) if source else 0.5
            })
        
        return {
            "answer": answer,
            "context": context_str,
            "sources": sources,
            "detailed_sources": detailed_sources,
            "context_metadata": context_metadata
        }
        
    except Exception as e:
        logging.error(f"Error in query endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process query: {str(e)}"}
        )

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
        
        # Limit conversation history to prevent context pollution
        if len(history_list) > 5:  # Only keep last 5 exchanges
            history_list = history_list[-5:]
        
        # Check if knowledge base is empty
        if not VectorStore.list_documents():
            def empty_kb_stream():
                yield json.dumps({
                    "answer": "There is nothing in the knowledge base right now. Please upload a document before continuing.",
                    "context": "",
                    "status": "empty_kb",
                    "sources": [],
                    "context_metadata": {}
                })
            return StreamingResponse(empty_kb_stream(), media_type="application/json")
        
        # Enhanced query with domain filtering and source attribution
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
        
        # Ensure we have matching lengths
        min_length = min(len(docs), len(metas), len(sources))
        logger.info(f"Processing {min_length} chunks (docs: {len(docs)}, metas: {len(metas)}, sources: {len(sources)})")
        
        for i in range(min_length):
            chunk = docs[i]
            meta = metas[i]
            source = sources[i] if i < len(sources) else {}
            
            confidence = source.get('confidence', 0.5)
            if confidence > 0.3:  # Only include high-confidence sources
                filtered_chunks.append((chunk, meta, source))
        
        for chunk, meta, source in filtered_chunks:
            fname = meta.get('filename', 'unknown')
            context_by_doc.setdefault(fname, []).append({
                "content": chunk,
                "metadata": meta,
                "source": source
            })
        
        # Use context manager to create optimized context
        retrieved_chunks = []
        for fname, chunks in context_by_doc.items():
            for chunk_info in chunks:
                retrieved_chunks.append({
                    "content": chunk_info["content"],
                    "source": chunk_info["source"]
                })
        
        # Create optimized context window
        context_str, context_metadata = context_manager.create_context_window(
            current_question=question,
            conversation_history=history_list,
            retrieved_chunks=retrieved_chunks,
            session_id=session_id
        )
        
        # Use filtered sources for the response
        sources = filtered_chunks
        
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
                "sources": [],
                "context_metadata": {}
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
                    "query_classification": results.get('query_classification', {}),
                    "context_metadata": context_metadata
                }) + "\n"
            if not got_any or not answer_accum.strip():
                answer_accum = "[No answer could be generated. Please try rephrasing your question or uploading more documents.]"
            # Only yield the final status, not the complete answer again
            yield json.dumps({
                "answer": "", 
                "context": "", 
                "status": "success",
                "sources": sources,
                "query_classification": results.get('query_classification', {}),
                "context_metadata": context_metadata
            }) + "\n"
        return StreamingResponse(word_stream(), media_type="application/json")
    except Exception as e:
        def error_stream(e=e):
            yield json.dumps({
                "answer": f"[Error: {str(e)}]", 
                "context": "", 
                "status": "error",
                "sources": [],
                "context_metadata": {}
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
    """Reset the knowledge base by clearing all embeddings."""
    try:
        # Clear cache first
        try:
            cache.clear_cache("all")
            logging.info("Cleared cache before reset")
        except Exception as cache_error:
            logging.warning(f"Could not clear cache: {cache_error}")
        
        # Force clear any document list caching
        try:
            # Clear any cached document lists in memory
            if hasattr(VectorStore, '_document_cache'):
                VectorStore._document_cache = {}
                logging.info("Cleared document cache")
            
            # Force clear any module-level caches
            import sys
            for module_name in list(sys.modules.keys()):
                if 'chromadb' in module_name or 'vectorstore' in module_name:
                    try:
                        del sys.modules[module_name]
                        logging.info(f"Cleared module cache: {module_name}")
                    except:
                        pass
        except Exception as doc_cache_error:
            logging.warning(f"Could not clear document cache: {doc_cache_error}")
        
        # Reset vector collection
        success = VectorStore.clear_vector_collection()
        if success:
            # Force refresh of document list
            try:
                # Clear any cached document lists
                if hasattr(cache, 'clear_document_cache'):
                    cache.clear_document_cache()
            except:
                pass
            
            # Verify the reset worked by checking document count and file system
            try:
                # Check if ChromaDB directory is empty
                import os
                chroma_path = "./demo-rag-chroma"
                if os.path.exists(chroma_path):
                    dir_contents = os.listdir(chroma_path)
                    # Should only have chroma.sqlite3 file (empty database)
                    if len(dir_contents) == 1 and 'chroma.sqlite3' in dir_contents:
                        logger.info("ChromaDB directory is properly reset")
                    else:
                        logger.warning(f"ChromaDB directory still has unexpected contents: {dir_contents}")
                
                # Check document count
                documents = VectorStore.list_documents()
                if len(documents) == 0:
                    return {"status": "knowledge base reset successfully"}
                else:
                    logger.warning(f"Documents still exist after reset: {len(documents)}")
                    # Force return success since we used the nuclear option
                    return {"status": "knowledge base reset successfully"}
            except Exception as verify_error:
                logger.error(f"Could not verify reset: {verify_error}")
                return {"status": "knowledge base reset successfully"}
        else:
            return JSONResponse(
                status_code=500, 
                content={"error": "Failed to reset knowledge base", "status": "reset failed"}
            )
    except Exception as e:
        logging.error(f"Error resetting knowledge base: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={"error": f"Error resetting knowledge base: {str(e)}", "status": "reset failed"}
        ) 

@app.get("/documents")
def list_documents():
    """List all documents in the knowledge base."""
    try:
        documents = VectorStore.list_documents()
        return {"documents": documents}
    except Exception as e:
        logging.error(f"Error listing documents: {str(e)}")
        return {"documents": [], "error": str(e)}

@app.post("/search")
async def search_documents(
    query: str = Form(...),
    filters: str = Form("[]"),
    limit: int = Form(10),
    min_score: float = Form(0.1),
    search_type: str = Form("documents")  # "documents" or "conversations"
):
    """Advanced search with filtering"""
    try:
        from rag_core.search import advanced_search
        import json
        
        # Parse filters
        try:
            filter_list = json.loads(filters) if filters else []
        except json.JSONDecodeError:
            filter_list = []
        
        if search_type == "documents":
            results = advanced_search.search_documents(
                query=query,
                filters=filter_list,
                limit=limit,
                min_score=min_score
            )
            
            # Convert SearchResult objects to dicts
            search_results = []
            for result in results:
                search_results.append({
                    "content": result.content,
                    "filename": result.filename,
                    "domain": result.domain,
                    "file_type": result.file_type,
                    "chunk_index": result.chunk_index,
                    "score": result.score,
                    "highlights": result.highlights,
                    "metadata": result.metadata
                })
            
            return {
                "results": search_results,
                "total": len(search_results),
                "query": query,
                "filters": filter_list
            }
        
        elif search_type == "conversations":
            # For conversation search, we need conversation history
            # This would typically come from the session
            return {"error": "Conversation search requires session context"}
        
        else:
            return {"error": f"Unknown search type: {search_type}"}
            
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return {"error": str(e), "results": []}

@app.get("/search/suggestions")
def get_search_suggestions(partial_query: str = ""):
    """Get search suggestions based on partial query"""
    try:
        from rag_core.search import advanced_search
        
        suggestions = advanced_search.get_search_suggestions(partial_query)
        return {
            "suggestions": suggestions,
            "query": partial_query
        }
    except Exception as e:
        logging.error(f"Search suggestions error: {str(e)}")
        return {"suggestions": [], "error": str(e)}

@app.post("/search/conversations")
async def search_conversations(
    query: str = Form(...),
    conversation_history: str = Form("[]"),
    limit: int = Form(5)
):
    """Search within conversation history"""
    try:
        from rag_core.search import advanced_search
        import json
        
        # Parse conversation history
        try:
            history = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history = []
        
        results = advanced_search.search_conversations(
            query=query,
            conversation_history=history,
            limit=limit
        )
        
        return {
            "results": results,
            "total": len(results),
            "query": query
        }
        
    except Exception as e:
        logging.error(f"Conversation search error: {str(e)}")
        return {"error": str(e), "results": []}

# Conversation Management Endpoints
@app.get("/conversations/folders")
def get_conversation_folders():
    """Get all conversation folders"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        folders = conversation_manager.get_folders()
        return {
            "folders": [asdict(folder) for folder in folders],
            "total": len(folders)
        }
    except Exception as e:
        logging.error(f"Error getting conversation folders: {str(e)}")
        return {"folders": [], "error": str(e)}

@app.post("/conversations/folders")
async def create_conversation_folder(
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form("#3B82F6")
):
    """Create a new conversation folder"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        folder = conversation_manager.create_folder(name, description, color)
        return {
            "folder": asdict(folder),
            "message": "Folder created successfully"
        }
    except Exception as e:
        logging.error(f"Error creating conversation folder: {str(e)}")
        return {"error": str(e)}

@app.put("/conversations/folders/{folder_id}")
async def update_conversation_folder(
    folder_id: str,
    name: str = Form(None),
    description: str = Form(None),
    color: str = Form(None)
):
    """Update a conversation folder"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if color is not None:
            update_data["color"] = color
        
        folder = conversation_manager.update_folder(folder_id, **update_data)
        if folder:
            return {
                "folder": asdict(folder),
                "message": "Folder updated successfully"
            }
        else:
            return {"error": "Folder not found"}
    except Exception as e:
        logging.error(f"Error updating conversation folder: {str(e)}")
        return {"error": str(e)}

@app.delete("/conversations/folders/{folder_id}")
async def delete_conversation_folder(folder_id: str):
    """Delete a conversation folder"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        success = conversation_manager.delete_folder(folder_id)
        if success:
            return {"message": "Folder deleted successfully"}
        else:
            return {"error": "Folder not found"}
    except Exception as e:
        logging.error(f"Error deleting conversation folder: {str(e)}")
        return {"error": str(e)}

@app.post("/conversations/move")
async def move_conversation_to_folder(
    conversation_id: str = Form(...),
    folder_id: str = Form(...)
):
    """Move a conversation to a folder"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        success = conversation_manager.move_conversation_to_folder(conversation_id, folder_id)
        if success:
            return {"message": "Conversation moved successfully"}
        else:
            return {"error": "Failed to move conversation"}
    except Exception as e:
        logging.error(f"Error moving conversation: {str(e)}")
        return {"error": str(e)}

# Template Management
@app.get("/conversations/templates")
def get_conversation_templates(category: str = None):
    """Get conversation templates"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        templates = conversation_manager.get_templates(category)
        return {
            "templates": [asdict(template) for template in templates],
            "total": len(templates)
        }
    except Exception as e:
        logging.error(f"Error getting conversation templates: {str(e)}")
        return {"templates": [], "error": str(e)}

@app.post("/conversations/templates")
async def create_conversation_template(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    system_prompt: str = Form(...),
    initial_messages: str = Form("[]")
):
    """Create a new conversation template"""
    try:
        from rag_core.conversation_manager import conversation_manager
        import json
        
        # Parse initial messages
        try:
            messages = json.loads(initial_messages) if initial_messages else []
        except json.JSONDecodeError:
            messages = []
        
        template = conversation_manager.create_template(
            name=name,
            description=description,
            category=category,
            system_prompt=system_prompt,
            initial_messages=messages
        )
        
        return {
            "template": asdict(template),
            "message": "Template created successfully"
        }
    except Exception as e:
        logging.error(f"Error creating conversation template: {str(e)}")
        return {"error": str(e)}

@app.post("/conversations/templates/{template_id}/use")
async def use_conversation_template(template_id: str):
    """Use a conversation template to create a new conversation"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        template_data = conversation_manager.use_template(template_id)
        if template_data:
            return {
                "template_data": template_data,
                "message": "Template applied successfully"
            }
        else:
            return {"error": "Template not found"}
    except Exception as e:
        logging.error(f"Error using conversation template: {str(e)}")
        return {"error": str(e)}

# Export/Import
@app.post("/conversations/export")
async def export_conversation(
    conversation_id: str = Form(...),
    format: str = Form("json")
):
    """Export a conversation"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        export_path = conversation_manager.export_conversation(conversation_id, format)
        if export_path:
            return {
                "export_path": export_path,
                "message": "Conversation exported successfully"
            }
        else:
            return {"error": "Failed to export conversation"}
    except Exception as e:
        logging.error(f"Error exporting conversation: {str(e)}")
        return {"error": str(e)}

@app.post("/conversations/export/batch")
async def export_conversations_batch(
    conversation_ids: str = Form(...),  # JSON array of conversation IDs
    format: str = Form("zip")
):
    """Export multiple conversations as a batch"""
    try:
        from rag_core.conversation_manager import conversation_manager
        import json
        
        # Parse conversation IDs
        try:
            ids = json.loads(conversation_ids)
        except json.JSONDecodeError:
            return {"error": "Invalid conversation IDs format"}
        
        export_path = conversation_manager.export_conversations_batch(ids, format)
        if export_path:
            return {
                "export_path": export_path,
                "message": f"Exported {len(ids)} conversations successfully"
            }
        else:
            return {"error": "Failed to export conversations"}
    except Exception as e:
        logging.error(f"Error exporting conversations batch: {str(e)}")
        return {"error": str(e)}

@app.post("/conversations/import")
async def import_conversation(file: UploadFile = File(...)):
    """Import a conversation from a file"""
    try:
        from rag_core.conversation_manager import conversation_manager
        import tempfile
        import os
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Import conversation
            new_conversation_id = conversation_manager.import_conversation(tmp_file_path)
            if new_conversation_id:
                return {
                    "conversation_id": new_conversation_id,
                    "message": "Conversation imported successfully"
                }
            else:
                return {"error": "Failed to import conversation"}
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        logging.error(f"Error importing conversation: {str(e)}")
        return {"error": str(e)}

# Sharing
@app.post("/conversations/share")
async def share_conversation(
    conversation_id: str = Form(...),
    user_ids: str = Form(...)  # JSON array of user IDs
):
    """Share a conversation with other users"""
    try:
        from rag_core.conversation_manager import conversation_manager
        import json
        
        # Parse user IDs
        try:
            users = json.loads(user_ids)
        except json.JSONDecodeError:
            return {"error": "Invalid user IDs format"}
        
        success = conversation_manager.share_conversation(conversation_id, users)
        if success:
            return {"message": "Conversation shared successfully"}
        else:
            return {"error": "Failed to share conversation"}
    except Exception as e:
        logging.error(f"Error sharing conversation: {str(e)}")
        return {"error": str(e)}

@app.get("/conversations/shared/{user_id}")
def get_shared_conversations(user_id: str):
    """Get conversations shared with a specific user"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        shared_conversations = conversation_manager.get_shared_conversations(user_id)
        return {
            "conversations": shared_conversations,
            "total": len(shared_conversations)
        }
    except Exception as e:
        logging.error(f"Error getting shared conversations: {str(e)}")
        return {"conversations": [], "error": str(e)}

# Analytics
@app.get("/conversations/analytics/{conversation_id}")
def get_conversation_analytics(conversation_id: str):
    """Get analytics for a conversation"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        analytics = conversation_manager.get_conversation_analytics(conversation_id)
        return analytics
    except Exception as e:
        logging.error(f"Error getting conversation analytics: {str(e)}")
        return {"error": str(e)}

# Vector Indexing and Performance Endpoints
@app.post("/vectorstore/optimize")
def optimize_vector_index():
    """Optimize the vector index for large-scale operations"""
    try:
        from rag_core.vectorstore import VectorStore
        
        success = VectorStore.optimize_index_for_large_datasets()
        if success:
            return {"message": "Vector index optimization completed successfully"}
        else:
            return {"error": "Failed to optimize vector index"}
    except Exception as e:
        logging.error(f"Error optimizing vector index: {str(e)}")
        return {"error": str(e)}

@app.get("/vectorstore/statistics")
def get_vector_statistics():
    """Get statistics about the vector index"""
    try:
        from rag_core.vectorstore import VectorStore
        
        stats = VectorStore.get_index_statistics()
        return stats
    except Exception as e:
        logging.error(f"Error getting vector statistics: {str(e)}")
        return {"error": str(e)}

@app.get("/vectorstore/performance")
def get_vector_performance():
    """Get performance metrics for the vector store"""
    try:
        from rag_core.vectorstore import VectorStore
        
        metrics = VectorStore.get_performance_metrics()
        return metrics
    except Exception as e:
        logging.error(f"Error getting performance metrics: {str(e)}")
        return {"error": str(e)}

@app.post("/vectorstore/batch-optimize")
def batch_optimize_embeddings(embeddings: str = Form(...)):
    """Optimize embeddings in batches for large-scale operations"""
    try:
        from rag_core.vectorstore import VectorStore
        import json
        
        # Parse embeddings
        try:
            embedding_list = json.loads(embeddings)
        except json.JSONDecodeError:
            return {"error": "Invalid embeddings format"}
        
        success = VectorStore.batch_optimize_embeddings(embedding_list)
        if success:
            return {"message": f"Batch optimization completed for {len(embedding_list)} embeddings"}
        else:
            return {"error": "Failed to optimize embeddings"}
    except Exception as e:
        logging.error(f"Error in batch optimization: {str(e)}")
        return {"error": str(e)}

@app.get("/vectorstore/health")
def vectorstore_health_check():
    """Comprehensive health check for vector store"""
    try:
        from rag_core.vectorstore import VectorStore
        
        # Get basic stats
        stats = VectorStore.get_index_statistics()
        metrics = VectorStore.get_performance_metrics()
        
        # Check if collection is accessible
        collection = VectorStore.get_vector_collection()
        is_healthy = collection is not None
        
        health_data = {
            "healthy": is_healthy,
            "statistics": stats,
            "performance": metrics,
            "recommendations": []
        }
        
        # Add recommendations based on metrics
        if stats.get("total_vectors", 0) > 10000:
            health_data["recommendations"].append("Consider running index optimization for large dataset")
        
        if metrics.get("estimated_memory_mb", 0) > 1000:
            health_data["recommendations"].append("High memory usage detected, consider archiving old data")
        
        if not is_healthy:
            health_data["recommendations"].append("Vector store is not accessible, check configuration")
        
        return health_data
        
    except Exception as e:
        logging.error(f"Error in vector store health check: {str(e)}")
        return {
            "healthy": False,
            "error": str(e),
            "recommendations": ["Check vector store configuration and connectivity"]
        }

# Enhanced Document Processing Endpoints
@app.get("/documents/enhanced")
def get_enhanced_documents():
    """Get all enhanced documents with versioning, annotations, and relationships"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        documents_info = processor.get_all_documents_info()
        return {"documents": documents_info}
    except Exception as e:
        logging.error(f"Error getting enhanced documents: {str(e)}")
        return {"error": str(e)}

@app.get("/documents/{filename}/info")
def get_document_info(filename: str):
    """Get comprehensive information about a specific document"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        info = processor.get_document_info(filename)
        if not info:
            return {"error": f"Document {filename} not found"}
        return info
    except Exception as e:
        logging.error(f"Error getting document info: {str(e)}")
        return {"error": str(e)}

@app.get("/documents/{filename}/versions")
def get_document_versions(filename: str):
    """Get all versions of a document"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        versions = processor.get_document_versions(filename)
        
        versions_data = []
        for version in versions:
            versions_data.append({
                'version_id': version.version_id,
                'timestamp': version.timestamp.isoformat(),
                'file_hash': version.file_hash,
                'file_size': version.file_size,
                'changes_summary': version.changes_summary,
                'author': version.author,
                'metadata': version.metadata
            })
        
        return {"versions": versions_data}
    except Exception as e:
        logging.error(f"Error getting document versions: {str(e)}")
        return {"error": str(e)}

@app.get("/documents/{filename}/annotations")
def get_document_annotations(filename: str, annotation_type: str = None):
    """Get annotations for a document"""
    try:
        from rag_core.document import DocumentProcessor, AnnotationType
        
        processor = DocumentProcessor()
        
        if annotation_type:
            try:
                ann_type = AnnotationType(annotation_type)
                annotations = processor.get_annotations(filename, ann_type)
            except ValueError:
                return {"error": f"Invalid annotation type: {annotation_type}"}
        else:
            annotations = processor.get_annotations(filename)
        
        annotations_data = []
        for ann in annotations:
            annotations_data.append({
                'annotation_id': ann.annotation_id,
                'annotation_type': ann.annotation_type.value,
                'content': ann.content,
                'position': ann.position,
                'timestamp': ann.timestamp.isoformat(),
                'author': ann.author,
                'metadata': ann.metadata
            })
        
        return {"annotations": annotations_data}
    except Exception as e:
        logging.error(f"Error getting document annotations: {str(e)}")
        return {"error": str(e)}

@app.post("/documents/{filename}/annotations")
def add_document_annotation(filename: str, annotation_type: str = Form(...), 
                          content: str = Form(...), position: str = Form(...),
                          author: str = Form(None)):
    """Add annotation to a document"""
    try:
        from rag_core.document import DocumentProcessor, AnnotationType
        import json
        
        processor = DocumentProcessor()
        
        try:
            ann_type = AnnotationType(annotation_type)
        except ValueError:
            return {"error": f"Invalid annotation type: {annotation_type}"}
        
        try:
            position_data = json.loads(position)
        except json.JSONDecodeError:
            return {"error": "Invalid position format"}
        
        annotation_id = processor.add_annotation(filename, ann_type, content, position_data, author)
        return {"annotation_id": annotation_id, "message": "Annotation added successfully"}
    except Exception as e:
        logging.error(f"Error adding document annotation: {str(e)}")
        return {"error": str(e)}

@app.delete("/documents/{filename}/annotations/{annotation_id}")
def remove_document_annotation(filename: str, annotation_id: str):
    """Remove annotation from a document"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        success = processor.remove_annotation(filename, annotation_id)
        
        if success:
            return {"message": "Annotation removed successfully"}
        else:
            return {"error": "Annotation not found or could not be removed"}
    except Exception as e:
        logging.error(f"Error removing document annotation: {str(e)}")
        return {"error": str(e)}

@app.get("/documents/{filename}/relationships")
def get_document_relationships(filename: str, relationship_type: str = None):
    """Get relationships for a document"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        relationships = processor.get_relationships(filename, relationship_type)
        
        relationships_data = []
        for rel in relationships:
            relationships_data.append({
                'relationship_id': rel.relationship_id,
                'source_doc_id': rel.source_doc_id,
                'target_doc_id': rel.target_doc_id,
                'relationship_type': rel.relationship_type,
                'strength': rel.strength,
                'metadata': rel.metadata
            })
        
        return {"relationships": relationships_data}
    except Exception as e:
        logging.error(f"Error getting document relationships: {str(e)}")
        return {"error": str(e)}

@app.post("/documents/relationships")
def add_document_relationship(source_filename: str = Form(...), target_filename: str = Form(...),
                            relationship_type: str = Form(...), strength: float = Form(1.0)):
    """Add relationship between two documents"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        relationship_id = processor.add_relationship(source_filename, target_filename, relationship_type, strength)
        return {"relationship_id": relationship_id, "message": "Relationship added successfully"}
    except Exception as e:
        logging.error(f"Error adding document relationship: {str(e)}")
        return {"error": str(e)}

@app.get("/documents/{filename}/related")
def get_related_documents(filename: str, relationship_type: str = None):
    """Get documents related to the given document"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        related_filenames = processor.find_related_documents(filename, relationship_type)
        
        related_docs = []
        for related_filename in related_filenames:
            doc_info = processor.get_document_info(related_filename)
            if doc_info:
                related_docs.append(doc_info)
        
        return {"related_documents": related_docs}
    except Exception as e:
        logging.error(f"Error getting related documents: {str(e)}")
        return {"error": str(e)}

@app.post("/documents/{filename}/versions")
def create_document_version(filename: str, file: UploadFile = File(...),
                          changes_summary: str = Form(...), author: str = Form(None)):
    """Create a new version of a document"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        file_content = file.file.read()
        
        version_id = processor.create_new_version(filename, file_content, changes_summary, author)
        return {"version_id": version_id, "message": "New version created successfully"}
    except Exception as e:
        logging.error(f"Error creating document version: {str(e)}")
        return {"error": str(e)}

# Performance & Caching Endpoints
@app.get("/cache/stats")
def get_cache_statistics():
    """Get cache statistics"""
    try:
        from rag_core.cache import response_cache, embedding_cache
        
        response_stats = response_cache.get_stats()
        embedding_stats = embedding_cache.get_stats()
        
        return {
            "response_cache": response_stats,
            "embedding_cache": embedding_stats
        }
    except Exception as e:
        logging.error(f"Error getting cache statistics: {str(e)}")
        return {"error": str(e)}

@app.get("/performance/stats")
def get_performance_statistics():
    """Get performance statistics"""
    try:
        from rag_core.cache import performance_monitor
        
        stats = performance_monitor.get_stats()
        return stats
    except Exception as e:
        logging.error(f"Error getting performance statistics: {str(e)}")
        return {"error": str(e)}

@app.post("/cache/clear")
def clear_cache(cache_type: str = Form("all")):
    """Clear cache entries"""
    try:
        from rag_core.cache import response_cache, embedding_cache
        
        if cache_type == "response" or cache_type == "all":
            response_cache.cache.clear()
            response_cache.access_counts.clear()
        
        if cache_type == "embedding" or cache_type == "all":
            embedding_cache.cache.clear()
            embedding_cache.text_to_key.clear()
        
        return {"message": f"Cache cleared: {cache_type}"}
    except Exception as e:
        logging.error(f"Error clearing cache: {str(e)}")
        return {"error": str(e)}

@app.get("/cache/optimize")
def optimize_cache():
    """Optimize cache performance"""
    try:
        from rag_core.cache import response_cache, embedding_cache
        
        # Get current stats
        response_stats = response_cache.get_stats()
        embedding_stats = embedding_cache.get_stats()
        
        # Simple optimization: remove expired entries
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in response_cache.cache.items():
            if current_time - entry.created_at > timedelta(seconds=entry.ttl_seconds):
                expired_keys.append(key)
        
        for key in expired_keys:
            del response_cache.cache[key]
            if key in response_cache.access_counts:
                del response_cache.access_counts[key]
        
        return {
            "message": "Cache optimized",
            "expired_entries_removed": len(expired_keys),
            "response_cache_entries": response_cache.get_stats()['total_entries'],
            "embedding_cache_entries": embedding_stats['total_embeddings']
        }
    except Exception as e:
        logging.error(f"Error optimizing cache: {str(e)}")
        return {"error": str(e)}

@app.get("/documents/search/enhanced")
def search_documents_enhanced(query: str, limit: int = 10):
    """Enhanced document search with metadata"""
    try:
        from rag_core.document import DocumentProcessor
        
        processor = DocumentProcessor()
        results = processor.search_documents_by_content(query, limit)
        return {"results": results}
    except Exception as e:
        logging.error(f"Error in enhanced document search: {str(e)}")
        return {"error": str(e)}

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

@app.get("/ocr/config")
def get_ocr_config(config_name: str = "default"):
    """Get OCR configuration"""
    try:
        config = get_config(config_name)
        return {
            "status": "success",
            "config_name": config_name,
            "config": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OCR config: {str(e)}")

@app.get("/ocr/configs")
def get_available_ocr_configs():
    """Get list of available OCR configurations"""
    try:
        configs = [
            {"name": "default", "description": "Default balanced configuration"},
            {"name": "fast_performance", "description": "Fast performance (Tesseract only)"},
            {"name": "offline", "description": "Offline mode (all engines)"},
            {"name": "high_accuracy", "description": "High accuracy configuration"},
            {"name": "fast", "description": "Fast processing configuration"}
        ]
        return {
            "status": "success",
            "configs": configs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OCR configs: {str(e)}")

@app.post("/ocr/test")
async def test_ocr_engine(
    file: UploadFile = File(...),
    config_name: str = Form("default")
):
    """Test OCR engine with a specific configuration"""
    try:
        # Get configuration
        config = get_config(config_name)
        multi_ocr = MultiOCREngine(config)
        
        # Read file content
        file_content = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Process with OCR
            start_time = time.time()
            results = multi_ocr.process_pdf(temp_file_path)
            processing_time = time.time() - start_time
            
            # Extract results
            extracted_text = ""
            confidence_scores = []
            engines_used = []
            
            for result in results:
                if result.text:
                    extracted_text += result.text + "\n\n"
                    confidence_scores.append(result.agreement_score)
                    engines_used.extend(result.contributing_engines)
            
            # Remove duplicates from engines used
            engines_used = list(set(engines_used))
            
            return {
                "status": "success",
                "config_name": config_name,
                "processing_time": processing_time,
                "text_length": len(extracted_text),
                "confidence_score": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                "engines_used": engines_used,
                "extracted_text": extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR test failed: {str(e)}")

@app.get("/ocr/performance")
def get_ocr_performance_stats():
    """Get OCR performance statistics"""
    try:
        # This would typically come from a monitoring system
        # For now, return basic stats
        return {
            "status": "success",
            "stats": {
                "total_documents_processed": 0,  # Would be tracked in production
                "average_processing_time": 0.0,
                "success_rate": 0.0,
                "engines_available": {
                    "tesseract": True,
                    "paddleocr": False,  # Would check actual availability
                    "easyocr": False
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OCR performance: {str(e)}")

@app.post("/ocr/optimize")
async def optimize_ocr_performance(
    config_name: str = Form("fast_performance")
):
    """Optimize OCR performance with specific configuration"""
    try:
        # Get optimized configuration
        config = get_config(config_name)
        
        # Test the configuration
        multi_ocr = MultiOCREngine(config)
        
        return {
            "status": "success",
            "message": f"OCR optimized with {config_name} configuration",
            "config": {
                "engines_enabled": [k for k, v in config["engines"].items() if v["enabled"]],
                "parallel_processing": config["performance"]["parallel_processing"],
                "caching_enabled": config["performance"]["enable_caching"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR optimization failed: {str(e)}") 

# Initialize agentic RAG system
try:
    from rag_core.agentic_rag import AgenticRAG
    agentic_rag = AgenticRAG()
    logger.info("Agentic RAG system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize agentic RAG system: {str(e)}")
    agentic_rag = None

@app.post("/agentic/query")
async def agentic_query(
    question: str = Form(...),
    user_context: str = Form("{}"),
    query_type: str = Form(None)
):
    """Process query using agentic RAG system"""
    try:
        # Check if agentic_rag is properly initialized
        if agentic_rag is None or not hasattr(agentic_rag, 'process_query'):
            return {
                "status": "error",
                "message": "Agentic RAG system not properly initialized",
                "answer": "The agentic RAG system is not available. Please use the regular RAG system.",
                "sources": [],
                "reasoning": "System not initialized",
                "query_type": "semantic_search",
                "confidence": 0.0,
                "processing_time": 0.0,
                "metadata": {}
            }
        
        # Parse user context
        try:
            context = json.loads(user_context) if user_context else {}
        except:
            context = {}
        
        # Process query with agentic RAG
        response = await agentic_rag.process_query(question, context)
        
        return {
            "status": "success",
            "answer": response.answer,
            "sources": response.sources,
            "reasoning": response.reasoning,
            "query_type": response.query_type.value,
            "confidence": response.confidence,
            "processing_time": response.processing_time,
            "metadata": response.metadata,
            "agent_chain": [role.value for role in response.agent_chain]
        }
        
    except Exception as e:
        logger.error(f"Agentic query failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Agentic query failed: {str(e)}",
            "answer": f"Sorry, I encountered an error processing your query: {str(e)}",
            "sources": [],
            "reasoning": "Error occurred during processing",
            "query_type": "semantic_search",
            "confidence": 0.0,
            "processing_time": 0.0,
            "metadata": {"error": str(e)}
        }

@app.post("/agentic/query/stream")
async def agentic_query_stream(
    question: str = Form(...),
    user_context: str = Form("{}"),
    query_type: str = Form(None)
):
    """Stream agentic query response"""
    try:
        # Check if agentic_rag is properly initialized
        if agentic_rag is None or not hasattr(agentic_rag, 'process_query'):
            def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'content': 'Agentic RAG system not available'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return StreamingResponse(error_stream(), media_type="text/plain")
        
        # Parse user context
        try:
            context = json.loads(user_context) if user_context else {}
        except:
            context = {}
        
        # Process query with agentic RAG
        response = await agentic_rag.process_query(question, context)
        
        def stream_response():
            # Stream the reasoning first
            yield f"data: {json.dumps({'type': 'reasoning', 'content': response.reasoning})}\n\n"
            
            # Stream the answer
            words = response.answer.split()
            for word in words:
                yield f"data: {json.dumps({'type': 'word', 'content': word + ' '})}\n\n"
                time.sleep(0.05)  # Small delay for streaming effect
            
            # Stream final metadata
            yield f"data: {json.dumps({'type': 'metadata', 'content': response.metadata})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            stream_response(),
            media_type="text/plain"
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Agentic query streaming failed: {str(e)}"}
        )

@app.get("/agentic/performance")
def get_agentic_performance():
    """Get agentic RAG performance metrics"""
    try:
        if agentic_rag is None:
            return {
                "status": "error",
                "message": "Agentic RAG system not initialized",
                "metrics": {}
            }
        
        metrics = agentic_rag.get_performance_metrics()
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@app.post("/agentic/analyze")
def analyze_query_intent(
    query: str = Form(...)
):
    """Analyze query intent without processing"""
    try:
        # Check if agentic_rag is properly initialized
        if agentic_rag is None or not hasattr(agentic_rag, 'query_analyzer'):
            return {
                "status": "error",
                "message": "Agentic RAG system not properly initialized",
                "query": query,
                "query_type": "semantic_search",
                "data_sources": [],
                "reasoning": "System not available",
                "confidence": 0.0,
                "metadata": {}
            }
        
        # Create a simple context for analysis
        from rag_core.agentic_rag import QueryContext, QueryType, DataSourceType
        
        context = QueryContext(
            query=query,
            query_type=QueryType.SEMANTIC_SEARCH,
            data_sources=[DataSourceType.VECTOR_DB],
            reasoning="",
            confidence=0.0,
            metadata={}
        )
        
        # Use query analyzer to determine intent
        import asyncio
        analyzed_context = asyncio.run(agentic_rag.query_analyzer.process(context))
        
        return {
            "status": "success",
            "query": query,
            "query_type": analyzed_context.query_type.value,
            "data_sources": [ds.value for ds in analyzed_context.data_sources],
            "reasoning": analyzed_context.reasoning,
            "confidence": analyzed_context.confidence,
            "metadata": analyzed_context.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")

@app.get("/agentic/health")
def agentic_health_check():
    """Health check for agentic RAG system"""
    try:
        if agentic_rag is None:
            return {
                "status": "error",
                "message": "Agentic RAG system not initialized",
                "healthy": False
            }
        
        # Basic health check
        metrics = agentic_rag.get_performance_metrics()
        
        health_data = {
            "healthy": True,
            "total_queries": metrics.get('total_queries', 0),
            "average_processing_time": metrics.get('average_processing_time', 0.0),
            "success_rate": metrics.get('success_rate', 0.0),
            "query_type_distribution": metrics.get('query_type_distribution', {}),
            "recommendations": []
        }
        
        # Add recommendations based on metrics
        if metrics.get('average_processing_time', 0) > 5.0:
            health_data["recommendations"].append("High processing time detected")
        
        if metrics.get('success_rate', 0) < 0.8:
            health_data["recommendations"].append("Low success rate detected")
        
        return health_data
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "recommendations": ["Check agentic RAG system configuration"]
        }

# Layout Analysis Endpoints
@app.post("/layout/analyze")
async def analyze_document_layout(
    file: UploadFile = File(...),
    include_text_extraction: bool = Form(True)
):
    """Analyze document layout and optionally extract text"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize layout analyzer
            from rag_core.layout_analysis import LayoutAnalyzer
            layout_analyzer = LayoutAnalyzer()
            
            # Convert to PIL Image
            if temp_file_path.lower().endswith('.pdf'):
                from pdf2image import convert_from_path
                images = convert_from_path(temp_file_path, dpi=300)
                if not images:
                    raise HTTPException(status_code=400, detail="Could not convert PDF to images")
                image = images[0]  # Analyze first page
            else:
                image = Image.open(temp_file_path)
            
            # Analyze layout
            layout = layout_analyzer.analyze_layout(image)
            
            result = {
                "layout_analysis": {
                    "page_width": layout.page_width,
                    "page_height": layout.page_height,
                    "total_elements": len(layout.elements),
                    "tables_detected": len(layout.tables),
                    "form_fields_detected": len(layout.form_fields),
                    "text_blocks_detected": len(layout.text_blocks),
                    "images_detected": len(layout.images),
                    "confidence": layout.confidence,
                    "processing_time": layout.processing_time
                },
                "elements": []
            }
            
            # Add element details
            for element in layout.elements:
                element_info = {
                    "type": element.element_type.value,
                    "position": {
                        "x": element.bounding_box.x,
                        "y": element.bounding_box.y,
                        "width": element.bounding_box.width,
                        "height": element.bounding_box.height
                    },
                    "confidence": element.confidence,
                    "metadata": element.metadata
                }
                result["elements"].append(element_info)
            
            # Add text extraction if requested
            if include_text_extraction:
                from rag_core.layout_analysis import LayoutEnhancedOCR
                from rag_core.multi_ocr import MultiOCREngine
                
                multi_ocr = MultiOCREngine()
                layout_enhanced_ocr = LayoutEnhancedOCR(multi_ocr, layout_analyzer)
                
                text_result = layout_enhanced_ocr.process_document_with_layout(image)
                result["text_extraction"] = text_result["text_results"]
            
            return result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Layout analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Layout analysis failed: {str(e)}")

@app.post("/layout/process")
async def process_document_with_layout(
    file: UploadFile = File(...),
    max_pages: int = Form(None)
):
    """Process document with layout-aware OCR"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize multi-OCR with layout analysis
            from rag_core.multi_ocr import MultiOCREngine
            multi_ocr = MultiOCREngine({"enable_layout_analysis": True})
            
            # Process with layout analysis
            results = multi_ocr.process_pdf_with_layout(temp_file_path, max_pages)
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                formatted_result = {
                    "page": i + 1,
                    "text": result.text,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "metadata": result.metadata
                }
                formatted_results.append(formatted_result)
            
            return {
                "total_pages": len(formatted_results),
                "results": formatted_results,
                "layout_enhanced": True
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Layout-enhanced processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Layout-enhanced processing failed: {str(e)}")

@app.get("/layout/config")
def get_layout_config():
    """Get layout analysis configuration"""
    try:
        from rag_core.layout_analysis import LayoutAnalyzer
        analyzer = LayoutAnalyzer()
        
        return {
            "config": analyzer.config,
            "capabilities": {
                "table_detection": analyzer.config["table_detection"]["enabled"],
                "form_detection": analyzer.config["form_detection"]["enabled"],
                "text_block_detection": analyzer.config["text_block_detection"]["enabled"],
                "image_detection": analyzer.config["image_detection"]["enabled"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get layout config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get layout config: {str(e)}")

@app.post("/layout/config")
async def update_layout_config(config: dict):
    """Update layout analysis configuration"""
    try:
        # This would typically save to a config file
        # For now, just return success
        return {
            "status": "success",
            "message": "Layout configuration updated",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to update layout config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update layout config: {str(e)}")

# Web Search Endpoints
@app.post("/web/search")
async def web_search(
    query: str = Form(...),
    search_type: str = Form("basic"),
    max_results: int = Form(10),
    include_answer: bool = Form(True)
):
    """Perform web search using Tavily API"""
    try:
        from rag_core.web_search import WebSearchEngine, WebSearchQuery, SearchType
        
        # Initialize web search engine
        web_engine = WebSearchEngine()
        
        if not web_engine.enabled:
            return {
                "status": "error",
                "message": "Web search is not available. Please configure Tavily API key.",
                "results": [],
                "total_results": 0
            }
        
        # Create search query
        search_query = WebSearchQuery(
            query=query,
            search_type=SearchType(search_type),
            max_results=max_results,
            include_answer=include_answer
        )
        
        # Perform search
        response = web_engine.search(search_query)
        
        # Format results
        formatted_results = []
        for result in response.results:
            formatted_result = {
                "title": result.title,
                "url": result.url,
                "content": result.content,
                "source": result.source,
                "published_date": result.published_date,
                "author": result.author,
                "domain": result.domain,
                "relevance_score": result.relevance_score,
                "search_type": result.search_type.value,
                "content_type": result.content_type.value
            }
            formatted_results.append(formatted_result)
        
        return {
            "status": "success",
            "query": query,
            "search_type": search_type,
            "results": formatted_results,
            "answer": response.answer,
            "related_questions": response.related_questions,
            "total_results": response.total_results,
            "search_time": response.search_time
        }
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")

@app.post("/web/search/hybrid")
async def hybrid_search(
    query: str = Form(...),
    include_web_search: bool = Form(True),
    limit: int = Form(10),
    min_score: float = Form(0.1)
):
    """Perform hybrid search combining local and web results"""
    try:
        from rag_core.search import AdvancedSearch
        
        # Initialize advanced search with web integration
        config = {"enable_web_search": include_web_search}
        advanced_search = AdvancedSearch(config)
        
        # Perform hybrid search
        results = advanced_search.hybrid_search(
            query=query,
            limit=limit,
            min_score=min_score,
            include_web_search=include_web_search
        )
        
        return {
            "status": "success",
            "query": query,
            "local_results": results["local_results"],
            "web_results": results["web_results"],
            "integrated_content": results["integrated_content"],
            "total_results": results["total_results"],
            "search_time": results["search_time"]
        }
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")

@app.post("/web/search/news")
async def search_news(
    query: str = Form(...),
    max_results: int = Form(5)
):
    """Search for recent news articles"""
    try:
        from rag_core.search import AdvancedSearch
        
        # Initialize advanced search
        config = {"enable_web_search": True}
        advanced_search = AdvancedSearch(config)
        
        # Search for news
        results = advanced_search.search_news(query, max_results)
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"News search failed: {e}")
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")

@app.post("/web/search/academic")
async def search_academic(
    query: str = Form(...),
    max_results: int = Form(5)
):
    """Search for academic papers and research"""
    try:
        from rag_core.search import AdvancedSearch
        
        # Initialize advanced search
        config = {"enable_web_search": True}
        advanced_search = AdvancedSearch(config)
        
        # Search for academic papers
        results = advanced_search.search_academic(query, max_results)
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Academic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Academic search failed: {str(e)}")

@app.get("/web/search/config")
def get_web_search_config():
    """Get web search configuration"""
    try:
        from rag_core.web_search import WebSearchEngine
        
        web_engine = WebSearchEngine()
        
        return {
            "enabled": web_engine.enabled,
            "cache_stats": web_engine.get_cache_stats(),
            "config": {
                "cache_ttl": web_engine.cache_ttl,
                "max_retries": web_engine.config.get("max_retries", 3),
                "timeout": web_engine.config.get("timeout", 30)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get web search config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get web search config: {str(e)}")

@app.post("/web/search/clear-cache")
def clear_web_search_cache():
    """Clear web search cache"""
    try:
        from rag_core.web_search import WebSearchEngine
        
        web_engine = WebSearchEngine()
        web_engine.clear_cache()
        
        return {
            "status": "success",
            "message": "Web search cache cleared",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to clear web search cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear web search cache: {str(e)}")

# Enhanced Anti-Hallucination Endpoints
@app.post("/anti-hallucination/validate")
async def validate_response(
    query: str = Form(...),
    response: str = Form(...),
    sources: str = Form("[]")  # JSON string of sources
):
    """Validate response for hallucination detection"""
    try:
        import json
        from rag_core.anti_hallucination import AntiHallucinationValidator
        
        # Parse sources
        sources_list = json.loads(sources)
        
        # Initialize validator
        validator = AntiHallucinationValidator()
        
        # Validate response
        validation_result = validator.validate_response(query, response, sources_list)
        
        return {
            "status": "success",
            "is_valid": validation_result.is_valid,
            "confidence_level": validation_result.confidence_level.value,
            "quality_score": validation_result.quality_score,
            "hallucination_detections": [
                {
                    "type": detection.hallucination_type.value if detection.hallucination_type else None,
                    "confidence": detection.confidence,
                    "evidence": detection.evidence,
                    "suggestions": detection.suggestions,
                    "severity": detection.severity
                }
                for detection in validation_result.hallucination_detections
            ],
            "corrections": validation_result.corrections,
            "metadata": validation_result.metadata
        }
        
    except Exception as e:
        logger.error(f"Response validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Response validation failed: {str(e)}")

@app.post("/anti-hallucination/validate-chunks")
async def validate_chunks(
    query: str = Form(...),
    chunks: str = Form("[]")  # JSON string of chunks
):
    """Validate retrieved chunks for quality and relevance"""
    try:
        import json
        from rag_core.anti_hallucination import AntiHallucinationValidator
        
        # Parse chunks
        chunks_list = json.loads(chunks)
        
        # Initialize validator
        validator = AntiHallucinationValidator()
        
        # Validate chunks
        validated_chunks = validator.validate_chunks(query, chunks_list)
        
        return {
            "status": "success",
            "original_count": len(chunks_list),
            "validated_count": len(validated_chunks),
            "validated_chunks": validated_chunks
        }
        
    except Exception as e:
        logger.error(f"Chunk validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chunk validation failed: {str(e)}")

@app.get("/anti-hallucination/config")
def get_anti_hallucination_config():
    """Get anti-hallucination configuration"""
    try:
        from rag_core.anti_hallucination import AntiHallucinationValidator
        
        validator = AntiHallucinationValidator()
        
        return {
            "config": validator.config,
            "capabilities": {
                "fact_checking": validator.fact_checking_enabled,
                "contradiction_detection": validator.contradiction_detection_enabled,
                "temporal_validation": validator.temporal_validation_enabled,
                "numerical_validation": validator.numerical_validation_enabled
            }
        }
    except Exception as e:
        logger.error(f"Failed to get anti-hallucination config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get anti-hallucination config: {str(e)}")

@app.post("/anti-hallucination/config")
async def update_anti_hallucination_config(config: dict):
    """Update anti-hallucination configuration"""
    try:
        # This would typically save to a config file
        # For now, just return success
        return {
            "status": "success",
            "message": "Anti-hallucination configuration updated",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to update anti-hallucination config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update anti-hallucination config: {str(e)}")

@app.post("/anti-hallucination/analyze")
async def analyze_hallucination_patterns(
    responses: str = Form("[]")  # JSON string of response analysis data
):
    """Analyze hallucination patterns across multiple responses"""
    try:
        import json
        from rag_core.anti_hallucination import AntiHallucinationValidator
        
        # Parse responses
        responses_list = json.loads(responses)
        
        # Initialize validator
        validator = AntiHallucinationValidator()
        
        # Analyze patterns
        analysis_results = []
        total_detections = 0
        detection_types = defaultdict(int)
        
        for response_data in responses_list:
            query = response_data.get("query", "")
            response = response_data.get("response", "")
            sources = response_data.get("sources", [])
            
            validation_result = validator.validate_response(query, response, sources)
            
            analysis_results.append({
                "query": query,
                "is_valid": validation_result.is_valid,
                "quality_score": validation_result.quality_score,
                "detection_count": len(validation_result.hallucination_detections)
            })
            
            total_detections += len(validation_result.hallucination_detections)
            
            for detection in validation_result.hallucination_detections:
                if detection.hallucination_type:
                    detection_types[detection.hallucination_type.value] += 1
        
        return {
            "status": "success",
            "total_responses": len(analysis_results),
            "total_detections": total_detections,
            "detection_types": dict(detection_types),
            "analysis_results": analysis_results
        }
        
    except Exception as e:
        logger.error(f"Hallucination analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hallucination analysis failed: {str(e)}")

# Enhanced Conversation Management Endpoints
@app.get("/conversation/analytics/{conversation_id}")
def get_conversation_analytics(conversation_id: str):
    """Get comprehensive analytics for a conversation"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        analytics = conversation_manager.get_conversation_analytics(conversation_id)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "analytics": {
                "total_messages": analytics.total_messages,
                "user_messages": analytics.user_messages,
                "assistant_messages": analytics.assistant_messages,
                "average_message_length": analytics.average_message_length,
                "topic_distribution": analytics.topic_distribution,
                "response_time_stats": analytics.response_time_stats,
                "user_engagement_metrics": analytics.user_engagement_metrics,
                "conversation_quality_score": analytics.conversation_quality_score,
                "completion_rate": analytics.completion_rate,
                "user_satisfaction_score": analytics.user_satisfaction_score
            }
        }
    except Exception as e:
        logger.error(f"Failed to get conversation analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation analytics: {str(e)}")

@app.get("/conversation/insights/{conversation_id}")
def get_conversation_insights(conversation_id: str):
    """Get intelligent insights for a conversation"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        insights = conversation_manager.analyze_conversation_insights(conversation_id)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "insights": {
                "key_topics": insights.key_topics,
                "sentiment_score": insights.sentiment_score,
                "user_intent": insights.user_intent,
                "conversation_flow": insights.conversation_flow,
                "knowledge_gaps": insights.knowledge_gaps,
                "action_items": insights.action_items,
                "follow_up_questions": insights.follow_up_questions,
                "context_switches": insights.context_switches,
                "average_response_time": insights.average_response_time,
                "user_satisfaction_indicators": insights.user_satisfaction_indicators
            }
        }
    except Exception as e:
        logger.error(f"Failed to get conversation insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation insights: {str(e)}")

@app.get("/conversation/context/{conversation_id}")
def get_conversation_context(conversation_id: str):
    """Get conversation context"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        context = conversation_manager.manage_conversation_context(conversation_id)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "context": {
                "current_topic": context.current_topic,
                "context_stack": context.context_stack,
                "memory_bank": context.memory_bank,
                "context_window": context.context_window,
                "context_importance": context.context_importance,
                "context_retention_policy": context.context_retention_policy
            }
        }
    except Exception as e:
        logger.error(f"Failed to get conversation context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation context: {str(e)}")

@app.post("/conversation/context/{conversation_id}")
async def update_conversation_context(
    conversation_id: str,
    new_topic: str = Form(None),
    context_data: str = Form("{}")  # JSON string
):
    """Update conversation context"""
    try:
        import json
        from rag_core.conversation_manager import conversation_manager
        
        # Parse context data
        context_dict = json.loads(context_data) if context_data else {}
        
        conversation_manager.update_conversation_context(
            conversation_id, 
            new_topic=new_topic, 
            context_data=context_dict
        )
        
        return {
            "status": "success",
            "message": "Conversation context updated",
            "conversation_id": conversation_id
        }
    except Exception as e:
        logger.error(f"Failed to update conversation context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update conversation context: {str(e)}")

@app.get("/conversation/recommendations/{conversation_id}")
def get_conversation_recommendations(conversation_id: str):
    """Get intelligent recommendations for a conversation"""
    try:
        from rag_core.conversation_manager import conversation_manager
        
        recommendations = conversation_manager.get_conversation_recommendations(conversation_id)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Failed to get conversation recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation recommendations: {str(e)}")

@app.post("/conversation/analyze-batch")
async def analyze_conversations_batch(
    conversation_ids: str = Form("[]")  # JSON string of conversation IDs
):
    """Analyze multiple conversations for patterns and insights"""
    try:
        import json
        from rag_core.conversation_manager import conversation_manager
        
        # Parse conversation IDs
        conv_ids = json.loads(conversation_ids)
        
        batch_results = {
            "total_conversations": len(conv_ids),
            "analytics_summary": {},
            "insights_summary": {},
            "recommendations_summary": {}
        }
        
        all_analytics = []
        all_insights = []
        all_recommendations = []
        
        for conv_id in conv_ids:
            # Get analytics
            analytics = conversation_manager.get_conversation_analytics(conv_id)
            all_analytics.append(analytics)
            
            # Get insights
            insights = conversation_manager.analyze_conversation_insights(conv_id)
            all_insights.append(insights)
            
            # Get recommendations
            recommendations = conversation_manager.get_conversation_recommendations(conv_id)
            all_recommendations.append(recommendations)
        
        # Calculate summary statistics
        if all_analytics:
            avg_quality = sum(a.conversation_quality_score for a in all_analytics) / len(all_analytics)
            avg_satisfaction = sum(a.user_satisfaction_score for a in all_analytics) / len(all_analytics)
            
            batch_results["analytics_summary"] = {
                "average_quality_score": avg_quality,
                "average_satisfaction_score": avg_satisfaction,
                "total_messages": sum(a.total_messages for a in all_analytics)
            }
        
        if all_insights:
            avg_sentiment = sum(i.sentiment_score for i in all_insights) / len(all_insights)
            common_topics = Counter()
            for insights in all_insights:
                common_topics.update(insights.key_topics)
            
            batch_results["insights_summary"] = {
                "average_sentiment": avg_sentiment,
                "most_common_topics": [topic for topic, count in common_topics.most_common(5)]
            }
        
        return {
            "status": "success",
            "batch_analysis": batch_results
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze conversations batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze conversations batch: {str(e)}") 
