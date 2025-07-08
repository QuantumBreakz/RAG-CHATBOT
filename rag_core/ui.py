# rag_core/ui.py
"""
Streamlit UI for PITB RAG MVP with sidebar, chat bubbles, header, and footer.
"""
import streamlit as st
from rag_core.vectorstore import VectorStore
from rag_core.document import DocumentProcessor
from rag_core.llm import LLMHandler
from rag_core.utils import sanitize_input
from rag_core import history
from rag_core import cache
from datetime import datetime
import base64
import logging

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
        .stTextInput > div > div > input {
            background-color: #3d3d3d !important;
            color: #ffffff !important;
        }
        .stButton > button {
            background-color: #4d4d4d !important;
            color: #ffffff !important;
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
            VectorStore.clear_vector_collection()
            st.session_state['uploads'] = []
            save_session_to_disk()
            st.success("Knowledge base has been reset. All embeddings cleared.")
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
        
        st.markdown("---")
        
        # File Upload Section
        st.markdown("## 📄 Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload PDF or DOCX files",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="file_uploader"
        )

        # Only process files that are not already in uploads (by file_hash)
        if uploaded_files:
            existing_hashes = {u['file_hash'] for u in st.session_state.get('uploads', [])}
            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.read()
                file_hash = cache.get_file_hash(file_bytes)
                if file_hash in existing_hashes:
                    continue  # Skip files already processed
                chat_id = st.session_state.get('conversation_id')
                # Check if we have a valid chat_id
                if chat_id is None:
                    st.error("No active conversation. Please start a new chat or select an existing one.")
                    continue
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    import tempfile
                    suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".docx"
                    temp_file = tempfile.NamedTemporaryFile("wb", suffix=suffix, delete=False)
                    temp_file.write(file_bytes)
                    temp_file.close()
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    try:
                        status_text.text("📄 Loading document...")
                        progress_bar.progress(20)
                        all_splits = DocumentProcessor.process_document(uploaded_file, file_bytes)
                        if all_splits:
                            status_text.text(f"🔍 Creating embeddings for {len(all_splits)} chunks...")
                            progress_bar.progress(50)
                            success = VectorStore.add_to_vector_collection(all_splits, uploaded_file.name)
                            if success:
                                progress_bar.progress(80)
                                status_text.text("💾 Saving to knowledge base...")
                                if 'uploads' not in st.session_state:
                                    st.session_state['uploads'] = []
                                if not any(u['file_hash'] == file_hash for u in st.session_state['uploads']):
                                    st.session_state['uploads'].append({
                                        'filename': uploaded_file.name,
                                        'file_hash': file_hash,
                                        'metadata': {'size': uploaded_file.size, 'type': uploaded_file.type, 'uploaded_at': datetime.now().isoformat(timespec='seconds')}
                                    })
                                    save_session_to_disk()
                                progress_bar.progress(100)
                                status_text.text("✅ Complete!")
                                st.success(f"✅ {uploaded_file.name} processed and added to knowledge base!")
                            else:
                                st.error(f"❌ Failed to add {uploaded_file.name} to vector collection. Please try again.")
                        else:
                            st.error(f"❌ Failed to process {uploaded_file.name}. The file might be corrupted or empty.")
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                        logging.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    finally:
                        progress_bar.empty()
                        status_text.empty()
        
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

    # --- Main Chat Area ---
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Conversation History Navigation
    with st.expander("🗂️ Conversation History", expanded=False):
        search_query = st.text_input("Search messages", key="history_search")
        filtered_history = [
            (i, msg) for i, msg in enumerate(st.session_state.get("conversation_history", []))
            if search_query.lower() in msg["content"].lower()
        ] if search_query else list(enumerate(st.session_state.get("conversation_history", [])))
        for i, msg in filtered_history:
            role = "🧑‍💼 User" if msg["role"] == "user" else "🤖 AI"
            snippet = msg["content"][:60] + ("..." if len(msg["content"]) > 60 else "")
            ts = msg.get("timestamp", "")[:19]
            highlight_style = "background:#ffe082; border-radius:6px;" if st.session_state.get("highlight_msg", -1) == i else ""
            if st.button(f"{role} | {ts} | {snippet}", key=f"history_btn_{i}"):
                st.session_state["highlight_msg"] = i
        st.caption("Click a message to highlight it in the chat below.")

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
                    # --- Edit user message logic ---
                    is_user = msg["role"] == "user"
                    edit_key = f"edit_msg_{i}"
                    editing = st.session_state.get(edit_key, False)
                    is_followup = msg.get("followup_to") is not None
                    followup_badge = "<span style='color:#1976D2; font-size:13px; margin-left:8px;'>↩️ Follow-up</span>" if is_followup else ""
                    highlight = st.session_state.get("highlight_msg", -1) == i
                    highlight_box = "box-shadow: 0 0 0 3px #ffe082;" if highlight else ""
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
                            col1, col2 = st.columns([8,1])
                            with col1:
                                st.markdown(
                                    f"""
                                    <div style=\"display: flex; justify-content: flex-end; margin-bottom: 15px; padding: 0 10px; {highlight_box}\">
                                        <div style=\"background: linear-gradient(135deg, #DCF8C6 0%, #C8E6C9 100%); color: #2E7D32; border-radius: 18px 18px 4px 18px; padding: 12px 18px; max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #A5D6A7;\">
                                            <div style=\"font-weight: 600; margin-bottom: 4px;\">You {followup_badge}</div>
                                            <div style=\"line-height: 1.4;\">{msg['content']}</div>
                                            <div style=\"font-size: 11px; color: #666; margin-top: 6px; text-align: right;\">{msg.get('timestamp', '')[:19]}</div>
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            with col2:
                                if st.button("✏️", key=f"edit_btn_{i}"):
                                    st.session_state[edit_key] = True
                                    st.rerun()
                        else:
                            st.markdown(
                                f"""
                                <div style=\"display: flex; justify-content: flex-start; margin-bottom: 15px; padding: 0 10px; {highlight_box}\">
                                    <div style=\"background: linear-gradient(135deg, #F5F5F5 0%, #E0E0E0 100%); color: #424242; border-radius: 18px 18px 18px 4px; padding: 12px 18px; max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #D0D0D0;\">
                                        <div style=\"font-weight: 600; margin-bottom: 4px; color: #1976D2;\">AI Assistant {followup_badge}</div>
                                        <div style=\"line-height: 1.4;\">{msg['content']}</div>
                                        <div style=\"font-size: 11px; color: #666; margin-top: 6px; text-align: right;\">{msg.get('timestamp', '')[:19]}</div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    if not is_user and msg.get("context_preview"):
                        with st.expander("Context Used", expanded=False):
                            st.markdown(f"<div style='font-size:13px; color:#333; background:#f9f9f9; border-radius:8px; padding:8px 12px; margin-bottom:4px;'>{msg['context_preview']}</div>", unsafe_allow_html=True)
        # End of chat rendering loop

        # Chat input with better styling
        st.markdown("---")
        # Disable chat input while processing
        is_processing = st.session_state.get('is_processing', False)
        chat_input_key = f"chat_input_{st.session_state.get('conversation_id', '')}_{len(st.session_state.get('conversation_history', []))}"

        # Use a form to ensure only Enter submits the chat input
        with st.form(key="chat_input_form", clear_on_submit=False):
            chat_input = st.text_input(
                "💬 Type your question and press Enter", 
                key=chat_input_key, 
                value=st.session_state.get('chat_input_value', ''),
                placeholder="Ask about your uploaded documents...",
                disabled=is_processing
            )
            submitted = st.form_submit_button("Send", use_container_width=True)

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
                    results = VectorStore.query_with_expanded_context(
                        sanitized_prompt,
                        n_results=st.session_state.get("n_results", 3),
                        expand=2,
                        filename=selected_filename
                    )
                    context = results.get("documents", [[]])[0] if results.get("documents") else []
                    context_str = " ".join(context)
                    logging.info(f"[DEBUG] context_str: {context_str}")
                    if not context_str.strip():
                        st.session_state["conversation_history"].append({
                            "role": "ai", 
                            "content": "[No relevant context found for your query. Please try rephrasing or uploading more documents.]", 
                            "timestamp": datetime.now().isoformat(timespec='seconds')
                        })
                        save_session_to_disk()
                        history.save_chat_context(st.session_state['conversation_id'], st.session_state['conversation_history'])
                        st.session_state['is_processing'] = False
                        st.session_state['chat_input_value'] = ''
                        st.experimental_set_query_params(**{})
                    else:
                        try:
                            # Stream the LLM response word by word
                            response_placeholder = st.empty()
                            streamed_response = ""
                            def stream_callback(word):
                                nonlocal streamed_response
                                streamed_response += word
                                response_placeholder.markdown(
                                    f"""
                                    <div style=\"display: flex; justify-content: flex-start; margin-bottom: 15px; padding: 0 10px;\">
                                        <div style=\"background: linear-gradient(135deg, #F5F5F5 0%, #E0E0E0 100%); color: #424242; border-radius: 18px 18px 18px 4px; padding: 12px 18px; max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #D0D0D0;\">
                                            <div style=\"font-weight: 600; margin-bottom: 4px; color: #1976D2;\">AI Assistant</div>
                                            <div style=\"line-height: 1.4;\">{streamed_response}</div>
                                            <div style=\"font-size: 11px; color: #666; margin-top: 6px; text-align: right;\">{datetime.now().isoformat(timespec='seconds')[:19]}</div>
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            response = LLMHandler.call_llm(sanitized_prompt, context_str, stream_callback=stream_callback)
                        except Exception as llm_exc:
                            logging.error(f"[LLM ERROR] {llm_exc}")
                            response = "[Error: Could not answer the question. LLM error: {}]".format(str(llm_exc))
                            streamed_response = response
                        st.session_state["conversation_history"].append({
                            "role": "ai", 
                            "content": streamed_response, 
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

if __name__ == "__main__":
    main()