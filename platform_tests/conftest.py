"""Shared test fixtures for platform tests using async SQLite."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from mesh_platform.models.base import Base
from mesh_platform.models.user import User, APIKey  # noqa: F401
from mesh_platform.models.workspace import Workspace, WorkspaceMembership  # noqa: F401
from mesh_platform.models.order import Order, OrderEvent  # noqa: F401
from mesh_platform.models.ledger import LedgerEntry, EscrowRecord  # noqa: F401
from mesh_platform.models.reputation import ReputationEvent, ReputationSnapshot  # noqa: F401
from mesh_platform.models.agent import AgentDefinition, AgentStatusLog  # noqa: F401
from mesh_platform.models.payment import PaymentIntent, PaymentWebhookEvent, Settlement  # noqa: F401
from mesh_platform.models.scenario import Scenario  # noqa: F401
from mesh_platform.models.marketplace import AgentTemplate  # noqa: F401
from mesh_platform.models.webhook import WebhookRegistration, WebhookDelivery  # noqa: F401
from mesh_platform.models.sla import SLARule, SLAAlert  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with overridden DB dependency."""
    from mesh_platform.app import create_app
    from mesh_platform.dependencies import get_db

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app(skip_lifespan=True)
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_user(
    client: AsyncClient,
    email: str = "test@mesh.io",
    password: str = "secret123",
    display_name: str = "Test User",
) -> dict:
    """Helper: register a user and return tokens."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
