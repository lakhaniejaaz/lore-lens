import jwt
import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.user import User

INVALID_CREDENTIALS_BODY = {
    "error": {
        "code": "invalid_credentials",
        "message": "Username or password is incorrect.",
    }
}


@pytest.fixture
def login_payload(valid_payload):
    return {"username": valid_payload["username"], "password": valid_payload["password"]}


def test_login_success_returns_200_with_expected_user_shape(client, existing_user, login_payload):
    response = client.post("/auth/login", json=login_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    user = body["data"]["user"]
    assert set(user.keys()) == {"id", "first_name", "last_name", "username", "email", "created_at"}
    assert user["id"] == existing_user.id
    assert user["username"] == existing_user.username
    assert "password" not in body
    assert "hashed_password" not in body
    assert "access_token" not in body


def test_login_username_case_insensitive(client, existing_user, login_payload):
    payload = {**login_payload, "username": login_payload["username"].upper()}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert response.json()["data"]["user"]["username"] == existing_user.username


def test_login_username_whitespace_trimmed(client, existing_user, login_payload):
    payload = {**login_payload, "username": f"  {login_payload['username']}  "}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert response.json()["data"]["user"]["username"] == existing_user.username


def test_login_sets_expected_cookie(client, existing_user, login_payload):
    response = client.post("/auth/login", json=login_payload)

    assert response.status_code == 200
    cookie_header = response.headers["set-cookie"]
    assert "access_token=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "samesite=lax" in cookie_header.lower()
    assert "Path=/" in cookie_header
    assert "Secure" not in cookie_header  # ENVIRONMENT=local in tests

    assert response.cookies.get("access_token") is not None


def test_login_jwt_has_expected_claims(client, existing_user, login_payload):
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200

    token = response.cookies.get("access_token")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    assert payload["sub"] == str(existing_user.id)
    assert "iat" in payload
    assert "exp" in payload
    assert set(payload.keys()) == {"sub", "iat", "exp"}


def test_login_incorrect_username_returns_generic_401(client, existing_user, login_payload):
    payload = {**login_payload, "username": "someone_else"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY
    assert "set-cookie" not in response.headers


def test_login_incorrect_password_returns_generic_401(client, existing_user, login_payload):
    payload = {**login_payload, "password": "wrong-password"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY
    assert "set-cookie" not in response.headers


def test_login_incorrect_username_and_password_returns_generic_401(client, existing_user, login_payload):
    payload = {"username": "someone_else", "password": "wrong-password"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("field", ["username", "password"])
def test_login_missing_field_rejected_422(client, existing_user, login_payload, field):
    payload = dict(login_payload)
    del payload[field]
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert field in body["error"]["fields"]
    assert "set-cookie" not in response.headers


def test_login_empty_username_rejected_422(client, existing_user, login_payload):
    payload = {**login_payload, "username": ""}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_login_empty_password_rejected_422(client, existing_user, login_payload):
    payload = {**login_payload, "password": ""}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_login_whitespace_only_username_rejected_422(client, existing_user, login_payload):
    payload = {**login_payload, "username": "   "}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_login_unexpected_extra_field_rejected_422(client, existing_user, login_payload):
    payload = {**login_payload, "remember_me": True}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_login_malformed_json_returns_422(client):
    response = client.post(
        "/auth/login",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_login_password_not_trimmed_before_verification(client, db_session, valid_payload):
    padded_password = "  correct-horse  "
    user = User(
        first_name=valid_payload["first_name"],
        last_name=valid_payload["last_name"],
        username=valid_payload["username"],
        email=valid_payload["email"],
        hashed_password=hash_password(padded_password),
    )
    db_session.add(user)
    db_session.commit()

    # The trimmed version must NOT match, since the stored password included whitespace.
    trimmed_response = client.post(
        "/auth/login", json={"username": valid_payload["username"], "password": "correct-horse"}
    )
    assert trimmed_response.status_code == 401
    assert "set-cookie" not in trimmed_response.headers

    exact_response = client.post(
        "/auth/login", json={"username": valid_payload["username"], "password": padded_password}
    )
    assert exact_response.status_code == 200


def test_login_incorrect_whitespace_returns_401(client, existing_user, login_payload):
    payload = {**login_payload, "password": f"  {login_payload['password']}  "}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY


def test_login_whitespace_only_password_not_rejected_by_validation_but_fails_auth(
    client, existing_user, login_payload
):
    payload = {**login_payload, "password": "   "}
    response = client.post("/auth/login", json=payload)

    # A whitespace-only password is a legal (if unlikely) credential, not a validation error.
    # Since no account has a whitespace-only password, it must fail verification, not validation.
    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY


def test_login_response_never_contains_password_hash(client, existing_user, login_payload):
    response = client.post("/auth/login", json=login_payload)

    assert response.status_code == 200
    assert existing_user.hashed_password not in response.text
    assert "hashed_password" not in response.text


def test_login_db_failure_returns_500_without_leaking_details(
    client, existing_user, login_payload, db_session, monkeypatch
):
    def _boom(self, *args, **kwargs):
        raise RuntimeError("connection reset by peer")

    monkeypatch.setattr(type(db_session), "query", _boom)

    response = client.post("/auth/login", json=login_payload)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "connection reset" not in response.text
    assert "set-cookie" not in response.headers


def test_login_password_verification_failure_returns_500(
    client, existing_user, login_payload, monkeypatch
):
    def _boom(password, hashed):
        raise RuntimeError("hashing backend unavailable")

    monkeypatch.setattr("app.api.routes.auth.verify_password", _boom)

    response = client.post("/auth/login", json=login_payload)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "set-cookie" not in response.headers


def test_login_jwt_generation_failure_returns_500(client, existing_user, login_payload, monkeypatch):
    def _boom(user_id):
        raise RuntimeError("signing key unavailable")

    monkeypatch.setattr("app.api.routes.auth.create_access_token", _boom)

    response = client.post("/auth/login", json=login_payload)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "set-cookie" not in response.headers
