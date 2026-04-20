# Submission Manifest

The submission package should contain the following repository sections:

- `README.md`
- `backend/`
- `frontend/`
- `configs/`
- `data/`
- `outputs/`
- `prompts/`
- `docs/`
- `scripts/`
- `.env.example`
- `Makefile`

## Why These Are Included

- `backend/`: reproducible CLI, API, and verification logic
- `frontend/`: presentation-ready demo UI that reads artifact-backed state
- `data/`: durable Q1 scrape and processed corpus artifacts
- `outputs/`: Q2, Q3, and Q4 artifacts including profiles, generations, evaluations, and workflow traces
- `prompts/`: editable prompt templates for Q2, Q3, and evaluation
- `docs/`: report support, rationale templates, workflow explanation, and final checklist
- `scripts/`: one-command reproducibility helpers for pipeline and demo setup

## Build Command

```bash
cd /Users/macbook/Desktop/ai-lab-final
source .venv/bin/activate
cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main build-submission-package
```
