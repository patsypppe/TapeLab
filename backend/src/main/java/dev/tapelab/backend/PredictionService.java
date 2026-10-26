package dev.tapelab.backend;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

/**
 * Predicts the price for each date in a range using only the closes before the range starts, then
 * sets each prediction against the actual price where the date has already happened.
 */
@Service
public class PredictionService {

    /** The longest horizon we allow, in trading days after the last close before the range. */
    public static final int MAX_DAYS_AHEAD = 20;
    /** Horizons up to here were checked against real data (1, 5 and 10 days). */
    public static final int TESTED_DAYS_AHEAD = 10;

    private final PriceRepository prices;

    public PredictionService(PriceRepository prices) {
        this.prices = prices;
    }

    public PredictionDto predict(String rawTicker, LocalDate from, LocalDate to) {
        String ticker = rawTicker.toUpperCase();
        if (from.isAfter(to)) {
            throw bad("from must not be after to");
        }
        var latestStored = prices.findFirstByIdTickerOrderByIdDateDesc(ticker).orElseThrow(() ->
            new ResponseStatusException(HttpStatus.NOT_FOUND,
                "No prices for " + ticker + ". Run: python -m tapelab.prices " + ticker));
        LocalDate latest = latestStored.getId().date();

        // Everything the forecast may use: the closes strictly before the first requested day.
        List<Price> history = new ArrayList<>(prices.findTop61ByIdTickerAndIdDateLessThanOrderByIdDateDesc(ticker, from));
        if (history.size() < ForecastCalculator.WINDOW + 1) {
            throw bad("Not enough price history before " + from + ": need " + (ForecastCalculator.WINDOW + 1)
                + " closes, have " + history.size());
        }
        Collections.reverse(history);
        Price origin = history.get(history.size() - 1);
        LocalDate originDate = origin.getId().date();
        double originClose = origin.getClose().doubleValue();
        List<Double> closes = history.stream().map(p -> p.getClose().doubleValue()).toList();

        // The trading days after the origin, up to the end of the range. Stored days are real trading
        // days; days beyond our latest price are weekdays, since market holidays are not known.
        Map<LocalDate, Double> actual = new LinkedHashMap<>();
        for (Price p : prices.findByIdTickerAndIdDateBetweenOrderByIdDate(ticker, originDate.plusDays(1), to)) {
            actual.put(p.getId().date(), p.getClose().doubleValue());
        }
        List<LocalDate> days = new ArrayList<>(actual.keySet());
        for (LocalDate d = latest.plusDays(1); !d.isAfter(to); d = d.plusDays(1)) {
            if (d.getDayOfWeek() != DayOfWeek.SATURDAY && d.getDayOfWeek() != DayOfWeek.SUNDAY) {
                days.add(d);
            }
        }
        if (days.size() > MAX_DAYS_AHEAD) {
            throw bad("That range reaches " + days.size() + " trading days past the last known close ("
                + originDate + "); the limit is " + MAX_DAYS_AHEAD);
        }
        List<ForecastCalculator.Range> ranges = ForecastCalculator.forecast(closes, Math.max(days.size(), 1));

        List<PredictionDto.Row> rows = new ArrayList<>();
        for (int i = 0; i < days.size(); i++) {
            LocalDate date = days.get(i);
            if (date.isBefore(from)) {
                continue; // counted as a day ahead, but not requested
            }
            ForecastCalculator.Range range = ranges.get(i);
            Double actualClose = actual.get(date);
            Double difference = actualClose == null ? null : round(actualClose - range.median(), 4);
            Double errorPct = actualClose == null ? null : round(Math.abs(actualClose - range.median()) / actualClose * 100, 2);
            Boolean inside = actualClose == null ? null : range.low() <= actualClose && actualClose <= range.high();
            rows.add(new PredictionDto.Row(date, range.dayAhead(), round(range.median(), 4), round(range.low(), 4),
                round(range.high(), 4), actualClose, difference, errorPct, inside));
        }
        if (rows.isEmpty()) {
            throw bad("There are no trading days between " + from + " and " + to);
        }
        return new PredictionDto(ticker, "random_walk", originDate, round(originClose, 4), rows, summarize(rows),
            notes(rows, originDate, originClose, latest));
    }

    private static PredictionDto.Summary summarize(List<PredictionDto.Row> rows) {
        List<PredictionDto.Row> known = rows.stream().filter(r -> r.actual() != null).toList();
        if (known.isEmpty()) {
            return new PredictionDto.Summary(0, null, null, 0);
        }
        double errorPct = known.stream().mapToDouble(PredictionDto.Row::errorPct).average().orElseThrow();
        double difference = known.stream().mapToDouble(r -> Math.abs(r.difference())).average().orElseThrow();
        int inside = (int) known.stream().filter(PredictionDto.Row::insideRange).count();
        return new PredictionDto.Summary(known.size(), round(errorPct, 2), round(difference, 4), inside);
    }

    private static List<String> notes(List<PredictionDto.Row> rows, LocalDate originDate, double originClose,
                                      LocalDate latest) {
        List<String> notes = new ArrayList<>();
        notes.add("The predicted price is the last close before the range (" + originDate + ", "
            + round(originClose, 2) + "): the model finds no reliable direction, so the error mostly measures how "
            + "far the stock really moved. The range is the honest part: it should hold the real price about 80% of the time.");
        if (rows.get(rows.size() - 1).dayAhead() > TESTED_DAYS_AHEAD) {
            notes.add("Dates more than " + TESTED_DAYS_AHEAD + " trading days ahead have not been backtested.");
        }
        if (rows.stream().anyMatch(r -> r.date().isAfter(latest))) {
            notes.add("Dates after " + latest + " have no actual price yet. They skip weekends only, so a market "
                + "holiday can shift them by a day.");
        }
        return notes;
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }

    private static double round(double value, int places) {
        return BigDecimal.valueOf(value).setScale(places, RoundingMode.HALF_UP).doubleValue();
    }
}
