package dev.tapelab.backend;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import org.hibernate.annotations.Immutable;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/** One saved forecast. The database allows inserts only, so the entity is immutable too. */
@Entity
@Immutable
@Table(name = "forecasts")
public class Forecast {

    @Id
    private Long id;
    private String ticker;
    @Column(name = "as_of")
    private LocalDate asOf;
    @Column(name = "made_at")
    private Instant madeAt;
    private String model;
    private int horizon;
    @Column(name = "last_close")
    private BigDecimal lastClose;
    @JdbcTypeCode(SqlTypes.JSON)
    private List<ForecastPoint> points;

    protected Forecast() {
    }

    public Long getId() { return id; }
    public String getTicker() { return ticker; }
    public LocalDate getAsOf() { return asOf; }
    public Instant getMadeAt() { return madeAt; }
    public String getModel() { return model; }
    public int getHorizon() { return horizon; }
    public BigDecimal getLastClose() { return lastClose; }
    public List<ForecastPoint> getPoints() { return points; }
}
