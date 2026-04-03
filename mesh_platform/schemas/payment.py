"""Pydantic schemas for payment endpoints."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    provider: str  # "xendit" or "cryptomus"
    amount: float
    currency: str


class PaymentIntentResponse(BaseModel):
    id: str
    workspace_id: str
    provider: str
    amount: float
    currency: str
    status: str
    payment_url: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    payments: list[PaymentIntentResponse]
