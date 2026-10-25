export type Price = {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type Reason = {
  analyst: string
  score: number
  rationale: string
}

export type Decision = {
  id: number
  ticker: string
  decidedFor: string
  decidedAt: string
  position: number
  reasons: Reason[]
  config: Record<string, unknown>
  filingId: number | null
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`)
  }
  return (await response.json()) as T
}

export const getPrices = (ticker: string) =>
  getJson<Price[]>(`/prices/${encodeURIComponent(ticker)}`)

export const getDecisions = () => getJson<Decision[]>('/decisions')
