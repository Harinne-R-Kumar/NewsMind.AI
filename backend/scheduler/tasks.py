"""
NewsMind AI - Scheduler
APScheduler-based task scheduler for automated newspaper delivery.
"""

import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.connection import async_session
from backend.models.models import User, DeliverySchedule, UserPreference, Interest, PreferredSource, ExcludedTopic, GeneratedReport
from backend.graph.workflow import run_newspaper_workflow
from backend.utils.logging import setup_logger

logger = setup_logger("scheduler")

# Initialize scheduler
scheduler = AsyncIOScheduler()


async def get_users_for_delivery() -> list:
    """Get users scheduled for delivery at current time."""
    current_time = datetime.utcnow().strftime("%H:%M")
    current_day = datetime.utcnow().strftime("%A").lower()
    
    async with async_session() as db:
        # Find schedules matching current time
        result = await db.execute(
            select(DeliverySchedule).where(DeliverySchedule.delivery_time == current_time)
        )
        schedules = result.scalars().all()
        
        users_to_process = []
        
        for schedule in schedules:
            # Check frequency
            if schedule.frequency == "daily":
                pass
            elif schedule.frequency == "weekdays" and current_day in ["saturday", "sunday"]:
                continue
            elif schedule.frequency == "weekends" and current_day not in ["saturday", "sunday"]:
                continue
            elif schedule.frequency == "weekly" and current_day != "monday":
                continue
            
            # Get user with preferences
            user_result = await db.execute(
                select(User).where(User.id == schedule.user_id, User.is_verified == True)
            )
            user = user_result.scalars().first()
            
            if not user:
                continue
            
            # Check if delivery is paused
            pref_result = await db.execute(
                select(UserPreference).where(UserPreference.user_id == user.id)
            )
            preference = pref_result.scalars().first()
            
            if preference and preference.delivery_paused:
                logger.info(f"Delivery paused for user {user.id}")
                continue
            
            # Get interests
            interests_result = await db.execute(
                select(Interest).where(Interest.user_id == user.id)
            )
            interests = [i.topic for i in interests_result.scalars().all()]
            
            # Get preferred sources
            sources_result = await db.execute(
                select(PreferredSource).where(PreferredSource.user_id == user.id)
            )
            preferred_sources = [s.source_name for s in sources_result.scalars().all()]
            
            # Get excluded topics
            excluded_result = await db.execute(
                select(ExcludedTopic).where(ExcludedTopic.user_id == user.id)
            )
            excluded_topics = [t.topic for t in excluded_result.scalars().all()]
            
            users_to_process.append({
                "user": user,
                "schedule": schedule,
                "preferences": {
                    "interests": interests,
                    "preferred_sources": preferred_sources,
                    "excluded_topics": excluded_topics,
                    "reading_style": preference.reading_style if preference else "bullet_points",
                    "timezone": preference.timezone if preference else "ist",
                    "preferred_language": preference.preferred_language if preference else "en",
                    "delivery_paused": preference.delivery_paused if preference else False,
                }
            })
        
        return users_to_process


async def process_user_delivery(user_data: dict):
    """Process delivery for a single user."""
    user = user_data["user"]
    preferences = user_data["preferences"]
    
    logger.info(f"Processing delivery for user {user.id} ({user.email})")
    
    try:
        # Run workflow
        result = await run_newspaper_workflow(
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            preferences=preferences,
            is_verified=user.is_verified,
            manual_trigger=False,
        )

        # Save generated report
        
        
        logger.info(f"Delivery complete for user {user.id}")
        return {"success": True, "user_id": user.id}
        
    except Exception as e:
        logger.error(f"Delivery failed for user {user.id}: {e}")
        return {"success": False, "user_id": user.id, "error": str(e)}


async def scheduled_delivery_task():
    """Main scheduled task that runs every minute."""
    logger.info("Checking for scheduled deliveries...")
    
    users = await get_users_for_delivery()
    
    if users:
        logger.info(f"Processing {len(users)} users for delivery")
        
        # Process users concurrently
        tasks = [process_user_delivery(user_data) for user_data in users]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        logger.info(f"Delivery complete: {success_count}/{len(users)} successful")
    else:
        logger.debug("No users scheduled for current time")


async def manual_generation_task(user_id: int):
    """Manually trigger newspaper generation for a user."""
    async with async_session() as db:
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalars().first()
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Get preferences
        pref_result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        preference = pref_result.scalars().first()
        
        # Get interests
        interests_result = await db.execute(
            select(Interest).where(Interest.user_id == user.id)
        )
        interests = [i.topic for i in interests_result.scalars().all()]
        
        # Get preferred sources
        sources_result = await db.execute(
            select(PreferredSource).where(PreferredSource.user_id == user.id)
        )
        preferred_sources = [s.source_name for s in sources_result.scalars().all()]
        
        # Get excluded topics
        excluded_result = await db.execute(
            select(ExcludedTopic).where(ExcludedTopic.user_id == user.id)
        )
        excluded_topics = [t.topic for t in excluded_result.scalars().all()]
    
    # Run workflow
    result = await run_newspaper_workflow(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        preferences={
            "interests": interests,
            "preferred_sources": preferred_sources,
            "excluded_topics": excluded_topics,
            "reading_style": preference.reading_style if preference else "bullet_points",
            "timezone": preference.timezone if preference else "ist",
            "preferred_language": preference.preferred_language if preference else "en",
            "delivery_paused": preference.delivery_paused if preference else False,
        },
        is_verified=user.is_verified,
        manual_trigger=True,
    )
    
    return {
    "success": True,
    "report_id": result.get("report_id"),
    "pdf_path": result.get("pdf_path")
}


def start_scheduler():
    """Start the scheduler."""
    # Add job to check every minute
    scheduler.add_job(
        scheduled_delivery_task,
        trigger=CronTrigger(minute="*"),  # Every minute
        id="scheduled_delivery",
        name="Check and process scheduled deliveries",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


async def init_scheduler():
    """Initialize scheduler on app startup."""
    start_scheduler()
