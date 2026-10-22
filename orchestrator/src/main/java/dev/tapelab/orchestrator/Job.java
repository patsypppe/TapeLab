package dev.tapelab.orchestrator;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "job", uniqueConstraints = @UniqueConstraint(columnNames = {"experimentId", "ticker", "runDate", "config"}))
public class Job {
    public enum Status { PENDING, RUNNING, DONE, FAILED }

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private Long experimentId;
    private String ticker;
    private LocalDate runDate;
    private String config;
    @Enumerated(EnumType.STRING)
    private Status status = Status.PENDING;
    private int attempts;
    private Instant createdAt = Instant.now();

    protected Job() {}

    public Job(Long experimentId, String ticker, LocalDate runDate, String config) {
        this.experimentId = experimentId;
        this.ticker = ticker;
        this.runDate = runDate;
        this.config = config;
    }

    public Long getId() { return id; }
    public Long getExperimentId() { return experimentId; }
    public String getTicker() { return ticker; }
    public LocalDate getRunDate() { return runDate; }
    public String getConfig() { return config; }
    public Status getStatus() { return status; }
    public int getAttempts() { return attempts; }
}
