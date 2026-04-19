Return JSON with this shape:
{
  "resolved_high_confidence_attributes": [
    {
      "attribute": "supported attribute",
      "rationale": "why it survives conflict resolution",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "low_confidence_or_conflicting_attributes": [
    {
      "attribute": "uncertain/conflicting attribute",
      "rationale": "what conflict or weakness remains",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "common_mismatches_between_expectation_and_reality": [
    {
      "mismatch": "common mismatch theme",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "negative_constraints": ["things an image prompt should avoid"],
  "resolution_notes": ["short note about major conflicts or uncertainty"]
}

Rules:
- Merge duplicates and keep the strongest evidence.
- Do not convert weak evidence into high-confidence attributes.
- Negative constraints should be practical prompt constraints, not full sentences.
- If a mismatch is only mentioned once and weakly, do not include it.
