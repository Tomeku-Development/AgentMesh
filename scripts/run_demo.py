#!/usr/bin/env python3
"""Run the MESH demo scenario locally (without Docker).

This script runs all agents in-process with a shared ledger and reputation engine.
Requires a running FoxMQ broker on localhost:1883.

Usage:
    python scripts/run_demo.py                           # Default settings
    python scripts/run_demo.py --host 127.0.0.1 --port 1883
    python scripts/run_demo.py --duration 120 --log-level DEBUG
"""

import argparse
import logging
import os
import sys
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mesh.core.config import MeshConfig
from mesh.core.identity import AgentIdentity
from mesh.core.ledger import Ledger
from mesh.core.reputation import ReputationEngine
from mesh.scenarios.electronics import ElectronicsScenario


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="Run MESH demo scenario")
    parser.add_argument("--host", default="127.0.0.1", help="FoxMQ broker host")
    parser.add_argument("--port", type=int, default=1883, help="FoxMQ broker port")
    parser.add_argument("--username", default="", help="FoxMQ username")
    parser.add_argument("--password", default="", help="FoxMQ password")
    parser.add_argument("--duration", type=int, default=0, help="Override scenario duration (seconds)")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    args = parser.parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger("mesh.demo")

    scenario = ElectronicsScenario()
    duration = args.duration or scenario.duration_seconds

    # Shared state (all agents in same process)
    ledger = Ledger()
    reputation = ReputationEngine()
    agents = []

    logger.info("=" * 60)
    logger.info("MESH Demo: %s", scenario.name)
    logger.info("Description: %s", scenario.description)
    logger.info("Duration: %ds | Agents: %d | Orders: %d",
                duration, sum(a.count for a in scenario.agents), len(scenario.orders))
    logger.info("=" * 60)

    # Import agent classes
    import importlib
    module_map = {
        "buyer": "mesh.agents.buyer:BuyerAgent",
        "supplier": "mesh.agents.supplier:SupplierAgent",
        "logistics": "mesh.agents.logistics:LogisticsAgent",
        "inspector": "mesh.agents.inspector:InspectorAgent",
        "oracle": "mesh.agents.oracle:OracleAgent",
    }

    # Create agents
    for agent_def in scenario.agents:
        for i in range(agent_def.count):
            config = MeshConfig(
                broker_host=args.host,
                broker_port=args.port,
                broker_username=args.username,
                broker_password=args.password,
                agent_role=agent_def.role,
                capabilities=",".join(agent_def.capabilities),
                initial_balance=agent_def.initial_balance,
                log_level=args.log_level,
            )
            identity = AgentIdentity.generate()
            mod_path, cls_name = module_map[agent_def.role].split(":")
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
            agent = cls(config, identity, ledger, reputation)

            if agent_def.role == "oracle":
                agent.set_base_prices(scenario.get_base_prices())
            elif agent_def.role == "supplier" and agent_def.inventory:
                agent.set_inventory(agent_def.inventory, agent_def.costs)

            agents.append(agent)

    # Start all agents
    logger.info("Starting %d agents...", len(agents))
    for agent in agents:
        try:
            agent.start()
            time.sleep(0.3)
        except Exception as e:
            logger.error("Failed to start agent %s: %s", agent.agent_id, e)
            logger.error("Is FoxMQ running on %s:%d?", args.host, args.port)
            for a in agents:
                try:
                    a.stop()
                except Exception:
                    pass
            sys.exit(1)

    logger.info("All agents started successfully")

    # Find buyer for placing orders
    buyer = next((a for a in agents if a.role == "buyer"), None)

    # Schedule orders
    start_time = time.time()
    for order_event in scenario.orders:
        def place_order(evt=order_event):
            delay = evt.at_second - (time.time() - start_time)
            if delay > 0:
                time.sleep(delay)
            if buyer:
                logger.info(">>> ORDER: %dx %s @ max $%.2f",
                            evt.quantity, evt.goods, evt.max_price_per_unit)
                buyer.create_order(
                    goods=evt.goods,
                    category=evt.category,
                    quantity=evt.quantity,
                    max_price_per_unit=evt.max_price_per_unit,
                    quality_threshold=evt.quality_threshold,
                )
        t = threading.Thread(target=place_order, daemon=True)
        t.start()

    # Run
    try:
        remaining = duration - (time.time() - start_time)
        if remaining > 0:
            time.sleep(remaining)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    # Print summary
    logger.info("=" * 60)
    logger.info("DEMO COMPLETE")
    logger.info("Ledger: %d transactions, $%.2f total transacted",
                ledger.transaction_count, ledger.total_transacted())
    logger.info("Balances:")
    for agent_id, balance in sorted(ledger.all_balances().items()):
        logger.info("  %s: $%.2f", agent_id[:16], balance)
    logger.info("=" * 60)

    # Shutdown
    for agent in agents:
        try:
            agent.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
