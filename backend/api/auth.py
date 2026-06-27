"""
NewsMind AI - Authentication Router
Why: Exposes endpoints for managing user sessions and registration.
How: FastAPI Router handling registration, login, token refresh, and password recovery.
Trade-offs: Using memory refresh tokens is common, but DB-persisted refresh token sessions
would be required in production to support session revocation.
"""

from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.connection import get_db
from backend.models.models import User, UserPreference
from backend.schemas.schemas import UserCreate, UserLogin, UserResponse, Token, TokenRefresh
from backend.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from backend.config import settings
from backend.api.deps import get_current_user
from backend.utils.logging import setup_logger
from backend.utils.email import send_verification_email

logger = setup_logger("auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user, hashes their credentials, and setups default empty preferences.
    """
    logger.info(f"Attempting to register user with email: {user_in.email}")

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        logger.warning(f"Registration failed: User with email {user_in.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Generate verification token
    verification_token = str(uuid.uuid4())

    hashed_pwd = get_password_hash(user_in.password)

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hashed_pwd,
        is_verified=False,
        verification_token=verification_token,
    )

    db.add(new_user)

    await db.flush()      # <-- gets user.id

    default_preference = UserPreference(
        user_id=new_user.id,
        preferred_language="en",
        timezone="IST",
        reading_style="bullet_points",
        delivery_paused=False,
    )

    db.add(default_preference)

    await db.commit()

    await db.refresh(new_user)

    verification_link = (
        f"http://localhost:5173/verify-email?"
        f"token={verification_token}"
    )

    await send_verification_email(
        new_user.email,
        verification_link,
    )

    logger.info(
        f"Verification email sent to {new_user.email}"
    )

    return new_user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies user credentials and issues signed access/refresh JWT tokens.
    Supports both JSON request body and standard OAuth2 Form payloads (for Swagger locks).
    """
    content_type = request.headers.get("content-type", "")
    email = None
    password = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            email = body.get("email")
            password = body.get("password")
        except Exception:
            pass
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        try:
            form = await request.form()
            email = form.get("username")
            password = form.get("password")
        except Exception:
            pass

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request. Provide email and password credentials.",
        )

    logger.info(f"Authentication attempt for email: {email}")

    # Query user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed authentication attempt for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate Tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    logger.info(f"User {email} successfully authenticated")
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh(payload: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """
    Accepts a long-lived refresh token and issues a new access token.
    """
    user_id_str = verify_token(payload.refresh_token, "refresh")
    if not user_id_str:
        logger.warning("Token refresh attempt failed: Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please login again.",
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload.",
        )

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        logger.warning(f"Refresh failed: User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
        )

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    logger.info(f"Tokens refreshed successfully for user ID: {user.id}")
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/verify-email")
async def verify_email(token: str = Query(..., description="The unique verification token sent to email"), db: AsyncSession = Depends(get_db)):
    """
    Validates the account activation token.
    Sets is_verified to true upon match.
    """
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation failed: Invalid or expired token link.",
        )

    user.is_verified = True
    user.verification_token = None  # Clear token after verify

    await db.commit()

    await db.refresh(user)

    return {

        "message":"Email verified successfully."

}
    logger.info(f"User {user.email} verified their email successfully")
    return {"message": "Email address verified successfully. Welcome to NewsMind AI!"}

@router.post("/resend-verification")
async def resend_verification_email(

    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),

):

    if current_user.is_verified:

        return {
            "message": "Email already verified."
        }

    current_user.verification_token = str(uuid.uuid4())

    await db.commit()

    await db.refresh(current_user)

    verification_link = (
        f"http://localhost:5173/verify-email?"
        f"token={current_user.verification_token}"
    )

    await send_verification_email(

        current_user.email,

        verification_link

    )

    return {

        "message": "Verification email sent."

    }

@router.post("/forgot-password")
async def forgot_password(email: str = Query(..., description="User account email address"), db: AsyncSession = Depends(get_db)):
    """
    Simulates forgot password link generation.
    In future phases, this will generate a reset token and trigger email delivery.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        # Avoid user enumeration attacks: return success anyway but don't perform action
        logger.info(f"Forgot password requested for non-existing email: {email}")
        return {"message": "If the account exists, a password reset link has been dispatched."}

    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    logger.info(f"Reset password token generated for {email}: {reset_token}")

    # Mock dispatch (later integrated into email agent)
    return {
        "message": "If the account exists, a password reset link has been dispatched.",
        "debug_token": reset_token if settings.DEBUG else None,  # Expose token in debug mode for test assertions
    }


@router.post("/reset-password")
async def reset_password(token: str = Query(..., description="Password reset token"), new_password: str = Query(..., description="New password value"), db: AsyncSession = Depends(get_db)):
    """
    Resets password of a user given a valid reset token.
    """
    result = await db.execute(select(User).where(User.reset_token == token))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset password failed: Invalid or expired token.",
        )

    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None  # Clear reset token
    logger.info(f"Password reset successfully for user {user.email}")
    return {"message": "Your password has been successfully updated."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's profile."""
    return current_user
@router.post("/resend-verification")
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.is_verified:
        return {"message": "Email already verified."}

    # Generate a new token
    current_user.verification_token = str(uuid.uuid4())

    await db.commit()
    await db.refresh(current_user)

    verification_link = (
        f"http://localhost:5173/verify-email?"
        f"token={current_user.verification_token}"
    )

    # TODO: Send actual email here
    # await send_verification_email(current_user.email, verification_link)

    logger.info(f"Verification link: {verification_link}")

    return {
        "message": "Verification email sent.",
        "verification_link": verification_link if settings.DEBUG else None,
    }
    
@router.delete("/delete-account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete the current user's account.
    """

    logger.info(f"Deleting account for user {current_user.email}")

    await db.delete(current_user)
    await db.commit()

    return {
        "message": "Account deleted successfully."
    }
