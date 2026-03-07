# codebase-indexer

A Claude Code skill that scans a project once and generates a living `/docs/` folder — so Claude reads the index instead of re-scanning the whole codebase every session.

## What it does

**First run:** Scans your project and writes five doc files:

| File | Purpose |
|---|---|
| `docs/architecture.md` | Structure, module map, data flow, external dependencies |
| `docs/implementation.md` | Per-module breakdown — entry points, key classes/functions |
| `docs/patterns.md` | Naming conventions, folder conventions, recurring idioms |
| `docs/decisions.md` | ADRs — *why* things are the way they are |
| `docs/changelog.md` | Dated log of what changed and which modules were affected |

**After each feature/bugfix:** Updates only the affected sections and appends a changelog entry. Asks whether an architectural decision was made before touching `decisions.md`.

`docs/` is added to `.gitignore` automatically — these are session artifacts, not committed documentation.

## Install

Copy `SKILL.md` into your Claude Code skills directory:

```bash
mkdir -p ~/.claude/skills/codebase-indexer
cp SKILL.md ~/.claude/skills/codebase-indexer/SKILL.md
```

Claude Code will discover the skill automatically on next launch.

## Usage

Open any existing project in Claude Code and the skill triggers automatically when Claude detects `docs/` doesn't exist yet, or when you say:

- **"index this codebase"** — runs full initial scan
- **"update docs"** / **"re-index"** — updates from recent changes only

## Supported project types

Detects and handles: Node.js, Java (Maven/Gradle), Go, Python, Rust, .NET, PHP — and polyglot/monorepo setups.

## How it works

```
First session                     Each subsequent session
─────────────────                 ──────────────────────
Glob + Grep scan         →        Read docs/architecture.md
Generate 5 doc files     →        Read docs/implementation.md
Add docs/ to .gitignore  →        Done — no re-scan needed
```

After a feature or fix:
```
git diff HEAD~1 --name-only  →  Re-scan only changed files
Update affected doc sections  →  Append changelog entry
Ask about architectural decision  →  Update decisions.md if yes
```
