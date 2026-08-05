# User Login Page Planning

## Goal

Create the frontend page that allows a user with an existing account to sign in to Lore Lens.

This feature covers frontend changes only. The backend login endpoint is already implemented, and no backend changes are required.

## User Story

As an existing user, I want to sign in to Lore Lens using my username and password so that I can access authenticated Lore Lens features.

## Tech Stack

- Frontend: React
- Language: TypeScript
- Backend API: FastAPI
- Routing: Existing frontend routing library and conventions
- API requests: Existing HTTP client or API request utilities
- Styling: Existing frontend styling approach and reusable components
- Testing: Existing frontend testing framework and conventions

## Figma design

### Signin page

./FigmaMocks/Sign In Screen.png

https://www.figma.com/design/oKXStg091VJ82UZaNsx9Lb/Lore-Lens-Mocks?node-id=43-18&t=9OYs8SBp18BH4FBk-1

### Reusable components 

./FigmaMocks/Reusable Components.png

https://www.figma.com/design/oKXStg091VJ82UZaNsx9Lb/Lore-Lens-Mocks?node-id=113-11&t=9OYs8SBp18BH4FBk-1


The implementation should follow the provided Figma design and reuse existing frontend components where appropriate.

## Existing Code Review

Before implementation, inspect the existing frontend, including:

- Project structure and architecture
- Existing routing configuration
- Existing page and component organization
- Existing reusable form components
- Existing text field components
- Existing error text field components
- Existing password field components
- Existing button components
- Existing API client or request utilities
- Existing environment configuration for the backend API URL
- Existing styling conventions
- Existing error-handling conventions
- Existing testing structure and conventions
- Existing dependency files

Existing code and components should be reused where appropriate rather than duplicating functionality.

## User Flow

1. The user navigates to `/login`.
2. The sign-in page is displayed.
3. The user enters a username and password.
4. The user selects the Sign In button or presses Enter while focused within the form.
5. The frontend validates that the required fields contain input.
6. If validation succeeds, the frontend calls `POST /auth/login`.
7. While the request is being processed, the form enters a loading state and additional submissions are prevented.
8. If the endpoint returns a successful `200` response, the user is navigated to `/home`.
9. If the endpoint returns an authentication or validation error, the error is displayed on the sign-in form.
10. If the endpoint returns a server error or the request cannot be completed, the documented generic error behaviour is used.

## Routes

### `/login`

Displays the user sign-in page.

The page should also be accessible when the user navigates directly to `/login`.

### `/home`

A temporary `/home` route should be created to verify successful login navigation.

The page should contain only:

```html
<h1>Home Page</h1>
```

Building the complete Home page is outside the scope of this feature.

### Root Route

Root-route authentication checks and redirect behaviour are outside the scope of this feature.

For this feature, successful login navigates directly to `/home`.

Authentication checks, protected routes, and redirects for missing or expired authentication will be implemented in a later Home page or application authentication-routing feature.

## API Contract

### Endpoint

`POST /auth/login`

### Request Body

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

### Request Requirements

- The username must be trimmed before submission.
- The password must be submitted exactly as entered.
- The password must not be trimmed, normalized, or otherwise modified.
- The request must use the existing configured backend API URL.
- The request must include credentials so the browser can receive and store the HTTP-only authentication cookie.

When using `fetch`, the request must include:

```typescript
credentials: "include"
```

When using Axios, the request must include:

```typescript
withCredentials: true
```

The implementation should follow whichever HTTP client is already used by the project.

### Successful Response

A successful login returns HTTP status `200`.

The frontend should use the existing backend response schema and should not depend on receiving the JWT in the response body.

The JWT is stored in an HTTP-only cookie and cannot be accessed directly through frontend JavaScript.

### Error Response

The implementation must inspect the existing backend login endpoint and use its actual error-response structure.

The frontend must not assume the response contains `error.message` unless that matches the existing backend contract.

FastAPI responses may use a `detail` property or another existing project-specific error structure.

## Form Fields

### Username

The Username field must:

- Allow the user to click or focus the field and enter a username.
- Display entered characters as plaintext.
- Have a maximum length of 50 characters.
- Use the input `maxLength` attribute.
- Allow all characters to be entered.
- Not apply frontend character-pattern validation.
- Be trimmed before submission.
- Treat an empty or whitespace-only value as missing.
- Use `autocomplete="username"`.

### Password

The Password field must:

- Allow the user to click or focus the field and enter a password.
- Hide entered characters using the browser's password-input behaviour.
- Use an input type of `password`.
- Have a maximum length of 255 characters.
- Use the input `maxLength` attribute.
- Allow all characters to be entered.
- Preserve whitespace exactly as entered.
- Not trim or normalize the password.
- Treat an empty value as missing.
- Use `autocomplete="current-password"`.

## Button Behaviour

### Sign In Button

When selected, the Sign In button must:

1. Clear any previous form-level API error.
2. Validate that the username and password contain input.
3. Display required-field errors when necessary.
4. Prevent the API request if client-side validation fails.
5. Call `POST /auth/login` when validation succeeds.
6. Include credentials with the request.
7. Enter a loading state while the request is running.
8. Prevent duplicate submissions while the request is running.
9. Navigate to `/home` when the endpoint returns `200`.
10. Restore the normal state if the request fails.

The form must also submit when the user presses Enter while focused within the form.

### Create User Button

The Create User page is outside the scope of this feature.

For this task, selecting the Create User button should not navigate away from the page.

It should temporarily log:

```typescript
console.log("Go to create user page");
```

### Forgot Password Button

The Forgot Password page is outside the scope of this feature.

For this task, selecting the Forgot Password button should not navigate away from the page.

It should temporarily log:

```typescript
console.log("Go to forgot password page");
```

## Validation Behaviour

### Missing Username

If the submitted username is empty or contains only whitespace:

- Do not call the login endpoint.
- Display the Username field using the reusable error text field component.
- Display the message `Username is required.`

### Missing Password

If the submitted password is empty:

- Do not call the login endpoint.
- Display the Password field using the reusable error text field component.
- Display the message `Password is required.`

### Multiple Missing Fields

If both fields are missing:

- Display an error for both fields.
- Do not call the login endpoint.
- Move focus to the first invalid field where supported by existing conventions.

### Clearing Field Errors

A field-level required error should be cleared when:

- The user corrects the field and resubmits the form, or
- Existing project conventions clear the error while the user types.

The implementation should follow the existing form-validation conventions consistently.

## Loading State

While the login request is in progress:

- The Sign In button must indicate that submission is in progress.
- The Sign In button must be disabled, or equivalent logic must prevent duplicate submissions.
- The username and password should remain visible in their current states.
- Only one login request may be active for a single submission.
- The loading state must end if the request fails.

## API Error Behaviour

### Invalid Credentials

If the backend returns an invalid-credentials response:

- Display the backend-provided safe error message using the reusable form-level error component.
- Display the error at the form level rather than assigning it specifically to the Username or Password field.
- Do not reveal whether the username or password was incorrect.
- Do not navigate away from `/login`.

### Backend Validation Error

If the backend returns a validation error:

- Use the existing frontend error-parsing conventions.
- Display a clear and safe error message.
- Do not navigate away from `/login`.

### Internal Server Error

If the endpoint returns HTTP status `500`:

- Navigate to the existing internal server error route if one already exists.
- If no internal server error route exists, display the following generic form-level error:

`Something went wrong. Please try again.`

A dedicated internal server error page should not be created unless it already exists or is explicitly added to the implementation scope.

### Network or Unexpected Error

If the request fails without a usable HTTP response, including network, timeout, CORS, or malformed-response failures:

- Display the generic form-level message `Something went wrong. Please try again.`
- Do not navigate to `/home`.
- Restore the form from its loading state.

### Error Reset Behaviour

Before each new login request:

- Clear any previous form-level API error.
- Revalidate the current field values.
- Preserve the user's entered values unless existing project conventions specify otherwise.

The password should remain entered after a failed login attempt unless the existing application follows a different established convention.

## Successful Login Behaviour

When `POST /auth/login` returns HTTP status `200`:

- Treat the login as successful.
- Do not attempt to read the HTTP-only JWT cookie through JavaScript.
- Navigate the user to `/home`.
- Use the existing router navigation conventions.
- Prefer replacing the current login history entry if supported by the existing routing approach so the Back button does not unnecessarily return to the submitted login form.

## Accessibility Requirements

The sign-in page must:

- Use a semantic HTML form.
- Use real `<label>` elements or an equivalent accessible association for each input.
- Associate validation messages with their corresponding fields.
- Use a real `<button>` element for the Sign In action.
- Support keyboard navigation.
- Support form submission using Enter.
- Provide a visible focus state consistent with the design system.
- Communicate loading and error states to assistive technology where supported by existing project conventions.
- Avoid using placeholder text as the only field label.
- Maintain sufficient colour contrast according to the existing design system.

## Reusable Components

The implementation should inspect and reuse existing components where appropriate, including:

- Standard text field
- Error text field
- Password text field
- Primary button
- Form-level error message
- Page layout
- Logo or branding
- Typography
- Loading indicator

New reusable components should only be created when the required behaviour cannot reasonably be supported by the existing components.

## Testing Requirements

Tests should follow the existing frontend testing framework and project conventions.

### Rendering Tests

Verify that:

- The `/login` page renders successfully.
- The Username field is displayed.
- The Password field is displayed.
- The Sign In button is displayed.
- The Create User button is displayed.
- The Forgot Password button is displayed.

### Validation Tests

Verify that:

- Submitting with both fields empty displays both required errors.
- Submitting without a username displays `Username is required.`
- Submitting without a password displays `Password is required.`
- A whitespace-only username is treated as missing.
- The API is not called when client-side validation fails.
- The username is trimmed before submission.
- The password is submitted without trimming or modification.

### API Request Tests

Verify that:

- A valid submission calls `POST /auth/login`.
- The correct username and password are sent.
- Credentials are included with the request.
- Only one request is sent per submission.
- Pressing Enter submits the form.

### Successful Login Tests

Verify that:

- A `200` response navigates the user to `/home`.
- The temporary `/home` page displays `Home Page`.
- The frontend does not attempt to retrieve the JWT from the response body or browser cookie APIs.

### Error Tests

Verify that:

- Invalid credentials display the backend-provided safe error.
- Invalid credentials do not navigate the user away from `/login`.
- A server error follows the defined internal server error behaviour.
- A network or unexpected error displays the generic error message.
- The loading state ends after a failed request.
- A previous API error is cleared before a new submission.

### Loading-State Tests

Verify that:

- The Sign In button enters a loading or disabled state during submission.
- Duplicate submissions are prevented while the request is pending.
- The button returns to its normal state after a failed request.

### Temporary Button Tests

Verify that:

- Selecting Create User logs `Go to create user page`.
- Selecting Forgot Password logs `Go to forgot password page`.
- Neither temporary button navigates away from `/login`.

## Acceptance Criteria

This feature is complete when:

- The sign-in page matches the provided Figma design.
- Existing reusable components are used where appropriate.
- The page is available at `/login`.
- The user can enter a username and password.
- Required-field validation works correctly.
- The username is trimmed before submission.
- The password is submitted unchanged.
- The login request includes browser credentials.
- Duplicate submissions are prevented.
- A successful login navigates to `/home`.
- The temporary `/home` route displays `Home Page`.
- Authentication errors are displayed safely at the form level.
- Server, network, and unexpected errors follow the documented behaviour.
- Create User and Forgot Password use their temporary console-log behaviour.
- Keyboard submission and accessibility requirements are supported.
- Automated frontend tests cover the required behaviours.
- Existing frontend tests continue to pass.
- No backend changes are made.

## Out of Scope

- User registration page
- Forgot Password page
- Complete Home page
- Password reset functionality
- Email-based login
- Social login
- Multi-factor authentication
- Remember Me functionality
- Authentication token storage changes
- Backend authentication changes
- Protected-route implementation beyond the temporary login-to-home navigation
- Automatic authentication checks for users who directly visit `/login`
- Full global authentication-state management unless already required by the existing frontend architecture

