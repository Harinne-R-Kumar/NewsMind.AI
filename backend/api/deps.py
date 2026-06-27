"""
NewsMind AI - Dependency Injection Providers
Why: Provides reusable dependencies for FastAPI request router pipelines.
How: Integrates OAuth2 security schemes and database session injections.
Trade-offs: Local session bindings are safe, but distributed systems
would require separate token verification mechanisms.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.connection import get_db
from backend.models.models import User
from backend.utils.security import verify_token

# Token endpoint mapping for Swagger interface authorization locks
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Decodes bearer token and resolves the caller from the User database.
    Raises 401 Unauthorized if verification fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Access token expired or invalid.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id_str = verify_token(token, "access")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    # Query user from DB
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency checking if user is fully verified.
    """
    # If email verification is pending, restrict certain proactive brief settings.
    # In initial prototyping, we allow unverified access but block production scheduler hooks.
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address must be verified before performing this action.",
        )
    return current_user
