# Planning for Frontend-to-Backend CORS Configuration

## Goal

Configure Cross-Origin Resource Sharing (CORS) so that the Lore Lens frontend can communicate with the FastAPI backend through the browser.

The immediate purpose of this work is to allow the frontend login page to call the existing authentication endpoints without being blocked by the browser's CORS policy.

The configuration must also support the HTTP-only JWT authentication cookie used by the Lore Lens authentication flow.

This planning document covers shared frontend and backend CORS configuration only.

## Background

The Lore Lens frontend and backend currently run on different origins during local development.

For example:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

Because the ports are different, the browser considers these separate origins.

The frontend can currently submit a login request, but the browser blocks the request or response because the backend does not return the required CORS headers.

Postman testing does not expose this issue because CORS is enforced by browsers rather than by Postman or the backend API itself.

## User Story

As a Lore Lens user, I want the frontend to communicate with the backend so that I can register, sign in, remain authenticated, and access protected application features through the browser.

## Tech Stack

- Frontend: React and TypeScript
- Backend: FastAPI
- Database: PostgreSQL
- Authentication: JWT stored in an HTTP-only cookie
- ORM: SQLAlchemy
- Configuration: Existing application configuration and environment-variable conventions

## Scope

This feature includes:

- Adding or updating FastAPI CORS middleware.
- Allowing the Lore Lens frontend development origin.
- Supporting credentialed browser requests.
- Ensuring frontend authentication requests include credentials.
- Confirming that browser-generated preflight requests succeed.
- Confirming that the JWT authentication cookie can be set and sent between the frontend and backend.
- Centralizing frontend credential configuration where supported by the existing architecture.
- Adding environment-based configuration for trusted frontend origins if consistent with the current backend configuration.
- Adding or updating automated tests where appropriate.
- Documenting any environment variables required for local development.

## Out of Scope

This feature does not include:

- Building or redesigning the login page.
- Building the user registration page.
- Changing existing authentication endpoint contracts.
- Changing JWT generation or validation logic.
- Replacing HTTP-only cookie authentication.
- Adding CSRF protection.
- Deploying the frontend or backend.
- Configuring unknown production domains.
- Supporting arbitrary third-party origins.
- Using wildcard origin access for credentialed requests.
- Refactoring unrelated frontend API code.
- Refactoring unrelated FastAPI application configuration.
- Changing authentication cookie settings unless an existing setting prevents local frontend authentication from working.

## Current Authentication Architecture

Lore Lens currently uses:

- `POST /auth/register` to create and authenticate a user.
- `POST /auth/login` to authenticate an existing user.
- `POST /auth/logout` to end the authenticated session.
- `GET /auth/me` to retrieve the currently authenticated user.

Authentication is handled through a JWT stored in an HTTP-only cookie.

Because authentication is cookie-based, the frontend request and backend CORS configuration must both explicitly support credentials.

## Functional Requirements

### Backend CORS Middleware

The FastAPI application must use `CORSMiddleware`.

The middleware must be registered on the primary FastAPI application.

The middleware must allow requests only from explicitly trusted frontend origins.

For local development, the allowed origin should include the URL used by the existing frontend development server.

Example:

```text
http://localhost:5173
```

The implementation must inspect the existing frontend configuration and confirm the actual frontend origin rather than assuming the port.

### Credential Support

The backend CORS configuration must include:

```python
allow_credentials=True
```

This is required because Lore Lens uses an HTTP-only cookie for authentication.

The backend must not combine credentialed browser requests with:

```python
allow_origins=["*"]
```

Credentialed requests must use explicit trusted origins.

### Allowed Methods

The CORS configuration must allow the HTTP methods used by the Lore Lens frontend.

At minimum, this includes:

- `GET`
- `POST`
- `OPTIONS`

Using the following is acceptable if it matches the existing project style:

```python
allow_methods=["*"]
```

Allowed origins must remain restricted even if all HTTP methods are permitted.

### Allowed Headers

The configuration must allow headers required by frontend API requests.

This will normally include:

- `Content-Type`
- `Accept`

Using the following is acceptable if it matches the existing project style:

```python
allow_headers=["*"]
```

Allowed origins must remain restricted even if all request headers are permitted.

### Preflight Requests

The backend must successfully respond to browser-generated `OPTIONS` preflight requests.

The preflight response must include the required CORS headers for the requesting trusted frontend origin.

The frontend must not manually send an `OPTIONS` request.

### Frontend Credential Configuration

Authentication-related frontend requests must include browser credentials.

For the native Fetch API, requests must use:

```typescript
credentials: "include"
```

For Axios, requests must use:

```typescript
withCredentials: true
```

The implementation must follow the HTTP client and request patterns already used by the frontend.

Credential configuration should be centralized in the existing API client, request wrapper, hook, or service where possible rather than repeated in every authentication request.

### Login Request

When the frontend submits valid login credentials:

- The browser must allow the request to reach the backend.
- The backend must return the existing successful login response.
- The browser must accept the authentication cookie.
- The frontend must be able to access the response body.
- No CORS error should appear in the browser console.

When the frontend submits invalid login credentials:

- The browser must allow the frontend to receive the backend error response.
- The frontend must be able to display or process the existing authentication error.
- The browser must not replace the backend response with a generic CORS failure.

### Registration Request

The shared CORS configuration must support the existing `POST /auth/register` endpoint.

The registration page itself remains out of scope, but the infrastructure must allow future frontend registration requests to:

- Reach the backend.
- Receive backend validation or duplicate-user errors.
- Receive the successful registration response.
- Accept the authentication cookie returned after successful registration.

### Authenticated User Request

After a successful login or registration request:

- The browser must store the existing authentication cookie.
- A request to `GET /auth/me` must include the authentication cookie.
- The backend must identify the authenticated user from the cookie.
- The frontend must receive the existing authenticated-user response.
- The request must not fail because of CORS.

### Logout Request

When the frontend calls `POST /auth/logout`:

- The browser must include credentials.
- The request must reach the backend.
- The existing authentication cookie must be cleared.
- A later request to `GET /auth/me` must return the existing unauthenticated response.
- The request must not fail because of CORS.

## Configuration Requirements

### Allowed Origins

Trusted frontend origins should be configurable rather than permanently tied to one environment where practical.

A suitable environment variable could be:

```text
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

If multiple origins are supported, the implementation must define and document the expected format.

For example:

```text
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

The final approach must follow the existing application configuration conventions.

### Origin Parsing

If origins are stored as a comma-separated environment variable:

- Each origin must be separated correctly.
- Whitespace around each origin must be removed.
- Empty values must not be added to the allowed-origin list.
- Origins must remain complete origin strings including scheme, hostname, and port where applicable.

Example parsed value:

```python
[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

### Origin Matching

Origins must match exactly.

The following values are different origins:

```text
http://localhost:5173
http://127.0.0.1:5173
http://localhost:3000
https://localhost:5173
```

Only origins intentionally used by the application should be allowed.

Configured origins should not include a trailing slash.

Correct:

```text
http://localhost:5173
```

Avoid:

```text
http://localhost:5173/
```

### Development and Production Configuration

The initial implementation must support the current local development environment.

The configuration should allow future deployed frontend origins to be added without changing authentication logic.

Production origins must not be guessed or added before they are known.

The application should fail clearly or use a safe documented development default if the CORS configuration is missing, depending on existing project configuration conventions.

The implementation must not silently allow all origins as a fallback.

## Cookie Compatibility Requirements

The implementation must inspect the existing authentication cookie settings, including:

- Cookie name
- `httponly`
- `secure`
- `samesite`
- `path`
- `domain`, if configured
- Cookie expiration or maximum age

The existing cookie settings should not be changed unless they prevent the current local frontend and backend origins from working together.

For local development over HTTP:

- A cookie configured with `secure=True` may not be stored or sent by the browser.
- The implementation must confirm whether secure-cookie behavior is already environment-dependent.
- Any required adjustment must follow the existing configuration architecture.
- Production security must not be weakened to solve a local development issue.

The frontend and backend running on different ports of the same hostname are different origins but generally remain the same site.

CORS configuration and cookie configuration must be treated as related but separate browser requirements.

## Security Requirements

- Do not use `allow_origins=["*"]` with credentialed requests.
- Only explicitly trusted frontend origins may access credentialed responses.
- Do not expose the JWT to frontend JavaScript.
- Do not move the JWT into `localStorage` or `sessionStorage`.
- Do not log authentication cookies or JWT values.
- Do not return the JWT in the JSON response.
- Do not disable browser security controls.
- Do not dynamically reflect any requesting origin without validating it against a trusted allowlist.
- Do not add production origins that have not been confirmed.
- Preserve the existing HTTP-only cookie authentication design.
- Preserve existing password and authentication security behavior.

## Error Handling Requirements

CORS configuration must allow the frontend to receive existing backend error responses.

This includes responses for:

- Invalid credentials.
- Missing required request fields.
- Invalid request formats.
- Duplicate registration fields.
- Missing authentication cookies.
- Invalid or expired JWTs.
- Internal server errors.

The CORS implementation must not replace application-level error handling.

The frontend should receive the existing backend response status code and response body whenever the request comes from a trusted origin.

Requests from untrusted origins must not receive credentialed CORS access.

## Testing Requirements

### Backend Automated Tests

Add or update tests to verify CORS behavior where consistent with the existing test suite.

Tests should cover:

- A request from an allowed frontend origin receives the expected CORS headers.
- A preflight request from an allowed origin succeeds.
- The allowed origin is returned in `Access-Control-Allow-Origin`.
- Credential support is returned through `Access-Control-Allow-Credentials`.
- Required methods are permitted.
- Required headers are permitted.
- An untrusted origin is not granted credentialed CORS access.
- Existing authentication endpoint behavior remains unchanged.

A successful allowed-origin response should include headers equivalent to:

```text
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true
```

The exact test implementation must follow existing FastAPI and pytest conventions.

### Frontend Testing

Add or update frontend tests where consistent with the existing testing structure.

Tests should confirm that:

- The login request includes credentials.
- Shared API configuration applies credentials to authentication requests.
- Existing login success handling remains unchanged.
- Existing login error handling remains unchanged.

Tests should avoid testing browser CORS enforcement directly if the current frontend testing tools cannot accurately reproduce browser behavior.

### Manual Browser Testing

Manual verification must be completed using the actual frontend in a browser.

The implementation should verify the following flow:

1. Start the FastAPI backend.
2. Start the React frontend.
3. Open the frontend using its configured development URL.
4. Open the browser developer tools.
5. Submit valid credentials through the login page.
6. Confirm no CORS error appears in the console.
7. Confirm the login request returns the expected status code.
8. Confirm the response includes the appropriate CORS headers.
9. Confirm the authentication cookie appears in browser storage.
10. Confirm the cookie remains HTTP-only.
11. Call or navigate through behavior that triggers `GET /auth/me`.
12. Confirm the authenticated-user request succeeds.
13. Log out through the frontend or frontend API client.
14. Confirm the authentication cookie is removed or expired.
15. Confirm `GET /auth/me` no longer returns an authenticated user.

### Invalid Login Testing

Manual testing must also verify:

1. Submit invalid login credentials.
2. Confirm the backend authentication response reaches the frontend.
3. Confirm the frontend receives the intended status code and error body.
4. Confirm no authentication cookie is created.
5. Confirm the browser console does not report a CORS failure.

### Untrusted-Origin Testing

Where practical, verify that a request from an origin not included in the configured allowlist does not receive credentialed CORS permission.

The backend may still process some direct requests because CORS is enforced by the browser, but it must not return headers that grant the untrusted browser origin access to the credentialed response.

## Expected Implementation Areas

The implementation may require changes to:

- The main FastAPI application entry point.
- Backend settings or configuration classes.
- Backend environment-variable examples.
- Backend test configuration.
- Backend CORS tests.
- The frontend API client or request wrapper.
- The frontend authentication service.
- The frontend login hook.
- Frontend API tests.
- Local development documentation.

The exact files must be identified after inspecting the existing codebase.

## Implementation Guidance

A typical FastAPI configuration may resemble:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This is an example only.

The final implementation must follow the existing Lore Lens architecture, naming conventions, settings structure, import organization, and application initialization pattern.

A typical Fetch request may resemble:

```typescript
await fetch(`${apiBaseUrl}/auth/login`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  credentials: "include",
  body: JSON.stringify(credentials),
});
```

This is also an example only.

The final frontend change must use the existing API request architecture rather than introducing a duplicate request pattern.

## Acceptance Criteria

The feature is complete when all of the following are true:

- The FastAPI application uses CORS middleware.
- The actual local frontend origin is explicitly allowed.
- Credentialed requests are enabled.
- Wildcard origins are not used with credentials.
- Browser-generated preflight requests succeed for the trusted frontend origin.
- Frontend authentication requests include credentials.
- A successful login request works through the browser without a CORS error.
- The browser accepts the HTTP-only authentication cookie.
- `GET /auth/me` succeeds after login and includes the authentication cookie.
- `POST /auth/logout` clears the authentication cookie through the frontend.
- Invalid login responses reach the frontend without being hidden by a CORS error.
- Untrusted origins are not granted credentialed CORS access.
- Existing authentication endpoint contracts remain unchanged.
- Existing backend authentication tests continue to pass.
- New or updated CORS tests pass.
- Required environment variables are documented.
- No unrelated frontend or backend functionality is changed.

## Edge Cases

The implementation must consider:

- The frontend using `localhost` while the allowed origin uses `127.0.0.1`.
- The frontend development server using a different port.
- The frontend origin including an accidental trailing slash in configuration.
- Multiple trusted development origins.
- Missing or empty CORS environment configuration.
- Whitespace in a comma-separated origins variable.
- Duplicate origins in configuration.
- Browser preflight requests sent before a login request.
- Invalid login responses requiring CORS headers.
- Backend exceptions still needing accessible response headers for trusted origins.
- Authentication cookies configured as secure during local HTTP development.
- Requests that omit frontend credential configuration.
- A frontend request using the correct API URL but an unapproved browser origin.
- Existing tests that do not send an `Origin` header and therefore do not exercise CORS behavior.

## Assumptions to Validate

Before implementation, confirm:

- The actual frontend development origin.
- The actual backend development origin.
- Whether the frontend uses Fetch, Axios, or a custom API client.
- Whether credentials are already configured globally.
- Where the FastAPI application is created.
- Whether CORS middleware already exists in any form.
- How backend settings are loaded.
- How list-based environment settings are represented.
- Whether environment-specific cookie settings already exist.
- Whether `localhost` and `127.0.0.1` are both used during development.
- Which frontend component, hook, or service currently submits login requests.
- Whether frontend and backend automated tests already include authentication request helpers.

## Implementation Order

1. Inspect the current FastAPI application initialization.
2. Inspect backend settings and environment-variable conventions.
3. Inspect the existing authentication cookie settings.
4. Inspect the frontend API request architecture.
5. Confirm the frontend and backend local origins.
6. Add or update allowed-origin configuration.
7. Register FastAPI CORS middleware.
8. Configure frontend authentication requests to include credentials.
9. Add or update backend tests.
10. Add or update frontend tests where appropriate.
11. Test login manually in the browser.
12. Test `GET /auth/me` after login.
13. Test logout and confirm the cookie is cleared.
14. Test invalid login behavior.
15. Document configuration requirements.
16. Run the complete existing backend and frontend test suites.

## Definition of Done

This task is complete when the Lore Lens frontend can communicate with the FastAPI authentication endpoints through the browser, the HTTP-only JWT cookie works across the local frontend and backend origins, trusted origins are explicitly restricted, and all relevant automated and manual tests pass.
