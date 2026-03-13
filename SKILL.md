---
name: codebase-indexer
description: Use when opening an existing codebase for the first time, or after completing a feature or bugfix — generates and maintains /docs/ index files so Claude does not re-scan the whole codebase each session.
---

# Codebase Indexer

Scan a project once, write five lean doc files to `docs/`, and read them every future session instead of re-scanning the whole codebase. After each feature or bugfix, update only what changed.

## Mode Detection

```
docs/ exists?
  ├─ yes → Signal present?
  │          ├─ yes → Phase 2: Update Mode
  │          └─ no  → Ask: "Re-index from scratch, or update from recent changes?"
  └─ no  → Comprehensive CLAUDE.md exists?
             ├─ yes → Supplement Mode (gap docs only)
             └─ no  → Phase 1: Initial Indexing (all 5 docs)
```

**Phase 2 signals:** user says "update docs", "re-index", "update", or just finished a feature/bugfix.

**Comprehensive CLAUDE.md:** A CLAUDE.md that already documents architecture, directory structure, key abstractions, and conventions. Read it and judge — if it covers what `architecture.md` and `implementation.md` would contain, use Supplement Mode.

## Execution

| Mode | Read this guide |
|------|----------------|
| No `docs/`, no comprehensive CLAUDE.md | Read `guides/initial-scan.md` — generate all 5 docs |
| No `docs/`, comprehensive CLAUDE.md exists | Read `guides/initial-scan.md` Step 0 — generate gap docs only (`patterns.md`, `decisions.md`, `changelog.md`) |
| `docs/` exists, update after changes | Read `guides/update-mode.md` and follow it |

Both guides reference templates in `templates/` — read those when generating or updating doc files.

## File Map

```
~/.claude/skills/codebase-indexer/
  SKILL.md                        ← you are here
  guides/
    initial-scan.md               ← Phase 1: full scan steps
    update-mode.md                ← Phase 2: diff-based update steps
    gitignore-rules.md            ← .gitignore handling
  templates/
    architecture.md               ← template for docs/architecture.md
    implementation.md             ← template for docs/implementation.md
    patterns.md                   ← template for docs/patterns.md
    decisions.md                  ← template for docs/decisions.md
    changelog.md                  ← template for docs/changelog.md
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Generating all 5 docs when a comprehensive CLAUDE.md exists | Run Step 0 — supplement mode generates only 3 gap docs |
| Auto-running `git diff` without checking CLAUDE.md policies | Suggest the command to the user; never run autonomously unless project allows it |
| Gitignoring `docs/` without asking the user | Ask: shared (committed) or local-only (gitignored)? |
| Using `git diff HEAD~1` on merge or squash commits | Use `git diff --name-only $(git merge-base HEAD HEAD~1)..HEAD` |
| Re-scanning the full codebase in Update Mode | Scope to changed files and their direct neighbors |
| Duplicating `.gitignore` entry | Always read first, append only if absent |
| Rewriting whole doc files on update | Edit only the sections corresponding to changed modules |
| Adding ADR for every change | Gate on "was this an architectural decision?" — most changes are not |
| Scanning `node_modules`, `target/`, `dist/` | Exclude build artifacts from all globs |
| Inventing details not found in scan | Say "not determinable from scan" rather than guessing |
| Updating docs after every small change | Update at natural checkpoints — before commit, before PR, or when explicitly asked |
