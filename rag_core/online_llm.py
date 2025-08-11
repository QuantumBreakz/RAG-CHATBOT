"""
Online LLM Integration Module
Supports multiple online LLM providers with a unified interface
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Generator
from abc import ABC, abstractmethod
import requests
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class OnlineLLMProvider(ABC):
    """Abstract base class for online LLM providers"""
    
    @abstractmethod
    def generate_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None, 
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate a response from the online LLM"""
        pass
    
    @abstractmethod
    def generate_streaming_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None,
                                  temperature: float = 0.7, max_tokens: int = 1000) -> Generator[str, None, None]:
        """Generate a streaming response from the online LLM"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the provider is accessible"""
        pass

class OpenAIProvider(OnlineLLMProvider):
    """OpenAI API integration"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None, 
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate a response using OpenAI API"""
        try:
            # Build messages
            messages = self._build_messages(prompt, context, conversation_history)
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return f"Error: OpenAI API returned {response.status_code}"
                
        except Exception as e:
            logger.error(f"OpenAI API request failed: {str(e)}")
            return f"Error: {str(e)}"
    
    def generate_streaming_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None,
                                  temperature: float = 0.7, max_tokens: int = 1000) -> Generator[str, None, None]:
        """Generate a streaming response using OpenAI API"""
        try:
            # Build messages
            messages = self._build_messages(prompt, context, conversation_history)
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data_json = json.loads(data_str)
                                if 'choices' in data_json and len(data_json['choices']) > 0:
                                    delta = data_json['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                yield f"Error: OpenAI API returned {response.status_code}"
                
        except Exception as e:
            logger.error(f"OpenAI API streaming request failed: {str(e)}")
            yield f"Error: {str(e)}"
    
    def _build_messages(self, prompt: str, context: str, conversation_history: List[Dict] = None) -> List[Dict]:
        """Build messages for OpenAI API"""
        from rag_core.config import SYSTEM_PROMPT
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
                role = msg.get("role", "user")
                if role == "ai":
                    role = "assistant"
                content = msg.get("content", "")
                if content.strip():
                    messages.append({"role": role, "content": content})
        
        # Add current prompt with context
        user_message = f"Context:\n{context}\n\nQuestion:\n{prompt}"
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False

class AnthropicProvider(OnlineLLMProvider):
    """Anthropic Claude API integration"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def generate_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None, 
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate a response using Anthropic API"""
        try:
            # Build messages
            messages = self._build_messages(prompt, context, conversation_history)
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                return f"Error: Anthropic API returned {response.status_code}"
                
        except Exception as e:
            logger.error(f"Anthropic API request failed: {str(e)}")
            return f"Error: {str(e)}"
    
    def generate_streaming_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None,
                                  temperature: float = 0.7, max_tokens: int = 1000) -> Generator[str, None, None]:
        """Generate a streaming response using Anthropic API"""
        try:
            # Build messages
            messages = self._build_messages(prompt, context, conversation_history)
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=data,
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data_json = json.loads(data_str)
                                if 'type' in data_json and data_json['type'] == 'content_block_delta':
                                    if 'delta' in data_json and 'text' in data_json['delta']:
                                        yield data_json['delta']['text']
                            except json.JSONDecodeError:
                                continue
            else:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                yield f"Error: Anthropic API returned {response.status_code}"
                
        except Exception as e:
            logger.error(f"Anthropic API streaming request failed: {str(e)}")
            yield f"Error: {str(e)}"
    
    def _build_messages(self, prompt: str, context: str, conversation_history: List[Dict] = None) -> List[Dict]:
        """Build messages for Anthropic API"""
        from rag_core.config import SYSTEM_PROMPT
        
        messages = []
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
                role = msg.get("role", "user")
                if role == "ai":
                    role = "assistant"
                content = msg.get("content", "")
                if content.strip():
                    messages.append({"role": role, "content": content})
        
        # Add current prompt with context
        user_message = f"Context:\n{context}\n\nQuestion:\n{prompt}"
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def test_connection(self) -> bool:
        """Test Anthropic API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Anthropic connection test failed: {str(e)}")
            return False

class OnlineLLMHandler:
    """Handler for online LLM providers with fallback to local model"""
    
    def __init__(self):
        self.providers = {}
        self.current_provider = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available online providers"""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.providers["openai"] = OpenAIProvider(openai_key)
            logger.info("OpenAI provider initialized")
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.providers["anthropic"] = AnthropicProvider(anthropic_key)
            logger.info("Anthropic provider initialized")
    
    def set_provider(self, provider_name: str) -> bool:
        """Set the current provider"""
        if provider_name in self.providers:
            self.current_provider = self.providers[provider_name]
            logger.info(f"Switched to {provider_name} provider")
            return True
        else:
            logger.warning(f"Provider {provider_name} not available")
            return False
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def test_provider(self, provider_name: str) -> bool:
        """Test if a provider is working"""
        if provider_name in self.providers:
            return self.providers[provider_name].test_connection()
        return False
    
    def generate_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None,
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate response using current provider or fallback to local"""
        if self.current_provider:
            try:
                return self.current_provider.generate_response(
                    prompt, context, conversation_history, temperature, max_tokens
                )
            except Exception as e:
                logger.error(f"Online provider failed, falling back to local: {str(e)}")
                return self._fallback_to_local(prompt, context, conversation_history, temperature, max_tokens)
        else:
            return self._fallback_to_local(prompt, context, conversation_history, temperature, max_tokens)
    
    def generate_streaming_response(self, prompt: str, context: str = "", conversation_history: List[Dict] = None,
                                  temperature: float = 0.7, max_tokens: int = 1000) -> Generator[str, None, None]:
        """Generate streaming response using current provider or fallback to local"""
        if self.current_provider:
            try:
                yield from self.current_provider.generate_streaming_response(
                    prompt, context, conversation_history, temperature, max_tokens
                )
            except Exception as e:
                logger.error(f"Online provider failed, falling back to local: {str(e)}")
                yield from self._fallback_to_local_streaming(prompt, context, conversation_history, temperature, max_tokens)
        else:
            yield from self._fallback_to_local_streaming(prompt, context, conversation_history, temperature, max_tokens)
    
    def _fallback_to_local(self, prompt: str, context: str, conversation_history: List[Dict] = None,
                          temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Fallback to local Ollama model"""
        from rag_core.llm import LLMHandler
        local_handler = LLMHandler()
        return local_handler.generate_response(prompt, context, conversation_history)
    
    def _fallback_to_local_streaming(self, prompt: str, context: str, conversation_history: List[Dict] = None,
                                   temperature: float = 0.7, max_tokens: int = 1000) -> Generator[str, None, None]:
        """Fallback to local Ollama model for streaming"""
        from rag_core.llm import LLMHandler
        local_handler = LLMHandler()
        yield from local_handler.call_llm(prompt, context, conversation_history)

# Global instance
online_llm_handler = OnlineLLMHandler()
