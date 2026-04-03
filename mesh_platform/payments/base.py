"""Abstract payment provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PaymentResult:
    provider_reference_id: str
    payment_url: str
    raw_response: dict


@dataclass
class WebhookEvent:
    webhook_id: str
    payment_intent_id: str | None
    status: str  # paid / expired / failed
    raw_payload: dict


class PaymentProvider(ABC):
    """Abstract interface for fiat and crypto payment providers."""

    @abstractmethod
    async def create_payment(
        self, amount: float, currency: str, metadata: dict[str, Any]
    ) -> PaymentResult:
        ...

    @abstractmethod
    def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        ...

    @abstractmethod
    def parse_webhook(self, body: bytes) -> WebhookEvent:
        ...
