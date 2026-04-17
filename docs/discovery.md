# Discovery Stage

This stage automatically discovers candidate product links from publicly accessible marketplace search pages and writes durable local artifacts.

## Current Adapter

- `bestbuy`: parses public Best Buy search result pages using straightforward HTML parsing.

## Inputs

- CLI command:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml --refresh
```

- Config file example: [configs/product_queries.example.yaml](/Users/macbook/Desktop/ai-lab-final/configs/product_queries.example.yaml)

## Outputs

Discovery artifacts are written to:

- `data/discovery/candidate_queries.json`
- `data/discovery/candidates.jsonl`
- `data/discovery/discovery_manifest.json`
- `data/discovery/raw_html/`

## Caching Behavior

- Reuses existing artifacts by default when they already exist.
- Use `--refresh` to force re-discovery.
- Use `--no-reuse-existing` to bypass artifact reuse explicitly.

## Failure Categories

- `blocked`
- `parse_failed`
- `no_results`
- `duplicate_removed`

## Manual Review

After discovery finishes:

1. Open `data/discovery/candidates.jsonl`.
2. Sort or inspect by `ranking_score`, `visible_review_count`, and `category_guess`.
3. Visit the saved `canonical_url` values manually.
4. Choose the final three products with category diversity, strong review coverage, and presentation value.
