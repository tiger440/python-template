# 0001 — Record architecture decisions

- Date: 2026-08-09
- Status: Accepted

## Context

This template seeds a multi-repo, multi-month portfolio (groundcite, signoff,
and the Rust sibling cachette). Decisions made early — storage, protocols,
naming, defaults — will be questioned later, by contributors and by the author.
Without a written trail, every debate restarts from zero.

## Decision

We record every structural decision as an ADR in `adr/`, using `template.md`,
numbered sequentially. One decision per file. PRs implementing a decision link
to its ADR.

## Options considered

- No records — fast today, amnesia in three months. Rejected.
- Heavy RFC process — overkill for a solo-maintainer project. Rejected.
- Lightweight ADRs (Nygard style) — minutes to write, permanent value. Chosen.

## Consequences

Slightly more ceremony before big changes; in exchange, the repo history
explains itself — which is exactly the signal a production-grade project sends.
