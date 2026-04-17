# CarReco Backend

Minimal FastAPI backend for the AI-assisted car recommendation MVP.

## Current Modules

- Recommendation API Layer: receives requests and returns recommendation responses.
- Input Validation Module: performs business-level validation, detects missing critical fields, and prepares follow-up signals.
- Preference Normalization Module: converts validated request data into a normalized internal preference model, hard constraints, soft preferences, and ambiguity flags.
- Follow-Up Question Module: decides when clarification is needed and returns targeted follow-up prompts with reason codes.
- Car Catalog Module: serves the seeded car dataset, queryable catalog records, and coverage/completeness indicators for downstream modules.
- Candidate Filtering Module: applies hard constraints to catalog records, returns a candidate set, rejection reasons, and filtering summary.
- Scoring and Ranking Module: scores filtered candidates with weighted MVP factors, produces ranked results, score breakdowns, and weak-match flags.
- Constraint Relaxation Module: loosens constraints in a controlled order when matches are too few or weak, and records what was relaxed.
- Explanation Generation Module: turns ranked candidates into user-facing reasons, tradeoffs, and alternative suggestion notes.
- Response Formatter Module: assembles the final API response shape for both follow-up and recommendation scenarios.

## Run

```bash
python -m uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `POST /recommendations`
