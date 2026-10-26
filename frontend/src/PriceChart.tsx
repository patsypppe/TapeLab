import type { Forecast, Price } from './api'
import { chartPoints, forecastChart } from './format'

const WIDTH = 900
const HEIGHT = 180
const HISTORY_DAYS = 60 // how much recent history to show next to a forecast

export function PriceChart({ prices, forecast }: { prices: Price[]; forecast: Forecast | null }) {
  if (prices.length < 2) {
    return <p>Not enough prices to draw a chart. Run <code>python -m tapelab.prices</code>.</p>
  }
  // Show only closes up to the day the forecast was made, so the band starts where the line ends.
  const recent = forecast ? prices.filter((p) => p.date <= forecast.asOf).slice(-HISTORY_DAYS) : []
  if (forecast && recent.length >= 2) {
    const chart = forecastChart(recent.map((p) => p.close), forecast.points, WIDTH, HEIGHT)
    const last = forecast.points[forecast.points.length - 1]
    return (
      <div>
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Recent closing price and forecast range">
          <polygon points={chart.band} fill="steelblue" fillOpacity="0.2" stroke="none" />
          <polyline points={chart.median} fill="none" stroke="steelblue" strokeWidth="1.5" strokeDasharray="4 4" />
          <polyline points={chart.history} fill="none" stroke="steelblue" strokeWidth="2" />
        </svg>
        <p className="note">
          Last {recent.length} closes, then the shaded 80% range for the next {forecast.horizon} trading days
          (ending {last.low.toFixed(2)} to {last.high.toFixed(2)}).
        </p>
      </div>
    )
  }
  const closes = prices.map((p) => p.close)
  return (
    <div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Closing price over time">
        <polyline fill="none" stroke="steelblue" strokeWidth="2" points={chartPoints(closes, WIDTH, HEIGHT)} />
      </svg>
      <p className="note">
        {prices[0].date} to {prices[prices.length - 1].date}: low {Math.min(...closes).toFixed(2)}, high{' '}
        {Math.max(...closes).toFixed(2)}
      </p>
    </div>
  )
}
