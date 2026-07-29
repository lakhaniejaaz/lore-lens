import jwt
import pytest

from app.core.config import settings
from app.core.security import create_access_token

NOT_AUTHENTICATED_BODY = {
    "error": {
        "code": "not_authenticated",
        "message": "Not authenticated.",
    }
}


def _get_me_with_cookie(client, token):
    client.cookies.set("access_token", token)
    return client.get("/auth/me")


def _valid_token_for(user_id):
    token, _ = create_access_token(user_id)
    return token


def test_me_success_returns_200_with_expected_user_shape(client, existing_user):
    response = _get_me_with_cookie(client, _valid_token_for(existing_user.id))

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"id", "first_name", "last_name", "username", "email", "created_at"}
    assert body["id"] == existing_user.id
    assert body["username"] == existing_user.username
    assert body["email"] == existing_user.email
    assert "password" not in body
    assert "hashed_password" not in body
    assert "access_token" not in body


def test_me_returns_the_user_identified_by_the_jwt_not_another_user(client, db_session, existing_user):
    from app.core.security import hash_password
    from app.db.models.user import User

    other_user = User(
        first_name="Grace",
        last_name="Hopper",
        username="grace_hopper",
        email="grace@example.com",
        hashed_password=hash_password("another-password"),
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    response = _get_me_with_cookie(client, _valid_token_for(existing_user.id))

    assert response.status_code == 200
    assert response.json()["id"] == existing_user.id
    assert response.json()["username"] == existing_user.username


def test_me_response_never_contains_password_hash(client, existing_user):
    response = _get_me_with_cookie(client, _valid_token_for(existing_user.id))

    assert response.status_code == 200
    assert existing_user.hashed_password not in response.text
    assert "hashed_password" not in response.text


def test_me_does_not_modify_the_database(client, db_session, existing_user):
    original_updated_at = existing_user.updated_at

    response = _get_me_with_cookie(client, _valid_token_for(existing_user.id))

    assert response.status_code == 200
    db_session.refresh(existing_user)
    assert existing_user.updated_at == original_updated_at


def test_me_ignores_request_body(client, existing_user):
    client.cookies.set("access_token", _valid_token_for(existing_user.id))
    response = client.request("GET", "/auth/me", json={"unexpected": "body"})

    assert response.status_code == 200
    assert response.json()["id"] == existing_user.id


def test_me_extra_unexpected_claims_do_not_affect_result(client, existing_user):
    token = jwt.encode(
        {"sub": str(existing_user.id), "iat": 0, "exp": 9999999999, "role": "admin"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _get_me_with_cookie(client, token)

    assert response.status_code == 200
    assert response.json()["id"] == existing_user.id


def test_me_missing_cookie_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_empty_cookie_returns_401(client):
    response = _get_me_with_cookie(client, "")

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_malformed_jwt_returns_401(client):
    response = _get_me_with_cookie(client, "not-a-valid-jwt")

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_invalid_signature_returns_401(client, existing_user):
    token = jwt.encode(
        {"sub": str(existing_user.id), "iat": 0, "exp": 9999999999},
        "a-completely-different-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _get_me_with_cookie(client, token)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_expired_jwt_returns_401(client, existing_user):
    token = jwt.encode(
        {"sub": str(existing_user.id), "iat": 0, "exp": 1},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _get_me_with_cookie(client, token)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_unexpected_algorithm_returns_401(client, existing_user):
    token = jwt.encode(
        {"sub": str(existing_user.id), "iat": 0, "exp": 9999999999},
        settings.JWT_SECRET_KEY,
        algorithm="HS384",
    )
    response = _get_me_with_cookie(client, token)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_missing_sub_claim_returns_401(client):
    token = jwt.encode(
        {"iat": 0, "exp": 9999999999},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _get_me_with_cookie(client, token)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


@pytest.mark.parametrize("sub", ["", None])
def test_me_null_or_empty_sub_claim_returns_401(client, sub):
    token = jwt.encode(
        {"sub": sub, "iat": 0, "exp": 9999999999},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _get_me_with_cookie(client, token)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_non_numeric_sub_claim_returns_401(client):
    token = jwt.encode(
        {"sub": "not-a-user-id", "iat": 0, "exp": 9999999999},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _get_me_with_cookie(client, token)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_jwt_for_nonexistent_user_returns_401_not_404(client):
    response = _get_me_with_cookie(client, _valid_token_for(999999))

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_jwt_for_deleted_user_returns_401(client, db_session, existing_user):
    token = _valid_token_for(existing_user.id)
    db_session.delete(existing_user)
    db_session.commit()

    response = _get_me_with_cookie(client, token)

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED_BODY


def test_me_db_failure_returns_500_without_leaking_details(client, existing_user, db_session, monkeypatch):
    def _boom(self, *args, **kwargs):
        raise RuntimeError("connection reset by peer")

    monkeypatch.setattr(type(db_session), "get", _boom)

    response = _get_me_with_cookie(client, _valid_token_for(existing_user.id))

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "connection reset" not in response.text
