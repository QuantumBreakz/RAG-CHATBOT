from rag_core.config import OLLAMA_LLM_MODEL, OLLAMA_BASE_URL, logger, SYSTEM_PROMPT
from tenacity import retry, stop_after_attempt, wait_exponential
import streamlit as st

MAX_HISTORY_MESSAGES = 10  # Number of previous messages to include (excluding system and current user prompt)

class LLMHandler:
    """Handles LLM interactions with retry logic."""
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_llm(prompt: str, context: str, stream_callback=None):
        import ollama
        try:
            # Build structured message history for Ollama
            history = st.session_state.conversation_history
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            # Only include the last MAX_HISTORY_MESSAGES
            truncated_history = history[-MAX_HISTORY_MESSAGES:] if len(history) > MAX_HISTORY_MESSAGES else history
            for msg in truncated_history:
                role = msg["role"]
                if role == "ai":
                    role = "assistant"
                elif role == "user":
                    role = "user"
                else:
                    continue  # skip unknown roles
                # Build metadata string
                meta = []
                if "timestamp" in msg:
                    meta.append(f"timestamp: {msg['timestamp']}")
                if "file" in msg:
                    meta.append(f"file: {msg['file']}")
                if "chunk" in msg:
                    meta.append(f"chunk: {msg['chunk']}")
                meta_str = " ".join(f"[{m}]" for m in meta)
                content = f"{meta_str} {msg['content']}" if meta_str else msg['content']
                messages.append({
                    "role": role,
                    "content": content
                })
            # Append the current user prompt as the last message
            messages.append({
                "role": "user",
                "content": f"Context: {context}\nQuestion: {prompt}"
            })
            # Debug: print prompt and context
            print("[LLM CALL] Prompt:", prompt)
            print("[LLM CALL] Context:", context)
            print("[LLM CALL] Messages:", messages)
            response_chunks = ollama.chat(
                model=OLLAMA_LLM_MODEL,
                stream=True,
                options={"base_url": OLLAMA_BASE_URL},
                messages=messages,
            )
            response = ""
            for chunk in response_chunks:
                print("[LLM CHUNK]", chunk)
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
            import traceback
            err_str = str(e)
            tb_str = traceback.format_exc()
            if 'Failed to establish a new connection' in err_str or 'Connection refused' in err_str:
                msg = '[LLM ERROR] Could not connect to Ollama server. Check OLLAMA_BASE_URL and if the server is running.'
            elif 'out of memory' in err_str.lower() or 'memory' in err_str.lower():
                msg = '[LLM ERROR] System out of memory. Check RAM usage and Ollama model requirements.'
            else:
                msg = f'[LLM ERROR] {err_str}'
            logger.error(msg + '\n' + tb_str)
            print(msg)
            print(tb_str)
            st.error(f"Error communicating with LLM: {msg}")
            return f"[Error: LLM call failed: {msg}]" 