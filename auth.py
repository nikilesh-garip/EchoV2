"""
Echo — Authentication Module

Handles bcrypt password hashing and JWT token creation/verification
via python-jose. Tokens are HS256-signed with a 24-hour expiry.
"""

import os
import time
from typing import Optional, Dict, Any

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────────

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "fallback_dev_secret_change_me")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_SECONDS: int = 86400  # 24 hours

# ── Password Hashing (using bcrypt directly) ─────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ── JWT Token Management ────────────────────────────────────────────────────────

def create_access_token(user_id: int, username: str) -> str:
    """Create a signed JWT access token with user_id and username claims."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token. Returns the payload dict on success,
    or None if the token is invalid/expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return {
            "user_id": int(user_id),
            "username": payload.get("username", ""),
            "iat": payload.get("iat"),
            "exp": payload.get("exp"),
        }
    except JWTError:
        return None
