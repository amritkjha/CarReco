## Common Context
I’m building an AI-assisted car recommendation backend from scratch and recently worked through the early system-design layers: API design, input validation, preference normalization, and follow-up question handling. A big part of the work has been translating messy user intent into reliable backend behavior without overcomplicating the MVP. That journey surfaced a few useful engineering lessons around modular design, AI readiness, ambiguity handling, and how to structure systems so they can scale from rule-based logic to more intelligent recommendation pipelines later.

## Topic Ideas

1. **Why AI systems need layered validation, not just schema validation**  
   Angle: difference between transport validation and business validation, and why both matter in AI-assisted products.

2. **How to design backend modules for AI features before adding the actual AI model**  
   Angle: building API, validation, normalization, and follow-up layers first creates a strong foundation for later intelligence.

3. **Turning messy user intent into structured data: the importance of preference normalization**  
   Angle: converting free text like “need good mileage and automatic” into machine-usable signals, weights, and constraints.

4. **Why ‘no preference’ should not be treated as just another value in recommendation systems**  
   Angle: a subtle but important design choice, converting “no preference” into absence of constraint rather than a literal category.

5. **Follow-up questions are a core product feature, not just a UX patch**  
   Angle: clarification logic improves recommendation quality and prevents bad outputs when inputs are missing, broad, or conflicting.

6. **Handling ambiguity in AI-assisted systems without pretending certainty**  
   Angle: using confidence or ambiguity flags when the backend infers meaning from free text instead of silently acting overconfident.

7. **Hard constraints vs soft preferences: a simple concept that dramatically improves recommendation design**  
   Angle: separating filtering logic from ranking logic makes systems easier to reason about and extend.

8. **Why some user conflicts should trigger clarification, not errors**  
   Angle: cases like preferred brand also being excluded are often better solved with follow-up questions than hard failures.

9. **Building explainable AI-ready backends with rule-based MVPs first**  
   Angle: even before advanced models, you can design systems to support explainability, auditability, and modular evolution.

10. **What building an AI recommendation MVP taught me about system design discipline**  
   Angle: modular decomposition, careful contracts between services, and designing for future scoring/filtering modules.