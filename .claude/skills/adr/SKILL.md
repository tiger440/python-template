---
name: adr
description: Create a new Architecture Decision Record from the repo template. Use when a structural or technology decision needs to be recorded before implementing it.
argument-hint: [decision title]
user-invocable: true
---

Create a new ADR in `adr/`:

1. Find the highest existing number in `adr/` and use the next one (4 digits, zero-padded).
2. Copy `adr/template.md` to `adr/NNNN-<kebab-case-title>.md`. The title comes
   from the argument: $ARGUMENTS — if no argument was given, ask for the title first.
3. Fill in the title, today's date, and status `Proposed`.
4. Interview me briefly — one question at a time: what is the context, which
   options were considered, what do we choose and why. Then write the Context /
   Decision / Options considered / Consequences sections in tight prose.
5. Remind me to reference this ADR in the PR that implements the decision, and
   to flip the status to `Accepted` when merged.
