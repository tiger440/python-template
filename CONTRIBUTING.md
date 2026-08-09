# Contributing

Thanks for taking the time. This repo is part of the trust stack; the bars
below are the same everywhere in it.

## Developer Certificate of Origin (DCO)

Every commit must be signed off. By signing off you certify the
[DCO 1.1](https://developercertificate.org/).

```bash
git commit -s -m "fix: correct the offset of the last span"
```

This appends `Signed-off-by: Your Name <you@example.com>` to the message. Set
`user.name` and `user.email` in git first. To fix a missing sign-off on the
last commit: `git commit --amend -s --no-edit`.

## Conventional Commits

Commit messages are required to follow
[Conventional Commits](https://www.conventionalcommits.org/) — `release-please`
derives versions and the changelog from them.

Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `perf`, `test`, `ci`.

A breaking change is `feat!:` (or any type with `!`) plus a `BREAKING CHANGE:`
footer.

```
feat(retrieval): add reciprocal rank fusion

fix: reject chunks whose char offsets fall outside the document

feat!: return spans instead of chunk ids

BREAKING CHANGE: `search()` now returns `Span` objects.
```

## Local checks

```bash
uv sync --all-extras
make check     # ruff check + ruff format --check + pyright + pytest
make fix       # auto-fix lint and formatting
```

`make check` is exactly what CI runs. Run it before opening a PR — never push a
red branch and wait for CI to tell you.

## Workflow

1. Short-lived branch off `main`.
2. Code + tests + docs in the same PR. A feature without tests is not done.
3. `make check` green locally, then push and open a PR.
4. CI green, then squash-merge. Never merge red.

New code ships typed (`pyright` strict) and documented (docstrings, and an
mkdocs page for any public API change).

## Structural decisions

One decision per Architecture Decision Record, in `adr/`, using
`adr/template.md`. Anything that changes storage, a dependency of substance, or
a public contract gets an ADR before the code.

## Reporting security issues

Do not open a public issue — see [SECURITY.md](SECURITY.md).
