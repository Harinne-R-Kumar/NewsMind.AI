"""
NewsMind AI - Database Connection Module
Why: Sets up async SQLite database connectivity using SQLAlchemy.
How: Configures an async engine and sessionmaker targeting the SQLite path defined in configurations.
Trade-offs: SQLite does not support multiple concurrent write transactions natively, but using
an async context pool minimizes thread-blocking of the FastAPI event loop during I/O.
"""

import sys
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.config import settings
from backend.utils.logging import setup_logger

logger = setup_logger("database")

# Create database engine
# SQLite requires 'check_same_thread=False' for multiple thread requests
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

try:
    engine = create_async_engine(
        DATABASE_URL,
        connect_args=connect_args,
        echo=False
    )
    async_session = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
except Exception as e:
    logger.critical(f"Failed to initialize database engine: {e}")
    sys.exit(1)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for obtaining async database sessions inside router contexts.
    Ensures rollback in case of uncaught request exceptions and closes the session.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables on application startup."""
    logger.info("Initializing database schemas...")
    try:
        async with engine.begin() as conn:
            # Import all models to register them on Base metadata
            from backend.models.models import (
                User, UserPreference, Interest, PreferredSource,
                ExcludedTopic, DeliverySchedule, ReadingHistory,
                SavedArticle, ArticleFeedback, GeneratedReport
            )
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database schemas: {e}", exc_info=True)
        raise
