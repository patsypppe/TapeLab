package dev.tapelab.backend;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.hibernate.annotations.Immutable;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/** One saved decision. The database allows inserts only, so the entity is immutable too. */
@Entity
@Immutable
@Table(name = "decisions")
public class Decision {

    @Id
    private Long id;
    private String ticker;
    @Column(name = "decided_for")
    private LocalDate decidedFor;
    @Column(name = "decided_at")
    private Instant decidedAt;
    private BigDecimal position;
    @JdbcTypeCode(SqlTypes.JSON)
    private List<Reason> reasons;
    @JdbcTypeCode(SqlTypes.JSON)
    private Map<String, Object> config;
    @Column(name = "filing_id")
    private Long filingId;

    protected Decision() {
    }

    public Long getId() { return id; }
    public String getTicker() { return ticker; }
    public LocalDate getDecidedFor() { return decidedFor; }
    public Instant getDecidedAt() { return decidedAt; }
    public BigDecimal getPosition() { return position; }
    public List<Reason> getReasons() { return reasons; }
    public Map<String, Object> getConfig() { return config; }
    public Long getFilingId() { return filingId; }
}
