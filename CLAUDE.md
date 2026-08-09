# Project memory — python-template (the trust stack)

## What this repo is

The shared Python template for a three-project open source portfolio, "the trust
stack" — self-hostable, production-grade pieces enterprises actually ask for:

- **groundcite** — grounded answers engine: hybrid retrieval, span-level
  citations, document-level permissions, evals built in. (Python, built first)
- **cachette** — correctness-first semantic cache for LLM APIs: verified hits,
  measured precision, drop-in OpenAI-compatible proxy. (Rust, built second)
- **signoff** — the human sign-off layer for AI agents: approvals, policies,
  durable pause/resume, audit. Wraps any framework, MCP-native. (Python, third)

Every Python repo in the stack is instantiated from this template. The quality
bars defined here apply to all of them.

## Non-negotiables

- Every public number must be reproducible: no benchmark claim without a
  `make bench` target that regenerates it.
- Boring tech by default: Postgres 16 (incl. pgvector + full-text search) is
  the only storage. Anything else requires an ADR first.
- Narrow and finished beats broad and half-done. Out-of-milestone scope →
  open an issue + ADR first, never code it directly.
- Quickstart must stay under 5 minutes on a clean machine.
- Code, docs, commits: English. Always.

## Engineering rules

- Python 3.12+. `uv` only — never call pip or poetry directly.
- Lint/format: ruff (line length 100). Types: pyright strict — new code ships typed.
- Conventional Commits are REQUIRED (release-please derives versions and
  changelogs from them): `feat | fix | docs | chore | refactor | perf | test | ci`.
  Breaking change: `feat!:` with a `BREAKING CHANGE:` footer.
- Tests: pytest. A feature without tests is not done. Keep the unit suite under 60 s.
- Errors: raise typed exceptions; never bare `except:`; no silent fallbacks.
- Observability: OpenTelemetry spans on every I/O boundary, from day one.
- Public API change → docstrings + mkdocs page updated in the same PR.

## Workflow

- Trunk-based: short-lived branch → PR → squash-merge. CI must be green — never merge red.
- Definition of done: code + tests + docs + conventional commit + benchmarks not regressed.
- Structural decisions get an ADR (use `/adr`). One decision per ADR.
- Before any release: run `/ship` and follow the checklist.
- Rhythm: ship something visible every week; release at most every two weeks.

## Commands

- `uv sync --all-extras` — install everything
- `make check` — ruff + format check + pyright + pytest (run before every PR)
- `make fix` — auto-fix lint + format
- `make docs-serve` — mkdocs live preview
- `make bench` — reproducible benchmark harness (placeholder in the template)
