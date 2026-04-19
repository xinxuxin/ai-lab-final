Return JSON with this shape:
{
  "product_name": "full product name",
  "category": "category",
  "high_confidence_visual_attributes": [
    {
      "attribute": "supported attribute",
      "rationale": "brief why",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "low_confidence_or_conflicting_attributes": [
    {
      "attribute": "uncertain attribute",
      "rationale": "why it is uncertain",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "common_mismatches_between_expectation_and_reality": [
    {
      "mismatch": "expectation vs reality gap",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "prompt_ready_description": "concise image-generation-ready description grounded in evidence",
  "negative_constraints": ["constraint one", "constraint two"]
}

Rules:
- The prompt_ready_description should be vivid but grounded.
- Include only attributes supported by the provided description/specs/evidence.
- If the listing and reviews disagree, keep the disagreement in low_confidence_or_conflicting_attributes.
- Negative constraints should explicitly avoid unsupported or contradicted details.
