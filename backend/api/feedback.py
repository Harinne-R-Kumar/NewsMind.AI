"""
NewsMind AI - Feedback API
Handle user feedback on articles and reports.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.connection import get_db
from backend.models.models import User, ArticleFeedback, GeneratedReport
from backend.schemas.schemas import ArticleFeedbackCreate, ReportFeedbackCreate
from backend.api.deps import get_current_user
from backend.utils.logging import setup_logger

logger = setup_logger("feedback")
router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("/article", status_code=status.HTTP_201_CREATED)
async def submit_article_feedback(
    data: ArticleFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback on an article."""
    valid_types = ["like", "dislike", "save", "read_later", "more_like_this", "dont_recommend"]
    if data.feedback_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid feedback type. Must be one of: {valid_types}")
    
    feedback = ArticleFeedback(
        user_id=current_user.id,
        article_title=data.article_title,
        article_url=data.article_url,
        feedback_type=data.feedback_type
    )
    db.add(feedback)
    await db.flush()

    try:
        from backend.agents.memory import MemoryAgent
        memory = MemoryAgent()
        await memory.store_feedback(current_user.id, data.article_title, data.feedback_type)
    except Exception as e:
        logger.warning(f"ChromaDB feedback sync failed: {e}")

    logger.info(f"Article feedback '{data.feedback_type}' from user {current_user.id}")
    return {"message": "Feedback recorded", "feedback_type": data.feedback_type}


@router.post("/report/{report_id}", status_code=status.HTTP_200_OK)
async def submit_report_feedback(
    report_id: int,
    data: ReportFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit overall feedback on a generated report."""
    result = await db.execute(
        select(GeneratedReport).where(
            GeneratedReport.id == report_id,
            GeneratedReport.user_id == current_user.id
        )
    )
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if data.overall_rating is not None:
        report.overall_rating = data.overall_rating
    if data.overall_feedback is not None:
        report.overall_feedback = data.overall_feedback
    
    logger.info(f"Report feedback for report {report_id} from user {current_user.id}")
    return {"message": "Report feedback recorded"}


@router.get("/article")
async def get_article_feedback(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's article feedback history."""
    result = await db.execute(
        select(ArticleFeedback).where(ArticleFeedback.user_id == current_user.id)
        .order_by(ArticleFeedback.created_at.desc())
        .limit(50)
    )
    feedbacks = result.scalars().all()
    return [
        {
            "id": f.id,
            "article_title": f.article_title,
            "article_url": f.article_url,
            "feedback_type": f.feedback_type,
            "created_at": f.created_at
        }
        for f in feedbacks
    ]
