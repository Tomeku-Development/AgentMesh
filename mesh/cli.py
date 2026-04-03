"""MESH CLI — entry point for running agents and demos."""

from __future__ import annotations

import argparse
import logging
import sys

from mesh.core.config import MeshConfig
from mesh.core.identity import AgentIdentity
from mesh.core.ledger import Ledger
from mesh.core.reputation import ReputationEngine


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run_agent(args: argparse.Namespace) -> None:
    """Run a single MESH agent."""
    config = MeshConfig(
        broker_host=args.host,
        broker_port=args.port,
        broker_username=args.username,
        broker_password=args.password,
        agent_role=args.role,
        agent_id=args.agent_id or "auto",
        capabilities=args.capabilities or "",
        initial_balance=args.balance,
        log_level=args.log_level,
    )
    setup_logging(config.log_level)

    identity = AgentIdentity.generate()
    ledger = Ledger()
    reputation = ReputationEngine()

    agent_classes = {
        "buyer": "mesh.agents.buyer:BuyerAgent",
        "supplier": "mesh.agents.supplier:SupplierAgent",
        "logistics": "mesh.agents.logistics:LogisticsAgent",
        "inspector": "mesh.agents.inspector:InspectorAgent",
        "oracle": "mesh.agents.oracle:OracleAgent",
    }

    if args.role not in agent_classes:
        print(f"Unknown role: {args.role}. Choose from: {', '.join(agent_classes)}")
        sys.exit(1)

    module_path, class_name = agent_classes[args.role].split(":")
    import importlib
    module = importlib.import_module(module_path)
    agent_cls = getattr(module, class_name)

    agent = agent_cls(config, identity, ledger, reputation)
    agent.start()
    agent.run_forever()


def run_demo(args: argparse.Namespace) -> None:
    """Run the full demo scenario with all agents."""
    from mesh.scenarios.electronics import ElectronicsScenario
    import time
    import threading

    scenario = ElectronicsScenario()
    config_base = MeshConfig(
        broker_host=args.host,
        broker_port=args.port,
        broker_username=args.username,
        broker_password=args.password,
        log_level=args.log_level,
    )
    setup_logging(config_base.log_level)
    logger = logging.getLogger("mesh.demo")

    # Shared state
    ledger = Ledger()
    reputation = ReputationEngine()
    agents = []

    logger.info("=== MESH Demo: %s ===", scenario.name)
    logger.info("Duration: %ds", scenario.duration_seconds)

    # Create agents
    supplier_idx = 0
    for agent_def in scenario.agents:
        for i in range(agent_def.count):
            config = MeshConfig(
                broker_host=config_base.broker_host,
                broker_port=config_base.broker_port,
                broker_username=config_base.broker_username,
                broker_password=config_base.broker_password,
                agent_role=agent_def.role,
                capabilities=",".join(agent_def.capabilities),
                initial_balance=agent_def.initial_balance,
                log_level=config_base.log_level,
            )

            identity = AgentIdentity.generate()
            module_map = {
                "buyer": "mesh.agents.buyer:BuyerAgent",
                "supplier": "mesh.agents.supplier:SupplierAgent",
                "logistics": "mesh.agents.logistics:LogisticsAgent",
                "inspector": "mesh.agents.inspector:InspectorAgent",
                "oracle": "mesh.agents.oracle:OracleAgent",
            }

            import importlib
            mod_path, cls_name = module_map[agent_def.role].split(":")
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)

            agent = cls(config, identity, ledger, reputation)

            # Set up role-specific data
            if agent_def.role == "oracle":
                agent.set_base_prices(scenario.get_base_prices())
            elif agent_def.role == "supplier" and agent_def.inventory:
                agent.set_inventory(agent_def.inventory, agent_def.costs)

            agents.append(agent)

    # Start all agents
    for agent in agents:
        agent.start()
        time.sleep(0.5)

    logger.info("All %d agents started", len(agents))

    # Find the buyer
    buyer = None
    for a in agents:
        if a.role == "buyer":
            buyer = a
            break

    # Schedule orders
    start_time = time.time()
    for order_event in scenario.orders:
        def place_order(evt=order_event):
            delay = evt.at_second - (time.time() - start_time)
            if delay > 0:
                time.sleep(delay)
            if buyer:
                logger.info(">>> Placing order: %dx %s @ max %.2f", evt.quantity, evt.goods, evt.max_price_per_unit)
                buyer.create_order(
                    goods=evt.goods,
                    category=evt.category,
                    quantity=evt.quantity,
                    max_price_per_unit=evt.max_price_per_unit,
                    quality_threshold=evt.quality_threshold,
                )

        t = threading.Thread(target=place_order, daemon=True)
        t.start()

    # Run until scenario ends or interrupted
    try:
        remaining = scenario.duration_seconds - (time.time() - start_time)
        if remaining > 0:
            time.sleep(remaining)
    except KeyboardInterrupt:
        pass

    logger.info("=== Demo Complete ===")
    logger.info("Ledger: %d transactions, %.2f total transacted", ledger.transaction_count, ledger.total_transacted())
    logger.info("Balances: %s", {k[:8]: f"{v:.2f}" for k, v in ledger.all_balances().items()})

    for agent in agents:
        agent.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="MESH — Decentralized Supply Chain Coordination")
    parser.add_argument("--host", default="127.0.0.1", help="FoxMQ broker host")
    parser.add_argument("--port", type=int, default=1883, help="FoxMQ broker port")
    parser.add_argument("--username", default="", help="FoxMQ username")
    parser.add_argument("--password", default="", help="FoxMQ password")
    parser.add_argument("--log-level", default="INFO", help="Log level")

    subparsers = parser.add_subparsers(dest="command")

    # run-agent subcommand
    agent_parser = subparsers.add_parser("run-agent", help="Run a single agent")
    agent_parser.add_argument("role", choices=["buyer", "supplier", "logistics", "inspector", "oracle"])
    agent_parser.add_argument("--agent-id", default="", help="Agent ID (auto-generated if empty)")
    agent_parser.add_argument("--capabilities", default="", help="Comma-separated capabilities")
    agent_parser.add_argument("--balance", type=float, default=10000, help="Initial balance")

    # demo subcommand
    demo_parser = subparsers.add_parser("demo", help="Run full demo scenario")

    parsed = parser.parse_args()

    if parsed.command == "run-agent":
        run_agent(parsed)
    elif parsed.command == "demo":
        run_demo(parsed)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
