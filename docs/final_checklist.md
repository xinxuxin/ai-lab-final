# Final Checklist

## Repository Verification

- Run `PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage q1`
- Run `PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage q2`
- Run `PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage q3`
- Run `PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage q4`
- Run `PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage full --frontend-dir ../frontend`

## Required Artifacts

- `data/selected_products.jsonl` contains exactly three selected products
- `data/processed/manifest.json` exists and passes Q1 checks
- `outputs/visual_profiles/<product_slug>/` contains both Q2 modes
- `outputs/generated_images/<product_slug>/openai/` exists
- `outputs/generated_images/<product_slug>/stability/` exists
- `outputs/evaluations/<product_slug>/summary.json` exists
- `outputs/workflow_runs/<run_id>/trace.json` exists

## Demo Readiness

- Backend starts with `uvicorn app.main:app --reload --app-dir src --port 8000`
- Frontend starts with `npm run dev`
- Workflow page shows the latest saved run trace
- Comparison page shows real-vs-generated panels
- Profile page shows baseline and review-informed tabs

## Submission Packaging

- Run `PYTHONPATH=src ../.venv/bin/python -m cli.main build-submission-package`
- Confirm `submission_package/submission_manifest.json` exists
- Confirm package includes `backend`, `frontend`, `data`, `outputs`, `docs`, and `prompts`
