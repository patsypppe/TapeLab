package dev.tapelab.backend;

import org.junit.jupiter.api.extension.ConditionEvaluationResult;
import org.junit.jupiter.api.extension.ExecutionCondition;
import org.junit.jupiter.api.extension.ExtensionContext;

/** Skips database tests when Postgres is not reachable, instead of failing them. */
class PostgresAvailableCondition implements ExecutionCondition {

    @Override
    public ConditionEvaluationResult evaluateExecutionCondition(ExtensionContext context) {
        return PostgresTest.available()
            ? ConditionEvaluationResult.enabled("Postgres is reachable")
            : ConditionEvaluationResult.disabled("Postgres is not running (docker compose up -d)");
    }
}
