"""
NewsMind AI - Pydantic Schemas
Request/response validation models.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# === AUTH ===

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


# === PREFERENCES ===

class InterestCreate(BaseModel):
    topic: str


class PreferredSourceCreate(BaseModel):
    source_name: str


class ExcludedTopicCreate(BaseModel):
    topic: str


class UserPreferenceUpdate(BaseModel):
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    reading_style: Optional[str] = None
    delivery_paused: Optional[bool] = None


class OnboardingRequest(BaseModel):
    name: str
    email: EmailStr
    preferred_language: str = "en"
    timezone: str = "ist"
    interests: List[str]
    custom_interests: List[str] = []
    excluded_topics: List[str] = []
    preferred_sources: List[str]
    reading_style: str = "bullet_points"
    delivery_time: str = "08:00"
    delivery_frequency: str = "daily"


class UserPreferenceResponse(BaseModel):
    preferred_language: str
    timezone: str
    reading_style: str
    delivery_paused: bool

    class Config:
        from_attributes = True


class InterestResponse(BaseModel):
    id: int
    topic: str

    class Config:
        from_attributes = True


# === SCHEDULE ===

class ScheduleCreate(BaseModel):
    delivery_time: str = "08:00"
    frequency: str = "daily"


class ScheduleResponse(BaseModel):
    id: int
    delivery_time: str
    frequency: str

    class Config:
        from_attributes = True


# === FEEDBACK ===

class ArticleFeedbackCreate(BaseModel):
    article_title: str
    article_url: str
    feedback_type: str  # like, dislike, save, read_later, more_like_this, dont_recommend


class ReportFeedbackCreate(BaseModel):
    overall_rating: Optional[int] = None
    overall_feedback: Optional[str] = None
    improvement_request: Optional[str] = None


# === REPORTS ===

class GeneratedReportResponse(BaseModel):
    id: int
    generated_at: datetime
    pdf_path: Optional[str]
    overall_rating: Optional[int]

    class Config:
        from_attributes = True


class ReportDetailResponse(BaseModel):
    id: int
    generated_at: datetime
    html_content: str
    pdf_path: Optional[str]
    overall_rating: Optional[int]
    overall_feedback: Optional[str]

    class Config:
        from_attributes = True
