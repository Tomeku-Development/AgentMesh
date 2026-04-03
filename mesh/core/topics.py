"""MQTT topic constants and builders for the MESH protocol."""

from __future__ import annotations

# ── Discovery ──────────────────────────────────────────
DISCOVERY_ANNOUNCE = "mesh/discovery/announce"
DISCOVERY_HEARTBEAT = "mesh/discovery/heartbeat"
DISCOVERY_GOODBYE = "mesh/discovery/goodbye"

# ── Orders ─────────────────────────────────────────────
ORDERS_PREFIX = "mesh/orders"

def order_request(order_id: str) -> str:
    return f"{ORDERS_PREFIX}/{order_id}/request"

def order_bid(order_id: str) -> str:
    return f"{ORDERS_PREFIX}/{order_id}/bid"

def order_counter(order_id: str) -> str:
    return f"{ORDERS_PREFIX}/{order_id}/counter"

def order_accept(order_id: str) -> str:
    return f"{ORDERS_PREFIX}/{order_id}/accept"

def order_reject(order_id: str) -> str:
    return f"{ORDERS_PREFIX}/{order_id}/reject"

def order_commit(order_id: str) -> str:
    return f"{ORDERS_PREFIX}/{order_id}/commit"

def order_status(order_id: str) -> str:
    return f"{ORDERS_PREFIX}/{order_id}/status"

# ── Shipping ───────────────────────────────────────────
SHIPPING_PREFIX = "mesh/shipping"

def shipping_request(shipment_id: str) -> str:
    return f"{SHIPPING_PREFIX}/{shipment_id}/request"

def shipping_bid(shipment_id: str) -> str:
    return f"{SHIPPING_PREFIX}/{shipment_id}/bid"

def shipping_assign(shipment_id: str) -> str:
    return f"{SHIPPING_PREFIX}/{shipment_id}/assign"

def shipping_transit(shipment_id: str) -> str:
    return f"{SHIPPING_PREFIX}/{shipment_id}/transit"

def shipping_deliver(shipment_id: str) -> str:
    return f"{SHIPPING_PREFIX}/{shipment_id}/deliver"

def shipping_confirm(shipment_id: str) -> str:
    return f"{SHIPPING_PREFIX}/{shipment_id}/confirm"

# ── Quality ────────────────────────────────────────────
QUALITY_PREFIX = "mesh/quality"

def quality_request(inspection_id: str) -> str:
    return f"{QUALITY_PREFIX}/{inspection_id}/request"

def quality_report(inspection_id: str) -> str:
    return f"{QUALITY_PREFIX}/{inspection_id}/report"

def quality_dispute(inspection_id: str) -> str:
    return f"{QUALITY_PREFIX}/{inspection_id}/dispute"

# ── Market ─────────────────────────────────────────────
MARKET_PRICES = "mesh/market/prices"
MARKET_DEMAND = "mesh/market/demand"
MARKET_ALERTS = "mesh/market/alerts"

# ── Reputation ─────────────────────────────────────────
REPUTATION_SCORES = "mesh/reputation/scores"
REPUTATION_UPDATES = "mesh/reputation/updates"

# ── Ledger ─────────────────────────────────────────────
LEDGER_BALANCES = "mesh/ledger/balances"
LEDGER_TRANSACTIONS = "mesh/ledger/transactions"
LEDGER_ESCROW = "mesh/ledger/escrow"

# ── Health ─────────────────────────────────────────────
HEALTH_ALERTS = "mesh/health/alerts"
HEALTH_REDISTRIBUTION = "mesh/health/redistribution"
HEALTH_RECOVERY = "mesh/health/recovery"

# ── System ─────────────────────────────────────────────
SYSTEM_METRICS = "mesh/system/metrics"

# ── Wildcard (for bridge/dashboard) ────────────────────
MESH_WILDCARD = "mesh/#"

# ── QoS mapping ───────────────────────────────────────
QOS_FIRE_AND_FORGET = 0  # heartbeats, transit updates
QOS_AT_LEAST_ONCE = 1    # bids, status updates
QOS_EXACTLY_ONCE = 2     # commits, settlements, reputation

def qos_for_topic(topic: str) -> int:
    """Return appropriate QoS level for a given topic."""
    if "heartbeat" in topic or "transit" in topic:
        return QOS_FIRE_AND_FORGET
    if "commit" in topic or "settlement" in topic or "reputation" in topic or "ledger" in topic:
        return QOS_EXACTLY_ONCE
    return QOS_AT_LEAST_ONCE
