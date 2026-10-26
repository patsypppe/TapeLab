package dev.tapelab.backend;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class ForecastCalculatorTest {

    @Test
    void matchesTheNumbersThePythonForecastProduces() throws IOException {
        // The same file is checked by the Python tests, so the two implementations cannot drift apart.
        JsonNode golden = new ObjectMapper().readTree(
            Path.of("..", "tests", "fixtures", "forecast_golden.json").toFile());
        List<Double> closes = new ArrayList<>();
        golden.get("closes").forEach(c -> closes.add(c.asDouble()));
        JsonNode expected = golden.get("points");

        List<ForecastCalculator.Range> ranges = ForecastCalculator.forecast(closes, expected.size());

        assertEquals(20, ranges.size());
        for (int i = 0; i < ranges.size(); i++) {
            JsonNode want = expected.get(i);
            assertEquals(want.get("day_ahead").asInt(), ranges.get(i).dayAhead());
            assertEquals(want.get("median").asDouble(), ranges.get(i).median(), 1e-9 * want.get("median").asDouble());
            assertEquals(want.get("low").asDouble(), ranges.get(i).low(), 1e-9 * want.get("low").asDouble());
            assertEquals(want.get("high").asDouble(), ranges.get(i).high(), 1e-9 * want.get("high").asDouble());
        }
    }

    @Test
    void theRangeWidensWithTheSquareRootOfTheDaysAhead() {
        List<Double> closes = new ArrayList<>();
        double price = 100;
        for (int i = 0; i < 80; i++) {
            price *= 1 + (i % 2 == 0 ? 0.01 : -0.008);
            closes.add(price);
        }
        List<ForecastCalculator.Range> ranges = ForecastCalculator.forecast(closes, 4);
        double day1 = Math.log(ranges.get(0).high() / ranges.get(0).low());
        double day4 = Math.log(ranges.get(3).high() / ranges.get(3).low());
        assertEquals(2.0, day4 / day1, 1e-9);
        assertTrue(ranges.get(0).low() < ranges.get(0).median() && ranges.get(0).median() < ranges.get(0).high());
        assertEquals(closes.get(closes.size() - 1), ranges.get(0).median(), 1e-9);
    }

    @Test
    void aFlatPriceGivesAZeroWidthRangeInsteadOfNaN() {
        List<Double> flat = new ArrayList<>();
        for (int i = 0; i < 70; i++) {
            flat.add(50.0);
        }
        ForecastCalculator.Range range = ForecastCalculator.forecast(flat, 1).get(0);
        assertFalse(Double.isNaN(range.low()) || Double.isNaN(range.high()));
        assertEquals(50.0, range.low(), 1e-9);
        assertEquals(50.0, range.high(), 1e-9);
    }

    @Test
    void tooLittleHistoryIsRejected() {
        List<Double> few = new ArrayList<>();
        for (int i = 0; i < 40; i++) {
            few.add(100.0 + i);
        }
        assertThrows(IllegalArgumentException.class, () -> ForecastCalculator.forecast(few, 5));
    }
}
