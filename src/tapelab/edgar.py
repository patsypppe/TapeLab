"""Reads the SEC's EDGAR service: ticker to company id, lists of filings, and filing documents."""
import os
import time
from dataclasses import dataclass
from datetime import date, datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
DOCUMENT_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
PAUSE = 0.15  # seconds between requests; the SEC allows at most 10 per second


@dataclass(frozen=True)
class FilingRef:
    ticker: str
    cik: int
    form: str
    accession: str
    filed_at: date
    accepted_at: datetime | None
    period_end: date | None
    url: str


def sec_client() -> httpx.Client:
    """An HTTP client that identifies us to the SEC, using SEC_USER_AGENT from the environment."""
    user_agent = os.environ.get("SEC_USER_AGENT")
    if not user_agent:
        raise RuntimeError("SEC_USER_AGENT is not set (a name and email, e.g. in your .env)")
    return httpx.Client(headers={"User-Agent": user_agent}, timeout=30)


def _get(client: httpx.Client, url: str) -> httpx.Response:
    """GET a URL after a short pause, so a loop of calls stays under the SEC's rate limit."""
    time.sleep(PAUSE)
    response = client.get(url)
    response.raise_for_status()
    return response


def lookup_cik(client: httpx.Client, ticker: str) -> int:
    """Find a company's SEC id (CIK) from its ticker symbol."""
    for entry in _get(client, TICKERS_URL).json().values():
        if entry["ticker"].upper() == ticker.upper():
            return int(entry["cik_str"])
    raise ValueError(f"No SEC company found for ticker {ticker}")


def parse_submissions(ticker: str, cik: int, payload: dict, form: str, limit: int) -> list[FilingRef]:
    """Pick the newest filings of one form from the SEC's list of a company's recent filings."""
    recent = payload["filings"]["recent"]
    refs = []
    for i, f in enumerate(recent["form"]):
        if f != form:
            continue
        accession = recent["accessionNumber"][i]
        accepted = recent["acceptanceDateTime"][i]
        period = recent["reportDate"][i]
        refs.append(FilingRef(
            ticker=ticker.upper(),
            cik=cik,
            form=f,
            accession=accession,
            filed_at=date.fromisoformat(recent["filingDate"][i]),
            accepted_at=datetime.fromisoformat(accepted) if accepted else None,
            period_end=date.fromisoformat(period) if period else None,
            url=DOCUMENT_URL.format(cik=cik, accession=accession.replace("-", ""),
                                    document=recent["primaryDocument"][i]),
        ))
    return sorted(refs, key=lambda r: r.filed_at, reverse=True)[:limit]


def list_filings(client: httpx.Client, ticker: str, form: str = "10-K", limit: int = 1) -> list[FilingRef]:
    """The newest filings of one form for a ticker."""
    cik = lookup_cik(client, ticker)
    payload = _get(client, SUBMISSIONS_URL.format(cik=cik)).json()
    return parse_submissions(ticker, cik, payload, form, limit)


def fetch_document(client: httpx.Client, ref: FilingRef) -> str:
    """Download the filing's main document as HTML text."""
    return _get(client, ref.url).text
