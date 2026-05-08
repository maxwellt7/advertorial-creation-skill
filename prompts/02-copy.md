# Phase 2 — Copy generation

You are generating the editorial body of the advertorial as an ordered list of typed sections. The result must read like an article, NOT a brand landing page.

## Inputs

- `runs/<run-id>/intake.md` — read this first
- `VOICE_KB.md`, `DESIGN_KB.md`, `CONVERSION_KB.md` — load the relevant sections for the chosen archetype, headline formula, and layout
- `ADVERTORIAL_TEMPLATE.md` — the master skeleton

## RAG queries — RUN ALL FOUR

Use the intake's niche and voice_archetype to pull niche-matched corpus exemplars. Run each query and keep the outputs in your working context for the generation step.

```bash
# Hooks
python -c "from scripts.rag_query import query; import json; print(json.dumps([r.model_dump() for r in query(text='hook for {product} solving {primary_problem}', chunk_types=['hook_headline'], niche='{niche}', source_corpus='advertorial', top_k=5)], indent=2))"

# Voice examples
python -c "from scripts.rag_query import query; import json; print(json.dumps([r.model_dump() for r in query(text='voice example for {voice_archetype}', chunk_types=['voice_example'], voice_archetype='{voice_archetype}', source_corpus='advertorial', top_k=8)], indent=2))"

# Structural beats
python -c "from scripts.rag_query import query; import json; print(json.dumps([r.model_dump() for r in query(text='structural beats for {layout_archetype}', chunk_types=['structural_beat'], niche='{niche}', top_k=6)], indent=2))"

# CTA patterns
python -c "from scripts.rag_query import query; import json; print(json.dumps([r.model_dump() for r in query(text='cta for {offer}', chunk_types=['cta_pattern'], niche='{niche}', top_k=4)], indent=2))"
```

## Generation rules

1. Choose section types from this enum (these are the only valid types):
   `hero, intro, numbered_reason, proof_quote, before_after, expert_quote, comparison_table, mechanism_explainer, lifestyle_routine, cta_button, risk_reversal, final_verdict, faq`
2. **Section 0 MUST be `hero`** — Phase 5 assembly assumes this convention.
3. Order remaining sections following CONVERSION_KB's master beat sheet, adapted to the layout_archetype.
4. Use 5–8 numbered_reason sections for product_review_listicle; fewer for native_news.
5. Insert at least 2 cta_button sections (after a strong proof, and final).
6. Insert risk_reversal before the final cta_button if the offer supports it.
7. Voice rules:
   - Match the rhythm patterns from VOICE_KB.md for the chosen archetype.
   - Use 2+ verbatim-style example sentences from the RAG voice_example results as anchors (do NOT plagiarize — borrow rhythm and phrase shape, not text).
   - Strictly avoid red-flag phrases listed in VOICE_KB.md.
8. Image-bearing sections (hero, numbered_reason, proof_quote, before_after, expert_quote, comparison_table, mechanism_explainer, lifestyle_routine) include a one-sentence `image_brief` describing the image direction.
9. Compliance: respect `intake.compliance_limits`.

## Output format

Write the result to `runs/<run-id>/copy.md` as a single pure-YAML document (no markdown frontmatter delimiters, no markdown headers). This makes Phase 5 parsing trivial.

```yaml
headline: "..."
subhead: "..."
byline_name: "..."
byline_role: "..."

sections:
  - section_type: hero
    heading: "..."
    body: |
      Multi-paragraph
      body text.
    image_brief: "..."

  - section_type: intro
    heading: "..."
    body: |
      ...

  - section_type: numbered_reason
    heading: "Reason #1: ..."
    body: |
      ...
    image_brief: "..."

  # ... all remaining sections in order ...

  - section_type: cta_button
    cta_text: "..."
    cta_url: TBD  # user supplies in Phase 5
```

Use YAML block scalars (`|`) for body text; keep section_type values exactly matching the enum in `scripts/image_router.KNOWN_SECTION_TYPES`.

## After writing

1. Update state:

```bash
python -c "
from scripts.state import current_run_dir, load_state, save_state, advance_phase
from pathlib import Path
rd = current_run_dir()
s = load_state(rd)
s.record_artifact('copy.md', rd / 'copy.md')
save_state(rd, s)
advance_phase(rd, 'copy', 'awaiting_review')
"
```

2. Tell the user: "Copy ready at `runs/<id>/copy.md`. Open it, edit freely, then `/advertorial continue` (or `/advertorial regenerate copy --note 'tighten reason 3'`)."

3. Stop. Do NOT proceed to Phase 3 in the same turn.
