# codebase-indexer

A Claude Code skill that scans a project once and generates a living `/docs/` folder — so Claude reads the index instead of re-scanning the whole codebase every session.

This project borrows the shape of a few strong ideas, especially Composto's AST-first compression mindset and tree-sitter's structured approach to code understanding. The implementation here adapts those ideas natively inside Claude Code rather than depending on Composto or tree-sitter at runtime.

## Acknowledgments

- [Composto](https://github.com/mertcanaltin/composto) — inspiration for tiered signal extraction, context budgeting, and health/security-aware context design.
- [tree-sitter](https://tree-sitter.github.io/tree-sitter/) — parsing model and language-grammar ecosystem that informed the AST-first direction.

## Evolution

- **Initial state:** a one-shot codebase indexer that produced a durable `/docs/` scaffold from a single scan.
- **Next:** auto-update rules were added so Claude could keep the index current without repeated manual runs.
- **Then:** changelog and decision tracking were layered in to preserve context across sessions.
- **Then:** graph-aware blast radius support was added to make update mode more targeted.
- **Now:** a signal-first, AST-inspired workflow (tiered extraction + budget-aware context packing) guides scans and updates while remaining self-contained.

## What it does

**First run:** Scans your project, writes five doc files, and installs auto-update rules in your project's `CLAUDE.md`:

| File | Purpose |
|---|---|
| `docs/architecture.md` | Structure, module map, data flow, external dependencies |
| `docs/implementation.md` | Per-module breakdown — entry points, key classes/functions |
| `docs/patterns.md` | Naming conventions, folder conventions, recurring idioms |
| `docs/decisions.md` | ADRs — *why* things are the way they are |
| `docs/changelog.md` | Dated log of what changed and which modules were affected |

**After the first run, you never invoke the skill again.** The rules in `CLAUDE.md` make Claude automatically read the docs at session start and update them after every feature or bugfix.

On first run, you'll be asked whether `docs/` should be committed (shared with the team) or gitignored (local only).

## Install

```bash
git clone https://github.com/heyEdem/codebase-indexer.git ~/.claude/skills/codebase-indexer
```

Claude Code will discover the skill automatically on next launch.

## Usage

Open any project in Claude Code and say:

- **"index this codebase"** — runs full initial scan

That's it. After the first scan, Claude handles everything automatically via the rules it plants in your project's `CLAUDE.md`.

You can also say **"update docs"** / **"re-index"** if you want to manually trigger an update.

Savings visibility (current project):
- **"/codebase-indexer savings"** — terminal comparison report
- **"/codebase-indexer savings terminal"** — explicit terminal mode
- **"/codebase-indexer savings html"** — generates a timestamped report in `docs/` (`codebase-indexer-savings-YYYYMMDD-HHMMSS.html`)
- After every successful `/codebase-indexer` run, savings are generated automatically by default:
  - terminal comparison shown immediately
  - new timestamped HTML report written to `docs/` (e.g., `codebase-indexer-savings-YYYYMMDD-HHMMSS.html`)

## Supported project types

Detects and handles: Node.js, Java (Maven/Gradle), Go, Python, Rust, .NET, PHP — and polyglot/monorepo setups.

## How it works

```
First run (invoke once)              Every session after (automatic)
───────────────────────              ───────────────────────────────
Scan codebase (signal-first)   →     Claude reads docs/ at session start
Generate 5 doc files           →     No re-scan needed
Install rules in CLAUDE.md     →     Auto-updates docs after changes
Add docs/ to .gitignore        →     Appends changelog entries
```

Optional deterministic helpers (inside this repo):
- `scripts/context_packer.py` — budget-aware L0/L1/L3 context packing
- `scripts/delta_context.py` — L2-style diff summarization for update mode

## Skill structure

```
~/.claude/skills/codebase-indexer/
  SKILL.md                  ← entry point (66 lines)
  guides/
    initial-scan.md         ← Phase 1: full scan steps
    update-mode.md          ← Phase 2: diff-based updates
    signal-first-ir.md      ← AST-inspired signal-first extraction rules
    gitignore-rules.md      ← .gitignore handling
  scripts/
    context_packer.py       ← deterministic context packing helper
    delta_context.py        ← deterministic delta summarization helper
  templates/
    architecture.md         ← template for each doc file
    implementation.md
    patterns.md
    decisions.md
    changelog.md
    claude-md-rules.md      ← rules planted into CLAUDE.md
```

Uses progressive disclosure — Claude only loads the files it needs for the current phase.
