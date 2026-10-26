import { describe, expect, it } from 'vitest'
import { chartPoints, forecastChart, signed, stance } from './format'

describe('stance', () => {
  it('labels full, none and partial positions', () => {
    expect(stance(1)).toBe('LONG')
    expect(stance(0)).toBe('FLAT')
    expect(stance(0.5)).toBe('50% long')
  })
})

describe('signed', () => {
  it('always shows the sign and two decimals', () => {
    expect(signed(0.3122)).toBe('+0.31')
    expect(signed(-0.48)).toBe('-0.48')
    expect(signed(0)).toBe('+0.00')
  })
})

describe('chartPoints', () => {
  it('puts the lowest value at the bottom left and the highest at the top right', () => {
    expect(chartPoints([1, 3], 100, 50, 10)).toBe('10.0,40.0 90.0,10.0')
  })

  it('draws a flat series as a straight line instead of NaN', () => {
    const points = chartPoints([5, 5, 5], 100, 50, 10)
    expect(points).not.toContain('NaN')
    expect(new Set(points.split(' ').map((p) => p.split(',')[1])).size).toBe(1)
  })

  it('returns nothing when there is less than a line to draw', () => {
    expect(chartPoints([], 100, 50)).toBe('')
    expect(chartPoints([4], 100, 50)).toBe('')
  })
})

describe('forecastChart', () => {
  const closes = [100, 100]
  const points = [
    { median: 100, low: 90, high: 110 },
    { median: 100, low: 80, high: 120 },
  ]
  const xs = (shape: string) => shape.split(' ').map((p) => Number(p.split(',')[0]))
  const ys = (shape: string) => shape.split(' ').map((p) => Number(p.split(',')[1]))

  it('starts the band and the middle line at the last close', () => {
    const chart = forecastChart(closes, points, 300, 100, 10)
    const lastClose = chart.history.split(' ').at(-1)
    expect(chart.band.split(' ')[0]).toBe(lastClose)
    expect(chart.median.split(' ')[0]).toBe(lastClose)
  })

  it('moves right through time and draws highs above lows (screen y points down)', () => {
    const chart = forecastChart(closes, points, 300, 100, 10)
    const [first, second] = xs(chart.history)
    expect(first).toBe(10)
    expect(second).toBeCloseTo(10 + 280 / 3, 0) // coordinates are rounded to one decimal
    expect(Math.max(...xs(chart.band))).toBeCloseTo(290)
    const [start, high1, high2, low2, low1] = ys(chart.band)
    expect(high2).toBeLessThan(high1) // a wider high is further up
    expect(low2).toBeGreaterThan(low1) // a wider low is further down
    expect(high1).toBeLessThan(start)
    expect(low1).toBeGreaterThan(start)
  })

  it('never produces NaN, even for a flat price with a zero-width range', () => {
    const chart = forecastChart([5, 5], [{ median: 5, low: 5, high: 5 }], 100, 50)
    expect(chart.band + chart.median + chart.history).not.toContain('NaN')
  })
})
