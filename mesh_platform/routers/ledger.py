"""Ledger read endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, case, literal_column

from mesh_platform.dependencies import DBSession, get_workspace
from mesh_platform.models.ledger import LedgerEntry
from mesh_platform.models.workspace import Workspace
from mesh_platform.schemas.ledger import BalanceResponse, BalancesResponse, LedgerEntryResponse, LedgerListResponse

router = APIRouter(tags=["ledger"])


@router.get(
    "/workspaces/{workspace_id}/ledger/transactions",
    response_model=LedgerListResponse,
)
async def list_transactions(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: DBSession,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    q = (
        select(LedgerEntry)
        .where(LedgerEntry.workspace_id == workspace.id)
        .order_by(LedgerEntry.recorded_at.desc())
        .limit(limit)
        .offset(offset)
    )
    count_q = select(func.count()).select_from(LedgerEntry).where(
        LedgerEntry.workspace_id == workspace.id
    )
    result = await db.execute(q)
    total_result = await db.execute(count_q)
    return LedgerListResponse(
        entries=list(result.scalars().all()),
        total=total_result.scalar_one(),
    )
