import type { Price } from './api'
import { chartPoints } from './format'

const WIDTH = 900
const HEIGHT = 180

export function PriceChart({ prices }: { prices: Price[] }) {
  if (prices.length < 2) {
    return <p>Not enough prices to draw a chart. Run <code>python -m tapelab.prices</code>.</p>
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
