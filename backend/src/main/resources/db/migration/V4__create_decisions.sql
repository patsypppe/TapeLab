CREATE TABLE decisions (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticker      TEXT          NOT NULL,
    decided_for DATE          NOT NULL,                   -- the trading day whose close the decision was made on
    decided_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),     -- when the row was written
    position    NUMERIC(4, 3) NOT NULL CHECK (position BETWEEN 0 AND 1),  -- target exposure: 0 flat, 1 fully long
    reasons     JSONB         NOT NULL,                   -- each analyst's score and explanation
    config      JSONB         NOT NULL DEFAULT '{}',      -- settings used: weights, model, windows
    filing_id   BIGINT REFERENCES filings (id),           -- the filing whose score was used, if any
    UNIQUE (ticker, decided_for)                          -- one decision per ticker per day
);

CREATE FUNCTION forbid_decision_changes() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'decisions are insert-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER decisions_insert_only
    BEFORE UPDATE OR DELETE ON decisions
    FOR EACH ROW EXECUTE FUNCTION forbid_decision_changes();

CREATE TRIGGER decisions_no_truncate
    BEFORE TRUNCATE ON decisions
    FOR EACH STATEMENT EXECUTE FUNCTION forbid_decision_changes();
