#!/usr/bin/env python3
"""Benchmark MESH components — measures throughput and latency of core operations.

Usage:
    python scripts/benchmark.py              # Run all benchmarks
    python scripts/benchmark.py --iterations 10000
"""

import argparse
import json
import os
import sys
import time
from statistics import mean, stdev

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mesh.core.clock import HLC
from mesh.core.crypto import canonical_json, sign_message, verify_signature
from mesh.core.identity import AgentIdentity
from mesh.core.ledger import Ledger
from mesh.core.messages import (
    DiscoveryAnnounce,
    Heartbeat,
    MessageEnvelope,
    PurchaseOrderRequest,
    SupplierBid,
)
from mesh.core.protocol import build_envelope, serialize_envelope, deserialize_envelope, verify_envelope
from mesh.core.registry import PeerRegistry
from mesh.core.reputation import ReputationEngine
from mesh.negotiation.engine import NegotiationEngine


def benchmark(name: str, fn, iterations: int) -> dict:
    """Run a benchmark and return timing stats."""
    # Warmup
    for _ in range(min(100, iterations // 10)):
        fn()

    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        fn()
        elapsed = time.perf_counter_ns() - start
        times.append(elapsed / 1_000_000)  # Convert to ms

    avg = mean(times)
    std = stdev(times) if len(times) > 1 else 0
    ops_per_sec = 1000 / avg if avg > 0 else float("inf")

    result = {
        "name": name,
        "iterations": iterations,
        "avg_ms": round(avg, 4),
        "std_ms": round(std, 4),
        "min_ms": round(min(times), 4),
        "max_ms": round(max(times), 4),
        "ops_per_sec": round(ops_per_sec, 0),
    }
    return result


def run_benchmarks(iterations: int) -> list[dict]:
    results = []

    # --- Identity ---
    results.append(benchmark(
        "Identity.generate()",
        lambda: AgentIdentity.generate(),
        iterations,
    ))

    identity = AgentIdentity.generate()
    msg = b"benchmark message payload"
    results.append(benchmark(
        "Identity.sign()",
        lambda: identity.sign(msg),
        iterations,
    ))

    sig = identity.sign(msg)
    results.append(benchmark(
        "Identity.verify()",
        lambda: identity.verify(msg, sig),
        iterations,
    ))

    # --- Crypto ---
    data = {"order_id": "test", "price": 99.5, "quantity": 50, "agent": "abc123"}
    results.append(benchmark(
        "canonical_json()",
        lambda: canonical_json(data),
        iterations,
    ))

    results.append(benchmark(
        "HMAC sign_message()",
        lambda: sign_message(data),
        iterations,
    ))

    hmac_sig = sign_message(data)
    results.append(benchmark(
        "HMAC verify_signature()",
        lambda: verify_signature(data, hmac_sig),
        iterations,
    ))

    # --- HLC ---
    hlc = HLC.create("bench_node")
    results.append(benchmark(
        "HLC.tick()",
        lambda: hlc.tick(),
        iterations,
    ))

    ts = hlc.tick()
    results.append(benchmark(
        "HLC.receive()",
        lambda: hlc.receive(ts),
        iterations,
    ))

    # --- Protocol ---
    announce = DiscoveryAnnounce(
        agent_id="bench_agent", role="supplier",
        capabilities=["electronics"], goods_categories=["electronics"],
        public_key_hex="deadbeef", status="online",
    )
    results.append(benchmark(
        "build_envelope()",
        lambda: build_envelope("bench_agent", "supplier", announce, hlc),
        iterations,
    ))

    envelope = build_envelope("bench_agent", "supplier", announce, hlc)
    results.append(benchmark(
        "verify_envelope()",
        lambda: verify_envelope(envelope),
        iterations,
    ))

    results.append(benchmark(
        "serialize_envelope()",
        lambda: serialize_envelope(envelope),
        iterations,
    ))

    payload_bytes = serialize_envelope(envelope)
    results.append(benchmark(
        "deserialize_envelope()",
        lambda: deserialize_envelope(payload_bytes),
        iterations,
    ))

    # --- Registry ---
    registry = PeerRegistry()
    for i in range(20):
        registry.update_from_announce(
            agent_id=f"agent_{i:03d}", role="supplier",
            capabilities=["electronics"], goods_categories=["electronics"],
            public_key_hex="", status="online",
        )
    results.append(benchmark(
        "Registry.check_liveness() (20 peers)",
        lambda: registry.check_liveness(5.0),
        iterations,
    ))

    # --- Ledger ---
    counter = [0]
    def ledger_transfer():
        ld = Ledger()
        ld.init_balance("a", 10000)
        ld.init_balance("b", 10000)
        ld.transfer("a", "b", 1.0, "payment")
    results.append(benchmark(
        "Ledger transfer cycle",
        ledger_transfer,
        iterations,
    ))

    # --- Reputation ---
    rep = ReputationEngine()
    rep.register("s1", "supplier", ["electronics"])
    results.append(benchmark(
        "Reputation.record_success()",
        lambda: rep.record_success("s1", "electronics", quality_score=0.95),
        iterations,
    ))

    results.append(benchmark(
        "Reputation.score_bid()",
        lambda: rep.score_bid(price=100, max_price=120, reputation=0.7, estimated_time=10, deadline=60, confidence=0.5),
        iterations,
    ))

    # --- Negotiation ---
    neg_counter = [0]
    def negotiation_cycle():
        eng = NegotiationEngine()
        oid = f"order_{neg_counter[0]}"
        neg_counter[0] += 1
        eng.create_session(oid, "buyer", 120, 100, 0.85, 30, 30)
        bid = SupplierBid(order_id=oid, supplier_id="s1", price_per_unit=105, available_quantity=50, estimated_fulfillment_seconds=10)
        session = eng.get_session(oid)
        session.add_bid(bid)
        eng.evaluate_bids(oid)
        eng.accept_bid(oid, bid)
    results.append(benchmark(
        "Full negotiation cycle",
        negotiation_cycle,
        iterations,
    ))

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark MESH components")
    parser.add_argument("--iterations", type=int, default=1000, help="Iterations per benchmark")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    print(f"MESH Benchmark — {args.iterations} iterations per test")
    print("=" * 75)

    results = run_benchmarks(args.iterations)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"{'Benchmark':<40} {'Avg (ms)':>10} {'Std':>10} {'Ops/sec':>12}")
        print("-" * 75)
        for r in results:
            print(f"{r['name']:<40} {r['avg_ms']:>10.4f} {r['std_ms']:>10.4f} {r['ops_per_sec']:>12,.0f}")

    print("=" * 75)
    print("Done.")


if __name__ == "__main__":
    main()
