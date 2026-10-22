package dev.tapelab.orchestrator;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/experiments")
public class ExperimentController {

    public record CreateRequest(@NotEmpty List<String> tickers, @NotEmpty List<LocalDate> dates,
                                @NotEmpty List<String> configs) {}

    private final JobRepository jobs;
    private final AtomicLong ids = new AtomicLong();

    public ExperimentController(JobRepository jobs) {
        this.jobs = jobs;
        this.ids.set(jobs.findAll().stream().mapToLong(Job::getExperimentId).max().orElse(0));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String, Object> create(@Valid @RequestBody CreateRequest req) {
        long id = ids.incrementAndGet();
        var cells = ExperimentGrid.expand(req.tickers(), req.dates(), req.configs());
        jobs.saveAll(cells.stream().map(c -> new Job(id, c.ticker(), c.date(), c.config())).toList());
        return Map.of("experimentId", id, "jobs", cells.size());
    }

    @GetMapping("/{id}")
    public Map<Job.Status, Long> status(@PathVariable long id) {
        Map<Job.Status, Long> out = new EnumMap<>(Job.Status.class);
        Arrays.stream(Job.Status.values()).forEach(s -> out.put(s, jobs.countByExperimentIdAndStatus(id, s)));
        return out;
    }
}
