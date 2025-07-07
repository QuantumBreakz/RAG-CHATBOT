import os
import tempfile
import streamlit as st
import json
import logging
import time
from typing import List, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv
import ollama
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredWordDocumentLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from streamlit.runtime.uploaded_file_manager import UploadedFile
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import pickle

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")

# Application Configuration
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB default
DEFAULT_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 400))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
DEFAULT_N_RESULTS = int(os.getenv("N_RESULTS", 10))

# Database Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./demo-rag-chroma")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "pitb_rag_app_demo")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "pitb_rag_app.log")

# Cache Configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))
EMBEDDINGS_CACHE_PATH = os.getenv("EMBEDDINGS_CACHE_PATH", "data/embeddings_cache")

# System prompt
SYSTEM_PROMPT = """
You are an AI assistant developed by PITB, tasked with providing detailed answers based solely on the given context and conversation history. Your goal is to analyze the information provided and formulate a comprehensive, well-structured response to the question.

Context will be passed as "Context:"
Conversation history will be passed as "Conversation History:"
User question will be passed as "Question:"

To answer the question:
1. Thoroughly analyze the context and conversation history, identifying key information relevant to the question.
2. Organize your thoughts and plan your response to ensure a logical flow of information.
3. Formulate a detailed answer that directly addresses the question, using only the information provided in the context and conversation history.
4. Ensure your answer is comprehensive, covering all relevant aspects found in the context and history.
5. If the context and history don't contain sufficient information to fully answer the question, state this clearly in your response.

Format your response as follows:
1. Use clear, concise language, answer concisely, do not exceed max length of 300 words.
2. Organize your answer into paragraphs for readability.
3. Use bullet points or numbered lists where appropriate to break down complex information.
4. If relevant, include any headings or subheadings to structure your response.
5. Ensure proper grammar, punctuation, and spelling throughout your answer.
6. Perform calculations if required or if available in document given the previous stats.
"""

# Custom CSS for PITB-inspired UI
st.markdown("""
<style>
    .main {
        background-color: #f5f7fa;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #005566;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #007a8c;
        transform: scale(1.05);
    }
    .stTextArea textarea {
        border: 2px solid #005566;
        border-radius: 8px;
        background-color: #ffffff;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
        border-right: 2px solid #005566;
        padding: 20px;
    }
    .header {
        background: linear-gradient(90deg, #005566, #00a1b7);
        color: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
    }
    .footer {
        background-color: #005566;
        color: white;
        padding: 10px;
        text-align: center;
        margin-top: 20px;
        border-radius: 8px;
    }
    .stExpander {
        background-color: #e8ecef;
        border-radius: 8px;
    }
    .dark-mode {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .dark-mode .sidebar .sidebar-content {
        background-color: #2c2c2c;
        border-right: 2px solid #00a1b7;
    }
    .dark-mode .stTextArea textarea {
        background-color: #333333;
        color: #ffffff;
    }
    .dark-mode .stExpander {
        background-color: #2c2c2c;
    }
    @media (max-width: 600px) {
        .header, .footer {
            padding: 10px;
            font-size: 0.9em;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Custom Dark Theme and Layout ---
# Add custom CSS for dark mode and accent colors
st.markdown('''
<style>
body, .main, .stApp {
    background-color: #181c23 !important;
    color: #e6e6e6 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #232733 !important;
    color: #e6e6e6 !important;
    border-right: 1px solid #2e3440;
}

/* Sidebar header and upload */
.st-emotion-cache-1v0mbdj, .st-emotion-cache-1v0mbdj h1, .st-emotion-cache-1v0mbdj h2 {
    color: #e6e6e6 !important;
}

/* Accent buttons */
.stButton>button {
    background-color: #2ecc71 !important;
    color: #181c23 !important;
    border-radius: 6px;
    font-weight: bold;
    border: none;
    transition: 0.2s;
}
.stButton>button:hover {
    background-color: #27ae60 !important;
    color: #fff !important;
}

/* Chat bubbles */
.user-bubble {
    background: #232733;
    color: #e6e6e6;
    border-radius: 12px 12px 4px 12px;
    padding: 10px 16px;
    margin-bottom: 8px;
    max-width: 80%;
    align-self: flex-end;
}
.ai-bubble {
    background: #2d3548;
    color: #e6e6e6;
    border-radius: 12px 12px 12px 4px;
    padding: 10px 16px;
    margin-bottom: 8px;
    max-width: 80%;
    align-self: flex-start;
}

/* Info panel */
.info-panel {
    background: #232733;
    border-radius: 10px;
    padding: 18px 16px;
    margin-top: 10px;
    color: #e6e6e6;
}

/* Table and entity highlight */
.entity-table {
    background: #232733;
    color: #e6e6e6;
    border-radius: 6px;
    width: 100%;
}
.entity-highlight {
    background: #2ecc71;
    color: #181c23;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
}

/* File upload area */
.stFileUploader {
    background: #232733 !important;
    border-radius: 8px;
    border: 1px solid #2e3440;
    color: #e6e6e6 !important;
}

/* Remove Streamlit default shadows */
.st-emotion-cache-1v0mbdj, .st-emotion-cache-1v0mbdj * {
    box-shadow: none !important;
}

</style>
''', unsafe_allow_html=True)

# --- Layout: Sidebar, Main, Right Panel ---
sidebar = st.sidebar
sidebar.image("pitb.png", width=120, caption="PITB Logo")
sidebar.title("Conversations")

# --- File Upload Section ---
sidebar.markdown("""
#### File Collection
""")

uploaded_files = sidebar.file_uploader(
    "Drop File Here or Click to Upload",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    key="sidebar_file_uploader",
    help="Upload one or more PDF or DOCX files for question answering."
)

if uploaded_files:
    sidebar.markdown("**Uploaded Files:**")
    for f in uploaded_files:
        sidebar.markdown(f"- {f.name}")

# --- Conversation List Placeholder ---
sidebar.markdown("""
---
##### Conversations
- <span style='color:#2ecc71'>Session 1 (Ready)</span>
- Session 2
""", unsafe_allow_html=True)

# --- Quick Upload Placeholder ---
sidebar.markdown("""
---
##### Quick Upload
<div style='background:#232733; border-radius:8px; padding:10px; text-align:center;'>
Drop File Here<br>Click to Upload
</div>
""", unsafe_allow_html=True)

# Main layout: 3 columns (sidebar is handled by Streamlit)
col1, col2, col3 = st.columns([0.05, 0.6, 0.35], gap="large")

with col2:
    st.markdown("<h2 style='color:#e6e6e6;'>Chat</h2>", unsafe_allow_html=True)
    # --- Chat History ---
    chat_container = st.container()
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    with chat_container:
        st.markdown("<div style='height:400px; background:#232733; border-radius:10px; padding:16px; overflow-y:auto; display:flex; flex-direction:column;'>", unsafe_allow_html=True)
        for msg in st.session_state.conversation_history:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ai-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    # --- Message Input ---
    chat_input = st.text_input("Type your message...", key="chat_input", label_visibility="collapsed", placeholder="Type your message...")
    col_send, col_regen = st.columns([0.7, 0.3])
    with col_send:
        send_clicked = st.button("Send", key="send_btn")
    with col_regen:
        regen_clicked = st.button("Regenerate", key="regen_btn")

    # --- Handle Send ---
    if send_clicked and chat_input.strip():
        st.session_state.conversation_history.append({"role": "user", "content": chat_input.strip()})
        # Placeholder for AI response
        st.session_state.conversation_history.append({"role": "ai", "content": "[AI response goes here]"})
        st.experimental_rerun()

    # --- Handle Regenerate ---
    if regen_clicked and st.session_state.conversation_history:
        # Remove last AI response and regenerate
        if st.session_state.conversation_history[-1]["role"] == "ai":
            st.session_state.conversation_history.pop()
        st.session_state.conversation_history.append({"role": "ai", "content": "[Regenerated AI response]"})
        st.experimental_rerun()

with col3:
    st.markdown('<div class="info-panel">', unsafe_allow_html=True)
    st.markdown("<h4 style='color:#2ecc71;'>Information Panel</h4>", unsafe_allow_html=True)
    # --- Entity Details Table ---
    st.markdown("<b>Entity</b> | <b>Description</b>")
    st.markdown("<div class='entity-table'><span class='entity-highlight'>HybRAGMC</span> &mdash; Hybrid RAG with Multi-Component architecture for advanced document QA.</div>", unsafe_allow_html=True)
    st.markdown("<div class='entity-table'><span class='entity-highlight'>VectorRAG</span> &mdash; Uses vector search for semantic retrieval.</div>", unsafe_allow_html=True)
    st.markdown("<div class='entity-table'><span class='entity-highlight'>GraphRAG</span> &mdash; Uses knowledge graphs for entity-based retrieval.</div>", unsafe_allow_html=True)
    # --- Highlighted Extracted Information ---
    st.markdown("<br><b>Extracted Information</b>")
    st.markdown("""
    <div style='background:#2d3548; color:#e6e6e6; border-radius:8px; padding:12px; margin-top:8px; font-size:0.95em;'>
    <span class='entity-highlight'>HybRAGMC</span> is an advanced approach that combines the strengths of vector-based and graph-based retrieval, enabling more accurate, diverse, and comprehensive answers for complex document QA tasks.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

class VectorStore:
    """Handles vector collection operations."""
    
    @staticmethod
    def get_vector_collection() -> Optional[chromadb.Collection]:
        """Initialize and return a Chroma vector collection."""
        try:
            ollama_ef = OllamaEmbeddingFunction(
                url=f"{OLLAMA_BASE_URL}/api/embeddings",
                model_name=OLLAMA_EMBEDDING_MODEL,
            )
            chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            return chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                embedding_function=ollama_ef,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            logger.error(f"Error initializing vector collection: {str(e)}")
            st.error(f"Failed to initialize vector collection: {str(e)}")
            return None

    @staticmethod
    def add_to_vector_collection(all_splits: List[Document], file_name: str) -> bool:
        """Add documents to the vector collection."""
        try:
            collection = VectorStore.get_vector_collection()
            if not collection:
                return False
            documents, metadatas, ids = [], [], []
            for idx, split in enumerate(all_splits):
                documents.append(split.page_content)
                metadatas.append(split.metadata)
                ids.append(f"{file_name}_{idx}")
            
            collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f"Added {len(documents)} documents to collection for {file_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding to vector collection: {str(e)}")
            st.error(f"Error adding to vector collection: {str(e)}")
            return False

    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def query_collection(prompt: str, n_results: int) -> Dict:
        """Query the vector collection with caching."""
        collection = VectorStore.get_vector_collection()
        if not collection:
            return {}
        return collection.query(query_texts=[prompt], n_results=n_results)

class DocumentProcessor:
    """Handles document loading and splitting."""
    
    @staticmethod
    def process_document(uploaded_file: UploadedFile) -> List[Document]:
        """Process an uploaded file and return split documents."""
        try:
            if uploaded_file.size > MAX_FILE_SIZE:
                st.error(f"File size exceeds limit of {MAX_FILE_SIZE / (1024 * 1024)} MB")
                logger.warning(f"File {uploaded_file.name} exceeds size limit")
                return []
            
            suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".docx"
            temp_file = tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False)
            temp_file.write(uploaded_file.read())
            temp_file.close()

            if suffix == ".pdf":
                loader = PyMuPDFLoader(temp_file.name)
            else:
                loader = UnstructuredWordDocumentLoader(temp_file.name)

            docs = loader.load()
            os.unlink(temp_file.name)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=st.session_state.get("chunk_size", DEFAULT_CHUNK_SIZE),
                chunk_overlap=st.session_state.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP),
                separators=["\n\n", "\n", ".", "!", "?", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            logger.info(f"Processed {len(splits)} chunks from {uploaded_file.name}")
            return splits
        except Exception as e:
            logger.error(f"Error processing document {uploaded_file.name}: {str(e)}")
            st.error(f"Error processing document: {str(e)}")
            return []

class LLMHandler:
    """Handles LLM interactions with retry logic."""
    
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_llm(prompt: str, context: str) -> str:
        """Call the LLM with the given prompt and context."""
        try:
            history_str = "\n".join(
                [f"Q: {entry['prompt']}\nA: {entry['response']}" 
                 for entry in st.session_state.conversation_history]
            )
            
            response_chunks = ollama.chat(
                model=OLLAMA_LLM_MODEL,
                stream=True,
                options={"base_url": OLLAMA_BASE_URL},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Context: {context}\nConversation History: {history_str}\nQuestion: {prompt}"
                    }
                ],
            )
            
            response = ""
            for chunk in response_chunks:
                if chunk["done"] is False:
                    response += chunk["message"]["content"]
                    yield chunk["message"]["content"]
                else:
                    break
            
            st.session_state.conversation_history.append({"prompt": prompt, "response": response})
            if len(st.session_state.conversation_history) > 3:
                st.session_state.conversation_history.pop(0)
                
            logger.info(f"LLM response generated for prompt: {prompt[:50]}...")
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            st.error(f"Error communicating with LLM: {str(e)}")
            return ""

def sanitize_input(text: str) -> str:
    """Sanitize input to prevent injection attacks."""
    return text.replace("<", "&lt;").replace(">", "&gt;").strip()

def get_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

def get_cache_path(file_hash):
    os.makedirs(EMBEDDINGS_CACHE_PATH, exist_ok=True)
    return f"{EMBEDDINGS_CACHE_PATH}/{file_hash}.pkl"

def save_embeddings_to_cache(file_hash, embeddings):
    with open(get_cache_path(file_hash), "wb") as f:
        pickle.dump(embeddings, f)

def load_embeddings_from_cache(file_hash):
    with open(get_cache_path(file_hash), "rb") as f:
        return pickle.load(f)

def process_documents(uploaded_files: list[UploadedFile]) -> list[Document]:
    """Process multiple uploaded files and return a list of Document chunks, with caching."""
    all_docs = []
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        file_hash = get_file_hash(file_bytes)
        cache_path = get_cache_path(file_hash)
        overwrite_cache = False

        if os.path.exists(cache_path):
            st.toast(f"Embeddings for {uploaded_file.name} already exist.")
            if st.button(f"Overwrite embeddings for {uploaded_file.name}?"):
                overwrite_cache = True
            else:
                st.info(f"Using cached embeddings for {uploaded_file.name}.")
                all_docs.extend(load_embeddings_from_cache(file_hash))
                continue

        # Store uploaded file as temp file
        suffix = os.path.splitext(uploaded_file.name)[-1]
        temp_file = tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False)
        temp_file.write(file_bytes)
        temp_file.close()

        # Load the file (only PDF supported here)
        try:
            loader = PyMuPDFLoader(temp_file.name)
            docs = loader.load()
        except Exception as e:
            st.error(f"Error loading {uploaded_file.name}: {e}")
            docs = []
        finally:
            os.unlink(temp_file.name)

        # Create chunks of documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,  # characters
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,  # semantic overlap
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        embeddings = text_splitter.split_documents(docs)
        save_embeddings_to_cache(file_hash, embeddings)
        all_docs.extend(embeddings)
    return all_docs

def main():
    st.set_page_config(page_title="PITB RAG Application v0.3", layout="wide")
    
    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "chunk_size" not in st.session_state:
        st.session_state.chunk_size = DEFAULT_CHUNK_SIZE
    if "chunk_overlap" not in st.session_state:
        st.session_state.chunk_overlap = DEFAULT_CHUNK_OVERLAP
    if "n_results" not in st.session_state:
        st.session_state.n_results = DEFAULT_N_RESULTS
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    # Header
    st.markdown(f"""
    <div class="header{' dark-mode' if st.session_state.dark_mode else ''}">
        <h1>PITB RAG Application v0.3</h1>
        <p>Powered by Punjab Information Technology Board</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150?text=PITB+Logo", caption="PITB Logo")
        
        # Configuration panel
        with st.expander("Settings", expanded=False):
            st.session_state.chunk_size = st.number_input(
                "Chunk Size", min_value=100, max_value=1000, value=st.session_state.chunk_size, step=50,
                help=f"Number of characters per document chunk (default: {DEFAULT_CHUNK_SIZE})"
            )
            st.session_state.chunk_overlap = st.number_input(
                "Chunk Overlap", min_value=0, max_value=200, value=st.session_state.chunk_overlap, step=10,
                help=f"Overlap between document chunks (default: {DEFAULT_CHUNK_OVERLAP})"
            )
            st.session_state.n_results = st.number_input(
                "Number of Results", min_value=1, max_value=20, value=st.session_state.n_results, step=1,
                help=f"Number of documents to retrieve (default: {DEFAULT_N_RESULTS})"
            )
            if st.checkbox("Dark Mode"):
                st.session_state.dark_mode = True
            else:
                st.session_state.dark_mode = False

        uploaded_files = st.file_uploader(
            "Upload PDF or DOCX Documents",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Upload one or more PDF or DOCX files for question answering."
        )

        if uploaded_files:
            st.subheader("Uploaded Files")
            for uploaded_file in uploaded_files:
                file_details = {
                    "Filename": uploaded_file.name,
                    "File Type": uploaded_file.type,
                    "File Size": f"{uploaded_file.size / 1024:.2f} KB"
                }
                st.json(file_details)

        process = st.button("Process Documents", key="process_btn")
        if st.button("Clear Conversation History", key="clear_history"):
            st.session_state.conversation_history = []
            st.success("Conversation history cleared!")

    # Process uploaded files
    if uploaded_files and process:
        total_files = len(uploaded_files)
        progress_bar = st.progress(0)
        for idx, uploaded_file in enumerate(uploaded_files):
            with st.spinner(f"Processing {uploaded_file.name}..."):
                all_splits = DocumentProcessor.process_document(uploaded_file)
                if all_splits:
                    chunks_json = {
                        "total_chunks": len(all_splits),
                        "chunks": [
                            {"content": chunk.page_content, "metadata": chunk.metadata}
                            for chunk in all_splits
                        ]
                    }
                    with st.expander(f"View Chunks for {uploaded_file.name}"):
                        st.json(chunks_json)
                    
                    normalized_file_name = uploaded_file.name.translate(
                        str.maketrans({"-": "_", ",": "_", " ": "_"})
                    )
                    VectorStore.add_to_vector_collection(all_splits, normalized_file_name)
            progress_bar.progress((idx + 1) / total_files)
        st.success("All documents processed!")

    # Question input
    st.subheader("Ask a Question")
    prompt = st.text_area(
        "Enter your question (related to the uploaded documents):",
        height=100,
        placeholder="Type your question here...",
        help="Ask a question based on the uploaded documents."
    )
    ask = st.button("Submit Question", key="ask_btn")
    
    collection = VectorStore.get_vector_collection()
    if collection:
        st.write(f"**Collection Status**: {len(collection.peek()['ids'])} documents indexed")

    # Handle question submission
    if ask and prompt:
        sanitized_prompt = sanitize_input(prompt)
        if len(sanitized_prompt) < 5:
            st.error("Please enter a valid question (minimum 5 characters).")
            logger.warning("Invalid prompt length")
        else:
            with st.spinner("Generating response..."):
                results = VectorStore.query_collection(sanitized_prompt, st.session_state.n_results)
                context = results.get("documents", [[]])[0] if results.get("documents") else []
                if not context:
                    st.error("No relevant documents found for the query.")
                    logger.warning(f"No relevant documents for prompt: {sanitized_prompt[:50]}...")
                else:
                    context_str = " ".join(context)
                    response = LLMHandler.call_llm(sanitized_prompt, context_str)
                    st.subheader("Response")
                    st.write_stream(response)

                    with st.expander("Retrieved Documents"):
                        st.json(results)

                    with st.expander("Conversation History"):
                        st.json(st.session_state.conversation_history)

    # Footer
    st.markdown(f"""
    <div class="footer{' dark-mode' if st.session_state.dark_mode else ''}">
        <p>© 2025 Punjab Information Technology Board. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()