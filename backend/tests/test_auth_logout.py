import jwt

from app.core.config import settings

SUCCESS_BODY = {"status": "success"}


def _post_logout_with_cookie(client, token):
    client.cookies.set("access_token", token)
    return client.post("/auth/logout")


def test_logout_success_returns_200_with_expected_body(client):
    response = _post_logout_with_cookie(client, "some.valid.looking.token")

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY


def test_logout_clears_expected_cookie(client):
    response = _post_logout_with_cookie(client, "some.valid.looking.token")

    assert response.status_code == 200
    cookie_header = response.headers["set-cookie"]
    assert "access_token=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "samesite=lax" in cookie_header.lower()
    assert "Path=/" in cookie_header
    assert "Secure" not in cookie_header  # ENVIRONMENT=local in tests

    # The cookie must be expired immediately, not merely re-set.
    assert "Max-Age=0" in cookie_header


def test_logout_without_cookie_returns_200_not_401(client):
    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY


def test_logout_without_cookie_still_sends_clear_instruction(client):
    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert "access_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_logout_with_expired_jwt_cookie_returns_200(client):
    expired_token = jwt.encode(
        {"sub": "1", "iat": 0, "exp": 1},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _post_logout_with_cookie(client, expired_token)

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY
    assert "access_token=" in response.headers["set-cookie"]


def test_logout_with_malformed_cookie_returns_200(client):
    response = _post_logout_with_cookie(client, "not-a-valid-jwt")

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY
    assert "access_token=" in response.headers["set-cookie"]


def test_logout_with_invalid_signature_cookie_returns_200(client):
    token_signed_with_wrong_key = jwt.encode(
        {"sub": "1", "iat": 0, "exp": 9999999999},
        "a-completely-different-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    response = _post_logout_with_cookie(client, token_signed_with_wrong_key)

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY


def test_logout_called_multiple_times_is_idempotent(client):
    first = _post_logout_with_cookie(client, "some.token")
    second = client.post("/auth/logout")
    third = _post_logout_with_cookie(client, "another.token")

    for response in (first, second, third):
        assert response.status_code == 200
        assert response.json() == SUCCESS_BODY
        assert "access_token=" in response.headers["set-cookie"]


def test_logout_response_identical_regardless_of_cookie_validity(client):
    responses = [
        client.post("/auth/logout"),
        _post_logout_with_cookie(client, "not-a-valid-jwt"),
        _post_logout_with_cookie(client, "some.valid.looking.token"),
    ]

    assert [r.status_code for r in responses] == [200, 200, 200]
    assert all(r.json() == SUCCESS_BODY for r in responses)


def test_logout_response_contains_no_jwt_or_user_info(client):
    response = _post_logout_with_cookie(client, "some.valid.looking.token")

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY
    assert set(response.json().keys()) == {"status"}


def test_logout_does_not_access_database(client, db_session, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("database should not be touched by logout")

    monkeypatch.setattr(type(db_session), "query", _boom)
    monkeypatch.setattr(type(db_session), "add", _boom)
    monkeypatch.setattr(type(db_session), "commit", _boom)

    response = _post_logout_with_cookie(client, "some.valid.looking.token")

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY


def test_logout_unexpected_error_returns_generic_500(client, monkeypatch):
    def _boom(response):
        raise RuntimeError("cookie backend unavailable")

    monkeypatch.setattr("app.api.routes.auth._clear_auth_cookie", _boom)

    response = client.post("/auth/logout")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
    }
    assert "cookie backend unavailable" not in response.text
    assert "set-cookie" not in response.headers
