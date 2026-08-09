---
name: deepdive
description: Explain a component of this repo at ML-engineer mathematical depth — derive the math, map each formula to the actual code, list failure modes, then quiz the user. Use when the user wants to deeply understand something just built or about to be built.
argument-hint: [component or concept]
user-invocable: true
---

The user is learning ML engineering through this project. Never hand-wave; mark
every empirical constant as empirical; use LaTeX notation for all math.

1. Identify the target: $ARGUMENTS if given, otherwise the component most
   recently built or modified (check `git log` / `git diff`).
2. Read the ACTUAL code involved before explaining anything.
3. Explain in five layers:
   a. **Role in the funnel** — which probability of the RAG error funnel this
      component moves (P(retrieved), P(used), P(faithful)…).
   b. **The exact math** — definitions, formulas, and a compact derivation of
      every non-obvious step.
   c. **Formula → code** — point to the exact lines implementing each term;
      flag any place where the code deviates from the canonical formula, and why.
   d. **Failure modes** — which inputs break it, which metric detects it, what
      the early signal looks like in an eval report.
   e. **The design space** — what we could swap it for, and what would change.
4. If `docs/ml-companion.md` exists, reference the matching chapter and stay
   consistent with its notation.
5. Finish with 3 questions to check understanding, hardest last. Wait for the
   answers, then correct them precisely — a wrong answer gets a precise
   correction, not encouragement.
6. If the discussion reveals a gap or an error in `docs/ml-companion.md`,
   propose a one-paragraph amendment to it.
