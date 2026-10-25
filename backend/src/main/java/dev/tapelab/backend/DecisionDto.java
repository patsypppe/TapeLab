package dev.tapelab.backend;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/** What the API returns for one decision. */
public record DecisionDto(Long id, String ticker, LocalDate decidedFor, Instant decidedAt,
                          BigDecimal position, List<Reason> reasons, Map<String, Object> config,
                          Long filingId) {

    static DecisionDto from(Decision d) {
        return new DecisionDto(d.getId(), d.getTicker(), d.getDecidedFor(), d.getDecidedAt(),
            d.getPosition(), d.getReasons(), d.getConfig(), d.getFilingId());
    }
}
