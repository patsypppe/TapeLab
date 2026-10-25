package dev.tapelab.backend;

import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DecisionRepository extends JpaRepository<Decision, Long> {

    List<Decision> findByTickerAndDecidedForBetweenOrderByDecidedForDesc(String ticker, LocalDate from, LocalDate to);

    List<Decision> findByDecidedForBetweenOrderByDecidedForDescTickerAsc(LocalDate from, LocalDate to);
}
