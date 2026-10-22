package dev.tapelab.orchestrator;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;

class ExperimentGridTest {
    @Test
    void expandsFullCartesianProductAndUppercasesTickers() {
        var cells = ExperimentGrid.expand(List.of("aapl", "msft"),
            List.of(LocalDate.of(2025, 3, 3), LocalDate.of(2025, 3, 4), LocalDate.of(2025, 3, 5)),
            List.of("debate0", "debate3"));
        assertEquals(12, cells.size());
        assertEquals("AAPL", cells.get(0).ticker());
    }
}
