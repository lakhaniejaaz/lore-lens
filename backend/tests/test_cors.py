ALLOWED_ORIGIN_1 = "http://localhost:5173"
ALLOWED_ORIGIN_2 = "http://localhost:3000"
UNTRUSTED_ORIGIN = "http://evil.example.com"


def test_allowed_origin_receives_cors_headers_on_login(client):
    response = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "wrong"},
        headers={"Origin": ALLOWED_ORIGIN_1},
    )

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN_1
    assert response.headers["access-control-allow-credentials"] == "true"


def test_second_allowed_origin_receives_cors_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "wrong"},
        headers={"Origin": ALLOWED_ORIGIN_2},
    )

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN_2
    assert response.headers["access-control-allow-credentials"] == "true"


def test_preflight_request_from_allowed_origin_succeeds(client):
    response = client.options(
        "/auth/login",
        headers={
            "Origin": ALLOWED_ORIGIN_1,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN_1
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_untrusted_origin_does_not_receive_cors_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "wrong"},
        headers={"Origin": UNTRUSTED_ORIGIN},
    )

    assert "access-control-allow-origin" not in response.headers


def test_untrusted_origin_preflight_is_not_granted_cors_access(client):
    response = client.options(
        "/auth/login",
        headers={
            "Origin": UNTRUSTED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert "access-control-allow-origin" not in response.headers
