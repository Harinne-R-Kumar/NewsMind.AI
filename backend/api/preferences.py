"""
NewsMind AI - Preferences API
Manage user interests, sources, and preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from backend.database.connection import get_db
from backend.models.models import (
    User, UserPreference, Interest, PreferredSource, ExcludedTopic
)
from backend.schemas.schemas import (
    UserPreferenceResponse, UserPreferenceUpdate,
    InterestCreate, InterestResponse,
    PreferredSourceCreate, ExcludedTopicCreate,
    OnboardingRequest
)
from backend.api.deps import get_current_user
from backend.utils.logging import setup_logger

logger = setup_logger("preferences")
router = APIRouter(prefix="/api/preferences", tags=["Preferences"])


@router.get("", response_model=UserPreferenceResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user preferences."""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preference = result.scalars().first()
    if not preference:
        # Create default preferences
        preference = UserPreference(user_id=current_user.id)
        db.add(preference)
        await db.flush()
    return preference


@router.put("", response_model=UserPreferenceResponse)
async def update_preferences(
    data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences."""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preference = result.scalars().first()
    if not preference:
        preference = UserPreference(user_id=current_user.id)
        db.add(preference)
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)
    await db.commit()
    await db.refresh(preference)
    
    logger.info(f"Updated preferences for user {current_user.id}")
    return preference


# === INTERESTS ===

@router.get("/interests", response_model=list[InterestResponse])
async def get_interests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user interests."""
    result = await db.execute(
        select(Interest).where(Interest.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/interests", response_model=InterestResponse, status_code=status.HTTP_201_CREATED)
async def add_interest(
    data: InterestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new interest."""
    # Check if exists
    result = await db.execute(
        select(Interest).where(
            Interest.user_id == current_user.id,
            Interest.topic == data.topic
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Interest already exists")
    
    interest = Interest(
    user_id=current_user.id,
    topic=data.topic
    )

    db.add(interest)

    await db.commit()
    await db.refresh(interest)

    return interest


@router.delete("/interests/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_interest(
    interest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove an interest."""
    result = await db.execute(
        select(Interest).where(
            Interest.id == interest_id,
            Interest.user_id == current_user.id
        )
    )
    interest = result.scalars().first()
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")
    
    await db.delete(interest)
    await db.commit()
    logger.info(f"Removed interest {interest_id} for user {current_user.id}")


# === PREFERRED SOURCES ===

@router.get("/sources", response_model=list[InterestResponse])
async def get_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferred sources."""
    result = await db.execute(
        select(PreferredSource).where(PreferredSource.user_id == current_user.id)
    )
    sources = result.scalars().all()
    return [{"id": s.id, "topic": s.source_name} for s in sources]


@router.post("/sources", response_model=InterestResponse, status_code=status.HTTP_201_CREATED)
async def add_source(
    data: PreferredSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a preferred source."""
    result = await db.execute(
        select(PreferredSource).where(
            PreferredSource.user_id == current_user.id,
            PreferredSource.source_name == data.source_name
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Source already added")
    
    source = PreferredSource(user_id=current_user.id, source_name=data.source_name)
    db.add(source)
    await db.commit()
    await db.refresh(source)
    logger.info(f"Added source '{data.source_name}' for user {current_user.id}")
    return {"id": source.id, "topic": source.source_name}


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a preferred source."""
    result = await db.execute(
        select(PreferredSource).where(
            PreferredSource.id == source_id,
            PreferredSource.user_id == current_user.id
        )
    )
    source = result.scalars().first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    await db.delete(source)
    await db.commit()
    logger.info(f"Removed source {source_id} for user {current_user.id}")


# === EXCLUDED TOPICS ===

@router.get("/excluded", response_model=list[InterestResponse])
async def get_excluded_topics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user excluded topics."""
    result = await db.execute(
        select(ExcludedTopic).where(ExcludedTopic.user_id == current_user.id)
    )
    topics = result.scalars().all()
    return [{"id": t.id, "topic": t.topic} for t in topics]


@router.post("/excluded", response_model=InterestResponse, status_code=status.HTTP_201_CREATED)
async def add_excluded_topic(
    data: ExcludedTopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a topic to exclude."""
    result = await db.execute(
        select(ExcludedTopic).where(
            ExcludedTopic.user_id == current_user.id,
            ExcludedTopic.topic == data.topic
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Topic already excluded")
    
    topic = ExcludedTopic(user_id=current_user.id, topic=data.topic)
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    logger.info(f"Added excluded topic '{data.topic}' for user {current_user.id}")
    return {"id": topic.id, "topic": topic.topic}


@router.delete("/excluded/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_excluded_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove an excluded topic."""
    result = await db.execute(
        select(ExcludedTopic).where(
            ExcludedTopic.id == topic_id,
            ExcludedTopic.user_id == current_user.id
        )
    )
    topic = result.scalars().first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    await db.delete(topic)
    await db.commit()
    logger.info(f"Removed excluded topic {topic_id} for user {current_user.id}")


# === ONBOARDING ===

@router.post("/onboarding", status_code=status.HTTP_201_CREATED)
async def complete_onboarding(
    data: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete user onboarding with all preferences."""
    # Update user name if provided
    if data.name:
        current_user.name = data.name
    
    # Create/update preferences
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preference = result.scalars().first()
    if not preference:
        preference = UserPreference(user_id=current_user.id)
        db.add(preference)
    
    preference.preferred_language = data.preferred_language
    preference.timezone = data.timezone
    preference.reading_style = data.reading_style
    
    # Add interests
    all_interests = data.interests + data.custom_interests
    for topic in all_interests:
        result = await db.execute(
            select(Interest).where(
                Interest.user_id == current_user.id,
                Interest.topic == topic
            )
        )
        if not result.scalars().first():
            db.add(Interest(user_id=current_user.id, topic=topic))
    
    # Add preferred sources
    for source in data.preferred_sources:
        result = await db.execute(
            select(PreferredSource).where(
                PreferredSource.user_id == current_user.id,
                PreferredSource.source_name == source
            )
        )
        if not result.scalars().first():
            db.add(PreferredSource(user_id=current_user.id, source_name=source))
    
    # Add excluded topics
    for topic in data.excluded_topics:
        result = await db.execute(
            select(ExcludedTopic).where(
                ExcludedTopic.user_id == current_user.id,
                ExcludedTopic.topic == topic
            )
        )
        if not result.scalars().first():
            db.add(ExcludedTopic(user_id=current_user.id, topic=topic))
    
    # Create delivery schedule
    from backend.models.models import DeliverySchedule
    result = await db.execute(
        select(DeliverySchedule).where(DeliverySchedule.user_id == current_user.id)
    )
    schedule = result.scalars().first()
    if not schedule:
        schedule = DeliverySchedule(user_id=current_user.id)
        db.add(schedule)
    schedule.delivery_time = data.delivery_time
    schedule.frequency = data.delivery_frequency
    await db.commit()
    logger.info(f"Completed onboarding for user {current_user.id}")
    return {"message": "Onboarding completed successfully"}
