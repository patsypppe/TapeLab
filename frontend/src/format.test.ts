import { describe, expect, it } from 'vitest'
import { chartPoints, signed, stance } from './format'

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
