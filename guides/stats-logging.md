# Stats Logging

After every successful run (any mode), append one entry to the stats log and output an inline savings card to the user.

## Log file location

```
~/.claude/skills/codebase-indexer/stats/runs.jsonl
```

Create the file if it does not exist. Never overwrite — always append.

---

## Entry format

One JSON object per line (JSONL). Fields:

| Field | Type | Description |
|---|---|---|
| `date` | string | ISO date of the run, e.g. `"2026-03-13"` |
| `project` | string | Basename of the working directory, e.g. `"event-mapper-v2"` |
| `mode` | string | `"full"`, `"supplement"`, or `"update"` |
| `docs_generated` | number | Count of doc files written this run |
| `docs_skipped` | number | Count of doc files skipped (2 for supplement, 0 otherwise) |
| `project_files` | number | Approximate number of source files in the project (from scan or Glob count — exclude node_modules, dist, etc.) |
| `tokens_saved_this_run` | number | Tokens saved during this specific run (index time savings) |
| `tokens_saved_future_est` | number | Tokens saved per future session by having docs available (recurring benefit) |
| `cost_saved_est_usd` | number | Dollar estimate: `(tokens_saved_this_run + tokens_saved_future_est) / 1_000_000 * 3.0` (Sonnet input rate) |
| `graph_available` | boolean | `true` if `.code-review-graph/graph.db` was present and used |

---

## Token savings estimates

### `full` mode
- `tokens_saved_this_run`: `0` — full scan is the baseline cost, no savings on first run
- `tokens_saved_future_est`: scale by project size:
  | `project_files` | `tokens_saved_future_est` | Rationale |
  |---|---|---|
  | < 50 | `8000` | Small project — session scan would be light anyway |
  | 50–200 | `20000` | Medium project — scan saves a meaningful chunk |
  | 200–1000 | `45000` | Large project — docs replace a substantial scan |
  | 1000+ | `90000` | Very large / monorepo — docs replace a very expensive scan |

### `supplement` mode
- `tokens_saved_this_run`: `6000` — ~2 fewer large docs generated at index time
- `tokens_saved_future_est`: `35000` — 2 large doc files never need to be loaded; CLAUDE.md already covers them

### `update` mode
- `tokens_saved_this_run`: scale by graph availability:
  | `graph_available` | `tokens_saved_this_run` | Rationale |
  |---|---|---|
  | false | `12000` | Targeted re-scan vs full codebase rescan |
  | true | `17000` | +5k from graph replacing Glob/Grep neighborhood scan |
- `tokens_saved_future_est`: `0` — update runs maintain existing savings, not create new ones

### Cost estimate formula
```
cost_saved_est_usd = round((tokens_saved_this_run + tokens_saved_future_est) / 1_000_000 * 3.0, 4)
```
Uses Sonnet input token rate (~$3/1M). Round to 4 decimal places.

---

## Example entries

```json
{"date":"2026-03-14","project":"fastapi-backend","mode":"full","docs_generated":5,"docs_skipped":0,"project_files":312,"tokens_saved_this_run":0,"tokens_saved_future_est":45000,"cost_saved_est_usd":0.135,"graph_available":false}
{"date":"2026-03-14","project":"fastapi-backend","mode":"update","docs_generated":2,"docs_skipped":0,"project_files":312,"tokens_saved_this_run":17000,"tokens_saved_future_est":0,"cost_saved_est_usd":0.051,"graph_available":true}
{"date":"2026-03-15","project":"event-mapper-v2","mode":"supplement","docs_generated":3,"docs_skipped":2,"project_files":88,"tokens_saved_this_run":6000,"tokens_saved_future_est":35000,"cost_saved_est_usd":0.123,"graph_available":false}
```

---

## How to append

1. Read the file first (may not exist — that's fine).
2. Append the new JSON line at the end.
3. If the file does not exist, create it with the new entry as the first line.

---

## Inline savings card (required after every run)

After logging, output a `concord-index-summary` JSON block. The Concord UI renders this as a formatted key-value table automatically. Do NOT output a plain-text card — the structured block replaces it.

Output exactly this (fill in values, no extra text around the block):

\`\`\`concord-index-summary
{"project":"<project>","mode":"<mode>","project_files":<project_files>,"docs_generated":<docs_generated>,"tokens_saved_this_run":<tokens_saved_this_run>,"tokens_saved_future_est":<tokens_saved_future_est>,"cost_saved_est_usd":<cost_saved_est_usd>}
\`\`\`

For `full` mode, set `tokens_saved_this_run` to `0` (baseline — future sessions benefit).
For `update` mode, set `tokens_saved_future_est` to `0`.

Example for a full-mode run on a medium project:

\`\`\`concord-index-summary
{"project":"concord","mode":"full","project_files":87,"docs_generated":5,"tokens_saved_this_run":0,"tokens_saved_future_est":20000,"cost_saved_est_usd":0.06}
\`\`\`

---

## What NOT to log

- Runs that failed or were abandoned mid-way
- Dry runs or planning-only sessions where no files were written
