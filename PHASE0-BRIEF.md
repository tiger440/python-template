# Phase 0 brief — bootstrap the trust-stack Python template

You are Claude Code, executing Phase 0 of a three-project open source portfolio
(read CLAUDE.md first for context and quality bars). Work step by step, verify
each step by running the commands and showing their output, and stop to ask if
a step fails twice. Every commit uses Conventional Commits.

## Inputs / decisions already made

- GitHub owner: `tiger440`  ← replace with the user's GitHub username before starting (ask if still a placeholder)
- Template repo name: `python-template`
- Projects instantiated from it later: `groundcite` (RAG answers engine — instantiated at the end of this brief), `signoff` (agent sign-off layer — later). `cachette` is Rust and will get its own template in Phase 2.
- License: Apache-2.0. Language: English. Default Python: 3.12.

## Step 0 — prerequisites (verify, don't assume)

Check and report each: `git --version` (≥ 2.40), `gh auth status`
(authenticated), `uv --version`, `docker --version`. If gh is not
authenticated, stop and ask the user to run `gh auth login`.

## Step 1 — repo bootstrap

This folder is already the repo root: CLAUDE.md, `.claude/`, and `adr/` are
pre-placed — do NOT overwrite them.

1. `git init -b main`
2. First commit of the pre-placed files: `chore: bootstrap template kit`
3. `gh repo create tiger440/python-template --public --source=. --push --description "Production-grade Python template: uv, ruff, pyright, pytest, release-please, mkdocs, OTel-ready"`

## Step 2 — scaffold (one commit per numbered item)

1. **Package**: uv-managed `pyproject.toml`, src layout, package name
   `trust_template` (placeholder — renamed at instantiation, see Step 5).
   One placeholder module with a small typed, docstringed function.
   Dev dependency group: ruff, pyright, pytest, pytest-cov, mkdocs-material,
   mkdocstrings[python].
2. **Ruff** (in pyproject): line-length 100, rule sets `E,F,W,I,N,UP,B,C4,SIM,RUF`;
   formatting via `ruff format`.
3. **Pyright**: strict mode, `src/` included, pythonVersion 3.12.
4. **Tests**: `tests/` with real tests for the placeholder function;
   coverage configured, `--cov-fail-under=85`.
5. **Makefile**: targets `check` (ruff check + ruff format --check + pyright +
   pytest), `fix`, `test`, `docs-serve`, `bench` (echo "no bench in template"
   placeholder), `rename NEW=<name>` (small script `scripts/rename_package.py`
   that renames the placeholder package + updates pyproject/README).
6. **CI** `.github/workflows/ci.yml`: on push/PR to main; matrix Python
   3.12/3.13; steps: actions/checkout@v4 → astral-sh/setup-uv (with cache
   enabled) → `uv sync --all-extras` → `make check`. Add a concurrency group
   with cancel-in-progress.
7. **Releases** `.github/workflows/release-please.yml`:
   googleapis/release-please-action@v4, release-type `python`, plus
   `.release-please-manifest.json` and `release-please-config.json`.
8. **Docs**: `mkdocs.yml` (material theme, light/dark toggle, repo link),
   `docs/index.md` (what this template provides), `docs/quickstart.md`;
   workflow `.github/workflows/docs.yml` deploying to GitHub Pages on push to
   main (use the official mkdocs-material + Pages actions pattern).
9. **Docker**: multi-stage Dockerfile (uv build stage → slim runtime, non-root
   user, HEALTHCHECK placeholder) + `.dockerignore`.
10. **Community files**: LICENSE (Apache-2.0, year 2026, owner's real name —
    ask if unknown), CONTRIBUTING.md (DCO sign-off, Conventional Commits, how
    to run `make check`), SECURITY.md (report privately via GitHub security
    advisories), `.github/ISSUE_TEMPLATE/bug.yml` + `feature.yml`,
    `.github/pull_request_template.md`, `.editorconfig`, `.gitignore`
    (Python + uv + IDE + OS).
11. **README.md**: what the template is, badges (CI, release, license), the
    quality bars summarized from CLAUDE.md, "Use this template" instructions
    including `make rename NEW=<project>`.

## Step 3 — make it a template + protections

- `gh api -X PATCH repos/tiger440/python-template -f is_template=true`
- Enable GitHub Pages for the docs workflow (via `gh api` if possible,
  otherwise print the exact UI steps and continue).
- Branch protection on main requiring the CI check (via `gh api`; if the
  account plan blocks it, print the UI steps and continue).

## Step 4 — verification checklist (run everything, show output)

- [ ] `uv sync --all-extras` clean
- [ ] `make check` fully green locally
- [ ] Push a `fix:`-typed commit on a branch → PR → CI green → squash-merge
- [ ] release-please opens/updates a release PR on main after that merge
- [ ] `uv run mkdocs build --strict` passes with zero warnings
- [ ] `docker build .` succeeds
- [ ] Repo shows the "Template" badge on GitHub

## Step 5 — instantiate groundcite (do it only if Step 4 is all green)

1. `gh repo create tiger440/groundcite --template tiger440/python-template --public --clone`
2. Inside it: `make rename NEW=groundcite`; README title/description:
   *"groundcite — grounded answers engine: hybrid retrieval, span-level
   citations, document-level permissions, evals built in. Self-hosted."*
3. Update CLAUDE.md's first section to describe groundcite specifically
   (keep the shared quality bars).
4. Copy `ml-companion.md` from the template folder root into groundcite's
   `docs/ml-companion.md` (personal learning companion — it belongs to
   groundcite's docs, not to the template) and commit it there
   (`docs: add ML companion`).
5. Commit `feat: instantiate groundcite from python-template`, push, CI green.

## Step 6 — cleanup

In the template repo: `git rm PHASE0-BRIEF.md README-KIT.md ml-companion.md`
(kit files, not template content — ml-companion.md only after Step 5 copied it
into groundcite), commit `chore: remove bootstrap kit files`, push.

## Guardrails

- Do NOT add application code, extra tools, or extra CI jobs beyond this spec —
  the template must stay minimal and fast.
- Time-box: this is one evening of work. If something drags (Pages permissions,
  branch protection on a free plan…), open a TODO issue on the repo and move on.
- Print the Step 4 checklist with ✅/❌ as your final summary.
