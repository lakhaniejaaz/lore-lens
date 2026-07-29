import jwt
from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import InternalServerError, NotAuthenticatedError
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise NotAuthenticatedError()

    try:
        payload = decode_access_token(access_token)
    except jwt.PyJWTError:
        raise NotAuthenticatedError()

    subject = payload.get("sub")
    if not subject:
        raise NotAuthenticatedError()

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise NotAuthenticatedError()

    try:
        user = db.get(User, user_id)
    except Exception:
        raise InternalServerError()

    if user is None:
        # A validated token can outlive the account it names (e.g. deletion).
        # Treat this as an auth failure rather than 404 to avoid confirming
        # or denying which user IDs exist.
        raise NotAuthenticatedError()

    return user
