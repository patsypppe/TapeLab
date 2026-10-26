import { useEffect, useState } from 'react'
import { getDecisions, getForecast, getPrices, type Decision, type Forecast, type Price } from './api'
import { DecisionsTable } from './DecisionsTable'
import { ForecastTable } from './ForecastTable'
import { PredictionPanel } from './PredictionPanel'
import { PriceChart } from './PriceChart'
import { PricesTable } from './PricesTable'

const TICKERS = ['AAPL', 'MSFT', 'NVDA']
const REFRESH_MS = 30_000

export default function App() {
  const [ticker, setTicker] = useState('AAPL')
  const [typed, setTyped] = useState('')
  const [decisions, setDecisions] = useState<Decision[] | null>(null)
  const [prices, setPrices] = useState<Price[] | null>(null)
  const [forecast, setForecast] = useState<Forecast | null>(null)
  const [error, setError] = useState('')
  const [updated, setUpdated] = useState('never')

  useEffect(() => {
    let cancelled = false // set when the ticker changes, so a slow old response cannot overwrite newer data

    async function load() {
      try {
        const [newDecisions, newPrices, newForecast] = await Promise.all([
          getDecisions(),
          getPrices(ticker),
          getForecast(ticker),
        ])
        if (cancelled) return
        setDecisions(newDecisions)
        setPrices(newPrices)
        setForecast(newForecast)
        setError('')
        setUpdated(new Date().toLocaleTimeString())
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      }
    }

    void load()
    const timer = setInterval(() => void load(), REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [ticker])

  return (
    <>
      <h1>TapeLab</h1>
      <p className="note">
        Live view of your database. Updated {updated}; refreshes every {REFRESH_MS / 1000} seconds.
      </p>
      {error && <p className="error">Could not load: {error}. Is the backend running on port 8081?</p>}

      <h2>Decisions (last 30 days)</h2>
      {decisions ? <DecisionsTable decisions={decisions} /> : <p>Loading...</p>}

      <h2>Prices: {ticker}</h2>
      <div>
        {TICKERS.map((t) => (
          <button key={t} disabled={t === ticker} onClick={() => setTicker(t)}>
            {t}
          </button>
        ))}{' '}
        <form
          style={{ display: 'inline' }}
          onSubmit={(e) => {
            e.preventDefault()
            if (typed.trim()) setTicker(typed.trim().toUpperCase())
          }}
        >
          <input value={typed} onChange={(e) => setTyped(e.target.value)} placeholder="other ticker" />
          <button type="submit">Show</button>
        </form>
      </div>
      {prices && (
        <>
          <PriceChart prices={prices} forecast={forecast} />
          <h2>Predict a date range: {ticker}</h2>
          <PredictionPanel key={ticker} ticker={ticker} lastDate={prices.at(-1)?.date ?? null} />
          {forecast ? (
            <>
              <h2>Next {forecast.horizon} trading days: {ticker}</h2>
              <ForecastTable forecast={forecast} />
            </>
          ) : (
            <p className="note">
              No forecast yet for {ticker}. Run <code>python -m tapelab.predict {ticker}</code>.
            </p>
          )}
          <h2>Recent prices: {ticker}</h2>
          <PricesTable prices={prices} />
        </>
      )}
    </>
  )
}
