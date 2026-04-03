"""Tests for Pydantic message models and protocol envelope."""

import pytest
from mesh.core.messages import (
    MessageEnvelope,
    MessageHeader,
    PurchaseOrderRequest,
    SupplierBid,
    CounterOffer,
    BidAcceptance,
    Heartbeat,
    DiscoveryAnnounce,
    LedgerTransaction,
    HealthAlert,
    InspectionReport,
)
from mesh.core.protocol import (
    build_envelope,
    verify_envelope,
    serialize_envelope,
    deserialize_envelope,
)
from mesh.core.clock import HLC


class TestMessageModels:
    def test_purchase_order_creation(self):
        po = PurchaseOrderRequest(
            goods="laptop_display", category="electronics",
            quantity=50, max_price_per_unit=120.0,
        )
        assert po.goods == "laptop_display"
        assert po.order_id  # Auto-generated UUID
        assert po.quality_threshold == 0.85  # Default

    def test_supplier_bid_creation(self):
        bid = SupplierBid(
            order_id="order-1", supplier_id="sup-1",
            price_per_unit=105.0, available_quantity=50,
        )
        assert bid.bid_id  # Auto-generated
        assert bid.reputation_score == 0.5  # Default

    def test_counter_offer_creation(self):
        counter = CounterOffer(
            order_id="order-1", original_bid_id="bid-1",
            from_agent="buyer-1", to_agent="sup-1",
            round=1, proposed_price_per_unit=100.0,
        )
        assert counter.round == 1
        assert counter.expires_seconds == 10

    def test_heartbeat_creation(self):
        hb = Heartbeat(agent_id="agent-1", role="buyer")
        assert hb.status == "healthy"
        assert hb.load == 0.0

    def test_inspection_report_validation(self):
        report = InspectionReport(
            inspection_id="insp-1", order_id="order-1",
            shipment_id="ship-1", inspector_id="ins-1",
            quality_score=0.92, quantity_verified=48,
            quantity_defective=2, passed=True,
        )
        assert report.passed
        assert report.recommendation == "accept"

    def test_ledger_transaction_types(self):
        tx = LedgerTransaction(
            tx_type="payment", from_agent="buyer", to_agent="supplier",
            amount=5000.0, order_id="order-1",
        )
        assert tx.tx_id  # Auto-generated
        assert tx.tx_type == "payment"


class TestProtocolEnvelope:
    def test_build_envelope(self):
        payload = PurchaseOrderRequest(
            goods="test", category="test", quantity=10, max_price_per_unit=100,
        )
        hlc = HLC.create("test-node")
        envelope = build_envelope("agent-1", "buyer", payload, hlc)
        assert envelope.header.sender_id == "agent-1"
        assert envelope.header.sender_role == "buyer"
        assert envelope.signature != ""

    def test_verify_envelope_valid(self):
        payload = Heartbeat(agent_id="agent-1", role="buyer")
        hlc = HLC.create("test-node")
        envelope = build_envelope("agent-1", "buyer", payload, hlc)
        assert verify_envelope(envelope)

    def test_verify_envelope_tampered(self):
        payload = Heartbeat(agent_id="agent-1", role="buyer")
        envelope = build_envelope("agent-1", "buyer", payload)
        envelope.payload["agent_id"] = "tampered"
        assert not verify_envelope(envelope)

    def test_serialize_deserialize_roundtrip(self):
        payload = SupplierBid(
            order_id="o1", supplier_id="s1",
            price_per_unit=100, available_quantity=50,
        )
        envelope = build_envelope("s1", "supplier", payload)
        serialized = serialize_envelope(envelope)
        restored = deserialize_envelope(serialized)
        assert restored.header.sender_id == "s1"
        assert restored.payload["order_id"] == "o1"

    def test_deserialize_bytes(self):
        payload = Heartbeat(agent_id="a1", role="oracle")
        envelope = build_envelope("a1", "oracle", payload)
        as_bytes = serialize_envelope(envelope).encode("utf-8")
        restored = deserialize_envelope(as_bytes)
        assert restored.header.sender_role == "oracle"

    def test_envelope_hlc_populated(self):
        hlc = HLC.create("node-1")
        payload = {"test": True}
        envelope = build_envelope("a1", "buyer", payload, hlc)
        assert "node-1" in envelope.header.hlc
