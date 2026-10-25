package dev.tapelab.backend;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.util.UUID;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

/**
 * Base class for tests that need the real database tables. It creates an empty throwaway schema and
 * points the app at it; Flyway then builds the tables from the migration files at startup, and the
 * schema is dropped when the tests finish.
 */
@SpringBootTest
@ExtendWith(PostgresAvailableCondition.class)
abstract class PostgresTest {

    private static final String URL = env("DB_URL", "jdbc:postgresql://localhost:5434/tapelab");
    private static final String USER = env("DB_USER", "tapelab");
    private static final String PASSWORD = env("DB_PASSWORD", "tapelab");
    private static final String SCHEMA = "test_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8);
    private static boolean created;

    private static String env(String name, String fallback) {
        String value = System.getenv(name);
        return value == null ? fallback : value;
    }

    static boolean available() {
        try (Connection ignored = DriverManager.getConnection(URL, USER, PASSWORD)) {
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private static synchronized void createSchema() throws Exception {
        if (created) {
            return;
        }
        try (Connection c = DriverManager.getConnection(URL, USER, PASSWORD); Statement s = c.createStatement()) {
            s.execute("CREATE SCHEMA " + SCHEMA);
        }
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try (Connection c = DriverManager.getConnection(URL, USER, PASSWORD); Statement s = c.createStatement()) {
                s.execute("DROP SCHEMA " + SCHEMA + " CASCADE");
            } catch (Exception ignored) {
                // best effort: a leftover test schema is harmless
            }
        }));
        created = true;
    }

    @DynamicPropertySource
    static void database(DynamicPropertyRegistry registry) throws Exception {
        createSchema();
        registry.add("spring.datasource.url", () -> URL + "?currentSchema=" + SCHEMA);
        registry.add("spring.datasource.username", () -> USER);
        registry.add("spring.datasource.password", () -> PASSWORD);
        // Tests must check the Flyway tables, never rebuild them, whatever stale config is in target/.
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "validate");
    }
}
