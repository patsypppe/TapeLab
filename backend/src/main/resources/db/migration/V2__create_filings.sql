CREATE TABLE filings (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticker      TEXT        NOT NULL,
    cik         BIGINT      NOT NULL,
    form        TEXT        NOT NULL,
    accession   TEXT        NOT NULL UNIQUE,  -- the SEC's own id for one filing
    filed_at    DATE        NOT NULL,         -- the day it became public; the agent may not see it earlier
    accepted_at TIMESTAMPTZ,                  -- exact acceptance time, for filings released after the close
    period_end  DATE,                         -- the period the report covers
    url         TEXT        NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX filings_ticker_filed_at ON filings (ticker, filed_at);

CREATE TABLE filing_chunks (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    filing_id  BIGINT  NOT NULL REFERENCES filings (id) ON DELETE CASCADE,
    idx        INTEGER NOT NULL,              -- position of the chunk within the filing
    kind       TEXT    NOT NULL CHECK (kind IN ('text', 'table')),
    text       TEXT    NOT NULL,
    UNIQUE (filing_id, idx)
);
