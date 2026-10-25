import type { Decision } from './api'
import { signed, stance } from './format'

export function DecisionsTable({ decisions }: { decisions: Decision[] }) {
  if (decisions.length === 0) {
    return (
      <p>
        No decisions yet. Run <code>python -m tapelab.decide AAPL MSFT NVDA</code>.
      </p>
    )
  }
  return (
    <table>
      <thead>
        <tr>
          <th>Day</th>
          <th>Ticker</th>
          <th>Stance</th>
          <th>Why</th>
        </tr>
      </thead>
      <tbody>
        {decisions.map((d) => (
          <tr key={d.id}>
            <td>{d.decidedFor}</td>
            <td>{d.ticker}</td>
            <td className={d.position >= 1 ? 'long' : 'flat'}>{stance(d.position)}</td>
            <td>
              <ul>
                {d.reasons.map((r) => (
                  <li key={r.analyst}>
                    <strong>{r.analyst}</strong> {signed(r.score)}: {r.rationale}
                  </li>
                ))}
              </ul>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
