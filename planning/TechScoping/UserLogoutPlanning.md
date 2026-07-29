# Planning for `POST /auth/logout`

## Goal

Create a backend API endpoint that logs a user out of Lore Lens by clearing the JWT authentication cookie.

After a successful request, the browser should no longer send the existing authentication cookie with future requests.

Redirecting or navigating to the Lore Lens sign-in page is a frontend responsibility and is outside the scope of this document.

This planning document covers backend changes only.

## User Story

As a user, I want to log out of Lore Lens so that the current browser session can no longer access my account.

## Tech Stack

- Frontend: React + TypeScript
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migration framework: Alembic
- JWT library: PyJWT
- Authentication mechanism: JWT stored in an HTTP-only cookie

## Logout Flow

1. Receive the logout request.
2. Create a successful response.
3. Clear the JWT authentication cookie using the same cookie name, path, domain, and relevant security configuration used when the cookie was created.
4. Return `200 OK`.

The endpoint does not require authentication because it should return a successful response and attempt to clear the authentication cookie even when the cookie is missing, expired, malformed, or otherwise invalid.

The endpoint should remain successful when:

- The authentication cookie is missing.
- The JWT is expired.
- The JWT is malformed or invalid.
- The user represented by the JWT no longer exists.
- Logout is called more than once.

This makes logout idempotent: calling it multiple times produces the same logged-out result.

### On Failure

If an unexpected application error prevents the logout response from being created:

- Return the application's standard internal-server-error response.
- Do not expose internal exception details or stack traces.

## Database Requirements

No database reads, writes, schema changes, or Alembic migrations should be required for this feature.

### Existing Assumptions

- Authentication uses a stateless JWT stored in an HTTP-only cookie.
- The application does not currently maintain server-side sessions.
- The application does not currently maintain a revoked-token denylist.
- Logging out invalidates the current browser session by deleting its authentication cookie.
- A previously issued JWT is not invalidated server-side and remains cryptographically valid until it expires.
- The logout response must use cookie settings compatible with those used by registration and login.

## Endpoint

- Method: `POST`
- Path: `/auth/logout`
- Authentication required: No
- Request body: None
- Success status: `200 OK`

The endpoint does not require authentication because it should still be possible to clear an expired, malformed, or otherwise unusable authentication cookie.

## Request Body

No request body is required.

The endpoint should not accept a user ID.

The backend does not need to identify, retrieve, or validate the user to remove the authentication cookie.

## Response Example

### Success

- Status code: `200 OK`
- Returns authentication token in JSON: No
- Returns user information: No
- Authenticates user: No
- Clears authentication cookie: Yes

```json
{
  "status": "success"
}
```

The response does not need to use the safe user response schema because logout does not return user information.

## Cookie Requirements

The response must delete or expire the JWT authentication cookie.

Cookie deletion must use configuration compatible with the cookie issued by registration and login, including where applicable:

- Cookie name
- Path
- Domain
- `HttpOnly`
- `Secure`
- `SameSite`

The response should expire the cookie immediately, such as by using an expired date or a non-positive maximum age.

The implementation should reuse the application's existing authentication-cookie name and configuration rather than duplicating cookie values where practical.

## Error Responses

### Request Validation Error

Because the endpoint has no request body or request parameters, normal logout requests should not produce field-validation errors.

Malformed HTTP requests may still be handled by FastAPI or the application's global error handlers.

Unexpected JSON fields do not need to be validated unless the endpoint explicitly defines an empty request schema.

### Internal Server Error

Examples:

- Unexpected response-generation failure
- Unexpected application error

Status code: `500 Internal Server Error`

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected error occurred."
  }
}
```

Internal exception details and stack traces must not be returned to the client.

## Security Requirements

- Clear the authentication cookie using settings compatible with the original cookie.
- Do not return the JWT or its contents.
- Do not return user information.
- Do not expose database details, exception details, or stack traces.
- Do not require or trust a user ID supplied by the client.
- Do not reveal whether the request contained a valid, invalid, expired, or missing token.
- Preserve the existing cookie security configuration used by registration and login.

## Validation Rules

There are no request fields to validate.

## Edge Cases

### Authentication Cookie Is Missing

- Return `200 OK`.
- Return the normal success response.
- Include the cookie-clearing instruction in the response where practical.

### Authentication Cookie Is Expired

- Return `200 OK`.
- Clear the authentication cookie.
- Do not return an authentication error.

### Authentication Cookie Is Malformed or Invalid

- Return `200 OK`.
- Clear the authentication cookie.
- Do not expose token-validation details.

### Logout Is Called Multiple Times

- Return `200 OK` for every request.
- Return the same response body for every request.
- Preserve the same cookie-clearing behavior.

### User No Longer Exists

- Return `200 OK`.
- Clear the authentication cookie.
- Do not query the database solely to confirm that the user exists.

## Test Cases

### Successful Logout With Authentication Cookie

- Return `200 OK`.
- Return the expected success response.
- Clear the authentication cookie.
- Verify that cookie deletion uses the expected cookie name.
- Verify that cookie deletion uses the expected path and domain configuration where applicable.
- Verify that no database operation is performed.

### Logout Without Authentication Cookie

- Return `200 OK`.
- Return the same success response.
- Do not return `401 Unauthorized`.

### Logout With Expired Authentication Cookie

- Return `200 OK`.
- Clear the authentication cookie.
- Do not expose expiration details.

### Logout With Invalid Authentication Cookie

- Return `200 OK`.
- Clear the authentication cookie.
- Do not expose JWT-validation details.

### Repeated Logout

- Multiple logout requests each return `200 OK`.
- Each response follows the same response contract.
- Each response preserves the cookie-clearing behavior.

### Response Security

- The response does not contain a JWT.
- The response does not contain user information.
- The response does not expose whether the previous cookie was valid.
- Internal exception details are not exposed.

### Unexpected Application Error

- Return `500 Internal Server Error`.
- Return the application's generic internal-error response.
- Do not return stack traces or internal exception messages.

## Definition of Done

- `POST /auth/logout` is available.
- The endpoint requires no request body.
- The endpoint does not require authentication.
- The endpoint returns `200 OK` whether the authentication cookie is valid, expired, invalid, or missing.
- The JWT authentication cookie is cleared using configuration compatible with registration and login.
- The endpoint does not read from or write to the database.
- The response does not contain a JWT.
- The response does not contain user information.
- Unexpected internal errors use the application's standard generic error response.
- All automated tests pass.
- API documentation reflects the endpoint contract.

## Out of Scope

- Frontend logout button or form
- Frontend navigation
- Sign-in-page redirect
- Server-side JWT revocation
- Revoked-token denylist
- Refresh-token revocation
- Logging out sessions on other devices or browsers
- Changing JWT expiration settings
- Database schema changes
