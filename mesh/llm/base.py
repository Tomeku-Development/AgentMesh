"""Abstract base class for LLM providers."""

from __future__ import annotations

import abc
import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from an LLM completion."""

    content: str
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_estimate: float  # USD estimate


class LLMProvider(abc.ABC):
    """Abstract base class for LLM providers."""

    @abc.abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            prompt: The user prompt/message
            system_prompt: System instructions (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content and metadata
        """
        ...

    async def complete_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Complete and parse as JSON.

        Args:
            prompt: The user prompt/message
            system_prompt: System instructions (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        resp = await self.complete(prompt, system_prompt, temperature, max_tokens)

        # Try to extract JSON from response (handle markdown code blocks)
        text = resp.content.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            if len(lines) > 2:
                text = "\n".join(lines[1:-1])
            elif len(lines) == 2:
                text = lines[1]

        # Try to find JSON in the text
        text = text.strip()

        # Handle case where JSON is embedded in other text
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx : end_idx + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nText: {text[:500]}")
            raise ValueError(f"Invalid JSON response: {e}") from e

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return provider name for logging/metrics."""
        ...

    @property
    @abc.abstractmethod
    def model_id(self) -> str:
        """Return the model identifier."""
        ...
