from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, DuplicateEmailError, DuplicateUsernameError, InternalServerError
from app.core.security import create_access_token, hash_password
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserRegisterRequest, UserRegisterResponse

router = APIRouter(prefix="/auth", tags=["auth"])

CONSTRAINT_TO_ERROR = {
    "ix_users_email": DuplicateEmailError,
    "ix_users_username": DuplicateUsernameError,
}


def _duplicate_error_from_integrity_error(exc: IntegrityError) -> AppError:
    constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None) or ""
    error_cls = CONSTRAINT_TO_ERROR.get(constraint)
    if error_cls is None:
        text = str(exc.orig).lower()
        if "email" in text:
            error_cls = DuplicateEmailError
        elif "username" in text:
            error_cls = DuplicateUsernameError
    return (error_cls or InternalServerError)()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRegisterResponse)
def register_user(payload: UserRegisterRequest, response: Response, db: Session = Depends(get_db)):
    try:
        hashed = hash_password(payload.password)
    except Exception:
        raise InternalServerError()

    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        email=payload.email,
        hashed_password=hashed,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _duplicate_error_from_integrity_error(exc)
    except Exception:
        db.rollback()
        raise InternalServerError()

    db.refresh(user)

    token, max_age = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        path="/",
        max_age=max_age,
    )

    return {"user": user}
