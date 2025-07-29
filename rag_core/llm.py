from rag_core.config import OLLAMA_LLM_MODEL, OLLAMA_BASE_URL, logger, SYSTEM_PROMPT
from tenacity import retry, stop_after_attempt, wait_exponential

MAX_HISTORY_MESSAGES = 10  # Number of previous messages to include (excluding system and current user prompt)

class LLMHandler:
    """Handles LLM interactions with retry logic."""
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_llm(prompt: str, context: str, conversation_history=None):
        """
        Generator: Call the LLM with the given prompt, context, and optional conversation history.
        Yields each token/word as it is generated.
        """
        import ollama
        try:
            # Build structured message history for Ollama
            history = conversation_history or []
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
            # Enhanced prompt with strict fact verification and anti-hallucination measures
            enhanced_prompt = f"""Context: {context}

Question: {prompt}

Instructions: Answer the question using ONLY the information from the provided context. Present the information clearly and concisely. Always cite your sources. Provide only the direct answer without any meta-commentary, verification text, or statements about what is not in the context. Do not repeat the question or add explanatory notes about the context."""
            
            messages.append({
                "role": "user",
                "content": enhanced_prompt
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
            for chunk in response_chunks:
                print("[LLM CHUNK]", chunk)
                if chunk["done"] is False:
                    word = chunk["message"]["content"]
                    yield word
                else:
                    break
            logger.info(f"LLM response generated for prompt: {prompt[:50]}...")
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
            yield f"[Error: LLM call failed: {msg}]" 