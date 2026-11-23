#!/usr/bin/env python3
"""Figures of the paper that are not plots of a final run.

    uv run python paper/figures.py           # writes paper/generated/fig_*.svg
    uv run python paper/figures.py --check   # exit 1 if a committed schematic is stale

Five schematics are written as plain SVG by this script (pipeline, tiers, drawn-state
grading, paired design, and the shapes of the result figures), so they are text, diff cleanly and
need no drawing program. They are 660 px wide, the width at which the PDF prints them, and no
text in them is smaller than 9.5 px (7 pt in print). One
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
        if size < MIN_SIZE:
            raise ValueError(f"in-figure text below {MIN_SIZE} px (7 pt in print): {s!r}")
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
# Layout: every schematic is W px wide and is printed at that width (the text column of
# the PDF is 658 CSS px), so 1 px of a figure is 0.75 pt on paper. MIN_SIZE keeps all
# in-figure text at 7 pt or more; Svg.text refuses anything smaller.
# --------------------------------------------------------------------------- #
W = 660
MIN_SIZE = 9.5
LOOKUP_FILL = "#d3e4f1"


def chars(px: float, size: float, mono: bool = False) -> int:
    """How many characters of this size fit in ``px`` (average glyph: 0.5 em; mono: 0.6 em)."""
    return max(8, int(px / (size * (0.6 if mono else 0.5))))


# --------------------------------------------------------------------------- #
# Figure 1: pipeline
# --------------------------------------------------------------------------- #
def fig_pipeline(v: dict) -> str:
    boxes = [
        ("1  Frozen public data", [
            f"{v['panel.n']} structures (PDB and AlphaFold DB),",
            f"{v['corpus.n_structures']} of them in tasks",
            "residue mapping (SIFTS)",
            f"{v['variants.n_usable']:,} variants classified as",
            "(likely) pathogenic in ClinVar"]),
        ("2  Generator scripts", [
            f"{v['corpus.n_templates']} templates.",
            "Each task gets: a request,",
            "a reference answer,",
            "its target atoms and a",
            "record of how it was made"]),
        ("3  Task corpus", [
            f"{v['corpus.n_tasks']} tasks, {v['corpus.n_tiers']} categories",
            f"scene track: {v['corpus.mvs.n']}",
            f"call-list track: {v['corpus.api.n']}",
            f"{v['corpus.n_twin_pairs']} pairs (one request, both tracks)",
            f"{v['corpus.heldback.n_tasks']} tasks on held-back structures"]),
        ("4  Model", [
            "is given a format guide and",
            "the request only:",
            "no structure file, no lookup",
            f"{v['plan.samples']} answers per task,",
            "each a scene or a call list"]),
        ("5  Grader", [
            "resolves reference and answer",
            "to their drawn state:",
            "per atom, how it is drawn",
            "and coloured",
            "(frozen atom tables)"]),
        ("6  Scores", [
            "F1 (partial credit)",
            "task success (yes or no)",
            "target score",
            "valid or invalid answer",
            "averages: strict, valid-only"]),
    ]
    x0, y0, w, h, gap, vgap = 10, 34, 206, 112, 11, 30
    yb = y0 + 2 * h + vgap + 44
    ch = 82
    s = Svg(W, yb + 2 * ch + 10 + 8, "How a MolBench task is built, answered and graded")
    s.text(x0, 20, "Steps 1 to 6. Grading (steps 5 and 6) uses no network and no model.", size=10, fill=MUTED)
    for i, (title, lines) in enumerate(boxes):
        x = x0 + (i % 3) * (w + gap)
        y = y0 + (i // 3) * (h + vgap)
        s.rect(x, y, w, h, fill=LOOKUP_FILL if i in (2, 5) else PALE)
        s.text(x + 10, y + 20, title, size=11.5, weight="bold")
        for j, ln in enumerate(lines):
            s.text(x + 10, y + 40 + j * 15, ln, size=10)
        if i % 3 < 2:
            s.arrow(x + w + 1, y + h / 2, x + w + gap - 1, y + h / 2)
    # from box 3 down and back to box 4
    xa, xb, ym = x0 + 2 * (w + gap) + w / 2, x0 + w / 2, y0 + h + vgap / 2
    s.raw(f'<path d="M{xa},{y0 + h + 1} V{ym} H{xb} V{y0 + h + vgap - 1}" fill="none" stroke="{MUTED}" '
          'stroke-width="1.4" marker-end="url(#arrow)"/>')
    s.text(x0, yb - 12, "Checks that do not depend on any model", size=11.5, weight="bold")
    checks = [
        ("Reference against structure (step 2)",
         "Each reference must select atoms, name the residue the generator intended, and grade as exactly right against itself."),
        ("Atom tables against the viewer (step 5)",
         "Selections were read back from the running viewers (Mol* 5.9.0, PDBe Mol* 3.3.2) and agree atom for atom."),
        ("Grader against a control set (step 5)",
         f"{v['controls.n']:,} control answers with a verdict known from how they were made. The grader "
         "was developed against them and now agrees with all; they are re-run on every change."),
        ("Format rules (step 3)",
         "One script validates every task file against the written task format; the run does not start "
         "unless every check passes."),
    ]
    cw = (W - 2 * x0 - gap) / 2
    for i, (title, body) in enumerate(checks):
        x = x0 + (i % 2) * (cw + gap)
        y = yb + (i // 2) * (ch + 10)
        s.rect(x, y, cw, ch, fill="#ffffff", dash="4 3")
        s.text(x + 10, y + 19, title, size=10.5, weight="bold")
        s.para(x + 10, y + 36, body, width=chars(cw - 20, 10), size=10, fill=MUTED)
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 2: tiers
# --------------------------------------------------------------------------- #
TIER_CARDS = [
    ("translation", "Translation", "tr-het-code-3ert", "Everything is in the request."),
    ("grounded", "Structure-grounded", "gr-ligand-1stp-btn", "A feature is named; the model must know its atoms."),
    ("interactions", "Interactions", "in-ca-distance-9fb2", "Named atoms and a measurement."),
    ("resolve", "Name resolution", "res-gene-p01112", "The protein is named; the entry is not."),
    ("clinical", "Clinical variant", "clin-pair-target-lyz-2nwd-w82r-mvs", None),
    ("followup", "Follow-up turn", "fu-referent-colour-5cj6-mvs", "A start state plus an edit."),
    ("accept_set", "Several right answers", "acc-residue-colour-4ins-mvs", "One countable thing is left open."),
    ("tool_only", "Viewer settings", "api-canvas-1udt", "Call-list track only."),
]
PROMPT_CHARS = 170      # a longer request is cut at a word and ends in an ellipsis


def fig_tiers(v: dict) -> str:
    prompts = {}
    for f in (REPO / "tasks").rglob("*.json"):
        t = json.loads(f.read_text(encoding="utf-8"))
        prompts[t.get("id")] = t
    cw, ch, gap, y0 = 314, 104, 12, 34
    s = Svg(W, y0 + 4 * (ch + gap) + 34, "The eight categories of task, each with one request from the corpus")
    s.text(10, 20, "Counts: tasks on the scene track / on the call-list track. Requests are quoted from the corpus.",
           size=10, fill=MUTED)
    for i, (tier, name, tid, needs) in enumerate(TIER_CARDS):
        x = 10 + (i % 2) * (cw + gap)
        y = y0 + (i // 2) * (ch + gap)
        lookup = tier in ("resolve", "clinical")
        if lookup:
            s.rect(x, y, cw, ch, fill=LOOKUP_FILL, stroke=BLUE, sw=1.8)
            s.text(x + 16 + len(name) * 6.6, y + 19, "lookup category", size=9.5, weight="bold", fill=BLUE)
        else:
            s.rect(x, y, cw, ch, fill=PALE)
        s.text(x + 10, y + 19, name, size=11.5, weight="bold")
        n_m, n_a = v[f"corpus.mvs.{tier}.n"], v[f"corpus.api.{tier}.n"]
        s.text(x + cw - 10, y + 19, f"{n_m or '–'} / {n_a or '–'}", size=10.5, anchor="end", fill=MUTED)
        if tier == "clinical":
            needs = (f"The residue must be found in the structure; copying the number in its name is wrong in "
                     f"{v['clin.n_face_value_wrong']} of {v['clin.n']} tasks.")
        yy = s.para(x + 10, y + 35, needs, width=chars(cw - 20, 10), size=10, fill=MUTED)
        prompt = " ".join(prompts[tid]["prompt"].split())
        if tier == "followup":
            prompt = "[start: a scene with one magenta chain] " + prompt
        if len(prompt) > PROMPT_CHARS:
            prompt = prompt[:PROMPT_CHARS - 3].rsplit(" ", 1)[0] + " …"
        s.para(x + 10, yy + 3, "“" + prompt + "”", width=chars(cw - 20, 10), size=10, italic=True)
    yf = y0 + 4 * (ch + gap) + 6
    s.para(10, yf, "Blue frame: the two lookup categories. The answer needs one fact that a person would look up "
           "(an entry, a residue number); the model must recall it.", width=chars(W - 20, 10), size=10, fill=MUTED)
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 4: drawn-state grading of the running example
# --------------------------------------------------------------------------- #
def fig_grading(v: dict) -> str:
    right, wrong = v["ex.auth_number"], v["ex.uniprot_position"]
    look = f"{v['ex.color']} {v['ex.rep_short']}"          # the look the request states
    mark = {"yellow": "#F0E442", "green": GREEN, "orange": ORANGE, "blue": BLUE}.get(v["ex.color"], GREEN)
    panels = [
        ("Reference", f"{v['ex.wild_type']}{right} of chain {v['ex.auth_chain']} as {look}. Nothing else.",
         right, False, "ex.mvs.right"),
        ("Answer A: number copied from the variant name",
         f"Author residue {wrong} drawn. It is {v['ex.face_value_residue']}{wrong}, another residue.",
         wrong, False, "ex.mvs.face"),
        ("Answer B: right residue, extra context",
         "The right residue, plus a grey cartoon of the whole protein that the request does not ask for.",
         right, True, "ex.mvs.context"),
    ]
    req = textwrap.wrap("Request: “" + v["ex.prompt"] + "”", width=chars(W - 20, 10))
    y0 = 14 + len(req) * 13 + 6
    pw, ph, gap, split = W - 20, 150, 10, 316
    s = Svg(W, y0 + 3 * (ph + gap), "Drawn-state grading of the running example")
    for j, ln in enumerate(req):
        s.text(10, 18 + j * 13, ln, size=10, fill=MUTED, italic=True)
    shown = [right - 1, right, right + 1, None, wrong - 1, wrong, wrong + 1]
    for i, (title, body, drawn, cartoon, key) in enumerate(panels):
        x, y = 10, y0 + i * (ph + gap)
        s.rect(x, y, pw, ph, fill="#ffffff")
        s.text(x + 10, y + 19, title, size=11, weight="bold")
        s.para(x + 10, y + 35, f"{body} Table 3, row {v[key.replace('ex.', 'ex.row.', 1)]}.",
               width=chars(split - 24, 10), size=10, fill=MUTED)
        # residue strip, left
        ys = y + 106
        s.text(x + 10, y + ph - 8, "Chain " + v["ex.auth_chain"] + ", author residue numbers", size=9.5, fill=MUTED)
        bx = x + 12
        cells = []
        for r in shown:
            if r is None:
                s.text(bx + 12, ys + 5, "…", size=13, fill=MUTED, anchor="middle")
                bx += 26
                continue
            s.rect(bx, ys - 12, 36, 24, fill=PALE, r=3)
            s.text(bx + 18, ys + 4, r, size=10, anchor="middle")
            cells.append((r, bx + 18))
            bx += 40
        if cartoon:
            s.raw(f'<path d="M{x + 12},{ys + 20} C{x + 80},{ys + 12} {x + 170},{ys + 28} {x + 276},{ys + 18}" '
                  f'fill="none" stroke="{GREY}" stroke-width="6" stroke-linecap="round"/>')
            s.text(x + 300, ys + 34, "grey cartoon, all residues", size=9.5, fill=MUTED, anchor="end")
        for r, cx in cells:
            if r == drawn:
                s.line(cx, ys - 12, cx, ys - 22, stroke=INK, sw=1.5)
                s.circle(cx, ys - 28, 7, mark, stroke=INK, sw=1.2)
                far = cx > x + 180
                s.text(cx - 11 if far else cx + 11, ys - 24, look, size=9.5, fill=INK,
                       anchor="end" if far else "start")
        # facts and scores, right
        xr = x + split
        s.line(xr - 8, y + 10, xr - 8, y + ph - 10)
        s.text(xr, y + 19, "Facts of the drawn state", size=10.5, weight="bold")
        if key == "ex.mvs.right":
            facts = [f"1 fact: the {v['ex.n_target_atoms']} atoms of {v['ex.wild_type']}{right}, {look}"]
        elif key == "ex.mvs.face":
            facts = [f"1 fact: the {v['ex.face_value_n_atoms']} atoms of {v['ex.face_value_residue']}{wrong}, {look}",
                     "(no atom shared with the reference)"]
        else:
            facts = [f"fact 1: {v['ex.wild_type']}{right}, grey cartoon and {look};",
                     "   one of its two styles is in the reference",
                     "fact 2: all other residues, grey cartoon;",
                     "   none of it is in the reference"]
        for j, ln in enumerate(facts):
            s.text(xr, y + 34 + j * 13, ln, size=10)
        ysc = y + ph - 58
        s.line(xr, ysc - 13, x + pw - 10, ysc - 13)
        rows = [("Recall (share of the reference the answer has)", f"{v[key + '.recall']:.2f}"),
                ("Precision (share of the answer the reference has)", f"{v[key + '.precision']:.2f}"),
                ("F1", f"{v[key + '.f1']:.2f}"),
                ("Task success", "yes" if v[key + ".success"] else "no"),
                ("Target score", f"{v[key + '.target']:.2f}")]
        for j, (k, val) in enumerate(rows):
            bold = "bold" if j >= 2 else "normal"
            s.text(xr, ysc + j * 13, k, size=10, weight=bold)
            s.text(x + pw - 10, ysc + j * 13, val, size=10, weight=bold, anchor="end")
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 3: paired design
# --------------------------------------------------------------------------- #
def fig_twins(v: dict) -> str:
    req = textwrap.wrap("“" + v["ex.prompt"] + "”", width=chars(W - 60, 10))
    rh = 26 + len(req) * 13 + 6
    s = Svg(W, rh + 398, "The paired design: one request, two answer formats, the same target atoms")
    s.rect(10, 8, W - 20, rh, fill=LOOKUP_FILL)
    s.text(W / 2, 24, "Request (identical on both tracks)", size=10.5, weight="bold", anchor="middle")
    for j, ln in enumerate(req):
        s.text(W / 2, 40 + j * 13, ln, size=10, anchor="middle", italic=True)
    y, w, h = 8 + rh + 22, 314, 150
    lx, rx = 10, 10 + w + 12
    s.arrow(W / 2 - 60, 8 + rh + 1, lx + w / 2 + 40, y - 2)
    s.arrow(W / 2 + 60, 8 + rh + 1, rx + w / 2 - 40, y - 2)
    for x, title in ((lx, "Scene track: a MolViewSpec scene (declarative)"),
                     (rx, "Call-list track: PDBe Mol* viewer calls (imperative)")):
        s.rect(x, y, w, h)
        s.text(x + 10, y + 19, title, size=10.5, weight="bold")
    entry = v["ex.entry"].lower()
    scene = [f"download  files.rcsb.org/download/{entry}.cif",
             " parse  mmcif",
             "  structure  model",
             f"   component  auth_asym_id = {v['ex.auth_chain']},",
             f"              auth_seq_id = {v['ex.auth_number']}",
             f"    representation  {v['ex.rep_scene']}",
             f"     color  {v['ex.color']}"]
    calls = [f'load   molecule_id = "{entry}"',
             f'color  uniprot_accession = "{v["ex.accession"]}",',
             f'       uniprot_residue_number = {v["ex.uniprot_position"]},',
             f'       representation = "{v["ex.rep_short"]}",',
             f'       representationColor = "{v["ex.color"]}"']
    for x, code, note in (
            (lx, scene, f"The model must turn UniProt {v['ex.uniprot_position']} into author residue "
                        f"{v['ex.auth_number']} itself."),
            (rx, calls, "The viewer does the mapping; the model only passes on the accession and the position.")):
        for j, ln in enumerate(code):
            s.text(x + 10, y + 38 + j * 13, ln, size=9.5, mono=True)
        s.para(x + 10, y + h - 21, note, width=chars(w - 20, 10), size=10, fill=MUTED)
    ty = y + h + 26
    s.arrow(lx + w / 2, y + h + 1, W / 2 - 80, ty - 2)
    s.arrow(rx + w / 2, y + h + 1, W / 2 + 80, ty - 2)
    s.rect(W / 2 - 215, ty, 430, 42, fill="#e6f4ef", stroke=GREEN, sw=1.5)
    s.text(W / 2, ty + 18, "Both references resolve to the same target atoms", size=11, weight="bold", anchor="middle")
    s.text(W / 2, ty + 33, f"{v['ex.wild_type']}{v['ex.auth_number']}, chain {v['ex.auth_chain']} of {v['ex.entry']}: "
           f"{v['ex.n_target_atoms']} atoms (checked when the task is built)", size=10, anchor="middle", fill=MUTED)
    gy = ty + 42 + 40
    gx, cw, chh = 290, 142, 30
    s.arrow(W / 2, ty + 43, W / 2, gy - 22)
    s.text(10, gy + 2, "Per model, every pair falls into one of four cells.", size=10.5, weight="bold")
    s.para(10, gy + 18, f"A side is right when at least 2 of its {v['plan.samples']} answers are target-right. "
           f"Counted over the {v['corpus.twins.n_with_target']} pairs that have a target score; repeated with "
           f"task success over all {v['corpus.n_twin_pairs']} pairs.", width=chars(gx - 30, 10), size=10, fill=MUTED)
    s.text(gx + cw / 2, gy - 6, "call list right", size=10, anchor="middle", fill=MUTED)
    s.text(gx + cw * 1.5, gy - 6, "call list wrong", size=10, anchor="middle", fill=MUTED)
    cells = [("right on both sides", PALE), ("right in the scene only", "#fdf0d5"),
             ("right in the call list only", "#fdf0d5"), ("right on neither side", PALE)]
    for k, (label, fill) in enumerate(cells):
        cx, cy = gx + (k % 2) * cw, gy + (k // 2) * chh
        s.rect(cx, cy, cw, chh, fill=fill, r=0)
        s.text(cx + cw / 2, cy + 19, label, size=10, anchor="middle")
    s.text(gx + 2 * cw + 8, gy + 19, "scene right", size=10, fill=MUTED)
    s.text(gx + 2 * cw + 8, gy + chh + 19, "scene wrong", size=10, fill=MUTED)
    s.text(gx + cw, gy + 2 * chh + 18, "McNemar's test compares the two shaded cells", size=10, anchor="middle", fill=MUTED)
    s.text(gx + cw, gy + 2 * chh + 31, "(right in one format only).", size=10, anchor="middle", fill=MUTED)
    return s.done()


# --------------------------------------------------------------------------- #
# Figure 6: October predictions regraded (matplotlib)
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
    # F1 is a mean score; the other two are shares of answers and are printed as percentages.
    series = [("f1", "F1 (mean, 0 to 1)", BLUE, "", False),
              ("success", "Task success (share of answers)", ORANGE, "//", True),
              ("highlight_exact", "Requested part exactly right (share of answers\nto tasks that mark one)", GREEN, "..", True)]
    fig, ax = plt.subplots(figsize=(6.85, 3.9))     # printed at this width: font sizes are in points
    bw = 0.25
    for j, (key, label, colour, hatch, share) in enumerate(series):
        xs = [i + (j - 1) * (bw + 0.02) for i in range(len(tiers))]
        ys = [v[f"oct.spec.{t}.{key}"] for t, _ in tiers]
        ax.bar(xs, ys, width=bw, color=colour, edgecolor="white", linewidth=1.0, hatch=hatch, label=label)
        for (t, _), x, y in zip(tiers, xs, ys):
            # The third series has its own denominator: answers to tasks with a marked requested part.
            n = v[f"oct.spec.{t}.highlight_n"] if key == "highlight_exact" else v[f"oct.spec.{t}.n"]
            ax.text(x, y + 0.015, (f"{y:.0%}" if share else f"{y:.2f}") + f"\nn = {n}", ha="center", va="bottom",
                    fontsize=7.5, color=INK, linespacing=1.15)
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels([n for _, n in tiers], fontsize=8.5)
    ax.set_ylim(0, 1.3)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])
    ax.set_ylabel("F1 (0 to 1), or share of answers (1 = 100%)\nAn unshowable answer counts as 0", fontsize=8.5)
    ax.tick_params(axis="y", labelsize=7.5, length=0)
    ax.tick_params(axis="x", length=0)
    ax.yaxis.grid(True, color="#e3e3e3", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.legend(frameon=False, fontsize=7.5, loc="upper center", ncol=3, columnspacing=1.0, handlelength=1.4)
    fig.tight_layout()
    fig.savefig(out, format="svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Figure 5: the shapes of the result figures (no data)
# --------------------------------------------------------------------------- #
EXAMPLE_OPACITY = 0.45     # example marks: the final colours and shapes, drawn pale


def fig_result_shapes(v: dict) -> str:
    """Three empty panels that show how the final-run figures will be read. Nothing in
    this figure is a result: each panel has axes, the marks explained in a key, and one
    example row in the final colours and shapes, drawn pale and labelled as an example."""
    ph, gap, top, split = 132, 10, 30, 300
    s = Svg(W, top + 3 * (ph + gap), "Layout of the result figure, in three panels, that the final run will fill; no data are shown")
    s.text(10, 19, "No data yet. The pale example mark in each panel has the final colour and shape; "
           "its position means nothing.", size=10, fill=MUTED)
    ticks = ["0", "0.25", "0.5", "0.75", "1"]

    def frame(i, title, sub):
        y0 = top + i * (ph + gap)
        s.rect(10, y0, W - 20, ph, fill="#ffffff")
        s.text(20, y0 + 19, title, size=11, weight="bold")
        s.para(20, y0 + 35, sub, chars(split - 30, 10), size=10, fill=MUTED)
        return y0

    def axis(ax, y0, aw, xlabel, head=None, pending=True):
        ay = y0 + ph - 38
        s.line(ax, ay, ax + aw, ay, stroke=INK)
        for k, t in enumerate(ticks):
            tx = ax + aw * k / (len(ticks) - 1)
            s.line(tx, ay, tx, ay + 4, stroke=INK)
            s.line(tx, y0 + 26, tx, ay, stroke="#e3e3e3")
            s.text(tx, ay + 15, t, size=9.5, anchor="middle", fill=MUTED)
        s.text(ax + aw / 2, ay + 30, xlabel, size=10, anchor="middle")
        if head:
            s.text(ax + aw / 2, y0 + 19, head, size=10, weight="bold", anchor="middle")
        if pending:
            s.text(ax + aw / 2, ay - 14, "⟦PENDING: final run⟧", size=10, anchor="middle", fill=MUTED)
        return ay

    # A: per model, one sub-panel per track (the two tracks are not compared with each other)
    y0 = frame(0, "A  Task success by model, one panel per track",
               f"One row per model, best first: {v['plan.n_core_models']} core models, up to "
               f"{v['plan.n_optional_models']} optional ones (†) and the keyword script. The two tracks are "
               "not compared with each other.")
    ky = y0 + ph - 12
    s.circle(26, ky - 4, 4.5, BLUE)
    s.text(36, ky, "task success rate, strict", size=9.5)
    s.line(160, ky - 4, 180, ky - 4, stroke=INK, sw=2)
    s.text(186, ky, "95% interval", size=9.5)
    for k, head in enumerate(("Scene track", "Call-list track")):
        ax, aw = split + 44 + k * 156, 132
        ay = axis(ax, y0, aw, "Task success rate", head)
        ry = y0 + 44
        if k == 0:
            s.text(ax - 6, ry + 4, "model", size=9.5, anchor="end", fill=MUTED)
        s.raw(f'<g opacity="{EXAMPLE_OPACITY}">')
        s.line(ax + aw * (0.40 + 0.1 * k), ry, ax + aw * (0.62 + 0.1 * k), ry, stroke=INK, sw=2)
        s.circle(ax + aw * (0.51 + 0.1 * k), ry, 4.5, BLUE)
        s.raw('</g>')

    # B: pairs
    y0 = frame(1, "B  The same request in both formats",
               f"One bar per model: its {v['corpus.twins.n_with_target']} pairs with a target score, by which side "
               f"is right (at least 2 of {v['plan.samples']} answers target-right).")
    ax, aw = split + 44, 288
    axis(ax, y0, aw, "Share of pairs")
    ry = y0 + 36
    s.text(ax - 6, ry + 11, "model", size=9.5, anchor="end", fill=MUTED)
    cuts = [(0.0, 0.45, "#8a8a8a", ""), (0.45, 0.60, "#c4c4c4", "url(#hatchA)"),
            (0.60, 0.72, "#c4c4c4", "url(#hatchB)"), (0.72, 1.0, "#f1f1f1", "")]
    s.raw('<defs><pattern id="hatchA" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
          f'<rect width="6" height="6" fill="#ffffff"/><line x1="0" y1="0" x2="0" y2="6" stroke="{BLUE}" stroke-width="2.4"/></pattern>'
          '<pattern id="hatchB" width="6" height="6" patternUnits="userSpaceOnUse">'
          f'<rect width="6" height="6" fill="#ffffff"/><circle cx="3" cy="3" r="1.6" fill="{ORANGE}"/></pattern></defs>')
    for a, b, fill, pat in cuts:
        s.raw(f'<rect x="{ax + aw * a:.1f}" y="{ry}" width="{aw * (b - a):.1f}" height="14" fill="{pat or fill}" stroke="#ffffff"/>')
    # the labels of Table 9, in the order of the bar from left to right: down the first
    # column of the key, then down the second
    keys = [("#8a8a8a", "", "1  right on both sides"), ("", "url(#hatchA)", "2  right in the scene only"),
            ("", "url(#hatchB)", "3  right in the call list only"), ("#f1f1f1", "", "4  right on neither side")]
    for k, (fill, pat, label) in enumerate(keys):
        s.text(ax + aw * (cuts[k][0] + cuts[k][1]) / 2, ry - 4, str(k + 1), size=9.5, anchor="middle", fill=MUTED)
        kx, kyy = 18 + (k // 2) * 128, y0 + ph - 26 + (k % 2) * 15
        s.raw(f'<rect x="{kx}" y="{kyy - 9}" width="14" height="10" fill="{pat or fill}" stroke="{LINE}" stroke-width="0.8"/>')
        s.text(kx + 20, kyy, label, size=9.5)

    # C: categories
    y0 = frame(2, "C  Where points are lost, by category",
               "One row per category and track, models averaged, valid answers only. Target score above task "
               "success: the requested atoms were right, the rest was not exact.")
    axis(ax, y0, aw, "Score, valid answers only")
    ry = y0 + 44
    s.text(ax - 6, ry + 4, "category", size=9.5, anchor="end", fill=MUTED)
    s.raw(f'<g opacity="{EXAMPLE_OPACITY}">')
    s.line(ax + aw * 0.38, ry, ax + aw * 0.80, ry, stroke=GREY, sw=1.5)
    s.raw(f'<path d="M{ax + aw * 0.38 - 5},{ry} l5,-5 l5,5 l-5,5 z" fill="{ORANGE}"/>')
    s.circle(ax + aw * 0.80, ry, 4.5, GREEN)
    s.raw('</g>')
    ky = y0 + ph - 12
    s.raw(f'<path d="M{21},{ky - 4} l5,-5 l5,5 l-5,5 z" fill="{ORANGE}"/>')
    s.text(36, ky, "task success rate", size=9.5)
    s.circle(146, ky - 4, 4.5, GREEN)
    s.text(156, ky, "target score", size=9.5)
    return s.done()


SCHEMATICS = {"fig_pipeline.svg": fig_pipeline, "fig_tiers.svg": fig_tiers,
              "fig_grading.svg": fig_grading, "fig_twins.svg": fig_twins,
              "fig_result_shapes.svg": fig_result_shapes}


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
