import type { ButtonHTMLAttributes } from 'react'
import './Button.css'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'text'
  loading?: boolean
  loadingLabel?: string
}

function Button({
  variant = 'primary',
  loading = false,
  loadingLabel = 'Loading…',
  disabled,
  children,
  className,
  ...buttonProps
}: ButtonProps) {
  return (
    <button
      type="button"
      className={`button button--${variant}${className ? ` ${className}` : ''}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...buttonProps}
    >
      {loading ? loadingLabel : children}
    </button>
  )
}

export default Button
