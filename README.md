# Advertorial Agent

A Claude Code skill that generates high-converting, human-sounding editorial advertorials from a conversational brief — with human-in-the-loop approval at four checkpoints — and pushes the finished page live to Framer via the unframer MCP.

The skill is grounded in a corpus of **159 top-performing listicle advertorials and 2,338 paired Facebook ads** reverse-engineered from the Funnel of the Week leaderboard. Voice rhythm, conversion psychology, layout archetypes, and image archetypes are all retrieved per-niche from this corpus at generation time.

> Status: v1 single-user. Designed so the state model + payload schema port cleanly to a Next.js UI later.

## What it does

`/advertorial new` walks you through a six-phase pipeline:

```
Intake → Copy → Design → Images → Assembly → Push to Framer
            ▲       ▲        ▲          ▲
       file edit  chat    chat     file edit
       (you)    (you)    (you)     (you)
```

At each `▲` checkpoint the skill stops and waits for your approval. You can:
- Edit the artifact file directly in your editor (Copy and Assembly phases)
- Reply in chat with `approve`, `regen hero — more daylight`, `swap palette to warm neutral`, `restart phase`, etc. (Design and Images phases)
- Hash detection means hand-edits are picked up automatically on `/advertorial continue`

The final output is one row in your Framer `advertorials` CMS collection plus N rows in `advertorial_sections`, rendered by a template page you build once.

## How it's grounded

The skill never invents structure or voice. Every generation phase pulls niche-matched exemplars from a Pinecone index built once from the corpus:

| Phase | Retrieval |
|---|---|
| Copy — hooks | `chunk_type=hook_headline`, niche-filtered |
| Copy — voice | `chunk_type=voice_example`, voice_archetype-filtered |
| Copy — beats | `chunk_type=structural_beat`, niche-filtered |
| Copy — CTA | `chunk_type=cta_pattern`, niche-filtered |
| Images | `chunk_type IN [image_prompt, fb_image_prompt]`, niche-filtered |

Plus four standalone knowledge bases (`VOICE_KB`, `DESIGN_KB`, `CONVERSION_KB`, `IMAGE_KB`) loaded into every relevant phase as universal rules.

## Architecture

```
.
├── SKILL.md                          # Claude Code skill orchestrator
├── prompts/
│   ├── 01-intake.md                  # phase-by-phase prompt fragments
│   ├── 02-copy.md
│   ├── 03-design.md
│   ├── 04-images.md
│   ├── 05-assembly.md
│   ├── 06-push.md
│   └── intent-classifier.md          # Haiku-backed user-reply parser
├── scripts/
│   ├── state.py                      # atomic state.json + run lifecycle + artifact hashing
│   ├── cost_tracker.py               # per-run cost ledger with $5 hard ceiling
│   ├── corpus_chunker.py             # parses advertorial + FB ad markdowns into typed chunks
│   ├── index_corpus.py               # one-shot Pinecone indexer
│   ├── rag_query.py                  # niche-filtered retrieval per phase
│   ├── image_router.py               # routes section_type → fal/openai
│   ├── image_gen.py                  # Flux Pro 1.1 / Ideogram v2 / gpt-image-1 wrappers
│   ├── intent_classifier.py          # Claude Haiku structured-output classifier
│   └── framer_push.py                # parent + sections payload builder
└── tests/                            # 43 unit tests
```

### Six phases

| # | Phase | Inputs | Outputs | HITL surface |
|---|---|---|---|---|
| 1 | **Intake** | conversational brief | `intake.md` (filled fields, archetypes) | in-chat confirm |
| 2 | **Copy** | intake + KBs + RAG (hooks, voice, beats, CTAs) | `copy.md` — typed section list | **file** — edit, then `continue` |
| 3 | **Design** | copy + DESIGN_KB | `design.md` — palette, fonts, per-section emphasis | in-chat (`approve` / `swap palette to X`) |
| 4 | **Images** | copy + IMAGE_KB + RAG | `image-briefs.md` + `images/*.png` | in-chat (`regen hero — more daylight`) |
| 5 | **Assembly** | all prior | `assembly.md` — Framer payload | **file** — edit, then `continue` |
| 6 | **Push** | assembly | Framer asset uploads + CMS upserts → live URL | preview link in chat |

### Image routing

| Section type | Model | Why |
|---|---|---|
| `hero`, `numbered_reason`, `before_after`, `expert_quote`, `lifestyle_routine` | Flux Pro 1.1 (fal) | Photorealism, product-in-context |
| `proof_quote`, `comparison_table` | Ideogram v2 (fal) | Renders embedded text reliably |
| `mechanism_explainer` | gpt-image-1 (OpenAI) | Diagrams, product cutaways |

### Framer CMS schema

Two collections, parent + child, linked by `slug`:

**`advertorials`** — one row per advertorial. Fields: `slug`, `headline`, `subhead`, `byline_*`, `niche`, `voice_archetype`, `layout_archetype`, `palette_*`, `font_*`, `hero_image`, `final_cta_*`.

**`advertorial_sections`** — many rows per advertorial. Fields: `parent_slug`, `order_index`, `section_type` (enum of 13 types), `heading`, `body`, `image`, `cta_*`, `design_emphasis`. The Framer template page iterates over these in `order_index` order.

## Setup

Requires Python 3.11+ and Claude Code with the unframer MCP server configured.

```bash
git clone https://github.com/maxwellt7/advertorial-creation-skill ~/.claude/skills/advertorial-agent
cd ~/.claude/skills/advertorial-agent

python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

cp .env.example .env
# Edit .env — fill in:
#   ANTHROPIC_API_KEY   - claude.ai console
#   OPENAI_API_KEY      - platform.openai.com (used for embeddings + gpt-image-1)
#   FAL_KEY             - fal.ai/dashboard/keys
#   PINECONE_API_KEY    - app.pinecone.io
#   ADVERTORIAL_CORPUS_PATH  - absolute path to your listicle_deliverables folder
#   ADVERTORIAL_RUNS_PATH    - where per-run state + artifacts are written
```

Run the test suite to confirm everything wires up:

```bash
pytest -v
# 43 passed
```

## One-time setup

### 1. Index the corpus into Pinecone

```bash
python -m scripts.index_corpus
```

Embeds all `/advertorials/*.md` and `/facebook_ads/*.md` files into typed chunks (~15K total) and upserts them into the Pinecone index `advertorial-corpus`. Takes 10–20 minutes. Costs about $1 in OpenAI embedding fees.

Verify retrieval works:

```bash
python -c "
from scripts.rag_query import query
r = query(text='hook for pet pee pad', chunk_types=['hook_headline'], niche='pet / home goods', source_corpus='advertorial', top_k=3)
[print(f'{x.score:.3f}  {x.text[:100]}') for x in r]
"
```

You should see relevant headlines with scores above 0.4.

### 2. Build the Framer template page

In Framer:

1. **Create the two CMS collections** described in [Framer CMS schema](#framer-cms-schema) above. The `section_type` field is a single-select with all 13 enum values: `hero, intro, numbered_reason, proof_quote, before_after, expert_quote, comparison_table, mechanism_explainer, lifestyle_routine, cta_button, risk_reversal, final_verdict, faq`.
2. **Create a template page at `/advertorial/[slug]`** that binds to a single `advertorials` row and iterates `advertorial_sections` filtered by `parent_slug = current.slug`, ordered by `order_index`.
3. **Build one component variant per `section_type`**, styled per the layout archetypes in `DESIGN_KB.md` (native-news, product-review-listicle, authority-explainer, lifestyle-routine-upgrade).
4. Test render with one hand-built sample row before connecting the skill.

The skill never modifies the Framer page itself — only writes CMS rows. So you can iterate on design freely without regenerating advertorials.

## Usage

In Claude Code:

```
/advertorial new
```

Paste a brief in your own words (a paragraph, a product page URL, or bullets). The skill asks targeted follow-ups, recommends a voice archetype + headline formula + layout archetype, then writes `intake.md`.

```
/advertorial continue
```

Advances through Copy → Design → Images → Assembly → Push. At each checkpoint the skill stops and waits for you.

### Commands

| Command | Behavior |
|---|---|
| `/advertorial` (no args) | Resume from current state |
| `/advertorial new` | Start a fresh run |
| `/advertorial continue` | Advance from `awaiting_review` |
| `/advertorial regenerate <phase> --note "..."` | Re-run a phase with note appended |
| `/advertorial push` | Re-run Phase 6 only (after partial failure) |
| `/advertorial recover --run <id>` | Reconstruct `state.json` from artifacts |
| `/advertorial status` | Print run summary |

### HITL replies (chat phases)

At Design and Images checkpoints, reply with any of:

- `approve` — advance to next phase
- `regen <target>` — regenerate one image / one design token
- `regen hero — more daylight, less cluttered counter` — regenerate with modifier
- `swap palette to warm neutral` — change palette
- `swap hero to lifestyle_routine archetype` — switch image archetype
- `restart phase` — full phase regeneration

A Claude Haiku call parses your intent, so phrasing is forgiving.

### Editing artifacts directly

For Copy and Assembly phases, just open the file in your editor:

```
open ~/Dropbox/.../Advertorial Agent/runs/<run-id>/copy.md
```

Edit anything, save, then `/advertorial continue`. The skill hashes the file and detects your edits — your version becomes ground truth for downstream phases.

## State and artifacts

Every run lives in `<ADVERTORIAL_RUNS_PATH>/<run-id>/`:

```
2026-05-08-puppy-pee-pad-001/
├── state.json              # phase, status, cost, artifact hashes
├── intake.md               # filled intake fields
├── copy.md                 # ordered section list with body, image briefs
├── design.md               # palette + fonts + per-section emphasis
├── image-briefs.md         # final composed prompts per image
├── images/
│   ├── 00-hero.png
│   ├── 02-numbered_reason.png
│   └── ...
├── assembly.md             # Framer-ready payload (parent + sections)
└── push-result.md          # live URL + upsert result
```

State writes are atomic (temp file + `os.replace`). Regenerated artifacts archive their predecessors as `<artifact>.v1.md`, `.v2.md`, etc.

## Cost guardrail

Each run has a `$5` hard ceiling tracked in `state.cost_usd`. At 80% the skill warns before the next paid call. At 100% it pauses. Typical run cost: ~$0.50 Anthropic + ~$0.05 embeddings + ~$1.50–3.00 image generation = under $4.

## Voice archetypes

Choose one in Phase 1. Each has its own rhythm rules and example sentences in `VOICE_KB.md`:

| Archetype | When to use |
|---|---|
| `first_person_tester` | Skeptical reviewer trying multiple options |
| `trend_aware_social_proof` | "Everyone is switching to..." behavioral shift |
| `clinical_authority` | Doctor / dermatologist / clinical study angle |
| `problem_agitation_relief` | Sensory pain → mechanism → relief |
| `beauty_lifestyle_upgrade` | Routine upgrade with sensory benefits |

## Layout archetypes

Choose one in Phase 1. Each maps to a Framer component variant set:

- `native_news` — single-column article, byline, large hero, body links as buttons
- `product_review_listicle` — numbered reasons, image per reason, CTA every 2–3 reasons
- `authority_explainer` — credentialed lead, problem-mechanism-proof, expert citations
- `lifestyle_routine_upgrade` — soft editorial visuals, sensory benefits, less aggressive urgency

## Tech stack

- **Python 3.11+** — Pydantic v2 for state schema, pytest for unit tests
- **Anthropic API** — generation (Claude) + intent classification (Haiku, structured output)
- **OpenAI API** — `text-embedding-3-large` for the corpus index, `gpt-image-1` for diagrams
- **Pinecone** — vector store, `advertorial-corpus` index, ~15K chunks
- **fal.ai** — Flux Pro 1.1 for photoreal hero/UGC images, Ideogram v2 for text-in-image
- **Framer** — destination CMS, accessed via the [unframer MCP](https://github.com/anthropics/claude-code/blob/main/docs/mcp.md) server in Claude Code

## Tests

```bash
pytest -v
```

43 unit tests covering: state atomic writes + artifact hashing, cost tracker thresholds, advertorial + FB ad chunkers, RAG query filter construction, image router section→model mapping, intent classifier (mocked), Framer payload builder. The image generation, Pinecone upsert, and Framer push paths are covered by the manual golden-path test rather than unit tests.

## Spec and plan

The full design spec and implementation plan live alongside the corpus in your Dropbox (not in this repo, since they reference local paths):

- Spec: `docs/specs/2026-05-08-advertorial-agent-design.md`
- Plan: `docs/plans/2026-05-08-advertorial-agent-implementation.md`

## Roadmap

- v1 (this): single-user Claude Code skill, end-to-end with manual Framer template build
- v1.1: FB ad sibling tool (uses the same `fb_*` chunks already indexed)
- v2: Next.js web app — same state model, same payload schema, polished intake form, multi-user

## License

Personal project. Not currently accepting contributions.
