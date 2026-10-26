package dev.tapelab.backend;

import java.time.LocalDate;
import java.util.List;

/** The answer to "predict these dates": a row per date, a summary of how well it did, and caveats. */
public record PredictionDto(String ticker, String model, LocalDate originDate, double originClose,
                            List<Row> rows, Summary summary, List<String> notes) {

    /** One date. The actual price and everything derived from it are null while the date is still ahead. */
    public record Row(LocalDate date, int dayAhead, double predicted, double low, double high,
                      Double actual, Double difference, Double errorPct, Boolean insideRange) {
    }

    /** How the prediction did on the dates that have an actual price. */
    public record Summary(int daysWithActual, Double meanAbsErrorPct, Double meanAbsDifference, int insideRange) {
    }
}
