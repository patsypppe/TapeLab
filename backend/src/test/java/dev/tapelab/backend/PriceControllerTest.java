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
@Transactional  // each test's rows are rolled back, so tests do not see each other's data
class PriceControllerTest extends PostgresTest {

    @Autowired
    MockMvc mvc;
    @Autowired
    JdbcTemplate jdbc;

    @BeforeEach
    void insertRows() {
        String sql = "INSERT INTO prices (ticker, date, open, high, low, close, volume) VALUES (?, ?::date, ?, ?, ?, ?, ?)";
        jdbc.update(sql, "AAPL", "2025-01-06", 12, 14, 11, 13.5, 3000);
        jdbc.update(sql, "AAPL", "2025-01-02", 10, 12, 9, 10.5, 1000);
        jdbc.update(sql, "AAPL", "2025-01-03", 10, 13, 10, 12, 2000);
        jdbc.update(sql, "MSFT", "2025-01-02", 50, 52, 49, 51, 500);
    }

    @Test
    void returnsOneTickersRowsInDateOrderWithinTheRange() throws Exception {
        mvc.perform(get("/prices/AAPL").param("from", "2025-01-02").param("to", "2025-01-03"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2))
            .andExpect(jsonPath("$[0].date").value("2025-01-02"))
            .andExpect(jsonPath("$[0].close").value(10.5))
            .andExpect(jsonPath("$[0].volume").value(1000))
            .andExpect(jsonPath("$[1].date").value("2025-01-03"));
    }

    @Test
    void ordersByDateEvenThoughRowsWereInsertedOutOfOrder() throws Exception {
        mvc.perform(get("/prices/AAPL").param("from", "2025-01-01").param("to", "2025-01-31"))
            .andExpect(jsonPath("$.length()").value(3))
            .andExpect(jsonPath("$[2].date").value("2025-01-06"));
    }

    @Test
    void tickerIsCaseInsensitive() throws Exception {
        mvc.perform(get("/prices/msft").param("from", "2025-01-01").param("to", "2025-01-31"))
            .andExpect(jsonPath("$.length()").value(1))
            .andExpect(jsonPath("$[0].close").value(51));
    }

    @Test
    void unknownTickerGivesAnEmptyList() throws Exception {
        mvc.perform(get("/prices/ZZZZ").param("from", "2025-01-01").param("to", "2025-01-31"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(0));
    }

    @Test
    void fromAfterToIsABadRequest() throws Exception {
        mvc.perform(get("/prices/AAPL").param("from", "2025-02-01").param("to", "2025-01-01"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void malformedDateIsABadRequest() throws Exception {
        mvc.perform(get("/prices/AAPL").param("from", "not-a-date"))
            .andExpect(status().isBadRequest());
    }
}
