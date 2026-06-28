from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from backend.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, nullable=False)

    report_id = Column(Integer, nullable=False)

    rating = Column(Integer, nullable=False)

    comment = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())