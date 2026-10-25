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
