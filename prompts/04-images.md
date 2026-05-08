# Phase 4 — Image generation

You are generating one image per image-bearing section in `copy.md`. Each image:
1. Pulls 3 niche-matched exemplar prompts from RAG.
2. Combines `IMAGE_KB.md` archetype template + intake context + the 3 exemplars.
3. Routes to the right model via `scripts/image_router.route(section_type)`.
4. Generates via `scripts/image_gen.generate(...)`.
5. Saves to `runs/<id>/images/<order_index:02d>-<section_type>.png`.

## Image-bearing section types

Only these section types get images:
`hero, numbered_reason, proof_quote, before_after, expert_quote, comparison_table, mechanism_explainer, lifestyle_routine`

## Per-section workflow

For each image-bearing section in `copy.md`:

1. Determine section_type and image_brief from copy.md.
2. RAG query:

```bash
python -c "
from scripts.rag_query import query
import json
results = query(
    text='image archetype: {section_type} for {niche}',
    chunk_types=['image_prompt', 'fb_image_prompt'],
    niche='{niche}',
    top_k=3,
)
print(json.dumps([r.model_dump() for r in results], indent=2))
"
```

3. Route the model:

```bash
python -c "from scripts.image_router import route; print(route('{section_type}').model_dump_json())"
```

4. Compose the final prompt as a single paragraph:
   - Start with the IMAGE_KB.md archetype template for that section type, filling its slots.
   - Add product/customer/niche specifics from intake.
   - Add the 3 RAG exemplars as "Style anchors:" appendix.
   - Add aspect ratio (4:3 for hero/numbered_reason/before_after; 1:1 for proof_quote/comparison_table; 4:5 for lifestyle_routine).

5. Append the final prompt to `runs/<id>/image-briefs.md` under a heading for that section.

6. Compute the image filename using the section's `order_index` (its position in `copy.md` sections list, zero-padded) and its `section_type`. Example: section 0 (hero) → `images/00-hero.png`, section 4 (numbered_reason) → `images/04-numbered_reason.png`. This convention is stable across regenerations and matches Phase 5's expectations.

7. Generate:

```bash
python -c "
from scripts.image_gen import generate
from scripts.state import current_run_dir
run = current_run_dir()
dest = run / 'images' / f'{order_index:02d}-{section_type}.png'
result = generate(provider='{provider}', model='{model}', prompt='''{prompt}''', dest=dest, aspect_ratio='{aspect_ratio}')
print(result.path)
"
```

8. Charge cost (rough estimates: Flux ~$0.04, Ideogram ~$0.04, gpt-image-1 ~$0.07):

```bash
python -c "from scripts.cost_tracker import charge; from scripts.state import current_run_dir; charge(current_run_dir(), amount_usd=0.04, reason='image:{order_index}-{section_type}')"
```

## After all images generated

1. Update state:

```bash
python -c "
from scripts.state import current_run_dir, load_state, save_state, advance_phase
rd = current_run_dir()
s = load_state(rd)
s.record_artifact('image-briefs.md', rd / 'image-briefs.md')
save_state(rd, s)
advance_phase(rd, 'images', 'awaiting_review')
"
```

2. Show thumbnails inline in chat with one-liners (use markdown image syntax).

3. Ask: "Approve, or `regen <section>` / `swap <section> to <archetype>` / `restart phase`?"

4. Classify and act on the reply (same pattern as Phase 3).

5. On `regen <section>`:
   - Rename current image to `images/<slug>.v1.png` (increment if v1 exists).
   - Re-run that single section's workflow with the modifier_note appended to the prompt.
   - Show the new image; ask again.

6. On full approve → advance to assembly phase.
