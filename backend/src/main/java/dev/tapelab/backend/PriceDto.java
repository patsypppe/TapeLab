package dev.tapelab.backend;

import java.math.BigDecimal;
import java.time.LocalDate;

/** What the API returns for one price row, so the JSON does not depend on the entity's shape. */
public record PriceDto(LocalDate date, BigDecimal open, BigDecimal high, BigDecimal low,
                       BigDecimal close, long volume) {

    static PriceDto from(Price p) {
        return new PriceDto(p.getId().date(), p.getOpen(), p.getHigh(), p.getLow(), p.getClose(),
            p.getVolume());
    }
}
