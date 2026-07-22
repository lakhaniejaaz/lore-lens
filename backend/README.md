# Back End

## Testing

Tests run against a real Postgres database (not SQLite/mocks) so DB-level constraints like unique email/username are exercised.

### One-time setup

1. Start the database: `docker compose up -d db`
2. Create the test database (only needed once, or after the `db_data` volume is recreated):
   ```bash
   docker exec lore_lens_db psql -U lore_lens_user -d lore_lens_db -c "CREATE DATABASE lore_lens_test_db;"
   ```
3. Apply migrations to the dev database: `docker compose run --rm backend alembic upgrade head`

### Running automated tests

Run the full suite:
```bash
docker compose run --rm \
  -e TEST_DATABASE_URL=postgresql+psycopg://lore_lens_user:lore_lens_password@db:5432/lore_lens_test_db \
  backend pytest -v
```

`TEST_DATABASE_URL` must point at a database separate from the app's dev DB — `tests/conftest.py` creates all tables in it at the start of the session and truncates them after each test.

Useful variations (append flags after `pytest`):
- Run a single file: `... backend pytest -v tests/test_auth_register.py`
- Run a single test: `... backend pytest -v tests/test_auth_register.py::test_register_success_returns_201_with_expected_user_shape`
- Run tests matching a keyword: `... backend pytest -v -k duplicate`
- Stop on first failure: `... backend pytest -x`

If you have a local Python environment with `backend/requirements.txt` installed and your host can reach the DB directly (see the port-conflict note below), you can skip `docker compose run` and just run `pytest` from the `backend/` directory with `TEST_DATABASE_URL` exported.

### Manually testing the endpoint (Postman)

Start the full stack: `docker compose up --build` (backend is then reachable at `http://localhost:8080`).

Base request setup, used for every case below:
- Method: `POST`
- URL: `http://localhost:8080/auth/register`
- Headers: `Content-Type: application/json`
- Body: select **raw** → **JSON**

**Successful registration:**
```json
{
  "first_name": "Ejaaz",
  "last_name": "Lakhani",
  "username": "lakhaniejaaz",
  "email": "ejaaz@example.com",
  "password": "password123"
}
```
Send it. Expect status `201` and a JSON body with no password/hash fields. Open the response's **Cookies** tab (below the response body) and confirm `access_token` is present with `HttpOnly` checked, `SameSite=Lax`, and `Path=/`.

**Duplicate email or username:** send the same request again (or change only `username`, keeping the same `email`). Expect `409` with `{"error": {"code": "duplicate_email", ...}}` (or `duplicate_username` if you instead reused the username).

**Validation error (e.g. short password):** change `password` to `"short"` and a fresh `username`/`email`. Expect `422` with `{"error": {"code": "validation_error", "fields": {"password": "..."}}}`.

**Malformed JSON:** in the raw body editor, type invalid JSON directly, e.g. `{not valid json` (Postman won't block sending it even though its JSON linter flags it). Expect `422` with `{"error": {"code": "validation_error", ...}}`.

**Inspecting the JWT claims:** open **Cookies** (bottom of the response, or Postman's cookie manager for `localhost`), copy the `access_token` value, and decode it at a tool like jwt.io — no signature verification needed to read the claims (`sub`, `iat`, `exp`).

### Port conflict note

If you have a local Postgres server already running on your Mac, it may already be bound to port 5432, which conflicts with the Docker `db` service. This repo maps the container to host port `5433` instead (`docker-compose.yml`), so host-side tools (`psql`, GUI clients, `alembic` run outside Docker) should connect to `localhost:5433`, not `5432`. Container-to-container traffic (e.g. `backend` → `db`) is unaffected and still uses port 5432 internally.
