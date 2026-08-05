import { useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import TextField from '../../components/TextField/TextField'
import Button from '../../components/Button/Button'
import FormError from '../../components/FormError/FormError'
import { login } from '../../api/auth'
import './LoginPage.css'

interface FieldErrors {
  username?: string
  password?: string
}

const GENERIC_ERROR_MESSAGE = 'Something went wrong. Please try again.'

function LoginPage() {
  const navigate = useNavigate()
  const usernameRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    // Guards against a duplicate in-flight request regardless of how
    // submission was triggered (click vs. Enter key).
    if (isSubmitting) {
      return
    }

    setFormError(null)

    const trimmedUsername = username.trim()
    const isUsernameMissing = trimmedUsername.length === 0
    const isPasswordMissing = password.length === 0

    if (isUsernameMissing || isPasswordMissing) {
      const nextFieldErrors: FieldErrors = {}
      if (isUsernameMissing) {
        nextFieldErrors.username = 'Username is required.'
      }
      if (isPasswordMissing) {
        nextFieldErrors.password = 'Password is required.'
      }
      setFieldErrors(nextFieldErrors)
      ;(isUsernameMissing ? usernameRef : passwordRef).current?.focus()
      return
    }

    setFieldErrors({})
    setIsSubmitting(true)

    const result = await login(trimmedUsername, password)

    if (result.ok) {
      navigate('/home', { replace: true })
      return
    }

    if (result.kind === 'validation' && result.fields) {
      setFieldErrors({
        username: result.fields.username,
        password: result.fields.password,
      })
      if (!result.fields.username && !result.fields.password) {
        setFormError(result.message)
      }
    } else {
      setFormError(result.message ?? GENERIC_ERROR_MESSAGE)
    }

    setIsSubmitting(false)
  }

  function handleCreateUser() {
    console.log('Go to create user page')
  }

  function handleForgotPassword() {
    console.log('Go to forgot password page')
  }

  return (
    <main className="login-page">
      <div className="login-card">
        <h1 className="login-card__title">Lore Lens</h1>
        <p className="login-card__subtitle">Sign in to your account</p>

        <form className="login-card__form" onSubmit={handleSubmit} noValidate>
          <TextField
            id="username"
            label="Username"
            placeholder="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            error={fieldErrors.username}
            maxLength={50}
            autoComplete="username"
            inputRef={usernameRef}
          />
          <TextField
            id="password"
            label="Password"
            type="password"
            placeholder="********"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={fieldErrors.password}
            maxLength={255}
            autoComplete="current-password"
            inputRef={passwordRef}
          />

          {formError && <FormError message={formError} />}

          <Button
            type="submit"
            variant="primary"
            className="login-card__submit"
            loading={isSubmitting}
            loadingLabel="Signing In…"
          >
            Sign In
          </Button>

          <div className="login-card__actions">
            <Button variant="secondary" onClick={handleCreateUser}>
              Create User
            </Button>
            <Button variant="text" onClick={handleForgotPassword}>
              Forgot Password
            </Button>
          </div>
        </form>
      </div>
    </main>
  )
}

export default LoginPage
