package dev.tapelab.backend;

import com.fasterxml.jackson.annotation.JsonAlias;
import java.math.BigDecimal;
import java.time.LocalDate;

/** The expected range for one day ahead. The stored JSON says day_ahead; the API says dayAhead. */
public record ForecastPoint(@JsonAlias("day_ahead") int dayAhead, LocalDate date, BigDecimal median,
                            BigDecimal low, BigDecimal high) {
}
