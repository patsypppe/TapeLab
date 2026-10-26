package dev.tapelab.backend;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

/** What the API returns for a forecast. */
public record ForecastDto(String ticker, LocalDate asOf, Instant madeAt, String model, int horizon,
                          BigDecimal lastClose, List<ForecastPoint> points) {

    static ForecastDto from(Forecast f) {
        return new ForecastDto(f.getTicker(), f.getAsOf(), f.getMadeAt(), f.getModel(), f.getHorizon(),
            f.getLastClose(), f.getPoints());
    }
}
