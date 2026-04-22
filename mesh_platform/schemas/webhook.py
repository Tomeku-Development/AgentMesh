"""Pydantic request/response schemas for webhooks and inbound triggers."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── Request schemas ──


class WebhookCreate(BaseModel):
    """Register a new outbound webhook (Requirement 2.1, 2.6)."""

    url: str = Field(description="HTTPS URL to receive webhook POST requests")
    event_types: list[str] = Field(
        min_length=1, description="Event types to subscribe to, e.g. ['order.request']"
    )
    secret: str = Field(min_length=1, description="HMAC-SHA256 secret for signature verification")

    @field_validator("url")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        """Webhook URLs must use HTTPS protocol (Requirement 2.6)."""
        if not v.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        return v


# ── Response schemas ──


class WebhookResponse(BaseModel):
    """Webhook registration detail (Requirement 2.1)."""

    id: str
    workspace_id: str
    url: str
    event_types: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    """List wrapper for webhook registrations (Requirement 2.7)."""

    webhooks: list[WebhookResponse]


class WebhookDeliveryResponse(BaseModel):
    """Delivery attempt detail (Requirement 2.4)."""

    id: int
    webhook_id: str
    event_type: str
    payload_json: str
    status: str
    http_status_code: int | None
    response_body: str | None
    attempt_number: int
    delivered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeliveryListResponse(BaseModel):
    """List wrapper for delivery history (Requirement 2.7)."""

    deliveries: list[WebhookDeliveryResponse]


# ── Inbound trigger schemas (Requirement 2.5) ──


class InboundTriggerRequest(BaseModel):
    """Inbound order trigger from external systems (Requirement 2.5)."""

    goods: str = Field(min_length=1, description="Goods name to order")
    category: str = Field(min_length=1, description="Goods category")
    quantity: int = Field(ge=1, description="Number of units")
    max_price_per_unit: float = Field(gt=0, description="Maximum price per unit")
    quality_threshold: float = Field(
        ge=0, le=1, default=0.8, description="Minimum quality score 0-1"
    )
