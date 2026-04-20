# Generating Product Image from Customer Reviews

Production-quality full-stack repository for a CMU final project that asks whether public product descriptions and customer reviews can be converted into grounded visual profiles, then used to generate realistic product images and compare them against real posted product photos.

## Status

This repository is in its completed submission state.

- `Q1` completed: product discovery, final product selection, public scraping, cleaning, and strict validation
- `Q2` completed: API-only LLM analysis with baseline and review-informed RAG modes
- `Q3` completed: dual-model image generation with OpenAI Images API and Stability AI API
- `Q4` completed: typed multi-agent workflow orchestration with saved traces
- frontend completed: artifact-backed presentation UI across all required pages
- verification completed: `verify-artifacts --stage full` passes against saved artifacts

## Master Guide

The most detailed project reference is:

- [docs/master_guide.md](/Users/macbook/Desktop/ai-lab-final/docs/master_guide.md)

Use that document for:

- presentation preparation
- experiment design details
- product rationale
- Q1 to Q4 implementation walkthrough
- evaluation results and model comparison
- workflow explanation
- reproducibility notes

## Project Goal

The core question is:

> Can review-grounded textual evidence improve product image generation compared with using product descriptions alone?

The repository answers this with an artifact-first pipeline:

1. discover candidate products from public marketplace pages
2. select exactly 3 products from distinct categories
3. scrape public descriptions, public reviews, and real product images once
4. clean the data into reusable corpora
5. extract structured visual profiles using API-only LLM analysis
6. generate product images using two API-only image models
7. compare generated images with real product images
8. orchestrate everything through a typed agentic workflow

## Final Selected Products

The final selected products are stored in [data/selected_products.jsonl](/Users/macbook/Desktop/ai-lab-final/data/selected_products.jsonl).

They are:

1. JBL Tour One M2 Wireless Over-Ear Adaptive Noise Cancelling Headphones
   Category: `audio`
2. Levoit Core 300 Air Purifier
   Category: `home-appliance`
3. Threshold Desk Lamp with USB Ports
   Category: `lighting`

Why these products were chosen:

- they belong to 3 distinct categories
- they offer different visual reasoning challenges
- they have enough public text and image evidence for grounded downstream analysis
- they support meaningful comparison across shape-heavy, material-heavy, and component-heavy objects

## Assignment Mapping

### Q1: Product Selection and Data Collection

Implemented with:

- candidate discovery from public marketplace search pages
- one-time product scraping
- durable raw and processed artifacts
- strict Q1 validation

Key outputs:

- [data/discovery](/Users/macbook/Desktop/ai-lab-final/data/discovery)
- [data/raw](/Users/macbook/Desktop/ai-lab-final/data/raw)
- [data/processed](/Users/macbook/Desktop/ai-lab-final/data/processed)
- [docs/q1_summary.md](/Users/macbook/Desktop/ai-lab-final/docs/q1_summary.md)

### Q2: API-Only Text Analysis

Implemented with:

- OpenAI API-only text analysis
- `baseline_description_only`
- `review_informed_rag`
- review-first chunking
- retrieval evidence saving
- structured `VisualProfile` synthesis

Key outputs:

- [outputs/visual_profiles](/Users/macbook/Desktop/ai-lab-final/outputs/visual_profiles)
- [prompts/q2](/Users/macbook/Desktop/ai-lab-final/prompts/q2)

### Q3: Image Generation and Comparison

Implemented with:

- OpenAI Images API
- Stability AI API
- pilot prompt plus pilot image
- refined final prompt plus 4 final images
- comparison panels against real product images
- human scoring template generation
- optional vision-assisted comparison layer

Key outputs:

- [outputs/generated_images](/Users/macbook/Desktop/ai-lab-final/outputs/generated_images)
- [outputs/evaluations](/Users/macbook/Desktop/ai-lab-final/outputs/evaluations)
- [prompts/q3](/Users/macbook/Desktop/ai-lab-final/prompts/q3)

### Q4: Agentic Workflow

Implemented with:

- typed agents
- artifact-aware workflow orchestrator
- reusable by-default artifact reuse
- saved run traces
- workflow page in the frontend

Key outputs:

- [outputs/workflow_runs](/Users/macbook/Desktop/ai-lab-final/outputs/workflow_runs)
- [docs/agentic_workflow.md](/Users/macbook/Desktop/ai-lab-final/docs/agentic_workflow.md)

## Repository Layout

```text
.
├── backend/                  # FastAPI app, Typer CLI, pipeline logic, tests
├── frontend/                 # React + Vite + TypeScript demo app
├── configs/                  # discovery and query configuration
├── data/
│   ├── discovery/            # candidate discovery artifacts
│   ├── raw/                  # one-time scraped product artifacts
│   └── processed/            # cleaned reusable corpora
├── outputs/
│   ├── visual_profiles/      # Q2 outputs
│   ├── generated_images/     # Q3 outputs
│   ├── evaluations/          # comparison and scoring outputs
│   └── workflow_runs/        # Q4 workflow traces
├── prompts/                  # editable prompt templates
├── docs/                     # supporting documentation
├── scripts/                  # convenience run scripts
└── submission_package/       # generated packaging output
```

## Technology Stack

### Backend

- Python 3.11+
- FastAPI
- Typer
- pydantic and pydantic-settings
- httpx
- BeautifulSoup4
- Pillow
- pytest
- ruff
- mypy

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- Framer Motion
- Recharts

### APIs

- OpenAI API
  - text analysis
  - embeddings
  - image generation
  - optional vision-assisted evaluation
- Stability AI API
  - image generation

## Environment Variables

Copy [.env.example](/Users/macbook/Desktop/ai-lab-final/.env.example) to `.env` in the repository root.

Required for full pipeline execution:

```env
OPENAI_API_KEY=your_openai_key
STABILITY_API_KEY=your_stability_key
```

Useful optional settings include:

```env
OPENAI_MODEL=gpt-4.1-mini
OPENAI_IMAGE_MODEL=gpt-image-1
EMBEDDING_MODEL=text-embedding-3-small
STABILITY_IMAGE_MODEL=stable-image-core
FRONTEND_API_BASE_URL=http://127.0.0.1:8000
DISCOVERY_TIMEOUT_SECONDS=20
SCRAPING_MAX_REVIEWS=100
MIN_CLEAN_REVIEW_COUNT=5
```

## Installation

### Backend

```bash
cd /Users/macbook/Desktop/ai-lab-final
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e "backend[dev]"
cp .env.example .env
```

### Frontend

```bash
cd /Users/macbook/Desktop/ai-lab-final/frontend
npm install
```

## Quick Start

### Start the backend

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --app-dir src --port 8000
```

Backend API:

- [http://127.0.0.1:8000](http://127.0.0.1:8000)
- [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### Start the frontend

```bash
cd /Users/macbook/Desktop/ai-lab-final/frontend
npm run dev
```

Frontend:

- [http://localhost:5173](http://localhost:5173)

## Frontend Demo Pages

The frontend is fully artifact-backed and presentation-ready. It includes:

- `/`
  Overview and project summary
- `/products`
  final 3 products, category, popularity, rationale
- `/reviews`
  review stats, sample reviews, retrieval evidence, chunking explanation
- `/profiles`
  baseline vs review-informed visual profiles
- `/generation`
  prompt history, pilot vs final prompts, model switcher, generated images
- `/comparison`
  real vs generated views, score charts, provider comparisons, summaries
- `/workflow`
  typed agents, workflow stages, latest trace, artifact handoffs

## One-Time Discovery and Scraping

The repository is designed around one-time artifact production.

Default behavior:

- reuse existing discovery artifacts
- reuse existing raw scrape artifacts
- reuse downstream processed and generated artifacts whenever possible

Only pass `--refresh` when you explicitly want to rerun a stage.

### Discover candidate products

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml
```

Force refresh:

```bash
PYTHONPATH=src ../.venv/bin/python -m cli.main discover-products --config ../configs/product_queries.yaml --refresh
```

### Scrape the selected products

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-all --input ../data/selected_products.jsonl --max-reviews 100
```

Force refresh:

```bash
PYTHONPATH=src ../.venv/bin/python -m cli.main scrape-all --input ../data/selected_products.jsonl --max-reviews 100 --refresh
```

## End-to-End Pipeline Commands

### Build cleaned corpus and verify Q1

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
PYTHONPATH=src ../.venv/bin/python -m cli.main build-corpus --raw-dir ../data/raw --output-dir ../data/processed --input ../data/selected_products.jsonl
PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage q1 --processed-dir ../data/processed --input ../data/selected_products.jsonl
```

### Extract Q2 visual profiles

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product jbl-tour-one-m2-wireless-over-ear-adaptive-noise-cancelling-headphones-black-89301002 --mode baseline_description_only
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product jbl-tour-one-m2-wireless-over-ear-adaptive-noise-cancelling-headphones-black-89301002 --mode review_informed_rag
```

Repeat for:

- `levoit-core-300-air-purifier-white-81910071`
- `desk-lamp-with-usb-ports-includes-led-light-bulb-threshold-8482-80705997`

### Generate Q3 images

Per product:

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --product levoit-core-300-air-purifier-white-81910071 --model openai --count 4
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --product levoit-core-300-air-purifier-white-81910071 --model stability --count 4
```

All products:

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --all --count 4
```

### Evaluate Q3 outputs

Human-template and summary outputs:

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
PYTHONPATH=src ../.venv/bin/python -m cli.main evaluate-images --all
```

Add optional vision-assisted evaluation:

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
PYTHONPATH=src ../.venv/bin/python -m cli.main evaluate-images --all --vision-assisted
```

### Run the Q4 workflow

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
PYTHONPATH=backend/src python -m cli.main run-workflow --all
```

## Reuse Behavior and Refresh Behavior

The pipeline is intentionally artifact-first.

By default it:

- reads saved discovery outputs
- reads saved scrape outputs
- reads saved processed corpora
- reads saved visual profiles
- reads saved generation outputs
- reads saved evaluation outputs
- reads saved workflow traces where appropriate

This keeps reruns cheap, reproducible, and presentation-friendly.

Use `--refresh` only when:

- you want to re-scrape public pages
- you want to regenerate outputs
- you want to explicitly overwrite stale downstream artifacts

## Current Artifact Snapshot

The current repository snapshot already contains:

- 3 selected products from 3 distinct categories
- cleaned Q1 corpora for all products
- baseline and review-informed visual profiles for all products
- generated images from 2 providers for all products
- evaluation outputs for all products
- workflow trace outputs
- a submission package builder

Important artifact roots:

- [data/selected_products.jsonl](/Users/macbook/Desktop/ai-lab-final/data/selected_products.jsonl)
- [data/processed/manifest.json](/Users/macbook/Desktop/ai-lab-final/data/processed/manifest.json)
- [outputs/visual_profiles](/Users/macbook/Desktop/ai-lab-final/outputs/visual_profiles)
- [outputs/generated_images](/Users/macbook/Desktop/ai-lab-final/outputs/generated_images)
- [outputs/evaluations](/Users/macbook/Desktop/ai-lab-final/outputs/evaluations)
- [outputs/workflow_runs](/Users/macbook/Desktop/ai-lab-final/outputs/workflow_runs)

## Evaluation Notes

The evaluation framework supports two layers:

1. human scoring template generation
2. optional vision-assisted evaluation

This is important for presentation accuracy:

- the human evaluation path is complete for all three products
- the vision-assisted layer is an augmenting layer, not the only evaluation path
- some products may show `partial` vision-assisted completion if rate limits interrupt a run after some comparison panels have already been scored

This is an honest limitation rather than a hidden failure, and the repository preserves both the partial status and any completed scores in the saved artifacts.

## Verification

### Run backend tests

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
pytest
ruff check src tests
mypy src tests
```

### Run frontend build

```bash
cd /Users/macbook/Desktop/ai-lab-final/frontend
npm run build
```

### Full repository verification

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
source ../.venv/bin/activate
PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage full --frontend-dir ../frontend
```

Verification checks:

- Q1 artifact completeness and selection rules
- Q2 profile existence, prompts, retrieval evidence, schema validity
- Q3 dual-model image generation, image integrity, manifests, evaluations
- Q4 workflow agents, traces, docs
- frontend production build

## Convenience Scripts

Run the full pipeline:

```bash
cd /Users/macbook/Desktop/ai-lab-final
./scripts/run_full_pipeline.sh
```

Run the backend plus frontend demo flow:

```bash
cd /Users/macbook/Desktop/ai-lab-final
./scripts/run_frontend_demo.sh
```

## Submission Packaging

Build the final submission package:

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
source ../.venv/bin/activate
PYTHONPATH=src ../.venv/bin/python -m cli.main build-submission-package
```

Outputs:

- [submission_package](/Users/macbook/Desktop/ai-lab-final/submission_package)
- [docs/submission_manifest.md](/Users/macbook/Desktop/ai-lab-final/docs/submission_manifest.md)

## Most Important Supporting Docs

- [docs/master_guide.md](/Users/macbook/Desktop/ai-lab-final/docs/master_guide.md)
- [docs/q1_summary.md](/Users/macbook/Desktop/ai-lab-final/docs/q1_summary.md)
- [docs/agentic_workflow.md](/Users/macbook/Desktop/ai-lab-final/docs/agentic_workflow.md)
- [docs/final_checklist.md](/Users/macbook/Desktop/ai-lab-final/docs/final_checklist.md)
- [docs/submission_manifest.md](/Users/macbook/Desktop/ai-lab-final/docs/submission_manifest.md)

## Known Limitations

- public marketplace pages can change over time, so scraping adapters are intentionally conservative
- optional vision-assisted evaluation is sensitive to API rate limits and may occasionally produce partial completion for a product while still preserving valid scored panels
- the repository favors saved artifacts and reproducibility over aggressively re-fetching external sources

## Final Summary

This repository now provides a complete, inspectable, reproducible, and presentation-ready implementation of the CMU project:

- grounded public data collection
- structured review-informed visual understanding
- dual-model API-only image generation
- real-vs-generated comparison
- typed multi-agent orchestration
- full-stack artifact-backed visualization
