import type { Forecast } from './api'

export function ForecastTable({ forecast }: { forecast: Forecast }) {
  return (
    <>
      <p className="note">
        Likely range for each of the next {forecast.horizon} trading days, from the {forecast.asOf} close of{' '}
        {forecast.lastClose.toFixed(2)}. Dates skip weekends only, so a market holiday can shift them by a day.
        This is a range, not a prediction of direction: the middle is simply the last close, and about one time
        in five the price is expected outside it. In a backtest on AAPL, MSFT and NVDA (2023 to 2026) the real
        price stayed inside ranges like this 77 to 84% of the time.
      </p>
      <table>
        <thead>
          <tr>
            <th>Day ahead</th>
            <th>Date</th>
            <th>Low</th>
            <th>Middle</th>
            <th>High</th>
          </tr>
        </thead>
        <tbody>
          {forecast.points.map((p) => (
            <tr key={p.dayAhead}>
              <td>+{p.dayAhead}</td>
              <td>{p.date}</td>
              <td>{p.low.toFixed(2)}</td>
              <td>{p.median.toFixed(2)}</td>
              <td>{p.high.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
