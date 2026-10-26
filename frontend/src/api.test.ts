import { afterEach, describe, expect, it, vi } from 'vitest'
import { getForecast } from './api'

function replyWith(status: number, body: unknown = {}) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(body), { status })))
}

afterEach(() => vi.unstubAllGlobals())

describe('getForecast', () => {
  it('returns null when no forecast exists yet', async () => {
    replyWith(404)
    expect(await getForecast('AAPL')).toBeNull()
  })

  it('returns the forecast when there is one', async () => {
    replyWith(200, { ticker: 'AAPL', points: [] })
    expect(await getForecast('AAPL')).toMatchObject({ ticker: 'AAPL' })
  })

  it('still treats a server error as an error', async () => {
    replyWith(500)
    await expect(getForecast('AAPL')).rejects.toThrow('returned 500')
  })

  it('asks for the right address', async () => {
    replyWith(200, {})
    await getForecast('b rk')
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe('/forecasts/b%20rk')
  })
})
