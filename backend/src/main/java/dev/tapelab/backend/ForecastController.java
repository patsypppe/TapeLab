package dev.tapelab.backend;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/forecasts")
public class ForecastController {

    private final ForecastRepository forecasts;

    public ForecastController(ForecastRepository forecasts) {
        this.forecasts = forecasts;
    }

    /** The newest saved 10-day forecast range for a ticker; 404 if none has been made yet. */
    @GetMapping("/{ticker}")
    public ForecastDto latest(@PathVariable String ticker, @RequestParam(defaultValue = "random_walk") String model) {
        return forecasts.findFirstByTickerAndModelOrderByAsOfDescMadeAtDesc(ticker.toUpperCase(), model)
            .map(ForecastDto::from)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND,
                "No forecast for " + ticker.toUpperCase() + " yet. Run: python -m tapelab.predict " + ticker.toUpperCase()));
    }
}
