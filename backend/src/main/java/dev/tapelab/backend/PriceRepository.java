package dev.tapelab.backend;

import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PriceRepository extends JpaRepository<Price, PriceId> {

    /** Spring builds the query from this name: one ticker, dates from to, oldest first. */
    List<Price> findByIdTickerAndIdDateBetweenOrderByIdDate(String ticker, LocalDate from, LocalDate to);
}
