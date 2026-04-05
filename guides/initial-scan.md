# Phase 1 — Initial Indexing

Follow these steps in order. Read templates from `templates/` when generating each doc file.

## Step 0: Check for Existing CLAUDE.md (Dedup Gate)

Read `CLAUDE.md` if it exists. Ask yourself: does it already document architecture, directory structure, key abstractions, state management, routing, and conventions?

**If yes (comprehensive CLAUDE.md) → Supplement Mode:**
- Skip generating `docs/architecture.md` and `docs/implementation.md` — they would duplicate what CLAUDE.md already covers and create two sources of truth that will drift.
- Only generate: `docs/patterns.md`, `docs/decisions.md`, `docs/changelog.md`
- Tell the user: "CLAUDE.md already covers architecture and implementation. Generating only gap docs: patterns, decisions, changelog."
- Jump to Step 3 (generating only the 3 gap files), then continue from Step 4.

**If no CLAUDE.md, or it's minimal → Full Mode:**
- Proceed with all steps below and generate all 5 docs.

---

## Step 1: Detect Project Type

Check for project manifests (use Glob/Read):

| Manifest | Stack |
|----------|-------|
| `package.json` | Node.js / JavaScript / TypeScript |
| `pom.xml` | Maven / Java |
| `build.gradle` / `build.gradle.kts` | Gradle / Java / Kotlin |
| `go.mod` | Go |
| `requirements.txt` / `pyproject.toml` / `setup.py` | Python |
| `Cargo.toml` | Rust |
| `*.csproj` / `*.sln` | .NET / C# |
| `composer.json` | PHP |

Multiple manifests = polyglot/monorepo — note all detected stacks.

## Step 2: Scan the Codebase

Use **Glob** and **Grep** (not Bash find/ls):

| What to find | How |
|---|---|
| Directory structure (3 levels max) | `Glob **/*` then collapse paths |
| Entry points | `Grep` for `main`, `app`, `index`, `server`, `Application` |
| Key abstractions | `Grep` for `class`, `interface`, `export`, `func`, `def` |
| Config files | `Glob` for `*.env*`, `*.config.*`, `application.yml`, `application.properties` |
| External deps | Read manifest + lockfile (`package-lock.json`, `go.sum`, `pom.xml` deps) |
| Routing / API | `Grep` for `@GetMapping`, `router.get`, `app.get`, `path=` |
| Test files | `Glob` for `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**`, `**/test/**` |

**Test Discovery Matching Priority:**

When mapping source modules to test files, use this priority ladder (stop at first match):

1. **Graph query** — if graph is available, call `query_graph_tool(pattern="tests_for", target=<function_name>)` for each key function
2. **Exact name match** — `auth.ts` → `auth.test.ts` or `auth.spec.ts`
3. **Substring match** — target name contained in test filename (e.g., `UserService.ts` → `user.test.ts`)
4. **Import scan** — grep test files for imports of the source file path (source → test)
5. **Fallback** — mark as "`— no test found`"

> **Import scan (same mechanism, two directions):** In initial scan Step 4, Claude greps test files for imports of the source file path (source → test). In update mode, Claude reads the changed test file's imports to identify which source modules it covers (test → source). Same signal, opposite traversal direction.

**Exclude:** `node_modules`, `.git`, `build/`, `dist/`, `target/`, `__pycache__`

Use patterns like `**/*.{ts,js,go,java,py,rs}` to limit scan depth.

## Step 3: Generate Doc Files

Write all five files under `docs/` in the project root:

1. Read `templates/architecture.md` → write `docs/architecture.md`
2. Read `templates/implementation.md` → write `docs/implementation.md`
3. Read `templates/patterns.md` → write `docs/patterns.md`
4. Read `templates/decisions.md` → write `docs/decisions.md`
5. Read `templates/changelog.md` → write `docs/changelog.md`

**When generating `implementation.md`:**
- Populate the ## Test Coverage table using the test discovery results from Step 2
- Map each key function/module found in the scan to its test file using the matching priority
- Mark unmapped modules with "`— no test found`"

Do not invent information — if something cannot be determined from the scan, say so explicitly.

## Step 4: Update .gitignore

Read `guides/gitignore-rules.md` and follow it.

## Step 5: Install Auto-Update Rules in CLAUDE.md

This is critical — it makes future doc updates automatic without re-invoking the skill.

1. Read `templates/claude-md-rules.md` to get the rules block.
2. Check if a `CLAUDE.md` exists in the project root.
   - If it exists: read it. If it already contains "Codebase Index" section, skip. Otherwise **append** the rules block to the end.
   - If it does not exist: **create** `CLAUDE.md` with the rules block.
3. Never duplicate — always check before writing.

After this step, Claude will automatically read docs at session start and update them after every feature/bugfix — no manual skill invocation needed.

## Step 6: Report

Tell the user:
- Which project type was detected
- Which files were created
- That CLAUDE.md now has auto-update rules installed
- One sentence summary (e.g., "Spring Boot REST API with 4 service modules and PostgreSQL.")

## Step 7: Log Stats

Read `guides/stats-logging.md` and append one entry to `stats/runs.jsonl`, then output the inline savings card.

- `mode`: `"full"` if all 5 docs were generated, `"supplement"` if only 3 gap docs were generated
- `docs_generated`: count of files actually written this run
- `docs_skipped`: 2 if supplement mode, 0 if full mode
- `project_files`: approximate source file count from Step 2 scan (exclude node_modules, dist, etc.)
- `tokens_saved_this_run`: `0` for full, `6000` for supplement
- `tokens_saved_future_est`: use the project_files scale table in stats-logging.md for full; `35000` for supplement
- `cost_saved_est_usd`: `(tokens_saved_this_run + tokens_saved_future_est) / 1_000_000 * 3.0`
- `graph_available`: `true` if `.code-review-graph/graph.db` was present
