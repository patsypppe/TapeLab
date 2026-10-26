/** LONG for a full position, FLAT for none, otherwise the share held. */
export function stance(position: number): string {
  if (position >= 1) return 'LONG'
  if (position <= 0) return 'FLAT'
  return `${Math.round(position * 100)}% long`
}

/** A score with its sign shown, e.g. +0.31 or -0.48. */
export function signed(score: number): string {
  return (score >= 0 ? '+' : '') + score.toFixed(2)
}

/** Turns a series of values into the points of an SVG line that fills a width by height box. */
export function chartPoints(values: number[], width: number, height: number, pad = 8): string {
  if (values.length < 2) return ''
  const min = Math.min(...values)
  const span = Math.max(...values) - min || 1 // a flat series would otherwise divide by zero
  return values
    .map((value, i) => {
      const x = pad + (i / (values.length - 1)) * (width - 2 * pad)
      const y = pad + (1 - (value - min) / span) * (height - 2 * pad)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

type Range = { median: number; low: number; high: number }

/**
 * Coordinates for a price line followed by a forecast band, drawn on one shared scale.
 * `band` is a closed shape that starts at the last close and spreads to the high and low of each day.
 */
export function forecastChart(closes: number[], points: Range[], width: number, height: number, pad = 8) {
  const last = closes.length - 1
  const steps = last + points.length // positions across the chart, so the line and band share the x axis
  const values = [...closes, ...points.flatMap((p) => [p.low, p.high])]
  const min = Math.min(...values)
  const span = Math.max(...values) - min || 1
  const x = (i: number) => pad + (i / steps) * (width - 2 * pad)
  const y = (v: number) => pad + (1 - (v - min) / span) * (height - 2 * pad)
  const at = (i: number, v: number) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`
  const start = at(last, closes[last])
  return {
    history: closes.map((c, i) => at(i, c)).join(' '),
    median: [start, ...points.map((p, d) => at(last + d + 1, p.median))].join(' '),
    band: [
      start,
      ...points.map((p, d) => at(last + d + 1, p.high)),
      ...points.map((p, d) => at(last + d + 1, p.low)).reverse(),
    ].join(' '),
  }
}

/** A price or amount with two decimals. */
export const money = (n: number): string => n.toFixed(2)

/** An amount with its sign, e.g. +1.25 or -0.40; a value that rounds to zero shows no sign. */
export function signedMoney(n: number): string {
  const rounded = Number(n.toFixed(2))
  if (rounded === 0) return '0.00'
  return (rounded > 0 ? '+' : '-') + Math.abs(rounded).toFixed(2)
}

/** The date `days` after (or before, if negative) an ISO date such as 2026-10-23. */
export function addDays(isoDate: string, days: number): string {
  return new Date(Date.parse(`${isoDate}T00:00:00Z`) + days * 86_400_000).toISOString().slice(0, 10)
}

type Summary = {
  daysWithActual: number
  meanAbsErrorPct: number | null
  meanAbsDifference: number | null
  insideRange: number
}

/** One plain sentence saying how the prediction did on the dates that already have an actual price. */
export function describeSummary(s: Summary): string {
  if (s.daysWithActual === 0 || s.meanAbsErrorPct === null || s.meanAbsDifference === null) {
    return 'No actual prices yet for these dates, so there is nothing to score.'
  }
  const share = Math.round((s.insideRange / s.daysWithActual) * 100)
  return (
    `Over the ${s.daysWithActual} day(s) with actual prices: on average ${s.meanAbsErrorPct.toFixed(2)}% off ` +
    `(${s.meanAbsDifference.toFixed(2)} in price). The real price was inside the 80% range on ` +
    `${s.insideRange} of ${s.daysWithActual} days (${share}%).`
  )
}
