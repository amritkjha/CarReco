# AI-Assisted Car Recommendation System MVP Spec

## 1. Problem Definition

Users looking for a car often struggle to compare many options across price, usage, body type, fuel type, safety, and ownership cost. The MVP should help a user quickly narrow down suitable cars by collecting a small set of preferences and returning a short, explainable recommendation list.

### Goal

Recommend the most relevant cars for a user's needs with simple reasoning, not a full buying advisor.

### MVP Scope

- Collect core user preferences through a guided form or chat.
- Match user needs against a structured car inventory or dataset.
- Return a ranked shortlist with brief explanations.
- Ask follow-up questions only when critical information is missing.

### Out of Scope

- Real-time dealer inventory.
- Financing, insurance, or loan approval.
- Test drive booking.
- Highly personalized long-term learning.
- Region-wide market intelligence beyond the available dataset.

## 2. User Inputs

The system should accept the following inputs:

### Required Inputs

- Budget range
- Primary use case
  - City commute
  - Family use
  - Highway travel
  - Off-road or mixed use
- Preferred body type
  - Hatchback
  - Sedan
  - SUV
  - MUV
  - Pickup
  - No preference
- Seating requirement
- Fuel preference
  - Petrol
  - Diesel
  - Hybrid
  - EV
  - No preference

### Optional Inputs

- Transmission preference
- Brand preferences or exclusions
- New or used car preference
- Safety priority
- Mileage or efficiency priority
- Boot space priority
- Performance priority
- Annual driving distance
- City or region
- Must-have features
  - ADAS
  - Sunroof
  - Rear camera
  - Connected features
  - Automatic climate control

## 3. Expected Outputs

The system should return:

### Primary Output

- Top 3 to 5 recommended cars

### For Each Recommendation

- Car make and model
- Approximate price range
- Match score or ranking position
- 2 to 4 reasons it matches the user
- Key tradeoff or limitation
- Summary specs
  - Body type
  - Fuel type
  - Transmission
  - Seating
  - Mileage or range
  - Safety rating if available

### Secondary Output

- 1 to 3 near-match alternatives
- A short note if recommendations are limited due to strict filters or missing data
- Suggested next question when user inputs are too broad or conflicting

## 4. Core Flow

### Step 1: Collect Preferences

Capture required inputs first. Ask follow-up questions only if budget, use case, or another high-impact input is missing.

### Step 2: Normalize Inputs

Convert user input into structured filters and priorities.

Examples:

- "Good mileage" -> efficiency priority
- "Mostly city driving" -> city commute use case
- "Family of 6" -> minimum 6 seats

### Step 3: Filter Candidate Cars

Remove cars that do not meet hard constraints such as:

- Budget ceiling
- Seating requirement
- Fuel preference, if strict
- Body type, if strict

### Step 4: Rank Remaining Cars

Score candidates using a simple weighted model based on:

- Budget fit
- Use case fit
- Feature match
- Safety fit
- Efficiency fit
- Brand preference fit

### Step 5: Generate Explainable Recommendations

Return the top recommendations with concise reasons and one tradeoff per car.

### Step 6: Handle Gaps

If no strong matches exist, relax only soft preferences and tell the user what was relaxed.

## 5. Edge Cases

### Missing Critical Inputs

- If budget or use case is missing, ask a follow-up question before recommending.

### Overly Broad Inputs

- If the user says "any car" or gives very loose preferences, return popular balanced options and ask one clarifying question.

### Conflicting Inputs

- Example: very low budget plus premium brand plus EV.
- Return the closest matches and clearly call out the conflict.

### No Exact Match

- Return near matches and explain which constraint prevented an exact fit.

### Unsupported or Unknown Cars

- If the dataset lacks enough information for a car, exclude it from top results or label it as low-confidence.

### Very Small Candidate Set

- If only 1 or 2 cars match, return them and explain the limited result set.

### Too Many Hard Filters

- Suggest which filters to relax first, such as brand or feature requirements.

### Ambiguous Natural Language

- Interpret obvious intent when possible, otherwise ask one clarifying follow-up.

## 6. MVP Success Criteria

- User can complete input in under 2 minutes.
- System returns recommendations in a single response.
- Each recommendation includes clear reasoning.
- System gracefully handles no-match and conflicting-input scenarios.
- Results feel useful enough to support shortlisting, not final purchase decisions.
