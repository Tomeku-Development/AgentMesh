"""Pydantic schemas for ledger endpoints."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class LedgerEntryResponse(BaseModel):
    id: int
    tx_id: str
    tx_type: str
    from_agent: str
    to_agent: str
    amount: float
    order_id: str | None = None
    memo: str | None = None
    recorded_at: datetime
    model_config = {"from_attributes": True}


class LedgerListResponse(BaseModel):
    entries: list[LedgerEntryResponse]
    total: int


class BalanceResponse(BaseModel):
    agent_id: str
    balance: float


class BalancesResponse(BaseModel):
    balances: list[BalanceResponse]
