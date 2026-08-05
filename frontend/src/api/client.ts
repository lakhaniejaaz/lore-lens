const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8080'

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    fields?: Record<string, string>
  }
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; kind: 'validation'; message: string; fields?: Record<string, string> }
  | { ok: false; kind: 'auth'; message: string }
  | { ok: false; kind: 'server'; message: string }
  | { ok: false; kind: 'network'; message: string }

const GENERIC_ERROR_MESSAGE = 'Something went wrong. Please try again.'

// Maps the backend's {error:{code,message,fields}} envelope onto a typed
// result so callers never parse raw fetch Responses themselves.
export async function apiRequest<T>(path: string, body: unknown): Promise<ApiResult<T>> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body),
    })
  } catch {
    return { ok: false, kind: 'network', message: GENERIC_ERROR_MESSAGE }
  }

  if (response.ok) {
    try {
      const data = (await response.json()) as T
      return { ok: true, data }
    } catch {
      return { ok: false, kind: 'network', message: GENERIC_ERROR_MESSAGE }
    }
  }

  if (response.status === 500) {
    return { ok: false, kind: 'server', message: GENERIC_ERROR_MESSAGE }
  }

  let parsed: ApiErrorBody | null = null
  try {
    parsed = (await response.json()) as ApiErrorBody
  } catch {
    return { ok: false, kind: 'network', message: GENERIC_ERROR_MESSAGE }
  }

  const message = parsed?.error?.message ?? GENERIC_ERROR_MESSAGE

  if (response.status === 401) {
    return { ok: false, kind: 'auth', message }
  }

  if (response.status === 422) {
    return { ok: false, kind: 'validation', message, fields: parsed?.error?.fields }
  }

  return { ok: false, kind: 'server', message: GENERIC_ERROR_MESSAGE }
}
