package dev.tapelab.backend;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PriceRepository extends JpaRepository<Price, PriceId> {

    /** Spring builds the query from this name: one ticker, dates from to, oldest first. */
    List<Price> findByIdTickerAndIdDateBetweenOrderByIdDate(String ticker, LocalDate from, LocalDate to);

    /** The 61 closes before a day, newest first: the 60 returns the forecast needs. */
    List<Price> findTop61ByIdTickerAndIdDateLessThanOrderByIdDateDesc(String ticker, LocalDate before);

    /** The most recent stored price for a ticker. */
    Optional<Price> findFirstByIdTickerOrderByIdDateDesc(String ticker);
}
