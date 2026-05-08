# Advertorial Agent

Claude Code skill that generates high-converting native-feeling advertorials and pushes them to Framer via CMS.

## Setup

Requires Python 3.11+.

1. Create and activate a virtualenv:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```
2. `cp .env.example .env` and fill in keys and paths.
3. `pip install -e .[dev]`.
4. One-time corpus index: `python -m scripts.index_corpus`.
5. Build the Framer template page (see the design spec, Section 7).

## Usage

In Claude Code: `/advertorial` to start a new run, then follow the conversational prompts.

See spec: ~/Dropbox/01. Professional/02. AI Tools/Advertorial Agent/docs/specs/2026-05-08-advertorial-agent-design.md
