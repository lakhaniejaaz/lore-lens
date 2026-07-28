# Planning for `POST /auth/login`

## Goal

Create a backend API endpoint that allows a user with an existing account to authenticate using their username and password.

After successful authentication, the backend will issue a JWT access token in an HTTP-only cookie.

Redirecting or navigating the user to the Lore Lens homepage is a frontend responsibility and is outside the scope of this document.

This planning document covers backend changes only.

## User Story

As an existing user, I want to log in to Lore Lens using my username and password so that I can access authenticated Lore Lens features.

## Tech Stack

- Frontend: React + TypeScript
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migration framework: Alembic
- JWT library: PyJWT
- Password hashing library: Same library used by registration

## Login Flow

1. Parse and validate the request body.
2. Trim and normalize the username to lowercase.
3. Query the database for a user with the normalized username.
4. Verify the submitted password against the user's stored password hash.
5. Generate a JWT access token using the user's ID.
6. Set the JWT in the HTTP-only authentication cookie.
7. Return a successful response containing the authenticated user's safe public fields.

### On Failure

- Do not authenticate the user.
- Do not generate an authentication token.
- Do not set an authentication cookie.
- Do not reveal whether the username or password was incorrect.
- Do not return the stored password hash or other sensitive database fields.

## Database Requirements

No database schema changes or Alembic migration should be required for this feature.

The endpoint will query against the existing users table created for registration.

### Required Existing Fields

- `id`
- `username`
- `hashed_password`
- Other safe user fields required by the response schema

### Existing Assumptions

- Username is stored in lowercase.
- Username has a database-level unique constraint.
- `hashed_password` is required.
- Plaintext passwords are never stored.
- Password hashes are never returned in an API response.

**Login is a read operation and should not normally require a database commit or rollback.**

## Endpoint

- Method: `POST`
- Path: `/auth/login`
- Authentication required: No
- Content type: `application/json`
- Success status: `200 OK`

## Request Body 

```json
{
    "username": "ejaaz_lakhani",
    "password": "strongPassword"
}
```

## Response Example

### Success

- Status code: `200 OK`
- Returns authentication token in JSON: No
- Authenticates user: Yes
- Sets authentication cookie: Yes

```json
{
  "status": "success",
  "data": {
    "user": {
      "id": "user-id",
      "first_name": "Ejaaz",
      "last_name": "Lakhani",
      "username": "ejaaz_lakhani",
      "email": "example@example.com",
      "created_at": "2026-07-27T12:00:00Z"
    }
  }
}
```

**The response should use the same safe user response schema used by the registration endpoint where practical.**

**The JWT must not be included in the JSON response because it is stored in an HTTP-only cookie.**

## Authentication Cookie

The login endpoint should use the same cookie name and configuration as the registration endpoint.

Expected properties:

- `HttpOnly`: enabled
- `Secure`: enabled in production
- `SameSite`: consistent with the application's deployment architecture
- `Path`: `/`
- Expiration or maximum age: consistent with the JWT expiration time

The cookie should only be added after the credentials have been successfully verified and the JWT has been generated.

## Error Responses

### Request Validation Error

Examples:

- Missing username
- Missing password
- Empty username
- Empty password
- Whitespace-only username
- Incorrect field type
- Unexpected additional field
- Malformed JSON

Status code: `422 Unprocessable Entity`

FastAPI and Pydantic may return the standard validation-error response unless the application uses a custom global error format.

### Invalid Credentials

This response must be identical when:

- The username does not exist.
- The password is incorrect.
- Both the username and password are incorrect.

Status code: `401 Unauthorized`

```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Username or password is incorrect."
  }
}
```

The response must not indicate which credential was incorrect.

### Internal Server Error

Examples:

- Database unavailable
- Password-verification failure
- JWT-generation failure
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

Internal exception details must not be returned to the client.

## Security Requirements

- Use a generic error response for all invalid credential combinations.
- Never return or log plaintext passwords.
- Never return the stored password hash.
- Use the password-hashing library's secure verification function.
- Generate the JWT only after successful password verification.
- Use the user's stable database ID as the JWT subject or primary identity claim.
- Apply the same JWT claims, expiration settings, signing algorithm, and secret configuration used by registration.
- Set the JWT only in the configured HTTP-only cookie.
- Do not log complete JWT values.
- Avoid exposing database or stack-trace details in error responses.

**The system must return the same response whether the username or password is incorrect. An unsuccessful login must not reveal which credential was invalid.**


## Validation Rules

### Username
- Required: Yes
- Type: String
- Trim leading and trailing whitespace: Yes
- Convert to lowercase before database lookup: Yes
- Reject empty or whitespace-only values: Yes
- Enforce the same general length constraints used during registration where practical

### Password
- Required: Yes
- Type: String
- Trim or normalize: No
- Preserve leading and trailing whitespace exactly as submitted: Yes
- Reject an empty string: Yes
- A whitespace-only password must not be trimmed or automatically treated as an empty password.
- If it does not match the stored password hash, return `401 Unauthorized`.

## Edge Cases

### Username Uses Different Capitalization

Normalize the submitted username to lowercase before querying the database.

Example:

- Stored username: `example_user`
- Submitted username: `Example_User`
- Expected result: The account is found.

### Username Contains Leading or Trailing Whitespace

Trim the username before normalization and lookup.

Example:

- Submitted username: `"  example_user  "`
- Normalized username: `"example_user"`

### Password Contains Leading or Trailing Whitespace

Preserve the password exactly as submitted.

A password containing whitespace may only succeed when that whitespace is part of the user's actual password.

### Username Does Not Exist

Return the generic `401 Unauthorized` invalid-credentials response.

Do not reveal that the username does not exist.

### Password Is Incorrect

Return the same generic `401 Unauthorized` response used for a nonexistent username.

### Database Is Unavailable

Return `500 Internal Server Error`.

Do not set an authentication cookie or return sensitive database details.

### Password Verification Fails Unexpectedly

Return `500 Internal Server Error`.

Do not generate a JWT or set an authentication cookie.

### JWT Generation Fails

Return `500 Internal Server Error`.

Do not set an authentication cookie.

## Test Cases

### Successful Authentication

- Correct username and password return `200`.
- Username lookup is case-insensitive.
- Leading and trailing username whitespace is ignored.
- Response contains only safe user fields.
- Response does not contain a JWT.
- HTTP-only authentication cookie is set.
- JWT contains the correct user identity.
- JWT expiration and claims match the registration implementation.

### Invalid Credentials

- Incorrect username with an otherwise valid password returns `401`.
- Correct username with an incorrect password returns `401`.
- Incorrect username and incorrect password return `401`.
- All invalid credential combinations return the same public response.
- No authentication cookie is set.
- No JWT is returned.

### Request Validation

- Missing username returns `422`.
- Missing password returns `422`.
- Empty username returns `422`.
- Empty password returns `422`.
- Whitespace-only username returns `422`.
- Unexpected request fields return `422` when extra fields are forbidden.
- Malformed JSON returns `422`.

### Password Handling

- Password is not trimmed before verification.
- A password with incorrect added whitespace returns `401`.
- Plaintext password is not returned or logged.
- Stored password hash is not returned.
- Whitespace-only password is preserved during verification and returns `401` when it does not match.

### Internal Failures

- Database failure returns `500`.
- Unexpected password-verification failure returns `500`.
- JWT-generation failure returns `500`.
- Internal failures do not set an authentication cookie.
- Internal failures do not expose exception or database details.

## Definition of Done

- `POST /auth/login` is available without prior authentication.
- Valid credentials return `200 OK`.
- Valid credentials result in an authentication cookie being set.
- The JWT uses the authenticated user's database ID.
- The JWT is not returned in the JSON response.
- The response contains only safe user fields.
- Incorrect credentials return a generic `401 Unauthorized` response.
- Missing or invalid request fields return `422`.
- Passwords are verified securely, are never normalized, and are never persisted, returned, or logged in plaintext.
- Failure responses do not set an authentication cookie.
- All automated tests pass.
- API documentation reflects the endpoint contract.

## Out of Scope

- Frontend login form
- Frontend navigation or homepage redirect
- Logout endpoint
- Refresh tokens
- Email-based login
- Email verification
- Password reset
- OAuth or social login
- Roles and permissions
- Account deletion
- Protected endpoints that read and validate the authentication cookie
- Production CSRF implementation
- Rate limiting or account lockout