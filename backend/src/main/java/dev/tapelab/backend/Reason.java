package dev.tapelab.backend;

/** One analyst's contribution to a decision, as stored in the decisions.reasons JSON. */
public record Reason(String analyst, double score, String rationale) {
}
