# Phase 2 — Update Mode

Follow these steps after a feature or bugfix. Read templates from `templates/` when updating doc files.

## Step 1: Read Existing Docs

Use **Read** on each file in `docs/`. Understand what is already documented.

## Step 2: Identify What Changed

Prefer the merge-base form to correctly handle merge commits and squash merges:

```bash
git diff --name-only $(git merge-base HEAD HEAD~1)..HEAD
```

Fallback if merge-base fails (simple linear history):

```bash
git diff HEAD~1 --name-only
```

> **Note:** `HEAD~1` breaks on merge commits (returns the second parent diff) and on squash merges (shows the entire branch as one commit). The merge-base form handles both cases correctly.

Note which modules/packages were touched.

## Step 3: Identify Affected Files and Blast Radius

**If `graph_available = true` (`.code-review-graph/graph.db` exists):**

Call the MCP tools instead of Glob/Grep:
1. `get_impact_radius_tool()` — returns the exact set of nodes and files affected by the changes (callers, dependents, inheritors, tests). No manual file scanning needed.
2. `get_review_context_tool()` — returns source snippets for changed areas plus structural review guidance.

This replaces the entire Glob/Grep neighborhood scan and costs ~300 tokens vs. 2,000–8,000 for manual scanning.

**If `graph_available = false`:**

Use Glob + Grep on the changed files and their direct neighbors (same package/directory). Do **not** re-scan the whole project.

## Step 4: Update Relevant Doc Files

| Changed area | Update these files |
|---|---|
| New module or package | `architecture.md`, `implementation.md` |
| New class / function / endpoint | `implementation.md` (run matching priority, then add to ## Test Coverage with test file or "— no test found") |
| Renamed files or folders | `architecture.md`, `patterns.md` |
| New dependency added | `architecture.md` |
| New naming or code pattern | `patterns.md` |
| Architectural decision | `decisions.md` (see step 5) |
| Test file added or removed | Re-map ## Test Coverage in `implementation.md` (see below) |

**Test file added or removed:**

When a test file is added, removed, or modified:
1. Read the changed test file
2. Extract `describe`/`it` block names and import statements
3. Match those against source modules:
   - Import scan: read test file imports to identify which source modules it covers (test → source)
   - Describe/it block names: grep for function/class names that match source module symbols
4. Add new rows for newly covered functions, remove rows pointing to deleted test files

> **Import scan (same mechanism, two directions):** In initial scan Step 4, Claude greps test files for imports of the source file path (source → test). In update mode, Claude reads the changed test file's imports to identify which source modules it covers (test → source). Same signal, opposite traversal direction.

Apply targeted edits — do not rewrite unaffected sections.

## Step 5: Decisions Gate

Ask: **"Did this change involve making or reversing an architectural decision?"**

| Change | Update decisions.md? |
|---|---|
| Added new API endpoint | No |
| Switched REST to GraphQL | **Yes** |
| Fixed a null pointer bug | No |
| Replaced ORM after performance issues | **Yes** — e.g., "chose JOOQ over Hibernate due to N+1 problems" |
| Added a new service module | Only if the structural choice was deliberate |

If yes — read `templates/decisions.md` for the ADR format, then append entry.
If no — skip `decisions.md`.

## Step 6: Append Changelog Entry

Always append a new dated entry to `docs/changelog.md`:

```markdown
## YYYY-MM-DD — [brief description]
- What changed
- Which modules were affected
```

## Step 7: Log Stats

Read `guides/stats-logging.md` and append one entry to `stats/runs.jsonl`, then output the inline savings card.

- `mode`: `"update"`
- `docs_generated`: count of doc files that were actually edited this run
- `docs_skipped`: 0
- `project_files`: reuse the approximate count from the existing `docs/` files (e.g. from `architecture.md` or `implementation.md` scope notes), or from the original scan — do not re-count the whole project
- `tokens_saved_this_run`: `12000` if `graph_available = false`; `17000` if `graph_available = true`
- `tokens_saved_future_est`: `0` — update runs maintain existing savings, they do not create new recurring ones
- `cost_saved_est_usd`: `tokens_saved_this_run / 1_000_000 * 3.0` (future_est is 0 so omit it from the sum)
- `graph_available`: `true` if `.code-review-graph/graph.db` was present and used, `false` otherwise
