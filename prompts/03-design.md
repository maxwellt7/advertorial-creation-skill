# Phase 3 — Design tokens

You are choosing the design tokens that the Framer template will consume. You are NOT building a layout; the Framer template already knows how to render each section type. You are setting palette, typography, and per-section emphasis.

## Inputs

- `runs/<run-id>/intake.md`
- `runs/<run-id>/copy.md` (re-hash to detect user edits)
- `DESIGN_KB.md` — load the layout archetype + niche palette section

## Generation rules

1. **Palette** — pick from `DESIGN_KB.md` "Color System by Niche". Output as exact hex values.
   - `palette_primary` — page background
   - `palette_accent` — heading + key inline text
   - `palette_cta` — CTA button color
2. **Typography** — choose two Framer-available fonts:
   - `font_heading` — sentence-case H1, high contrast
   - `font_body` — readable 16–19 px body
   Sensible defaults: Fraunces (heading) + Inter (body) for native_news; Tiempos Headline + Inter for authority_explainer; Editorial New + Inter for lifestyle_routine_upgrade. Override only with reason.
3. **Per-section emphasis** — for each section in `copy.md`, mark `design_emphasis` as `low / normal / high`:
   - hero → high
   - first cta_button after a hook → high
   - final_verdict → high
   - intro, faq → low
   - everything else → normal
4. **Trust elements** — recommend which trust elements (star ratings, byline, before/after proof, expert note, sticky CTA) to include based on `intake.proof_assets`. List them.

## Output format

Write to `runs/<run-id>/design.md` as pure YAML. `section_emphasis` is a list of strings in the SAME ORDER as `sections[]` in `copy.md` — Phase 5 will zip them together.

```yaml
palette_primary: "#FFFFFF"
palette_accent: "#1A1A1A"
palette_cta: "#E84C00"
font_heading: "Fraunces"
font_body: "Inter"
trust_elements:
  - star_ratings_near_hero
  - editorial_byline
  - sticky_cta_mobile
section_emphasis:
  - high      # 0: hero
  - low       # 1: intro
  - normal    # 2: numbered_reason (Reason #1)
  - normal    # 3: numbered_reason (Reason #2)
  - high      # 4: proof_quote
  - high      # 5: cta_button (mid)
  # ... one entry per section in copy.md, in order
```

The number of entries in `section_emphasis` MUST equal `len(copy.md sections)`. Verify before writing.

## After writing

1. Update state:

```bash
python -c "
from scripts.state import current_run_dir, load_state, save_state, advance_phase
rd = current_run_dir()
s = load_state(rd)
s.record_artifact('design.md', rd / 'design.md')
save_state(rd, s)
advance_phase(rd, 'design', 'awaiting_review')
"
```

2. Print a tight summary in chat:
   - Palette swatches as hex + names
   - Font pairing
   - Trust elements
   - High-emphasis sections list

3. Ask: "Approve, or `swap palette to <X>` / `make CTA punchier` / `restart phase`?"

4. When the user replies, classify via:

```bash
python -c "from scripts.intent_classifier import classify; import sys; print(classify(sys.argv[1], phase='design').model_dump_json())" "<user reply>"
```

5. If `approve` → `advance_phase('design', 'complete')` then `advance_phase('images', 'in_progress')` and tell the user to run `/advertorial continue`.
6. If targeted change → regenerate the relevant tokens, rewrite `design.md`, restart this conversation step.
