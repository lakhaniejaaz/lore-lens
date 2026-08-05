import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import LoginPage from './LoginPage'
import HomePage from '../HomePage/HomePage'

interface MockResponse {
  ok: boolean
  status: number
  json: () => Promise<unknown>
}

function successResponse(): MockResponse {
  return {
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({ status: 'success', data: { user: { id: 1, username: 'lakhaniejaaz' } } }),
  }
}

function invalidCredentialsResponse(): MockResponse {
  return {
    ok: false,
    status: 401,
    json: () =>
      Promise.resolve({
        error: { code: 'invalid_credentials', message: 'Username or password is incorrect.' },
      }),
  }
}

function validationResponse(): MockResponse {
  return {
    ok: false,
    status: 422,
    json: () =>
      Promise.resolve({
        error: {
          code: 'validation_error',
          message: 'One or more fields are invalid.',
          fields: { username: 'Username must be between 3 and 50 characters.' },
        },
      }),
  }
}

function serverErrorResponse(): MockResponse {
  return {
    ok: false,
    status: 500,
    json: () =>
      Promise.resolve({ error: { code: 'internal_server_error', message: 'boom' } }),
  }
}

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/home" element={<HomePage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('rendering', () => {
    it('renders the sign-in form controls', () => {
      renderLoginPage()

      expect(screen.getByLabelText('Username')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Create User' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Forgot Password' })).toBeInTheDocument()
    })
  })

  describe('validation', () => {
    it('shows both required errors when both fields are empty and does not call the API', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(screen.getByText('Username is required.')).toBeInTheDocument()
      expect(screen.getByText('Password is required.')).toBeInTheDocument()
      expect(fetch).not.toHaveBeenCalled()
    })

    it('shows "Username is required." and moves focus to the username field when only username is missing', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(screen.getByText('Username is required.')).toBeInTheDocument()
      expect(screen.queryByText('Password is required.')).not.toBeInTheDocument()
      expect(screen.getByLabelText('Username')).toHaveFocus()
      expect(fetch).not.toHaveBeenCalled()
    })

    it('shows "Password is required." when only password is missing', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(screen.getByText('Password is required.')).toBeInTheDocument()
      expect(fetch).not.toHaveBeenCalled()
    })

    it('treats a whitespace-only username as missing', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), '   ')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(screen.getByText('Username is required.')).toBeInTheDocument()
      expect(fetch).not.toHaveBeenCalled()
    })

    it('trims the username and preserves the password exactly when submitting', async () => {
      vi.mocked(fetch).mockResolvedValue(successResponse() as unknown as Response)
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), '  lakhaniejaaz  ')
      await user.type(screen.getByLabelText('Password'), '  pass word  ')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1))
      const [, init] = vi.mocked(fetch).mock.calls[0]
      const body = JSON.parse(init!.body as string)
      expect(body).toEqual({ username: 'lakhaniejaaz', password: '  pass word  ' })
    })
  })

  describe('API requests', () => {
    it('calls POST /auth/login with credentials included', async () => {
      vi.mocked(fetch).mockResolvedValue(successResponse() as unknown as Response)
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1))
      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(url).toContain('/auth/login')
      expect(init).toMatchObject({ method: 'POST', credentials: 'include' })
    })

    it('submits the form when Enter is pressed while focused within it', async () => {
      vi.mocked(fetch).mockResolvedValue(successResponse() as unknown as Response)
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'strongPassword{Enter}')

      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1))
    })

    it('sends only one request when the button is clicked again while a submission is pending', async () => {
      let resolveFetch: (value: MockResponse) => void = () => {}
      const pending = new Promise<MockResponse>((resolve) => {
        resolveFetch = resolve
      })
      vi.mocked(fetch).mockReturnValue(pending as unknown as Promise<Response>)

      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')

      const signInButton = screen.getByRole('button', { name: 'Sign In' })
      await user.click(signInButton)
      await user.click(signInButton)

      expect(fetch).toHaveBeenCalledTimes(1)

      resolveFetch(successResponse())
      await waitFor(() => expect(screen.getByRole('heading', { name: 'Home Page' })).toBeInTheDocument())
    })
  })

  describe('successful login', () => {
    it('navigates to /home on a 200 response without reading document.cookie', async () => {
      vi.mocked(fetch).mockResolvedValue(successResponse() as unknown as Response)
      const cookieSpy = vi.spyOn(document, 'cookie', 'get')
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(await screen.findByRole('heading', { name: 'Home Page' })).toBeInTheDocument()
      expect(cookieSpy).not.toHaveBeenCalled()
    })
  })

  describe('error handling', () => {
    it('shows the backend-provided message for invalid credentials without navigating away', async () => {
      vi.mocked(fetch).mockResolvedValue(invalidCredentialsResponse() as unknown as Response)
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'wrongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(await screen.findByRole('alert')).toHaveTextContent('Username or password is incorrect.')
      expect(screen.getByLabelText('Username')).toBeInTheDocument()
      expect(screen.queryByRole('heading', { name: 'Home Page' })).not.toBeInTheDocument()
    })

    it('shows a field-level message when the backend returns a validation error', async () => {
      vi.mocked(fetch).mockResolvedValue(validationResponse() as unknown as Response)
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'ab')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(await screen.findByText('Username must be between 3 and 50 characters.')).toBeInTheDocument()
      expect(screen.queryByRole('heading', { name: 'Home Page' })).not.toBeInTheDocument()
    })

    it('shows the generic message on a server error and does not navigate', async () => {
      vi.mocked(fetch).mockResolvedValue(serverErrorResponse() as unknown as Response)
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong. Please try again.')
      expect(screen.queryByRole('heading', { name: 'Home Page' })).not.toBeInTheDocument()
    })

    it('shows the generic message on a network failure and restores the form', async () => {
      vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'))
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      const signInButton = screen.getByRole('button', { name: 'Sign In' })
      await user.click(signInButton)

      expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong. Please try again.')
      expect(screen.queryByRole('heading', { name: 'Home Page' })).not.toBeInTheDocument()
      await waitFor(() => expect(signInButton).not.toBeDisabled())
    })

    it('clears a previous form-level error before a new submission', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(invalidCredentialsResponse() as unknown as Response)
      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'wrongPassword')
      await user.click(screen.getByRole('button', { name: 'Sign In' }))
      expect(await screen.findByRole('alert')).toHaveTextContent('Username or password is incorrect.')

      let resolveFetch: (value: MockResponse) => void = () => {}
      const pending = new Promise<MockResponse>((resolve) => {
        resolveFetch = resolve
      })
      vi.mocked(fetch).mockReturnValueOnce(pending as unknown as Promise<Response>)

      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      expect(screen.queryByRole('alert')).not.toBeInTheDocument()

      resolveFetch(successResponse())
      await waitFor(() => expect(screen.getByRole('heading', { name: 'Home Page' })).toBeInTheDocument())
    })
  })

  describe('loading state', () => {
    it('disables and relabels the Sign In button while the request is pending, then restores it on failure', async () => {
      let resolveFetch: (value: MockResponse) => void = () => {}
      const pending = new Promise<MockResponse>((resolve) => {
        resolveFetch = resolve
      })
      vi.mocked(fetch).mockReturnValue(pending as unknown as Promise<Response>)

      const user = userEvent.setup()
      renderLoginPage()

      await user.type(screen.getByLabelText('Username'), 'lakhaniejaaz')
      await user.type(screen.getByLabelText('Password'), 'strongPassword')
      const signInButton = screen.getByRole('button', { name: 'Sign In' })
      await user.click(signInButton)

      expect(signInButton).toBeDisabled()
      expect(signInButton).toHaveTextContent('Signing In…')

      resolveFetch(invalidCredentialsResponse())

      await waitFor(() => expect(signInButton).not.toBeDisabled())
      expect(signInButton).toHaveTextContent('Sign In')
    })
  })

  describe('temporary buttons', () => {
    it('logs "Go to create user page" and does not navigate away when Create User is selected', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      const user = userEvent.setup()
      renderLoginPage()

      await user.click(screen.getByRole('button', { name: 'Create User' }))

      expect(consoleSpy).toHaveBeenCalledWith('Go to create user page')
      expect(fetch).not.toHaveBeenCalled()
      expect(screen.getByLabelText('Username')).toBeInTheDocument()
      consoleSpy.mockRestore()
    })

    it('logs "Go to forgot password page" and does not navigate away when Forgot Password is selected', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      const user = userEvent.setup()
      renderLoginPage()

      await user.click(screen.getByRole('button', { name: 'Forgot Password' }))

      expect(consoleSpy).toHaveBeenCalledWith('Go to forgot password page')
      expect(fetch).not.toHaveBeenCalled()
      expect(screen.getByLabelText('Username')).toBeInTheDocument()
      consoleSpy.mockRestore()
    })
  })

  describe('accessibility', () => {
    it('associates the required-field error message with its input', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await user.click(screen.getByRole('button', { name: 'Sign In' }))

      const usernameInput = screen.getByLabelText('Username')
      const errorMessage = screen.getByText('Username is required.')

      expect(usernameInput).toHaveAttribute('aria-invalid', 'true')
      expect(usernameInput.getAttribute('aria-describedby')).toBe(errorMessage.id)
    })
  })
})
