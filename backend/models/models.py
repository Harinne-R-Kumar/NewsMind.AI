"""
NewsMind AI - Database Models
Clean, production-quality models for the Agentic AI application.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    preference = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    interests = relationship("Interest", back_populates="user", cascade="all, delete-orphan")
    preferred_sources = relationship("PreferredSource", back_populates="user", cascade="all, delete-orphan")
    excluded_topics = relationship("ExcludedTopic", back_populates="user", cascade="all, delete-orphan")
    delivery_schedules = relationship("DeliverySchedule", back_populates="user", cascade="all, delete-orphan")
    reading_histories = relationship("ReadingHistory", back_populates="user", cascade="all, delete-orphan")
    saved_articles = relationship("SavedArticle", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("ArticleFeedback", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("GeneratedReport", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    """User delivery and language preferences."""
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    preferred_language = Column(String, default="en")
    timezone = Column(String, default="ist")
    reading_style = Column(String, default="bullet_points")  # bullet_points, narrative, detailed
    delivery_paused = Column(Boolean, default=False)

    user = relationship("User", back_populates="preference")


class Interest(Base):
    """User interest topics."""
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String, nullable=False)

    user = relationship("User", back_populates="interests")


class PreferredSource(Base):
    """User preferred news sources."""
    __tablename__ = "preferred_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String, nullable=False)

    user = relationship("User", back_populates="preferred_sources")


class ExcludedTopic(Base):
    """Topics user wishes to avoid."""
    __tablename__ = "excluded_topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String, nullable=False)

    user = relationship("User", back_populates="excluded_topics")


class DeliverySchedule(Base):
    """Newspaper delivery schedule."""
    __tablename__ = "delivery_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    delivery_time = Column(String, default="08:00")  # HH:MM format
    frequency = Column(String, default="daily")  # daily, weekdays, weekends, weekly

    user = relationship("User", back_populates="delivery_schedules")


class ReadingHistory(Base):
    """Articles read by user."""
    __tablename__ = "reading_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_title = Column(String, nullable=False)
    article_url = Column(String, nullable=False)
    article_source = Column(String, nullable=True)
    section = Column(String, nullable=True)
    read_at = Column(DateTime, default=func.now())
    time_spent_seconds = Column(Integer, default=0)

    user = relationship("User", back_populates="reading_histories")


class SavedArticle(Base):
    """User bookmarked articles."""
    __tablename__ = "saved_articles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    section = Column(String, nullable=True)
    saved_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="saved_articles")


class ArticleFeedback(Base):
    """User feedback on articles."""
    __tablename__ = "article_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_title = Column(String, nullable=False)
    article_url = Column(String, nullable=False)
    feedback_type = Column(String, nullable=False)  # like, dislike, save, read_later, more_like_this, dont_recommend
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="feedbacks")


class GeneratedReport(Base):
    """Generated newspapers."""
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    generated_at = Column(DateTime, default=func.now())
    pdf_path = Column(String, nullable=True)
    html_content = Column(Text, nullable=False)
    overall_rating = Column(Integer, nullable=True)  # 1-5 stars
    overall_feedback = Column(Text, nullable=True)

    user = relationship("User", back_populates="reports")

