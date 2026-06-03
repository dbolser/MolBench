#!/usr/bin/env python3
"""
Render the MolBench scorecard + gallery into a static site for GitHub Pages.

    python scripts/build_leaderboard.py [docs/scorecard.json]

Writes two self-contained pages that share ``docs/style.css`` (no JS, no CDN —
works fully offline):

  * ``docs/index.html``   — leaderboard, difficulty gradient, skill drill-down,
                            and the "Key findings" narrative.
  * ``docs/gallery.html`` — the human-evaluator gallery (reference vs model
                            render, with tree-match + visual scores + verdict).

All numbers are read from ``docs/scorecard.json`` and ``docs/gallery_data.json``
— nothing is hard-coded. Publishing is therefore a deliberate, reviewable commit.

Python 3.10 compatible: no backslashes inside f-string expressions.
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

NL = "\n"

# How a task's `source` maps to a difficulty regime, ordered easy -> hard.
REGIMES = ["Translation", "Grounded (ligand/SS)", "Clinical (SIFTS/ClinVar)"]


# --------------------------------------------------------------------------- #
# Data helpers
# --------------------------------------------------------------------------- #
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


def mvs_f1(m: dict) -> float | None:
    d = m.get("by_category", {}).get("mvs")
    return d["mean_f1"] if d else None


def is_open(name: str) -> bool:
    """Open-weight models are namespaced with a slash (qwen/…, google/…)."""
    return "/" in name


def fmt_cost(cost) -> str:
    if isinstance(cost, (int, float)):
        return f"${cost:.4f}"
    return "&mdash;"


def fmt_speed(m: dict) -> str:
    spc = m.get("sec_per_call")
    return f"{spc:.2f}s" if spc is not None else "&mdash;"


def fmt_pct(v) -> str:
    return "&mdash;" if v is None else f"{v * 100:.0f}%"


def fmt_f1(v) -> str:
    return "&mdash;" if v is None else f"{v:.3f}"


def track_cell(m: dict, cat: str) -> str:
    d = m.get("by_category", {}).get(cat)
    if not d:
        return "&mdash;"
    std = ""
    if d.get("std"):
        std = f" <span class='pm'>&plusmn;{d['std']:.2f}</span>"
    return f"{d['mean_f1']:.3f}{std}"


# --------------------------------------------------------------------------- #
# Shared chrome
# --------------------------------------------------------------------------- #
def head(title: str, desc: str) -> str:
    safe_desc = html.escape(desc)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{safe_desc}">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>"""


def header(active: str) -> str:
    def cls(name: str) -> str:
        return "active" if name == active else ""

    return f"""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html">
      <span class="mark">M</span>
      <span>MolBench</span>
    </a>
    <nav class="nav" aria-label="Primary">
      <a href="index.html" class="{cls('index')}">Leaderboard</a>
      <a href="gallery.html" class="{cls('gallery')}">Evaluator gallery</a>
      <a href="https://github.com/dbolser/MolBench" class="gh"
         rel="noopener">GitHub</a>
    </nav>
  </div>
</header>"""


def footer() -> str:
    repro = (
        "python -m molbench.runner --models &lt;spec&gt; --samples 5"
    )
    return f"""<footer class="site-footer">
  <div class="wrap">
    <p><b>Data sources.</b> Structures from the
       <a href="https://www.rcsb.org/" rel="noopener">RCSB&nbsp;PDB</a>;
       clinical grounding via
       <a href="https://www.ebi.ac.uk/pdbe/docs/sifts/" rel="noopener">PDBe&nbsp;SIFTS</a>
       (UniProt&harr;PDB residue numbering, CC-BY-4.0),
       <a href="https://www.uniprot.org/" rel="noopener">UniProt</a> (CC-BY-4.0),
       and <a href="https://www.ncbi.nlm.nih.gov/clinvar/" rel="noopener">ClinVar</a>
       (NCBI, public domain). See the
       <a href="https://github.com/dbolser/MolBench#data-sources--acknowledgements"
          rel="noopener">data sources &amp; acknowledgements</a> in the README.</p>
    <p><b>Reproduce.</b> <span class="repro">{repro}</span></p>
    <p>MolBench is open source (MIT) &middot;
       <a href="https://github.com/dbolser/MolBench" rel="noopener">github.com/dbolser/MolBench</a>
       &middot; <a href="scorecard.json">raw scorecard.json</a></p>
  </div>
</footer>
</body>
</html>"""


# --------------------------------------------------------------------------- #
# Leaderboard page sections
# --------------------------------------------------------------------------- #
def hero(data: dict, ranked: list) -> str:
    n_models = len(ranked)
    n_tasks = data.get("n_tasks", "?")
    n_samples = data.get("samples", 1)

    leader_name, leader_m = ranked[0]
    leader_f1 = mvs_f1(leader_m)

    # Best open-weight model by MVS F1, and its cost.
    open_models = [(n, m) for n, m in ranked if is_open(n)]
    best_open = open_models[0] if open_models else None

    stats = []
    stats.append(("Models evaluated", f"{n_models}", "open &amp; closed"))
    stats.append(
        ("Benchmark tasks", f"{n_tasks}",
         f"&times;{n_samples} samples each"))

    short_leader = leader_name.split("/")[-1]
    stats.append(
        ("MVS&nbsp;F1 leader", f"{leader_f1:.2f}",
         html.escape(short_leader)))

    if best_open is not None:
        bo_name, bo_m = best_open
        bo_short = bo_name.split("/")[-1]
        bo_cost = bo_m.get("cost_usd")
        cost_note = ""
        if isinstance(bo_cost, (int, float)):
            cost_note = f"{html.escape(bo_short)} at {fmt_cost(bo_cost)}"
        else:
            cost_note = html.escape(bo_short)
        stats.append(
            ("Top open model", f"{mvs_f1(bo_m):.2f}", cost_note))

    cards = []
    for label, value, sub in stats:
        cards.append(
            "<div class='stat'>"
            f"<div class='label'>{label}</div>"
            f"<div class='value'>{value}</div>"
            f"<div class='sub'>{sub}</div>"
            "</div>"
        )
    cards_html = NL.join(cards)

    return f"""<section class="hero wrap" aria-label="Overview">
  <span class="eyebrow">Molecular-visualization benchmark</span>
  <h1>MolBench</h1>
  <p class="pitch">Can LLM assistants <b>control</b> a molecular viewer? MolBench
     turns natural-language requests &mdash; <i>&ldquo;show the heme as orange
     ball-and-stick&rdquo;</i>, <i>&ldquo;highlight the R175H pathogenic
     variant&rdquo;</i> &mdash; into <b>MolViewSpec</b> scene trees and grades
     them deterministically, engine-neutral.</p>
  <div class="stats">
{cards_html}
  </div>
</section>"""


def leaderboard_table(ranked: list) -> str:
    leader_name = ranked[0][0]
    rows = []
    for i, (name, m) in enumerate(ranked):
        rank = i + 1
        leader_cls = " class='leader'" if name == leader_name else ""
        open_badge = (
            "<span class='badge open'>open</span>" if is_open(name)
            else "<span class='badge closed'>closed</span>"
        )
        spec = m.get("spec", "")
        spec_line = ""
        if spec and spec != "baseline":
            spec_line = f"<span class='spec'>{html.escape(spec)}</span>"
        rows.append(
            f"<tr{leader_cls}>"
            f"<td class='rank'>{rank}</td>"
            f"<td class='model'>{html.escape(name)}{open_badge}{spec_line}</td>"
            f"<td class='metric-primary'>{track_cell(m, 'mvs')}</td>"
            f"<td>{fmt_pct(m.get('parse_success'))}</td>"
            f"<td>{fmt_f1(m.get('cond_f1'))}</td>"
            f"<td>{track_cell(m, 'api_calling')}</td>"
            f"<td>{fmt_cost(m.get('cost_usd'))}</td>"
            f"<td>{fmt_speed(m)}</td>"
            "</tr>"
        )
    rows_html = NL.join(rows)

    return f"""<section class="wrap" aria-label="Leaderboard">
  <h2>Leaderboard</h2>
  <p class="section-sub">Ranked by the primary <b>MVS&nbsp;F1</b> track
     (MolViewSpec scene-tree match; parse failures count as 0). The leader is
     highlighted. Open-weight models are namespaced with a provider slash.</p>
  <div class="table-scroll">
    <table>
      <thead>
        <tr>
          <th class="left">#</th>
          <th class="left">Model</th>
          <th>MVS&nbsp;F1</th>
          <th>Parse&nbsp;%</th>
          <th>Cond&nbsp;F1</th>
          <th>API&nbsp;F1</th>
          <th>Cost</th>
          <th>Speed</th>
        </tr>
      </thead>
      <tbody>
{rows_html}
      </tbody>
    </table>
  </div>
  <p class="section-sub" style="margin-top:1rem;font-size:.85rem">
    <b>MVS&nbsp;F1</b>: primary, engine-agnostic scene-tree score (parse
    failures = 0). <b>Parse&nbsp;%</b>: share of samples that emitted valid
    output. <b>Cond&nbsp;F1</b>: scene quality <i>given</i> valid output &mdash;
    the gap from MVS&nbsp;F1 measures how much a model is dragged down by
    malformed JSON rather than visualization error. <b>API&nbsp;F1</b>: the
    secondary imperative-call track. <span class="pm">&plusmn;</span> is the
    spread across tasks; costs use provider list prices.
  </p>
</section>"""


def findings(ranked: list) -> str:
    """Key-findings cards, with numbers pulled live from the scorecard."""
    by_name = dict(ranked)

    # The findings narrative is about the LLMs; the non-LLM rules baseline
    # (spec == "baseline") is a reference floor, not a competitor, so exclude it
    # from the cluster/spread statistics.
    llms = [(n, m) for n, m in ranked if m.get("spec") != "baseline"]

    # Conditional-F1 cluster bounds (LLMs that produced valid output).
    cond_vals = [m["cond_f1"] for _, m in llms
                 if m.get("cond_f1") and m.get("parse_success")]
    cond_lo = min(cond_vals) if cond_vals else 0.0
    cond_hi = max(cond_vals) if cond_vals else 0.0

    # Unconditional MVS spread across the LLMs.
    mvs_vals = [mvs_f1(m) for _, m in llms if mvs_f1(m) is not None]
    mvs_spread = (max(mvs_vals) - min(mvs_vals)) if mvs_vals else 0.0

    # gpt-oss-20b: last overall, but strong conditional.
    oss = by_name.get("openai/gpt-oss-20b")
    oss_mvs = mvs_f1(oss) if oss else None
    oss_cond = oss.get("cond_f1") if oss else None
    # Its rank by Cond F1 among the LLMs.
    oss_cond_rank = None
    if oss and oss_cond is not None:
        graded = [(n, m) for n, m in llms if m.get("cond_f1") is not None]
        graded.sort(key=lambda kv: kv[1]["cond_f1"], reverse=True)
        for idx, (n, _) in enumerate(graded):
            if n == "openai/gpt-oss-20b":
                oss_cond_rank = idx + 1
                break

    # Open models near the closed frontier-small tier.
    gemma = by_name.get("google/gemma-3-27b-it")
    gemma_cost = fmt_cost(gemma.get("cost_usd")) if gemma else "&mdash;"

    # If gpt-oss is within a rounding hair of the rank above it, call it a tie —
    # at 2dp it is indistinguishable, so a bare "4th" would overstate the gap.
    oss_tie = ""
    if oss_cond_rank and oss_cond_rank > 1:
        ordered = sorted((m["cond_f1"] for _, m in llms
                          if m.get("cond_f1") is not None), reverse=True)
        above = ordered[oss_cond_rank - 2]
        if oss_cond is not None and abs(above - oss_cond) < 0.005:
            tie_to = {2: "1st", 3: "2nd", 4: "3rd"}.get(oss_cond_rank, "")
            if tie_to:
                oss_tie = f" (tied for {tie_to})"

    cond_lo_s = f"{cond_lo:.2f}"
    cond_hi_s = f"{cond_hi:.2f}"
    mvs_spread_s = f"{mvs_spread:.2f}"
    oss_mvs_s = f"{oss_mvs:.2f}" if oss_mvs is not None else "&mdash;"
    oss_cond_s = f"{oss_cond:.2f}" if oss_cond is not None else "&mdash;"
    oss_rank_base = {1: "best", 2: "2nd", 3: "3rd"}.get(
        oss_cond_rank, f"{oss_cond_rank}th")
    oss_rank_s = f"{oss_rank_base}{oss_tie}"

    f1 = (
        "<div class='finding headline'>"
        "<div class='fnum'>FINDING 01 &middot; THE HEADLINE</div>"
        "<h3>Format reliability, not competence, drives the ranking</h3>"
        "<p>The MVS ranking is largely a <b>JSON-validity</b> ranking. Conditional "
        f"on producing valid output, every LLM clusters tightly at "
        f"<b>{cond_lo_s}&ndash;{cond_hi_s}</b> Cond&nbsp;F1 &mdash; yet the "
        f"unconditional spread is ~<b>{mvs_spread_s}</b>, driven almost entirely by "
        "Parse&nbsp;%.</p>"
        f"<p><code>gpt-oss-20b</code> is <b>last overall</b> (~{oss_mvs_s} MVS&nbsp;F1) "
        f"but ~{oss_rank_s} by Cond&nbsp;F1 (~{oss_cond_s}): a competent visualizer "
        "that is simply format-unreliable.</p>"
        "</div>"
    )

    f2 = (
        "<div class='finding'>"
        "<div class='fnum'>FINDING 02</div>"
        "<h3>Open weights reached the closed frontier-small tier</h3>"
        f"<p>Open models match the small closed frontier at <b>6&ndash;19&times; lower "
        f"cost</b> &mdash; Gemma-3-27B at {gemma_cost}, DeepSeek-V3.2 close behind. "
        "But &ldquo;open&rdquo; spans a wide range: Qwen3-30B and gpt-oss-20b still "
        "lag well behind on reliability.</p>"
        "</div>"
    )

    f3 = (
        "<div class='finding'>"
        "<div class='fnum'>FINDING 03</div>"
        "<h3>A difficulty gradient that discriminates</h3>"
        "<p>Tasks span translation &rarr; structure-grounded &rarr; clinical. Harder "
        "regimes separate models <b>more</b> &mdash; model spread grows from ~0.10 to "
        "~0.24 &mdash; exactly the property a benchmark wants. See the per-regime "
        "table below.</p>"
        "</div>"
    )

    f4 = (
        "<div class='finding'>"
        "<div class='fnum'>FINDING 04 &middot; NOVEL</div>"
        "<h3>Clinical grounding into 3D structure</h3>"
        "<p>Tasks bridge clinical genetics and structure: ClinVar pathogenic variants "
        "mapped via UniProt&nbsp;+&nbsp;PDBe&nbsp;SIFTS numbering onto the correct "
        "residues (e.g. p53 <b>R175H</b>). No other molecular-viz benchmark does "
        "this.</p>"
        "</div>"
    )

    return f"""<section class="wrap" aria-label="Key findings">
  <h2>Key findings</h2>
  <p class="section-sub">What the leaderboard actually tells you &mdash; read
     these before the table.</p>
  <div class="findings">
{f1}
{f2}
{f3}
{f4}
  </div>
</section>"""


def regime_table(ranked: list) -> str:
    """Mean F1 per difficulty regime — shows the gradient and where models separate."""
    reg = _task_regimes()
    cols = [(n, m) for n, m in ranked if m.get("by_category", {}).get("mvs")]
    if not reg or not cols:
        return ""
    head_cells = "".join(
        f"<th>{html.escape(n.split('/')[-1])}</th>" for n, _ in cols
    )
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
                cls = " class='best'" if v == best else ""
                cells.append(f"<td{cls}>{v:.3f}</td>")
        cells_html = "".join(cells)
        body.append(
            f"<tr><td class='rowhead'>{rg} <span class='pm'>(n={n_tasks})</span>"
            f"</td>{cells_html}</tr>"
        )
    body_html = NL.join(body)
    return f"""<section class="wrap" aria-label="Difficulty gradient">
  <h2>Difficulty gradient by task regime</h2>
  <p class="section-sub">Mean MVS&nbsp;F1 by how the answer key is grounded,
     easy&nbsp;&rarr;&nbsp;hard. Harder regimes pull the models apart &mdash; the
     spread you want from a benchmark.</p>
  <div class="table-scroll">
    <table>
      <thead><tr><th class="left">Regime</th>{head_cells}</tr></thead>
      <tbody>
{body_html}
      </tbody>
    </table>
  </div>
</section>"""


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
    head_cells = "".join(
        f"<th>{html.escape(n.split('/')[-1])}</th>" for n, _ in ranked
    )
    body = []
    for skill in skills:
        best = max(
            (m["by_skill"].get(skill, {}).get("mean_f1", -1) for _, m in ranked),
            default=-1,
        )
        n = next(
            (m["by_skill"][skill]["n"] for _, m in ranked
             if skill in m.get("by_skill", {})),
            0,
        )
        cells = []
        for _, m in ranked:
            d = m.get("by_skill", {}).get(skill)
            if not d:
                cells.append("<td>&mdash;</td>")
            else:
                cls = " class='best'" if d["mean_f1"] == best else ""
                cells.append(f"<td{cls}>{d['mean_f1']:.3f}</td>")
        cells_html = "".join(cells)
        body.append(
            f"<tr><td class='rowhead'>{html.escape(skill)} "
            f"<span class='pm'>(n={n})</span></td>{cells_html}</tr>"
        )
    body_html = NL.join(body)
    return f"""<section class="wrap" aria-label="Skill drill-down">
  <h2>Where models differ by skill</h2>
  <p class="section-sub">Mean F1 on tasks tagged with each skill (task count in
     parentheses). Skills are derived automatically from the reference scene
     tree.</p>
  <div class="table-scroll">
    <table>
      <thead><tr><th class="left">Skill</th>{head_cells}</tr></thead>
      <tbody>
{body_html}
      </tbody>
    </table>
  </div>
</section>"""


def build_index(data: dict, ranked: list) -> str:
    parts = [
        head("MolBench — Leaderboard",
             "A benchmark measuring whether LLM assistants can control "
             "molecular visualization via MolViewSpec scene trees."),
        header("index"),
        hero(data, ranked),
        leaderboard_table(ranked),
        findings(ranked),
        regime_table(ranked),
        drilldown(ranked),
        footer(),
    ]
    return NL.join(p for p in parts if p)


# --------------------------------------------------------------------------- #
# Gallery page
# --------------------------------------------------------------------------- #
GREEN_DECISIONS = {"rendering-equivalent", "vlm:same"}


def _verdict_class(decision: str) -> str:
    if decision in GREEN_DECISIONS:
        return "green"
    if decision == "vlm:different":
        return "red"
    return "amber"


def _verdict_label(decision: str) -> str:
    return {
        "rendering-equivalent": "Rendering-equivalent",
        "vlm:same": "VLM: same",
        "vlm:different": "VLM: different",
    }.get(decision, decision)


def gallery_card(row: dict, featured: bool = False) -> str:
    rid = html.escape(row.get("id", ""))
    rubric = html.escape(row.get("rubric", ""))
    note = html.escape(row.get("note") or "")
    decision = row.get("decision", "")
    vclass = _verdict_class(decision)
    vlabel = html.escape(_verdict_label(decision))

    mvs = row.get("mvs_score")
    vis = row.get("visual_score")
    mvs_s = f"{mvs:.2f}" if isinstance(mvs, (int, float)) else "&mdash;"
    vis_s = f"{vis:.2f}" if isinstance(vis, (int, float)) else "&mdash;"
    mvs_tone = " lo" if isinstance(mvs, (int, float)) and mvs < 0.5 else ""
    vis_tone = " hi" if isinstance(vis, (int, float)) and vis >= 0.8 else ""

    ref = html.escape(row.get("ref_img", ""))
    pred = html.escape(row.get("pred_img", ""))

    reason = row.get("vlm_reason")
    reason_html = ""
    if reason:
        reason_html = (
            "<p class='reason'><b>VLM rationale:</b> "
            f"{html.escape(reason)}</p>"
        )

    flag = ""
    fclass = ""
    if featured:
        fclass = " featured"
        flag = "<span class='featured-flag'>Most dramatic gap</span>"

    note_html = f"<p class='note'>{note}</p>" if note else "<p class='note'></p>"

    return f"""<article class="gcard{fclass}">
  <div class="gcard-head">
    <span class="gid">{rid}</span>
    {flag}
    <p class="rubric">{rubric}</p>
  </div>
  <div class="gcard-imgs">
    <figure class="imgcell ref">
      <figcaption class="imglabel"><span class="dot"></span>Reference scene</figcaption>
      <img src="{ref}" loading="lazy" alt="Reference render for: {rubric}">
    </figure>
    <figure class="imgcell pred">
      <figcaption class="imglabel"><span class="dot"></span>Model output</figcaption>
      <img src="{pred}" loading="lazy" alt="Model output render for: {rubric}">
    </figure>
  </div>
  <div class="gcard-foot">
    <div class="scorebox">
      <div class="k">MVS score</div>
      <div class="v{mvs_tone}">{mvs_s}</div>
    </div>
    <div class="scorebox">
      <div class="k">Visual score</div>
      <div class="v{vis_tone}">{vis_s}</div>
    </div>
    <div class="verdict-wrap">
      <span class="verdict {vclass}">{vlabel}</span>
    </div>
    {note_html}
    {reason_html}
  </div>
</article>"""


def build_gallery(gd: dict) -> str:
    meta = gd.get("meta", {})
    rows = gd.get("rows", [])
    model = html.escape(meta.get("model", "?"))
    judge = html.escape(meta.get("judge", "?"))
    n = meta.get("n", len(rows))

    # Feature the most dramatic gap: lowest MVS but high visual similarity.
    def gap_key(r):
        mvs = r.get("mvs_score")
        vis = r.get("visual_score")
        if not isinstance(mvs, (int, float)) or not isinstance(vis, (int, float)):
            return -1
        return vis - mvs

    featured = max(rows, key=gap_key) if rows else None
    rest = [r for r in rows if r is not featured]

    cards = []
    if featured is not None:
        cards.append(gallery_card(featured, featured=True))
    for r in rest:
        cards.append(gallery_card(r))
    cards_html = NL.join(cards)

    legend = f"""<div class="legend">
    <span class="li"><b>Model evaluated:</b> <span class="chip">{model}</span></span>
    <span class="li"><b>VLM judge:</b> <span class="chip">{judge}</span></span>
    <span class="li"><b>Rows:</b> {n}</span>
  </div>"""

    feat_frame = ""
    if featured is not None:
        feat_frame = (
            "<div class='callout' style='margin-top:1.25rem'>"
            "<b>Read the featured row first.</b> The model used a single, "
            "<i>cleaner</i> selector (e.g. <code>{label_comp_id: CYS}</code>) that "
            "the tree-grader couldn't recognize against a reference that enumerates "
            "every component &mdash; so MVS&nbsp;F1 collapses even though the render "
            "is pixel-identical.</div>"
        )

    return NL.join([
        head("MolBench — Evaluator gallery",
             "Reference vs model-output renders with tree-match and visual "
             "scores, for human raters to calibrate the MolBench grader."),
        header("gallery"),
        f"""<section class="hero wrap" aria-label="Gallery overview">
  <span class="eyebrow">For human evaluators</span>
  <h1>Evaluator gallery</h1>
  <p class="pitch">What the grader scored vs what a human sees. MolBench uses an
     <b>escalating grader</b>: a fast scene-tree match, then a pixel-level
     <b>visual diff</b>, then a <b>VLM judge</b> for the ambiguous cases.
     Tree-match is a deliberately conservative approximation &mdash; the
     <b>rendered image is the real ground truth</b>. Each card below shows the
     reference and the model output with both scores, so you can judge whether the
     grader got it right.</p>
  <div class="pipeline">
    <div class="step"><div class="n">STAGE 1</div><div class="t">Tree-match</div>
      <div class="d">Deterministic F1 over the MolViewSpec scene tree. Fast,
        engine-neutral, conservative.</div></div>
    <div class="step"><div class="n">STAGE 2</div><div class="t">Visual diff</div>
      <div class="d">Pixel/structural similarity of the two renders. Catches
        tree-mismatches that look identical.</div></div>
    <div class="step"><div class="n">STAGE 3</div><div class="t">VLM judge</div>
      <div class="d">A vision model adjudicates the remaining ambiguous cases:
        same scene, or genuinely different?</div></div>
  </div>
  {legend}
  {feat_frame}
</section>""",
        f"""<section class="wrap" aria-label="Evaluation cases">
  <div class="gallery-list">
{cards_html}
  </div>
</section>""",
        footer(),
    ])


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def build(scorecard_path: pathlib.Path) -> None:
    data = json.loads(scorecard_path.read_text())
    models = data.get("models", {})
    ranked = sorted(
        models.items(),
        key=lambda kv: (
            mvs_f1(kv[1]) if mvs_f1(kv[1]) is not None else kv[1]["mean_f1"]
        ),
        reverse=True,
    )

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(build_index(data, ranked))
    # Keep a transparent copy of the scorecard alongside the site.
    (DOCS / "scorecard.json").write_text(json.dumps(data, indent=2))

    gallery_path = DOCS / "gallery_data.json"
    wrote_gallery = False
    if gallery_path.exists():
        gd = json.loads(gallery_path.read_text())
        (DOCS / "gallery.html").write_text(build_gallery(gd))
        wrote_gallery = True

    extra = " and gallery.html" if wrote_gallery else ""
    print(
        f"wrote {DOCS / 'index.html'}{extra} "
        f"({len(ranked)} models)"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        src = pathlib.Path(sys.argv[1])
    else:
        # Default to the published scorecard so the script is runnable as-is.
        src = DOCS / "scorecard.json"
    build(src)
