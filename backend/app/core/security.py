"""Password hashing, default-password generation and JWT helpers."""
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import settings

# No look-alike characters (0/O, 1/l/I) so students can type the emailed password without guessing.
_LOWER = "abcdefghjkmnpqrstuvwxyz"
_UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_DIGITS = "23456789"


def generate_default_password(length: int = 10) -> str:
    """Random per-user password (crypto-secure) containing lower, upper and a digit."""
    alphabet = _LOWER + _UPPER + _DIGITS
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c in _LOWER for c in pw) and any(c in _UPPER for c in pw) and any(c in _DIGITS for c in pw):
            return pw


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jose.JWTError if the token is invalid or expired."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
