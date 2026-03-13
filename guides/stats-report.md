# Stats Report

Read and summarize the stats log when the user asks for a usage report or token savings summary.

## Log file location

```
~/.claude/skills/codebase-indexer/stats/runs.jsonl
```

## How to read it

Use the Read tool on `stats/runs.jsonl`. Each line is a JSON object — parse them individually.

If the file does not exist, tell the user: "No runs logged yet. Stats are recorded after each codebase-indexer invocation."

## Report format

Present the following summary:

### Overall
- Total runs logged
- Breakdown by mode (full / supplement / update)
- Total estimated tokens saved across all runs
- Date range (first run → latest run)

### By project
List each unique project with:
- Number of runs
- Modes used
- Tokens saved

### Trend
If there are 5+ runs, note whether supplement or update mode is being used more over time (indicates the index is being maintained vs rebuilt).

## Example output

```
📊 Codebase Indexer Stats

Total runs: 8  (2026-02-06 → 2026-03-13)
Modes: full ×1, supplement ×4, update ×3
Estimated tokens saved: ~224,000

By project:
  event-mapper-v2    supplement ×1, update ×2   → ~65k tokens saved
  payroll-app        full ×1, update ×1          → ~12k tokens saved
  bonarda-frontend   supplement ×3               → ~123k tokens saved

Trend: supplement mode dominant — index is being reused well ✓
```

## Trigger phrases

Respond to: "show stats", "codebase-indexer stats", "how many tokens saved", "indexer report"
