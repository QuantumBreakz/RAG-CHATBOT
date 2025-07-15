# rag_core/ui.py
"""
Streamlit UI for PITB RAG MVP with sidebar, chat bubbles, header, and footer.
"""
import streamlit as st
from rag_core.utils import sanitize_input
from rag_core import history
from rag_core import cache
from datetime import datetime
import base64
import logging
import requests
import json

# ================= UI/UX Improvements Roadmap =================
#
# Visual Conversation Threading:
#   - Visually group follow-up questions and answers.
#   - Highlight when a user references a previous answer.
#
# Message Editing/Resending:
#   - Allow users to edit and resend previous questions.
#   - Clearly show which AI answer corresponds to which user message.
#
# Context Preview:
#   - Show a summary/preview of the context/chunks used for each answer.
#   - Let users see what the bot is referencing.
#
# History Navigation:
#   - Enable scrolling, searching, or filtering previous messages.
#   - Allow jumping to relevant points in the conversation.
#
# Feedback on Context Use:
#   - After each answer, show a note: "This answer used X previous messages for context."
#
# File-by-File Recommendations:
#   - rag_core/llm.py: Structured message list, history windowing, context window management.
#   - rag_core/ui.py: Threading, context preview, message-level actions, history window size setting.
#   - rag_core/document.py: Chunk linking, section headers.
#   - rag_core/history.py: Message threads, summarization.
#   - rag_core/vectorstore.py: Contextual retrieval, smarter chunk expansion.
#   - rag_core/utils.py: Text summarization, context formatting.
#
# General Codebase Improvements:
#   - Type annotations, modular prompt construction, unit tests, granular error handling.
# ==============================================================

# Helper to sync session state with persistent conversation

def load_conversation_to_session(conv):
    st.session_state['conversation_id'] = conv['id']
    # Try to load context from context database
    context = history.load_chat_context(conv['id'])
    if context is not None:
        st.session_state['conversation_history'] = context
    else:
        st.session_state['conversation_history'] = conv['messages']
    st.session_state['uploads'] = conv.get('uploads', [])
    st.session_state['conversation_title'] = conv.get('title', '')
    st.session_state['chat_input_value'] = ''

def save_session_to_disk():
    conv = {
        'id': st.session_state['conversation_id'],
        'title': st.session_state.get('conversation_title', ''),
        'created_at': st.session_state.get('conversation_created_at', datetime.now().isoformat(timespec='seconds')),
        'messages': st.session_state.get('conversation_history', []),
        'uploads': st.session_state.get('uploads', [])
    }
    history.save_conversation(conv)

def get_image_base64(image_path):
    """Convert image to base64 for embedding in HTML"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

def main():
    # --- Sidebar: Knowledge Base Documents ---
    def fetch_documents():
        try:
            response = requests.get('http://localhost:8000/documents')
            if response.ok:
                return response.json().get('documents', [])
            else:
                st.error("Failed to fetch documents: " + response.text)
                return []
        except Exception as e:
            st.error(f"Error fetching documents: {str(e)}")
            return []
    
    # Ensure required session state keys are initialized
    if 'conversation_id' not in st.session_state:
        conversations = history.list_conversations()
        if conversations:
            loaded = history.load_conversation(conversations[0]['id'])
            if loaded:
                load_conversation_to_session(loaded)
        else:
            new_conv = history.new_conversation()
            load_conversation_to_session(new_conv)
            history.save_conversation(new_conv)
    
    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    # Set page config with theme
    st.set_page_config(
        page_title="PITB RAG MVP", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply theme using Streamlit's built-in theme
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
        }
        .stSidebar {
            background-color: #2d2d2d !important;
        }
        /* Text input and text area */
        input[type="text"], input[type="search"], textarea, .stTextInput input, .stTextArea textarea {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
            border: 1px solid #444 !important;
        }
        /* Placeholder text */
        input[type="text"]::placeholder, textarea::placeholder {
            color: #bbbbbb !important;
            opacity: 1 !important;
        }
        /* Number input */
        input[type="number"], .stNumberInput input {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
            border: 1px solid #444 !important;
        }
        /* Selectbox and dropdowns */
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
        }
        .stSelectbox div[data-baseweb="select"] span {
            color: #ffffff !important;
        }
        /* File uploader */
        .stFileUploader, .stFileUploader > div {
            background-color: #2d2d2d !important;
            color: #ffffff !important;
        }
        /* Buttons */
        .stButton > button {
            background-color: #444 !important;
            color: #ffffff !important;
            border: 1px solid #666 !important;
        }
        .stButton > button:active, .stButton > button:focus {
            background-color: #666 !important;
            color: #fff !important;
        }
        /* Expander */
        .stExpander > div {
            background-color: #232323 !important;
            color: #ffffff !important;
        }
        /* Info, success, warning, error boxes */
        .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
            background-color: #232323 !important;
            color: #ffffff !important;
        }
        /* Markdown, text, captions */
        .stMarkdown, .stText, .stCaption {
            color: #ffffff !important;
        }
        /* General text */
        p, h1, h2, h3, h4, h5, h6, span, div {
            color: #ffffff !important;
        }
        /* Table headers and cells */
        th, td {
            background-color: #232323 !important;
            color: #ffffff !important;
        }
        /* Scrollbar */
        ::-webkit-scrollbar {
            background: #232323 !important;
        }
        ::-webkit-scrollbar-thumb {
            background: #444 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # --- Header with ROX Chatbot Name (no logo) ---
    header_html = """
    <div style='width:100%; background:#003366; padding:16px 0 8px 0; text-align:center; margin-bottom:20px;'>
        <span style='color:white; font-size:2rem; font-weight:bold; vertical-align:middle;'>XOR CHATBOT</span>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # Detect developer mode from URL path or query param
    dev_mode = False
    query_params = st.query_params
    if 'dev' in query_params and query_params['dev'][0] == '1':
        dev_mode = True
    # For path-based (e.g., /developers), Streamlit doesn't natively support path routing, so use query param

    # --- Sidebar: Conversation List ---
    with st.sidebar:
        # Theme Toggle
        st.markdown("### 🌓 Theme")
        theme_col1, theme_col2 = st.columns(2)
        with theme_col1:
            if st.button("☀️ Light", key="light_theme", use_container_width=True):
                st.session_state.theme = 'light'
                st.rerun()
        with theme_col2:
            if st.button("🌙 Dark", key="dark_theme", use_container_width=True):
                st.session_state.theme = 'dark'
                st.rerun()
        
        st.markdown("---")
        st.markdown("# 💬 Conversations")
        
        # New Chat Button
        if st.button("➕ New Chat", key="new_chat_btn", use_container_width=True):
            new_conv = history.new_conversation()
            load_conversation_to_session(new_conv)
            history.save_conversation(new_conv)
            st.rerun()
        
        st.markdown("---")
        
        # Conversation List with Management
        conversations = history.list_conversations()
        selected_id = st.session_state.get('conversation_id')
        
        if not conversations:
            st.info("No conversations yet. Start a new chat!")
        else:
            for conv in conversations:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Highlight current conversation
                        if conv['id'] == selected_id:
                            st.markdown(f"**{conv['title']}** ({conv['created_at'][:10]})")
                        else:
                            if st.button(f"{conv['title']} ({conv['created_at'][:10]})", key=f"conv_{conv['id']}", use_container_width=True):
                                loaded = history.load_conversation(conv['id'])
                                if loaded:
                                    load_conversation_to_session(loaded)
                                    st.rerun()
                    
                    with col2:
                        # Dropdown for conversation management
                        with st.popover("⚙️", help="Manage conversation"):
                            if st.button("✏️ Rename", key=f"rename_{conv['id']}"):
                                st.session_state[f"renaming_{conv['id']}"] = True
                                st.rerun()
                            
                            # Allow deleting any chat, including the current one
                            if st.button("🗑️ Delete", key=f"delete_{conv['id']}" ):
                                history.delete_conversation(conv['id'])
                                history.delete_chat_context(conv['id'])
                                st.success(f"Deleted conversation: {conv['title']}")
                                # If current chat is deleted, clear session and prompt for new chat
                                if st.session_state.get('conversation_id') == conv['id']:
                                    for k in ['conversation_id', 'conversation_history', 'uploads', 'conversation_title', 'chat_input_value']:
                                        if k in st.session_state:
                                            del st.session_state[k]
                                    st.session_state['is_processing'] = False
                                    st.rerun()
                                else:
                                    st.session_state['is_processing'] = False
                                    st.rerun()
                            
                            if st.button("🧹 Clear Context", key=f"clear_context_{conv['id']}"):
                                history.delete_chat_context(conv['id'])
                                st.success(f"Cleared context for: {conv['title']}")
                                st.rerun()
        
        st.markdown("---")
        # Add button to clear/reset knowledge base
        if st.button("🧹 Reset Knowledge Base (Clear All Embeddings)", key="reset_kb_btn", use_container_width=True):
            try:
                response = requests.post('http://localhost:8000/reset_kb')
                if response.ok:
                    st.session_state['uploads'] = []
                    save_session_to_disk()
                    st.success("Knowledge base has been reset. All embeddings cleared.")
                else:
                    st.error("Failed to reset knowledge base: " + response.text)
            except Exception as e:
                st.error(f"Error resetting knowledge base: {str(e)}")
            st.rerun()
        
        # Current Chat Management
        if selected_id:
            st.markdown("### 📋 Current Chat")
            current_title = st.session_state.get('conversation_title', '')
            
            # Rename functionality
            if st.session_state.get(f"renaming_{selected_id}", False):
                new_title = st.text_input("New title:", value=current_title, key=f"new_title_{selected_id}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Save", key=f"save_title_{selected_id}"):
                        st.session_state['conversation_title'] = new_title
                        save_session_to_disk()
                        st.session_state[f"renaming_{selected_id}"] = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_title_{selected_id}"):
                        st.session_state[f"renaming_{selected_id}"] = False
                        st.rerun()
            else:
                st.markdown(f"**Title:** {current_title}")
                if st.button("✏️ Rename", key=f"rename_current"):
                    st.session_state[f"renaming_{selected_id}"] = True
                    st.rerun()
            
            # Upload preview
            uploads = st.session_state.get('uploads', [])
            if uploads:
                st.markdown("**📄 Uploaded Files:**")
                for upload in uploads:
                    with st.expander(f"📎 {upload['filename']}", expanded=False):
                        st.markdown(f"**Size:** {upload['metadata']['size']} bytes")
                        st.markdown(f"**Type:** {upload['metadata']['type']}")
                        st.markdown(f"**Uploaded:** {upload['metadata']['uploaded_at'][:19]}")
                        if st.button("🗑️ Remove", key=f"remove_upload_{upload['filename']}_{upload['file_hash']}"):
                            st.session_state['uploads'].remove(upload)
                            save_session_to_disk()
                            st.rerun()
            else:
                st.info("No files uploaded yet.")
            
            # Download Chat History Button
            export_url = f"http://localhost:8000/history/export/{selected_id}"
            st.markdown(f"[⬇️ Download Chat History]({export_url})", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # File Upload Section
        st.markdown("## 📄 Upload Documents")

        # Helper function to upload file to backend

        def upload_file_to_backend(uploaded_file):
            files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post('http://localhost:8000/upload', files=files)
            if response.ok:
                return response.json()
            else:
                st.error("Upload failed: " + response.text)
                return None

        # Helper function to query backend
        def query_backend(question, n_results=3, expand=2, filename=None, conversation_history=None):
            """Query the backend API for RAG responses."""
            try:
                data = {
                    'question': question,
                    'n_results': n_results,
                    'expand': expand,
                    'conversation_history': json.dumps(conversation_history or [])
                }
                if filename:
                    data['filename'] = filename
                
                response = requests.post('http://localhost:8000/query', data=data)
                if response.ok:
                    return response.json()
                else:
                    st.error(f"Query failed: {response.text}")
                    return None
            except Exception as e:
                st.error(f"Error calling backend: {str(e)}")
                return None

        uploaded_files = st.file_uploader(
            "Upload PDF, DOCX, CSV, or Excel files",
            type=["pdf", "docx", "csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key="file_uploader"
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                with st.spinner(f"Uploading and processing {uploaded_file.name}..."):
                    upload_result = upload_file_to_backend(uploaded_file)
                if upload_result:
                    if hasattr(st, 'toast'):
                        st.toast(f"{uploaded_file.name} processed! Chunks created: {upload_result['num_chunks']}", icon="✅")
                    else:
                        st.success(f"{uploaded_file.name} processed! Chunks created: {upload_result['num_chunks']}")
                    # Refresh document list after upload
                    st.session_state['documents_list'] = fetch_documents()
                else:
                    if hasattr(st, 'toast'):
                        st.toast(f"Upload failed for {uploaded_file.name}", icon="❌")
                    else:
                        st.error(f"Upload failed for {uploaded_file.name}")
        
        # Settings Section
        with st.expander("⚙️ Settings", expanded=False):
            st.markdown("_Configure chunk size, overlap, and results if needed._")
            chunk_size = st.number_input(
                "Chunk Size", min_value=100, max_value=1000, value=st.session_state.get("chunk_size", 400), step=50
            )
            chunk_overlap = st.number_input(
                "Chunk Overlap", min_value=0, max_value=200, value=st.session_state.get("chunk_overlap", 100), step=10
            )
            n_results = st.number_input(
                "Number of Results", min_value=1, max_value=20, value=st.session_state.get("n_results", 3), step=1
            )
            st.session_state["chunk_size"] = chunk_size
            st.session_state["chunk_overlap"] = chunk_overlap
            st.session_state["n_results"] = n_results
            # --- Developer/User View Switch ---
            st.markdown("---")
            if dev_mode:
                st.success("Developer mode is ON. Timestamps and context will be shown.")
                if st.button("Switch to User View", key="switch_user_view"):
                    st.query_params.clear()  # Remove dev param
                    st.rerun()
            else:
                st.info("User mode is ON. Timestamps and context are hidden.")
                if st.button("Switch to Developer View", key="switch_dev_view"):
                    st.query_params["dev"] = "1"
                    st.rerun()

    # --- Main Chat Area ---
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Responsive CSS for mobile/tablet
    st.markdown("""
    <style>
    @media (max-width: 900px) {
        .stApp { font-size: 15px !important; }
        .stSidebar { width: 100vw !important; }
        .stButton > button, .stTextInput input, .stTextArea textarea {
            font-size: 1rem !important;
        }
    }
    @media (max-width: 600px) {
        .stApp { font-size: 14px !important; }
        .stSidebar { width: 100vw !important; }
        .stButton > button, .stTextInput input, .stTextArea textarea {
            font-size: 0.95rem !important;
        }
    }
    /* Visually distinct buttons */
    .stButton > button {
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(44,62,80,0.10) !important;
        transition: box-shadow 0.2s, background 0.2s;
        font-weight: 600;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 16px rgba(44,62,80,0.18) !important;
        background: #e3f2fd !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Floating Chat Input Area ---
    st.markdown("""
    <style>
    .floating-chat-input {
        position: sticky;
        bottom: 0;
        left: 0;
        width: 100%;
        background: #fff;
        box-shadow: 0 0 16px rgba(44,62,80,0.10);
        border-radius: 18px 18px 0 0;
        padding: 18px 24px 12px 24px;
        z-index: 100;
        margin-top: 24px;
    }
    .send-btn {
        background: linear-gradient(135deg, #1976D2 0%, #64B5F6 100%);
        color: #fff;
        border: none;
        border-radius: 50%;
        width: 48px;
        height: 48px;
        font-size: 1.5rem;
        box-shadow: 0 2px 8px rgba(25,118,210,0.10);
        cursor: pointer;
        margin-left: 12px;
        transition: box-shadow 0.2s, background 0.2s;
    }
    .send-btn:hover {
        box-shadow: 0 4px 16px rgba(25,118,210,0.18);
        background: #1565c0;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Scroll to Latest Button ---
    if len(st.session_state.get("conversation_history", [])) > 8:
        if st.button("⬇️ Scroll to Latest", key="scroll_latest_btn", use_container_width=True):
            st.experimental_rerun()

    # Chat header with current conversation info
    if st.session_state.get('conversation_title'):
        st.markdown(f"### 💬 {st.session_state.get('conversation_title')}")

        # Chat container with better styling
        chat_container = st.container()
        with chat_container:
            chat_placeholder = st.empty()
            with chat_placeholder.container():
                # Improved chat bubbles with better styling
                for i, msg in enumerate(st.session_state.get("conversation_history", [])):
                    is_user = msg["role"] == "user"
                    edit_key = f"edit_msg_{i}"
                    editing = st.session_state.get(edit_key, False)
                    is_followup = msg.get("followup_to") is not None
                    followup_badge = "<span style='color:#1976D2; font-size:13px; margin-left:8px;'>↩️ Follow-up</span>" if is_followup else ""
                    highlight = st.session_state.get("highlight_msg", -1) == i
                    highlight_box = "box-shadow: 0 0 0 3px #ffe082;" if highlight else ""
                    avatar_svg_user = '''<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="16" fill="#DCF8C6"/><text x="16" y="21" text-anchor="middle" font-size="16" fill="#2E7D32" font-family="Arial" font-weight="bold">U</text></svg>'''
                    avatar_svg_ai = '''<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="16" fill="#E0E0E0"/><text x="16" y="21" text-anchor="middle" font-size="16" fill="#1976D2" font-family="Arial" font-weight="bold">A</text></svg>'''
                    if is_user and editing:
                        new_text = st.text_area("Edit your message:", value=msg["content"], key=f"edit_input_{i}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 Save", key=f"save_edit_{i}"):
                                # Replace message and truncate history after this point
                                st.session_state["conversation_history"] = st.session_state["conversation_history"][:i] + [{
                                    "role": "user",
                                    "content": new_text,
                                    "timestamp": datetime.now().isoformat(timespec='seconds')
                                }]
                                save_session_to_disk()
                                history.save_chat_context(st.session_state['conversation_id'], st.session_state['conversation_history'])
                                st.session_state[edit_key] = False
                                st.session_state['chat_input_value'] = ''
                                st.session_state['is_processing'] = False
                                st.rerun()
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_edit_{i}"):
                                st.session_state[edit_key] = False
                                st.session_state['is_processing'] = False
                                st.rerun()
                    else:
                        if is_user:
                            st.markdown(
                                f"""
                                <div style='display: flex; justify-content: flex-end; margin-bottom: 24px; padding: 0 10px; {highlight_box}'>
                                    <div style='display: flex; flex-direction: row-reverse; align-items: flex-end;'>
                                        <div style='margin-left: 12px;'>{avatar_svg_user}</div>
                                        <div style="background: linear-gradient(135deg, #DCF8C6 0%, #C8E6C9 100%); color: #2E7D32; border-radius: 18px 18px 4px 18px; padding: 18px 22px; max-width: 70%; box-shadow: 0 4px 16px rgba(44, 62, 80, 0.10); border: 1px solid #A5D6A7; font-size: 1.08rem; line-height: 1.6; margin-bottom: 2px;">
                                            <div style="font-weight: 600; margin-bottom: 4px;">You {followup_badge}</div>
                                            <div>{msg['content']}</div>
                                            {f'<div style=\'font-size: 11px; color: #666; margin-top: 8px; text-align: right;\'>{msg.get('timestamp', '')[:19]}</div>' if dev_mode else ''}
                                        </div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            if st.button("✏️", key=f"edit_btn_{i}"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        else:
                            st.markdown(
                                f"""
                                <div style='display: flex; justify-content: flex-start; margin-bottom: 24px; padding: 0 10px; {highlight_box}'>
                                    <div style='display: flex; flex-direction: row; align-items: flex-end;'>
                                        <div style='margin-right: 12px;'>{avatar_svg_ai}</div>
                                        <div style="background: linear-gradient(135deg, #F5F5F5 0%, #E0E0E0 100%); color: #1976D2; border-radius: 18px 18px 18px 4px; padding: 18px 22px; max-width: 70%; box-shadow: 0 4px 16px rgba(44, 62, 80, 0.10); border: 1px solid #D0D0D0; font-size: 1.08rem; line-height: 1.6; margin-bottom: 2px;">
                                            <div style="font-weight: 600; margin-bottom: 4px; color: #1976D2;">AI Assistant {followup_badge}</div>
                                            <div>{msg['content']}</div>
                                            {f'<div style=\'font-size: 11px; color: #666; margin-top: 8px; text-align: right;\'>{msg.get('timestamp', '')[:19]}</div>' if dev_mode else ''}
                                        </div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    # Only show context preview in dev mode
                    if not is_user and msg.get("context_preview") and dev_mode:
                        with st.expander("Context Used", expanded=False):
                            st.markdown(f"<div style='font-size:13px; color:#333; background:#f9f9f9; border-radius:8px; padding:8px 12px; margin-bottom:4px;'>{msg['context_preview']}</div>", unsafe_allow_html=True)
        # End of chat rendering loop

        # --- Floating Chat Input Area Implementation ---
        st.markdown('<div class="floating-chat-input">', unsafe_allow_html=True)
        # Disable chat input while processing
        is_processing = st.session_state.get('is_processing', False)
        chat_input_key = f"chat_input_{st.session_state.get('conversation_id', '')}_{len(st.session_state.get('conversation_history', []))}"
        with st.form(key="chat_input_form", clear_on_submit=False):
            chat_input = st.text_input(
                "💬 Type your question and press Enter", 
                key=chat_input_key, 
                value=st.session_state.get('chat_input_value', ''),
                placeholder="Ask about your uploaded documents...",
                disabled=is_processing
            )
            send_col1, send_col2 = st.columns([8,1])
            with send_col1:
                submitted = st.form_submit_button("Send", use_container_width=True)
            with send_col2:
                send_icon = st.form_submit_button("➡️", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # If no chat is loaded, prompt user to start/select a chat
    if 'conversation_id' not in st.session_state or not st.session_state.get('conversation_id'):
        st.info("No active chat. Please start a new chat or select one from the sidebar.")
    elif submitted and chat_input and not is_processing:
        st.session_state['is_processing'] = True
        sanitized_prompt = sanitize_input(chat_input.strip())
        if "conversation_history" not in st.session_state:
            st.session_state["conversation_history"] = []
        # Guard: Prevent duplicate user messages
        if len(st.session_state["conversation_history"]) > 0 and st.session_state["conversation_history"][-1]["role"] == "user" and st.session_state["conversation_history"][-1]["content"] == sanitized_prompt:
            st.session_state['is_processing'] = False
            st.session_state['chat_input_value'] = ''
            st.experimental_set_query_params(**{})  # Clear widget value
            st.warning("Duplicate message ignored.")
        else:
            # Add user message
            st.session_state["conversation_history"].append({
                "role": "user", 
                "content": sanitized_prompt, 
                "timestamp": datetime.now().isoformat(timespec='seconds')
            })
            st.session_state['chat_input_value'] = ''
            # Save to disk immediately
            save_session_to_disk()
            # Save context after user message
            history.save_chat_context(st.session_state['conversation_id'], st.session_state['conversation_history'])
            # Always save conversation history for all chats
            history.save_conversation({
                'id': st.session_state['conversation_id'],
                'title': st.session_state.get('conversation_title', ''),
                'created_at': st.session_state.get('conversation_created_at', datetime.now().isoformat(timespec='seconds')),
                'messages': st.session_state.get('conversation_history', []),
                'uploads': st.session_state.get('uploads', [])
            })
            with st.spinner("🤔 Thinking..."):
                # Allow retrieval from all uploaded documents if more than one is present
                uploads = st.session_state.get('uploads', [])
                if len(uploads) == 1:
                    selected_filename = uploads[0]['filename']
                else:
                    selected_filename = None  # Search all documents
                
                # Get conversation history for context
                conversation_history = st.session_state.get("conversation_history", [])
                
                # Query backend API
                query_result = query_backend(
                    question=sanitized_prompt,
                    n_results=st.session_state.get("n_results", 3),
                    expand=2,
                    filename=selected_filename,
                    conversation_history=conversation_history
                )
                
                if query_result is None:
                    # API call failed
                    st.session_state["conversation_history"].append({
                        "role": "ai", 
                        "content": "[Error: Could not connect to the backend service. Please try again.]", 
                        "timestamp": datetime.now().isoformat(timespec='seconds')
                    })
                    save_session_to_disk()
                    history.save_chat_context(st.session_state['conversation_id'], st.session_state['conversation_history'])
                    st.session_state['is_processing'] = False
                    st.session_state['chat_input_value'] = ''
                    st.experimental_set_query_params(**{})
                    st.rerun()
                elif query_result.get('status') == 'no_context':
                    # No relevant context found
                    st.session_state["conversation_history"].append({
                        "role": "ai", 
                        "content": query_result['answer'], 
                        "timestamp": datetime.now().isoformat(timespec='seconds')
                    })
                    save_session_to_disk()
                    history.save_chat_context(st.session_state['conversation_id'], st.session_state['conversation_history'])
                    st.session_state['is_processing'] = False
                    st.session_state['chat_input_value'] = ''
                    st.experimental_set_query_params(**{})
                    st.rerun()
                else:
                    # Success - display the response
                    answer = query_result.get('answer', '')
                    context_str = query_result.get('context', '')
                    
                    # Display the response (for now, non-streaming)
                    st.session_state["conversation_history"].append({
                        "role": "ai", 
                        "content": answer, 
                        "timestamp": datetime.now().isoformat(timespec='seconds'),
                        "context_preview": context_str
                    })
                    # Save to disk immediately
                    save_session_to_disk()
                    # Save context after AI message
                    history.save_chat_context(st.session_state['conversation_id'], st.session_state['conversation_history'])
                    # Always save conversation history for all chats
                    history.save_conversation({
                        'id': st.session_state['conversation_id'],
                        'title': st.session_state.get('conversation_title', ''),
                        'created_at': st.session_state.get('conversation_created_at', datetime.now().isoformat(timespec='seconds')),
                        'messages': st.session_state.get('conversation_history', []),
                        'uploads': st.session_state.get('uploads', [])
                    })
                    st.session_state['is_processing'] = False
                    st.session_state['chat_input_value'] = ''
                    st.experimental_set_query_params(**{})
                st.rerun()

    # --- Footer ---
    st.markdown(
        """
        <div style='width:100%; background:#003366; color:white; text-align:center; padding:8px 0; position:fixed; bottom:0; left:0;'>
            © 2025 XOR Chatbot. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Sidebar: Knowledge Base Documents ---
    st.markdown("---")
    st.markdown("### 📚 Knowledge Base Documents")
    if 'documents_list' not in st.session_state:
        st.session_state['documents_list'] = fetch_documents()
    if st.button("🔄 Refresh Documents", key="refresh_docs_btn", use_container_width=True):
        st.session_state['documents_list'] = fetch_documents()
        st.rerun()
    docs = st.session_state['documents_list']
    if not docs:
        st.info("No documents indexed yet.")
    else:
        for doc in docs:
            with st.container():
                col1, col2 = st.columns([4,1])
                with col1:
                    st.markdown(f"**{doc['filename']}**  ")
                    st.caption(f"Chunks: {doc['count']}")
                    if doc.get('examples'):
                        with st.expander("Show Metadata Examples", expanded=False):
                            for meta in doc['examples']:
                                st.json(meta)
                with col2:
                    # Modal confirmation for document delete
                    if st.session_state.get(f"confirm_delete_{doc['filename']}", False):
                        st.markdown(f"""
                            <div style='position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.25); z-index:10000; display:flex; align-items:center; justify-content:center;'>
                                <div style='background:#fff; border-radius:16px; box-shadow:0 8px 32px rgba(0,0,0,0.18); padding:32px 40px; min-width:320px; text-align:center;'>
                                    <div style='font-size:1.2rem; margin-bottom:18px;'>Are you sure you want to delete <b>{doc['filename']}</b>?</div>
                                    <button style='background:#d32f2f; color:#fff; border:none; border-radius:8px; padding:10px 24px; margin-right:12px; font-size:1rem; box-shadow:0 2px 8px rgba(211,47,47,0.12); cursor:pointer;' onclick="window.location.reload()">Delete</button>
                                    <button style='background:#eee; color:#333; border:none; border-radius:8px; padding:10px 24px; font-size:1rem; box-shadow:0 2px 8px rgba(0,0,0,0.08); cursor:pointer;' onclick="window.location.reload()">Cancel</button>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    if st.button("🗑️ Delete", key=f"delete_doc_{doc['filename']}", help="Delete this document", use_container_width=True):
                        st.session_state[f"confirm_delete_{doc['filename']}"] = True
                    if st.session_state.get(f"confirm_delete_{doc['filename']}", False):
                        # Actually delete if confirmed (simulate modal with rerun)
                        try:
                            del_resp = requests.delete(f"http://localhost:8000/documents/{doc['filename']}")
                            if del_resp.ok:
                                if hasattr(st, 'toast'):
                                    st.toast(f"Deleted {doc['filename']}", icon="🗑️")
                                else:
                                    st.success(f"Deleted {doc['filename']}")
                                st.session_state['documents_list'] = fetch_documents()
                                st.session_state[f"confirm_delete_{doc['filename']}"] = False
                                st.rerun()
                            else:
                                if hasattr(st, 'toast'):
                                    st.toast(f"Failed to delete: {doc['filename']}", icon="❌")
                                else:
                                    st.error("Failed to delete: " + del_resp.text)
                                st.session_state[f"confirm_delete_{doc['filename']}"] = False
                        except Exception as e:
                            if hasattr(st, 'toast'):
                                st.toast(f"Error deleting document: {str(e)}", icon="❌")
                            else:
                                st.error(f"Error deleting document: {str(e)}")
                            st.session_state[f"confirm_delete_{doc['filename']}"] = False
        # Modal confirmation for knowledge base reset
        if st.session_state.get('confirm_reset_kb', False):
            st.markdown("""
                <div style='position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.25); z-index:10000; display:flex; align-items:center; justify-content:center;'>
                    <div style='background:#fff; border-radius:16px; box-shadow:0 8px 32px rgba(0,0,0,0.18); padding:32px 40px; min-width:320px; text-align:center;'>
                        <div style='font-size:1.2rem; margin-bottom:18px;'>Are you sure you want to <b>reset the knowledge base</b>?</div>
                        <button style='background:#d32f2f; color:#fff; border:none; border-radius:8px; padding:10px 24px; margin-right:12px; font-size:1rem; box-shadow:0 2px 8px rgba(211,47,47,0.12); cursor:pointer;' onclick="window.location.reload()">Reset</button>
                        <button style='background:#eee; color:#333; border:none; border-radius:8px; padding:10px 24px; font-size:1rem; box-shadow:0 2px 8px rgba(0,0,0,0.08); cursor:pointer;' onclick="window.location.reload()">Cancel</button>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        if st.button("🧹 Reset Knowledge Base (Clear All Embeddings)", key="reset_kb_btn", use_container_width=True):
            st.session_state['confirm_reset_kb'] = True
        if st.session_state.get('confirm_reset_kb', False):
            try:
                response = requests.post('http://localhost:8000/reset_kb')
                if response.ok:
                    st.session_state['uploads'] = []
                    save_session_to_disk()
                    if hasattr(st, 'toast'):
                        st.toast("Knowledge base has been reset. All embeddings cleared.", icon="🧹")
                    else:
                        st.success("Knowledge base has been reset. All embeddings cleared.")
                else:
                    if hasattr(st, 'toast'):
                        st.toast("Failed to reset knowledge base: " + response.text, icon="❌")
                    else:
                        st.error("Failed to reset knowledge base: " + response.text)
            except Exception as e:
                if hasattr(st, 'toast'):
                    st.toast(f"Error resetting knowledge base: {str(e)}", icon="❌")
                else:
                    st.error(f"Error resetting knowledge base: {str(e)}")
            st.session_state['confirm_reset_kb'] = False
            st.rerun()

if __name__ == "__main__":
    main()