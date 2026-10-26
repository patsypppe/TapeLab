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
class ForecastControllerTest extends PostgresTest {

    @Autowired
    MockMvc mvc;
    @Autowired
    JdbcTemplate jdbc;

    @BeforeEach
    void insertRows() {
        String sql = "INSERT INTO forecasts (ticker, as_of, model, horizon, last_close, points) "
            + "VALUES (?, ?::date, ?, 10, ?, ?::jsonb)";
        String older = "[{\"day_ahead\": 1, \"date\": \"2025-01-03\", \"median\": 100.0, \"low\": 95.0, \"high\": 105.0}]";
        String newer = "[{\"day_ahead\": 1, \"date\": \"2025-06-23\", \"median\": 178.47, \"low\": 175.0, \"high\": 182.25},"
            + " {\"day_ahead\": 2, \"date\": \"2025-06-24\", \"median\": 178.47, \"low\": 173.5, \"high\": 183.9}]";
        jdbc.update(sql, "AAPL", "2025-01-02", "random_walk", 100, older);
        jdbc.update(sql, "AAPL", "2025-06-20", "random_walk", 178.47, newer);
        jdbc.update(sql, "AAPL", "2025-06-20", "drift", 178.47, "[]");
    }

    @Test
    void returnsTheNewestForecastWithItsRangesInCamelCase() throws Exception {
        mvc.perform(get("/forecasts/aapl"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.ticker").value("AAPL"))
            .andExpect(jsonPath("$.asOf").value("2025-06-20"))
            .andExpect(jsonPath("$.model").value("random_walk"))
            .andExpect(jsonPath("$.horizon").value(10))
            .andExpect(jsonPath("$.lastClose").value(178.47))
            .andExpect(jsonPath("$.points.length()").value(2))
            .andExpect(jsonPath("$.points[0].dayAhead").value(1))
            .andExpect(jsonPath("$.points[0].date").value("2025-06-23"))
            .andExpect(jsonPath("$.points[0].low").value(175.0))
            .andExpect(jsonPath("$.points[1].high").value(183.9));
    }

    @Test
    void anotherModelCanBeRequested() throws Exception {
        mvc.perform(get("/forecasts/AAPL").param("model", "drift"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.model").value("drift"))
            .andExpect(jsonPath("$.points.length()").value(0));
    }

    @Test
    void aTickerWithNoForecastIsNotFoundWithAHelpfulMessage() throws Exception {
        mvc.perform(get("/forecasts/ZZZZ"))
            .andExpect(status().isNotFound());
    }
}
