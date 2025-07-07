from rag_core.config import OLLAMA_LLM_MODEL, OLLAMA_BASE_URL, logger, SYSTEM_PROMPT
from tenacity import retry, stop_after_attempt, wait_exponential
import streamlit as st

class LLMHandler:
    """Handles LLM interactions with retry logic."""
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_llm(prompt: str, context: str, stream_callback=None):
        import ollama
        try:
            # Build conversation history string from UI format (role/content)
            history_str = ""
            history = st.session_state.conversation_history
            for i in range(0, len(history)-1, 2):
                user_msg = history[i]
                ai_msg = history[i+1] if i+1 < len(history) else None
                if user_msg["role"] == "user":
                    history_str += f"Q: {user_msg['content']}\n"
                    if ai_msg and ai_msg["role"] == "ai":
                        history_str += f"A: {ai_msg['content']}\n"
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
                    word = chunk["message"]["content"]
                    response += word
                    if stream_callback:
                        stream_callback(word)
                else:
                    break
            logger.info(f"LLM response generated for prompt: {prompt[:50]}...")
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            st.error(f"Error communicating with LLM: {str(e)}")
            return "" 