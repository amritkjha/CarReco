# Backend Module Breakdown

This document breaks the MVP into backend modules based on the product spec in [`docs/spec.md`](/Volumes/Saarthi.ai(CUX)/Projects/CarReco/docs/spec.md).

## 1. Recommendation API Layer

### Responsibility

- Expose the main backend endpoints for submitting recommendation requests and returning recommendation responses.
- Validate request shape at the transport layer.
- Coordinate the end-to-end recommendation flow.

### Inputs

- HTTP or RPC request containing user preferences
- Request metadata such as session ID, request ID, and timestamp

### Outputs

- Recommendation response with ranked cars, explanations, alternatives, and system notes
- Validation or error response for malformed requests

### Dependencies

- Input Validation Module
- Preference Normalization Module
- Recommendation Orchestrator
- Response Formatter Module
- Logging and Monitoring Module

## 2. Input Validation Module

### Responsibility

- Validate required fields and acceptable value ranges
- Detect missing critical inputs such as budget or use case
- Enforce schema constraints before downstream processing

### Inputs

- Raw user preference payload from the API layer

### Outputs

- Validated preference payload
- Validation errors
- Missing-field flags for follow-up generation

### Dependencies

- Shared request schema definitions
- Domain enums for fuel type, body type, transmission, and priority fields

## 3. Preference Normalization Module

### Responsibility

- Convert raw user input into a structured internal preference model
- Standardize natural language into canonical values
- Separate hard constraints from soft preferences

### Inputs

- Validated user input
- Optional free-text preference fields

### Outputs

- Normalized preference object
- Hard constraints
- Soft preferences and weights
- Confidence flags for ambiguous inputs

### Dependencies

- Input Validation Module
- Domain mapping rules
- Optional LLM or NLP helper for free-text interpretation

## 4. Follow-Up Question Module

### Responsibility

- Decide when the system should ask a clarifying question instead of generating recommendations
- Generate a small number of targeted follow-up prompts for missing or conflicting inputs

### Inputs

- Validation results
- Normalized preferences
- Ambiguity and conflict flags

### Outputs

- Follow-up question payload
- Reason code such as `missing_budget`, `missing_use_case`, or `conflicting_preferences`

### Dependencies

- Input Validation Module
- Preference Normalization Module
- Rules engine for missing and conflicting input handling

## 5. Car Catalog Module

### Responsibility

- Provide access to the structured car dataset used by the MVP
- Serve car records and derived attributes needed for filtering and ranking

### Inputs

- Query parameters from filtering and ranking modules

### Outputs

- Car inventory records
- Model specifications and metadata
- Dataset coverage or completeness indicators

### Dependencies

- Car database or catalog store
- Data access layer or repository layer

## 6. Candidate Filtering Module

### Responsibility

- Apply hard constraints to eliminate clearly unsuitable cars
- Produce a candidate set for ranking

### Inputs

- Normalized hard constraints
- Car catalog records

### Outputs

- Candidate car list
- Filter rejection reasons
- Candidate count summary

### Dependencies

- Preference Normalization Module
- Car Catalog Module

## 7. Scoring and Ranking Module

### Responsibility

- Score each candidate car against the user's priorities
- Rank cars using simple weighted logic aligned with the MVP spec

### Inputs

- Candidate car list
- Soft preferences and weights
- Ranking factors such as budget fit, use case fit, efficiency, safety, and feature match

### Outputs

- Ranked recommendation list
- Per-car score breakdown
- Low-confidence or weak-match flags

### Dependencies

- Candidate Filtering Module
- Preference Normalization Module
- Scoring rules configuration

## 8. Constraint Relaxation Module

### Responsibility

- Handle no-match or very small candidate scenarios
- Relax soft constraints in a controlled order and retry recommendation generation

### Inputs

- Original normalized preferences
- Candidate count summary
- Ranked result quality signals

### Outputs

- Relaxed preference set
- Relaxation notes explaining what was loosened
- Expanded candidate list when available

### Dependencies

- Candidate Filtering Module
- Scoring and Ranking Module
- Rules for relaxable vs non-relaxable constraints

## 9. Explanation Generation Module

### Responsibility

- Generate concise reasons for why each car was recommended
- Identify one key tradeoff or limitation per recommendation
- Support explainable output instead of raw scores only

### Inputs

- Ranked cars
- Score breakdowns
- Car attributes
- Relaxation notes when applicable

### Outputs

- Recommendation reasons
- Tradeoff statements
- Alternative suggestion notes

### Dependencies

- Scoring and Ranking Module
- Car Catalog Module
- Optional LLM or template-based explanation generator

## 10. Response Formatter Module

### Responsibility

- Assemble the final response payload expected by the frontend or client
- Keep output shape consistent across normal, edge-case, and follow-up responses

### Inputs

- Ranked recommendations
- Explanations
- Alternatives
- Follow-up question payloads
- Limitation and confidence notes

### Outputs

- Final API response object

### Dependencies

- Explanation Generation Module
- Follow-Up Question Module
- Recommendation Orchestrator

## 11. Recommendation Orchestrator

### Responsibility

- Drive the end-to-end recommendation workflow
- Route requests through validation, normalization, filtering, ranking, explanation, and formatting
- Handle branching logic for edge cases

### Inputs

- Recommendation request from the API layer

### Outputs

- Final recommendation response
- Final follow-up response
- Workflow status and reason codes

### Dependencies

- Input Validation Module
- Preference Normalization Module
- Follow-Up Question Module
- Candidate Filtering Module
- Scoring and Ranking Module
- Constraint Relaxation Module
- Explanation Generation Module
- Response Formatter Module

## 12. Logging and Monitoring Module

### Responsibility

- Capture request traces, validation failures, low-result scenarios, and scoring outcomes
- Support debugging, quality checks, and future tuning of recommendation logic

### Inputs

- Request metadata
- Module-level status events
- Error events
- Recommendation summary metrics

### Outputs

- Structured logs
- Metrics and alerts

### Dependencies

- API Layer
- Recommendation Orchestrator
- External logging and monitoring stack

## Suggested Processing Sequence

1. Recommendation API Layer receives the request.
2. Input Validation Module checks schema and required fields.
3. Preference Normalization Module converts input into structured preferences.
4. Follow-Up Question Module interrupts the flow if critical inputs are missing or conflicting.
5. Car Catalog Module provides the searchable inventory.
6. Candidate Filtering Module applies hard constraints.
7. Scoring and Ranking Module ranks the remaining cars.
8. Constraint Relaxation Module retries when results are too weak or empty.
9. Explanation Generation Module creates reasons and tradeoffs.
10. Response Formatter Module returns the final response.
11. Logging and Monitoring Module records the flow throughout.
