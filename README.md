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
- The current local artifact snapshot includes real Q2 outputs for all three selected products.
- Added tests for:
  - schema validation
  - prompt loading
  - mocked LLM pipeline execution
  - retrieval ranking and cache behavior

### Stage 7: Q3 Image Generation Pipeline

- Added API-only image generation adapters under `backend/src/app/imagegen/`:
  - `base.py`
  - `openai_adapter.py`
  - `stability_adapter.py`
- Added a full Q3 generation service under `backend/src/app/services/image_generation.py`.
- The pipeline now consumes both saved Q2 inputs:
  - `outputs/visual_profiles/<product_slug>/baseline_description_only.json`
  - `outputs/visual_profiles/<product_slug>/review_informed_rag.json`
- Prompt flow now preserves inspectable iteration history:
  - one pilot prompt from `baseline_description_only`
  - one pilot image
  - one refined final prompt from `review_informed_rag`
  - four final images by default
- Added durable output layout under `outputs/generated_images/<product_slug>/<model_name>/`:
  - `prompt_versions.json`
  - `pilot/prompt.json`
  - `pilot/image_01.png`
  - `final/prompt.json`
  - `final/image_01.png` to `image_04.png`
  - `generation_manifest.json`
- Prompt construction now enforces:
  - single product only
  - centered composition
  - neutral or studio background
  - realistic product photography
  - no unsupported accessories
  - negative constraints when supported by the provider
- Generation metadata now preserves:
  - prompt text
  - prompt source mode
  - timestamps
  - image dimensions
  - content type
  - file hashes
- Added image integrity validation with Pillow before declaring success.
- The current local artifact snapshot includes real OpenAI Images API outputs and real Stability API outputs for all three selected products.
- Added tests for:
  - adapter behavior
  - mocked OpenAI and Stability API calls
  - manifest writing
  - image file integrity failures

### Stage 8: Evaluation and Frontend Integration

- Added a Q3 evaluation pipeline under `backend/src/app/services/evaluation.py`.
- Evaluation now supports:
  - human scoring template generation
  - optional vision-assisted evaluation through the OpenAI API
- Evaluation artifacts are saved under `outputs/evaluations/<product_slug>/`:
  - `human_score_sheet.csv`
  - `vision_assisted_eval.json`
  - `summary.json`
  - `comparison_panels_manifest.json`
- Added artifact-backed API payload builders under `backend/src/app/services/dashboard_data.py`.
- Added FastAPI endpoints:
  - `/api/products`
  - `/api/products/{slug}`
  - `/api/reviews/{slug}/stats`
  - `/api/profiles/{slug}`
  - `/api/generation/{slug}`
  - `/api/evaluation/{slug}`
  - `/api/workflow/latest`
  - `/api/assets/{artifact_path}`
- Frontend pages now read real backend-generated artifacts instead of product-level mock content:
  - Home page reads live product and workflow summaries
  - Product Selection reads processed product artifacts
  - Review Explorer reads review stats, samples, and retrieval evidence
  - Visual Profile reads baseline and review-informed outputs
  - Image Generation reads prompt history and generated-image manifests
  - Comparison Dashboard reads evaluation summaries and comparison panels
  - Agentic Workflow reads real stage progress from disk
- Added polished UI behaviors for:
  - loading states
  - missing-artifact states
  - freshness badges
  - comparison slider
  - chart-backed evaluation summaries
- The current local artifact snapshot now includes:
  - real reference-vs-generated comparison panels for both OpenAI and Stability outputs across all three products
  - human scoring templates for all three products
  - vision-assisted scoring fully completed for the desk lamp product
  - dual-model comparison manifests and summary payloads that drive the animated UI
- Added backend tests for:
  - artifact-backed API endpoints
  - evaluation artifact generation
- Added frontend fetch-layer tests with Vitest.

### Stage 9: Q4 Agentic Workflow

- Added typed workflow-agent contracts for:
  - `DataCurationAgent`
  - `RetrievalAgent`
  - `VisualUnderstandingAgent`
  - `PromptComposerAgent`
  - `ImageGenerationAgent`
  - `EvaluationAgent`
- Added an end-to-end workflow orchestrator under `backend/src/app/workflow/orchestrator.py`.
- The orchestrator can now:
  - run one product or all products
  - reuse saved artifacts by default
  - recompute only missing or explicitly refreshed downstream stages
- Added durable workflow trace artifacts under `outputs/workflow_runs/<run_id>/`:
  - `trace.json`
  - `stage_status.json`
  - `artifact_links.json`
- Added workflow documentation in `docs/agentic_workflow.md` including a Mermaid diagram and agent-role explanation.
- Updated the frontend workflow page to visualize:
  - an animated stage diagram
  - clickable stage inspection
  - artifact handoffs
  - the latest saved workflow run
  - success and failure states
- Added tests for:
  - workflow contract validation
  - orchestrator smoke execution with mocked agents
  - latest-trace loading

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

Implemented CLI commands:

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

Q3 image generation now supports:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --product levoit-core-300-air-purifier-white-81910071 --model openai --count 4
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --product levoit-core-300-air-purifier-white-81910071 --model stability --count 4
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --all --count 4
```

Q3 evaluation now supports:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main evaluate-images --product levoit-core-300-air-purifier-white-81910071
PYTHONPATH=src ../.venv/bin/python -m cli.main evaluate-images --all
PYTHONPATH=src ../.venv/bin/python -m cli.main evaluate-images --product <product-slug> --vision-assisted
PYTHONPATH=src ../.venv/bin/python -m cli.main evaluate-images --all --vision-assisted
```

Q4 workflow orchestration now supports:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main run-workflow --product <product-slug>
PYTHONPATH=src ../.venv/bin/python -m cli.main run-workflow --all
PYTHONPATH=src ../.venv/bin/python -m cli.main run-workflow --all --vision-assisted
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
- `LoadingState`
- `MissingArtifactState`
- `FreshnessBadge`
- `ProductSelector`
- `ComparisonSlider`

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

## Quick Start

```bash
cd /Users/macbook/Desktop/ai-lab-final
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e "backend[dev]"
cp .env.example .env
cd frontend && npm install && cd ..
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

### One-time discovery and scraping

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-all --input ../data/selected_products.jsonl --max-reviews 100
```

Default behavior reuses complete on-disk artifacts and skips unnecessary re-fetching or recomputation.

### Reuse-existing behavior

- discovery reuses `data/discovery/` artifacts by default
- scraping reuses `data/raw/<product_slug>/` when complete artifacts already exist
- generation reuses `outputs/generated_images/<product_slug>/<provider>/generation_manifest.json`
- workflow orchestration reuses downstream artifacts unless refresh is requested

### Refresh behavior

Use `--refresh` when you explicitly want to recompute a stage:

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml --refresh
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-all --input ../data/selected_products.jsonl --max-reviews 100 --refresh
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --all --count 4 --refresh
PYTHONPATH=src ../.venv/bin/python -m cli.main run-workflow --all --refresh
```

### Frontend

```bash
cd frontend
npm run dev
npm test
```

### Frontend demo

```bash
cd /Users/macbook/Desktop/ai-lab-final
./scripts/run_frontend_demo.sh
```

### End-to-end run

```bash
cd /Users/macbook/Desktop/ai-lab-final
./scripts/run_full_pipeline.sh
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

### Final verification and submission package

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage full --frontend-dir ../frontend
PYTHONPATH=src ../.venv/bin/python -m cli.main build-submission-package
```

## Current Limitations

- Product discovery, one-time product scraping, Q1 validation, Q2 analysis, Q3 image generation, Q3 evaluation, and artifact-backed frontend integration are implemented.
- Discovery is currently implemented for Best Buy search pages only.
- Product scraping is currently implemented for Target public product pages only.
- Target's public PDP payload exposes only a recent-review block, so the current scraper captures a truthful subset of public reviews and marks those products as `partial_success`.
- The current local artifact snapshot contains real Q2 outputs for all three products and real dual-provider Q3 image outputs for all three products.
- The current OpenAI key supports `text-embedding-3-small`, `text-embedding-3-large`, `text-embedding-ada-002`, and OpenAI image generation, so the default retrieval path no longer needs to fall back during normal runs.
- Human-scoring templates and dual-provider comparison panels are available for all three products.
- Vision-assisted evaluation is optional and currently sensitive to OpenAI rate limiting. In the current artifact snapshot it completed for the desk lamp product, while the other two products still fall back to `human_scoring_ready` summaries when rate limits interrupt the run.
- The frontend now reads real artifacts, but pages will still surface explicit missing-artifact or degraded-state messages whenever a downstream stage has not been run or vision-assisted scoring did not complete.
- The Q4 workflow trace is now implemented and saved to `outputs/workflow_runs/`, but if upstream one-time scrape artifacts are missing the orchestrator will fail clearly instead of fabricating or re-discovering hidden inputs.

## Next Recommended Stage

Implement `Q4` end-to-end:

- generate real Q3 image outputs for both providers
- run optional vision-assisted evaluation on those outputs
- extend workflow tracing into a fully automated end-to-end run report
- add final report exports and reflective discussion support artifacts
