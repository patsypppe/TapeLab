"""Minimal SEC EDGAR client. SEC requires a descriptive User-Agent and <=10 req/s."""
import httpx

BASE = "https://data.sec.gov"


class EdgarClient:
    def __init__(self, user_agent: str):
        self._http = httpx.Client(headers={"User-Agent": user_agent}, timeout=30)

    def recent_filings(self, cik: int, form: str = "10-K") -> list[dict]:
        r = self._http.get(f"{BASE}/submissions/CIK{cik:010d}.json")
        r.raise_for_status()
        recent = r.json()["filings"]["recent"]
        rows = zip(recent["form"], recent["accessionNumber"], recent["primaryDocument"],
                   recent["filingDate"])
        return [
            {"form": f, "accession": a, "document": d, "date": dt}
            for f, a, d, dt in rows if f == form
        ]
