# Codebase Index Rules

These rules are injected into the project's CLAUDE.md by the codebase-indexer skill. Append them to an existing CLAUDE.md or create a new one.

**Important before injecting:** Read the existing CLAUDE.md for conflicting instructions (e.g., "do not run commands autonomously"). If conflicts exist, adjust the rules block below to fit — never inject rules that contradict the project's existing guidelines.

---

## Rules to inject:

```markdown
## Codebase Index

This project has a living `docs/` folder with patterns, decisions, and changelog files.

### Session Start
- Read `docs/architecture.md` and `docs/implementation.md` if they exist before doing any work.
- These files contain the project map — do not re-scan the codebase from scratch.
- If the project has a comprehensive CLAUDE.md, that takes precedence over doc files for architecture and implementation details.

### During Session
- Before opening any source file, check `docs/` first — if the answer exists in docs, return it without reading source.
- Only fall back to reading source files when docs don't contain what you need.

### Graph-Powered Queries (if code-review-graph is installed)

If `.code-review-graph/graph.db` exists in this project, prefer MCP tools over file scanning:
- `get_impact_radius_tool()` — before doing any Glob/Grep to find what a change affects
- `get_review_context_tool()` — when performing a code review or summarising what changed
- `query_graph_tool(pattern, target)` — to find callers, tests, or dependents of any function
- `semantic_search_nodes_tool(query)` — to find abstractions by concept rather than exact name

Fall back to Grep/Glob only when the graph does not cover what you need (e.g. config files, comments, string literals).

### Updating Docs (run /codebase-indexer or invoke explicitly)

Update docs at natural checkpoints — before committing, before a PR, or when explicitly asked. Do not update after every small change.

To identify what changed, suggest the user run:
```
git diff --name-only $(git merge-base HEAD HEAD~1)..HEAD
```
or share the output with you. Do not run this autonomously unless the project's CLAUDE.md explicitly allows autonomous shell commands.

Once you know what changed, apply targeted edits to the relevant doc files:
- New module/package → update `docs/architecture.md`, `docs/implementation.md` (if they exist)
- New class/function/endpoint → update `docs/implementation.md` (if it exists)
- Renamed files/folders → update `docs/architecture.md`, `docs/patterns.md`
- New dependency → update `docs/architecture.md` (if it exists)
- New naming/code pattern → update `docs/patterns.md`

Then:
1. Ask: "Did this change involve making or reversing an architectural decision?"
   - If yes → append an ADR entry to `docs/decisions.md`
   - If no → skip
2. Append a dated changelog entry to `docs/changelog.md`:
   ```
   ## YYYY-MM-DD — [brief description]
   - What changed
   - Which modules were affected
   ```
```
