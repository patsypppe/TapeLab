CREATE TABLE filing_scores (
    filing_id  BIGINT           NOT NULL REFERENCES filings (id) ON DELETE CASCADE,
    model      TEXT             NOT NULL,  -- scores from different models are kept apart
    score      DOUBLE PRECISION NOT NULL CHECK (score BETWEEN -1 AND 1),
    rationale  TEXT             NOT NULL,
    scored_at  TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (filing_id, model)
);
