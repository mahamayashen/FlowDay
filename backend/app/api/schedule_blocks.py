from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.schedule_block import (
    ScheduleBlockCreate,
    ScheduleBlockResponse,
    ScheduleBlockUpdate,
)
from app.services.schedule_block_service import (
    create_schedule_block,
    delete_schedule_block,
    get_schedule_block,
    list_schedule_blocks,
    update_schedule_block,
)

router = APIRouter(prefix="/schedule-blocks", tags=["schedule-blocks"])


@router.post(
    "", response_model=ScheduleBlockResponse, status_code=status.HTTP_201_CREATED
)
async def create_schedule_block_route(
    body: ScheduleBlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScheduleBlockResponse:
    """Create a new schedule block."""
    block = await create_schedule_block(db=db, user_id=current_user.id, data=body)
    return ScheduleBlockResponse.model_validate(block)


@router.get("", response_model=list[ScheduleBlockResponse])
async def list_schedule_blocks_route(
    date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleBlockResponse]:
    """List schedule blocks for a given date."""
    blocks = await list_schedule_blocks(db=db, user_id=current_user.id, query_date=date)
    return [ScheduleBlockResponse.model_validate(b) for b in blocks]


@router.get("/{block_id}", response_model=ScheduleBlockResponse)
async def get_schedule_block_route(
    block_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScheduleBlockResponse:
    """Get a single schedule block by ID."""
    block = await get_schedule_block(db=db, block_id=block_id, user_id=current_user.id)
    return ScheduleBlockResponse.model_validate(block)


@router.put("/{block_id}", response_model=ScheduleBlockResponse)
async def update_schedule_block_route(
    block_id: uuid.UUID,
    body: ScheduleBlockUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScheduleBlockResponse:
    """Update a schedule block (resize/move)."""
    block = await update_schedule_block(
        db=db, block_id=block_id, user_id=current_user.id, data=body
    )
    return ScheduleBlockResponse.model_validate(block)


@router.delete(
    "/{block_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def delete_schedule_block_route(
    block_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a schedule block."""
    await delete_schedule_block(db=db, block_id=block_id, user_id=current_user.id)
