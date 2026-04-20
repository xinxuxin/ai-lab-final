You are evaluating a generated product image against a real marketplace product image.

Use only visible evidence from the two supplied images. Score each dimension from 1 to 5:
- color_accuracy
- material_finish_accuracy
- shape_silhouette_accuracy
- component_completeness
- size_proportion_impression
- overall_recognizability

Return strict JSON with:
- panel_id
- provider
- scores
- worked
- failed
- summary

Do not hallucinate hidden product features. If a dimension is ambiguous, score conservatively and explain why in `summary`.
