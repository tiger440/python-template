# python-template

The shared Python template for **the trust stack** — self-hostable,
production-grade open source pieces. Every Python repo in the stack is
instantiated from here, so the quality bars are defined once.

## What the template provides

| Area | Tooling |
|---|---|
| Packaging | `uv`, `src/` layout, hatchling, Python 3.12 / 3.13 |
| Lint & format | `ruff` (line length 100, rules `E,F,W,I,N,UP,B,C4,SIM,RUF`) |
| Types | `pyright` in strict mode |
| Tests | `pytest` + `pytest-cov`, coverage gated at 85% |
| CI | GitHub Actions, matrix 3.12/3.13, cancel-in-progress concurrency |
| Releases | `release-please`, versions derived from Conventional Commits |
| Docs | `mkdocs-material` + `mkdocstrings`, deployed to GitHub Pages |
| Container | multi-stage Dockerfile, non-root runtime |
| Community | Apache-2.0, DCO sign-off, security policy, issue and PR templates |

## Quality bars

These apply to every repo instantiated from the template:

- Every public number is reproducible — no benchmark claim without `make bench`.
- Boring tech by default; Postgres 16 is the only storage. Anything else needs an ADR.
- Narrow and finished beats broad and half-done.
- The quickstart stays under 5 minutes on a clean machine.
- Code, docs and commits are in English, always.
- A feature without tests is not done; new code ships typed.
- Trunk-based flow: short-lived branch → PR → squash-merge, CI green.

## API reference

::: trust_template.text
