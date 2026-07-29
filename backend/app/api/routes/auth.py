from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    DuplicateEmailError,
    DuplicateUsernameError,
    InternalServerError,
    InvalidCredentialsError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import (
    LogoutResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
)

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


def _set_auth_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        path="/",
        max_age=max_age,
    )


def _clear_auth_cookie(response: Response) -> None:
    # Attributes must match _set_auth_cookie so the browser recognizes this as
    # the same cookie and actually deletes it rather than setting an unrelated one.
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        path="/",
    )


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
    _set_auth_cookie(response, token, max_age)

    return {"user": user}


@router.post("/login", status_code=status.HTTP_200_OK, response_model=UserLoginResponse)
def login_user(payload: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == payload.username).first()
    except Exception:
        raise InternalServerError()

    if user is None:
        # Same error as a wrong password: existence of the username must not leak.
        raise InvalidCredentialsError()

    try:
        password_matches = verify_password(payload.password, user.hashed_password)
    except Exception:
        raise InternalServerError()

    if not password_matches:
        raise InvalidCredentialsError()

    try:
        token, max_age = create_access_token(user.id)
    except Exception:
        raise InternalServerError()

    _set_auth_cookie(response, token, max_age)

    return {"data": {"user": user}}


@router.post("/logout", status_code=status.HTTP_200_OK, response_model=LogoutResponse)
def logout_user(response: Response):
    # No auth required and no JWT decoding: logout must succeed even when the
    # cookie is missing, expired, or invalid, so nothing here can depend on it.
    try:
        _clear_auth_cookie(response)
    except Exception:
        raise InternalServerError()

    return {"status": "success"}


@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
