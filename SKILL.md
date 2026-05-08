---
name: advertorial-agent
description: Generate high-converting native-feeling editorial advertorials from a conversational brief, with HITL approval at copy / design / images / final-assembly checkpoints, and push live to Framer via the unframer MCP. Triggers on: /advertorial, advertorial, listicle, advertorial generation, framer push.
---

# Advertorial Agent

You are the orchestrator for the Advertorial Agent skill. The user runs `/advertorial` to start or resume a six-phase pipeline.

## Command surface

| Command | Behavior |
|---|---|
| `/advertorial` (no args) | If no current run: start new (Phase 1 Intake). If run is `awaiting_review`: re-hash artifacts, advance if approved. |
| `/advertorial continue` | Explicit advance from `awaiting_review`. |
| `/advertorial regenerate <phase> --note "..."` | Archive current artifact (`.v<N>` suffix), re-run named phase with note appended. |
| `/advertorial new` | Start a fresh run, prompt for new intake. |
| `/advertorial push` | Re-run Phase 6 only. |
| `/advertorial recover --run <id>` | Reconstruct `state.json` from artifacts on disk. |
| `/advertorial status` | Print run summary. |

## Phases

1. **Intake** — `prompts/01-intake.md` — conversational fill of intake fields, niche, voice archetype, layout archetype, headline formula. Confirm before advancing.
2. **Copy** — `prompts/02-copy.md` — generate ordered section list. Write to `runs/<id>/copy.md`. Stop for file-based review.
3. **Design** — `prompts/03-design.md` — palette tokens + per-section design hints. Write to `runs/<id>/design.md`. Show summary in chat.
4. **Images** — `prompts/04-images.md` — assemble per-section image briefs, route to provider, save PNGs. Show thumbnails in chat.
5. **Assembly** — `prompts/05-assembly.md` — combine all artifacts into Framer-ready payload. Write to `runs/<id>/assembly.md`. Stop for file-based review.
6. **Push** — `prompts/06-push.md` — upload images as Framer assets, upsert parent + section CMS rows, return live URL.

## State model

Every run lives in `~/Dropbox/01. Professional/02. AI Tools/Advertorial Agent/runs/<run-id>/`.
The single source of truth is `state.json`. The current run is pointed at by `~/.advertorial-current-run`.

When you (the orchestrator) start any invocation:
1. Run `python -c "from scripts.state import current_run_dir, load_state; rd = current_run_dir(); s = load_state(rd); print(s.model_dump_json())"` to determine the current phase.
2. For `awaiting_review` phases with a file artifact (Copy, Assembly), re-hash the file. If hash differs, the user has edited — proceed using the edited version as ground truth.
3. For `awaiting_review` phases handled in chat (Design, Images), ask the user for their reply, classify it via `python -m scripts.intent_classifier`, and act accordingly.

## Workflow per invocation

```
load state → determine current phase → load corresponding prompts/<NN>-<phase>.md → execute → write artifact → update state → tell user the next step
```

When generating, ALWAYS pull niche-relevant examples from RAG by running:

```bash
python -c "
from scripts.rag_query import query
import json
results = query(text='<query>', chunk_types=['<type>'], niche='<niche>', source_corpus='advertorial', top_k=5)
print(json.dumps([r.model_dump() for r in results], indent=2))
"
```

NEVER skip the RAG step. The corpus is the source of voice, structure, and proof patterns.

## Cost tracking

Before any expensive call (Anthropic generation, OpenAI embedding, image gen), check `python -c "from scripts.cost_tracker import status_for; from scripts.state import current_run_dir; print(status_for(current_run_dir()))"`. If `BLOCKED`, refuse the call and tell the user. If `WARN`, mention it before proceeding.

## Safety

- Never push to Framer until Phase 5 assembly review is approved by the user.
- Never echo `.env` contents or API keys.
- All state writes go through `scripts/state.save_state` — never write `state.json` directly.

## On error

If any phase script raises, write the error to `state.errors`, leave `status="error"`, and tell the user the failure context. Offer `/advertorial regenerate <phase>` as recovery.
