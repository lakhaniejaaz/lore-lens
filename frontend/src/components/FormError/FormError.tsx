import './FormError.css'

interface FormErrorProps {
  message: string
}

function FormError({ message }: FormErrorProps) {
  return (
    <p className="form-error" role="alert">
      {message}
    </p>
  )
}

export default FormError
