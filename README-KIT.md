# Kit Phase 0 — mode d'emploi (à lire par toi, pas par Claude Code)

Ce kit contient tout ce qu'il faut pour exécuter la Phase 0 de la roadmap avec
Claude Code sur ta machine : la mémoire projet (`CLAUDE.md`), les réglages et
skills Claude Code (`.claude/`), les ADR de départ (`adr/`), et le brief
exécutable (`PHASE0-BRIEF.md`).

## Noms retenus (tous vérifiés disponibles le 09/08/2026)

| Projet | Nom | Registre vérifié |
|---|---|---|
| RAG — grounded answers engine | **groundcite** | PyPI libre |
| Cache sémantique (Rust) | **cachette** | crates.io libre |
| Sign-off agents (HITL) | **signoff** | PyPI libre |

Alternatives vérifiées libres si tu changes d'avis avant de créer les repos :
`citeproof`, `truecite`, `answerable`, `groundspan`, `citespan` (RAG) ;
`vericache`, `provencache`, `truecache` (cache) ; `holdpoint` (agents).

## Prérequis sur ta machine

- git ≥ 2.40, **gh** (GitHub CLI) authentifié (`gh auth login`), **uv**, Docker
- **Claude Code** installé et connecté (docs officielles : code.claude.com)

## Étapes (10 minutes de setup, puis Claude Code déroule)

1. Crée un dossier vide `python-template/` là où tu ranges tes projets.
2. Décompresse le kit **dedans** — `CLAUDE.md`, `.claude/`, `adr/`,
   `PHASE0-BRIEF.md`, `README-KIT.md` doivent être à la racine du dossier.
3. Ouvre `PHASE0-BRIEF.md` et remplace `<OWNER>` par ton username GitHub
   (2 secondes : `sed -i 's/<OWNER>/tonusername/g' PHASE0-BRIEF.md`).
4. Lance `claude` dans le dossier.
5. Colle le prompt de kickoff ci-dessous.
6. Laisse dérouler — Claude Code te demandera confirmation pour les `git push`,
   `gh` et `docker` (c'est voulu, voir `.claude/settings.json`).
7. À la fin, exige la checklist ✅/❌ de l'étape 4 du brief. Tout doit être vert.

## Prompt de kickoff (à coller tel quel)

```
Read PHASE0-BRIEF.md and CLAUDE.md, then execute the brief end to end.
Work step by step: run the commands, show the outputs, and verify each
step before moving to the next. Ask me before anything destructive or
anything not covered by the brief. Finish by printing the Step 4
verification checklist with a pass/fail mark for each item.
```

## Fourni dans `.claude/`

- `settings.json` — permissions raisonnables : uv/make/git locaux autorisés,
  `git push`, `gh` et `docker` en confirmation.
- `/adr` — crée un Architecture Decision Record numéroté depuis le template.
- `/ship` — checklist de pré-release (à utiliser dès la première v0.1 de groundcite).
- `/deepdive <composant>` — explication niveau ML engineer du composant visé :
  maths dérivées, mapping formule → lignes de code réelles, modes d'échec, puis
  quiz. À utiliser après chaque brique construite, en tandem avec
  `ml-companion.md` (fourni à la racine du kit, copié dans `docs/` de
  groundcite à l'instanciation).

## Conseils Claude Code pour la suite

- Utilise le **plan mode** pour chaque gros morceau de la Phase 1 (chunking,
  hybride, citations…) : tu valides le plan avant qu'il code.
- `/install-github-app` (optionnel) active @claude sur tes PRs GitHub — utile à
  partir de la Phase 1 pour la revue de code.
- Le fichier `CLAUDE.md` est ta mémoire projet : fais-la évoluer, c'est elle qui
  maintient le niveau d'exigence d'une session à l'autre.

## Et ensuite ?

Fin de Phase 0 = template en ligne + repo **groundcite** instancié, CI verte.
Lundi, on attaque la S2 de la roadmap : ingestion Docling + pgvector + premier
`/query` bout en bout. Reviens me voir pour préparer le brief de la S2.
