from datetime import date

import httpx
import pytest

from tapelab import edgar
from tapelab.edgar import fetch_document, list_filings, lookup_cik, parse_submissions, sec_client

# Made-up data in the shape of the SEC's responses, not a real download.
TICKERS = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
           "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"}}

SUBMISSIONS = {"filings": {"recent": {
    "form": ["8-K", "10-K", "10-Q", "10-K"],
    "accessionNumber": ["0000320193-25-000100", "0000320193-25-000079",
                        "0000320193-25-000050", "0000320193-24-000123"],
    "filingDate": ["2025-11-05", "2025-10-31", "2025-08-01", "2024-11-01"],
    "reportDate": ["", "2025-09-27", "2025-06-28", "2024-09-28"],
    "acceptanceDateTime": ["2025-11-05T21:00:00.000Z", "2025-10-31T06:01:26.000Z",
                           "2025-08-01T06:00:00.000Z", "2024-11-01T06:00:00.000Z"],
    "primaryDocument": ["a.htm", "aapl-20250927.htm", "q.htm", "aapl-20240928.htm"],
}}}


@pytest.fixture(autouse=True)
def no_pause(monkeypatch):
    monkeypatch.setattr(edgar, "PAUSE", 0)


def mock_client(seen=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        path = request.url.path
        if path.endswith("company_tickers.json"):
            return httpx.Response(200, json=TICKERS)
        if "/submissions/" in path:
            return httpx.Response(200, json=SUBMISSIONS)
        return httpx.Response(200, text="<html>the filing</html>")
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parse_picks_newest_filings_of_one_form():
    refs = parse_submissions("aapl", 320193, SUBMISSIONS, "10-K", limit=5)
    assert [r.accession for r in refs] == ["0000320193-25-000079", "0000320193-24-000123"]
    newest = refs[0]
    assert newest.filed_at == date(2025, 10, 31) and newest.period_end == date(2025, 9, 27)
    assert newest.accepted_at.hour == 6 and newest.accepted_at.tzinfo is not None
    assert newest.url == ("https://www.sec.gov/Archives/edgar/data/320193/"
                          "000032019325000079/aapl-20250927.htm")
    assert len(parse_submissions("aapl", 320193, SUBMISSIONS, "10-K", limit=1)) == 1


def test_missing_report_date_becomes_none():
    (ref,) = parse_submissions("aapl", 320193, SUBMISSIONS, "8-K", limit=1)
    assert ref.period_end is None


def test_lookup_cik_is_case_insensitive_and_rejects_unknown():
    client = mock_client()
    assert lookup_cik(client, "aapl") == 320193
    with pytest.raises(ValueError):
        lookup_cik(client, "ZZZZ")


def test_list_and_fetch_use_the_right_urls():
    seen = []
    client = mock_client(seen)
    (ref,) = list_filings(client, "MSFT", "10-K", limit=1)
    assert ref.cik == 789019 and "CIK0000789019.json" in str(seen[-1].url)
    assert fetch_document(client, ref) == "<html>the filing</html>"
    assert str(seen[-1].url) == ref.url


def test_sec_client_needs_user_agent(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(RuntimeError):
        sec_client()
    monkeypatch.setenv("SEC_USER_AGENT", "TapeLab test@example.com")
    assert sec_client().headers["user-agent"] == "TapeLab test@example.com"
