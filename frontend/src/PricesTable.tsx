import type { Price } from './api'

const ROWS = 15

export function PricesTable({ prices }: { prices: Price[] }) {
  const latest = prices.slice(-ROWS).reverse() // newest first
  return (
    <table>
      <thead>
        <tr>
          <th>Day</th>
          <th>Open</th>
          <th>High</th>
          <th>Low</th>
          <th>Close</th>
          <th>Volume</th>
        </tr>
      </thead>
      <tbody>
        {latest.map((p) => (
          <tr key={p.date}>
            <td>{p.date}</td>
            <td>{p.open.toFixed(2)}</td>
            <td>{p.high.toFixed(2)}</td>
            <td>{p.low.toFixed(2)}</td>
            <td>{p.close.toFixed(2)}</td>
            <td>{p.volume.toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
