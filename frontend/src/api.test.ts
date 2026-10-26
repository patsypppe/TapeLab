import { afterEach, describe, expect, it, vi } from 'vitest'
import { getForecast, getPrediction } from './api'

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

describe('getPrediction', () => {
  it('asks for the ticker and the dates', async () => {
    replyWith(200, { rows: [] })
    await getPrediction('aapl', '2026-10-01', '2026-10-05')
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe('/predictions/aapl?from=2026-10-01&to=2026-10-05')
  })

  it('shows the explanation the server gives for a bad request', async () => {
    replyWith(400, { detail: 'from must not be after to' })
    await expect(getPrediction('AAPL', '2026-10-09', '2026-10-01')).rejects.toThrow('from must not be after to')
  })

  it('falls back to the status when the error has no explanation', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('oops', { status: 500 })))
    await expect(getPrediction('AAPL', '2026-10-01', '2026-10-05')).rejects.toThrow('returned 500')
  })
})
