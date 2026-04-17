# Generating Product Image from Customer Reviews

Production-quality full-stack repository for a CMU final project that studies how public product descriptions and customer reviews can be converted into image-generation-ready prompts, then compared against real posted product images.

## Assignment Alignment

This repository is structured to support all four required questions:

- `Q1`: discover candidate products, justify selection of exactly three products across different categories and popularity levels, and collect descriptions plus public customer reviews.
- `Q2`: analyze text artifacts with API-only LLM workflows, prompt engineering, chunking, and retrieval support to produce visual profiles for downstream image generation.
- `Q3`: generate 3 to 5 images per product with at least two API-only image models, iterate prompts, and compare outputs against reference product imagery.
- `Q4`: orchestrate the whole pipeline with an agentic workflow that preserves traces, artifacts, and rerun controls.

## Stage 1 Progress

Initial full-stack skeleton is complete in this stage.

- Backend FastAPI app, Typer CLI, pydantic settings, schema layer, workflow placeholders, and smoke tests are in place.
- Frontend Vite + React + TypeScript + Tailwind + Framer Motion dashboard shell is in place with the required demo routes.
- Shared `artifacts/`, `docs/`, `prompts/`, and `reports/` folders are created for durable project outputs.
- Repository-level install, run, lint, and test commands are documented and available through `Makefile`.

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
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.cjs
│   ├── src/
│   │   ├── components/
│   │   ├── data/
│   │   ├── layouts/
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
python -m cli.main discover-products
python -m cli.main run-workflow
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

- Product discovery, scraping, retrieval, prompt execution, image generation, and evaluation are scaffolded but not yet implemented.
- Frontend currently uses presentation-friendly mock data only and does not call backend APIs yet.
- Artifact manifests, workflow traces, and report exports are placeholders awaiting real stage outputs.

## Next Recommended Stage

Implement `Q1` end-to-end:

- automated candidate discovery for public product links
- manual/traceable final selection of exactly three products
- durable scrape artifacts for descriptions and public reviews
- crawl logs, manifests, and reproducibility notes

