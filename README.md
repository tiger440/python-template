# python-template

[![CI](https://github.com/tiger440/python-template/actions/workflows/ci.yml/badge.svg)](https://github.com/tiger440/python-template/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/tiger440/python-template?display_name=tag&sort=semver)](https://github.com/tiger440/python-template/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

The shared Python template for **the trust stack** — self-hostable,
production-grade open source pieces. Every Python repo in the stack
(`groundcite`, `signoff`) is instantiated from here, so the quality bars live
in one place.

## What you get

- **uv**-managed project, `src/` layout, Python 3.12 / 3.13
- **ruff** lint + format (line length 100)
- **pyright** in strict mode
- **pytest** with coverage gated at 85%
- **CI** on push and PR, matrix 3.12/3.13, cancel-in-progress concurrency
- **release-please** for versions and changelogs from Conventional Commits
- **mkdocs-material** docs deployed to GitHub Pages
- Multi-stage **Dockerfile** (uv build stage → slim non-root runtime)
- Community files: Apache-2.0, CONTRIBUTING (DCO), SECURITY, issue/PR templates

## Quality bars

- Every public number is reproducible: no benchmark claim without `make bench`.
- Boring tech by default: Postgres 16 is the only storage. Anything else needs an ADR.
- Narrow and finished beats broad and half-done.
- Quickstart stays under 5 minutes on a clean machine.
- Code, docs and commits are in English, always.
- Conventional Commits are required; `make check` must be green before every PR.
- New code ships typed, tested and documented in the same PR.

See [CLAUDE.md](CLAUDE.md) for the full engineering rules.

## Use this template

```bash
gh repo create <owner>/<project> --template tiger440/python-template --public --clone
cd <project>
make rename NEW=<project>
uv sync --all-extras
make check
```

`make rename` renames the placeholder package `trust_template` to your project
name and updates `pyproject.toml`, the tests, the docs and this README.

## Commands

| Command | What it does |
|---|---|
| `uv sync --all-extras` | install everything |
| `make check` | ruff check + ruff format --check + pyright + pytest |
| `make fix` | auto-fix lint and formatting |
| `make test` | pytest with coverage |
| `make docs-serve` | mkdocs live preview |
| `make bench` | reproducible benchmark harness (placeholder here) |
| `make rename NEW=<name>` | rename the placeholder package |

## License

Apache-2.0 — see [LICENSE](LICENSE).
