"""LLM Router with failover, circuit breaker, and statistics tracking."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class LLMDisabledError(Exception):
    """Raised when LLM is disabled in configuration."""

    pass


class LLMProviderError(Exception):
    """Raised when all LLM providers fail."""

    pass


@dataclass
class ProviderStats:
    """Statistics for a single provider."""

    name: str
    calls: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    total_cost: float = 0.0
    latencies: deque = field(default_factory=lambda: deque(maxlen=20))
    circuit_open: bool = False
    circuit_open_until: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency from recent calls."""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    def record_success(self, latency_ms: float, cost: float) -> None:
        """Record a successful call."""
        self.calls += 1
        self.consecutive_failures = 0
        self.latencies.append(latency_ms)
        self.total_cost += cost

    def record_failure(self) -> None:
        """Record a failed call."""
        self.calls += 1
        self.failures += 1
        self.consecutive_failures += 1

    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if not self.circuit_open:
            return False
        # Check if cooldown period has passed
        if time.time() > self.circuit_open_until:
            logger.info(f"Circuit breaker for {self.name} resetting (cooldown expired)")
            self.circuit_open = False
            self.consecutive_failures = 0
            return False
        return True

    def trip_circuit(self, cooldown_seconds: float = 60.0) -> None:
        """Trip the circuit breaker."""
        self.circuit_open = True
        self.circuit_open_until = time.time() + cooldown_seconds
        logger.warning(
            f"Circuit breaker tripped for {self.name}. "
            f"Will retry after {cooldown_seconds}s"
        )


class LLMRouter:
    """Router for LLM calls with failover, circuit breaker, and statistics.

    Primary provider is tried first. On failure, fallback provider is used.
    Circuit breaker prevents cascading failures by temporarily disabling
    providers with consecutive failures.
    """

    CIRCUIT_FAILURE_THRESHOLD = 5
    CIRCUIT_COOLDOWN_SECONDS = 60.0

    def __init__(self, config: Any = None):
        """Initialize the router with configuration.

        Args:
            config: MeshConfig instance. LLM config fields will be accessed
                    with graceful fallback to defaults if not present.
        """
        self._primary: LLMProvider | None = None
        self._fallback: LLMProvider | None = None
        self._primary_stats = ProviderStats(name="primary")
        self._fallback_stats = ProviderStats(name="fallback")
        self._enabled = True

        if config is not None:
            self._init_from_config(config)

    def _init_from_config(self, config: Any) -> None:
        """Initialize providers from MeshConfig."""
        # Check if LLM is enabled
        try:
            self._enabled = getattr(config, "llm_enabled", True)
        except AttributeError:
            self._enabled = True

        if not self._enabled:
            logger.info("LLM is disabled in configuration")
            return

        # Get provider configuration with graceful fallbacks
        try:
            primary_provider = getattr(config, "llm_primary_provider", "openrouter")
        except AttributeError:
            primary_provider = "openrouter"

        try:
            model = getattr(config, "llm_model", "anthropic/claude-3-haiku")
        except AttributeError:
            model = "anthropic/claude-3-haiku"

        # Initialize primary provider
        self._primary = self._create_provider(config, primary_provider, model, "primary")

        # Initialize fallback provider (if configured)
        try:
            fallback_provider = getattr(config, "llm_fallback_provider", None)
            fallback_model = getattr(config, "llm_fallback_model", model)
        except AttributeError:
            fallback_provider = None
            fallback_model = model

        if fallback_provider:
            self._fallback = self._create_provider(
                config, fallback_provider, fallback_model, "fallback"
            )

    def _create_provider(
        self, config: Any, provider_type: str, model: str, role: str
    ) -> LLMProvider | None:
        """Create a provider instance based on type."""
        provider_type = provider_type.lower()

        if provider_type == "bedrock":
            return self._create_bedrock_provider(config, model, role)
        elif provider_type == "openrouter":
            return self._create_openrouter_provider(config, model, role)
        else:
            logger.warning(f"Unknown provider type: {provider_type}")
            return None

    def _create_bedrock_provider(
        self, config: Any, model: str, role: str
    ) -> LLMProvider:
        """Create a Bedrock provider."""
        try:
            region = getattr(config, "llm_bedrock_region", "us-east-1")
        except AttributeError:
            region = "us-east-1"

        try:
            access_key = getattr(config, "llm_bedrock_access_key", "")
        except AttributeError:
            access_key = ""

        try:
            secret_key = getattr(config, "llm_bedrock_secret_key", "")
        except AttributeError:
            secret_key = ""

        logger.info(f"Creating Bedrock provider ({role}) with model {model}")
        from .bedrock import BedrockProvider

        return BedrockProvider(
            region=region,
            access_key_id=access_key,
            secret_access_key=secret_key,
            model_id=model,
        )

    def _create_openrouter_provider(
        self, config: Any, model: str, role: str
    ) -> LLMProvider:
        """Create an OpenRouter provider."""
        try:
            api_key = getattr(config, "llm_openrouter_api_key", "")
        except AttributeError:
            api_key = ""

        try:
            base_url = getattr(config, "llm_openrouter_base_url", "https://openrouter.ai/api/v1")
        except AttributeError:
            base_url = "https://openrouter.ai/api/v1"

        if not api_key:
            logger.warning(f"OpenRouter API key not configured for {role} provider")

        logger.info(f"Creating OpenRouter provider ({role}) with model {model}")
        from .openrouter import OpenRouterProvider

        return OpenRouterProvider(
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    def set_providers(
        self, primary: LLMProvider, fallback: LLMProvider | None = None
    ) -> None:
        """Manually set providers (for testing or custom configuration)."""
        self._primary = primary
        self._fallback = fallback
        self._primary_stats = ProviderStats(name=primary.name if primary else "primary")
        self._fallback_stats = ProviderStats(name=fallback.name if fallback else "fallback")
        self._enabled = True

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate completion with failover.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse from successful provider

        Raises:
            LLMDisabledError: If LLM is disabled
            LLMProviderError: If all providers fail
        """
        if not self._enabled:
            raise LLMDisabledError("LLM is disabled in configuration")

        errors = []

        # Try primary provider
        if self._primary and not self._primary_stats.is_circuit_open():
            try:
                response = await self._primary.complete(
                    prompt, system_prompt, temperature, max_tokens
                )
                self._primary_stats.record_success(
                    response.latency_ms, response.cost_estimate
                )
                return response
            except Exception as e:
                logger.warning(f"Primary provider failed: {e}")
                self._primary_stats.record_failure()
                errors.append(f"primary: {e}")

                # Check if circuit should trip
                if (
                    self._primary_stats.consecutive_failures
                    >= self.CIRCUIT_FAILURE_THRESHOLD
                ):
                    self._primary_stats.trip_circuit(self.CIRCUIT_COOLDOWN_SECONDS)
        elif self._primary and self._primary_stats.is_circuit_open():
            logger.debug("Primary provider circuit is open, skipping")

        # Try fallback provider
        if self._fallback and not self._fallback_stats.is_circuit_open():
            try:
                response = await self._fallback.complete(
                    prompt, system_prompt, temperature, max_tokens
                )
                self._fallback_stats.record_success(
                    response.latency_ms, response.cost_estimate
                )
                return response
            except Exception as e:
                logger.warning(f"Fallback provider failed: {e}")
                self._fallback_stats.record_failure()
                errors.append(f"fallback: {e}")

                # Check if circuit should trip
                if (
                    self._fallback_stats.consecutive_failures
                    >= self.CIRCUIT_FAILURE_THRESHOLD
                ):
                    self._fallback_stats.trip_circuit(self.CIRCUIT_COOLDOWN_SECONDS)
        elif self._fallback and self._fallback_stats.is_circuit_open():
            logger.debug("Fallback provider circuit is open, skipping")

        # All providers failed
        if not self._primary and not self._fallback:
            raise LLMProviderError("No LLM providers configured")

        raise LLMProviderError(
            f"All LLM providers failed: {'; '.join(errors)}"
        )

    async def complete_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Generate completion and parse as JSON.

        Same failover logic as complete().

        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON dictionary

        Raises:
            LLMDisabledError: If LLM is disabled
            LLMProviderError: If all providers fail
            ValueError: If response cannot be parsed as JSON
        """
        if not self._enabled:
            raise LLMDisabledError("LLM is disabled in configuration")

        errors = []

        # Try primary provider
        if self._primary and not self._primary_stats.is_circuit_open():
            try:
                result = await self._primary.complete_json(
                    prompt, system_prompt, temperature, max_tokens
                )
                return result
            except Exception as e:
                logger.warning(f"Primary provider JSON failed: {e}")
                self._primary_stats.record_failure()
                errors.append(f"primary: {e}")

                if (
                    self._primary_stats.consecutive_failures
                    >= self.CIRCUIT_FAILURE_THRESHOLD
                ):
                    self._primary_stats.trip_circuit(self.CIRCUIT_COOLDOWN_SECONDS)

        # Try fallback provider
        if self._fallback and not self._fallback_stats.is_circuit_open():
            try:
                result = await self._fallback.complete_json(
                    prompt, system_prompt, temperature, max_tokens
                )
                return result
            except Exception as e:
                logger.warning(f"Fallback provider JSON failed: {e}")
                self._fallback_stats.record_failure()
                errors.append(f"fallback: {e}")

                if (
                    self._fallback_stats.consecutive_failures
                    >= self.CIRCUIT_FAILURE_THRESHOLD
                ):
                    self._fallback_stats.trip_circuit(self.CIRCUIT_COOLDOWN_SECONDS)

        if not self._primary and not self._fallback:
            raise LLMProviderError("No LLM providers configured")

        raise LLMProviderError(
            f"All LLM providers failed: {'; '.join(errors)}"
        )

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all providers.

        Returns:
            Dictionary with per-provider stats and overall stats
        """
        primary_dict = {
            "name": self._primary_stats.name,
            "calls": self._primary_stats.calls,
            "failures": self._primary_stats.failures,
            "avg_latency_ms": round(self._primary_stats.avg_latency_ms, 2),
            "total_cost": round(self._primary_stats.total_cost, 6),
            "circuit_open": self._primary_stats.is_circuit_open(),
        }

        fallback_dict = {
            "name": self._fallback_stats.name,
            "calls": self._fallback_stats.calls,
            "failures": self._fallback_stats.failures,
            "avg_latency_ms": round(self._fallback_stats.avg_latency_ms, 2),
            "total_cost": round(self._fallback_stats.total_cost, 6),
            "circuit_open": self._fallback_stats.is_circuit_open(),
        }

        return {
            "enabled": self._enabled,
            "primary": primary_dict,
            "fallback": fallback_dict,
            "total_calls": self._primary_stats.calls + self._fallback_stats.calls,
            "total_cost": round(
                self._primary_stats.total_cost + self._fallback_stats.total_cost, 6
            ),
        }

    def reset_circuits(self) -> None:
        """Reset all circuit breakers."""
        self._primary_stats.circuit_open = False
        self._primary_stats.consecutive_failures = 0
        self._fallback_stats.circuit_open = False
        self._fallback_stats.consecutive_failures = 0
        logger.info("All circuit breakers reset")

    @property
    def enabled(self) -> bool:
        """Check if LLM is enabled."""
        return self._enabled

    @property
    def primary_provider(self) -> LLMProvider | None:
        """Get primary provider."""
        return self._primary

    @property
    def fallback_provider(self) -> LLMProvider | None:
        """Get fallback provider."""
        return self._fallback
