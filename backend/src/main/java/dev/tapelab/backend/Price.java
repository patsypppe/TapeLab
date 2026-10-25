package dev.tapelab.backend;

import jakarta.persistence.EmbeddedId;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import java.math.BigDecimal;

/** One day's price bar for one ticker; maps to the prices table. Read-only for this service. */
@Entity
@Table(name = "prices")
public class Price {

    @EmbeddedId
    private PriceId id;
    private BigDecimal open;
    private BigDecimal high;
    private BigDecimal low;
    private BigDecimal close;
    private long volume;

    protected Price() {
    }

    public PriceId getId() { return id; }
    public BigDecimal getOpen() { return open; }
    public BigDecimal getHigh() { return high; }
    public BigDecimal getLow() { return low; }
    public BigDecimal getClose() { return close; }
    public long getVolume() { return volume; }
}
