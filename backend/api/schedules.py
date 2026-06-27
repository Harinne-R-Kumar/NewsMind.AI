"""
NewsMind AI - Schedule API
Manage delivery schedules.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.connection import get_db
from backend.models.models import User, DeliverySchedule
from backend.schemas.schemas import ScheduleCreate, ScheduleResponse
from backend.api.deps import get_current_user
from backend.utils.logging import setup_logger

logger = setup_logger("schedules")
router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


@router.get("", response_model=list[ScheduleResponse])
async def get_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user delivery schedules."""
    result = await db.execute(
        select(DeliverySchedule).where(DeliverySchedule.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a delivery schedule."""
    schedule = DeliverySchedule(
        user_id=current_user.id,
        delivery_time=data.delivery_time,
        frequency=data.frequency
    )
    db.add(schedule)
    await db.flush()
    logger.info(f"Created schedule for user {current_user.id}")
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a delivery schedule."""
    result = await db.execute(
        select(DeliverySchedule).where(
            DeliverySchedule.id == schedule_id,
            DeliverySchedule.user_id == current_user.id
        )
    )
    schedule = result.scalars().first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.delivery_time = data.delivery_time
    schedule.frequency = data.frequency
    logger.info(f"Updated schedule {schedule_id} for user {current_user.id}")
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a delivery schedule."""
    result = await db.execute(
        select(DeliverySchedule).where(
            DeliverySchedule.id == schedule_id,
            DeliverySchedule.user_id == current_user.id
        )
    )
    schedule = result.scalars().first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    await db.delete(schedule)
    logger.info(f"Deleted schedule {schedule_id} for user {current_user.id}")
