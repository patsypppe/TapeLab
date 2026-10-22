package dev.tapelab.orchestrator;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/** Expands tickers x dates x configs into one job spec per cell. */
public final class ExperimentGrid {

    public record Cell(String ticker, LocalDate date, String config) {}

    private ExperimentGrid() {}

    public static List<Cell> expand(List<String> tickers, List<LocalDate> dates, List<String> configs) {
        List<Cell> cells = new ArrayList<>(tickers.size() * dates.size() * configs.size());
        for (String config : configs) {
            for (String ticker : tickers) {
                for (LocalDate date : dates) {
                    cells.add(new Cell(ticker.toUpperCase(), date, config));
                }
            }
        }
        return cells;
    }
}
