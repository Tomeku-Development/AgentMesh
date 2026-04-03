"""Shared test fixtures for MESH tests."""

import sys
import os
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mesh.core.config import MeshConfig
from mesh.core.identity import AgentIdentity
from mesh.core.ledger import Ledger
from mesh.core.reputation import ReputationEngine
from mesh.core.registry import PeerRegistry


@pytest.fixture
def config():
    return MeshConfig(broker_host="127.0.0.1", broker_port=1883)


@pytest.fixture
def identity():
    return AgentIdentity.generate()


@pytest.fixture
def ledger():
    ld = Ledger()
    ld.init_balance("buyer_001", 10000)
    ld.init_balance("supplier_001", 5000)
    ld.init_balance("supplier_002", 5000)
    ld.init_balance("logistics_001", 2000)
    ld.init_balance("inspector_001", 2000)
    return ld


@pytest.fixture
def reputation():
    engine = ReputationEngine()
    engine.register("buyer_001", "buyer", ["electronics"])
    engine.register("supplier_001", "supplier", ["electronics", "displays"])
    engine.register("supplier_002", "supplier", ["electronics", "batteries"])
    engine.register("logistics_001", "logistics", ["shipping"])
    engine.register("inspector_001", "inspector", ["quality_control"])
    return engine


@pytest.fixture
def registry():
    return PeerRegistry(suspect_threshold=15.0, dead_threshold=30.0)
