CREATE TABLE prices (
    ticker  TEXT           NOT NULL,
    date    DATE           NOT NULL,
    open    NUMERIC(14, 4) NOT NULL,
    high    NUMERIC(14, 4) NOT NULL,
    low     NUMERIC(14, 4) NOT NULL,
    close   NUMERIC(14, 4) NOT NULL,
    volume  BIGINT         NOT NULL CHECK (volume >= 0),
    PRIMARY KEY (ticker, date),
    CHECK (high >= low)
);
