import { describe, expect, it } from 'vitest'
import { addDays, chartPoints, describeSummary, forecastChart, money, signed, signedMoney, stance } from './format'

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

describe('money formats', () => {
  it('shows two decimals, with a sign where the direction matters', () => {
    expect(money(262.4587)).toBe('262.46')
    expect(signedMoney(1.254)).toBe('+1.25')
    expect(signedMoney(-0.4)).toBe('-0.40')
    expect(signedMoney(-0.001)).toBe('0.00') // no "-0.00"
  })
})

describe('addDays', () => {
  it('moves an ISO date across month and year ends without timezone surprises', () => {
    expect(addDays('2026-10-23', -6)).toBe('2026-10-17')
    expect(addDays('2026-12-30', 3)).toBe('2027-01-02')
    expect(addDays('2024-02-28', 2)).toBe('2024-03-01') // a leap year
  })
})

describe('describeSummary', () => {
  it('says how far off the prediction was and how often the range held', () => {
    const text = describeSummary({ daysWithActual: 5, meanAbsErrorPct: 1.234, meanAbsDifference: 3.456, insideRange: 4 })
    expect(text).toContain('5 day(s)')
    expect(text).toContain('1.23% off')
    expect(text).toContain('3.46 in price')
    expect(text).toContain('4 of 5 days (80%)')
  })

  it('explains when there is nothing to score yet', () => {
    const text = describeSummary({ daysWithActual: 0, meanAbsErrorPct: null, meanAbsDifference: null, insideRange: 0 })
    expect(text).toContain('nothing to score')
  })
})
