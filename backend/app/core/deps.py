"""FastAPI dependencies for authentication and role checks."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import User, UserRole

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Logged-in user from the Bearer token. Does NOT enforce the forced password change
    (needed so /auth/me and /auth/change-password stay reachable)."""
    if creds is None:
        raise _unauthorized()
    try:
        user_id = uuid.UUID(decode_access_token(creds.credentials)["sub"])
    except (JWTError, KeyError, ValueError):
        raise _unauthorized("Invalid or expired token")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Invalid or expired token")
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Like get_current_user, but blocks accounts that still have the default password."""
    if user.must_change_password:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You must change your default password first")
    return user


def require_roles(*roles: UserRole):
    def checker(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to do this")
        return user

    return checker
