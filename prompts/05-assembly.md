# Phase 5 — Assembly

You are combining all artifacts into one structured payload that Phase 6 will push to Framer.

## Inputs (re-hash all)

- `runs/<id>/intake.md`
- `runs/<id>/copy.md`
- `runs/<id>/design.md`
- `runs/<id>/image-briefs.md`
- `runs/<id>/images/*.png`

If any artifact's hash differs from `state.json`, treat the on-disk version as ground truth.

## Build the assembly object

Read `copy.md` and `design.md` as pure YAML, merge into the assembly shape that `scripts.framer_push.build_payload` consumes:

```bash
python -c "
import yaml
from datetime import date
from scripts.state import current_run_dir, load_state, generate_run_id

IMAGE_BEARING = {'hero','numbered_reason','proof_quote','before_after','expert_quote','comparison_table','mechanism_explainer','lifestyle_routine'}
FINAL_CTA_URL = input('Final CTA URL (destination for all CTA buttons): ').strip()

run = current_run_dir()
state = load_state(run)
copy = yaml.safe_load((run / 'copy.md').read_text())
design = yaml.safe_load((run / 'design.md').read_text())
intake = state.intake.model_dump()

emphasis = design.get('section_emphasis') or []
assert len(emphasis) == len(copy['sections']), f'design.section_emphasis length mismatch: {len(emphasis)} vs {len(copy[\"sections\"])}'
assert copy['sections'][0]['section_type'] == 'hero', 'First section must be hero (Phase 2 convention)'

def image_path(i: int, section_type: str) -> str | None:
    if section_type not in IMAGE_BEARING:
        return None
    return str(run / 'images' / f'{i:02d}-{section_type}.png')

final_cta = next((s.get('cta_text') for s in copy['sections'] if s['section_type'] == 'final_verdict'), None)
final_cta = final_cta or next((s.get('cta_text') for s in reversed(copy['sections']) if s['section_type'] == 'cta_button'), 'Get It Today')

assembly = {
    'slug': generate_run_id(copy['headline']),
    'headline': copy['headline'],
    'subhead': copy['subhead'],
    'byline_name': copy['byline_name'],
    'byline_role': copy['byline_role'],
    'published_date': date.today().isoformat(),
    'niche': intake['niche'],
    'voice_archetype': intake['voice_archetype'],
    'layout_archetype': intake['layout_archetype'],
    'palette_primary': design['palette_primary'],
    'palette_accent': design['palette_accent'],
    'palette_cta': design['palette_cta'],
    'font_heading': design['font_heading'],
    'font_body': design['font_body'],
    'hero_image': str(run / 'images' / '00-hero.png'),  # convention: section 0 is always hero
    'final_cta_text': final_cta,
    'final_cta_url': FINAL_CTA_URL,
    'sections': [
        {
            'section_type': s['section_type'],
            'heading': s.get('heading', ''),
            'body': s.get('body', ''),
            'image': image_path(i, s['section_type']),
            'cta_text': s.get('cta_text'),
            'cta_url': FINAL_CTA_URL if s.get('cta_url') == 'TBD' else s.get('cta_url'),
            'design_emphasis': emphasis[i],
        }
        for i, s in enumerate(copy['sections'])
    ],
}

(run / 'assembly.md').write_text(yaml.safe_dump(assembly, sort_keys=False, allow_unicode=True))
print(f'Assembly written, {len(assembly[\"sections\"])} sections')
"
```

## final_cta_url handling

If `copy.md` left `cta_url: TBD`, the script above will prompt for it once. Use that for ALL `cta_button` sections and the parent `final_cta_url`.

## Validation

Validate the assembly by feeding it through `build_payload`:

```bash
python -c "
import yaml
from scripts.state import current_run_dir
from scripts.framer_push import build_payload
run = current_run_dir()
data = yaml.safe_load((run / 'assembly.md').read_text())
payload = build_payload(data)
print(f'OK: {len(payload.sections)} sections, slug={payload.parent.slug}')
"
```

Expected: `OK: N sections, slug=<slug>`. If validation fails (raises), fix `assembly.md` (likely an invalid section_type or missing required field) and re-run.

## After writing

1. Update state:

```bash
python -c "
from scripts.state import current_run_dir, load_state, save_state, advance_phase
rd = current_run_dir()
s = load_state(rd)
s.record_artifact('assembly.md', rd / 'assembly.md')
save_state(rd, s)
advance_phase(rd, 'assembly', 'awaiting_review')
"
```

2. Tell the user: "Assembled draft ready at `runs/<id>/assembly.md`. Review the full payload. Edit any field if needed, then `/advertorial continue` to push to Framer."

3. Stop.
