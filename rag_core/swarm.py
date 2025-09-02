# Swarm orchestrator for provider routing and fallback
from __future__ import annotations
from typing import Dict, Any, Generator, List, Optional

from rag_core.config import (
    SWARM_ENABLED,
    PROVIDER_PRIORITY,
    logger,
)
from rag_core.llm import LLMHandler
from rag_core.online_llm import OnlineLLMHandler


class SwarmOrchestrator:
    """Routes requests across providers according to priority with graceful fallback."""

    def __init__(self) -> None:
        self.enabled: bool = bool(SWARM_ENABLED)
        self.priority: List[str] = [p.strip().lower() for p in PROVIDER_PRIORITY]
        self.local: LLMHandler = LLMHandler()
        self.online: OnlineLLMHandler = OnlineLLMHandler()
        self.available_online: List[str] = self.online.get_available_providers()

    def _provider_iter(self, preferred: Optional[str] = None) -> List[str]:
        order = list(self.priority)
        if preferred:
            preferred_l = preferred.lower()
            if preferred_l in order:
                order = [preferred_l] + [p for p in order if p != preferred_l]
        return order

    def generate(self, prompt: str, *, context: str = "", conversation_history: Optional[List[Dict[str, Any]]] = None,
                 temperature: Optional[float] = None, max_tokens: Optional[int] = None,
                 preferred_provider: Optional[str] = None) -> str:
        if not self.enabled:
            return self.local.generate_response(prompt, context, conversation_history)

        for provider in self._provider_iter(preferred_provider):
            try:
                if provider == "ollama":
                    return self.local.generate_response(prompt, context, conversation_history)
                if provider in self.available_online:
                    ok = self.online.set_provider(provider)
                    if not ok:
                        continue
                    return self.online.generate_response(prompt, context, conversation_history,
                                                         temperature=temperature or 0.7,
                                                         max_tokens=max_tokens or 1000)
            except Exception as e:
                logger.warning(f"Provider {provider} failed, trying next: {e}")
                continue
        # Last resort
        return self.local.generate_response(prompt, context, conversation_history)

    def stream(self, prompt: str, *, context: str = "", conversation_history: Optional[List[Dict[str, Any]]] = None,
               temperature: Optional[float] = None, max_tokens: Optional[int] = None,
               preferred_provider: Optional[str] = None) -> Generator[str, None, None]:
        if not self.enabled:
            yield from self.local.call_llm(prompt, context, conversation_history,
                                           temperature=temperature, max_tokens=max_tokens)
            return

        for provider in self._provider_iter(preferred_provider):
            try:
                if provider == "ollama":
                    yield from self.local.call_llm(prompt, context, conversation_history,
                                                   temperature=temperature, max_tokens=max_tokens)
                    return
                if provider in self.available_online:
                    ok = self.online.set_provider(provider)
                    if not ok:
                        continue
                    yield from self.online.generate_streaming_response(prompt, context, conversation_history,
                                                                        temperature=temperature or 0.7,
                                                                        max_tokens=max_tokens or 1000)
                    return
            except Exception as e:
                logger.warning(f"Provider {provider} failed, trying next: {e}")
                continue
        # Last resort
        yield from self.local.call_llm(prompt, context, conversation_history,
                                       temperature=temperature, max_tokens=max_tokens)
