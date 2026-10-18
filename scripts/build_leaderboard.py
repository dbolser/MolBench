#!/usr/bin/env python3
"""
Render the MolBench scorecard + gallery into a static site for GitHub Pages.

    python scripts/build_leaderboard.py [docs/scorecard.json]

Writes three self-contained pages that share ``docs/style.css`` (no JS, no CDN —
works fully offline):

  * ``docs/index.html``    — leaderboard, key findings, prompting conditions (2×2),
                             difficulty gradient, skill drill-down, tiered grading.
  * ``docs/failures.html`` — why each failing MVS sample scored 0 (outcome
                             breakdown, Mol* messages, every failing sample).
  * ``docs/gallery.html``  — the human-evaluator gallery (reference vs model
                             render, with tree-match + visual scores + verdict).

All numbers are read from ``docs/scorecard.json`` and the ``docs/*_data.json``
files written by ``scripts/build_site_data.py`` — nothing is hard-coded.
Publishing is therefore a deliberate, reviewable commit.

Python 3.10 compatible: no backslashes inside f-string expressions.
"""

from __future__ import annotations

import functools
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
GRADIENT = ["Translation", "Grounded (ligand/SS)", "Clinical (SIFTS/ClinVar)"]
# Regimes that test another skill, not a harder step on the gradient: shown below it, unordered.
OTHER_REGIMES = ["Resolution (by name)", "Interactions (atoms)"]
REGIMES = GRADIENT + OTHER_REGIMES
_SOURCE_REGIME = {
    "generated": "Translation", "curated": "Translation",
    "grounded": "Grounded (ligand/SS)",
    "clinvar-variant": "Clinical (SIFTS/ClinVar)", "clinvar-hotspots": "Clinical (SIFTS/ClinVar)",
    "sifts-named": "Clinical (SIFTS/ClinVar)",
    "resolve": "Resolution (by name)",
    "interactions": "Interactions (atoms)",
}


OUTCOME_LABELS = {
    "valid": "valid scene", "invalid_json": "invalid JSON", "not_mvs": "not an MVS tree",
    "invalid_mvs": "invalid MVS", "load_failed": "failed to load",
}


# --------------------------------------------------------------------------- #
# Data helpers
# --------------------------------------------------------------------------- #
def _regime_of(source: str) -> str:
    # Explicit, so a new task source can't silently land in another regime's numbers.
    if source not in _SOURCE_REGIME:
        raise ValueError(f"task source {source!r} has no regime; add it to _SOURCE_REGIME")
    return _SOURCE_REGIME[source]


@functools.lru_cache(maxsize=1)
def _task_regimes() -> dict[str, str]:
    # Scans + parses every task file; memoised so the several call sites
    # (findings, regime_table) share one pass per build.
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


def has_mvs(m: dict) -> bool:
    return mvs_f1(m) is not None


def slug(name: str) -> str:
    return name.replace("/", "_")


def short(name: str) -> str:
    return name.split("/")[-1]


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
      <a href="failures.html" class="{cls('failures')}">Failures</a>
      <a href="gallery.html" class="{cls('gallery')}">Evaluator gallery</a>
      <a href="https://github.com/dbolser/MolBench" class="gh"
         rel="noopener">GitHub</a>
    </nav>
  </div>
</header>"""


def footer() -> str:
    repro = (
        "python -m molbench.runner --models &lt;spec&gt; --categories mvs --validate "
        "--escalate --judge claude-opus-4-8"
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
    meta = data.get("meta", {})
    mt = meta.get("mvs_track", {})
    at = meta.get("api_track", {})
    llms = [(n, m) for n, m in ranked if has_mvs(m) and m.get("spec") != "baseline"]

    leader_name, leader_m = ranked[0]
    leader_f1 = mvs_f1(leader_m)

    # Best open-weight model by MVS F1, and its cost.
    open_models = [(n, m) for n, m in llms if is_open(n)]
    best_open = open_models[0] if open_models else None

    stats = []
    stats.append(("LLMs evaluated", f"{len(llms)}", "open &amp; closed"))
    stats.append(
        ("Benchmark tasks", f"{mt.get('n_tasks', '?')}&thinsp;+&thinsp;{at.get('n_tasks', '?')}",
         f"MVS &times;{mt.get('samples', 1)} &middot; API &times;{at.get('samples', '?')}"))

    stats.append(
        ("MVS&nbsp;F1 leader", f"{leader_f1:.2f}",
         html.escape(short(leader_name))))

    if best_open is not None and best_open[0] != leader_name:
        bo_name, bo_m = best_open
        bo_cost = bo_m.get("cost_usd")
        cost_note = html.escape(short(bo_name))
        if isinstance(bo_cost, (int, float)):
            cost_note += f" at {fmt_cost(bo_cost)}"
        stats.append(("Top open model", f"{mvs_f1(bo_m):.2f}", cost_note))
    else:
        valid = [m["valid_scene"] for _, m in llms if m.get("valid_scene") is not None]
        stats.append(("Median valid scenes", fmt_pct(statistics.median(valid)) if valid else "&mdash;",
                      "Mol* accepts the scene"))

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
  <p class="pitch">Can LLM assistants turn natural-language requests &mdash;
     <i>&ldquo;show the heme as orange ball-and-stick&rdquo;</i>,
     <i>&ldquo;superpose the subunits and hide the waters&rdquo;</i> &mdash; into
     correct molecular visualizations? MolBench measures <b>two distinct
     skills</b>: <b>authoring</b> a declarative <b>MolViewSpec</b> scene (<i>what
     the picture is</i>) and <b>controlling</b> a live <b>Mol*</b> viewer through
     imperative API calls (<i>what the tool does</i>). Both are graded
     deterministically against frozen, correct-by-construction answers.</p>
  <div class="stats">
{cards_html}
  </div>
</section>"""


def _valid_cell(name: str, m: dict) -> str:
    """Valid-scene % with the outcome breakdown as a tooltip, linked to the details."""
    vs = m.get("valid_scene")
    oc = m.get("outcomes")
    if vs is None or not oc:
        return "&mdash;"
    tip = html.escape(" · ".join(f"{OUTCOME_LABELS[o]}: {n}" for o, n in oc.items() if n))
    anchor = "spec" if m.get("spec") == "baseline" else f"spec-{slug(name)}"
    return f"<a href='failures.html#{anchor}' title='{tip}'>{fmt_pct(vs)}</a>"


def leaderboard_table(data: dict, ranked: list) -> str:
    meta = data.get("meta", {})
    leader_name = ranked[0][0]
    rows = []
    rank = 0
    notes: dict[str, int] = {}

    def mark(text: str) -> str:
        notes.setdefault(text, len(notes) + 1)
        return f"<sup>{notes[text]}</sup>"

    for name, m in ranked:
        scored = has_mvs(m)
        if scored:
            rank += 1
        leader_cls = " class='leader'" if name == leader_name else ""
        open_badge = (
            "<span class='badge open'>open</span>" if is_open(name)
            else "<span class='badge closed'>closed</span>"
        )
        sup = ""
        if m.get("route_note"):
            sup = mark("Ran via OpenRouter in October (the July API-track result used the "
                       "provider's native API). Treated as the same model.")
        if m.get("mvs_not_run"):
            sup = mark("Not re-run in October: OpenRouter's upstream (Mistral) rate-limited "
                       "every attempt (11 tries). MVS columns blank; API track from July.")
        spec = m.get("spec", "")
        spec_line = ""
        if spec and spec != "baseline":
            spec_line = f"<span class='spec'>{html.escape(spec)}</span>"
        rows.append(
            f"<tr{leader_cls}>"
            f"<td class='rank'>{rank if scored else '&mdash;'}</td>"
            f"<td class='model'>{html.escape(name)}{sup}{open_badge}{spec_line}</td>"
            f"<td class='metric-primary'>{track_cell(m, 'mvs')}</td>"
            f"<td>{fmt_f1(m.get('validated_f1'))}</td>"
            f"<td>{_valid_cell(name, m)}</td>"
            f"<td>{fmt_f1(m.get('cond_f1')) if scored else '&mdash;'}</td>"
            f"<td>{track_cell(m, 'api_calling')}</td>"
            f"<td>{fmt_cost(m.get('cost_usd'))}</td>"
            f"<td>{fmt_speed(m)}</td>"
            "</tr>"
        )
    rows_html = NL.join(rows)
    notes_html = " ".join(f"<sup>{i}</sup>&nbsp;{html.escape(t)}" for t, i in notes.items())
    mt = meta.get("mvs_track", {})
    at = meta.get("api_track", {})
    api_when = (at.get("run") or "")[:10]

    return f"""<section class="wrap" aria-label="Leaderboard">
  <h2>Leaderboard</h2>
  <p class="section-sub">Two tracks, two skills. <b>MVS&nbsp;F1</b> (the primary
     ranking) scores <i>scene authoring</i> &mdash; the declarative MolViewSpec
     tree a model emits, matched against the reference by the atoms each selection
     picks out. A scene scores 0 unless Mol* would show it.
     <b>API&nbsp;F1</b> scores <i>tool control</i> &mdash; the imperative
     Mol*/PDBeMolstar calls that drive a live viewer (superpose, hide waters, spin,
     focus), the operations a static scene cannot express. The leader is
     highlighted; open-weight models are namespaced with a provider slash.</p>
  <div class="table-scroll">
    <table>
      <thead>
        <tr>
          <th class="left">#</th>
          <th class="left">Model</th>
          <th>MVS&nbsp;F1</th>
          <th>Validated&nbsp;F1</th>
          <th>Valid&nbsp;scene</th>
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
    <b>MVS&nbsp;F1</b>: primary scene-authoring score, {mt.get('n_tasks', '?')} tasks,
    {mt.get('samples', 1)} sample each, run {html.escape(mt.get('run', '?'))}.
    Engine-neutral <i>by design</i> &mdash; though Mol* is currently the only viewer
    that implements MolViewSpec. <b>Validated&nbsp;F1</b>: the same scenes after the
    render-and-judge cascade (see <a href="#tiered">Tiered grading</a>).
    <b>Valid&nbsp;scene</b>: share of samples Mol* accepts and renders; the rest are
    invalid JSON, invalid MVS or failed to load, and score 0 &mdash; hover for the
    breakdown, click for <a href="failures.html">every failing sample</a>.
    <b>Cond&nbsp;F1</b>: scene quality over valid scenes only &mdash; the gap from
    MVS&nbsp;F1 is how much a model loses to broken output rather than to
    visualization error. <b>API&nbsp;F1</b>: the tool-control track, not re-run in
    October: these are the {api_when} results ({at.get('n_tasks', '?')} tasks,
    &times;{at.get('samples', '?')} samples, same grader). <b>Cost</b>: the October
    MVS run at provider list prices (&mdash; = not reported). <b>Speed</b>: seconds
    per call from the July run (October timings include rendering).
    <span class="pm">&plusmn;</span> is the spread across tasks.
  </p>
  <p class="section-sub" style="font-size:.85rem">{notes_html}</p>
</section>"""


def findings(ranked: list, cond: dict | None = None) -> str:
    """Key-findings cards, with numbers pulled live from the scorecard."""
    # The findings narrative is about the LLMs; the non-LLM rules baseline
    # (spec == "baseline") is a reference floor, not a competitor, and a model with
    # no MVS run has nothing to say here.
    llms = [(n, m) for n, m in ranked if m.get("spec") != "baseline" and has_mvs(m)]

    # Conditional-F1 cluster bounds (LLMs that produced valid scenes).
    cond_vals = [m["cond_f1"] for _, m in llms if m.get("cond_f1") and m.get("valid_scene")]
    cond_lo = min(cond_vals) if cond_vals else 0.0
    cond_hi = max(cond_vals) if cond_vals else 0.0

    # Unconditional MVS spread across the LLMs, and how well validity alone predicts it.
    mvs_vals = [mvs_f1(m) for _, m in llms]
    mvs_spread = (max(mvs_vals) - min(mvs_vals)) if mvs_vals else 0.0
    pairs = [(m["valid_scene"], mvs_f1(m)) for _, m in llms if m.get("valid_scene") is not None]
    corr = (statistics.correlation(*zip(*pairs)) if len(pairs) > 2 else None)

    # Why the failures fail: invalid JSON vs a parsed scene Mol* rejects.
    tot = {o: sum((m.get("outcomes") or {}).get(o, 0) for _, m in llms) for o in OUTCOME_LABELS}
    n_fail = sum(v for o, v in tot.items() if o != "valid")

    # Format-unreliability exemplar: the LLM with the lowest overall MVS F1,
    # chosen dynamically so this finding can never contradict the table. The point
    # is the *gap* between its conditional competence and its unconditional score.
    ex_name, ex_m = min(llms, key=lambda nm: mvs_f1(nm[1]), default=(None, None))

    cond_lo_s = f"{cond_lo:.2f}"
    cond_hi_s = f"{cond_hi:.2f}"
    mvs_spread_s = f"{mvs_spread:.2f}"

    ex_p = ""
    if ex_name and ex_m.get("cond_f1") is not None:
        oc = ex_m.get("outcomes") or {}
        ex_p = (f"<p><code>{html.escape(ex_name)}</code> is <b>last among the LLMs</b> "
                f"(~{mvs_f1(ex_m):.2f} MVS&nbsp;F1) yet scores ~{ex_m['cond_f1']:.2f} "
                "Cond&nbsp;F1 &mdash; competent when its scene is valid, but it usually "
                f"isn&rsquo;t (valid scene {fmt_pct(ex_m.get('valid_scene'))}; "
                f"{oc.get('invalid_json', 0)} of {sum(oc.values())} samples are invalid "
                "JSON).</p>")
    corr_s = (f" Valid-scene rate alone correlates with MVS&nbsp;F1 at "
              f"<b>r&nbsp;=&nbsp;{corr:.3f}</b>." if corr is not None else "")
    split_s = ""
    if n_fail:
        split_s = (f" Of the {n_fail} failed samples, <b>{tot['invalid_json']}</b> are "
                   f"invalid JSON and {tot['invalid_mvs']} are JSON that Mol* rejects as "
                   f"MVS ({tot['load_failed']} more failed to load) &mdash; "
                   "<a href='failures.html'>details</a>.")
    f1 = (
        "<div class='finding headline'>"
        "<div class='fnum'>FINDING 01 &middot; THE HEADLINE</div>"
        "<h3>Output validity, not competence, drives the ranking</h3>"
        "<p>The MVS ranking is largely a <b>valid-output</b> ranking. Over valid "
        f"scenes, every LLM clusters at <b>{cond_lo_s}&ndash;{cond_hi_s}</b> Cond&nbsp;F1 "
        f"&mdash; yet the unconditional spread is ~<b>{mvs_spread_s}</b>.{corr_s}"
        f"{split_s}</p>"
        + ex_p +
        "</div>"
    )

    # Finding 02: open vs closed, computed.
    opens = [(n, m) for n, m in llms if is_open(n)]
    closeds = [(n, m) for n, m in llms if not is_open(n)]
    f2 = ""
    if opens and closeds:
        (on, om), (cn, cm) = opens[0], closeds[0]
        verb = "beats" if mvs_f1(om) > mvs_f1(cm) else "trails"
        cost_s = ""
        oc_, cc_ = om.get("cost_usd"), cm.get("cost_usd")
        if isinstance(oc_, (int, float)) and isinstance(cc_, (int, float)) and oc_ > 0:
            cost_s = (f" at <b>{cc_ / oc_:.0f}&times; lower cost</b> ({fmt_cost(oc_)} vs "
                      f"{fmt_cost(cc_)} for the run)")
        tail = ", ".join(f"{html.escape(short(n))} ({mvs_f1(m):.2f})" for n, m in opens[-2:])
        f2 = (
            "<div class='finding'>"
            "<div class='fnum'>FINDING 02</div>"
            "<h3>The best open model is at the closed frontier-small tier</h3>"
            f"<p>The top open model, <b>{html.escape(short(on))}</b> ({mvs_f1(om):.2f}), "
            f"{verb} the best closed model, {html.escape(short(cn))} ({mvs_f1(cm):.2f}){cost_s}. "
            f"But &ldquo;open&rdquo; spans a wide range: {tail} sit at the bottom, "
            "mostly on invalid output.</p>"
            "</div>"
        )

    # Finding 03: is the per-regime model spread actually growing with difficulty?
    # Compute it live — with a wider panel this can flip, because format-unreliable
    # models inject validity-driven spread that swamps the difficulty signal.
    regimes = _task_regimes()
    reg_order = GRADIENT
    reg_spread: dict[str, float] = {}
    for rg in reg_order:
        per = []
        for _, m in llms:
            fs = [t["f1"] for t in m.get("tasks", []) if regimes.get(t.get("id")) == rg]
            if fs:
                per.append(statistics.fmean(fs))
        if len(per) >= 2:
            reg_spread[rg] = max(per) - min(per)
    grows = (len(reg_spread) == 3
             and reg_spread[reg_order[0]] <= reg_spread[reg_order[1]] <= reg_spread[reg_order[2]])

    if grows:
        f3_head = "A difficulty gradient that discriminates"
        f3_body = ("Harder regimes separate models <b>more</b> &mdash; model spread "
                   f"grows from ~{reg_spread[reg_order[0]]:.2f} to "
                   f"~{reg_spread[reg_order[2]]:.2f} &mdash; exactly the property a "
                   "benchmark wants.")
    elif reg_spread:
        vals = list(reg_spread.values())
        f3_head = "Regime spread is dominated by output reliability"
        f3_body = ("Across regimes the model spread runs "
                   f"~{min(vals):.2f}&ndash;{max(vals):.2f}; in the expanded panel it "
                   "tracks <b>output validity</b> &mdash; a few models rarely emit a "
                   "valid scene &mdash; more than task difficulty.")
    else:
        f3_head = "A difficulty gradient that discriminates"
        f3_body = "Model performance separates across the three regimes."
    f3 = (
        "<div class='finding'>"
        "<div class='fnum'>FINDING 03</div>"
        f"<h3>{f3_head}</h3>"
        "<p>Tasks span translation &rarr; structure-grounded &rarr; clinical. "
        + f3_body +
        " See the per-regime table below.</p>"
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

    f5 = f6 = ""
    if cond:
        cs = conditions_summary(cond)
        if cs.get("n_models"):
            drop = cs["biggest_valid_drop"]
            f5 = (
                "<div class='finding'>"
                "<div class='fnum'>FINDING 05</div>"
                "<h3>Grounding dossiers don&rsquo;t lift scores</h3>"
                "<p>Adding a frozen fact sheet about each structure (chains, ligands, "
                f"numbering) changes MVS&nbsp;F1 by <b>{cs['mean_delta']:+.3f}</b> on "
                f"average across {cs['n_models']} models. On the {cs['pooled_n']} "
                "task&times;model pairs whose scene is valid in both runs the effect is "
                f"<b>{cs['pooled_delta']:+.3f}</b>. The drop comes from more invalid "
                "output on the longer prompt, worst for "
                f"{html.escape(short(drop[0]))} (valid scenes {fmt_pct(drop[1])} &rarr; "
                f"{fmt_pct(drop[2])}). <a href='#conditions'>The 2&times;2 &darr;</a></p>"
                "</div>"
            )
        if cs.get("bare_n"):
            f6 = (
                "<div class='finding'>"
                "<div class='fnum'>FINDING 06</div>"
                "<h3>Without the MVS reference, no model writes a valid scene</h3>"
                f"<p>With only the output contract (&ldquo;bare&rdquo;), "
                f"<b>{cs['bare_valid']} of {cs['bare_n']}</b> scenes are valid across "
                f"{cs['bare_models']} models, with or without a dossier. Mostly the JSON "
                "parses but Mol* rejects it &mdash; parameters written straight onto the "
                "node instead of under <code>params</code>. Models don&rsquo;t know MVS "
                "from pretraining.</p>"
                "</div>"
            )

    cards = NL.join(c for c in (f1, f2, f3, f4, f5, f6) if c)
    return f"""<section class="wrap" aria-label="Key findings">
  <h2>Key findings</h2>
  <p class="section-sub">What the leaderboard actually tells you &mdash; read
     these before the table.</p>
  <div class="findings">
{cards}
  </div>
</section>"""


def conditions_summary(cond: dict) -> dict:
    """Headline numbers of the 2×2, from ``conditions_data.json``."""
    rows = cond.get("models", {})
    paired = {n: r for n, r in rows.items() if "dossier" in r}
    s = cond.get("summary", {})
    out: dict = {"n_models": len(paired), "mean_delta": s.get("mean_delta"),
                 "pooled_n": s.get("pooled_both_valid", {}).get("n"),
                 "pooled_delta": s.get("pooled_both_valid", {}).get("delta"),
                 "pooled": s.get("pooled_both_valid", {}),
                 "mean_lookup_delta": s.get("mean_lookup_delta"),
                 "n_lookup": cond.get("n_lookup_tasks")}
    if paired:
        n = max(paired, key=lambda k: (paired[k]["spec"]["valid_scene"]
                                       - paired[k]["spec_grounded"]["valid_scene"], k))
        out["biggest_valid_drop"] = (n, paired[n]["spec"]["valid_scene"],
                                     paired[n]["spec_grounded"]["valid_scene"])
        out["lookup_gainers"] = sorted(
            ((k, r["dossier_lookup"]) for k, r in paired.items()
             if (r["dossier_lookup"]["delta"] or 0) >= 0.10),
            key=lambda kv: -kv[1]["delta"])
        out["lookup_losers"] = sum((r["dossier_lookup"]["delta"] or 0) <= -0.10
                                   for r in paired.values())
    bare = [r[c] for r in rows.values() for c in ("bare", "bare_grounded") if c in r]
    out["bare_models"] = sum("bare" in r for r in rows.values())
    out["bare_n"] = sum(sum(b["outcomes"].values()) for b in bare)
    out["bare_valid"] = sum(b["outcomes"]["valid"] for b in bare)
    return out


def _delta(v) -> str:
    return "&mdash;" if v is None else f"{v:+.3f}"


def conditions_section(cond: dict | None, ranked: list) -> str:
    if not cond or not cond.get("models"):
        return ""
    rows = cond["models"]
    cs = conditions_summary(cond)
    order = [n for n, _ in ranked if n in rows]
    body = []
    for n in order:
        r = rows[n]
        sp, gr = r["spec"], r.get("spec_grounded")
        if not gr:
            continue
        d, dl = r["dossier"], r["dossier_lookup"]
        body.append(
            "<tr>"
            f"<td class='model' title='{html.escape(n)}'>{html.escape(short(n))}</td>"
            f"<td>{sp['mvs_f1']:.3f}</td><td>{gr['mvs_f1']:.3f}</td>"
            f"<td class='metric-primary'>{_delta(d['delta'])}</td>"
            f"<td><a href='failures.html#spec-{slug(n)}'>{fmt_pct(sp['valid_scene'])}</a></td>"
            f"<td><a href='failures.html#spec_grounded-{slug(n)}'>{fmt_pct(gr['valid_scene'])}</a></td>"
            f"<td>{_delta(d['delta_both_valid'])} <span class='pm'>(n={d['n_both_valid']})</span></td>"
            f"<td>{_delta(dl['delta'])}</td>"
            "</tr>")
    bare = []
    for n in order:
        r = rows[n]
        if "bare" not in r:
            continue
        cells = "".join(
            f"<td>{fmt_pct(r[c]['valid_scene'])}</td><td>{r[c]['mvs_f1']:.3f}</td>"
            if c in r else "<td>&mdash;</td><td>&mdash;</td>"
            for c in ("spec", "bare", "bare_grounded"))
        bare.append(f"<tr><td class='model' title='{html.escape(n)}'>{html.escape(short(n))}</td>"
                    f"{cells}</tr>")
    body_html, bare_html = NL.join(body), NL.join(bare)

    pooled = cs["pooled"]
    gainers = cs.get("lookup_gainers", [])
    if gainers:
        names = ", ".join(
            f"{html.escape(short(k))} ({v['delta']:+.2f}; {_delta(v['delta_both_valid'])} "
            f"on the {v['n_both_valid']} valid in both)" for k, v in gainers)
        trigger = (f"{len(gainers)} model{'s' if len(gainers) > 1 else ''} pass +0.10 there "
                   f"&mdash; {names} &mdash; and {cs['lookup_losers']} lose as much. With "
                   f"{cs['n_lookup']} tasks and one sample, one task flipping between invalid "
                   f"and valid moves the mean by ~{0.7 / cs['n_lookup']:.2f}; the gains come "
                   "from such flips, not from better answers.")
    else:
        trigger = "No model gains +0.10 there."
    drop = cs["biggest_valid_drop"]
    return f"""<section class="wrap" aria-label="Prompting conditions" id="conditions">
  <h2>Prompting conditions (the 2&times;2)</h2>
  <p class="section-sub">Every model above ran with the <b>spec</b> prompt: the output
     contract plus a neutral MolViewSpec reference. We also ran it with a
     <b>dossier</b> &mdash; a grounding pack of facts about the task&rsquo;s structure
     (chains, residue ranges, ligand codes and atom names, SIFTS/UniProt numbering,
     ClinVar positions), built offline and frozen with the task. And a <b>bare</b>
     prompt, the output contract only, on three models. {cond.get('n_tasks', '?')}
     MVS tasks, {cond.get('samples', 1)} sample, run {html.escape(cond.get('run', '?'))}.</p>
  <div class="callout">
    <b>Dossiers don&rsquo;t help.</b> Mean change in MVS&nbsp;F1: {_delta(cs['mean_delta'])}
    over {cs['n_models']} models. On the {pooled.get('n')} task&times;model pairs valid in
    both runs: {_delta(pooled.get('delta'))} ({pooled.get('better')} better,
    {pooled.get('worse')} worse, {pooled.get('same')} unchanged). The overall drop is
    more invalid output on the longer prompt (worst:
    {html.escape(short(drop[0]))}, valid scenes {fmt_pct(drop[1])} &rarr; {fmt_pct(drop[2])}).
    On the {cs['n_lookup']} lookup-heavy tasks (clinical and resolve-by-name) the mean
    change is {_delta(cs['mean_lookup_delta'])}. {trigger}
    <b>Bare:</b> {cs['bare_valid']} valid scenes of {cs['bare_n']}.
  </div>
  <div class="table-scroll" style="margin-top:1.5rem">
    <table class="matrix">
      <thead>
        <tr>
          <th class="left">Model</th>
          <th>Spec&nbsp;F1</th>
          <th>+Dossier&nbsp;F1</th>
          <th>&Delta;</th>
          <th>Valid (spec)</th>
          <th>Valid (+dossier)</th>
          <th>&Delta; valid in both</th>
          <th>&Delta; lookup tasks</th>
        </tr>
      </thead>
      <tbody>
{body_html}
      </tbody>
    </table>
  </div>
  <p class="section-sub" style="margin-top:1rem;font-size:.85rem">
     <b>&Delta;</b> = dossier &minus; spec, MVS&nbsp;F1 (tree match, no rendering).
     <b>&Delta; valid in both</b>: mean paired change over the tasks whose scene Mol*
     accepts in both runs (n tasks). <b>&Delta; lookup tasks</b>: all
     {cs['n_lookup']} clinical and resolve-by-name tasks, valid or not.</p>
  <h3 style="margin-top:2rem">Bare prompt (no MVS reference)</h3>
  <div class="table-scroll">
    <table class="matrix">
      <thead>
        <tr>
          <th class="left">Model</th>
          <th>Valid (spec)</th><th>F1 (spec)</th>
          <th>Valid (bare)</th><th>F1 (bare)</th>
          <th>Valid (bare+dossier)</th><th>F1 (bare+dossier)</th>
        </tr>
      </thead>
      <tbody>
{bare_html}
      </tbody>
    </table>
  </div>
  <p class="section-sub" style="margin-top:1rem;font-size:.85rem">
     Bare scenes mostly parse as JSON but are invalid MVS &mdash; see the
     <a href="failures.html#messages">Mol* messages</a>. Without the reference, models
     don&rsquo;t know the MVS tree format.</p>
</section>"""


def _matrix(rows: list[tuple[str, dict]], cols: list[tuple[str, str]], value) -> str:
    """Models as rows, ``cols`` = [(key, header html)]; best value per column marked."""
    vals = {n: {k: value(m, k) for k, _ in cols} for n, m in rows}
    best = {k: max((v[k] for v in vals.values() if v[k] is not None), default=None)
            for k, _ in cols}
    head_cells = "".join(f"<th>{h}</th>" for _, h in cols)
    body = []
    for n, _ in rows:
        cells = []
        for k, _ in cols:
            v = vals[n][k]
            if v is None:
                cells.append("<td>&mdash;</td>")
            else:
                cls = " class='best'" if v == best[k] else ""
                cells.append(f"<td{cls}>{v:.3f}</td>")
        body.append(f"<tr><td class='model' title='{html.escape(n)}'>{html.escape(short(n))}</td>"
                    f"{''.join(cells)}</tr>")
    body_html = NL.join(body)
    return f"""  <div class="table-scroll">
    <table class="matrix">
      <thead><tr><th class="left">Model</th>{head_cells}</tr></thead>
      <tbody>
{body_html}
      </tbody>
    </table>
  </div>"""


def regime_table(ranked: list) -> str:
    """Mean F1 per difficulty regime — shows the gradient and where models separate."""
    reg = _task_regimes()
    rows = [(n, m) for n, m in ranked if has_mvs(m)]
    if not reg or not rows:
        return ""
    cols = []
    for rg in REGIMES:
        n_tasks = sum(1 for v in reg.values() if v == rg)
        ran = any(reg.get(t["id"]) == rg for _, m in rows for t in m["tasks"])
        if n_tasks and ran:
            other = " <span class='pm'>(other)</span>" if rg in OTHER_REGIMES else ""
            cols.append((rg, f"{html.escape(rg)}<br><span class='pm'>n={n_tasks}</span>{other}"))

    def value(m, rg):
        fs = [t["f1"] for t in m["tasks"] if reg.get(t["id"]) == rg]
        return statistics.fmean(fs) if fs else None

    other_note = (" Columns marked <i>other</i> test a different skill and are not "
                  "ordered by difficulty." if any(c in OTHER_REGIMES for c, _ in cols) else "")
    return f"""<section class="wrap" aria-label="Difficulty gradient">
  <h2>Difficulty gradient by task regime</h2>
  <p class="section-sub">Mean MVS&nbsp;F1 by how the answer key is grounded,
     easy&nbsp;&rarr;&nbsp;hard, left to right. Best per column highlighted.{other_note}</p>
{_matrix(rows, cols, value)}
</section>"""


def drilldown(ranked: list) -> str:
    """A model x skill matrix: 'on selection, model X beats Y'."""
    rows = [(n, m) for n, m in ranked if m.get("by_skill") and has_mvs(m)]
    skills = sorted({s for _, m in rows for s in m["by_skill"]})
    if not skills:
        return ""
    cols = []
    for skill in skills:
        n = next(m["by_skill"][skill]["n"] for _, m in rows if skill in m["by_skill"])
        cols.append((skill, f"{html.escape(skill)}<br><span class='pm'>n={n}</span>"))

    def value(m, skill):
        d = m["by_skill"].get(skill)
        return d["mean_f1"] if d else None

    return f"""<section class="wrap" aria-label="Skill drill-down">
  <h2>Where models differ by skill</h2>
  <p class="section-sub">Mean MVS&nbsp;F1 on tasks tagged with each skill (task count
     under the name). Skills are derived automatically from the reference scene
     tree.</p>
{_matrix(rows, cols, value)}
</section>"""


def tiered_grading(esc: dict | None) -> str:
    """Escalating (tiered) grader results across models, + a gallery link."""
    if not esc or not esc.get("models"):
        return ""
    models = esc["models"]
    prelim = bool(esc.get("preliminary"))
    badge = "<span class='badge open'>preliminary</span>" if prelim else ""
    gallery_url = esc.get("gallery_url", "gallery.html")
    judge = html.escape(esc.get("judge", ""))
    totals = esc.get("totals", {})
    n_models = totals.get("n_models", len(models))
    lift_lo = esc.get("lift_min", 0.0)
    lift_hi = esc.get("lift_max", 0.0)
    resc = totals.get("rescued", 0)
    escd = totals.get("escalated", 0)
    r_vis = totals.get("rescued_visual", 0)
    r_vlm = totals.get("rescued_vlm", 0)
    resc_pct = f"{(resc / escd * 100):.0f}%" if escd else "&mdash;"
    t1_rule = html.escape(esc.get("t1_rule", "near-identical renders"))

    cards = [
        ("Models analysed", f"{n_models}", f"spec run, {html.escape(esc.get('run', ''))}"),
        ("Imperfect valid scenes", f"{escd}", "rendered for a visual check"),
        ("Rescued", f"{resc} <span class='pm'>({resc_pct})</span>",
         f"{r_vis} pixel-identical &middot; {r_vlm} by the VLM"),
        ("Validated &minus; tree F1", f"+{lift_lo:.2f}&ndash;{lift_hi:.2f}",
         "range across models"),
    ]
    cards_html = NL.join(
        "<div class='stat'>"
        f"<div class='label'>{lab}</div>"
        f"<div class='value'>{val_}</div>"
        f"<div class='sub'>{sub}</div></div>"
        for lab, val_, sub in cards
    )

    ordered = sorted(models.items(), key=lambda kv: kv[1]["validated_f1"],
                     reverse=True)
    trows = []
    for name, s in ordered:
        open_badge = ("<span class='badge open'>open</span>" if is_open(name)
                      else "<span class='badge closed'>closed</span>")
        lift = s["validated_f1"] - s["tree_f1"]
        trows.append(
            "<tr>"
            f"<td class='model' title='{html.escape(name)}'>{html.escape(short(name))}"
            f"{open_badge}</td>"
            f"<td>{s['tree_f1']:.3f}</td>"
            f"<td class='metric-primary'>{s['validated_f1']:.3f}</td>"
            f"<td class='pm'>+{lift:.3f}</td>"
            f"<td>{s.get('perfect', 0)}</td>"
            f"<td>{s.get('escalated', 0)}</td>"
            f"<td>{s.get('rescued_visual', 0)}</td>"
            f"<td>{s.get('rescued_vlm', 0)}</td>"
            f"<td>{s.get('confirmed_different', 0)}</td>"
            f"<td>{s.get('failed', s.get('unparseable', 0))}</td>"
            "</tr>"
        )
    trows_html = NL.join(trows)

    return f"""<section class="wrap" aria-label="Tiered grading" id="tiered">
  <h2>Tiered grading {badge}</h2>
  <p class="section-sub">Tree-matching can under-credit a scene that renders the same
     through a different tree. The <b>escalating grader</b> renders each valid but
     imperfect scene and escalates only when needed: <b>tree-match &rarr; visual
     diff &rarr; VLM judge</b>. The visual diff rescues only near-identical renders
     ({t1_rule}), because a one-residue highlight changes just a few pixels. Across
     {n_models} models it confirmed {resc} of {escd} imperfect scenes ({resc_pct}) as
     the <i>right</i> scene &mdash; {r_vis} pixel-identical, {r_vlm} judged the same
     by the VLM. That moves validated F1 by only +{lift_lo:.2f} to
     +{lift_hi:.2f}: grading selections by the atoms they pick out already credits
     most equivalent namings.</p>
  <div class="stats">
{cards_html}
  </div>
  <div class="table-scroll" style="margin-top:1.5rem">
    <table class="matrix">
      <thead>
        <tr>
          <th class="left">Model</th>
          <th>Tree&nbsp;F1</th>
          <th>Validated&nbsp;F1</th>
          <th>&Delta;</th>
          <th>Perfect</th>
          <th>Escalated</th>
          <th>Pixel&nbsp;same</th>
          <th>VLM&nbsp;same</th>
          <th>Different</th>
          <th>Failed</th>
        </tr>
      </thead>
      <tbody>
{trows_html}
      </tbody>
    </table>
  </div>
  <p class="section-sub" style="margin-top:1rem;font-size:.85rem">
     <b>Validated&nbsp;F1</b> uses a <i>rescue-only</i> policy: a task scores 1.0
     when the cascade confirms it renders the reference scene, otherwise it keeps
     its tree-match score (the VLM gives a binary same/different, not a graded
     score). <b>Perfect</b>: tree match already 1.0, not rendered.
     <b>Escalated</b>: valid, imperfect scenes that were rendered. <b>Pixel same</b> /
     <b>VLM same</b>: rescued at the visual-diff / VLM tier. <b>Different</b>: the VLM
     saw a different scene. <b>Failed</b>: no valid scene, scores 0 (see
     <a href="failures.html">failures</a>). The VLM verdicts are not yet checked
     against human raters &mdash; see the side-by-side evidence in the
     <a href="{gallery_url}"><b>evaluator gallery &rarr;</b></a>. Judge: {judge}.</p>
</section>"""


def build_index(data: dict, ranked: list, esc: dict | None = None,
                banner: str | None = None, cond: dict | None = None) -> str:
    parts = [
        head("MolBench — Leaderboard",
             "A benchmark measuring whether LLM assistants can author declarative "
             "MolViewSpec molecular scenes and drive a live Mol* viewer through "
             "imperative API calls."),
        header("index"),
        banner or "",
        hero(data, ranked),
        leaderboard_table(data, ranked),
        findings(ranked, cond),
        conditions_section(cond, ranked),
        regime_table(ranked),
        drilldown(ranked),
        tiered_grading(esc),
        footer(),
    ]
    return NL.join(p for p in parts if p)


# --------------------------------------------------------------------------- #
# Failures page
# --------------------------------------------------------------------------- #
COND_LABELS = {
    "spec": "Spec (headline run)",
    "spec_grounded": "Spec + dossier",
    "bare": "Bare (no MVS reference)",
    "bare_grounded": "Bare + dossier",
}
RAW_SHOW = 4000
TREE_SHOW = 6000


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return html.escape(text)
    return (html.escape(text[:limit])
            + f"\n<span class='pm'>&hellip; {len(text) - limit:,} more characters; full "
              "text in <a href='failures_data.json'>failures_data.json</a></span>")


def _outcome_badge(o: str) -> str:
    return f"<span class='oc oc-{o}'>{html.escape(OUTCOME_LABELS.get(o, o))}</span>"


def _first_line(f: dict) -> str:
    if f.get("error"):
        return f["error"]
    if f.get("mvs_issues"):
        return " ".join(x.strip() for x in f["mvs_issues"][:2])
    if f.get("load_error"):
        return f["load_error"].splitlines()[0]
    return ""


def failure_item(f: dict, raw_missing: bool = False) -> str:
    o = f["outcome"]
    parts = [f"<p class='prompt'><b>Prompt:</b> {html.escape(f.get('prompt', ''))}</p>"]
    if o in ("invalid_json", "not_mvs"):
        parts.append(f"<p><b>Parser:</b> <code>{html.escape(f.get('error') or '')}</code></p>")
        raw = f.get("raw")
        if raw is None:
            parts.append("<p class='pm'>Raw model text was not archived for this run.</p>")
        elif not raw:
            parts.append("<p class='pm'>The model returned an empty response.</p>")
        else:
            parts.append(f"<details><summary>Raw model text ({len(raw):,} chars)</summary>"
                         f"<pre>{_clip(raw, RAW_SHOW)}</pre></details>")
    else:
        if o == "invalid_mvs":
            msgs = html.escape("\n".join(f.get("mvs_issues") or []))
            parts.append(f"<p><b>Mol* validator:</b></p><pre class='msgs'>{msgs}</pre>")
        if o == "load_failed":
            err = f.get("load_error") or ""
            head_, _, rest = err.partition("\n")
            parts.append(f"<p><b>Load error:</b> <code>{html.escape(head_)}</code></p>")
            if rest:
                parts.append(f"<details><summary>Stack trace</summary>"
                             f"<pre>{_clip(rest, RAW_SHOW)}</pre></details>")
        tree = json.dumps(f.get("predicted"), indent=1)
        parts.append(f"<details><summary>Predicted tree</summary>"
                     f"<pre>{_clip(tree, TREE_SHOW)}</pre></details>")
    summary = (f"<code>{html.escape(f['id'])}</code> {_outcome_badge(o)} "
               f"<span class='why'>{html.escape(_first_line(f)[:160])}</span>")
    return (f"<details class='fail'><summary>{summary}</summary>"
            f"<div class='fail-body'>{''.join(parts)}</div></details>")


def outcome_table(cond: str, per: dict, order: list[str]) -> str:
    rows = []
    for n in order:
        if n not in per:
            continue
        r = per[n]
        cells = []
        for o in OUTCOME_LABELS:
            v = r["outcomes"].get(o, 0)
            if "failures" in r and v and o != "valid":
                cells.append(f"<td><a href='#{cond}-{slug(n)}-{o}'>{v}</a></td>")
            else:
                cells.append(f"<td>{v if v else '<span class=pm>0</span>'}</td>")
        name = (f"<a href='#{cond}-{slug(n)}'>{html.escape(n)}</a>" if "failures" in r
                else html.escape(n))
        rows.append(f"<tr><td class='model'>{name}</td>{''.join(cells)}"
                    f"<td class='metric-primary'>{r['mvs_f1']:.3f}</td></tr>")
    heads = "".join(f"<th>{html.escape(l)}</th>" for l in OUTCOME_LABELS.values())
    return f"""<div class="table-scroll">
    <table>
      <thead><tr><th class="left">Model</th>{heads}<th>MVS&nbsp;F1</th></tr></thead>
      <tbody>
{NL.join(rows)}
      </tbody>
    </table>
  </div>"""


def messages_section(fd: dict) -> str:
    conds = [c for c in COND_LABELS if c in fd.get("conditions", {})]
    heads = "".join(f"<th>{html.escape(COND_LABELS[c].split(' (')[0])}</th>" for c in conds)
    rows = []
    for g in fd.get("mvs_messages", []):
        ex = "".join(f"<li><code>{html.escape(e['text'])}</code> <span class='pm'>&times;{e['n']}</span></li>"
                     for e in g["examples"])
        cells = "".join(f"<td>{g['counts'].get(c, 0) or '<span class=pm>0</span>'}</td>"
                        for c in conds)
        top = g["examples"][0] if g["examples"] else None
        top_html = (f"<div class='pm'>most often: <code>{html.escape(top['text'])}</code> "
                    f"&times;{top['n']}</div>" if top else "")
        rows.append(f"<tr><td class='left msg'><details><summary><code>{html.escape(g['pattern'])}"
                    f"</code>{top_html}</summary><ul>{ex}</ul></details></td>{cells}"
                    f"<td>{g['n_models']}</td></tr>")
    jrows = []
    for g in fd.get("json_errors", []):
        cells = "".join(f"<td>{g['counts'].get(c, 0) or '<span class=pm>0</span>'}</td>"
                        for c in conds)
        jrows.append(f"<tr><td class='left msg'><code>{html.escape(g['pattern'])}</code></td>{cells}</tr>")
    return f"""<section class="wrap" aria-label="Common messages" id="messages">
  <h2>Most common failure messages</h2>
  <p class="section-sub">Mol*&rsquo;s validator messages for <b>invalid MVS</b>,
     grouped with quoted names replaced by &ldquo;&hellip;&rdquo; (click a row for
     the concrete messages). Counts are issues, across all models; a scene can
     have several. Mol* stops at the first bad node, so one issue per scene is
     typical.</p>
  <div class="table-scroll">
    <table>
      <thead><tr><th class="left">Mol* message</th>{heads}<th>Models</th></tr></thead>
      <tbody>
{NL.join(rows)}
      </tbody>
    </table>
  </div>
  <p class="section-sub" style="margin-top:1.5rem">JSON parser errors for
     <b>invalid JSON</b>, with line/column positions removed. &ldquo;No JSON object
     found&rdquo; is usually an empty response.</p>
  <div class="table-scroll">
    <table>
      <thead><tr><th class="left">Parser error</th>{heads}</tr></thead>
      <tbody>
{NL.join(jrows)}
      </tbody>
    </table>
  </div>
</section>"""


def build_failures(fd: dict, order: list[str]) -> str:
    conds = fd.get("conditions", {})
    tables = []
    for c in COND_LABELS:
        if c not in conds:
            continue
        per = conds[c]
        link = any("failures" in r for r in per.values())
        names = [n for n in order if n in per] + sorted(set(per) - set(order))
        note = "" if link else (" <span class='pm'>(counts only: every scene fails the "
                                "same way; see the messages below)</span>")
        tables.append(f"<h3 id='{c}'>{html.escape(COND_LABELS[c])}{note}</h3>"
                      + outcome_table(c, per, names))
    lists = []
    for c in COND_LABELS:
        per = conds.get(c, {})
        names = [n for n in order if n in per and "failures" in per[n]]
        if not names:
            continue
        lists.append(f"<h2 id='{c}-samples'>Failing samples &middot; "
                     f"{html.escape(COND_LABELS[c])}</h2>")
        for n in names:
            r = per[n]
            nf = len(r["failures"])
            missing = (" <span class='pm'>Raw text not archived for this run.</span>"
                       if r.get("raw_missing") else "")
            blocks = [f"<h3 id='{c}-{slug(n)}'>{html.escape(n)} "
                      f"<span class='pm'>&middot; {nf} of {r['n']} failed &middot; "
                      f"{html.escape(COND_LABELS[c])}</span>{missing}</h3>"]
            if not nf:
                blocks.append("<p class='pm'>No failures.</p>")
            for o in OUTCOME_LABELS:
                fs = [f for f in r["failures"] if f["outcome"] == o]
                if not fs:
                    continue
                blocks.append(f"<h4 id='{c}-{slug(n)}-{o}'>{_outcome_badge(o)} "
                              f"<span class='pm'>{len(fs)}</span></h4>")
                blocks.extend(failure_item(f) for f in fs)
            lists.append(f"<div class='fail-model'>{NL.join(blocks)}</div>")
    explain = "".join(
        f"<li>{_outcome_badge(o)} {d}</li>" for o, d in (
            ("valid", "Mol* accepts and renders the scene; graded by tree match."),
            ("invalid_json", "the output does not parse as JSON (the parser error is shown)."),
            ("not_mvs", "valid JSON, but not an MVS tree (no <code>root</code> node)."),
            ("invalid_mvs", "an MVS-shaped tree that Mol*&rsquo;s own validator rejects "
                            "(its messages are shown)."),
            ("load_failed", "passes validation but Mol* fails to load or render it."),
        ))
    return NL.join([
        head("MolBench — Failure details",
             "Why each failing MolBench MVS sample scored zero: invalid JSON, invalid "
             "MVS, or a scene Mol* failed to load."),
        header("failures"),
        f"""<section class="hero wrap" aria-label="Failures overview">
  <span class="eyebrow">Every sample that scored 0</span>
  <h1>Failure details</h1>
  <p class="pitch">The leaderboard groups these as &ldquo;not a valid scene&rdquo;.
     Here they are apart. Each MVS sample gets one outcome; everything but a valid
     scene scores 0, because Mol* shows nothing for it. Run
     {html.escape(fd.get('run', '?'))}, 1 sample per task.</p>
  <ul class="oc-legend">{explain}</ul>
  <p class="section-sub">Jump to: <a href="#breakdown">outcome breakdown</a> &middot;
     <a href="#messages">common messages</a> &middot;
     <a href="#spec-samples">failing samples (spec)</a> &middot;
     <a href="#spec_grounded-samples">failing samples (spec + dossier)</a>.
     Full data: <a href="failures_data.json">failures_data.json</a>.</p>
</section>""",
        f"""<section class="wrap" aria-label="Outcome breakdown" id="breakdown">
  <h2>Outcome breakdown</h2>
  <p class="section-sub">Samples per outcome, per model and prompting condition
     (70 tasks each). Click a count to jump to those samples. The <b>spec</b> run is
     the leaderboard; the others are the <a href="index.html#conditions">2&times;2</a>.</p>
  {NL.join(tables)}
</section>""",
        messages_section(fd),
        f"""<section class="wrap" aria-label="Failing samples">
{NL.join(lists)}
</section>""",
        footer(),
    ])


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
    model_html = (f"<span class='gmodel'>{html.escape(row['model'])}</span>"
                  if row.get("model") else "")
    rubric = html.escape(row.get("rubric", ""))
    note = html.escape(row.get("note") or "")
    if isinstance(row.get("changed_pixels"), int):
        note += f" {row['changed_pixels']:,} pixels differ."
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
    {model_html}
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
    <span class="li"><b>Models:</b> <span class="chip">{model}</span></span>
    <span class="li"><b>VLM judge:</b> <span class="chip">{judge}</span></span>
    <span class="li"><b>Rows:</b> {n}</span>
  </div>"""

    feat_frame = ""
    if featured is not None and isinstance(featured.get("mvs_score"), (int, float)):
        how = {"rendering-equivalent": "renders pixel-identically to the reference",
               "vlm:same": "was judged the same scene by the VLM",
               "vlm:different": "was judged a different scene by the VLM"}.get(
                   featured.get("decision"), "was rendered and compared")
        feat_frame = (
            "<div class='callout' style='margin-top:1.25rem'>"
            "<b>Read the featured card first.</b> Its tree scored "
            f"{featured['mvs_score']:.2f} by tree match, yet the scene {how}. "
            "Do you agree? The VLM-judged cards are where a human check matters "
            "most: the VLM&rsquo;s verdicts have not yet been validated against "
            "human raters.</div>"
        )
    rule = meta.get("rule")
    if rule:
        feat_frame += (f"<p class='section-sub' style='margin-top:1rem;font-size:.85rem'>"
                       f"<b>How cards are picked:</b> {html.escape(rule)}</p>")

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
def rank_models(models: dict) -> list:
    """MVS F1 descending; models with no MVS run go last (by overall F1)."""
    return sorted(models.items(),
                  key=lambda kv: (has_mvs(kv[1]),
                                  mvs_f1(kv[1]) if has_mvs(kv[1]) else kv[1]["mean_f1"]),
                  reverse=True)


def _load(path: pathlib.Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def build(scorecard_path: pathlib.Path, out_dir: pathlib.Path = DOCS,
          banner: str | None = None) -> None:
    data = json.loads(scorecard_path.read_text())
    ranked = rank_models(data.get("models", {}))

    # Escalation / gallery / 2x2 / failures data live alongside the output (a staging
    # dir carries its own copies), so the page is self-contained wherever it is deployed.
    esc = _load(out_dir / "escalation_data.json")
    cond = _load(out_dir / "conditions_data.json")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(build_index(data, ranked, esc, banner=banner,
                                                    cond=cond))
    # Keep a transparent copy of the scorecard alongside the site.
    (out_dir / "scorecard.json").write_text(json.dumps(data, indent=2))

    wrote = ["index.html"]
    gd = _load(out_dir / "gallery_data.json")
    if gd:
        (out_dir / "gallery.html").write_text(build_gallery(gd))
        wrote.append("gallery.html")
    fd = _load(out_dir / "failures_data.json")
    if fd:
        (out_dir / "failures.html").write_text(build_failures(fd, [n for n, _ in ranked]))
        wrote.append("failures.html")
    print(f"wrote {', '.join(wrote)} to {out_dir} ({len(ranked)} models)")


# Amber notice injected at the top of a non-production build so a staging URL is
# never mistaken for the published leaderboard.
STAGING_BANNER = (
    '<div style="background:#b45309;color:#fff;text-align:center;'
    'padding:.6rem 1rem;font-weight:600;font-size:.9rem;letter-spacing:.01em">'
    '&#9888; STAGING PREVIEW &mdash; expanded 17-model panel under review; '
    'not the published leaderboard. '
    '<a href="../" style="color:#fff;text-decoration:underline">'
    '&larr; live leaderboard</a></div>'
)


if __name__ == "__main__":
    argv = sys.argv[1:]
    banner = STAGING_BANNER if "--staging" in argv else None
    argv = [a for a in argv if a != "--staging"]
    out_dir = DOCS
    if "--out-dir" in argv:
        i = argv.index("--out-dir")
        out_dir = pathlib.Path(argv[i + 1])
        del argv[i:i + 2]
    # Default to the published scorecard so the script is runnable as-is.
    src = pathlib.Path(argv[0]) if argv else DOCS / "scorecard.json"
    build(src, out_dir=out_dir, banner=banner)
