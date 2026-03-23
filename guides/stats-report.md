# Stats Report

Read and summarize the stats log when the user asks for a usage report or token savings summary.

## Log file location

```
~/.claude/skills/codebase-indexer/stats/runs.jsonl
```

## How to read it

Use the Read tool on `stats/runs.jsonl`. Each line is a JSON object — parse them individually.

If the file does not exist or is empty, tell the user:
> "No runs logged yet. Stats are recorded automatically after each codebase-indexer run."

---

## Calculations

Before rendering the report, compute:

| Value | How |
|---|---|
| `total_runs` | Count of all entries |
| `total_tokens_saved` | Sum of `tokens_saved_this_run` + `tokens_saved_future_est` across all entries (use `tokens_saved_est` for legacy entries that predate the schema change) |
| `total_cost_saved` | Sum of `cost_saved_est_usd` across all entries (or compute from `total_tokens_saved / 1_000_000 * 3.0` for legacy entries) |
| `mode_counts` | Count of entries per mode |
| `graph_runs` | Count of entries where `graph_available = true` |
| `projects` | Unique project names |
| `date_range` | Earliest and latest `date` fields |
| `update_ratio` | `update` runs / total runs (health indicator) |
| `avg_files` | Average `project_files` across entries that have it |

---

## Report format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Codebase Indexer · Token Intelligence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Runs      <total_runs> runs across <project_count> projects
  Period    <first_date> → <latest_date>

  SAVINGS SUMMARY
  ┌─────────────────────────────────────────────┐
  │  Tokens saved (all time)  ~<total_tokens>   │
  │  Estimated cost saved     ~$<total_cost>    │
  │  Avg per run              ~<avg_tokens>/run │
  └─────────────────────────────────────────────┘

  BREAKDOWN BY MODE
  full       ×<n>   → <tokens> tokens  (~$<cost>)
  supplement ×<n>   → <tokens> tokens  (~$<cost>)
  update     ×<n>   → <tokens> tokens  (~$<cost>)

  BY PROJECT
  <project>   <mode summary>   ~<tokens> tokens  (~$<cost>)
  ...

  INDEX HEALTH
  <health assessment — see below>

  GRAPH BOOST
  <graph section — see below>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Index Health assessment

Evaluate `update_ratio` and provide a specific, actionable line:

| Condition | Output |
|---|---|
| No update runs at all | `No update runs yet. Run "update docs" after your next feature to start compounding savings.` |
| update_ratio < 0.2 | `Mostly first-time indexes. The index is being created but not maintained — savings are one-time. Run update mode after features/bugfixes to compound them.` |
| update_ratio 0.2–0.5 | `Index is being maintained. Update runs are building up recurring savings. Good cadence.` |
| update_ratio > 0.5 | `Strong maintenance cadence. The index is being actively reused — this is where the compounding savings come from.` |

Also flag: if any project has a `full` run but no subsequent `update` run, list those projects specifically:
> "Projects indexed but never updated: <list> — run update mode on these to start saving."

---

## Graph Boost section

| Condition | Output |
|---|---|
| `graph_runs = 0` | `No runs with code-review-graph yet. Install it to save an extra ~5k tokens per update run via blast-radius analysis.` |
| `graph_runs > 0` | `Graph-powered runs: <graph_runs>/<total_runs>. Graph runs saved ~<extra> additional tokens vs non-graph runs.` |

For graph extra savings: `graph_runs * 5000` tokens above the non-graph update baseline.

---

## Number formatting

- Tokens: format with k suffix (e.g. `41,000` → `41k`, `321,000` → `321k`)
- Costs: always show 2 decimal places (e.g. `$0.96`)
- If total savings is 0 (all `full` mode, no update/supplement): show future savings instead with a note:
  > "All runs are first-time indexes. No in-run savings yet, but ~<sum of tokens_saved_future_est>k tokens will be saved across future sessions on these projects."

---

## Example output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Codebase Indexer · Token Intelligence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Runs      9 runs across 8 projects
  Period    2026-03-13 → 2026-03-22

  SAVINGS SUMMARY
  ┌─────────────────────────────────────────────┐
  │  Tokens saved (all time)  ~388k             │
  │  Estimated cost saved     ~$1.16            │
  │  Avg per run              ~43k/run          │
  └─────────────────────────────────────────────┘

  BREAKDOWN BY MODE
  full       ×7   → 0 this run  (+315k future)  (~$0.95)
  supplement ×1   → 41k         (+35k future)   (~$0.23)
  update     ×1   → 17k                         (~$0.05)

  BY PROJECT
  event-mapper-v2     supplement + update   ~93k   (~$0.28)
  devflow             full                  ~45k   (~$0.14)
  mac-download-mgr    full                  ~45k   (~$0.14)
  dstv-channels       full                  ~20k   (~$0.06)
  claude-token-disp   full                  ~8k    (~$0.02)
  payroll-app         full                  ~45k   (~$0.14)
  ios                 full                  ~90k   (~$0.27)
  concord             full                  ~45k   (~$0.14)

  INDEX HEALTH
  7 projects indexed but never updated: devflow, mac-download-manager,
  dstv-channels-lineup, claude-token-display, payroll-app, ios, concord
  → Run "update docs" after your next feature on these to start compounding savings.

  GRAPH BOOST
  No runs with code-review-graph yet. Install it to save an extra ~5k tokens
  per update run via blast-radius analysis.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Trigger phrases

Respond to: "show stats", "codebase-indexer stats", "how many tokens saved", "indexer report", "token savings", "show me the stats"
