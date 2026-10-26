package dev.tapelab.backend;

import java.util.ArrayList;
import java.util.List;

/**
 * The forecast math, ported from Python's tapelab.forecast (random-walk model). The golden-file
 * test checks that both give the same numbers, so neither can change without the other.
 */
public final class ForecastCalculator {

    /** Past daily returns used to estimate how much the stock moves. */
    public static final int WINDOW = 60;
    /** For a normal distribution, 80% of outcomes fall within this many standard deviations. */
    public static final double Z80 = 1.2816;

    /** The expected range for one day ahead; 80% of outcomes should land between low and high. */
    public record Range(int dayAhead, double median, double low, double high) {
    }

    private ForecastCalculator() {
    }

    /** The range for each of the next {@code horizon} trading days, from the closes available now (oldest first). */
    public static List<Range> forecast(List<Double> closes, int horizon) {
        if (closes.size() < WINDOW + 1) {
            throw new IllegalArgumentException("Need at least " + (WINDOW + 1) + " closes, got " + closes.size());
        }
        List<Double> recent = closes.subList(closes.size() - (WINDOW + 1), closes.size());
        double[] returns = new double[WINDOW];
        double sum = 0;
        for (int i = 0; i < WINDOW; i++) {
            returns[i] = Math.log(recent.get(i + 1) / recent.get(i));
            sum += returns[i];
        }
        double mean = sum / WINDOW;
        double squares = 0;
        for (double r : returns) {
            squares += (r - mean) * (r - mean);
        }
        double sigma = Math.sqrt(squares / (WINDOW - 1)); // sample standard deviation, as in Python's stdev
        double start = Math.log(recent.get(WINDOW));
        List<Range> ranges = new ArrayList<>(horizon);
        for (int day = 1; day <= horizon; day++) {
            double spread = Z80 * sigma * Math.sqrt(day);
            ranges.add(new Range(day, Math.exp(start), Math.exp(start - spread), Math.exp(start + spread)));
        }
        return ranges;
    }
}
