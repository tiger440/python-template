---
name: ship
description: Pre-release checklist for cutting a release of this repo. Use before merging a release-please PR or announcing a new version.
user-invocable: true
---

Run the full pre-release checklist and report a pass/fail table at the end:

1. `make check` — lint, format, types, tests all green.
2. `make bench` if this repo has a real bench harness — compare against the
   last published numbers and flag any regression larger than 5 %.
3. README quickstart: follow it literally (fresh temp dir); confirm it works
   in under 5 minutes and that every command still exists.
4. Docs build: `uv run mkdocs build --strict` — zero warnings.
5. Changelog: read the release-please PR body; confirm it reads well and no
   WIP/fixup commits leaked into it.
6. Version consistency: pyproject version matches the release-please manifest.
7. Only after every item passes: tell me it is safe to merge the release PR.
   Never create or push tags manually — release-please owns tagging.
