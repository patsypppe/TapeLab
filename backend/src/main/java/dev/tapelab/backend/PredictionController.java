package dev.tapelab.backend;

import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/predictions")
public class PredictionController {

    private final PredictionService predictions;

    public PredictionController(PredictionService predictions) {
        this.predictions = predictions;
    }

    /** A predicted price and 80% range for each date from..to, set against the actual price where known. */
    @GetMapping("/{ticker}")
    public PredictionDto predict(
            @PathVariable String ticker,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return predictions.predict(ticker, from, to);
    }
}
