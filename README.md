# Generating Product Image from Customer Reviews

Production-quality full-stack repository for a CMU final project that studies how public product descriptions and customer reviews can be converted into image-generation-ready prompts, then compared against real posted product images.

## Assignment Alignment

This repository is structured to support all four required questions:

- `Q1`: discover candidate products, justify selection of exactly three products across different categories and popularity levels, and collect descriptions plus public customer reviews.
- `Q2`: analyze text artifacts with API-only LLM workflows, prompt engineering, chunking, and retrieval support to produce visual profiles for downstream image generation.
- `Q3`: generate 3 to 5 images per product with at least two API-only image models, iterate prompts, and compare outputs against reference product imagery.
- `Q4`: orchestrate the whole pipeline with an agentic workflow that preserves traces, artifacts, and rerun controls.

## Stage Progress

### Stage 1: Repository Skeleton

- Backend FastAPI app, Typer CLI, pydantic settings, schema layer, workflow placeholders, and smoke tests are in place.
- Frontend Vite + React + TypeScript + Tailwind + Framer Motion dashboard shell is in place with the required demo routes.
- Shared `artifacts/`, `docs/`, `prompts/`, and `reports/` folders are created for durable project outputs.
- Repository-level install, run, lint, and test commands are documented and available through `Makefile`.

### Stage 2: Presentation Frontend

- The frontend now includes a complete animated demo UI for all assignment-aligned routes:
  - Home / Overview
  - Product Selection
  - Review Explorer
  - Visual Profile
  - Image Generation
  - Comparison Dashboard
  - Agentic Workflow
- Mock artifact data now lives under `frontend/src/mock/` and is structured to resemble future real pipeline outputs.
- Home page includes animated hero content, four Q1-Q4 pipeline panels, and a rubric-focused presentation section.
- The remaining pages now provide polished, responsive, presentation-ready placeholder visualizations for charts, evidence panels, prompt versions, image grids, and workflow traces.

### Stage 3: Automated Product Discovery

- Added a marketplace discovery adapter architecture under `backend/src/app/collectors/discovery/`.
- Implemented a public search-page adapter for Best Buy with straightforward HTML parsing.
- Added one-time artifact output under `data/discovery/`:
  - `candidate_queries.json`
  - `candidates.jsonl`
  - `discovery_manifest.json`
  - `raw_html/`
- Discovery now supports caching, `--refresh`, deduplication by canonical URL, ranking by review visibility and product relevance, and failure-category reporting.
- Added parser fixtures, parser tests, documentation, and example discovery configs.

### Stage 4: One-Time Product Scraping

- Added a product-page scraper adapter architecture under `backend/src/app/collectors/product_pages/`.
- Implemented a public Target adapter that:
  - fetches product page HTML
  - fetches public `pdp_client_v1` JSON
  - extracts product title, category, description, bullets, visible rating/review count, recent public reviews, and real product image URLs
- Added strict durable artifact output under `data/raw/<product_slug>/`:
  - `product_meta.json`
  - `description.json`
  - `reviews.jsonl`
  - `images/`
  - `raw_html/`
  - `scrape_report.json`
- Added `data/raw/raw_manifest.json` with per-product completeness, counts, status, and timestamps.
- Scraping now reuses complete on-disk artifacts by default and only re-fetches when `--refresh` is passed.
- Added selected-product input tracking in `data/selected_products.jsonl` with exactly three products across distinct categories.
- Added fixture-based parser tests and mocked-network persistence tests for the scraping stage.

### Stage 5: Processed Corpus and Q1 Validation

- Added a processed corpus pipeline under `backend/src/app/services/corpus.py`.
- Raw scrape artifacts are now transformed into cleaned reusable corpora under `data/processed/<product_slug>/`:
  - `product.json`
  - `description_clean.txt`
  - `reviews_clean.jsonl`
  - `review_stats.json`
  - `image_manifest.json`
- Added `data/processed/manifest.json` for reporting-friendly global corpus metadata.
- Cleaning now normalizes whitespace, removes duplicate reviews, filters extremely short reviews, and drops low-information reviews while preserving review metadata.
- Added strict Q1 validation for:
  - exactly 3 selected products
  - 3 distinct categories
  - non-empty cleaned descriptions
  - configurable minimum cleaned review count
  - at least 1 valid real image per product
- Added generated reporting support docs:
  - `docs/q1_summary.md`
  - `docs/q1_selection_rationale_template.md`
- Added `verify-artifacts --stage q1` with human-readable and machine-readable output.
- Added tests for duplicate removal, category uniqueness, empty description failure, and minimum review threshold failure.

### Stage 6: Q2 LLM Analysis Pipeline

- Added a full API-only Q2 analysis pipeline under `backend/src/app/services/visual_profiles.py`.
- Implemented two modes:
  - `baseline_description_only`
  - `review_informed_rag`
- Added review chunking where one review is the primary chunk unit and only overly long reviews are split.
- Added a pluggable retrieval layer:
  - default local embedding cache retriever
  - optional managed vector DB adapter placeholder
- Implemented aspect-specific retrieval queries for:
  - appearance and shape
  - color and finish
  - material and texture
  - size and scale
  - expectation vs reality mismatches
- Added a three-step prompt chain:
  - aspect evidence extraction
  - conflict resolution
  - final `VisualProfile` synthesis
- Added editable prompt templates under `prompts/q2/`.
- Added schema validation plus retry-on-parse-failure for every LLM step.
- Added output paths under `outputs/visual_profiles/<product_slug>/` for:
  - `baseline_description_only.json`
  - `review_informed_rag.json`
  - `retrieval_evidence.json`
  - `llm_trace.json`
- Added a retrieval fallback path so `review_informed_rag` can degrade to keyword-overlap retrieval when the configured OpenAI project lacks embedding-model access.
- Added tests for:
  - schema validation
  - prompt loading
  - mocked LLM pipeline execution
  - retrieval ranking and cache behavior

## Repository Structure

```text
.
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── artifacts/
│   └── README.md
├── backend/
│   ├── .env.example
│   ├── pyproject.toml
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── collectors/
│   │   │   ├── config/
│   │   │   ├── evaluation/
│   │   │   ├── imagegen/
│   │   │   ├── llm/
│   │   │   ├── models/
│   │   │   ├── retrieval/
│   │   │   ├── services/
│   │   │   ├── utils/
│   │   │   ├── workflow/
│   │   │   └── main.py
│   │   └── cli/
│   └── tests/
├── docs/
│   └── README.md
├── configs/
│   ├── product_queries.example.yaml
│   └── product_queries.yaml
├── data/
│   ├── discovery/
│   ├── raw/
│   └── selected_products.jsonl
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.cjs
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── mock/
│   │   ├── pages/
│   │   └── styles/
│   ├── tailwind.config.cjs
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── prompts/
│   └── README.md
└── reports/
    └── README.md
```

## Backend Overview

- FastAPI app entrypoint: [backend/src/app/main.py](/Users/macbook/Desktop/ai-lab-final/backend/src/app/main.py)
- Health endpoint: [backend/src/app/api/routes.py](/Users/macbook/Desktop/ai-lab-final/backend/src/app/api/routes.py)
- Settings: [backend/src/app/config/settings.py](/Users/macbook/Desktop/ai-lab-final/backend/src/app/config/settings.py)
- Schemas: [backend/src/app/models/schemas.py](/Users/macbook/Desktop/ai-lab-final/backend/src/app/models/schemas.py)
- CLI: [backend/src/cli/main.py](/Users/macbook/Desktop/ai-lab-final/backend/src/cli/main.py)

Implemented CLI placeholders:

- `discover-products`
- `scrape-product`
- `scrape-all`
- `build-corpus`
- `extract-visual-profile`
- `generate-images`
- `evaluate-images`
- `run-workflow`
- `verify-artifacts`
- `serve-api`

Discovery command now supports:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml --refresh
```

Scraping commands now support:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-all --input ../data/selected_products.jsonl --max-reviews 100
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-all --input ../data/selected_products.jsonl --max-reviews 100 --refresh
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-product --url https://www.target.com/p/levoit-core-300-air-purifier-white/-/A-81910071 --max-reviews 100
```

Processed corpus and Q1 verification now support:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main build-corpus --raw-dir ../data/raw --output-dir ../data/processed --input ../data/selected_products.jsonl
PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage q1 --processed-dir ../data/processed --input ../data/selected_products.jsonl
```

Q2 visual-profile extraction now supports:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product levoit-core-300-air-purifier-white-81910071 --mode baseline_description_only
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product levoit-core-300-air-purifier-white-81910071 --mode review_informed_rag
```

## Frontend Overview

Implemented routes:

- `/`
- `/products`
- `/reviews`
- `/profiles`
- `/generation`
- `/comparison`
- `/workflow`

Reusable UI components:

- `StatCard`
- `StageCard`
- `ArtifactBadge`
- `AnimatedSection`
- `ImageGrid`
- `Timeline`
- `PageHeader`
- `ConfidenceChip`
- `FlowDiagram`
- `PromptCard`

## Local Setup

### Backend install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e "backend[dev]"
cp .env.example .env
```

### Frontend install

```bash
cd frontend
npm install
```

## Run Locally

### Backend API

```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --app-dir src --port 8000
```

### Backend CLI

```bash
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-all --input ../data/selected_products.jsonl --max-reviews 100
PYTHONPATH=src ../.venv/bin/python -m cli.main build-corpus --raw-dir ../data/raw --output-dir ../data/processed --input ../data/selected_products.jsonl
PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage q1 --processed-dir ../data/processed --input ../data/selected_products.jsonl
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product <product-slug> --mode baseline_description_only
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product <product-slug> --mode review_informed_rag
PYTHONPATH=src ../.venv/bin/python -m cli.main run-workflow
```

### Frontend

```bash
cd frontend
npm run dev
```

## Validation Commands

### Backend checks

```bash
source .venv/bin/activate
cd backend
pytest
ruff check src tests
black --check src tests
mypy src
```

### Frontend build

```bash
cd frontend
npm run build
```

## Current Limitations

- Product discovery, one-time product scraping, Q1 processed-corpus validation, and the Q2 LLM analysis pipeline are implemented; image generation and evaluation are still pending.
- Discovery is currently implemented for Best Buy search pages only.
- Product scraping is currently implemented for Target public product pages only.
- Target's public PDP payload exposes only a recent-review block, so the current scraper captures a truthful subset of public reviews and marks those products as `partial_success`.
- The Q2 pipeline is fully implemented and tested. A real local smoke run was completed for `levoit-core-300-air-purifier-white-81910071` in both modes.
- The tested OpenAI project key allowed chat completions but not `text-embedding-3-small`, so `review_informed_rag` automatically fell back to keyword-overlap retrieval during the live run.
- Frontend currently uses presentation-friendly mock data only and does not call backend APIs yet.
- Workflow traces and downstream report exports are still placeholders awaiting later stages.
- Comparison and generation pages currently use styled placeholders rather than real saved image thumbnails.

## Next Recommended Stage

Implement `Q3` end-to-end:

- add API-only image generation providers and prompt iteration records
- generate 3-5 images per product for at least two models
- compare generated images to real product images
- connect the frontend Visual Profile / Generation / Comparison pages to saved outputs
