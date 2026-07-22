# Planning for POST /auth/register — create user and authenticate session

## Goal

Create a backend API endpoint that allows a new user to register with a username, first name, last name, email address, and password.

After the user is created successfully, the endpoint will authenticate the user by issuing a JWT access token in an HTTP-only cookie.

This planning document covers backend changes only.

## User Story

As a new user I want to be able to create an account so that I can access the Lore Lens features.

## Tech Stack
- Frontend: React + TypeScript
- Backend: FastAPI
- DB: PostgreSQL
- Migration Framework: Alembic
- JWT library: PyJWT
- Email validation: Pydantic `EmailStr`

## Registration Flow

1. Parse and validate the request.
2. Trim and normalize non-password fields.
3. Hash the password.
4. Create and add the user through SQLAlchemy.
5. Commit the transaction.
6. Refresh/read the created user if required.
7. Generate the JWT using the committed user's ID.
8. Set the HTTP-only authentication cookie.
9. Return the safe user response.

On Failure
- Roll back any active database transaction.
- Do not generate a token.
- Do not set a cookie.

## Database Requirements

- ORM: SQLAlchemy
- Migration framework: Alembic
- Email has a database-level unique constraint.
- Username has a database-level unique constraint.
- Email is stored lowercase.
- Username is stored lowercase.
- `hashed_password` is required.
- The database is the final authority for duplicate prevention.
- Registration is committed before the authentication cookie is returned.
- A failed transaction is rolled back.

## Endpoint(s)

- Method: POST
- Path: /auth/register
- Authentication required: No
- Content type: application/json

## Request Body 

```json
{
    "first_name": "",
    "last_name": "",
    "username": "",
    "email": "",
    "password": ""
}
```

## Response Example

### Success

- Status Code 201
- Returns Created User: Yes
- Returns auth token: No
- Automatically logs user in: Yes
- Sets cookie: Yes

```json
{
  "user": {
    "id": "",
    "first_name": "",
    "last_name": "",
    "username": "",
    "email": "",
    "created_at": ""
  }
}
```

### Errors

- Missing or invalid field
- Duplicate email
- Duplicate username
- Malformed JSON
- Password-hashing failure
- Database failure
- Unexpected server error

- Invalid or missing field: 422
- Malformed JSON: 422
- Duplicate email: 409
- Duplicate username: 409
- Password-hashing failure: 500
- Database failure: 500
- Unexpected server error: 500


invalid username length example
```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields are invalid.",
    "fields": {
      "username": "Username must be at least 3 characters."
    }
  }
}
```

duplicate email error example
```json
{
  "error": {
    "code": "duplicate_email",
    "message": "An account with this email already exists."
  }
}
```

duplicate username error example
```json
{
  "error": {
    "code": "duplicate_username",
    "message": "This username is already in use."
  }
}
```

internal error example
```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected error occurred."
  }
}
```


## Validation Rules

First name:
- Required: Yes
- Minimum length: 1
- Maximum length: 50
- Trim surrounding whitespace: Yes
- Reject whitespace-only values: Yes

Last name:
- Required: Yes
- Minimum length: 1
- Maximum length: 50
- Trim surrounding whitespace: Yes
- Reject whitespace-only values: Yes

Username:
- Required: Yes
- Minimum length: 3
- Maximum length: 50
- Allowed characters: Letters, numbers, underscores and hyphens
- Spaces allowed: No
- Case sensitivity: No 
- Comparison: `ejaaz` and `Ejaaz` are treated as the same username
- Storage: Store username in lowercase
- Trim surrounding whitespace: Yes
- Reject whitespace-only values: Yes
- Compared case-insensitively: Yes

Email:
- Required: Yes
- Minimum length: 1
- Maximum length: 255
- Trim surrounding whitespace: Yes
- Reject whitespace-only values: Yes
- Convert to lowercase: Yes
- Validation method: Pydantic `EmailStr`
- Case-insensitive uniqueness: Yes

Password:
- Required: Yes
- Minimum length: 8
- Maximum length: 255
- Trim or normalize: No
- Composition requirements, if any: No
- Spaces allowed: Yes
- Reject whitespace-only values: Yes

## Password Hashing

- Password-hashing library: `pwdlib[argon2]`
- Hashing algorithm: Argon2id
- Hash configuration: `PasswordHash.recommended()`
- Plaintext password never stored: True
- Plaintext password never logged: True
- Password hash never returned: True

## Authentication Behaviour

- Token type: JWT access token
- Token subject: Newly created user's ID
- Token returned in JSON: No
- Refresh token created: No
- User is authenticated immediately after registration: Yes
- Access-token expiration: 60 minutes
- Signing secret: Loaded from environment configuration
- Signing algorithm: HS256

## Cookie Configuration

- Cookie name: `access_token`
- Value: JWT access token
- HTTP-only: Yes
- Secure: Yes in production
- SameSite: `Lax`
- Path: `/`
- Max age: Same as access-token expiration
- Available to frontend JavaScript: No

**CSRF protection: Not implemented in this issue; required before production deployment if cookie-authenticated state-changing endpoints are added.** 

## Cookie Behaviour 

- Secure: Configurable by environment
- Secure cookie in local development over HTTP: No
- Secure cookie in production over HTTPS: Yes

## JWT Claims

- `sub`: Newly created user's ID, represented as a string
- `iat`: Token creation time
- `exp`: Token expiration time
- Additional personal information in token: None

## Edge Cases

- Email with different capitalization: convert to lower case and check for duplicate
- Username with different capitalization: convert to lower case and check for duplicate
- Leading/trailing whitespace in first name, last name, username and email: Trim before validation.
- Leading/trailing whitespace in password: Preserve exactly as submitted. Never trim or normalize passwords.
- Whitespace-only password: Reject with 422.
- Empty or whitespace-only values: reject and throw error 422
- Extremely long input: reject and throw error 422
- Two simultaneous duplicate registrations: DB has unique constraint. Second one should be rejected with error 409
- Unexpected request fields: Throw error 422
- Database unavailable: Return error 500 and nothing else. No sensitive DB fields should be returned 
- Hashing failure: Return 500, do not create user entry
- Malformed JSON: Return 422 using the documented validation-error structure.

## Test Cases

- Successful registration
- Correct response structure
- Correct cookie configuration
- Valid token is created
- Password is hashed
- Password/hash are not returned
- Duplicate email rejected
- Duplicate username rejected
- Case-insensitive duplicates rejected
- Invalid email rejected
- Weak password rejected (min length not met)
- Missing fields rejected
- Database uniqueness constraint enforced
- Access token identifies the newly created user by ID.
- Access token is not included in the JSON body.
- Cookie is HTTP-only.
- Cookie path and SameSite values are correct.
- Secure cookie behaviour follows the environment.
- No cookie is set when registration fails.
- Unexpected fields are rejected.
- Password whitespace is preserved.
- Names, username and email are trimmed correctly.
- User is not created if hashing fails.
- Failed database transactions are rolled back.
- First name is required and rejects whitespace-only input.
- Last name is required and rejects whitespace-only input.
- Username is stored lowercase.
- Email is stored lowercase.
- Password is not trimmed or normalized.
- Whitespace-only password is rejected.
- Malformed JSON returns the documented 422 response.
- Database errors do not expose internal details.
- Hashing errors do not expose internal details.
- A JWT and cookie are created only after a successful commit.
- A duplicate database constraint error triggers a rollback.
- JWT includes `sub`, `iat` and `exp`.
- JWT does not include password, password hash or unnecessary personal data.

## Definition of Done

- Alembic migration runs successfully.
- Endpoint returns 201 for valid registration.
- User is saved correctly.
- Password is securely hashed.
- Authentication cookie is set.
- Duplicate users cannot be created.
- All automated tests pass.
- API documentation reflects the endpoint.

## Out of Scope 

- Login endpoint
- Logout endpoint
- Refresh tokens
- Email verification
- Password reset
- OAuth or social login
- Roles and permissions
- Frontend registration form
- Production CSRF implementation
- Account deletion
- Protected endpoints that read and validate the authentication cookie