"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mesh_platform.models.base import init_db, async_session_factory
from mesh_platform.services.capability_seed import seed_capabilities
from mesh_platform.services.plan_seed import seed_plans


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session_factory() as db:
        await seed_capabilities(db)
        await seed_plans(db)
        await db.commit()
    yield


def create_app(*, skip_lifespan: bool = False) -> FastAPI:
    app = FastAPI(
        title="MESH Platform API",
        description="Enterprise SaaS control plane for MESH decentralized supply chain coordination",
        version="0.1.0",
        lifespan=None if skip_lifespan else lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from mesh_platform.routers.auth import router as auth_router
    from mesh_platform.routers.workspaces import router as workspaces_router
    from mesh_platform.routers.orders import router as orders_router
    from mesh_platform.routers.ledger import router as ledger_router
    from mesh_platform.routers.agents import router as agents_router
    from mesh_platform.routers.payments import router as payments_router
    from mesh_platform.routers.api_keys import router as api_keys_router
    from mesh_platform.routers.capabilities import router as capabilities_router
    from mesh_platform.routers.admin import router as admin_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(workspaces_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(ledger_router, prefix="/api/v1")
    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(api_keys_router, prefix="/api/v1")
    app.include_router(capabilities_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    from mesh_platform.gateway.ws_endpoint import router as gateway_router
    app.include_router(gateway_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
