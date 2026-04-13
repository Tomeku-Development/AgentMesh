"""OpenRouter LLM provider."""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Default base URL for OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Approximate pricing per 1K tokens for common models
OPENROUTER_PRICING = {
    "anthropic/claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "anthropic/claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "anthropic/claude-3-5-haiku": {"input": 0.001, "output": 0.005},
    "anthropic/claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "openai/gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "openai/gpt-4o": {"input": 0.0025, "output": 0.01},
}


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM provider using httpx."""

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-3-haiku",
        base_url: str = OPENROUTER_BASE_URL,
    ):
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (e.g., anthropic/claude-3-haiku)
            base_url: OpenRouter API base URL
        """
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._pricing = OPENROUTER_PRICING.get(
            model, {"input": 0.001, "output": 0.003}
        )
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://mesh.tashi.network",
                    "X-Title": "MESH Supply Chain",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def model_id(self) -> str:
        return self._model

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate completion using OpenRouter API."""
        client = await self._get_client()

        # Build OpenAI-compatible request
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_body = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Retry with exponential backoff
        max_retries = 3
        base_delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            try:
                start_time = time.perf_counter()

                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=request_body,
                )

                latency_ms = (time.perf_counter() - start_time) * 1000

                if response.status_code != 200:
                    error_body = response.text[:500]
                    raise RuntimeError(
                        f"OpenRouter API error {response.status_code}: {error_body}"
                    )

                data = response.json()

                # Extract content
                content = ""
                choices = data.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")

                # Extract token counts
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                # Calculate cost estimate
                input_cost = (input_tokens / 1000) * self._pricing["input"]
                output_cost = (output_tokens / 1000) * self._pricing["output"]
                cost_estimate = input_cost + output_cost

                logger.debug(
                    f"OpenRouter completion: {input_tokens} in, {output_tokens} out, "
                    f"{latency_ms:.1f}ms, ${cost_estimate:.6f}"
                )

                return LLMResponse(
                    content=content,
                    model=self._model,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_estimate=cost_estimate,
                )

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"OpenRouter request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"OpenRouter request failed after {max_retries} attempts: {e}")

        raise RuntimeError(f"OpenRouter request failed: {last_exception}")
