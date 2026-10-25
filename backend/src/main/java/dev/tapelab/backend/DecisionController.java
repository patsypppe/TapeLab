package dev.tapelab.backend;

import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/decisions")
public class DecisionController {

    private final DecisionRepository decisions;

    public DecisionController(DecisionRepository decisions) {
        this.decisions = decisions;
    }

    /** Saved decisions, newest first; optionally for one ticker; defaults to the last 30 days. */
    @GetMapping
    public List<DecisionDto> list(
            @RequestParam(required = false) String ticker,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        LocalDate end = to != null ? to : LocalDate.now();
        LocalDate start = from != null ? from : end.minusDays(30);
        if (start.isAfter(end)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "from must not be after to");
        }
        List<Decision> found = ticker == null
            ? decisions.findByDecidedForBetweenOrderByDecidedForDescTickerAsc(start, end)
            : decisions.findByTickerAndDecidedForBetweenOrderByDecidedForDesc(ticker.toUpperCase(), start, end);
        return found.stream().map(DecisionDto::from).toList();
    }
}
