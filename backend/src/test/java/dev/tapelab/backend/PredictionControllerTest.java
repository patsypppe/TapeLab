package dev.tapelab.backend;

import static org.hamcrest.Matchers.containsString;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.nullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.jayway.jsonpath.JsonPath;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.time.LocalDate;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.transaction.annotation.Transactional;

@AutoConfigureMockMvc
@Transactional
class PredictionControllerTest extends PostgresTest {

    // 100 consecutive days from 2025-01-01 to 2025-04-10 (a Thursday); each stored day counts as a trading day.
    static final LocalDate FIRST = LocalDate.of(2025, 1, 1);
    static final LocalDate LAST = FIRST.plusDays(99);

    @Autowired
    MockMvc mvc;
    @Autowired
    JdbcTemplate jdbc;
    @PersistenceContext
    EntityManager entityManager;

    static double close(int i) {
        return 100 + i * 0.3 + (i % 4) * 0.9; // a gently rising, slightly bumpy series
    }

    @BeforeEach
    void insertPrices() {
        for (int i = 0; i < 100; i++) {
            double c = close(i);
            jdbc.update("INSERT INTO prices (ticker, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, 1)",
                "AAPL", FIRST.plusDays(i), c, c, c, c);
        }
    }

    ResultActions predict(String ticker, LocalDate from, LocalDate to) throws Exception {
        return mvc.perform(get("/predictions/" + ticker).param("from", from.toString()).param("to", to.toString()));
    }

    @Test
    void aPastRangeIsPredictedFromTheCloseBeforeItAndScoredAgainstTheActualPrices() throws Exception {
        LocalDate from = FIRST.plusDays(80), to = FIRST.plusDays(84);
        double originClose = close(79);
        double day1Actual = Math.round(close(80) * 10000) / 10000.0;
        predict("aapl", from, to)
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.originDate").value(FIRST.plusDays(79).toString()))
            .andExpect(jsonPath("$.originClose").value(originClose))
            .andExpect(jsonPath("$.rows.length()").value(5))
            .andExpect(jsonPath("$.rows[0].date").value(from.toString()))
            .andExpect(jsonPath("$.rows[0].dayAhead").value(1))
            .andExpect(jsonPath("$.rows[4].dayAhead").value(5))
            .andExpect(jsonPath("$.rows[0].predicted").value(originClose))
            .andExpect(jsonPath("$.rows[0].actual").value(day1Actual))
            .andExpect(jsonPath("$.rows[0].difference").value(Math.round((close(80) - originClose) * 10000) / 10000.0))
            .andExpect(jsonPath("$.summary.daysWithActual").value(5));
    }

    @Test
    void differenceAndErrorPercentAreConsistentWithPredictedAndActual() throws Exception {
        predict("AAPL", FIRST.plusDays(70), FIRST.plusDays(74))
            .andExpect(jsonPath("$.rows[2].difference").value(
                Math.round((close(72) - close(69)) * 10000) / 10000.0))
            .andExpect(jsonPath("$.rows[2].errorPct").value(
                Math.round(Math.abs(close(72) - close(69)) / close(72) * 10000) / 100.0));
    }

    @Test
    void theInsideRangeFlagMatchesTheRangeForEveryDay() throws Exception {
        predict("AAPL", FIRST.plusDays(70), FIRST.plusDays(79))
            .andExpect(jsonPath("$.rows[?(@.actual >= @.low && @.actual <= @.high)].insideRange").value(
                hasItem(true)))
            .andExpect(jsonPath("$.rows[?(@.actual < @.low || @.actual > @.high)].insideRange").isEmpty());
    }

    @Test
    void aRangeThatRunsIntoTheFutureHasNoActualYetAndSkipsWeekends() throws Exception {
        // LAST is Thursday 2025-04-10: Friday 11th and Monday 14th follow, then the weekend is skipped.
        predict("AAPL", LAST.minusDays(1), LAST.plusDays(4))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.rows.length()").value(4))
            .andExpect(jsonPath("$.rows[1].date").value(LAST.toString()))
            .andExpect(jsonPath("$.rows[1].actual").value(Math.round(close(99) * 10000) / 10000.0))
            .andExpect(jsonPath("$.rows[2].date").value("2025-04-11"))
            .andExpect(jsonPath("$.rows[2].actual").value(nullValue()))
            .andExpect(jsonPath("$.rows[2].errorPct").value(nullValue()))
            .andExpect(jsonPath("$.rows[3].date").value("2025-04-14"))
            .andExpect(jsonPath("$.summary.daysWithActual").value(2))
            .andExpect(jsonPath("$.notes[*]").value(hasItem(containsString("have no actual price yet"))));
    }

    @Test
    void aRangeWhollyInTheFutureCountsTheDaysFromTheLastKnownClose() throws Exception {
        predict("AAPL", LocalDate.of(2025, 4, 14), LocalDate.of(2025, 4, 15))
            .andExpect(jsonPath("$.originDate").value(LAST.toString()))
            .andExpect(jsonPath("$.rows.length()").value(2))
            .andExpect(jsonPath("$.rows[0].dayAhead").value(2)) // Friday the 11th is day 1
            .andExpect(jsonPath("$.rows[1].dayAhead").value(3));
    }

    @Test
    void thePredictionNeverDependsOnPricesAfterTheRangeStarts() throws Exception {
        LocalDate from = FIRST.plusDays(80), to = FIRST.plusDays(82);
        String before = predict("AAPL", from, to).andReturn().getResponse().getContentAsString();

        // Change every price from the first requested day on; the prediction must not move, only the actuals.
        jdbc.update("UPDATE prices SET close = 9999 WHERE ticker = 'AAPL' AND date >= ?", from);
        entityManager.clear(); // forget the objects loaded above so the next request re-reads the changed rows
        String after = predict("AAPL", from, to).andReturn().getResponse().getContentAsString();

        for (int row = 0; row < 3; row++) {
            for (String field : new String[] {"predicted", "low", "high"}) {
                String path = "$.rows[" + row + "]." + field;
                assertEquals((Double) JsonPath.read(before, path), (Double) JsonPath.read(after, path), path);
            }
        }
        assertEquals(9999.0, (Double) JsonPath.read(after, "$.rows[0].actual"));
        assertNotEquals((Double) JsonPath.read(before, "$.rows[0].actual"), (Double) JsonPath.read(after, "$.rows[0].actual"));
    }

    @Test
    void aLongRangeIsWarnedAboutAndAnExcessiveOneIsRefused() throws Exception {
        predict("AAPL", FIRST.plusDays(75), FIRST.plusDays(89)) // 15 days ahead
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.notes[*]").value(hasItem(containsString("not been backtested"))));
        predict("AAPL", FIRST.plusDays(70), FIRST.plusDays(95)) // 26 days ahead
            .andExpect(status().isBadRequest());
    }

    @Test
    void badRequestsAreRejectedWithTheRightStatus() throws Exception {
        predict("AAPL", FIRST.plusDays(80), FIRST.plusDays(70))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.detail").value("from must not be after to")); // the message reaches the client
        predict("AAPL", FIRST.plusDays(30), FIRST.plusDays(32)).andExpect(status().isBadRequest()); // too little history
        predict("ZZZZ", FIRST.plusDays(80), FIRST.plusDays(82)).andExpect(status().isNotFound());
        mvc.perform(get("/predictions/AAPL").param("from", "2025-03-01")).andExpect(status().isBadRequest()); // no 'to'
    }
}
