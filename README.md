# Advertorial Agent

Claude Code skill that generates high-converting native-feeling advertorials and pushes them to Framer via CMS.

## Setup

1. `cp .env.example .env` and fill in keys.
2. `pip install -e .[dev]` from this directory.
3. One-time corpus index: `python -m scripts.index_corpus`
4. Build the Framer template page (see `docs/specs/2026-05-08-advertorial-agent-design.md` Section 7).

## Usage

In Claude Code: `/advertorial` to start a new run, then follow the conversational prompts.

See spec: `~/Dropbox/.../Advertorial Agent/docs/specs/2026-05-08-advertorial-agent-design.md`
