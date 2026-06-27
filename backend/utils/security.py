"""
NewsMind AI - Security Utilities
Why: Implements credential hashing and cryptographically signed JWT credentials.
How: Utilizes passlib (bcrypt) for hashing and python-jose (JWT) for token management.
Trade-offs: Local symmetric signing (HS256) is simple to implement, but asymmetric key pairs (RS256)
would be required if third-party microservices needed to independently verify our user tokens.
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from backend.config import settings

# Password context setup (bcrypt scheme)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if a raw password matches its stored bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Computes a bcrypt hash for a plain-text password.
    """
    print(password)
    print(type(password))
    print(len(password))
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a short-lived access JWT token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a long-lived refresh JWT token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)  # Default: 30 days

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Decodes and validates a JWT token.
    Returns the subject string if signature is valid, type matches, and it hasn't expired.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
        token_sub: str = payload.get("sub")
        token_type_found: str = payload.get("type")

        if token_sub is None or token_type_found != token_type:
            return None

        # Expiration is checked automatically during jwt.decode
        return token_sub
    except JWTError:
        return None
