#!/usr/bin/env python3
"""
Render a scorecard JSON into a static leaderboard for GitHub Pages.

    python scripts/build_leaderboard.py [results/scorecard.json]

Writes a self-contained ``docs/index.html`` (no JS, no external assets) plus a
copy of the scorecard at ``docs/scorecard.json`` for transparency. Publishing a
result is therefore a deliberate, reviewable commit — not an automatic side
effect of running the bench.
"""

from __future__ import annotations

import html
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"


def perfect_count(model: dict) -> int:
    return sum(1 for t in model["tasks"]
               if t.get("category") == "api_calling" and t.get("f1") == 1.0)


def row(rank: int, name: str, m: dict) -> str:
    u = m.get("usage", {}) or {}
    cost = m.get("cost_usd")
    cost_str = f"${cost:.4f}" if isinstance(cost, (int, float)) else "&mdash;"
    toks = (f"{u.get('input_tokens', 0):,} / {u.get('output_tokens', 0):,}"
            if u.get("calls") else "&mdash;")
    return (
        "<tr>"
        f"<td class='rank'>{rank}</td>"
        f"<td class='model'>{html.escape(name)}</td>"
        f"<td class='f1'>{m['mean_f1']:.3f}</td>"
        f"<td>{perfect_count(m)} / {m['n_graded']}</td>"
        f"<td class='spec'>{html.escape(m.get('spec', ''))}</td>"
        f"<td>{toks}</td>"
        f"<td>{cost_str}</td>"
        "</tr>"
    )


def build(scorecard_path: pathlib.Path) -> None:
    data = json.loads(scorecard_path.read_text())
    models = data.get("models", {})
    ranked = sorted(models.items(), key=lambda kv: kv[1]["mean_f1"], reverse=True)
    rows = "\n".join(row(i + 1, name, m) for i, (name, m) in enumerate(ranked))
    n_tasks = data.get("n_tasks", "?")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MolBench &mdash; Leaderboard</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
          max-width: 860px; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; }}
  h1 {{ margin-bottom: .2rem; }}
  .sub {{ color: #888; margin-top: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1.5rem; }}
  th, td {{ text-align: left; padding: .5rem .6rem; border-bottom: 1px solid #8884; }}
  th {{ font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; color: #888; }}
  td.f1 {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
  td.rank {{ color: #888; }}
  td.model {{ font-weight: 600; }}
  td.spec {{ font-family: ui-monospace, monospace; font-size: .85rem; color: #888; }}
  tr:first-child td.rank {{ color: #d4a017; font-weight: 700; }}
  footer {{ margin-top: 2rem; font-size: .85rem; color: #888; }}
  code {{ background: #8882; padding: .1em .35em; border-radius: 4px; }}
</style>
</head>
<body>
  <h1>MolBench</h1>
  <p class="sub">Molecular-visualization benchmark for CI assistants &mdash;
     Component&nbsp;1 (API calling), {n_tasks} tasks.</p>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Model</th><th>Mean&nbsp;F1</th><th>Perfect</th>
        <th>Spec</th><th>Tokens&nbsp;(in/out)</th><th>Cost</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <footer>
    <p>Higher F1 is better. &ldquo;Perfect&rdquo; counts API tasks scored exactly 1.0.
       Costs use the published per-token list prices at run time.</p>
    <p>Reproduce: <code>python -m molbench.runner --models &lt;spec&gt;</code> &middot;
       <a href="./scorecard.json">raw scorecard.json</a> &middot;
       <a href="https://github.com/dbolser/MolBench">source</a></p>
  </footer>
</body>
</html>
"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(page)
    (DOCS / "scorecard.json").write_text(json.dumps(data, indent=2))
    print(f"wrote {DOCS/'index.html'} and {DOCS/'scorecard.json'} "
          f"({len(ranked)} models)")


if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "results" / "scorecard.json"
    build(src)
