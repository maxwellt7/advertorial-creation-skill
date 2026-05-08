# Phase 1 — Intake

You are gathering the inputs needed to generate the advertorial. Use the corpus's `ADVERTORIAL_TEMPLATE.md` as the field reference.

## What to do

1. Greet the user briefly and ask for an opening brief in their own words. Accept whatever shape they give: a paragraph, a product page URL, a list of bullets.
2. Parse the brief into the following intake fields. Ask focused follow-up questions to fill gaps. NEVER ask a question whose answer is already in the brief.

| Field | What you need |
|---|---|
| product | Name + one-sentence description |
| niche | One of: consumer product / ecommerce, nutrition / supplements, beauty / skincare, apparel / socks, footwear / comfort shoes, sleep / bedding, coffee / protein beverage, haircare, CBD / stress relief, oral care, pet / home goods. If user's product fits none, propose the closest. |
| target_customer | Who has the problem |
| primary_problem | Specific frustration |
| desired_outcome | Specific result |
| unique_mechanism | Why this works differently |
| proof_assets | Reviews / expert / demo / before-after / guarantee — what's available |
| offer | Price / discount / bundle / trial / guarantee |
| compliance_limits | What can't be claimed |

3. Recommend a **voice archetype** based on the brief. Choose ONE from VOICE_KB.md:
   - first_person_tester (skeptical reviewer)
   - trend_aware_social_proof
   - clinical_authority
   - problem_agitation_relief
   - beauty_lifestyle_upgrade

   Tell the user your choice and ask if they want to swap.

4. Recommend a **headline formula** from CONVERSION_KB.md:
   - trial_winner
   - social_switch
   - persistent_problem
   - expert_explainer
   - obsession_trend

   Tell the user your choice and ask if they want to swap.

5. Recommend a **layout archetype** from DESIGN_KB.md:
   - native_news
   - product_review_listicle
   - authority_explainer
   - lifestyle_routine_upgrade

   Tell the user your choice and ask if they want to swap.

6. Once all fields are filled and archetypes chosen, write the result to `runs/<run-id>/intake.md` as a YAML block followed by a human-readable summary. Use this exact format:

```yaml
---
product: "..."
niche: "..."
target_customer: "..."
primary_problem: "..."
desired_outcome: "..."
unique_mechanism: "..."
proof_assets: "..."
offer: "..."
compliance_limits: "..."
voice_archetype: "..."
headline_formula: "..."
layout_archetype: "..."
---
```

7. Update state via:

```bash
python -c "
from scripts.state import current_run_dir, load_state, save_state, IntakeData, advance_phase
rd = current_run_dir()
s = load_state(rd)
s.intake = IntakeData(product='...', niche='...', ...)
save_state(rd, s)
advance_phase(rd, 'copy', 'in_progress')
"
```

8. Tell the user: "Intake captured. Run `/advertorial continue` to proceed to copy generation."

## Constraints

- Ask one focused question per turn. Do not bombard with a checklist.
- If the user provides a URL, use WebFetch to read the page and infer fields, then confirm only the gaps and the archetype recommendations.
- Never advance to Phase 2 without all fields filled.
