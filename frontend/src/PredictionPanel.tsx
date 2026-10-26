import { useState } from 'react'
import { getPrediction, type Prediction } from './api'
import { addDays, describeSummary, money, signedMoney } from './format'

/** Pick two dates, press Predict, and see the predicted price against the actual one for each day. */
export function PredictionPanel({ ticker, lastDate }: { ticker: string; lastDate: string | null }) {
  const [fromInput, setFromInput] = useState<string | null>(null)
  const [toInput, setToInput] = useState<string | null>(null)
  const [result, setResult] = useState<Prediction | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // Until the user picks dates, suggest the last week of stored prices, so there are actual prices to compare.
  const to = toInput ?? lastDate ?? ''
  const from = fromInput ?? (lastDate ? addDays(lastDate, -6) : '')

  async function predict() {
    setBusy(true)
    setError('')
    try {
      setResult(await getPrediction(ticker, from, to))
    } catch (e) {
      setResult(null)
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          void predict()
        }}
      >
        <label>
          From <input type="date" value={from} onChange={(e) => setFromInput(e.target.value)} />
        </label>{' '}
        <label>
          To <input type="date" value={to} onChange={(e) => setToInput(e.target.value)} />
        </label>{' '}
        <button type="submit" disabled={busy || !from || !to}>
          {busy ? 'Predicting...' : 'Predict'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <>
          <p>
            <strong>{describeSummary(result.summary)}</strong>
          </p>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Day ahead</th>
                <th>Predicted</th>
                <th>80% range</th>
                <th>Actual</th>
                <th>Difference</th>
                <th>Error</th>
                <th>In range</th>
              </tr>
            </thead>
            <tbody>
              {result.rows.map((r) => (
                <tr key={r.date}>
                  <td>{r.date}</td>
                  <td>+{r.dayAhead}</td>
                  <td>{money(r.predicted)}</td>
                  <td>
                    {money(r.low)} to {money(r.high)}
                  </td>
                  <td>{r.actual === null ? 'not yet' : money(r.actual)}</td>
                  <td>{r.difference === null ? '-' : signedMoney(r.difference)}</td>
                  <td>{r.errorPct === null ? '-' : `${r.errorPct.toFixed(2)}%`}</td>
                  <td>{r.insideRange === null ? '-' : r.insideRange ? 'yes' : 'no'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="note">Difference is actual minus predicted. Error is the size of that difference as a share of the actual price.</p>
          <ul className="note">
            {result.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </>
      )}
    </>
  )
}
