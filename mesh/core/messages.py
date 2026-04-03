"""Pydantic models for all MESH protocol messages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def _uuid() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Envelope ───────────────────────────────────────────

class MessageHeader(BaseModel):
    """Common header for all MESH messages."""
    message_id: str = Field(default_factory=_uuid)
    timestamp: str = Field(default_factory=_now_iso)
    sender_id: str
    sender_role: Literal["buyer", "supplier", "logistics", "inspector", "oracle"]
    protocol_version: str = "mesh/1.0"
    hlc: str = ""


class MessageEnvelope(BaseModel):
    """Top-level message wrapper with signature."""
    header: MessageHeader
    payload: dict[str, Any]
    signature: str = ""


# ── Discovery ──────────────────────────────────────────

class DiscoveryAnnounce(BaseModel):
    """Agent presence announcement (retained)."""
    agent_id: str
    role: Literal["buyer", "supplier", "logistics", "inspector", "oracle"]
    capabilities: list[str] = Field(default_factory=list)
    goods_categories: list[str] = Field(default_factory=list)
    public_key_hex: str = ""
    status: Literal["online", "busy", "degraded", "rejoining"] = "online"
    max_concurrent_orders: int = 5


class Heartbeat(BaseModel):
    """Periodic liveness signal."""
    agent_id: str
    role: str
    status: Literal["healthy", "busy", "degraded"] = "healthy"
    load: float = 0.0  # 0.0 - 1.0
    active_orders: int = 0
    uptime_seconds: float = 0.0


class Goodbye(BaseModel):
    """Graceful shutdown notification."""
    agent_id: str
    reason: str = "shutdown"


# ── Orders ─────────────────────────────────────────────

class PurchaseOrderRequest(BaseModel):
    """Buyer publishes a purchase order."""
    order_id: str = Field(default_factory=_uuid)
    goods: str
    category: str
    quantity: int
    max_price_per_unit: float
    quality_threshold: float = 0.85
    delivery_deadline_seconds: int = 60
    required_capabilities: list[str] = Field(default_factory=list)
    bid_deadline_seconds: int = 10


class SupplierBid(BaseModel):
    """Supplier's bid on a purchase order."""
    order_id: str
    bid_id: str = Field(default_factory=_uuid)
    supplier_id: str
    price_per_unit: float
    available_quantity: int
    estimated_fulfillment_seconds: int = 10
    reputation_score: float = 0.5
    notes: str = ""


class CounterOffer(BaseModel):
    """Counter-offer during negotiation."""
    order_id: str
    counter_id: str = Field(default_factory=_uuid)
    original_bid_id: str
    from_agent: str
    to_agent: str
    round: int = 1
    proposed_price_per_unit: float
    proposed_quantity: int | None = None
    proposed_deadline_seconds: int | None = None
    justification: str = ""
    expires_seconds: int = 10


class BidAcceptance(BaseModel):
    """Buyer accepts a bid."""
    order_id: str
    accepted_bid_id: str
    supplier_id: str
    agreed_price_per_unit: float
    agreed_quantity: int
    escrow_amount: float
    escrow_tx_id: str = Field(default_factory=_uuid)


class BidRejection(BaseModel):
    """Buyer rejects a bid."""
    order_id: str
    rejected_bid_id: str
    supplier_id: str
    reason: str = ""


class OrderCommit(BaseModel):
    """Supplier confirms commitment."""
    order_id: str
    supplier_id: str
    committed_at: str = Field(default_factory=_now_iso)
    estimated_ready_seconds: int = 10


class OrderStatus(BaseModel):
    """Order status update."""
    order_id: str
    status: Literal[
        "open", "bidding", "negotiating", "committed", "fulfilling",
        "shipping", "delivered", "inspecting", "settled", "cancelled",
        "failed", "recovering"
    ]
    updated_by: str
    details: str = ""


# ── Shipping ───────────────────────────────────────────

class ShippingRequest(BaseModel):
    """Request for shipping quotes."""
    shipment_id: str = Field(default_factory=_uuid)
    order_id: str
    origin: str = "supplier_warehouse"
    destination: str = "buyer_warehouse"
    weight_kg: float = 10.0
    fragile: bool = False
    deadline_seconds: int = 30
    bid_deadline_seconds: int = 10


class ShippingBid(BaseModel):
    """Logistics provider's shipping bid."""
    shipment_id: str
    bid_id: str = Field(default_factory=_uuid)
    logistics_id: str
    price: float
    estimated_transit_seconds: int = 15
    vehicle_type: Literal["truck", "drone", "rail"] = "truck"


class ShippingAssign(BaseModel):
    """Shipping task assigned to logistics agent."""
    shipment_id: str
    order_id: str
    logistics_id: str
    accepted_bid_id: str
    price: float


class TransitUpdate(BaseModel):
    """In-transit status update."""
    shipment_id: str
    logistics_id: str
    status: Literal["picked_up", "in_transit", "out_for_delivery", "delivered"]
    eta_seconds: int = 0
    condition: Literal["good", "damaged", "unknown"] = "good"


# ── Quality ────────────────────────────────────────────

class InspectionRequest(BaseModel):
    """Request quality inspection."""
    inspection_id: str = Field(default_factory=_uuid)
    order_id: str
    shipment_id: str
    goods: str
    quantity_expected: int
    quality_threshold: float


class InspectionReport(BaseModel):
    """Quality inspection results."""
    inspection_id: str
    order_id: str
    shipment_id: str
    inspector_id: str
    quality_score: float  # 0.0 - 1.0
    quantity_verified: int
    quantity_defective: int = 0
    defect_descriptions: list[str] = Field(default_factory=list)
    passed: bool
    recommendation: Literal["accept", "partial_accept", "reject"] = "accept"


# ── Market ─────────────────────────────────────────────

class MarketPriceUpdate(BaseModel):
    """Oracle publishes market prices."""
    oracle_id: str
    prices: dict[str, dict[str, float]]  # {goods: {price, trend, volatility}}
    epoch: int = 0


class MarketDemand(BaseModel):
    """Oracle publishes demand forecasts."""
    oracle_id: str
    forecasts: dict[str, dict[str, float]]  # {goods: {demand, growth_rate}}
    epoch: int = 0


# ── Reputation ─────────────────────────────────────────

class ReputationUpdate(BaseModel):
    """Score change event."""
    subject_id: str
    capability: str
    old_score: float
    new_score: float
    reason: Literal[
        "order_fulfilled", "quality_pass", "on_time", "late_delivery",
        "quality_fail", "no_show", "byzantine", "decay"
    ]
    evidence_order_id: str = ""


# ── Ledger ─────────────────────────────────────────────

class LedgerTransaction(BaseModel):
    """Single economic transaction."""
    tx_id: str = Field(default_factory=_uuid)
    tx_type: Literal[
        "escrow_lock", "escrow_release", "payment", "fee", "penalty", "reward", "burn"
    ]
    from_agent: str
    to_agent: str
    amount: float
    order_id: str = ""
    memo: str = ""
    balance_after_from: float = 0.0
    balance_after_to: float = 0.0


# ── Health ─────────────────────────────────────────────

class HealthAlert(BaseModel):
    """Failure detection alert."""
    detector_id: str
    suspect_agent_id: str
    alert_type: Literal["heartbeat_timeout", "anomaly", "byzantine", "overload"]
    severity: Literal["warning", "critical", "fatal"] = "warning"
    missed_heartbeats: int = 0
    last_seen_seconds_ago: float = 0.0
    recommended_action: Literal["monitor", "redistribute", "quarantine"] = "monitor"


class RoleRedistribution(BaseModel):
    """Role reassignment after agent failure."""
    redistribution_id: str = Field(default_factory=_uuid)
    failed_agent_id: str
    failed_role: str
    replacement_agent_id: str
    assumed_capabilities: list[str] = Field(default_factory=list)
    active_orders_transferred: list[str] = Field(default_factory=list)
