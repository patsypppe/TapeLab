package dev.tapelab.backend;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

class BackendApplicationTest extends PostgresTest {

    @Autowired
    JdbcTemplate jdbc;

    @Test
    void contextLoadsAgainstTheRealSchema() {
        // Passes if Spring starts and the migrations created the tables the app expects.
        Integer tables = jdbc.queryForObject(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = current_schema()"
                + " AND table_name IN ('prices', 'filings', 'filing_chunks', 'filing_scores', 'decisions')",
            Integer.class);
        assertEquals(5, tables);
    }
}
