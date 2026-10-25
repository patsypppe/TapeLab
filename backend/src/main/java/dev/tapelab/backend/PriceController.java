package dev.tapelab.backend;

import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/prices")
public class PriceController {

    private final PriceRepository prices;

    public PriceController(PriceRepository prices) {
        this.prices = prices;
    }

    /** Daily prices for one ticker between two dates; defaults to the last year up to today. */
    @GetMapping("/{ticker}")
    public List<PriceDto> list(
            @PathVariable String ticker,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        LocalDate end = to != null ? to : LocalDate.now();
        LocalDate start = from != null ? from : end.minusYears(1);
        if (start.isAfter(end)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "from must not be after to");
        }
        return prices.findByIdTickerAndIdDateBetweenOrderByIdDate(ticker.toUpperCase(), start, end)
            .stream().map(PriceDto::from).toList();
    }
}
