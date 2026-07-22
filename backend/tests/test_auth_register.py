import jwt
import pytest

from app.core.config import settings
from app.core.security import verify_password
from app.db.models.user import User


def test_register_success_returns_201_with_expected_user_shape(client, valid_payload):
    response = client.post("/auth/register", json=valid_payload)

    assert response.status_code == 201
    body = response.json()
    user = body["user"]
    assert set(user.keys()) == {"id", "first_name", "last_name", "username", "email", "created_at"}
    assert user["first_name"] == "Ada"
    assert user["last_name"] == "Lovelace"
    assert user["username"] == "ada_lovelace"
    assert user["email"] == "ada@example.com"
    assert "password" not in body
    assert "hashed_password" not in body
    assert "access_token" not in body


def test_register_password_is_hashed_and_not_returned(client, valid_payload, db_session):
    response = client.post("/auth/register", json=valid_payload)
    assert response.status_code == 201

    user = db_session.query(User).filter_by(email="ada@example.com").first()
    assert user is not None
    assert user.hashed_password != valid_payload["password"]
    assert verify_password(valid_payload["password"], user.hashed_password)


def test_register_password_whitespace_preserved_exactly(client, valid_payload, db_session):
    payload = {**valid_payload, "password": "  secretpw  "}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    user = db_session.query(User).filter_by(email="ada@example.com").first()
    assert verify_password("  secretpw  ", user.hashed_password)
    assert not verify_password("secretpw", user.hashed_password)


def test_register_sets_expected_cookie(client, valid_payload):
    response = client.post("/auth/register", json=valid_payload)

    assert response.status_code == 201
    cookie_header = response.headers["set-cookie"]
    assert "access_token=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "samesite=lax" in cookie_header.lower()
    assert "Path=/" in cookie_header
    assert "Secure" not in cookie_header  # ENVIRONMENT=local in tests

    assert response.cookies.get("access_token") is not None


def test_register_jwt_has_expected_claims(client, valid_payload):
    response = client.post("/auth/register", json=valid_payload)
    assert response.status_code == 201

    token = response.cookies.get("access_token")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    user_id = response.json()["user"]["id"]
    assert payload["sub"] == str(user_id)
    assert "iat" in payload
    assert "exp" in payload
    assert set(payload.keys()) == {"sub", "iat", "exp"}


def test_register_username_and_email_stored_lowercase(client, valid_payload):
    payload = {**valid_payload, "username": "Ada_Lovelace", "email": "Ada@Example.com"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    user = response.json()["user"]
    assert user["username"] == "ada_lovelace"
    assert user["email"] == "ada@example.com"


def test_register_names_are_trimmed(client, valid_payload):
    payload = {**valid_payload, "first_name": "  Ada  ", "last_name": "  Lovelace  "}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    user = response.json()["user"]
    assert user["first_name"] == "Ada"
    assert user["last_name"] == "Lovelace"


def test_register_duplicate_email_rejected_409(client, valid_payload):
    client.post("/auth/register", json=valid_payload)
    second = {**valid_payload, "username": "someone_else"}
    response = client.post("/auth/register", json=second)

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "duplicate_email",
            "message": "An account with this email already exists.",
        }
    }
    assert "set-cookie" not in response.headers


def test_register_duplicate_username_rejected_409(client, valid_payload):
    client.post("/auth/register", json=valid_payload)
    second = {**valid_payload, "email": "someone-else@example.com"}
    response = client.post("/auth/register", json=second)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_username"
    assert "set-cookie" not in response.headers


def test_register_case_insensitive_duplicate_email_rejected_409(client, valid_payload):
    client.post("/auth/register", json=valid_payload)
    second = {**valid_payload, "username": "someone_else", "email": "ADA@EXAMPLE.COM"}
    response = client.post("/auth/register", json=second)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_email"


def test_register_case_insensitive_duplicate_username_rejected_409(client, valid_payload):
    client.post("/auth/register", json=valid_payload)
    second = {**valid_payload, "email": "someone-else@example.com", "username": "ADA_LOVELACE"}
    response = client.post("/auth/register", json=second)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_username"


@pytest.mark.parametrize("field", ["first_name", "last_name", "username", "email", "password"])
def test_register_missing_required_field_rejected_422(client, valid_payload, field):
    payload = dict(valid_payload)
    del payload[field]
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert field in body["error"]["fields"]


@pytest.mark.parametrize("field", ["first_name", "last_name", "username", "password"])
def test_register_whitespace_only_field_rejected_422(client, valid_payload, field):
    payload = {**valid_payload, field: "   "}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_register_invalid_email_format_rejected_422(client, valid_payload):
    payload = {**valid_payload, "email": "not-an-email"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert "email" in response.json()["error"]["fields"]


def test_register_username_invalid_characters_rejected_422(client, valid_payload):
    payload = {**valid_payload, "username": "ada lovelace!"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert "username" in response.json()["error"]["fields"]


def test_register_username_too_short_rejected_422(client, valid_payload):
    payload = {**valid_payload, "username": "ab"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert "username" in response.json()["error"]["fields"]


def test_register_password_too_short_rejected_422(client, valid_payload):
    payload = {**valid_payload, "password": "short1"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert "password" in response.json()["error"]["fields"]


def test_register_unexpected_extra_field_rejected_422(client, valid_payload):
    payload = {**valid_payload, "role": "admin"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_register_malformed_json_returns_422(client):
    response = client.post(
        "/auth/register",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_register_hashing_failure_returns_500_and_creates_no_user(
    client, valid_payload, db_session, monkeypatch
):
    def _boom(password):
        raise RuntimeError("hashing backend unavailable")

    monkeypatch.setattr("app.api.routes.auth.hash_password", _boom)

    response = client.post("/auth/register", json=valid_payload)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "set-cookie" not in response.headers
    assert db_session.query(User).filter_by(email="ada@example.com").first() is None


def test_register_db_failure_returns_500_without_leaking_details(
    client, valid_payload, db_session, monkeypatch
):
    def _boom(self):
        raise RuntimeError("connection reset by peer")

    monkeypatch.setattr(type(db_session), "commit", _boom)

    response = client.post("/auth/register", json=valid_payload)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "connection reset" not in response.text
