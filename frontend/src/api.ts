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

export type ForecastPoint = {
  dayAhead: number
  date: string
  median: number
  low: number
  high: number
}

export type Forecast = {
  ticker: string
  asOf: string
  madeAt: string
  model: string
  horizon: number
  lastClose: number
  points: ForecastPoint[]
}

/** The newest saved forecast for a ticker, or null when none has been made yet. */
export async function getForecast(ticker: string): Promise<Forecast | null> {
  const url = `/forecasts/${encodeURIComponent(ticker)}`
  const response = await fetch(url)
  if (response.status === 404) return null
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`)
  }
  return (await response.json()) as Forecast
}

export type PredictionRow = {
  date: string
  dayAhead: number
  predicted: number
  low: number
  high: number
  actual: number | null
  difference: number | null
  errorPct: number | null
  insideRange: boolean | null
}

export type PredictionSummary = {
  daysWithActual: number
  meanAbsErrorPct: number | null
  meanAbsDifference: number | null
  insideRange: number
}

export type Prediction = {
  ticker: string
  model: string
  originDate: string
  originClose: number
  rows: PredictionRow[]
  summary: PredictionSummary
  notes: string[]
}

/** A predicted price and range for each date from..to, scored against actual prices where they exist. */
export async function getPrediction(ticker: string, from: string, to: string): Promise<Prediction> {
  const url = `/predictions/${encodeURIComponent(ticker)}?from=${from}&to=${to}`
  const response = await fetch(url)
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(problem?.detail ?? `${url} returned ${response.status}`)
  }
  return (await response.json()) as Prediction
}
