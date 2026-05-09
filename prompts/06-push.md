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

### Step 2: Discover the live Framer schema

Always start by calling `mcp__unframer__getCMSCollections` to get the current `advertorials` and `advertorial_sections` schemas. Field IDs and enum case IDs are auto-generated and may have changed since this prompt was written. Build a local map of `field_name → field_id` and `enum_value_name → case_id` for both collections.

If a required field is missing (e.g., `byline_role`) or named differently (e.g., `layout_archetypes` plural in Framer vs `layout_archetype` singular in our payload), reconcile gracefully:

- Field name mappings (apply when building upsert payloads):
  - `layout_archetype` (payload) → `layout_archetypes` (Framer)
- If a field doesn't exist on the Framer side, omit it from the upsert (do not error).
- Do NOT send a `slug` field to the parent collection — Framer auto-generates the slug from the title field (`headline`) for routing. The payload's `slug` value is for our own deduplication tracking only.

### Step 3: Upload images as Framer assets

For each unique image referenced in the payload (`parent.hero_image_local_path` plus every `section.image_local_path` that is non-null):

The unframer MCP does not expose a dedicated asset upload primitive surfaced in the tool list. Use this fallback path:

```bash
curl -F "reqtype=fileupload" -F "fileToUpload=@<absolute path to image>" https://catbox.moe/user/api.php
```

Catbox returns a public image URL. Record each mapping in `runs/<id>/asset-urls.json`:

```json
{
  "<absolute local path>": "<public url returned by catbox>"
}
```

Image fields on Framer CMS items accept a public URL string directly as their value.

### Step 4: Find or create the parent advertorials row

Call `mcp__unframer__getCMSItems` for the `advertorials` collection. Search the returned items for one whose auto-generated slug matches `payload.parent.slug`. If matched, capture its `id` (this is the Framer-generated CMS item ID — we'll need it for child references and for idempotent updates).

If no match exists, you'll create a new item in Step 5 and capture the new `id`.

### Step 5: Upsert the parent CMS row

Build a `fieldData` object using the field IDs from Step 2's schema. The structure for each field follows Framer's typed value format:

```json
{
  "<headline_field_id>":      { "type": "string",   "value": "<headline>" },
  "<subhead_field_id>":       { "type": "string",   "value": "<subhead>" },
  "<byline_name_field_id>":   { "type": "string",   "value": "<byline_name>" },
  "<byline_role_field_id>":   { "type": "string",   "value": "<byline_role>" },
  "<published_date_field_id>": { "type": "date",    "value": "<ISO 8601 date>" },
  "<niche_field_id>":         { "type": "string",   "value": "<niche>" },
  "<voice_archetype_field_id>": { "type": "string", "value": "<voice_archetype>" },
  "<layout_archetypes_field_id>": { "type": "enum", "value": "<case ID matching layout_archetype name>" },
  "<palette_primary_field_id>": { "type": "color", "value": "<hex>" },
  "<palette_accent_field_id>": { "type": "color",  "value": "<hex>" },
  "<palette_cta_field_id>":   { "type": "color",   "value": "<hex>" },
  "<font_heading_field_id>":  { "type": "string",  "value": "<font name>" },
  "<font_body_field_id>":     { "type": "string",  "value": "<font name>" },
  "<hero_image_field_id>":    { "type": "image",   "value": "<public asset url>" },
  "<final_cta_text_field_id>": { "type": "string", "value": "<cta text>" },
  "<final_cta_url_field_id>": { "type": "link",    "value": "<cta url>" }
}
```

For the enum value (`layout_archetypes`), translate the human-readable name (e.g., `product_review_listicle`) into Framer's enum case ID by looking it up in the schema returned by Step 2.

Call `mcp__unframer__upsertCMSItem` with:
- `collectionId`: the `advertorials` collection ID
- `itemId`: the parent's existing item ID if found in Step 4, otherwise omit (Framer creates a new one)
- `fieldData`: the object above

Capture the response's item ID as `<parent_item_id>` — you'll use it for every child section.

### Step 6: Find existing section rows

Call `mcp__unframer__getCMSItems` for the `advertorial_sections` collection. Filter the returned items in code to those whose `parent_slug` (collectionReference) value equals `<parent_item_id>`. Build a map `order_index → existing_section_item_id` so you can update existing sections instead of creating duplicates.

### Step 7: Upsert each child section row

For each section in `payload.sections`, in `order_index` order:

```json
{
  "<parent_slug_field_id>": { "type": "collectionReference", "value": "<parent_item_id>" },
  "<order_index_field_id>": { "type": "number", "value": <order_index> },
  "<section_type_field_id>": { "type": "enum", "value": "<case ID for this section_type>" },
  "<heading_field_id>":     { "type": "string", "value": "<heading>" },
  "<body_field_id>":        { "type": "formattedText", "value": "<body markdown>" },
  "<image_field_id>":       { "type": "image", "value": "<public asset url or null>" },
  "<cta_text_field_id>":    { "type": "string", "value": "<cta text or empty string>" },
  "<cta_url_field_id>":     { "type": "link", "value": "<cta url or null>" },
  "<design_emphasis_field_id>": { "type": "enum", "value": "<case ID for low/normal/high>" }
}
```

Look up the section type's enum case ID in the schema (e.g., `numbered_reason` → `kzyxWbb4B`).

Call `mcp__unframer__upsertCMSItem` with:
- `collectionId`: the `advertorial_sections` collection ID
- `itemId`: the existing section's item ID from Step 6's map (if `order_index` matches), otherwise omit
- `fieldData`: the object above

Track the result for each section. If any single section upsert fails, log the section index but continue with remaining sections.

### Step 8: Validate child count

After all section upserts, call `mcp__unframer__getCMSItems` again on `advertorial_sections`, filter by `parent_slug == <parent_item_id>`, and confirm the count equals `len(payload.sections)`. If mismatch, mark the push as partial.

### Step 9: Get the live URL

Call `mcp__unframer__getProjectWebsiteUrl`. If a published URL is returned, compose `<published_url>/advertorial/<auto_slug>`. If only staging is available, use staging. If neither exists, the user has not published the project yet — note this in `push-result.md` and remind them to publish.

The `<auto_slug>` is the Framer-generated slug from the parent row's `headline`. It's typically a kebab-cased version of the headline (e.g., `why-shelters-are-switching-to-these-pee-pads`). Confirm by inspecting the parent item's slug in the response from Step 5.

### Step 10: Write push-result.md

```yaml
---
status: success
slug: "<auto-generated slug>"
parent_item_id: "<parent_item_id>"
live_url: "https://<project-domain>/advertorial/<slug>"
sections_uploaded: 8
sections_expected: 8
asset_uploads: 5
errors: []
---
```

If status is partial, list the failed steps and which sections failed by index.

### Step 11: Update state

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

### Step 12: Report to user

```
Live preview: https://<project-domain>/advertorial/<slug>

Run complete. Total cost: $X.XX.
```

## Failure handling

- **Asset upload fails:** retry once, then stop. Mark `status: partial`. Tell user `/advertorial push` will resume.
- **Schema discovery fails:** stop and tell user. Phase 6 cannot proceed without the live schema.
- **Parent upsert fails:** stop, do not attempt section upserts. Mark `status: partial`.
- **A section upsert fails mid-batch:** continue with remaining sections; mark partial; list failed indexes.
- **Project not published (no production / staging URL):** push CMS rows successfully, but tell the user no live URL is available until they publish in Framer's UI.
- **Re-run after partial failure:** idempotency on parent slug match (Step 4) and `(parent_item_id, order_index)` match (Step 6) means re-running is safe.
