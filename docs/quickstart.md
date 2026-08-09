# Quickstart

Target: a working checkout with green checks in under 5 minutes.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs and manages Python itself)
- `git`, `make`
- Docker (optional, only for `docker build`)

## Start a project from the template

```bash
gh repo create <owner>/<project> --template tiger440/python-template --public --clone
cd <project>
make rename NEW=<project>
uv sync --all-extras
make check
```

`make rename` moves `src/trust_template` to `src/<project>` and rewrites the
placeholder name in `pyproject.toml`, the tests and the docs.

## Daily loop

```bash
make fix     # auto-fix lint and formatting
make test    # pytest with coverage
make check   # everything CI runs, locally
```

Open a short-lived branch, commit with
[Conventional Commits](https://www.conventionalcommits.org/), push, let CI go
green, then squash-merge. `release-please` opens a release PR that bumps the
version and writes the changelog from those commit messages.

## Docs

```bash
make docs-serve    # live preview on http://127.0.0.1:8000
make docs-build    # strict build, exactly what CI publishes
```

## Container

```bash
docker build -t <project> .
docker run --rm <project>
```
