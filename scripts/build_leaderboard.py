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
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
TASKS_DIR = REPO / "tasks"

# How a task's `source` maps to a difficulty regime, ordered easy -> hard.
REGIMES = ["Translation", "Grounded (ligand/SS)", "Clinical (SIFTS/ClinVar)"]


def _regime_of(source: str) -> str:
    if source in ("generated", "curated"):
        return "Translation"
    if source == "grounded":
        return "Grounded (ligand/SS)"
    return "Clinical (SIFTS/ClinVar)"


def _task_regimes() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in TASKS_DIR.rglob("*.json"):
        try:
            t = json.loads(f.read_text())
        except (ValueError, OSError):
            continue
        if t.get("category") == "mvs":
            out[t["id"]] = _regime_of(t.get("source", "curated"))
    return out


def regime_table(ranked: list) -> str:
    """Mean F1 per difficulty regime — shows the gradient and where models separate."""
    reg = _task_regimes()
    if not reg:
        return ""
    head = "".join(f"<th>{html.escape(n)}</th>" for n, m in ranked if m.get("by_category", {}).get("mvs"))
    cols = [(n, m) for n, m in ranked if m.get("by_category", {}).get("mvs")]
    body = []
    for rg in REGIMES:
        n_tasks = sum(1 for v in reg.values() if v == rg)
        if not n_tasks:
            continue
        vals = {}
        for n, m in cols:
            fs = [t["f1"] for t in m["tasks"] if reg.get(t["id"]) == rg]
            vals[n] = statistics.fmean(fs) if fs else None
        best = max((v for v in vals.values() if v is not None), default=None)
        cells = []
        for n, _ in cols:
            v = vals[n]
            if v is None:
                cells.append("<td>&mdash;</td>")
            else:
                lead = " class='f1'" if v == best else ""
                cells.append(f"<td{lead}>{v:.3f}</td>")
        body.append(f"<tr><td class='model'>{rg} <span class='pm'>({n_tasks})</span></td>{''.join(cells)}</tr>")
    return (
        "<h2>Difficulty gradient by task regime</h2>"
        "<p class='sub'>Mean F1 by how the answer key is grounded, easy to hard. "
        "Harder regimes separate the models more &mdash; the property a benchmark wants.</p>"
        f"<table><thead><tr><th>Regime</th>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def mvs_f1(m: dict) -> float | None:
    d = m.get("by_category", {}).get("mvs")
    return d["mean_f1"] if d else None


def track_cell(m: dict, cat: str) -> str:
    d = m.get("by_category", {}).get(cat)
    if not d:
        return "&mdash;"
    std = f" <span class='pm'>±{d['std']:.2f}</span>" if d.get("std") else ""
    return f"{d['mean_f1']:.3f}{std}"


def runtime_str(m: dict) -> str:
    spc = m.get("sec_per_call")
    return f"{spc:.2f}s/call" if spc is not None else "&mdash;"


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
        f"<td class='f1'>{track_cell(m, 'mvs')}</td>"
        f"<td>{track_cell(m, 'api_calling')}</td>"
        f"<td class='spec'>{html.escape(m.get('spec', ''))}</td>"
        f"<td>{toks}</td>"
        f"<td>{cost_str}</td>"
        f"<td>{runtime_str(m)}</td>"
        "</tr>"
    )


def drilldown(ranked: list) -> str:
    """A skill x model matrix: 'on selection, model X beats Y'."""
    skills: list[str] = []
    for _, m in ranked:
        for s in m.get("by_skill", {}):
            if s not in skills:
                skills.append(s)
    if not skills:
        return ""
    skills.sort()
    head = "".join(f"<th>{html.escape(n)}</th>" for n, _ in ranked)
    body = []
    for skill in skills:
        cells = []
        best = max((m["by_skill"].get(skill, {}).get("mean_f1", -1) for _, m in ranked),
                   default=-1)
        n = next((m["by_skill"][skill]["n"] for _, m in ranked if skill in m.get("by_skill", {})), 0)
        for _, m in ranked:
            d = m.get("by_skill", {}).get(skill)
            if not d:
                cells.append("<td>&mdash;</td>")
            else:
                lead = " class='f1'" if d["mean_f1"] == best else ""
                cells.append(f"<td{lead}>{d['mean_f1']:.3f}</td>")
        body.append(f"<tr><td class='model'>{skill} <span class='pm'>({n})</span></td>{''.join(cells)}</tr>")
    return (
        "<h2>Drill-down by skill</h2>"
        "<p class='sub'>Mean F1 on tasks tagged with each skill (task count in parens). "
        "Skills are derived automatically from the reference scene tree.</p>"
        f"<table><thead><tr><th>Skill</th>{head}</tr></thead><tbody>"
        f"{''.join(body)}</tbody></table>"
    )


def build(scorecard_path: pathlib.Path) -> None:
    data = json.loads(scorecard_path.read_text())
    models = data.get("models", {})
    # Rank by the primary track (MVS); fall back to overall mean if absent.
    ranked = sorted(models.items(),
                    key=lambda kv: (mvs_f1(kv[1]) if mvs_f1(kv[1]) is not None
                                    else kv[1]["mean_f1"]),
                    reverse=True)
    rows = "\n".join(row(i + 1, name, m) for i, (name, m) in enumerate(ranked))
    n_tasks = data.get("n_tasks", "?")
    n_samples = data.get("samples", 1)
    regimes = regime_table(ranked)
    drill = drilldown(ranked)

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
  h2 {{ margin-top: 2.5rem; font-size: 1.15rem; }}
  .sub {{ color: #888; margin-top: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1.5rem; }}
  th, td {{ text-align: left; padding: .5rem .6rem; border-bottom: 1px solid #8884; }}
  th {{ font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; color: #888; }}
  td.f1 {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
  td.rank {{ color: #888; }}
  td.model {{ font-weight: 600; }}
  td.spec {{ font-family: ui-monospace, monospace; font-size: .85rem; color: #888; }}
  td .pm {{ color: #999; font-weight: 400; font-size: .85em; }}
  tr:first-child td.rank {{ color: #d4a017; font-weight: 700; }}
  footer {{ margin-top: 2rem; font-size: .85rem; color: #888; }}
  code {{ background: #8882; padding: .1em .35em; border-radius: 4px; }}
</style>
</head>
<body>
  <h1>MolBench</h1>
  <p class="sub">Molecular-visualization benchmark for CI assistants &mdash;
     {n_tasks} tasks, {n_samples} sample(s)/task. Ranked by the primary
     <b>MVS</b> (MolViewSpec scene-tree) track.</p>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Model</th><th>MVS&nbsp;F1</th><th>API&nbsp;F1</th>
        <th>Spec</th><th>Tokens&nbsp;(in/out)</th><th>Cost</th><th>Speed</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
  {regimes}
  {drill}
  <footer>
    <p>Higher F1 is better. <b>MVS&nbsp;F1</b> is the primary, engine-agnostic
       scene-tree score; <b>API&nbsp;F1</b> is the secondary imperative-PDBeMolstar
       track. &plusmn; is the spread across tasks. Costs use published list prices.</p>
    <p>Reproduce: <code>python -m molbench.runner --models &lt;spec&gt; --samples 5</code> &middot;
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
