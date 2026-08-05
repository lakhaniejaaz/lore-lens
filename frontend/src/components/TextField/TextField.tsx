import type { InputHTMLAttributes, Ref } from 'react'
import './TextField.css'

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  id: string
  label: string
  error?: string
  inputRef?: Ref<HTMLInputElement>
}

function TextField({ id, label, error, inputRef, className, ...inputProps }: TextFieldProps) {
  const errorId = `${id}-error`

  return (
    <div className="text-field">
      <label
        className={`text-field__label${error ? ' text-field__label--error' : ''}`}
        htmlFor={id}
      >
        {label}
      </label>
      <input
        id={id}
        ref={inputRef}
        className={`text-field__input${error ? ' text-field__input--error' : ''}${className ? ` ${className}` : ''}`}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...inputProps}
      />
      {error && (
        <p className="text-field__error" id={errorId}>
          {error}
        </p>
      )}
    </div>
  )
}

export default TextField
