# Savings Report

Use this guide when the user asks for savings visibility, especially:
- `/codebase-indexer savings`
- `/codebase-indexer savings terminal`
- `/codebase-indexer savings html`
- "show savings", "token savings report", "did this help"

Default scope is **current project only**.

Note: savings reporting is also generated automatically at the end of every successful indexer run (terminal + timestamped HTML). This guide also covers on-demand re-generation.

---

## Data source (project-local)

Read:

```
<project-root>/.codebase-indexer/savings.jsonl
```

Each line is one JSON object from successful indexing runs.

If file is missing or empty, tell the user:
> "No project-local savings logged yet. Run /codebase-indexer to create your first savings record."

---

## Output modes

### Terminal mode (default)

Show a compact, confidence-aware comparison:

```
Codebase Indexer Savings (Project)
Project            : <name>
Path               : <abs path>
Period             : <first_date> -> <last_date>
Runs               : <n>

This Run Comparison
Raw baseline est   : <tokens>
Indexer run est    : <tokens>
Saved this run     : <tokens>
Future est benefit : <tokens>
Mode / Graph       : <mode> / <yes|no>

Cumulative Savings
Saved this-run     : <tokens>
Saved future-est   : <tokens>
Saved total        : <tokens>
Estimated cost     : $<cost>

Breakdown by Mode
full               : x<n> <tokens>
supplement         : x<n> <tokens>
update             : x<n> <tokens>

Measurement Quality
Measured runs      : <n>
Estimated runs     : <n>
Method note        : Estimated values follow codebase-indexer sizing heuristics.
```

### HTML mode

Generate:

```
<project-root>/docs/codebase-indexer-savings-YYYYMMDD-HHMMSS.html
```

Requirements:
- polished, legible visual summary
- clear baseline vs indexer comparison cards
- mode contribution chart
- recent runs table
- explicit methodology/quality footnote

---

## Recommended helper script

Use:

```bash
python3 scripts/savings_report.py --project-root . --format terminal
python3 scripts/savings_report.py --project-root . --format html
python3 scripts/savings_report.py --project-root . --format both --output docs/codebase-indexer-savings.html --timestamp-html yes
```

If HTML mode is requested, return the output path.

---

## Accuracy and trust rules

1. Never present estimates as exact telemetry.
2. Always include measurement quality (`measured` vs `estimated`).
3. Show both:
   - savings this run
   - future estimated savings
4. Keep project scope strict: only entries whose `project_root` matches current root.
5. If comparison fields are missing in legacy rows, compute deterministic fallbacks and label them estimated.
