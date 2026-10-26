"""Regenerates forecast_golden.json from the Python forecast. Run it only when the algorithm changes on purpose:

    python tests/fixtures/make_forecast_golden.py

Both the Python and the Java tests must then reproduce these numbers, so the two implementations cannot drift apart.
"""
import json
import random
from pathlib import Path

from tapelab.forecast import WINDOW, forecast

rng, price, closes = random.Random(2024), 100.0, []
for _ in range(100):
    price *= 1 + rng.gauss(0.0004, 0.014)
    closes.append(price)

points = forecast(closes, horizon=20, window=WINDOW, model="random_walk")
golden = {
    "model": "random_walk",
    "window": WINDOW,
    "closes": closes,
    "points": [{"day_ahead": p.day_ahead, "median": p.median, "low": p.low, "high": p.high} for p in points],
}
Path(__file__).with_name("forecast_golden.json").write_text(json.dumps(golden, indent=1) + "\n")
print(f"wrote {len(closes)} closes and {len(points)} forecast days")
