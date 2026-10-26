package dev.tapelab.backend;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ForecastRepository extends JpaRepository<Forecast, Long> {

    /** The newest forecast for a ticker and model: latest as_of day, then latest time it was made. */
    Optional<Forecast> findFirstByTickerAndModelOrderByAsOfDescMadeAtDesc(String ticker, String model);
}
