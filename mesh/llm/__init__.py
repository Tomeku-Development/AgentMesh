"""LLM abstraction layer for MESH multi-agent supply chain system.

This module provides a unified interface for LLM operations with:
- Multiple provider support (Amazon Bedrock, OpenRouter)
- Automatic failover with circuit breaker pattern
- Cost and latency tracking
- JSON response parsing with validation
- Prompt templates for supply chain agents
- Response caching with TTL

Example usage:
    from mesh.llm import LLMRouter, PromptTemplates

    # Create router with config
    router = LLMRouter(config)

    # Generate a response
    system_prompt, user_prompt = PromptTemplates.supplier_bid_prompt(
        goods="electronics",
        cost=50.0,
        market_price=75.0,
        ...
    )
    response = await router.complete(user_prompt, system_prompt)

    # Or get parsed JSON
    result = await router.complete_json(user_prompt, system_prompt)
"""

from __future__ import annotations

from . import prompts as PromptTemplates
from .base import LLMProvider, LLMResponse
from .bedrock import BedrockProvider
from .cache import LLMCache
from .openrouter import OpenRouterProvider
from .router import LLMDisabledError, LLMProviderError, LLMRouter

__all__ = [
    # Base classes
    "LLMProvider",
    "LLMResponse",
    # Providers
    "BedrockProvider",
    "OpenRouterProvider",
    # Router
    "LLMRouter",
    "LLMDisabledError",
    "LLMProviderError",
    # Cache
    "LLMCache",
    # Prompts (module)
    "PromptTemplates",
]
