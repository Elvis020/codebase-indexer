# Stats Logging

After every successful run (any mode), append one entry to the stats log. This builds a ledger of usage and token savings over time.

## Log file location

```
~/.claude/skills/codebase-indexer/stats/runs.jsonl
```

Create the file if it does not exist. Never overwrite — always append.

## Entry format

One JSON object per line (JSONL). Fields:

| Field | Type | Description |
|---|---|---|
| `date` | string | ISO date of the run, e.g. `"2026-03-13"` |
| `project` | string | Basename of the working directory, e.g. `"event-mapper-v2"` |
| `mode` | string | `"full"`, `"supplement"`, or `"update"` |
| `docs_generated` | number | Count of doc files written this run |
| `docs_skipped` | number | Count of doc files skipped (2 for supplement, 0 otherwise) |
| `tokens_saved_est` | number | Estimated tokens saved vs doing a full scan (see table below) |

## Token savings estimates

Use these when populating `tokens_saved_est`:

| Mode | Estimate | Rationale |
|---|---|---|
| `full` | `0` | Baseline — no savings |
| `supplement` | `41000` | ~6k at index time (2 fewer docs generated) + ~35k per future session (2 large docs never loaded) |
| `update` | `12000` | Targeted re-scan vs full codebase rescan |

These are conservative estimates derived from empirical session analysis. Use them consistently so comparisons are meaningful.

## Example entry

```json
{"date":"2026-03-13","project":"event-mapper-v2","mode":"supplement","docs_generated":3,"docs_skipped":2,"tokens_saved_est":41000}
```

## How to append

Write the entry using the Write tool. To avoid overwriting, first Read the file (it may not exist — that's fine), then append the new line at the end.

If the file does not exist yet, create it with just the new entry as the first line.

## What NOT to log

- Runs that failed or were abandoned mid-way
- Dry runs or planning-only sessions where no files were written
