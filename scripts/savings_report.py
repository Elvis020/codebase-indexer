#!/usr/bin/env python3
"""Project-local savings report generator for codebase-indexer.

Outputs:
- terminal summary
- HTML report (tasteful, readable, transparent about estimation quality)
- combined mode for end-of-run defaults (terminal + new timestamped HTML)
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SavingsEntry:
    date: str
    project: str
    project_root: str
    mode: str
    project_files: int
    graph_available: bool
    docs_generated: int
    docs_skipped: int
    tokens_raw_baseline_est: int
    tokens_indexer_run_est: int
    tokens_saved_this_run: int
    tokens_saved_future_est: int
    cost_saved_est_usd: float
    measurement_quality: str


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def size_bucket(files: int) -> str:
    if files < 50:
        return "small"
    if files <= 200:
        return "medium"
    if files <= 1000:
        return "large"
    return "xlarge"


def infer_baseline_tokens(project_files: int, mode: str) -> int:
    bucket = size_bucket(project_files)
    if mode in {"full", "supplement"}:
        return {
            "small": 12000,
            "medium": 30000,
            "large": 75000,
            "xlarge": 160000,
        }[bucket]

    # update mode baseline is scoped to changed areas, not full project scans
    return {
        "small": 9000,
        "medium": 22000,
        "large": 42000,
        "xlarge": 70000,
    }[bucket]


def normalize_entry(raw: dict[str, Any], project_root: str, price_per_million: float) -> SavingsEntry:
    project_files = int(raw.get("project_files", 0) or 0)
    mode = str(raw.get("mode", "update"))
    saved_this = int(raw.get("tokens_saved_this_run", 0) or 0)
    saved_future = int(raw.get("tokens_saved_future_est", 0) or 0)

    baseline = raw.get("tokens_raw_baseline_est")
    indexer = raw.get("tokens_indexer_run_est")

    if baseline is None and indexer is not None:
        baseline = int(indexer) + saved_this
    elif baseline is not None:
        baseline = int(baseline)

    if baseline is None:
        baseline = infer_baseline_tokens(project_files, mode)

    if indexer is None:
        indexer = max(0, int(baseline) - saved_this)
    else:
        indexer = int(indexer)

    quality = str(raw.get("measurement_quality", "estimated"))

    cost = raw.get("cost_saved_est_usd")
    if cost is None:
        cost = round((saved_this + saved_future) / 1_000_000 * price_per_million, 4)

    return SavingsEntry(
        date=str(raw.get("date", "")),
        project=str(raw.get("project", Path(project_root).name)),
        project_root=str(raw.get("project_root", project_root)),
        mode=mode,
        project_files=project_files,
        graph_available=bool(raw.get("graph_available", False)),
        docs_generated=int(raw.get("docs_generated", 0) or 0),
        docs_skipped=int(raw.get("docs_skipped", 0) or 0),
        tokens_raw_baseline_est=int(baseline),
        tokens_indexer_run_est=int(indexer),
        tokens_saved_this_run=saved_this,
        tokens_saved_future_est=saved_future,
        cost_saved_est_usd=float(cost),
        measurement_quality=quality,
    )


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_money(n: float) -> str:
    return f"${n:,.2f}"


def summarize(entries: list[SavingsEntry]) -> dict[str, Any]:
    entries_sorted = sorted(entries, key=lambda e: e.date)
    last = entries_sorted[-1]

    total_saved_this = sum(e.tokens_saved_this_run for e in entries_sorted)
    total_saved_future = sum(e.tokens_saved_future_est for e in entries_sorted)
    total_saved = total_saved_this + total_saved_future
    total_cost = sum(e.cost_saved_est_usd for e in entries_sorted)

    mode_tokens: dict[str, int] = defaultdict(int)
    mode_counts: dict[str, int] = defaultdict(int)
    for e in entries_sorted:
        mode_counts[e.mode] += 1
        mode_tokens[e.mode] += e.tokens_saved_this_run + e.tokens_saved_future_est

    measured_runs = sum(1 for e in entries_sorted if e.measurement_quality == "measured")
    estimated_runs = len(entries_sorted) - measured_runs
    graph_runs = sum(1 for e in entries_sorted if e.graph_available)

    return {
        "runs": len(entries_sorted),
        "period_start": entries_sorted[0].date,
        "period_end": entries_sorted[-1].date,
        "last": last,
        "total_saved_this": total_saved_this,
        "total_saved_future": total_saved_future,
        "total_saved": total_saved,
        "total_cost": total_cost,
        "mode_counts": dict(mode_counts),
        "mode_tokens": dict(mode_tokens),
        "measured_runs": measured_runs,
        "estimated_runs": estimated_runs,
        "graph_runs": graph_runs,
        "recent": entries_sorted[-5:],
    }


def terminal_report(summary: dict[str, Any], project_root: str) -> str:
    last: SavingsEntry = summary["last"]
    lines: list[str] = []

    lines.append("Codebase Indexer Savings (Project)")
    lines.append(f"Project            : {last.project}")
    lines.append(f"Path               : {project_root}")
    lines.append(f"Period             : {summary['period_start']} -> {summary['period_end']}")
    lines.append(f"Runs               : {summary['runs']}")
    lines.append("")

    lines.append("This Run Comparison")
    lines.append(f"Raw baseline est   : {fmt_int(last.tokens_raw_baseline_est)} tokens")
    lines.append(f"Indexer run est    : {fmt_int(last.tokens_indexer_run_est)} tokens")
    lines.append(f"Saved this run     : {fmt_int(last.tokens_saved_this_run)} tokens")
    lines.append(f"Future est benefit : {fmt_int(last.tokens_saved_future_est)} tokens")
    lines.append(f"Mode / Graph       : {last.mode} / {'yes' if last.graph_available else 'no'}")
    lines.append("")

    lines.append("Cumulative Savings")
    lines.append(f"Saved this-run     : {fmt_int(summary['total_saved_this'])} tokens")
    lines.append(f"Saved future-est   : {fmt_int(summary['total_saved_future'])} tokens")
    lines.append(f"Saved total        : {fmt_int(summary['total_saved'])} tokens")
    lines.append(f"Estimated cost     : {fmt_money(summary['total_cost'])}")
    lines.append("")

    lines.append("Breakdown by Mode")
    for mode in ["full", "supplement", "update"]:
        count = summary["mode_counts"].get(mode, 0)
        tokens = summary["mode_tokens"].get(mode, 0)
        lines.append(f"{mode:<18}: x{count:<3} {fmt_int(tokens)} tokens")
    lines.append("")

    lines.append("Measurement Quality")
    lines.append(f"Measured runs      : {summary['measured_runs']}")
    lines.append(f"Estimated runs     : {summary['estimated_runs']}")
    lines.append("Method note        : Estimated values follow codebase-indexer sizing heuristics.")
    lines.append("")

    lines.append("Recent Runs")
    lines.append("date       mode        saved_this   saved_future   quality")
    for e in summary["recent"]:
        lines.append(
            f"{e.date:<10} {e.mode:<11} {fmt_int(e.tokens_saved_this_run):>10} {fmt_int(e.tokens_saved_future_est):>13}   {e.measurement_quality}"
        )

    return "\n".join(lines)


def mode_bar(value: int, max_value: int) -> str:
    if max_value <= 0:
        return "0%"
    pct = int((value / max_value) * 100)
    return f"{pct}%"


def html_report(summary: dict[str, Any], project_root: str) -> str:
    last: SavingsEntry = summary["last"]
    mode_tokens = summary["mode_tokens"]
    max_mode = max(mode_tokens.values()) if mode_tokens else 1

    rows = "\n".join(
        f"<tr><td>{e.date}</td><td>{e.mode}</td><td>{fmt_int(e.tokens_raw_baseline_est)}</td><td>{fmt_int(e.tokens_indexer_run_est)}</td><td>{fmt_int(e.tokens_saved_this_run)}</td><td>{fmt_int(e.tokens_saved_future_est)}</td><td>{e.measurement_quality}</td></tr>"
        for e in summary["recent"]
    )

    bars = []
    for mode in ["full", "supplement", "update"]:
        value = mode_tokens.get(mode, 0)
        pct = mode_bar(value, max_mode)
        bars.append(
            f"""
            <div class=\"bar-row\">
              <div class=\"bar-label\">{mode}</div>
              <div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:{pct}\"></div></div>
              <div class=\"bar-value\">{fmt_int(value)}</div>
            </div>
            """
        )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Codebase Indexer Savings</title>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
  <link href=\"https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap\" rel=\"stylesheet\">
  <style>
    :root {{
      --bg: #f7f4ef;
      --bg-2: #efe8dd;
      --ink: #1f1a14;
      --muted: #6a5e50;
      --card: rgba(255,255,255,0.72);
      --stroke: rgba(56,44,31,0.14);
      --accent: #0e7a66;
      --accent-soft: rgba(14,122,102,0.18);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: 'IBM Plex Sans', system-ui, sans-serif;
      color: var(--ink);
      background: radial-gradient(1200px 700px at 80% -10%, #e1d2be 0%, transparent 60%),
                  radial-gradient(900px 500px at -10% 10%, #d8e9df 0%, transparent 55%),
                  linear-gradient(180deg, var(--bg), var(--bg-2));
      min-height: 100vh;
      animation: fadein 560ms cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .wrap {{ max-width: 1040px; margin: 36px auto 72px; padding: 0 20px; }}
    .hero {{ margin-bottom: 22px; }}
    h1 {{
      font-family: 'Fraunces', serif;
      font-size: clamp(2rem, 4vw, 3rem);
      line-height: 1.06;
      margin: 0 0 8px;
      letter-spacing: -0.02em;
    }}
    .sub {{ color: var(--muted); font-size: 1rem; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 20px 0 24px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--stroke);
      border-radius: 16px;
      padding: 14px 14px 12px;
      backdrop-filter: blur(6px);
      box-shadow: 0 8px 30px rgba(27,20,13,0.06);
    }}
    .k {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }}
    .v {{ font-size: 1.5rem; font-weight: 600; margin-top: 4px; }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--stroke);
      border-radius: 18px;
      padding: 18px;
      margin-bottom: 14px;
    }}
    h2 {{ font-size: 1.08rem; margin: 0 0 14px; letter-spacing: 0.01em; }}
    .cmp {{ display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 10px; }}
    .pill {{ background: #fff; border: 1px solid var(--stroke); border-radius: 12px; padding: 10px; }}
    .pill b {{ display: block; font-size: 1.12rem; margin-top: 4px; }}
    .bar-row {{ display: grid; grid-template-columns: 96px 1fr 120px; gap: 10px; align-items: center; margin-bottom: 10px; }}
    .bar-label {{ color: var(--muted); text-transform: uppercase; font-size: 12px; letter-spacing: .08em; }}
    .bar-track {{ height: 10px; border-radius: 999px; background: #ece5da; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 999px; background: linear-gradient(90deg, #0e7a66, #23a087); transition: width .5s cubic-bezier(0.16,1,0.3,1); }}
    .bar-value {{ text-align: right; font-variant-numeric: tabular-nums; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .94rem; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--stroke); }}
    th {{ color: var(--muted); font-weight: 600; font-size: .8rem; letter-spacing: .06em; text-transform: uppercase; }}
    .foot {{ color: var(--muted); font-size: .9rem; margin-top: 10px; }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .cmp {{ grid-template-columns: repeat(2, minmax(0,1fr)); }}
      .bar-row {{ grid-template-columns: 80px 1fr 90px; }}
    }}
    @media (max-width: 620px) {{
      .grid, .cmp {{ grid-template-columns: 1fr; }}
    }}
    @keyframes fadein {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>Codebase Savings Report</h1>
      <div class=\"sub\">{last.project} · {project_root} · period {summary['period_start']} to {summary['period_end']}</div>
    </div>

    <section class=\"grid\">
      <article class=\"card\"><div class=\"k\">Total Runs</div><div class=\"v\">{summary['runs']}</div></article>
      <article class=\"card\"><div class=\"k\">Saved This-Run</div><div class=\"v\">{fmt_int(summary['total_saved_this'])}</div></article>
      <article class=\"card\"><div class=\"k\">Future Est. Savings</div><div class=\"v\">{fmt_int(summary['total_saved_future'])}</div></article>
      <article class=\"card\"><div class=\"k\">Estimated Value</div><div class=\"v\">{fmt_money(summary['total_cost'])}</div></article>
    </section>

    <section class=\"panel\">
      <h2>This Run Comparison</h2>
      <div class=\"cmp\">
        <div class=\"pill\">Raw baseline<b>{fmt_int(last.tokens_raw_baseline_est)}</b></div>
        <div class=\"pill\">Indexer run<b>{fmt_int(last.tokens_indexer_run_est)}</b></div>
        <div class=\"pill\">Saved now<b>{fmt_int(last.tokens_saved_this_run)}</b></div>
        <div class=\"pill\">Future benefit<b>{fmt_int(last.tokens_saved_future_est)}</b></div>
      </div>
      <div class=\"foot\">Mode: <b>{last.mode}</b> · Graph: <b>{'yes' if last.graph_available else 'no'}</b> · Quality: <b>{last.measurement_quality}</b></div>
    </section>

    <section class=\"panel\">
      <h2>Mode Contribution</h2>
      {''.join(bars)}
    </section>

    <section class=\"panel\">
      <h2>Recent Runs</h2>
      <table>
        <thead>
          <tr><th>Date</th><th>Mode</th><th>Raw baseline</th><th>Indexer run</th><th>Saved now</th><th>Future est</th><th>Quality</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <div class=\"foot\">Generated {generated_at}. Estimated values use codebase-indexer project-size heuristics unless run quality is marked <b>measured</b>.</div>
    </section>
  </div>
</body>
</html>
"""


def timestamped_output_path(output_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return output_path.with_name(f"{output_path.stem}-{stamp}{output_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate project-local codebase-indexer savings report")
    parser.add_argument("--project-root", default=".", help="Project root")
    parser.add_argument("--input", default=".codebase-indexer/savings.jsonl", help="Savings JSONL path (relative to project root unless absolute)")
    parser.add_argument("--format", choices=["terminal", "html", "both"], default="terminal", help="Output format")
    parser.add_argument("--output", default="docs/codebase-indexer-savings.html", help="HTML output path (relative to project root unless absolute)")
    parser.add_argument("--timestamp-html", choices=["yes", "no"], default="yes", help="When writing HTML, append timestamp to filename")
    parser.add_argument("--price-per-million", type=float, default=3.0, help="USD per 1M input tokens")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path

    raw_entries = parse_jsonl(input_path)
    if not raw_entries:
        print("No project-local savings data found. Run /codebase-indexer first to log savings.")
        return

    root_str = str(root)
    filtered = [
        e for e in raw_entries
        if str(e.get("project_root", root_str)) == root_str
    ]
    if not filtered:
        print("No savings entries found for this project root.")
        return

    entries = [normalize_entry(e, root_str, args.price_per_million) for e in filtered]
    summary = summarize(entries)

    if args.format == "terminal":
        print(terminal_report(summary, root_str))
        return

    html = html_report(summary, root_str)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    if args.timestamp_html == "yes":
        output_path = timestamped_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    if args.format == "html":
        print(str(output_path))
        return

    # both mode: terminal first, then generated file path
    print(terminal_report(summary, root_str))
    print("")
    print(f"HTML report: {output_path}")


if __name__ == "__main__":
    main()
