 n# Planning for `GET /auth/me` — Retrieve Authenticated User

## Goal

Create a backend API endpoint that returns the currently authenticated user.

The endpoint will retrieve the JWT access token from the authentication cookie, validate and decode the token, extract the user ID, retrieve the corresponding user from the database, and return the user’s safe account information.

This planning document covers backend changes only.

## User Story

As an authenticated user, I want the application to retrieve my account information so that the frontend can confirm that I am logged in and display my user details.

## Tech Stack

- Frontend: React + TypeScript
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migration framework: Alembic
- JWT library: PyJWT
- Validation and response schemas: Pydantic
- Authentication method: JWT access token stored in an HTTP-only cookie

## Endpoint

- Method: `GET`
- Path: `/auth/me`
- Authentication required: Yes
- Request body: None
- Success status code: `200 OK`
- Response content type: `application/json`

## Authentication Requirements

The endpoint requires a valid JWT access token in the configured authentication cookie.

The endpoint must return an authentication error when:

- The authentication cookie is missing.
- The JWT is expired.
- The JWT signature is invalid.
- The JWT cannot be decoded.
- The JWT payload is missing the user ID.
- The user ID in the JWT is invalid.
- The user referenced by the JWT no longer exists.

## Request

### Headers

No custom request headers are required.

The client may send:

- `Accept: application/json`

For cross-origin frontend requests, the client must be configured to include credentials so that the browser sends the authentication cookie.

### Cookies

The request must contain the configured authentication cookie containing the JWT access token.

The endpoint must use the same:

- Cookie name
- JWT secret
- JWT algorithm
- Token payload structure
- Authentication configuration

as the registration, login, and logout endpoints.

### Request Body

The endpoint does not accept a request body.

Any user information must be determined from the JWT access token and database rather than from client-provided request data.

## Response

### Success Response

The endpoint returns `200 OK` with the currently authenticated user’s safe account information.

Example response:

```json
{
  "id": 1,
  "first_name": "Example",
  "last_name": "User",
  "username": "example_user",
  "email": "example@example.com",
  "created_at": "2026-07-29T12:00:00Z"
}
```

The response must not include:

- Password
- Plaintext password
- Password hash
- JWT access token
- Authentication cookie configuration
- Other private internal fields

### Error Responses

The endpoint returns `401 Unauthorized` when authentication cannot be completed.

Example error conditions include:

- Missing authentication cookie
- Expired JWT
- Invalid JWT
- Malformed JWT payload
- Missing user ID claim
- Invalid user ID claim
- User no longer exists

The error response should follow the existing API error-response conventions.

Example response:

```json
{
  "detail": "Not authenticated."
}
```

A `404 Not Found` response should not be returned when the user referenced by the JWT does not exist. This condition should be treated as an authentication failure to avoid exposing unnecessary account information.

## Authentication Flow

1. Receive the `GET /auth/me` request.
2. Read the JWT access token from the configured authentication cookie.
3. Return `401 Unauthorized` if the cookie is missing.
4. Decode and validate the JWT using the configured secret and algorithm.
5. Return `401 Unauthorized` if the token is expired, invalid, or cannot be decoded.
6. Extract the user ID from the expected JWT claim.
7. Return `401 Unauthorized` if the user ID claim is missing or invalid.
8. Query the database for the user matching the extracted user ID.
9. Return `401 Unauthorized` if the user does not exist.
10. Return `200 OK` with the safe user response.

## JWT Validation Requirements

The endpoint must:

- Read the token only from the configured authentication cookie.
- Validate the JWT signature.
- Use the configured JWT algorithm.
- Validate the token expiration time.
- Reject expired tokens.
- Reject tokens signed with an unexpected algorithm.
- Reject malformed or undecodable tokens.
- Verify that the expected user ID claim is present.
- Verify that the user ID claim can be converted to the expected user ID type.
- Never trust the user ID without successfully validating the token first.

The endpoint should use the same JWT claim structure created by the registration and login endpoints.

## Database Requirements

The endpoint must query the existing users table using the user ID extracted from the validated JWT.

The database query must:

- Use the existing SQLAlchemy database session dependency.
- Retrieve a user by primary key.
- Return only the user associated with the authenticated JWT.
- Treat a missing user as an authentication failure.

No database schema changes or Alembic migrations should be required.

The endpoint is read-only and must not commit, update, or delete any database records.

## Response Schema

The endpoint should return the existing safe user response schema used by the registration or login endpoint, provided it contains the required fields.

The response should include:

- `id`
- `first_name`
- `last_name`
- `username`
- `email`
- `created_at`

The response must not expose the user’s password hash or other internal authentication data.

## Validation Rules

The endpoint does not accept user-provided request data, so no request-body validation is required.

Authentication validation must confirm that:

- The authentication cookie exists.
- The JWT is valid and unexpired.
- The expected user ID claim exists.
- The user ID has the expected type or can be safely converted to it.
- A matching user exists in the database.

Unexpected or additional JWT claims should not affect the endpoint unless they conflict with required token validation.

## Security Considerations

- Read the JWT from the configured HTTP-only cookie rather than from the request body.
- Validate the JWT before trusting any value from its payload.
- Restrict decoding to the configured JWT algorithm.
- Do not return the JWT in the response body.
- Do not expose the password hash or other private database fields.
- Do not accept a user ID through the URL, query parameters, headers, or request body.
- Do not allow a client to request another user’s information by changing request data.
- Return a consistent authentication error for missing, invalid, expired, or unusable credentials.
- Avoid exposing whether a particular user ID exists.
- Do not log the raw JWT or authentication cookie value.
- Reuse existing cookie and JWT configuration to avoid inconsistent authentication behaviour.

## Error Handling

Authentication failures should use the project’s existing error-handling conventions.

The endpoint should return `401 Unauthorized` when:

- The authentication cookie is missing.
- The token is expired.
- The token signature is invalid.
- The token is malformed or cannot be decoded.
- The expected user ID claim is missing.
- The user ID claim is invalid.
- The user referenced by the token does not exist.

The endpoint should not expose internal PyJWT, SQLAlchemy, or application exception details in the response.

Unexpected database or server errors should follow the application’s existing internal-error handling conventions.

## Edge Cases

The implementation should account for:

- No authentication cookie being included.
- An empty authentication cookie.
- A malformed JWT.
- A JWT with an invalid signature.
- An expired JWT.
- A JWT signed with an unsupported algorithm.
- A JWT without the expected user ID claim.
- A JWT with a null or empty user ID claim.
- A JWT with a user ID in an invalid format.
- A valid JWT referencing a user that has been deleted.
- Additional unexpected claims in the JWT.
- A request containing a body even though the endpoint does not require one.
- A database error while retrieving the user.

## Test Cases

Tests should follow the existing project testing structure and conventions.

Tests should verify both the HTTP response and the returned response data.

### Successful Requests

Test that:

- A request with a valid authentication cookie returns `200 OK`.
- The response contains the authenticated user’s correct information.
- The response matches the expected user response schema.
- The response does not include the password hash.
- The endpoint returns the user identified by the JWT rather than another user.
- The endpoint does not modify the user or create new database records.

### Authentication Failures

Test that the endpoint returns `401 Unauthorized` when:

- The authentication cookie is missing.
- The authentication cookie is empty.
- The JWT is malformed.
- The JWT signature is invalid.
- The JWT is expired.
- The JWT uses an unexpected algorithm.
- The JWT is missing the expected user ID claim.
- The user ID claim is invalid.
- The JWT cannot otherwise be decoded or validated.

The tests should verify that authentication failure responses follow the existing API error format.

### Database and User State

Test that:

- A valid JWT referencing an existing user returns that user.
- A valid JWT referencing a nonexistent user returns `401 Unauthorized`.
- A valid JWT referencing a deleted user returns `401 Unauthorized`.
- The endpoint does not commit or alter database state.
- Unexpected database errors follow the existing application error-handling conventions.

## Existing Code to Reuse

The implementation should reuse existing code where appropriate, including:

- The authentication router used by registration, login, and logout.
- The configured authentication cookie name.
- JWT secret and algorithm settings.
- JWT decoding or validation helpers, if already implemented.
- The SQLAlchemy database session dependency.
- The existing `User` model.
- The existing safe user response schema.
- Existing authentication exceptions or error-response helpers.
- Existing test fixtures and user factory utilities.
- Existing test helpers for creating JWTs or authenticated clients.

If JWT validation logic currently exists only inside another endpoint, it may be appropriate to extract it into a reusable authentication dependency or helper.

## Files Expected to Change

Expected changes may include:

- The existing authentication router or route module.
- The existing authentication service, utility, or dependency module.
- The authentication test module.
- Shared test fixtures or helpers, if needed.

A new authentication dependency module may be created if the project does not already have an appropriate location for reusable current-user authentication logic.

No user-model changes, database migrations, or frontend changes should be required.

## Out of Scope

The following are outside the scope of this endpoint:

- User registration.
- User login.
- User logout.
- Refresh tokens.
- Token revocation or denylisting.
- Session storage in the database.
- Role-based authorization.
- Permission checks.
- Updating user account information.
- Deleting user accounts.
- Password changes or password resets.
- Email verification.
- Returning another user’s profile.
- Frontend authentication-state implementation.
- Automatically refreshing or replacing expired tokens.

## Acceptance Criteria

- `GET /auth/me` is available under the authentication router.
- The endpoint requires authentication.
- The endpoint reads the JWT from the configured authentication cookie.
- The JWT signature, algorithm, and expiration are validated.
- The user ID is extracted from the expected JWT claim.
- The user is retrieved from the database using the validated user ID.
- A valid authenticated request returns `200 OK`.
- The response contains the authenticated user’s safe account information.
- The response does not contain a password, password hash, or JWT.
- A missing cookie returns `401 Unauthorized`.
- An invalid or malformed JWT returns `401 Unauthorized`.
- An expired JWT returns `401 Unauthorized`.
- A missing or invalid user ID claim returns `401 Unauthorized`.
- A JWT referencing a nonexistent user returns `401 Unauthorized`.
- Existing project architecture, naming, and error-handling conventions are followed.
- Automated tests cover successful and unsuccessful authentication cases.
- All existing tests continue to pass.
- No database migration is introduced unless an unexpected requirement is discovered.

## Implementation Notes

The preferred implementation is to create or reuse a dependency that resolves the currently authenticated user.

The dependency should:

1. Read the JWT from the authentication cookie.
2. Validate and decode the JWT.
3. Extract and validate the user ID.
4. Retrieve the user from the database.
5. Return the user or raise the project’s standard `401 Unauthorized` exception.

The route can then depend on the resolved user and return it using the safe response schema.

This dependency can later be reused by other protected Lore Lens endpoints.

Implementation should remain focused on retrieving the current user and should not add refresh-token, authorization, or session-management behaviour.

## Open Questions and Assumptions

- Assume the JWT contains the user ID using the same claim created by the registration and login endpoints.
- Assume the JWT is stored using the same cookie name used by registration, login, and logout.
- Assume an existing safe user response schema can be reused.
- Assume all authentication failures should return the same general `401 Unauthorized` response.
- Confirm the exact name and type of the JWT user ID claim from the existing implementation.
- Confirm whether reusable JWT decoding logic already exists.
- Confirm the project’s standard authentication error message.
- Confirm whether the current authentication cookie should be cleared when the JWT is invalid, expired, or references a nonexistent user.
- Confirm whether requests containing an unnecessary body should be ignored or rejected according to existing FastAPI behaviour and project conventions.
