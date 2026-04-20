# Master Guide

## Project Title

**Generating Product Image from Customer Reviews**

This repository is a full-stack, artifact-first CMU final project that studies whether public product descriptions and customer reviews can be transformed into image-generation-ready structured visual profiles, then used to generate product images and compare them against real posted product photos.

This guide is the master reference for:

- project motivation
- assignment mapping
- data collection and cleaning
- experiment design
- Q1 through Q4 implementation details
- model and prompt choices
- evaluation results
- workflow design
- frontend demo structure
- reproducibility and verification
- presentation preparation

## 1. Executive Summary

The project takes three publicly visible marketplace products from different categories, collects their product descriptions, reviews, and reference images, and converts those artifacts into a structured visual understanding pipeline.

The core research question is:

> Can grounded textual evidence from product listings and customer reviews improve the quality of generated product imagery compared with using product descriptions alone?

To answer that, the repository implements:

- `Q1`: one-time product discovery, selection, scraping, cleaning, and strict validation
- `Q2`: API-only LLM analysis using two modes:
  - `baseline_description_only`
  - `review_informed_rag`
- `Q3`: dual-model image generation with:
  - OpenAI Images API
  - Stability AI API
- `Q3/Q4`: real-vs-generated evaluation, comparison analytics, and a typed multi-agent workflow
- a full-stack frontend that reads real artifact-backed state from disk through FastAPI

The current repository snapshot now includes:

- all 3 selected products
- cleaned corpora and strict Q1 validation
- Q2 visual profiles for all products
- Q3 generated images from both OpenAI and Stability for all products
- comparison panels and evaluation outputs for all products
- a saved Q4 workflow trace
- final verification and submission packaging tooling

## 2. Assignment Mapping

## Q1: Product Selection and Data Collection

Required by assignment:

- exactly 3 products
- different categories
- category and popularity considerations
- rationale for selection
- descriptions and reviews collected

Implemented in repository:

- automated candidate discovery from public marketplace search pages
- durable one-time scraping of selected product pages
- cleaned and processed corpora under `data/processed/`
- strict Q1 validation through `verify-artifacts --stage q1`

## Q2: API-only Text Analysis

Required by assignment:

- LLM API only
- prompt engineering and or RAG
- chunking consideration
- output suitable for downstream diffusion or image generation

Implemented in repository:

- OpenAI API-only text analysis
- baseline vs review-informed modes
- one-review-first chunking strategy
- local embedding retriever with fallback behavior
- retrieval evidence saving
- final structured `VisualProfile` objects

## Q3: Image Generation and Comparison

Required by assignment:

- at least 2 image generation models via API only
- 3 to 5 images per product
- prompt iteration
- compare generated images to real posted product images
- explain model differences and successes or failures

Implemented in repository:

- OpenAI Images API
- Stability AI API
- pilot prompt + pilot image + refined final prompt + 4 final images
- comparison panels against real product images
- human scoring sheet generation
- optional and partial vision-assisted evaluation

## Q4: Agentic Workflow

Required by assignment:

- build an AI agentic workflow connecting all stages

Implemented in repository:

- typed agents
- workflow orchestrator
- reusable artifact-aware orchestration
- trace writing
- workflow visualization in frontend

## 3. Repository Structure

High-level important folders:

- `backend/`
  - FastAPI API
  - Typer CLI
  - collection, Q2, Q3, evaluation, verification, and workflow logic
- `frontend/`
  - React + Vite + TypeScript + Tailwind + Framer Motion demo app
- `data/`
  - durable Q1 artifacts
- `outputs/`
  - Q2, Q3, evaluation, and workflow artifacts
- `prompts/`
  - editable prompt templates
- `docs/`
  - summary docs, workflow docs, checklist docs, this master guide
- `scripts/`
  - convenience scripts for full pipeline and frontend demo

Most important artifact roots:

- `data/discovery/`
- `data/raw/`
- `data/processed/`
- `outputs/visual_profiles/`
- `outputs/generated_images/`
- `outputs/evaluations/`
- `outputs/workflow_runs/`

## 4. Technology Stack

## Backend

- Python 3.11+
- FastAPI
- Typer
- Pydantic / pydantic-settings
- httpx
- BeautifulSoup4
- Pillow
- pytest
- ruff
- mypy

## Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- Framer Motion
- Recharts

## APIs

- OpenAI API
  - text analysis
  - embeddings
  - image generation
  - optional vision-assisted evaluation
- Stability AI API
  - image generation

## 5. Product Selection and Q1 Design

## Final Selected Products

The final three selected products are:

1. **JBL Tour One M2 Wireless Over-Ear Adaptive Noise Cancelling Headphones (Black)**
   - Category: `audio`
   - Popularity hint: `medium`
   - Rationale: distinct audio category, visible form factor, multiple real product images, sufficient public review coverage

2. **Levoit Core 300 Air Purifier White**
   - Category: `home-appliance`
   - Popularity hint: `high`
   - Rationale: clean industrial design, strong review coverage, good candidate for text-to-visual grounding

3. **Desk Lamp with USB Ports (Includes LED Light Bulb) - Threshold™**
   - Category: `lighting`
   - Popularity hint: `high`
   - Rationale: visible structure and component details, enough reviews for visual extraction, clear real-vs-generated comparison opportunities

## Why These Products Were Good Experimental Choices

- They belong to clearly different categories.
- They have different visual challenges:
  - headphones: curved wearable shape and material cues
  - air purifier: minimal industrial appliance geometry
  - desk lamp: multiple physical components and proportion-sensitive structure
- They have enough public text and image evidence for downstream analysis.
- They give a useful range of complexity:
  - some products are visually constrained and consistent
  - others create more ambiguity for generation and evaluation

## Q1 Validation Results

From real artifacts:

- selected products: `3`
- distinct categories: `3`
- minimum cleaned review threshold: `5`

Per product:

| Product | Cleaned Reviews | Valid Real Images | Description Characters |
|---|---:|---:|---:|
| JBL headphones | 8 | 10 | 3453 |
| Levoit air purifier | 8 | 14 | 475 |
| Desk lamp | 7 | 4 | 604 |

Q1 status: **PASS**

## Q1 Artifact Design

Discovery artifacts:

- `data/discovery/candidate_queries.json`
- `data/discovery/candidates.jsonl`
- `data/discovery/discovery_manifest.json`
- `data/discovery/raw_html/`

Raw scrape artifacts:

- `data/raw/<product_slug>/product_meta.json`
- `data/raw/<product_slug>/description.json`
- `data/raw/<product_slug>/reviews.jsonl`
- `data/raw/<product_slug>/images/`
- `data/raw/<product_slug>/raw_html/`
- `data/raw/<product_slug>/scrape_report.json`
- `data/raw/raw_manifest.json`

Processed artifacts:

- `data/processed/<product_slug>/product.json`
- `data/processed/<product_slug>/description_clean.txt`
- `data/processed/<product_slug>/reviews_clean.jsonl`
- `data/processed/<product_slug>/review_stats.json`
- `data/processed/<product_slug>/image_manifest.json`
- `data/processed/manifest.json`

## 6. Q2 Design: Text Analysis, Retrieval, and Visual Profiles

## Core Question

How should product text be transformed into a representation suitable for image generation?

The repository uses two modes:

1. `baseline_description_only`
   - uses the cleaned product description only
   - acts as a baseline for prompt quality

2. `review_informed_rag`
   - uses cleaned reviews plus retrieval
   - aims to surface expectation-vs-reality and more grounded visible details

## Chunking Strategy

Chunking design:

- one review is the default chunk unit
- only overly long reviews are split
- this keeps retrieval evidence interpretable
- each chunk can still be traced back to its source review

Why this matters:

- product reviews are naturally self-contained units
- smaller evidence units reduce hallucinated synthesis
- it becomes easier to show evidence snippets in the frontend and report

## Retrieval Design

The retrieval layer is pluggable.

Default behavior:

- local embedding-based retriever
- cached and reusable
- API-only embeddings via OpenAI

Fallback behavior:

- keyword-overlap retrieval if embeddings are unavailable

Aspect-specific retrieval queries:

- appearance and shape
- color and finish
- material and texture
- size and scale
- expectation-versus-reality mismatches

## Prompt Chain

The Q2 pipeline uses a staged prompt chain instead of one giant prompt:

1. aspect evidence extraction
2. conflict resolution
3. final visual profile synthesis

This improves:

- inspectability
- evidence grounding
- error localization
- reproducibility

## VisualProfile Output Schema

Each final Q2 output includes:

- `product_name`
- `category`
- `high_confidence_visual_attributes`
- `low_confidence_or_conflicting_attributes`
- `common_mismatches_between_expectation_and_reality`
- `prompt_ready_description`
- `negative_constraints`

## Real Q2 Output Summary

Review-informed profile counts:

| Product | High-Confidence Attributes | Low-Confidence Attributes | Mismatches | Negative Constraints |
|---|---:|---:|---:|---:|
| Desk lamp | 7 | 1 | 0 | 0 |
| JBL headphones | 4 | 2 | 0 | 0 |
| Levoit air purifier | 2 | 2 | 0 | 2 |

Interpretation:

- desk lamp produced the richest explicit visual structure
- JBL produced a moderate but stable set of attributes
- Levoit produced fewer strong attributes, reflecting a more minimal visual form

## Q2 Artifacts

For each product:

- `outputs/visual_profiles/<product_slug>/baseline_description_only.json`
- `outputs/visual_profiles/<product_slug>/review_informed_rag.json`
- `outputs/visual_profiles/<product_slug>/retrieval_evidence.json`
- `outputs/visual_profiles/<product_slug>/llm_trace.json`

## 7. Q3 Design: Prompting and Image Generation

## Generation Providers

The project uses two image-generation providers:

- `OpenAI Images API`
- `Stability AI API`

This satisfies the assignment requirement to use at least two API-only image-generation models.

## Prompt Flow

For each product and each provider:

1. generate one pilot prompt
2. generate one pilot image
3. refine to a final prompt
4. generate four final images

This creates:

- 1 pilot image per provider per product
- 4 final images per provider per product

So each product gets:

- OpenAI: 5 total images
- Stability: 5 total images

Across all products:

- 3 products × 2 providers × 5 images = **30 generated images**

## Prompt Constraints

Prompt construction enforces:

- single product only
- centered composition
- neutral or studio background
- realistic product photography
- no unsupported accessories
- negative constraints where supported

## Real Q3 Generation Results

Per provider and product:

| Product | Provider | Pilot Images | Final Images | Status |
|---|---|---:|---:|---|
| Desk lamp | OpenAI | 1 | 4 | completed |
| Desk lamp | Stability | 1 | 4 | completed |
| JBL headphones | OpenAI | 1 | 4 | completed |
| JBL headphones | Stability | 1 | 4 | completed |
| Levoit air purifier | OpenAI | 1 | 4 | completed |
| Levoit air purifier | Stability | 1 | 4 | completed |

## Q3 Artifacts

For each product and provider:

- `outputs/generated_images/<product_slug>/<provider>/prompt_versions.json`
- `outputs/generated_images/<product_slug>/<provider>/pilot/prompt.json`
- `outputs/generated_images/<product_slug>/<provider>/pilot/image_01.png`
- `outputs/generated_images/<product_slug>/<provider>/final/prompt.json`
- `outputs/generated_images/<product_slug>/<provider>/final/image_01.png` to `image_04.png`
- `outputs/generated_images/<product_slug>/<provider>/generation_manifest.json`

## 8. Q3 Evaluation Design

## Evaluation Rubric Dimensions

The evaluation rubric uses six dimensions:

- color accuracy
- material / finish accuracy
- shape / silhouette accuracy
- component completeness
- size / proportion impression
- overall recognizability

## Two Evaluation Modes

1. **Human scoring template**
   - `human_score_sheet.csv`
   - manually fillable
   - presentation and report friendly

2. **Vision-assisted evaluation**
   - optional
   - API-based
   - generates provider-level averages and panel-level worked/failed descriptions

## Comparison Panel Design

Each product gets comparison panels that combine:

- real product image
- generated OpenAI image
- generated Stability image

The repository stores durable metadata rather than only transient UI state.

## Real Evaluation Results

## Product 1: JBL Headphones

Status:

- `vision_assisted_status`: `completed`
- comparison panels: `8`
- providers compared: `openai`, `stability`

Aggregate scores:

| Dimension | OpenAI | Stability |
|---|---:|---:|
| color accuracy | 4.50 | 4.25 |
| material finish accuracy | 4.00 | 3.75 |
| shape silhouette accuracy | 3.50 | 4.00 |
| component completeness | 3.00 | 3.25 |
| size proportion impression | 4.00 | 4.00 |
| overall recognizability | 3.75 | 4.00 |

Interpretation:

- both providers performed well on JBL
- OpenAI was slightly stronger on color and finish
- Stability was slightly stronger on silhouette and recognizability
- this is the strongest-performing product overall

## Product 2: Levoit Air Purifier

Status:

- `vision_assisted_status`: `partial`
- comparison panels: `8`
- providers compared: `openai`, `stability`

Aggregate scores from partial successful panels:

| Dimension | OpenAI | Stability |
|---|---:|---:|
| color accuracy | 4.00 | 4.00 |
| material finish accuracy | 3.75 | 3.00 |
| shape silhouette accuracy | 3.75 | 2.00 |
| component completeness | 3.25 | 3.00 |
| size proportion impression | 4.00 | 2.00 |
| overall recognizability | 3.50 | 3.00 |

Interpretation:

- OpenAI appears stronger for shape and proportion on this minimal product
- Stability is more variable here, especially for silhouette and scale
- partial scoring still provides useful directional evidence

## Product 3: Desk Lamp

Status:

- `vision_assisted_status`: `completed`
- comparison panels: `8`
- providers compared: `openai`, `stability`

Aggregate scores:

| Dimension | OpenAI | Stability |
|---|---:|---:|
| color accuracy | 2.75 | 2.00 |
| material finish accuracy | 2.50 | 1.75 |
| shape silhouette accuracy | 2.25 | 1.50 |
| component completeness | 3.00 | 1.00 |
| size proportion impression | 2.75 | 1.75 |
| overall recognizability | 2.50 | 1.50 |

Interpretation:

- the desk lamp is the hardest product
- multiple parts and fine structural details make grounded generation harder
- OpenAI outperformed Stability across all dimensions
- both providers struggled more here than on headphones or the air purifier

## Cross-Product Provider Averages

Using the currently saved evaluation artifacts:

### OpenAI average across products

- color accuracy: `3.75`
- material finish accuracy: `3.42`
- shape silhouette accuracy: `3.17`
- component completeness: `3.08`
- size proportion impression: `3.58`
- overall recognizability: `3.25`

### Stability average across products

- color accuracy: `3.42`
- material finish accuracy: `2.83`
- shape silhouette accuracy: `2.50`
- component completeness: `2.42`
- size proportion impression: `2.58`
- overall recognizability: `2.83`

## High-Level Result Pattern

Across the current saved artifacts:

- OpenAI is generally stronger overall
- Stability can match or slightly exceed OpenAI for certain silhouette-heavy cases
- headphones are easiest
- desk lamp is hardest
- minimal appliance geometry is in the middle

## 9. Q4 Agentic Workflow

## Why the Workflow Is Agentic

This is not a single prompt chain hidden behind one function call.

It is agentic because:

- responsibilities are decomposed into specialized agents
- each agent has typed inputs and outputs
- each stage can reuse durable outputs
- handoffs are saved to disk
- the frontend can inspect the run trace

## Agents

- `DataCurationAgent`
- `RetrievalAgent`
- `VisualUnderstandingAgent`
- `PromptComposerAgent`
- `ImageGenerationAgent`
- `EvaluationAgent`

## Orchestrator Behavior

The orchestrator can:

- run one product
- run all products
- reuse existing artifacts by default
- recompute only missing downstream stages unless refresh is requested

## Real Workflow Run

Latest saved run:

- run id: `20260420T160007Z-a7fac78d`
- scope: `all`
- status: `completed`

Saved workflow artifacts:

- `outputs/workflow_runs/20260420T160007Z-a7fac78d/trace.json`
- `outputs/workflow_runs/20260420T160007Z-a7fac78d/stage_status.json`
- `outputs/workflow_runs/20260420T160007Z-a7fac78d/artifact_links.json`

All six stages completed for all three products.

## 10. Frontend Design and Demo Flow

The frontend is designed for a final presentation and reads real artifact-backed state through the backend API.

Routes:

- `/`
- `/products`
- `/reviews`
- `/profiles`
- `/generation`
- `/comparison`
- `/workflow`

## Recommended Demo Order

1. **Home**
   - show project scope
   - show Q1 to Q4 pipeline
   - show rubric focus

2. **Products**
   - explain the 3 selected products
   - point out category diversity and review/image counts

3. **Reviews**
   - show review volume
   - explain cleaning, chunking, and retrieval evidence

4. **Profiles**
   - compare baseline vs review-informed visual profiles
   - show evidence-backed attributes and conflicts

5. **Generation**
   - show pilot vs final prompts
   - show OpenAI vs Stability output grids

6. **Comparison**
   - show real vs generated images
   - discuss rubric dimensions
   - explain provider differences and product difficulty

7. **Workflow**
   - close with the typed agentic workflow
   - show trace and artifact handoffs

## 11. Verification and Reproducibility

The repository includes strict verification and packaging tools.

## Full Verification

Command:

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
source ../.venv/bin/activate
PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage full --frontend-dir ../frontend
```

Latest real result:

- `Q1`: PASS
- `Q2`: PASS
- `Q3`: PASS
- `Q4`: PASS
- `frontend`: PASS

## Submission Package

Command:

```bash
cd /Users/macbook/Desktop/ai-lab-final/backend
source ../.venv/bin/activate
PYTHONPATH=src ../.venv/bin/python -m cli.main build-submission-package
```

Output:

- `submission_package/`
- `submission_package/submission_manifest.json`

## Convenience Scripts

Full pipeline:

```bash
cd /Users/macbook/Desktop/ai-lab-final
./scripts/run_full_pipeline.sh
```

Frontend demo:

```bash
cd /Users/macbook/Desktop/ai-lab-final
./scripts/run_frontend_demo.sh
```

## 12. Strengths of This Project

- artifact-first design instead of hidden transient state
- one-time scraping and reuse-by-default behavior
- explicit Q1 validation
- dual-mode Q2 analysis
- dual-provider image generation
- real comparison against reference product images
- typed agentic orchestration
- presentation-ready full-stack UI
- repository-level verification and packaging

## 13. Current Limitations

- some vision-assisted runs are still sensitive to OpenAI rate limiting
- Levoit currently uses partial vision-assisted aggregation rather than a fully completed set of all panels
- scraped review availability is limited by what the public Target product payload exposes
- frontend bundle size is still larger than ideal, though production build passes

These limitations are documented rather than hidden, which is important for scientific rigor.

## 14. Key Scientific Takeaways

1. Review-informed analysis is useful because reviews reveal expectation-versus-reality and visible details that descriptions alone may omit.
2. Product category strongly affects difficulty:
   - simple but shape-sensitive appliances are moderately difficult
   - highly structured multi-part objects like lamps are much harder
   - headphones produced the strongest results in this snapshot
3. OpenAI and Stability do not fail in the same way:
   - OpenAI is generally stronger overall
   - Stability can remain competitive on some silhouette-heavy cases
4. The best experimental framing is not “did the model make a pretty image,” but “did it preserve the right visible product cues under a controlled rubric.”

## 15. Suggested Presentation Outline

## Slide 1: Title and Problem

- project title
- core question
- why customer reviews matter

## Slide 2: Assignment Framing

- map project to Q1 through Q4

## Slide 3: Data and Product Selection

- three products
- rationale
- categories and popularity

## Slide 4: Q1 Pipeline

- discovery
- scraping
- cleaning
- validation

## Slide 5: Q2 Method

- baseline description only
- review-informed RAG
- chunking
- retrieval
- visual profile schema

## Slide 6: Q2 Example Artifact

- show one real `review_informed_rag.json`
- show evidence snippets

## Slide 7: Q3 Generation Design

- OpenAI vs Stability
- pilot and final prompts
- image count design

## Slide 8: Q3 Example Results

- one product
- real image vs generated image panels

## Slide 9: Evaluation Rubric

- six dimensions
- explain human sheet and vision-assisted mode

## Slide 10: Results Table

- headphones
- air purifier
- desk lamp

## Slide 11: Cross-Provider Insights

- OpenAI average vs Stability average
- explain where each model is stronger or weaker

## Slide 12: Q4 Agentic Workflow

- show workflow page
- explain typed agents and trace artifacts

## Slide 13: Reproducibility

- full verification pass
- submission package

## Slide 14: Limitations and Future Work

- rate limits
- more products
- fuller human evaluation
- stronger managed vector DB experiments

## 16. Most Important Files for Presentation

Use these during prep:

- [README.md](/Users/macbook/Desktop/ai-lab-final/README.md)
- [docs/q1_summary.md](/Users/macbook/Desktop/ai-lab-final/docs/q1_summary.md)
- [docs/agentic_workflow.md](/Users/macbook/Desktop/ai-lab-final/docs/agentic_workflow.md)
- [docs/final_checklist.md](/Users/macbook/Desktop/ai-lab-final/docs/final_checklist.md)
- [outputs/evaluations](/Users/macbook/Desktop/ai-lab-final/outputs/evaluations)
- [outputs/workflow_runs/20260420T160007Z-a7fac78d/trace.json](/Users/macbook/Desktop/ai-lab-final/outputs/workflow_runs/20260420T160007Z-a7fac78d/trace.json)

## 17. Final One-Sentence Conclusion

This project demonstrates that an artifact-grounded, review-informed, multi-stage pipeline can generate and evaluate product images more rigorously than a single prompt workflow, while remaining reproducible, inspectable, and presentation-ready.
