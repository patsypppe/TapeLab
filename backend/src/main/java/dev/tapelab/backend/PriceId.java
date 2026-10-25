package dev.tapelab.backend;

import jakarta.persistence.Embeddable;
import java.io.Serializable;
import java.time.LocalDate;

/** The two columns that together identify one price row: a ticker on a day. */
@Embeddable
public record PriceId(String ticker, LocalDate date) implements Serializable {
}
