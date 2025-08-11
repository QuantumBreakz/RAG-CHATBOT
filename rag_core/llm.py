from rag_core.config import OLLAMA_LLM_MODEL, OLLAMA_BASE_URL, logger, SYSTEM_PROMPT
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict, Any
# --- Add Cross-Language Support import ---
from rag_core.language_processor import language_processor, LanguageCode

MAX_HISTORY_MESSAGES = 10  # Number of previous messages to include (excluding system and current user prompt)

class LLMHandler:
    """Handles LLM interactions with retry logic."""
    
    def __init__(self):
        """Initialize LLM handler"""
        pass
    
    def generate_response(self, prompt: str, context: str = "", conversation_history=None, 
                        target_language: LanguageCode = None) -> str:
        """
        Generate a complete response from the LLM with strict context enforcement and conversation history.
        Returns the full response as a string.
        """
        # Process multi-language query if target language is specified
        original_prompt = prompt
        if target_language and target_language != LanguageCode.ENGLISH:
            # Detect and translate the query
            multi_lang_query = language_processor.process_multi_language_query(
                prompt, [target_language]
            )
            
            if target_language in multi_lang_query.translated_queries:
                prompt = multi_lang_query.translated_queries[target_language]
                logger.info(f"Translated query from {multi_lang_query.detected_language.value} "
                          f"to {target_language.value}: {original_prompt} -> {prompt}")
        
        # Log the context and conversation history for debugging
        logger.info(f"LLM Context for query: {repr(context)[:1000]}")
        logger.info(f"LLM Conversation History: {self._format_history(conversation_history)[:1000]}")
        
        # Use the proper system prompt with anti-hallucination rules
        user_prompt = f"""
Context:
{context}

Conversation History (last 5 turns):
{self._format_history(conversation_history)}

Question:
{prompt}
"""
        
        response_parts = []
        try:
            for word in self.call_llm(user_prompt, context, conversation_history):
                response_parts.append(word)
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {str(e)}"
        answer = ''.join(response_parts)
        return answer
    
    def process_multi_language_query(self, query: str, target_languages: List[LanguageCode] = None) -> Dict[str, Any]:
        """
        Process a query in multiple languages and return responses for each language.
        """
        if not target_languages:
            target_languages = [LanguageCode.ENGLISH]
        
        # Process the multi-language query
        multi_lang_query = language_processor.process_multi_language_query(query, target_languages)
        
        # Generate responses for each target language
        responses = {}
        for target_lang in target_languages:
            if target_lang in multi_lang_query.translated_queries:
                translated_query = multi_lang_query.translated_queries[target_lang]
                
                # Generate response for this language
                response = self.generate_response(
                    prompt=translated_query,
                    target_language=target_lang
                )
                
                responses[target_lang.value] = {
                    "query": translated_query,
                    "response": response,
                    "language": target_lang.value,
                    "confidence": multi_lang_query.confidence
                }
        
        return {
            "original_query": query,
            "detected_language": multi_lang_query.detected_language.value,
            "detection_confidence": multi_lang_query.confidence,
            "processing_time": multi_lang_query.processing_time,
            "responses": responses,
            "metadata": multi_lang_query.metadata
        }

    def _format_history(self, conversation_history):
        if not conversation_history:
            return ""
        # Only include the last 5 user+assistant pairs (10 messages)
        history = conversation_history[-10:]
        formatted = ""
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted += f"{role.capitalize()}: {content}\n"
        return formatted

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_llm(prompt: str, context: str, conversation_history=None, *, model_name: str | None = None, temperature: float | None = None, max_tokens: int | None = None):
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
                
                # Clean content - remove timestamp pollution and metadata
                content = msg['content']
                # Remove timestamp patterns like [timestamp: 2025-07-29T08:46:02.115Z]
                import re
                content = re.sub(r'\[timestamp: [^\]]+\]', '', content)
                content = re.sub(r'\[file: [^\]]+\]', '', content)
                content = re.sub(r'\[chunk: [^\]]+\]', '', content)
                # Clean up extra whitespace
                content = re.sub(r'\s+', ' ', content).strip()
                
                if content:  # Only add if content is not empty after cleaning
                    messages.append({
                        "role": role,
                        "content": content
                    })
            
            # Use the prompt parameter directly (which should already contain context and history)
            user_prompt = prompt
            
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            # Debug: print prompt and context
            print("[LLM CALL] Prompt:", prompt)
            print("[LLM CALL] Context:", context)
            print("[LLM CALL] Messages:", messages)
            
            # Build options with overrides
            opts = {"base_url": OLLAMA_BASE_URL}
            if temperature is not None:
                opts["temperature"] = float(temperature)
            if max_tokens is not None:
                opts["num_predict"] = int(max_tokens)

            response_chunks = ollama.chat(
                model=(model_name or OLLAMA_LLM_MODEL),
                stream=True,
                options=opts,
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

    @staticmethod
    def _format_history_static(conversation_history):
        if not conversation_history:
            return ""
        history = conversation_history[-10:]
        formatted = ""
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted += f"{role.capitalize()}: {content}\n"
        return formatted 