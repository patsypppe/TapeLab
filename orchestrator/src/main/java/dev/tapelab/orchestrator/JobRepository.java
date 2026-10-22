package dev.tapelab.orchestrator;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface JobRepository extends JpaRepository<Job, Long> {
    List<Job> findByExperimentId(Long experimentId);
    long countByExperimentIdAndStatus(Long experimentId, Job.Status status);
}
