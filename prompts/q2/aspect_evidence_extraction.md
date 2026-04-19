Return JSON with this shape:
{
  "aspect_key": "<repeat input aspect_key>",
  "supported_attributes": [
    {
      "attribute": "short visual/material/size attribute",
      "rationale": "why the evidence supports it",
      "evidence_snippets": ["direct snippet 1", "direct snippet 2"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "conflicting_or_uncertain_attributes": [
    {
      "attribute": "short uncertain or conflicting attribute",
      "rationale": "why this remains uncertain or conflicting",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ],
  "expectation_reality_mismatches": [
    {
      "mismatch": "difference between expectation and real product experience",
      "evidence_snippets": ["direct snippet"],
      "source_chunk_ids": ["chunk-id"],
      "source_review_ids": ["review-id"]
    }
  ]
}

Rules:
- Ground every attribute in the provided evidence only.
- Prefer fewer, stronger attributes over long speculative lists.
- Keep snippets verbatim and short.
- If evidence is weak, place the attribute under conflicting_or_uncertain_attributes.
- If there is no support for an item, return an empty list for that section.
