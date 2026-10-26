CREATE TABLE forecasts (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticker     TEXT           NOT NULL,
    as_of      DATE           NOT NULL,                 -- the last close the forecast was built from
    made_at    TIMESTAMPTZ    NOT NULL DEFAULT now(),
    model      TEXT           NOT NULL,
    horizon    INTEGER        NOT NULL CHECK (horizon > 0),
    last_close NUMERIC(14, 4) NOT NULL,
    points     JSONB          NOT NULL,                 -- one entry per day ahead: day_ahead, date, median, low, high
    UNIQUE (ticker, as_of, model)                       -- one forecast per ticker, day and model
);

-- Saved before the outcome is known, so it can be scored honestly later: never edited afterwards.
CREATE FUNCTION forbid_forecast_changes() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'forecasts are insert-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER forecasts_insert_only
    BEFORE UPDATE OR DELETE ON forecasts
    FOR EACH ROW EXECUTE FUNCTION forbid_forecast_changes();

CREATE TRIGGER forecasts_no_truncate
    BEFORE TRUNCATE ON forecasts
    FOR EACH STATEMENT EXECUTE FUNCTION forbid_forecast_changes();
