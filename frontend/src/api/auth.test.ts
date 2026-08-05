import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { login } from './auth'

function mockFetchOnce(response: { ok: boolean; status: number; json?: () => Promise<unknown> }) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: response.ok,
      status: response.status,
      json: response.json ?? (() => Promise.resolve({})),
    }),
  )
}

describe('login', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends a POST request with credentials included and the given username/password', async () => {
    mockFetchOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'success', data: { user: { id: 1 } } }),
    })

    await login('lakhaniejaaz', 'strongPassword')

    expect(fetch).toHaveBeenCalledTimes(1)
    const [url, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toContain('/auth/login')
    expect(init).toMatchObject({
      method: 'POST',
      credentials: 'include',
    })
    expect(JSON.parse(init.body as string)).toEqual({
      username: 'lakhaniejaaz',
      password: 'strongPassword',
    })
  })

  it('returns ok data on a 200 response', async () => {
    const user = { id: 1, username: 'lakhaniejaaz' }
    mockFetchOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'success', data: { user } }),
    })

    const result = await login('lakhaniejaaz', 'strongPassword')

    expect(result).toEqual({
      ok: true,
      data: { status: 'success', data: { user } },
    })
  })

  it('maps a 401 invalid-credentials response to kind "auth" using the backend message', async () => {
    mockFetchOnce({
      ok: false,
      status: 401,
      json: () =>
        Promise.resolve({
          error: { code: 'invalid_credentials', message: 'Username or password is incorrect.' },
        }),
    })

    const result = await login('lakhaniejaaz', 'wrong')

    expect(result).toEqual({
      ok: false,
      kind: 'auth',
      message: 'Username or password is incorrect.',
    })
  })

  it('maps a 422 validation response to kind "validation" with fields', async () => {
    mockFetchOnce({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          error: {
            code: 'validation_error',
            message: 'One or more fields are invalid.',
            fields: { username: 'Username is required.' },
          },
        }),
    })

    const result = await login('', 'strongPassword')

    expect(result).toEqual({
      ok: false,
      kind: 'validation',
      message: 'One or more fields are invalid.',
      fields: { username: 'Username is required.' },
    })
  })

  it('maps a 500 response to kind "server" with the generic message regardless of body', async () => {
    mockFetchOnce({
      ok: false,
      status: 500,
      json: () =>
        Promise.resolve({ error: { code: 'internal_server_error', message: 'leaked detail' } }),
    })

    const result = await login('lakhaniejaaz', 'strongPassword')

    expect(result).toEqual({
      ok: false,
      kind: 'server',
      message: 'Something went wrong. Please try again.',
    })
  })

  it('maps a network failure to kind "network" with the generic message', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    )

    const result = await login('lakhaniejaaz', 'strongPassword')

    expect(result).toEqual({
      ok: false,
      kind: 'network',
      message: 'Something went wrong. Please try again.',
    })
  })
})
