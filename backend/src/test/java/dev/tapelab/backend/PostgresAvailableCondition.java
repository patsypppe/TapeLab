package dev.tapelab.backend;

import org.junit.jupiter.api.extension.ConditionEvaluationResult;
import org.junit.jupiter.api.extension.ExecutionCondition;
import org.junit.jupiter.api.extension.ExtensionContext;

/** Skips database tests when Postgres is not reachable, except on CI, where it is required. */
class PostgresAvailableCondition implements ExecutionCondition {

    @Override
    public ConditionEvaluationResult evaluateExecutionCondition(ExtensionContext context) {
        if (System.getenv("CI") != null) {
            // On a CI machine a missing database must fail the build, not silently skip the tests.
            return ConditionEvaluationResult.enabled("CI is set: Postgres is required");
        }
        return PostgresTest.available()
            ? ConditionEvaluationResult.enabled("Postgres is reachable")
            : ConditionEvaluationResult.disabled("Postgres is not running (docker compose up -d)");
    }
}
