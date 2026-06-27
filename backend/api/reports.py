"""
NewsMind AI - Reports API
Generate and manage newspapers.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.connection import get_db
from backend.models.models import User, GeneratedReport
from backend.schemas.schemas import GeneratedReportResponse, ReportDetailResponse
from backend.api.deps import get_current_user
from backend.utils.logging import setup_logger

logger = setup_logger("reports")
router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("", response_model=list[GeneratedReportResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's generated reports."""
    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.user_id == current_user.id)
        .order_by(GeneratedReport.generated_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific report with full content."""
    result = await db.execute(
        select(GeneratedReport).where(
            GeneratedReport.id == report_id,
            GeneratedReport.user_id == current_user.id
        )
    )
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
async def download_report_pdf(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download report PDF."""
    result = await db.execute(
        select(GeneratedReport).where(
            GeneratedReport.id == report_id,
            GeneratedReport.user_id == current_user.id
        )
    )
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=f"newspaper_{report_id}.pdf"
    )


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_newspaper(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger newspaper generation."""
    from backend.scheduler.tasks import manual_generation_task
    
    logger.info(f"Manual newspaper generation triggered by user {current_user.id}")
    
    try:
        result = await manual_generation_task(current_user.id)
        
        if result.get("success"):
            return {
                "message": "Newspaper generated successfully",
                "report_id": result.get("report_id"),
                "pdf_path": result.get("pdf_path")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate newspaper")
            )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
