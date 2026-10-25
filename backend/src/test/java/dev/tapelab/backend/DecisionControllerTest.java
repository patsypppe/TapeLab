package dev.tapelab.backend;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

@AutoConfigureMockMvc
@Transactional
class DecisionControllerTest extends PostgresTest {

    @Autowired
    MockMvc mvc;
    @Autowired
    JdbcTemplate jdbc;

    @BeforeEach
    void insertRows() {
        String sql = "INSERT INTO decisions (ticker, decided_for, position, reasons, config) "
            + "VALUES (?, ?::date, ?, ?::jsonb, ?::jsonb)";
        String reasons = "[{\"analyst\": \"technical\", \"score\": 0.31, \"rationale\": \"SMA10 above SMA30\"},"
            + " {\"analyst\": \"fundamentals\", \"score\": 0.5, \"rationale\": \"strong growth\"}]";
        String config = "{\"model\": \"fake\", \"weights\": \"equal\"}";
        jdbc.update(sql, "AAPL", "2025-01-02", 1, reasons, config);
        jdbc.update(sql, "AAPL", "2025-01-03", 0, "[]", config);
        jdbc.update(sql, "MSFT", "2025-01-03", 1, "[]", config);
    }

    @Test
    void returnsOneTickersDecisionsNewestFirstWithParsedReasons() throws Exception {
        mvc.perform(get("/decisions").param("ticker", "aapl").param("from", "2025-01-01").param("to", "2025-01-31"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2))
            .andExpect(jsonPath("$[0].decidedFor").value("2025-01-03"))
            .andExpect(jsonPath("$[1].decidedFor").value("2025-01-02"))
            .andExpect(jsonPath("$[1].position").value(1.0))
            .andExpect(jsonPath("$[1].reasons.length()").value(2))
            .andExpect(jsonPath("$[1].reasons[0].analyst").value("technical"))
            .andExpect(jsonPath("$[1].reasons[0].score").value(0.31))
            .andExpect(jsonPath("$[1].reasons[1].rationale").value("strong growth"))
            .andExpect(jsonPath("$[1].config.model").value("fake"));
    }

    @Test
    void withoutATickerReturnsEveryTicker() throws Exception {
        mvc.perform(get("/decisions").param("from", "2025-01-01").param("to", "2025-01-31"))
            .andExpect(jsonPath("$.length()").value(3))
            .andExpect(jsonPath("$[0].ticker").value("AAPL"))  // same day: tickers in alphabetical order
            .andExpect(jsonPath("$[1].ticker").value("MSFT"));
    }

    @Test
    void dateRangeLimitsTheResults() throws Exception {
        mvc.perform(get("/decisions").param("from", "2025-01-03").param("to", "2025-01-03"))
            .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    void unknownTickerGivesAnEmptyList() throws Exception {
        mvc.perform(get("/decisions").param("ticker", "ZZZZ").param("from", "2025-01-01").param("to", "2025-01-31"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(0));
    }

    @Test
    void fromAfterToIsABadRequest() throws Exception {
        mvc.perform(get("/decisions").param("from", "2025-02-01").param("to", "2025-01-01"))
            .andExpect(status().isBadRequest());
    }
}
