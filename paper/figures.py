#!/usr/bin/env python3
"""Figures of the paper that are not plots of a final run.

    uv run python paper/figures.py           # writes paper/generated/fig_*.svg
    uv run python paper/figures.py --check   # exit 1 if a committed schematic is stale

Four schematics are written as plain SVG by this script (pipeline, tiers, drawn-state
grading, paired design), so they are text, diff cleanly and need no drawing program. One
chart (the October predictions regraded) is drawn with matplotlib. Every number and every
request shown is read from ``paper/generated/values.json`` / ``corpus_values.json`` or from
the task files; nothing is typed here. Colours are the Okabe-Ito set (blue, orange, bluish
green), checked for colour-vision deficiency, and every coloured mark also has a label.
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import sys
import textwrap

PAPER = pathlib.Path(__file__).resolve().parent
REPO = PAPER.parent
GEN = PAPER / "generated"

BLUE, ORANGE, GREEN = "#0072B2", "#E69F00", "#009E73"
INK, MUTED, LINE, PALE, GREY = "#1a1a1a", "#555555", "#8a8a8a", "#f3f5f7", "#b8b8b8"
FONT = "Helvetica, Arial, sans-serif"


def values() -> dict:
    v = json.loads((GEN / "values.json").read_text(encoding="utf-8"))
    v.update(json.loads((GEN / "corpus_values.json").read_text(encoding="utf-8")))
    return v


# --------------------------------------------------------------------------- #
# A very small SVG writer
# --------------------------------------------------------------------------- #
class Svg:
    def __init__(self, w: int, h: int, title: str):
        self.w, self.h = w, h
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="{FONT}" role="img" aria-label="{html.escape(title, quote=True)}">',
            f"<title>{html.escape(title)}</title>",
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/>'
            "</marker></defs>",
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        ]

    def rect(self, x, y, w, h, fill=PALE, stroke=LINE, r=6, sw=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
                          f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=12, weight="normal", fill=INK, anchor="start", mono=False, italic=False):
        fam = ' font-family="DejaVu Sans Mono, Menlo, Consolas, monospace" xml:space="preserve"' if mono else ""
        it = ' font-style="italic"' if italic else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
                          f'text-anchor="{anchor}"{fam}{it}>{html.escape(str(s))}</text>')

    def para(self, x, y, s, width, size=11, lh=None, **kw) -> int:
        """Wrapped text; returns the y after the last line."""
        lh = lh or round(size * 1.3)
        for line in textwrap.wrap(str(s), width=width) or [""]:
            self.text(x, y, line, size=size, **kw)
            y += lh
        return y

    def arrow(self, x1, y1, x2, y2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTED}" '
                          f'stroke-width="1.4" marker-end="url(#arrow)"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=LINE, sw=1.0):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, x, y, r, fill, stroke="#ffffff", sw=1.5):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def raw(self, s):
        self.parts.append(s)

    def done(self) -> str:
        return "\n".join(self.parts + ["</svg>"]) + "\n"


# --------------------------------------------------------------------------- #
# Figure 1: pipeline
# --------------------------------------------------------------------------- #
def fig_pipeline(v: dict) -> str:
    s = Svg(980, 380, "How a MolBench task is built, answered and graded")
    boxes = [
        ("1  Frozen public data", [
            f"{v['panel.n']} structures (PDB and",
            "AlphaFold DB)",
            "residue mapping (SIFTS)",
            f"{v['variants.n_confirmed']:,} pathogenic variants",
            "confirmed in ClinVar"]),
        ("2  Generator scripts", [
            f"{v['corpus.n_templates']} templates",
            "request",
            "reference answer",
            "target atoms",
            "provenance record"]),
        ("3  Task corpus", [
            f"{v['corpus.n_tasks']} tasks, {v['corpus.n_tiers']} tiers",
            f"scene track: {v['corpus.mvs.n']}",
            f"call-list track: {v['corpus.api.n']}",
            f"{v['corpus.n_twin_pairs']} pairs (same request,",
            "both tracks)"]),
        ("4  Model", [
            "system prompt with the",
            "format reference",
            "+ the request",
            "one answer:",
            "scene or call list"]),
        ("5  Grader", [
            "resolve reference and",
            "answer to drawn state:",
            "per atom, how it is",
            "drawn and coloured",
            "(frozen atom tables)"]),
        ("6  Scores", [
            "F1 (graded)",
            "task success (exact)",
            "target score",
            "validity outcome",
            "strict / valid-only"]),
    ]
    w, h, gap, x0, y0 = 146, 150, 16, 12, 56
    s.text(x0, 28, "From public data to a score", size=15, weight="bold")
    s.text(x0, 44, "No step uses the network or a model at grading time.", size=11, fill=MUTED)
    for i, (title, lines) in enumerate(boxes):
        x = x0 + i * (w + gap)
        fill = "#e8f1f8" if i in (2, 5) else PALE
        s.rect(x, y0, w, h, fill=fill)
        s.text(x + 10, y0 + 22, title, size=12, weight="bold")
        y = y0 + 44
        for ln in lines:
            s.text(x + 10, y, ln, size=10.5)
            y += 17
        if i < len(boxes) - 1:
            s.arrow(x + w + 2, y0 + h / 2, x + w + gap - 2, y0 + h / 2)
    # checks band
    yb = y0 + h + 50
    s.text(x0, yb - 12, "Checks that do not depend on any model", size=12, weight="bold")
    checks = [
        ("Reference against structure (step 2)",
         "Each reference must select atoms, name the wild-type residue, and grade as exactly right against itself."),
        ("Atom tables against the viewer (step 5)",
         "Selections were read back from the real viewers (Mol* 5.9.0, pdbe-molstar 3.3.2) and agree atom for atom."),
        ("Grader against a control set (step 5)",
         f"{v['controls.n']:,} answer pairs with a verdict known from construction: "
         f"{v['controls.mvs.new.false_pass'] + v['controls.api.new.false_pass']} wrong answers passed, "
         f"{v['controls.mvs.new.false_fail'] + v['controls.api.new.false_fail']} right answers failed."),
        ("Held-back split (step 3)",
         f"{v['corpus.heldback.n_tasks']} tasks on {v['corpus.heldback.n_structures']} structures that no public task uses."),
    ]
    cw = (980 - 2 * x0 - 3 * gap) / 4
    for i, (title, body) in enumerate(checks):
        x = x0 + i * (cw + gap)
        s.rect(x, yb, cw, 112, fill="#ffffff", dash="4 3")
        s.text(x + 10, yb + 20, title, size=11.5, weight="bold")
        s.para(x + 10, yb + 38, body, width=37, size=10.5, fill=MUTED)
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 2: tiers
# --------------------------------------------------------------------------- #
TIER_CARDS = [
    ("translation", "Translation", "tr-het-code-3ert", "Everything is in the request."),
    ("grounded", "Structure-grounded", "gr-ligand-1stp-btn", "A named feature must be found in the structure."),
    ("interactions", "Interactions", "in-ca-distance-9fb2", "Named atoms and a measurement."),
    ("resolve", "Name resolution", "res-gene-p01112", "The protein is named; the entry is not."),
    ("clinical", "Clinical variant", "clin-short-target-lyz-2nwd-f75i-mvs", "UniProt numbering must be mapped to the structure."),
    ("followup", "Follow-up turn", "fu-referent-colour-5cj6-mvs", "A start state plus an edit."),
    ("accept_set", "Several right answers", "acc-residue-colour-4ins-mvs", "One countable thing is left open."),
    ("tool_only", "Viewer settings", "api-canvas-1udt", "Call-list track only."),
]


def fig_tiers(v: dict) -> str:
    prompts = {}
    for f in (REPO / "tasks").rglob("*.json"):
        t = json.loads(f.read_text(encoding="utf-8"))
        prompts[t.get("id")] = t
    s = Svg(980, 400, "The eight tiers of the benchmark, each with one request from the corpus")
    s.text(12, 28, "Eight tiers, one example request each", size=15, weight="bold")
    s.text(12, 44, "Counts are tasks on the scene track / the call-list track. Requests are quoted from the corpus.",
           size=11, fill=MUTED)
    cw, ch, gap = 230, 152, 12
    for i, (tier, name, tid, needs) in enumerate(TIER_CARDS):
        x = 12 + (i % 4) * (cw + gap)
        y = 60 + (i // 4) * (ch + gap)
        lookup = tier in ("resolve", "clinical")
        s.rect(x, y, cw, ch, fill="#e8f1f8" if lookup else PALE)
        s.text(x + 10, y + 22, name, size=12.5, weight="bold")
        n_m, n_a = v[f"corpus.mvs.{tier}.n"], v[f"corpus.api.{tier}.n"]
        s.text(x + cw - 10, y + 22, f"{n_m or '–'} / {n_a or '–'}", size=11.5, anchor="end", fill=MUTED)
        yy = s.para(x + 10, y + 42, needs, width=38, size=10.5, fill=MUTED)
        t = prompts[tid]
        prompt = " ".join(t["prompt"].split())
        if tier == "followup":
            prompt = "[start: a scene with one magenta chain] " + prompt
        if len(prompt) > 205:
            prompt = prompt[:202].rsplit(" ", 1)[0] + " …"
        s.para(x + 10, yy + 8, "“" + prompt + "”", width=38, size=10.5, italic=True)
    s.text(12, 60 + 2 * ch + gap + 18,
           "Shaded: lookup tiers, where the answer needs a fact that is not in the request and cannot be read off the format.",
           size=10.5, fill=MUTED)
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 3: drawn-state grading of the running example
# --------------------------------------------------------------------------- #
def fig_grading(v: dict) -> str:
    s = Svg(980, 520, "Drawn-state grading of the running example")
    right, wrong = v["ex.auth_number"], v["ex.uniprot_position"]
    s.text(12, 28, "Grading on drawn state: three answers to the running example", size=15, weight="bold")
    s.para(12, 46, "Request: “" + v["ex.prompt"] + "”", width=150, size=11, fill=MUTED, italic=True)
    panels = [
        ("Reference", f"{v['ex.wild_type']}{right} of chain {v['ex.auth_chain']} as green ball-and-stick. Nothing else.",
         right, False, "ex.mvs.right"),
        ("Answer A: number taken at face value",
         f"Author residue {wrong} drawn. It is {v['ex.face_value_residue']}{wrong}, another residue.",
         wrong, False, "ex.mvs.face"),
        ("Answer B: right residue, extra context",
         "The right residue, plus a grey cartoon of the whole protein that the request does not ask for.",
         right, True, "ex.mvs.context"),
    ]
    pw, ph, gap, y0 = 310, 418, 13, 86
    shown = [right - 1, right, right + 1, None, wrong - 1, wrong, wrong + 1]
    for i, (title, body, drawn, cartoon, key) in enumerate(panels):
        x = 12 + i * (pw + gap)
        s.rect(x, y0, pw, ph, fill="#ffffff")
        s.text(x + 12, y0 + 22, title, size=12.5, weight="bold")
        s.para(x + 12, y0 + 40, body, width=52, size=10.5, fill=MUTED)
        # residue strip
        ys = y0 + 150
        s.text(x + 12, ys - 52, "Chain " + v["ex.auth_chain"] + ", author residue numbers", size=10, fill=MUTED)
        bx = x + 16
        cells = []
        for r in shown:
            if r is None:
                s.text(bx + 14, ys + 5, "…", size=14, fill=MUTED, anchor="middle")
                bx += 28
                continue
            s.rect(bx, ys - 14, 36, 28, fill=PALE, r=3)
            s.text(bx + 18, ys + 4, r, size=10.5, anchor="middle")
            cells.append((r, bx + 18))
            bx += 40
        if cartoon:
            s.raw(f'<path d="M{x + 14},{ys + 30} C{x + 80},{ys + 18} {x + 150},{ys + 44} {x + 290},{ys + 28}" '
                  f'fill="none" stroke="{GREY}" stroke-width="7" stroke-linecap="round"/>')
            s.text(x + 292, ys + 50, "grey cartoon, all residues", size=10, fill=MUTED, anchor="end")
        for r, cx in cells:
            if r == drawn:
                s.line(cx, ys - 14, cx, ys - 30, stroke=GREEN, sw=3)
                s.circle(cx, ys - 34, 7, GREEN)
                far = cx > x + pw - 130
                s.text(cx - 12 if far else cx + 12, ys - 31, "green ball-and-stick", size=10, fill=INK,
                       anchor="end" if far else "start")
        # facts
        yf = ys + 76
        s.text(x + 12, yf, "Facts of the final state", size=11, weight="bold")
        if key == "ex.mvs.right":
            facts = [f"1 display class: {v['ex.n_target_atoms']} atoms of {v['ex.wild_type']}{right},",
                     "   green ball-and-stick"]
        elif key == "ex.mvs.face":
            facts = [f"1 display class: {v['ex.face_value_n_atoms']} atoms of {v['ex.face_value_residue']}{wrong},",
                     "   green ball-and-stick (no atom shared",
                     "   with the reference)"]
        else:
            facts = [f"class 1: {v['ex.wild_type']}{right}, grey cartoon and",
                     "   green ball-and-stick (half unrequested)",
                     "class 2: all other residues, grey cartoon",
                     "   (unrequested)"]
        for j, ln in enumerate(facts):
            s.text(x + 12, yf + 18 + j * 15, ln, size=10.5)
        # scores
        ysc = y0 + ph - 96
        s.line(x + 12, ysc - 14, x + pw - 12, ysc - 14)
        rows = [("Recall (reference facts present)", f"{v[key + '.recall']:.2f}"),
                ("Precision (answer facts requested)", f"{v[key + '.precision']:.2f}"),
                ("F1", f"{v[key + '.f1']:.2f}"),
                ("Task success", "yes" if v[key + ".success"] else "no"),
                ("Target score", f"{v[key + '.target']:.2f}")]
        for j, (k, val) in enumerate(rows):
            bold = "bold" if j >= 2 else "normal"
            s.text(x + 12, ysc + 4 + j * 18, k, size=11, weight=bold)
            s.text(x + pw - 12, ysc + 4 + j * 18, val, size=11, weight=bold, anchor="end")
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 4: paired design
# --------------------------------------------------------------------------- #
def fig_twins(v: dict) -> str:
    s = Svg(980, 500, "The paired design: one request, two output formats, the same target atoms")
    s.text(12, 28, "One request, two formats, the same target atoms", size=15, weight="bold")
    s.rect(190, 44, 600, 56, fill="#e8f1f8")
    s.text(490, 62, "Request (identical on both tracks)", size=11, weight="bold", anchor="middle")
    yy = 78
    for ln in textwrap.wrap("“" + v["ex.prompt"] + "”", width=100):
        s.text(490, yy, ln, size=10.5, anchor="middle", italic=True)
        yy += 14
    # two answers
    lx, rx, y, w, h = 12, 502, 132, 466, 170
    s.arrow(380, 102, 260, 130)
    s.arrow(600, 102, 720, 130)
    s.rect(lx, y, w, h)
    s.text(lx + 12, y + 22, "Scene track: a MolViewSpec scene (declarative)", size=12, weight="bold")
    scene = ["download  https://files.rcsb.org/download/2nwd.cif",
             "  parse  mmcif",
             "    structure  model",
             f"      component  auth_asym_id = {v['ex.auth_chain']}, auth_seq_id = {v['ex.auth_number']}",
             "        representation  ball_and_stick",
             f"          color  {v['ex.color']}"]
    for j, ln in enumerate(scene):
        s.text(lx + 14, y + 46 + j * 16, ln, size=10.5, mono=True)
    s.text(lx + 12, y + h - 12, f"The model must turn UniProt {v['ex.uniprot_position']} into author residue "
           f"{v['ex.auth_number']} itself.", size=10.5, fill=MUTED)
    s.rect(rx, y, w, h)
    s.text(rx + 12, y + 22, "Call-list track: PDBe Mol* viewer calls (imperative)", size=12, weight="bold")
    calls = ['load   molecule_id = "2nwd"',
             f'color  uniprot_accession = "{v["ex.accession"]}",',
             f'       uniprot_residue_number = {v["ex.uniprot_position"]},',
             '       representation = "ball-and-stick",',
             f'       representationColor = "{v["ex.color"]}"']
    for j, ln in enumerate(calls):
        s.text(rx + 14, y + 46 + j * 16, ln, size=10.5, mono=True)
    s.text(rx + 12, y + h - 12, "The viewer can do the mapping; the model must know the accession and the call.",
           size=10.5, fill=MUTED)
    # same atoms
    ty = y + h + 34
    s.arrow(lx + w / 2, y + h + 2, 400, ty - 2)
    s.arrow(rx + w / 2, y + h + 2, 580, ty - 2)
    s.rect(290, ty, 400, 44, fill="#e6f4ef", stroke=GREEN, sw=1.5)
    s.text(490, ty + 19, "Both references resolve to the same target atoms", size=11.5, weight="bold", anchor="middle")
    s.text(490, ty + 35, f"{v['ex.wild_type']}{v['ex.auth_number']}, chain {v['ex.auth_chain']} of {v['ex.entry']}: "
           f"{v['ex.n_target_atoms']} atoms (checked when the task is built)", size=10.5, anchor="middle", fill=MUTED)
    # 2x2
    gy = ty + 74
    s.arrow(490, ty + 46, 490, gy - 4)
    gx, cw, chh = 330, 150, 34
    s.text(gx - 12, gy + 14, f"Per model, over the {v['corpus.n_twin_pairs']} pairs:", size=11, anchor="end", weight="bold")
    s.text(gx - 12, gy + 30, "task success on each side", size=10.5, anchor="end", fill=MUTED)
    s.text(gx + cw / 2, gy - 6, "call list right", size=10.5, anchor="middle", fill=MUTED)
    s.text(gx + cw * 1.5, gy - 6, "call list wrong", size=10.5, anchor="middle", fill=MUTED)
    cells = [("both right", PALE, INK), ("format error (call list)", "#fdf0d5", INK),
             ("format error (scene)", "#fdf0d5", INK), ("both wrong: content", PALE, INK)]
    for k, (label, fill, ink) in enumerate(cells):
        cx, cy = gx + (k % 2) * cw, gy + (k // 2) * chh
        s.rect(cx, cy, cw, chh, fill=fill, r=0)
        s.text(cx + cw / 2, cy + 21, label, size=10.5, anchor="middle", fill=ink)
    s.text(gx + 2 * cw + 10, gy + 21, "scene right", size=10.5, fill=MUTED)
    s.text(gx + 2 * cw + 10, gy + chh + 21, "scene wrong", size=10.5, fill=MUTED)
    s.text(gx + cw, gy + 2 * chh + 20, "McNemar's test compares the two shaded (discordant) cells.",
           size=10.5, anchor="middle", fill=MUTED)
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 5: October predictions regraded (matplotlib)
# --------------------------------------------------------------------------- #
def fig_october(v: dict, out: pathlib.Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "molbench"
    matplotlib.rcParams["svg.fonttype"] = "none"
    matplotlib.rcParams["font.family"] = ["DejaVu Sans"]
    import matplotlib.pyplot as plt

    tiers = [("translation", "Translation"), ("grounded", "Structure-grounded,\nname resolution,\ninteractions"),
             ("clinical", "Clinical variant")]
    series = [("f1", "F1 (whole final state)", BLUE, ""),
              ("success", "Task success (final state exactly right)", ORANGE, "//"),
              ("highlight_exact", "Requested part exactly right", GREEN, "..")]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    bw = 0.25
    for j, (key, label, colour, hatch) in enumerate(series):
        xs = [i + (j - 1) * (bw + 0.02) for i in range(len(tiers))]
        ys = [v[f"oct.spec.{t}.{key}"] for t, _ in tiers]
        ax.bar(xs, ys, width=bw, color=colour, edgecolor="white", linewidth=1.0, hatch=hatch, label=label)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.015, f"{y:.2f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels([n for _, n in tiers], fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Mean over all outputs (invalid output = 0)", fontsize=9)
    ax.tick_params(axis="y", labelsize=8, length=0)
    ax.tick_params(axis="x", length=0)
    ax.yaxis.grid(True, color="#e3e3e3", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(out, format="svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)


SCHEMATICS = {"fig_pipeline.svg": fig_pipeline, "fig_tiers.svg": fig_tiers,
              "fig_grading.svg": fig_grading, "fig_twins.svg": fig_twins}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a schematic is stale")
    args = ap.parse_args(argv)
    v = values()
    made = {name: fn(v) for name, fn in SCHEMATICS.items()}
    if args.check:
        stale = [n for n, text in made.items()
                 if not (GEN / n).exists() or (GEN / n).read_text(encoding="utf-8") != text]
        for n in stale:
            print(f"stale: paper/generated/{n}", file=sys.stderr)
        print(f"{len(made)} schematics checked, {len(stale)} stale")
        return 1 if stale else 0
    for name, text in made.items():
        (GEN / name).write_text(text, encoding="utf-8")
    fig_october(v, GEN / "fig_october_regrade.svg")
    print(f"wrote {len(made) + 1} figures to {GEN.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
