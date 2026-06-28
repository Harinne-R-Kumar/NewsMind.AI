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

from fastapi.responses import HTMLResponse, RedirectResponse
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
    # Use the rating submitted in this request if present,
    # otherwise use the rating that was already stored by
    # the quick feedback endpoint.
    rating = (
        data.overall_rating
        if data.overall_rating is not None
        else report.overall_rating
    )

    if (
        rating is not None
        and rating <= 3
        and (
            data.improvement_request is None
            or data.improvement_request.strip() == ""
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Please tell us what should be improved."
        )
    if data.overall_rating is not None:
        report.overall_rating = data.overall_rating
    # Save fields first
    if data.overall_feedback is not None:
        report.overall_feedback = data.overall_feedback

    if data.improvement_request is not None:
        report.improvement_request = data.improvement_request
    await db.commit()

    # Analyze feedback
    if (
        data.overall_feedback is not None
        or data.improvement_request is not None
    ):
        try:
            from backend.agents.learning import LearningAgent
            from backend.agents.memory import MemoryAgent

            learning = LearningAgent()

            feedback_text = ""

            if report.overall_feedback:
                feedback_text += report.overall_feedback

            if report.improvement_request:
                feedback_text += (
                    "\nImprovement Request:\n"
                    + report.improvement_request
                )

            learning_result = await learning.analyze_feedback(
                rating=rating,
                comment=feedback_text
            )

            memory = MemoryAgent()

            await memory.store_learning_signal(
                current_user.id,
                learning_result
            )

            logger.info(f"Learning Result: {learning_result}")

        except Exception as e:
            logger.error(e)
    await db.commit()
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

@router.get("/report/{report_id}/{rating}")
async def quick_feedback(
    report_id: int,
    rating: int,
    db: AsyncSession = Depends(get_db),
):
    """
    One-click feedback from email.
    """

    result = await db.execute(
        select(GeneratedReport).where(
            GeneratedReport.id == report_id
        )
    )

    report = result.scalars().first()

    if not report:
        return HTMLResponse(
            "<h2>Report not found.</h2>",
            status_code=404
        )

    report.overall_rating = rating

    await db.commit()

    if rating <= 3:

        return RedirectResponse(
            url=f"http://localhost:5173/report-feedback/{report_id}",
            status_code=302
        )

    return HTMLResponse("""
    <html>
    <body style="font-family:Arial;text-align:center;padding-top:100px;">
    <h1>🎉 Thank you!</h1>
    <p>Your feedback has been recorded.</p>
    </body>
    </html>
    """)