# Phase 6 — Framer push

You are uploading the approved assembly to Framer via the unframer MCP. This phase is idempotent — safe to re-run.

## Inputs

- `runs/<id>/assembly.md` (re-hash; treat as ground truth)
- All approved images in `runs/<id>/images/`

## Push sequence

### Step 1: Build the validated payload

```bash
python -c "
import yaml
from scripts.state import current_run_dir
from scripts.framer_push import build_payload
run = current_run_dir()
data = yaml.safe_load((run / 'assembly.md').read_text())
payload = build_payload(data)
(run / 'push-payload.json').write_text(payload.model_dump_json(indent=2))
print(f'OK: {len(payload.sections)} sections')
"
```

### Step 2: Upload images as Framer assets

For each unique image referenced in the payload (parent.hero_image_local_path + every section.image_local_path that is non-null):

Use the unframer MCP tool to upload the asset. The exact tool and parameter shape depends on what's exposed by the MCP server. Check via `mcp__unframer__getProjectXml` or `mcp__unframer__createCodeFile` to discover the asset upload primitive.

If the unframer MCP exposes a dedicated asset endpoint, use it. If not, the fallback is to host the image at a public URL (e.g., upload to a static host) and reference that URL in the CMS row.

Record each upload's resulting Framer asset URL in `runs/<id>/asset-urls.json` as `{"<local_path>": "<framer_asset_url>"}`.

### Step 3: Upsert parent CMS row

Use `mcp__unframer__upsertCMSItem` with the `advertorials` collection.
- Map every parent.* field to the corresponding CMS field.
- Substitute hero_image_local_path with the asset URL from asset-urls.json.
- Use parent.slug as the unique key for upsert idempotency.

### Step 4: Upsert each child section row

For each section in payload.sections (in order_index order):

Use `mcp__unframer__upsertCMSItem` with the `advertorial_sections` collection.
- Map every field. Substitute image_local_path with asset URL if non-null.
- Use the composite key (parent_slug, order_index) as the unique upsert key.

### Step 5: Validate child count

`mcp__unframer__getCMSItems` on `advertorial_sections` filtered by parent_slug.
Confirm count == len(payload.sections). If mismatch, log to push-result.md and warn user.

### Step 6: Get the live URL

`mcp__unframer__getProjectWebsiteUrl` and compose the live URL: `<base_url>/advertorial/<slug>`.

### Step 7: Write push-result.md

```yaml
---
status: success | partial
slug: "<slug>"
live_url: "https://<project-domain>/advertorial/<slug>"
parent_uploaded: true
sections_uploaded: 8
sections_expected: 8
asset_uploads: 5
errors: []
---
```

### Step 8: Update state

```bash
python -c "
from scripts.state import current_run_dir, load_state, save_state, advance_phase
rd = current_run_dir()
s = load_state(rd)
s.record_artifact('push-result.md', rd / 'push-result.md')
save_state(rd, s)
advance_phase(rd, 'complete', 'complete')
"
```

### Step 9: Report to user

```
Live preview: https://<project-domain>/advertorial/<slug>

Run complete. Total cost: $X.XX.
```

## Failure handling

- If asset upload fails: retry once, then stop. Mark `status: partial` in push-result.md. Tell user `/advertorial push` will resume.
- If parent upsert fails: stop, do not attempt section upserts. Mark `status: partial`.
- If a section upsert fails mid-batch: continue with remaining sections, mark partial, list the failed indexes in push-result.md.
- Re-run after partial failure: idempotency on `slug` and `(parent_slug, order_index)` means rerunning is safe.
