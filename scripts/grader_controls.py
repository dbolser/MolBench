#!/usr/bin/env python3
"""
Build and score the grader control set (plan gap G3, decision 18).

A control is a (reference, answer) pair with a known verdict:

* **identical**  - the answer is the reference; must pass;
* **equivalent** - the answer is written differently but the viewer shows the same
  thing; must pass;
* **wrong**      - the viewer shows something else; must fail.

"Pass" is task success as ``molbench.grader.grade_task`` reports it. Every pair is
built by rule from the frozen structure panel (``data/panel``, ``molbench/atom_tables``,
``molbench/sifts_tables``): no network, no hand-written answer. The verdicts do not
come from the grader: each rewrite is one whose effect is known from the structure
(for example, a residue addressed by its label numbering instead of its author
numbering, chosen where the two name the same atoms), and ``--viewer`` checks the
MVS verdicts against headless Mol* itself (the atoms each representation draws, their
colours and opacity, read back from the viewer).

    python scripts/grader_controls.py            # rebuild tests/controls/*.jsonl + summary.json
    python scripts/grader_controls.py --check    # build nothing; fail if the files are stale
    python scripts/grader_controls.py --viewer   # also check MVS controls and the drawing
                                                 # rules in Mol* (needs the execute extra)
    python scripts/grader_controls.py --viewer-api N   # check N API answers in pdbe-molstar
    python scripts/grader_controls.py --october DIR    # regrade the October MVS scorecards

Files written (all under ``tests/controls/``): ``mvs.jsonl``, ``api.jsonl`` (one control
per line), ``summary.json`` (the grader's false-pass and false-fail rates, per track and
per kind - the numbers the paper quotes), ``viewer_check.json`` (``--viewer``),
``october_regrade.json`` and ``colour_evidence.json`` (``--october``).
"""

from __future__ import annotations

import argparse
import copy
import functools
import gzip
import hashlib
import http.server
import itertools
import json
import pathlib
import random
import sys
import threading
from typing import Any, Callable

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import atoms, drawn, grader, grounding, mvs, sifts  # noqa: E402
from molbench import pdbe_state as ps  # noqa: E402

OUT = REPO / "tests" / "controls"
SEED = 20261112
PER_KIND = 20                      # instances aimed for per kind and track
N_IDENTICAL = 150                  # identical pairs kept per track (spread over kinds and entries)
SKIP = {"1hsg"}                    # the API prompt's worked example: never used
PALETTE = [c for c in drawn.TASK_PALETTE if c not in ("gray", "white", "black")]


# --- the panel, as residues ----------------------------------------------------------

class Entry:
    """A panel entry: its atom table cut into residues, and its frozen facts."""

    def __init__(self, entry_id: str):
        self.id = entry_id
        self.table = atoms.load_table(entry_id)
        self.facts = grounding.facts(entry_id) or {}
        t = self.table
        c = t.columns
        self.all = (1 << t.n) - 1
        self.polymer = t.static.get("polymer", 0)
        self.protein = t.static.get("protein", 0)
        self.residues: list[dict] = []
        for ri, mask in t.index("residue_index").items():
            row = (mask & -mask).bit_length() - 1
            self.residues.append({
                "ri": ri, "mask": mask, "row": row,
                "auth_asym_id": c["auth_asym_id"][row], "auth_seq_id": c["auth_seq_id"][row],
                "ins": c["pdbx_PDB_ins_code"][row], "label_asym_id": c["label_asym_id"][row],
                "label_seq_id": c["label_seq_id"][row], "comp": c["label_comp_id"][row],
                "entity": c["label_entity_id"][row],
                "polymer": bool(mask & self.polymer), "protein": bool(mask & self.protein)})
        self.residues.sort(key=lambda r: r["row"])
        self.af = entry_id.startswith("af-")

    @property
    def url(self) -> str:
        if self.af:
            _, acc, frag, rest = self.id.split("-", 3)
            return f"https://alphafold.ebi.ac.uk/files/AF-{acc.upper()}-{frag.upper()}-{rest}.cif"
        return f"https://files.rcsb.org/download/{self.id}.cif"

    def sel(self, expr: Any) -> int:
        return self.table.selector(expr) or 0

    def auth(self, r: dict) -> dict:
        return {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["auth_seq_id"]}

    def label(self, r: dict) -> dict:
        return {"label_asym_id": r["label_asym_id"], "label_seq_id": r["label_seq_id"]}

    def auth_unique(self, r: dict) -> bool:
        """The author chain and number name exactly this residue's atoms."""
        return not r["ins"] and self.sel(self.auth(r)) == r["mask"]

    def label_unique(self, r: dict) -> bool:
        return self.sel(self.label(r)) == r["mask"]

    def plain(self) -> list[dict]:
        """Protein residues that both numberings name unambiguously, with a side chain."""
        names = self.table.index("label_atom_id")
        cb, ca = names.get("CB", 0), names.get("CA", 0)
        return [r for r in self.residues if r["protein"] and r["mask"] & cb and r["mask"] & ca
                and self.auth_unique(r) and self.label_unique(r)]

    def chains(self) -> list[dict]:
        """Polymer chains (facts), with the atoms of each as the cartoon sees them."""
        out = []
        for ch in self.facts.get("chains", []):
            m = self.sel({"label_asym_id": ch["label_asym_id"]}) & self.polymer
            if m:
                out.append({**ch, "mask": m})
        return out


@functools.lru_cache(maxsize=None)
def entry(entry_id: str) -> Entry:
    return Entry(entry_id)


def panel_ids() -> list[str]:
    return sorted(e["id"] for e in grounding.panel_entries() if e["id"] not in SKIP)


# --- MVS scene building --------------------------------------------------------------

def comp(selector: Any, *children: dict, custom: dict | None = None) -> dict:
    node: dict = {"kind": "component", "params": {"selector": selector}, "children": list(children)}
    if custom:
        node["custom"] = custom
    return node


def rep(rtype: str, *children: dict, **params: Any) -> dict:
    return {"kind": "representation", "params": {"type": rtype, **params},
            "children": list(children)}


def col(color: str, selector: Any = None, theme: str | None = None) -> dict:
    node: dict = {"kind": "color", "params": {"color": color}}
    if selector is not None:
        node["params"]["selector"] = selector
    if theme:
        node["custom"] = {"molstar_color_theme_name": theme}
    return node


def scene(e: Entry, comps: list[dict], structure: dict | None = None, url: str | None = None,
          fmt: str = "mmcif") -> dict:
    return {"kind": "root", "children": [
        {"kind": "download", "params": {"url": url or e.url}, "children": [
            {"kind": "parse", "params": {"format": fmt}, "children": [
                {"kind": "structure", "params": structure or {"type": "model"},
                 "children": comps}]}]}]}


def components(tree: dict) -> list[dict]:
    return tree["children"][0]["children"][0]["children"][0]["children"]


def with_components(tree: dict, comps: list[dict]) -> dict:
    out = copy.deepcopy(tree)
    out["children"][0]["children"][0]["children"][0]["children"] = comps
    return out


def hexcolor(name: str, upper: bool = False) -> str:
    r, g, b = drawn.COLOR_NAMES[name]
    s = f"#{r:02x}{g:02x}{b:02x}"
    return s.upper() if upper else s


class Ctx:
    """Seeded choices for one entry, shared by every control built on it."""

    def __init__(self, e: Entry, seed: int):
        self.e = e
        self.rng = random.Random(f"{seed}:{e.id}")
        plain = e.plain()
        self.plain = plain
        self.res = self.rng.choice(plain) if plain else None
        self.c1, self.c2, self.c3 = self.rng.sample(PALETTE, 3)
        self.chains = e.chains()

    def neighbour(self, r: dict, step: int = 1) -> dict | None:
        for q in self.plain:
            if (q["auth_asym_id"] == r["auth_asym_id"] and q["label_asym_id"] == r["label_asym_id"]
                    and q["auth_seq_id"] == r["auth_seq_id"] + step):
                return q
        return None

    def run(self, n: int = 6) -> list[dict] | None:
        """n consecutive plain residues (author and label numbers both consecutive)."""
        starts = list(self.plain)
        self.rng.shuffle(starts)
        for r in starts:
            out = [r]
            while len(out) < n:
                q = self.neighbour(out[-1])
                if q is None or q["label_seq_id"] != out[-1]["label_seq_id"] + 1:
                    break
                out.append(q)
            if len(out) == n:
                lo, hi = out[0]["auth_seq_id"], out[-1]["auth_seq_id"]
                rng_sel = {"auth_asym_id": r["auth_asym_id"], "beg_auth_seq_id": lo,
                           "end_auth_seq_id": hi}
                union = 0
                for q in out:
                    union |= q["mask"]
                if self.e.sel(rng_sel) == union:      # nothing else carries those numbers
                    return out
        return None

    def ligand(self) -> dict | None:
        ligs = [lg for lg in self.e.facts.get("ligands", []) if lg.get("kind") == "ligand"
                and self.e.sel({"label_comp_id": lg["comp_id"]})]
        return self.rng.choice(sorted(ligs, key=lambda x: x["comp_id"])) if ligs else None

    # base scenes
    def highlight(self, r: dict | None = None, colour: str | None = None,
                  rtype: str = "ball_and_stick") -> dict:
        r = r or self.res
        return scene(self.e, [comp("polymer", rep("cartoon", col("gray"))),
                              comp(self.e.auth(r), rep(rtype, col(colour or self.c1)))])


Rewrite = Callable[[Ctx], "tuple[dict, dict] | None"]
MVS_EQUIVALENT: dict[str, tuple[str, Rewrite, bool]] = {}
MVS_WRONG: dict[str, tuple[str, Rewrite, bool]] = {}
API_EQUIVALENT: dict[str, tuple[str, Rewrite, bool]] = {}
API_WRONG: dict[str, tuple[str, Rewrite, bool]] = {}


def control(registry: dict, name: str, what: str, viewer: bool = True):
    def deco(fn: Rewrite) -> Rewrite:
        registry[name] = (what, fn, viewer)
        return fn
    return deco


# --- MVS: equivalent rewrites (must pass) ---------------------------------------------

@control(MVS_EQUIVALENT, "all_vs_polymer_cartoon",
         "selector 'all' instead of 'polymer' under a cartoon (a cartoon draws polymer only)")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = c.highlight()
    pred = copy.deepcopy(ref)
    components(pred)[0]["params"]["selector"] = "all"
    return ref, pred


@control(MVS_EQUIVALENT, "residue_list_vs_range",
         "six residues listed one by one instead of an author-number range")
def _(c: Ctx):
    run = c.run()
    if not run:
        return None
    a = run[0]["auth_asym_id"]
    rng_sel = {"auth_asym_id": a, "beg_auth_seq_id": run[0]["auth_seq_id"],
               "end_auth_seq_id": run[-1]["auth_seq_id"]}
    mk = lambda s: scene(c.e, [comp("polymer", rep("cartoon", col("gray"))),  # noqa: E731
                               comp(s, rep("ball_and_stick", col(c.c1)))])
    return mk(rng_sel), mk([c.e.auth(r) for r in run])


@control(MVS_EQUIVALENT, "range_split_in_two",
         "one residue range written as two adjacent ranges in two components")
def _(c: Ctx):
    run = c.run()
    if not run:
        return None
    a = run[0]["auth_asym_id"]
    r = lambda lo, hi: {"auth_asym_id": a, "beg_auth_seq_id": lo["auth_seq_id"],  # noqa: E731
                        "end_auth_seq_id": hi["auth_seq_id"]}
    style = lambda: rep("spacefill", col(c.c2))  # noqa: E731
    return (scene(c.e, [comp(r(run[0], run[-1]), style())]),
            scene(c.e, [comp(r(run[0], run[2]), style()), comp(r(run[3], run[-1]), style())]))


@control(MVS_EQUIVALENT, "label_vs_author_residue",
         "a residue addressed by label chain and number instead of author chain and number")
def _(c: Ctx):
    # prefer a residue whose two numbers differ, so the rewrite is not a no-op
    diff = [r for r in c.plain if r["auth_seq_id"] != r["label_seq_id"]
            or r["auth_asym_id"] != r["label_asym_id"]]
    pool = diff or c.plain
    if not pool:
        return None
    r = c.rng.choice(pool)
    ref = c.highlight(r)
    pred = copy.deepcopy(ref)
    components(pred)[1]["params"]["selector"] = c.e.label(r)
    return ref, pred


@control(MVS_EQUIVALENT, "label_range_vs_author_range",
         "a residue range in label numbering instead of author numbering")
def _(c: Ctx):
    run = c.run()
    if not run:
        return None
    auth = {"auth_asym_id": run[0]["auth_asym_id"], "beg_auth_seq_id": run[0]["auth_seq_id"],
            "end_auth_seq_id": run[-1]["auth_seq_id"]}
    lab = {"label_asym_id": run[0]["label_asym_id"], "beg_label_seq_id": run[0]["label_seq_id"],
           "end_label_seq_id": run[-1]["label_seq_id"]}
    union = 0
    for q in run:
        union |= q["mask"]
    if c.e.sel(lab) != union:
        return None
    mk = lambda s: scene(c.e, [comp("polymer", rep("cartoon", col("gray"))),  # noqa: E731
                               comp(s, rep("surface", col(c.c3)))])
    return mk(auth), mk(lab)


@control(MVS_EQUIVALENT, "one_component_vs_several",
         "three residues in one component (a selector list) or in three components")
def _(c: Ctx):
    if len(c.plain) < 3:
        return None
    rs = c.rng.sample(c.plain, 3)
    base = [comp("polymer", rep("cartoon", col("gray")))]
    one = scene(c.e, base + [comp([c.e.auth(r) for r in rs], rep("ball_and_stick", col(c.c1)))])
    many = scene(c.e, copy.deepcopy(base) + [comp(c.e.auth(r), rep("ball_and_stick", col(c.c1)))
                                             for r in rs])
    return one, many


@control(MVS_EQUIVALENT, "colour_name_vs_hex",
         "a colour given as #rrggbb (lower or upper case) instead of its name")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = c.highlight()
    pred = copy.deepcopy(ref)
    upper = c.rng.random() < 0.5
    components(pred)[1]["children"][0]["children"][0]["params"]["color"] = hexcolor(c.c1, upper)
    components(pred)[0]["children"][0]["children"][0]["params"]["color"] = hexcolor("gray", not upper)
    return ref, pred


@control(MVS_EQUIVALENT, "gray_vs_grey", "'grey' instead of 'gray'")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = c.highlight()
    pred = copy.deepcopy(ref)
    components(pred)[0]["children"][0]["children"][0]["params"]["color"] = "grey"
    return ref, pred


@control(MVS_EQUIVALENT, "nested_colour_vs_flat_components",
         "one cartoon with a colour child for one chain, or one cartoon component per chain")
def _(c: Ctx):
    chains = c.chains
    if len(chains) < 2 or len(chains) > 12:
        return None
    union = 0
    for ch in chains:
        union |= ch["mask"]
    if union != c.e.polymer:
        return None
    pick = c.rng.choice(chains)
    sel = lambda ch: {"label_asym_id": ch["label_asym_id"]}  # noqa: E731
    nested = scene(c.e, [comp("polymer", rep("cartoon", col("gray"), col(c.c1, sel(pick))))])
    flat = scene(c.e, [comp(sel(ch), rep("cartoon", col(c.c1 if ch is pick else "gray")))
                       for ch in chains])
    return nested, flat


@control(MVS_EQUIVALENT, "chain_by_author_vs_label_id",
         "a chain's cartoon selected by author chain id, label chain id or entity id")
def _(c: Ctx):
    cands = [ch for ch in c.chains
             if c.e.sel({"auth_asym_id": ch["auth_asym_id"]}) & c.e.polymer == ch["mask"]]
    if not cands:
        return None
    ch = c.rng.choice(cands)
    ent = c.e.sel({"label_entity_id": ch["entity_id"]}) & c.e.polymer
    alt = ({"label_entity_id": ch["entity_id"]} if ent == ch["mask"] and c.rng.random() < 0.5
           else {"label_asym_id": ch["label_asym_id"]})
    mk = lambda s: scene(c.e, [comp(s, rep("cartoon", col(c.c2)))])  # noqa: E731
    return mk({"auth_asym_id": ch["auth_asym_id"]}), mk(alt)


@control(MVS_EQUIVALENT, "ligand_by_name_vs_copies",
         "a ligand selected by residue name, or each copy by author chain and number")
def _(c: Ctx):
    lg = c.ligand()
    if lg is None:
        return None
    by_name = {"label_comp_id": lg["comp_id"]}
    copies = [{"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"],
               "label_comp_id": lg["comp_id"]} for cp in lg["copies"]]
    if c.e.sel(by_name) != c.e.sel(copies):
        return None
    mk = lambda s: scene(c.e, [comp("polymer", rep("cartoon", col("gray"))),  # noqa: E731
                               comp(s, rep("ball_and_stick", col(c.c1)))])
    return mk(by_name), mk(copies)


@control(MVS_EQUIVALENT, "children_reordered",
         "components, and the keys inside nodes, in another order")
def _(c: Ctx):
    if len(c.plain) < 2:
        return None
    r1, r2 = c.rng.sample(c.plain, 2)
    ref = scene(c.e, [comp("polymer", rep("cartoon", col("gray"))),
                      comp(c.e.auth(r1), rep("ball_and_stick", col(c.c1))),
                      comp(c.e.auth(r2), rep("spacefill", col(c.c2)))])
    pred = copy.deepcopy(ref)
    comps = components(pred)
    comps.reverse()

    def flip(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: flip(node[k]) for k in reversed(list(node))}
        if isinstance(node, list):
            return [flip(x) for x in node]
        return node
    return ref, flip(pred)


@control(MVS_EQUIVALENT, "envelope_and_file_source",
         "a full state with metadata, and the same entry from another server or as BinaryCIF")
def _(c: Ctx):
    if c.res is None or c.e.af:
        return None
    ref = c.highlight()
    which = c.rng.choice(["pdbe", "bcif", "wrap"])
    if which == "pdbe":
        url, fmt = f"https://www.ebi.ac.uk/pdbe/entry-files/download/{c.e.id}_updated.cif", "mmcif"
    elif which == "bcif":
        url, fmt = f"https://models.rcsb.org/{c.e.id}.bcif", "bcif"
    else:
        url, fmt = f"https://files.rcsb.org/download/{c.e.id.upper()}.cif", "mmcif"
    inner = scene(c.e, copy.deepcopy(components(ref)), url=url, fmt=fmt)
    pred = {"kind": "single", "root": inner,
            "metadata": {"version": "1.4", "timestamp": "2026-01-01T00:00:00Z", "title": "x"}}
    return ref, pred


@control(MVS_EQUIVALENT, "defaults_written_out",
         "defaults stated explicitly: opacity 1, colour selector 'all', model_index 0, size_factor 1")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = c.highlight()
    pred = with_components(ref, [
        comp("polymer", rep("cartoon", col("gray", "all"),
                            {"kind": "opacity", "params": {"opacity": 1.0}}, size_factor=1)),
        comp(c.e.auth(c.res), rep("ball_and_stick", col(c.c1), size_factor=1))])
    pred["children"][0]["children"][0]["children"][0]["params"] = {"type": "model", "model_index": 0}
    return ref, pred


@control(MVS_EQUIVALENT, "trace_atom_under_cartoon",
         "a cartoon on the C-alpha atoms of a range instead of on the residues")
def _(c: Ctx):
    run = c.run()
    if not run:
        return None
    sel = {"auth_asym_id": run[0]["auth_asym_id"], "beg_auth_seq_id": run[0]["auth_seq_id"],
           "end_auth_seq_id": run[-1]["auth_seq_id"]}
    mk = lambda s: scene(c.e, [comp(s, rep("cartoon", col(c.c1)))])  # noqa: E731
    return mk(sel), mk({**sel, "label_atom_id": "CA"})


@control(MVS_EQUIVALENT, "residue_vs_its_atoms",
         "a residue's ball-and-stick selected atom by atom instead of as a residue")
def _(c: Ctx):
    if c.res is None:
        return None
    r = c.res
    names = sorted({c.e.table.columns["label_atom_id"][i] for i in range(c.e.table.n)
                    if r["mask"] >> i & 1})
    ref = c.highlight(r)
    pred = copy.deepcopy(ref)
    components(pred)[1]["params"]["selector"] = [{**c.e.auth(r), "label_atom_id": n} for n in names]
    return ref, pred


@control(MVS_EQUIVALENT, "overridden_colour",
         "a colour that a later colour node replaces (the last one wins)")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = c.highlight()
    pred = copy.deepcopy(ref)
    components(pred)[1]["children"][0]["children"].insert(0, col(c.c2))
    components(pred)[0]["children"][0]["children"].insert(0, col(c.c3))
    return ref, pred


@control(MVS_EQUIVALENT, "empty_extra_component",
         "an extra component that selects no atoms (nothing is drawn for it)")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = c.highlight()
    pred = copy.deepcopy(ref)
    components(pred).append(comp({"auth_asym_id": "zz9"}, rep("spacefill", col(c.c2))))
    return ref, pred


@control(MVS_EQUIVALENT, "focus_on_separate_component",
         "the focus node on its own component with the same selector", viewer=False)
def _(c: Ctx):
    if c.res is None:
        return None
    sel = c.e.auth(c.res)
    base = comp("polymer", rep("cartoon", col("gray")))
    ref = scene(c.e, [base, comp(sel, rep("ball_and_stick", col(c.c1)), {"kind": "focus", "params": {}})])
    pred = scene(c.e, [copy.deepcopy(base), comp(sel, rep("ball_and_stick", col(c.c1))),
                       comp(c.e.label(c.res), {"kind": "focus", "params": {}})])
    return ref, pred


@control(MVS_EQUIVALENT, "chain_theme_vs_one_colour_per_chain",
         "reference colours by the chain-id theme; the answer gives each chain its own colour",
         viewer=False)
def _(c: Ctx):
    chains = c.chains
    if not 2 <= len(chains) <= len(PALETTE):
        return None
    auth_ids = sorted({ch["auth_asym_id"] for ch in chains})
    if len(auth_ids) != len(chains):
        return None
    for ch in chains:
        if c.e.sel({"auth_asym_id": ch["auth_asym_id"]}) & c.e.polymer != ch["mask"]:
            return None
    ref = scene(c.e, [comp("polymer", rep("cartoon", col("white", theme="chain-id")))])
    colours = c.rng.sample(PALETTE, len(chains))
    pred = scene(c.e, [comp({"auth_asym_id": ch["auth_asym_id"]}, rep("cartoon", col(k)))
                       for ch, k in zip(chains, colours)])
    return ref, pred


@control(MVS_EQUIVALENT, "ribbon_type_on_non_polymer",
         "a cartoon asked for on a ligand or ion: Mol* draws ball-and-stick instead")
def _(c: Ctx):
    het = [s for s in ("ligand", "ion") if c.e.table.static.get(s, 0)
           and not c.e.table.static[s] & c.e.polymer]
    if not het:
        return None
    s = c.rng.choice(het)
    mk = lambda t: scene(c.e, [comp("polymer", rep("cartoon", col("gray"))),  # noqa: E731
                               comp(s, rep(t, col(c.c1)))])
    return mk("ball_and_stick"), mk(c.rng.choice(["cartoon", "backbone", "putty"]))


# --- MVS: wrong answers (must fail) ---------------------------------------------------

@control(MVS_WRONG, "residue_off_by_one", "the neighbouring residue is highlighted")
def _(c: Ctx):
    cands = [r for r in c.plain if c.neighbour(r)]
    if not cands:
        return None
    r = c.rng.choice(cands)
    return c.highlight(r), c.highlight(c.neighbour(r))


@control(MVS_WRONG, "wrong_chain", "the same residue number in another chain")
def _(c: Ctx):
    by_num: dict[int, list[dict]] = {}
    for r in c.plain:
        by_num.setdefault(r["auth_seq_id"], []).append(r)
    pairs = [(a, b) for rs in by_num.values() for a in rs for b in rs
             if a["auth_asym_id"] != b["auth_asym_id"]]
    if not pairs:
        return None
    a, b = c.rng.choice(pairs)
    return c.highlight(a), c.highlight(b)


@control(MVS_WRONG, "label_number_as_author_number",
         "the label residue number written in the author-number field (structures where they differ)")
def _(c: Ctx):
    cands = [r for r in c.plain if r["label_seq_id"] != r["auth_seq_id"]]
    if not cands:
        return None
    r = c.rng.choice(cands)
    ref = c.highlight(r)
    pred = copy.deepcopy(ref)
    components(pred)[1]["params"]["selector"] = {"auth_asym_id": r["auth_asym_id"],
                                                 "auth_seq_id": r["label_seq_id"]}
    return ref, pred


@control(MVS_WRONG, "author_number_as_label_number",
         "the author residue number written in the label-number field (structures where they differ)")
def _(c: Ctx):
    cands = [r for r in c.plain if r["label_seq_id"] != r["auth_seq_id"]]
    if not cands:
        return None
    r = c.rng.choice(cands)
    ref = c.highlight(r)
    pred = copy.deepcopy(ref)
    components(pred)[1]["params"]["selector"] = {"label_asym_id": r["label_asym_id"],
                                                 "label_seq_id": r["auth_seq_id"]}
    return ref, pred


@control(MVS_WRONG, "uniprot_number_as_author_number",
         "the UniProt residue number used as the author number (structures with an offset)")
def _(c: Ctx):
    table = sifts.load(c.e.id)
    if table is None:
        return None
    by_key = {(r["label_asym_id"], r["label_seq_id"]): r for r in c.plain}
    cands = []
    for row in table.rows:
        r = by_key.get((row.label_asym_id, row.label_seq_id))
        if r is not None and row.observed and row.auth_seq_id != row.unp_num:
            cands.append((r, row.unp_num))
    if not cands:
        return None
    r, unp = c.rng.choice(cands)
    ref = c.highlight(r)
    pred = copy.deepcopy(ref)
    components(pred)[1]["params"]["selector"] = {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": unp}
    return ref, pred


@control(MVS_WRONG, "wrong_colour", "the highlight in another palette colour")
def _(c: Ctx):
    if c.res is None:
        return None
    return c.highlight(colour=c.c1), c.highlight(colour=c.c2)


@control(MVS_WRONG, "near_miss_colour",
         "a neighbouring shade outside the tolerance (lightgray for gray, darkred for red, ...)")
def _(c: Ctx):
    if c.res is None:
        return None
    name, near = c.rng.choice([("gray", "lightgray"), ("gray", "silver"), ("red", "darkred"),
                               ("green", "lime"), ("blue", "navy"), ("orange", "gold"),
                               ("yellow", "khaki"), ("purple", "mediumpurple")])
    assert drawn.color_distance(drawn.COLOR_NAMES[name], drawn.COLOR_NAMES[near]) > drawn.COLOR_TOLERANCE
    mk = lambda k: scene(c.e, [comp("polymer", rep("cartoon", col(k)))])  # noqa: E731
    return mk(name), mk(near)


@control(MVS_WRONG, "wrong_representation", "the highlight in another representation type")
def _(c: Ctx):
    if c.res is None:
        return None
    a, b = c.rng.sample(["ball_and_stick", "spacefill", "surface", "line"], 2)
    return c.highlight(rtype=a), c.highlight(rtype=b)


@control(MVS_WRONG, "missing_component", "one requested component is not drawn")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = c.highlight()
    pred = copy.deepcopy(ref)
    components(pred).pop(c.rng.choice([0, 1]))
    return ref, pred


@control(MVS_WRONG, "extra_component", "something that was not asked for is drawn as well")
def _(c: Ctx):
    if c.res is None:
        return None
    ref = scene(c.e, [comp(c.e.auth(c.res), rep("ball_and_stick", col(c.c1)))])
    pred = copy.deepcopy(ref)
    extra = c.rng.choice([comp("polymer", rep("cartoon", col("gray"))),
                          comp("all", rep("line", col("gray"))),
                          comp("polymer", rep("surface", col("white"),
                                              {"kind": "opacity", "params": {"opacity": 0.3}}))])
    components(pred).insert(0, extra)
    return ref, pred


@control(MVS_WRONG, "wrong_ligand_copy", "another copy of the ligand than the one asked for")
def _(c: Ctx):
    ligs = [lg for lg in c.e.facts.get("ligands", []) if len(lg.get("copies", [])) >= 2]
    c.rng.shuffle(ligs)
    for lg in ligs:
        sels = [{"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"],
                 "label_comp_id": lg["comp_id"]} for cp in lg["copies"]]
        masks = [c.e.sel(s) for s in sels]
        ok = [i for i, m in enumerate(masks) if m and all(not m & o for j, o in enumerate(masks) if j != i)]
        if len(ok) >= 2:
            i, j = c.rng.sample(ok, 2)
            mk = lambda s: scene(c.e, [comp(s, rep("ball_and_stick", col(c.c1)))])  # noqa: E731
            return mk(sels[i]), mk(sels[j])
    return None


@control(MVS_WRONG, "wrong_entry", "the same scene on another structure", viewer=False)
def _(c: Ctx):
    ref = scene(c.e, [comp("polymer", rep("cartoon", col(c.c1)))])
    others = [i for i in panel_ids() if i != c.e.id and not i.startswith("af-")]
    other = entry(c.rng.choice(others))
    return ref, scene(other, copy.deepcopy(components(ref)))


@control(MVS_WRONG, "empty_scene", "the structure is loaded and nothing is drawn")
def _(c: Ctx):
    if c.res is None:
        return None
    return c.highlight(), scene(c.e, [])


@control(MVS_WRONG, "all_vs_polymer_ball_and_stick",
         "'all' instead of 'polymer' under ball-and-stick (waters and ligands are drawn too)")
def _(c: Ctx):
    if c.e.all == c.e.polymer:
        return None
    mk = lambda s: scene(c.e, [comp(s, rep("ball_and_stick", col(c.c1)))])  # noqa: E731
    return mk("polymer"), mk("all")


@control(MVS_WRONG, "wrong_opacity", "a transparent surface with another opacity, or opaque")
def _(c: Ctx):
    a, b = c.rng.choice([(0.5, 1.0), (0.3, 0.7), (0.5, 0.2)])
    mk = lambda o: scene(c.e, [comp("polymer", rep("surface", col(c.c1),  # noqa: E731
                                                   *([{"kind": "opacity", "params": {"opacity": o}}]
                                                     if o != 1.0 else [])))])
    return mk(a), mk(b)


@control(MVS_WRONG, "focus_wrong_or_missing", "the camera focus is on another residue, or absent",
         viewer=False)
def _(c: Ctx):
    if len(c.plain) < 2:
        return None
    r1, r2 = c.rng.sample(c.plain, 2)
    base = lambda: [comp("polymer", rep("cartoon", col("gray"))),  # noqa: E731
                    comp(c.e.auth(r1), rep("ball_and_stick", col(c.c1)))]
    ref = scene(c.e, base())
    components(ref)[1]["children"].append({"kind": "focus", "params": {}})
    pred = scene(c.e, base())
    if c.rng.random() < 0.5:
        components(pred).append(comp(c.e.auth(r2), {"kind": "focus", "params": {}}))
    return ref, pred


@control(MVS_WRONG, "label_text_wrong", "the residue label has another text", viewer=False)
def _(c: Ctx):
    if c.res is None:
        return None
    r = c.res
    mk = lambda text: scene(c.e, [comp(c.e.auth(r), rep("ball_and_stick", col(c.c1)),  # noqa: E731
                                       {"kind": "label", "params": {"text": text}})])
    return mk(f"{r['comp']} {r['auth_seq_id']}"), mk(f"{r['comp']} {r['auth_seq_id'] + 1}")


@control(MVS_WRONG, "chain_colours_swapped", "two chains' colours the wrong way round")
def _(c: Ctx):
    if len(c.chains) < 2:
        return None
    a, b = c.rng.sample(c.chains, 2)
    sel = lambda ch: {"label_asym_id": ch["label_asym_id"]}  # noqa: E731
    mk = lambda x, y: scene(c.e, [comp(sel(a), rep("cartoon", col(x))),  # noqa: E731
                                  comp(sel(b), rep("cartoon", col(y)))])
    return mk(c.c1, c.c2), mk(c.c2, c.c1)


@control(MVS_WRONG, "range_too_short", "a residue range that stops three residues early")
def _(c: Ctx):
    run = c.run(8)
    if not run:
        return None
    r = lambda hi: {"auth_asym_id": run[0]["auth_asym_id"], "beg_auth_seq_id": run[0]["auth_seq_id"],  # noqa: E731
                    "end_auth_seq_id": hi["auth_seq_id"]}
    mk = lambda s: scene(c.e, [comp("polymer", rep("cartoon", col("gray"))),  # noqa: E731
                               comp(s, rep("ball_and_stick", col(c.c1)))])
    return mk(r(run[-1])), mk(r(run[-4]))


@control(MVS_WRONG, "one_colour_for_chain_theme",
         "reference colours by chain; the answer paints every chain the same colour", viewer=False)
def _(c: Ctx):
    if len({ch["auth_asym_id"] for ch in c.chains}) < 2:
        return None
    ref = scene(c.e, [comp("polymer", rep("cartoon", col("white", theme="chain-id")))])
    return ref, scene(c.e, [comp("polymer", rep("cartoon", col(c.c1)))])


@control(MVS_WRONG, "assembly_instead_of_model",
         "the biological assembly is loaded where the deposited model was asked for", viewer=False)
def _(c: Ctx):
    if c.e.af:
        return None
    comps = [comp("polymer", rep("cartoon", col(c.c1)))]
    return scene(c.e, comps), scene(c.e, copy.deepcopy(comps), structure={"type": "assembly",
                                                                          "assembly_id": "1"})


@control(MVS_WRONG, "side_chain_atoms_only",
         "only the side chain is drawn where the whole residue was asked for")
def _(c: Ctx):
    if c.res is None:
        return None
    r = c.res
    ref = c.highlight(r)
    pred = copy.deepcopy(ref)
    names = sorted({c.e.table.columns["label_atom_id"][i] for i in range(c.e.table.n)
                    if r["mask"] >> i & 1} - {"N", "CA", "C", "O"})
    components(pred)[1]["params"]["selector"] = [{**c.e.auth(r), "label_atom_id": n} for n in names]
    return ref, pred


# --- API action lists -----------------------------------------------------------------

def load(e: Entry) -> dict:
    return {"action": "load", "molecule_id": e.id}


def rgb(name: str) -> dict:
    r, g, b = drawn.COLOR_NAMES[name]
    return {"r": r, "g": g, "b": b}


def api_auth(r: dict, **more: Any) -> dict:
    return {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["auth_seq_id"], **more}


def api_label(r: dict, **more: Any) -> dict:
    return {"struct_asym_id": r["label_asym_id"], "residue_number": r["label_seq_id"], **more}


def api_highlight(c: Ctx, r: dict | None = None, colour: str | None = None) -> list[dict]:
    r = r or c.res
    return [load(c.e), {"action": "color", "data": [api_auth(r, color=colour or c.c1)]}]


def _api(fn: Rewrite) -> Rewrite:
    """API controls are built on PDB entries only (an AlphaFold model needs custom_data)."""
    @functools.wraps(fn)
    def wrapped(c: Ctx):
        if c.e.af or c.res is None:
            return None
        return fn(c)
    return wrapped


@control(API_EQUIVALENT, "auth_chain_vs_label_chain",
         "struct_asym_id (label chain) instead of auth_asym_id for the same chain")
@_api
def _(c: Ctx):
    r = c.res
    ref = api_highlight(c, r)
    pred = copy.deepcopy(ref)
    pred[1]["data"] = [{"struct_asym_id": r["label_asym_id"], "auth_seq_id": r["auth_seq_id"],
                        "color": c.c1}]
    return ref, pred


@control(API_EQUIVALENT, "auth_seq_id_alias", "auth_residue_number instead of auth_seq_id")
@_api
def _(c: Ctx):
    r = c.res
    ref = api_highlight(c, r)
    pred = copy.deepcopy(ref)
    pred[1]["data"] = [{"auth_asym_id": r["auth_asym_id"], "auth_residue_number": r["auth_seq_id"],
                        "color": c.c1}]
    return ref, pred


@control(API_EQUIVALENT, "label_vs_author_residue",
         "struct_asym_id + residue_number (label) instead of auth_asym_id + auth_seq_id")
@_api
def _(c: Ctx):
    diff = [r for r in c.plain if r["auth_seq_id"] != r["label_seq_id"]] or c.plain
    r = c.rng.choice(diff)
    ref = api_highlight(c, r)
    pred = copy.deepcopy(ref)
    pred[1]["data"] = [api_label(r, color=c.c1)]
    return ref, pred


@control(API_EQUIVALENT, "residue_list_vs_range",
         "six residues one by one instead of a start/end range (label or author numbers)")
@_api
def _(c: Ctx):
    run = c.run()
    if not run:
        return None
    if c.rng.random() < 0.5:
        rng_p = {"struct_asym_id": run[0]["label_asym_id"], "start_residue_number": run[0]["label_seq_id"],
                 "end_residue_number": run[-1]["label_seq_id"], "color": c.c1}
    else:
        rng_p = {"auth_asym_id": run[0]["auth_asym_id"], "start_auth_residue_number": run[0]["auth_seq_id"],
                 "end_auth_residue_number": run[-1]["auth_seq_id"], "color": c.c1}
    return ([load(c.e), {"action": "color", "data": [rng_p]}],
            [load(c.e), {"action": "color", "data": [api_auth(r, color=c.c1) for r in run]}])


@control(API_EQUIVALENT, "colour_name_hex_or_rgb",
         "a colour as #rrggbb or as an {r,g,b} object instead of its name")
@_api
def _(c: Ctx):
    ref = api_highlight(c)
    pred = copy.deepcopy(ref)
    pred[1]["data"][0]["color"] = c.rng.choice([hexcolor(c.c1), hexcolor(c.c1, True), rgb(c.c1)])
    return ref, pred


@control(API_EQUIVALENT, "one_call_vs_two_kept",
         "two residues in one color call, or in two calls with keep_colors")
@_api
def _(c: Ctx):
    if len(c.plain) < 2:
        return None
    r1, r2 = c.rng.sample(c.plain, 2)
    one = [load(c.e), {"action": "color", "data": [api_auth(r1, color=c.c1), api_auth(r2, color=c.c2)]}]
    two = [load(c.e), {"action": "color", "data": [api_auth(r1, color=c.c1)]},
           {"action": "color", "data": [api_auth(r2, color=c.c2)], "keep_colors": True,
            "keep_representations": True}]
    return one, two


@control(API_EQUIVALENT, "independent_steps_reordered",
         "settings that do not interact, in another order")
@_api
def _(c: Ctx):
    steps = [{"action": "set_property", "name": "hide_water", "value": True},
             {"action": "set_property", "name": "bg_color", "value": "#000000"},
             {"action": "set_property", "name": "spin", "value": True}]
    paint = {"action": "color", "data": [api_auth(c.res, color=c.c1)]}
    ref = [load(c.e)] + steps + [paint]
    shuffled = steps[:]
    c.rng.shuffle(shuffled)
    return ref, [load(c.e), paint] + list(reversed(shuffled))


@control(API_EQUIVALENT, "no_op_steps", "steps that change nothing are added")
@_api
def _(c: Ctx):
    ref = api_highlight(c)
    pred = [ref[0], {"action": "clear_selection"}, {"action": "clear_tooltips"},
            {"action": "set_property", "name": "spin", "value": False},
            {"action": "reset", "camera": True}, ref[1], {"action": "clear_highlight"}]
    return ref, pred


@control(API_EQUIVALENT, "style_action_vs_property",
         "set_property visual_style instead of set_visual_style")
@_api
def _(c: Ctx):
    style = c.rng.choice(["ball-and-stick", "spacefill", "molecular-surface", "gaussian-surface"])
    paint = {"action": "color", "data": [api_auth(c.res, color=c.c1)]}
    return ([load(c.e), {"action": "set_visual_style", "style": style}, paint],
            [load(c.e), {"action": "set_property", "name": "visual_style", "value": style}, paint])


@control(API_EQUIVALENT, "entity_vs_chain", "an entity id instead of the entity's only chain")
@_api
def _(c: Ctx):
    cands = [ch for ch in c.chains
             if c.e.sel({"label_entity_id": ch["entity_id"]}) == c.e.sel({"label_asym_id": ch["label_asym_id"]})]
    if not cands:
        return None
    ch = c.rng.choice(cands)
    return ([load(c.e), {"action": "color", "data": [{"struct_asym_id": ch["label_asym_id"], "color": c.c2}]}],
            [load(c.e), {"action": "color", "data": [{"entity_id": ch["entity_id"], "color": c.c2}]}])


@control(API_EQUIVALENT, "ligand_by_name_vs_copies",
         "a ligand by residue name, or each copy by author chain and number")
@_api
def _(c: Ctx):
    lg = c.ligand()
    if lg is None:
        return None
    t = c.e.table
    by_name = ps.resolve_param(t, {"label_comp_id": lg["comp_id"]}, c.e.id)
    copies = [{"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"]} for cp in lg["copies"]]
    union = 0
    for p in copies:
        union |= ps.resolve_param(t, p, c.e.id)
    if union != by_name:
        return None
    return ([load(c.e), {"action": "color", "data": [{"label_comp_id": lg["comp_id"], "color": c.c1}]}],
            [load(c.e), {"action": "color", "data": [{**p, "color": c.c1} for p in copies]}])


@control(API_EQUIVALENT, "focus_flag_vs_focus_action",
         "focus: true inside the color call, or a separate focus action")
@_api
def _(c: Ctx):
    r = c.res
    return ([load(c.e), {"action": "color", "data": [api_auth(r, color=c.c1, focus=True)]}],
            [load(c.e), {"action": "color", "data": [api_auth(r, color=c.c1)]},
             {"action": "focus", "data": [api_label(r)]}])


@control(API_EQUIVALENT, "entry_id_case_or_url",
         "the entry id in upper case, or the same entry loaded by URL")
@_api
def _(c: Ctx):
    ref = api_highlight(c)
    pred = copy.deepcopy(ref)
    if c.rng.random() < 0.5:
        pred[0] = {"action": "load", "molecule_id": c.e.id.upper()}
    else:
        pred[0] = {"action": "load", "custom_data": {
            "url": f"https://www.ebi.ac.uk/pdbe/entry-files/download/{c.e.id}_updated.cif",
            "format": "cif", "binary": False}}
    return ref, pred


@control(API_EQUIVALENT, "uniprot_vs_author_number",
         "a residue by UniProt accession and number, or every mapped copy by author numbering")
@_api
def _(c: Ctx):
    table = sifts.load(c.e.id)
    if table is None:
        return None
    by_key = {(r["label_asym_id"], r["label_seq_id"]): r for r in c.plain}
    positions: dict[tuple, list] = {}
    for row in table.rows:
        if row.observed:
            positions.setdefault((row.accession, row.unp_num), []).append(row)
    cands = [(k, rows) for k, rows in positions.items()
             if all((x.label_asym_id, x.label_seq_id) in by_key for x in rows)]
    offset = [x for x in cands if any(y.auth_seq_id != x[0][1] for y in x[1])]
    pool = offset or cands
    if not pool:
        return None
    (acc, num), rows = c.rng.choice(sorted(pool, key=lambda x: x[0]))
    rs = [by_key[(x.label_asym_id, x.label_seq_id)] for x in rows]
    return ([load(c.e), {"action": "color", "data": [api_auth(r, color=c.c1) for r in rs]}],
            [load(c.e), {"action": "color", "data": [{"uniprot_accession": acc,
                                                       "uniprot_residue_number": num, "color": c.c1}]}])


@control(API_EQUIVALENT, "selections_reordered", "the selections of one call in another order")
@_api
def _(c: Ctx):
    if len(c.plain) < 3:
        return None
    rs = c.rng.sample(c.plain, 3)
    data = [api_auth(r, color=k) for r, k in zip(rs, (c.c1, c.c2, c.c3))]
    return ([load(c.e), {"action": "color", "data": data}],
            [load(c.e), {"action": "color", "data": list(reversed(copy.deepcopy(data)))}])


@control(API_EQUIVALENT, "rebuilt_after_a_wrong_step",
         "a wrong color call followed by the right one (only the final state counts)")
@_api
def _(c: Ctx):
    if len(c.plain) < 2:
        return None
    r1, r2 = c.rng.sample(c.plain, 2)
    ref = api_highlight(c, r1)
    return ref, [ref[0], {"action": "color", "data": [api_auth(r2, color=c.c2)]}, copy.deepcopy(ref[1])]


@control(API_EQUIVALENT, "tooltip_text_case_and_spaces",
         "tooltip text differing only in case and repeated spaces")
@_api
def _(c: Ctx):
    r = c.res
    text = f"{r['comp'].title()} {r['auth_seq_id']} of chain {r['auth_asym_id']}"
    mk = lambda t: [load(c.e), {"action": "tooltips", "data": [api_auth(r, tooltip=t)]}]  # noqa: E731
    return mk(text), mk("  " + text.upper().replace(" ", "  "))


@control(API_EQUIVALENT, "side_chain_flag_vs_representation",
         "sideChain: true instead of representation: ball-and-stick")
@_api
def _(c: Ctx):
    r = c.res
    mk = lambda **kw: [load(c.e), {"action": "color", "data": [api_auth(  # noqa: E731
        r, color=c.c1, representationColor=c.c1, **kw)]}]
    return mk(representation="ball-and-stick"), mk(sideChain=True)


# --- API: wrong answers ---------------------------------------------------------------

@control(API_WRONG, "residue_off_by_one", "the neighbouring residue is coloured")
@_api
def _(c: Ctx):
    cands = [r for r in c.plain if c.neighbour(r)]
    if not cands:
        return None
    r = c.rng.choice(cands)
    return api_highlight(c, r), api_highlight(c, c.neighbour(r))


@control(API_WRONG, "wrong_chain", "the same residue number in another chain")
@_api
def _(c: Ctx):
    by_num: dict[int, list[dict]] = {}
    for r in c.plain:
        by_num.setdefault(r["auth_seq_id"], []).append(r)
    pairs = [(a, b) for rs in by_num.values() for a in rs for b in rs
             if a["auth_asym_id"] != b["auth_asym_id"]]
    if not pairs:
        return None
    a, b = c.rng.choice(pairs)
    return api_highlight(c, a), api_highlight(c, b)


@control(API_WRONG, "author_number_as_label_number",
         "the author residue number given as residue_number, which is label numbering")
@_api
def _(c: Ctx):
    cands = [r for r in c.plain if r["label_seq_id"] != r["auth_seq_id"]]
    if not cands:
        return None
    r = c.rng.choice(cands)
    ref = api_highlight(c, r)
    pred = copy.deepcopy(ref)
    pred[1]["data"] = [{"struct_asym_id": r["label_asym_id"], "residue_number": r["auth_seq_id"],
                        "color": c.c1}]
    return ref, pred


@control(API_WRONG, "label_number_as_author_number",
         "the label residue number given as auth_seq_id")
@_api
def _(c: Ctx):
    cands = [r for r in c.plain if r["label_seq_id"] != r["auth_seq_id"]]
    if not cands:
        return None
    r = c.rng.choice(cands)
    ref = api_highlight(c, r)
    pred = copy.deepcopy(ref)
    pred[1]["data"] = [{"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["label_seq_id"],
                        "color": c.c1}]
    return ref, pred


@control(API_WRONG, "uniprot_number_as_author_number",
         "the UniProt residue number used as the author number (structures with an offset)")
@_api
def _(c: Ctx):
    table = sifts.load(c.e.id)
    if table is None:
        return None
    by_key = {(r["label_asym_id"], r["label_seq_id"]): r for r in c.plain}
    cands = [(by_key[(x.label_asym_id, x.label_seq_id)], x.unp_num) for x in table.rows
             if x.observed and x.auth_seq_id != x.unp_num and (x.label_asym_id, x.label_seq_id) in by_key]
    if not cands:
        return None
    r, unp = c.rng.choice(cands)
    ref = api_highlight(c, r)
    pred = copy.deepcopy(ref)
    pred[1]["data"] = [{"auth_asym_id": r["auth_asym_id"], "auth_seq_id": unp, "color": c.c1}]
    return ref, pred


@control(API_WRONG, "wrong_colour", "another palette colour")
@_api
def _(c: Ctx):
    return api_highlight(c, colour=c.c1), api_highlight(c, colour=c.c2)


@control(API_WRONG, "wrong_representation", "another representation type for the residue")
@_api
def _(c: Ctx):
    a, b = c.rng.sample(["ball-and-stick", "spacefill", "molecular-surface"], 2)
    mk = lambda t: [load(c.e), {"action": "color", "data": [api_auth(  # noqa: E731
        c.res, color=c.c1, representation=t, representationColor=c.c1)]}]
    return mk(a), mk(b)


@control(API_WRONG, "missing_step", "one requested step is left out")
@_api
def _(c: Ctx):
    ref = [load(c.e), {"action": "set_property", "name": "hide_water", "value": True},
           {"action": "set_visual_style", "style": "spacefill"},
           {"action": "color", "data": [api_auth(c.res, color=c.c1)]}]
    if not c.e.table.static.get("water", 0):
        ref.pop(1)
    pred = copy.deepcopy(ref)
    pred.pop(c.rng.randrange(1, len(pred)))
    return ref, pred


@control(API_WRONG, "extra_step", "something that was not asked for is done as well")
@_api
def _(c: Ctx):
    ref = api_highlight(c)
    extra = c.rng.choice([{"action": "set_visual_style", "style": "spacefill"},
                          {"action": "set_property", "name": "spin", "value": True},
                          {"action": "set_property", "name": "bg_color", "value": "#000000"},
                          {"action": "set_property", "name": "hide_polymer", "value": True}])
    return ref, [ref[0], extra, copy.deepcopy(ref[1])]


@control(API_WRONG, "wrong_ligand_copy", "another copy of the ligand than the one asked for")
@_api
def _(c: Ctx):
    ligs = [lg for lg in c.e.facts.get("ligands", []) if len(lg.get("copies", [])) >= 2]
    c.rng.shuffle(ligs)
    for lg in ligs:
        ps_ = [{"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"]} for cp in lg["copies"]]
        masks = [ps.resolve_param(c.e.table, p, c.e.id) for p in ps_]
        ok = [i for i, m in enumerate(masks) if m and all(not m & o for j, o in enumerate(masks) if j != i)]
        if len(ok) >= 2:
            i, j = c.rng.sample(ok, 2)
            mk = lambda p: [load(c.e), {"action": "color", "data": [{**p, "color": c.c1}]}]  # noqa: E731
            return mk(ps_[i]), mk(ps_[j])
    return None


@control(API_WRONG, "wrong_entry", "the same calls on another structure")
@_api
def _(c: Ctx):
    others = [i for i in panel_ids() if i != c.e.id and not i.startswith("af-")]
    ref = [load(c.e), {"action": "set_visual_style", "style": "spacefill"}]
    return ref, [{"action": "load", "molecule_id": c.rng.choice(others)}, copy.deepcopy(ref[1])]


@control(API_WRONG, "bare_load", "the structure is loaded and nothing else is done")
@_api
def _(c: Ctx):
    return api_highlight(c), [load(c.e)]


@control(API_WRONG, "colour_lost_without_keep",
         "a second color call without keep_colors wipes the first colour")
@_api
def _(c: Ctx):
    if len(c.plain) < 2:
        return None
    r1, r2 = c.rng.sample(c.plain, 2)
    ref = [load(c.e), {"action": "color", "data": [api_auth(r1, color=c.c1), api_auth(r2, color=c.c2)]}]
    pred = [load(c.e), {"action": "color", "data": [api_auth(r1, color=c.c1)]},
            {"action": "color", "data": [api_auth(r2, color=c.c2)]}]
    return ref, pred


@control(API_WRONG, "style_after_colour", "the global style is set after colouring, which wipes it")
@_api
def _(c: Ctx):
    paint = {"action": "color", "data": [api_auth(c.res, color=c.c1)]}
    style = {"action": "set_visual_style", "style": "spacefill"}
    return [load(c.e), style, paint], [load(c.e), paint, style]


@control(API_WRONG, "focus_wrong_or_missing", "the focus is on another residue, or absent")
@_api
def _(c: Ctx):
    if len(c.plain) < 2:
        return None
    r1, r2 = c.rng.sample(c.plain, 2)
    paint = {"action": "color", "data": [api_auth(r1, color=c.c1)]}
    ref = [load(c.e), paint, {"action": "focus", "data": [api_auth(r1)]}]
    pred = [load(c.e), paint] + ([{"action": "focus", "data": [api_auth(r2)]}]
                                 if c.rng.random() < 0.5 else [])
    return ref, pred


@control(API_WRONG, "range_too_short", "a residue range that stops three residues early")
@_api
def _(c: Ctx):
    run = c.run(8)
    if not run:
        return None
    mk = lambda hi: [load(c.e), {"action": "color", "data": [{  # noqa: E731
        "auth_asym_id": run[0]["auth_asym_id"], "start_auth_residue_number": run[0]["auth_seq_id"],
        "end_auth_residue_number": hi["auth_seq_id"], "color": c.c1}]}]
    return mk(run[-1]), mk(run[-4])


@control(API_WRONG, "colour_does_not_reach_added_representation",
         "color given where representationColor was needed: the added sticks stay element-coloured")
@_api
def _(c: Ctx):
    r = c.res
    return ([load(c.e), {"action": "color", "data": [api_auth(
                r, color=c.c1, representation="ball-and-stick", representationColor=c.c1)]}],
            [load(c.e), {"action": "color", "data": [api_auth(
                r, color=c.c1, representation="ball-and-stick")]}])


# --- building the set -----------------------------------------------------------------

def build(seed: int = SEED, per_kind: int = PER_KIND) -> dict[str, list[dict]]:
    ids = panel_ids()
    out: dict[str, list[dict]] = {"mvs": [], "api": []}
    for track, registries in (("mvs", (("equivalent", MVS_EQUIVALENT), ("wrong", MVS_WRONG))),
                              ("api", (("equivalent", API_EQUIVALENT), ("wrong", API_WRONG)))):
        identical: dict[str, Any] = {}
        for group, registry in registries:
            for kind, (what, fn, viewer) in registry.items():
                order = ids[:]
                random.Random(f"{seed}:{track}:{kind}").shuffle(order)
                n = 0
                for eid in order:
                    if n >= per_kind:
                        break
                    c = Ctx(entry(eid), int(hashlib.sha256(f"{seed}:{track}:{kind}".encode())
                                            .hexdigest()[:8], 16))
                    made = fn(c)
                    if made is None:
                        continue
                    ref, pred = made
                    n += 1
                    out[track].append({
                        "id": f"{track}-{group}-{kind}-{eid}", "track": track, "group": group,
                        "kind": kind, "what": what, "entry": eid,
                        "expect": "pass" if group == "equivalent" else "fail",
                        "viewer": viewer, "reference": ref, "prediction": pred})
                    identical.setdefault(json.dumps(ref, sort_keys=True), (kind, eid, ref))
        every = sorted(identical.values(), key=lambda x: (x[1], x[0], json.dumps(x[2], sort_keys=True)))
        random.Random(f"{seed}:{track}:identical").shuffle(every)
        for i, (kind, eid, ref) in enumerate(sorted(every[:N_IDENTICAL], key=lambda x: (x[0], x[1]))):
            out[track].append({
                "id": f"{track}-identical-{i:03d}-{kind}-{eid}", "track": track, "group": "identical",
                "kind": "identical", "what": "the answer is the reference itself", "entry": eid,
                "expect": "pass", "viewer": True, "reference": ref, "prediction": copy.deepcopy(ref)})
    return out


def as_task(ctl: dict) -> dict:
    if ctl["track"] == "mvs":
        return {"id": ctl["id"], "category": "mvs", "reference_mvs": ctl["reference"]}
    return {"id": ctl["id"], "category": "api_calling", "reference": ctl["reference"]}


def old_success(ctl: dict) -> bool:
    """Task success as the graders before this work would have called it (F1 = 1)."""
    try:
        if ctl["track"] == "mvs":
            return mvs.grade_mvs_paths(ctl["reference"], ctl["prediction"])["f1"] >= 1.0
        return grader.grade_sequence(ctl["reference"], ctl["prediction"])["f1"] >= 1.0
    except Exception:  # noqa: BLE001 - a crash is not a success
        return False


def _rate(k: int, n: int) -> dict:
    return {"errors": k, "n": n, "rate": round(k / n, 4) if n else None}


def summarise(controls: dict[str, list[dict]]) -> dict:
    """Grade every control and count the grader's mistakes."""
    summary: dict[str, Any] = {
        "what": "Grader control set: (reference, answer) pairs with a known verdict, built by "
                "scripts/grader_controls.py from the frozen structure panel. A false pass is a "
                "wrong answer graded as a task success; a false fail is an identical or "
                "equivalent answer graded as not a success.",
        "seed": SEED, "tracks": {}}
    for track, ctls in controls.items():
        kinds: dict[str, dict] = {}
        mistakes: list[dict] = []
        tally = {name: {"false_pass": 0, "false_fail": 0, "false_fail_equivalent": 0}
                 for name in ("new", "old")}
        n_must_pass = sum(c["expect"] == "pass" for c in ctls)
        n_must_fail = len(ctls) - n_must_pass
        n_equivalent = sum(c["group"] == "equivalent" for c in ctls)
        for c in ctls:
            g = grader.grade_task(as_task(c), c["prediction"])
            got = bool(g["success"])
            old = old_success(c)
            k = kinds.setdefault(f"{c['group']}:{c['kind']}", {
                "group": c["group"], "kind": c["kind"], "what": c["what"], "n": 0,
                "graded_success": 0, "old_grader_success": 0, "mean_f1": 0.0, "mean_target_f1": 0.0})
            k["n"] += 1
            k["graded_success"] += got
            k["old_grader_success"] += old
            k["mean_f1"] += g["f1"]
            k["mean_target_f1"] += g["target_f1"]
            want = c["expect"] == "pass"
            for name, verdict in (("new", got), ("old", old)):
                if verdict and not want:
                    tally[name]["false_pass"] += 1
                if not verdict and want:
                    tally[name]["false_fail"] += 1
                    tally[name]["false_fail_equivalent"] += c["group"] == "equivalent"
            if got != want:
                mistakes.append({"id": c["id"], "expect": c["expect"], "f1": g["f1"]})
            # consistency of the graded scores with the verdict
            if want and (g["f1"] != 1.0 or g["target_f1"] != 1.0):
                mistakes.append({"id": c["id"], "expect": "f1 = target_f1 = 1",
                                 "f1": g["f1"], "target_f1": g["target_f1"]})
            if not want and g["f1"] >= 1.0:
                mistakes.append({"id": c["id"], "expect": "f1 < 1", "f1": g["f1"]})
        for k in kinds.values():
            k["mean_f1"] = round(k["mean_f1"] / k["n"], 4)
            k["mean_target_f1"] = round(k["mean_target_f1"] / k["n"], 4)
        summary["tracks"][track] = {
            "n_controls": len(ctls),
            "n_identical": sum(c["group"] == "identical" for c in ctls),
            "n_equivalent": sum(c["group"] == "equivalent" for c in ctls),
            "n_wrong": n_must_fail,
            "n_equivalent_kinds": len({c["kind"] for c in ctls if c["group"] == "equivalent"}),
            "n_wrong_kinds": len({c["kind"] for c in ctls if c["group"] == "wrong"}),
            "n_entries": len({c["entry"] for c in ctls}),
            "grader": {"false_pass": _rate(tally["new"]["false_pass"], n_must_fail),
                       "false_fail": _rate(tally["new"]["false_fail"], n_must_pass),
                       "false_fail_equivalent_only": _rate(tally["new"]["false_fail_equivalent"],
                                                           n_equivalent)},
            "previous_grader": {
                "what": ("October path grader, F1 = 1 taken as success" if track == "mvs" else
                         "July sequence grader, F1 = 1 taken as success"),
                "false_pass": _rate(tally["old"]["false_pass"], n_must_fail),
                "false_fail": _rate(tally["old"]["false_fail"], n_must_pass),
                "false_fail_equivalent_only": _rate(tally["old"]["false_fail_equivalent"],
                                                    n_equivalent)},
            "mistakes": mistakes,
            "kinds": sorted(kinds.values(), key=lambda k: (k["group"], k["kind"])),
        }
    return summary


def dump_jsonl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows)


def write_all(controls: dict[str, list[dict]], check: bool = False) -> int:
    files = {OUT / f"{track}.jsonl": dump_jsonl(rows) for track, rows in controls.items()}
    files[OUT / "summary.json"] = json.dumps(summarise(controls), indent=1) + "\n"
    stale = 0
    OUT.mkdir(parents=True, exist_ok=True)
    for path, text in files.items():
        if check:
            if not path.exists() or path.read_text() != text:
                print(f"STALE: {path.relative_to(REPO)}")
                stale += 1
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(REPO)} ({len(text) // 1024} kB)")
    return stale


def load_controls(track: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / f"{track}.jsonl").read_text().splitlines()]


# --- Mol* as the oracle (MVS) ----------------------------------------------------------

_STATE_JS = """
async ({ mvs }) => {
  if (!window._viewer) window._viewer = await molstar.Viewer.create('app', { layoutIsExpanded: false,
    layoutShowControls: false, layoutShowSequence: false, layoutShowLog: false });
  const viewer = window._viewer, plugin = viewer.plugin;
  try { await viewer.loadMvsData(mvs, 'mvsj', { replaceExisting: true }); }
  catch (e) { return {error: String(e)}; }
  const busy = plugin.behaviors.state.isBusy;
  for (let t = 0; busy.value && t < 1200; t++) await new Promise(r => setTimeout(r, 50));
  await new Promise(r => setTimeout(r, 100));
  const decode = (os) => {
    const arr = [];
    if (typeof os === 'number') { const f = new Float64Array(1); const u = new Int32Array(f.buffer); f[0] = os;
      for (let k = u[0]; k < u[1]; k++) arr.push(k); }
    else for (let k = 0; k < os.length; k++) arr.push(os[k]);
    return arr; };
  const reps = [];
  for (const cell of plugin.state.data.cells.values()) {
    const repr = cell.obj && cell.obj.data && cell.obj.data.repr;
    const p = cell.transform.params || {};
    if (!repr || !p.type || !p.type.name || !repr.renderObjects) continue;
    const rec = {type: p.type.name, alpha: p.type.params && p.type.params.alpha,
                 theme: p.colorTheme && p.colorTheme.name, colors: {}};
    for (const ro of repr.renderObjects) {
      const v = ro.values;
      if (!v.uGroupCount || !v.drawCount.ref.value) continue;
      const ic = v.instanceCount.ref.value, gc = v.uGroupCount.ref.value;
      const ct = v.dColorType && v.dColorType.ref.value;
      const tex = v.tColor && v.tColor.ref.value && v.tColor.ref.value.array;
      for (let i = 0; i < ic; i++) for (let g = 0; g < gc; g++) {
        const l = repr.getLoci({objectId: ro.id, instanceId: i, groupId: g});
        if (!l || l.kind !== 'element-loci') continue;
        let rgb = -1;
        if (ct === 'uniform') { const c = v.uColor.ref.value;
          rgb = (Math.round(c[0]*255)<<16)|(Math.round(c[1]*255)<<8)|Math.round(c[2]*255); }
        else if (tex && ct === 'group') { rgb = (tex[g*3]<<16)|(tex[g*3+1]<<8)|tex[g*3+2]; }
        else if (tex && ct === 'groupInstance') { const o = (i*gc+g)*3; rgb = (tex[o]<<16)|(tex[o+1]<<8)|tex[o+2]; }
        else if (tex && ct === 'instance') { rgb = (tex[i*3]<<16)|(tex[i*3+1]<<8)|tex[i*3+2]; }
        for (const e of l.elements) {
          const src = e.unit.model.atomicHierarchy.atomSourceIndex;
          for (const k of decode(e.indices)) (rec.colors[rgb] = rec.colors[rgb] || []).push(src.value(e.unit.elements[k]));
        }
      }
    }
    reps.push(rec);
  }
  return {reps};
}
"""
_MOLSTAR_TYPES = {"ball-and-stick": "ball_and_stick", "molecular-surface": "surface",
                  "gaussian-surface": "surface", "cartoon": "cartoon", "backbone": "backbone",
                  "putty": "putty", "line": "line", "spacefill": "spacefill",
                  "carbohydrate": "carbohydrate"}
_RESIDUE_LEVEL = ("cartoon", "backbone", "putty", "carbohydrate")


class _CifHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, *args):
        pass


class Molstar:
    """Headless Mol* (the pinned bundle): the drawn state of an MVS scene, read back
    from the viewer's own representation objects."""

    def __init__(self, cache: pathlib.Path):
        self.cache = cache

    def __enter__(self):
        from playwright.sync_api import sync_playwright

        from molbench.render import _GL_ARGS, RENDER_HTML
        self.cache.mkdir(parents=True, exist_ok=True)
        self._server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(_CifHandler, directory=str(self.cache)))
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(args=_GL_ARGS)
        self._html = RENDER_HTML.as_uri()
        self._page = None
        self._n = 0
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        self._server.shutdown()

    def _local(self, tree: Any) -> tuple[Any, str | None]:
        """The scene with its download pointed at the frozen file (as plain mmCIF)."""
        tree = copy.deepcopy(tree)
        root = mvs.extract_root(tree)
        found: list[str] = []

        def walk(node: dict) -> None:
            if node.get("kind") == "download":
                eid = mvs.entry_of_url(node["params"]["url"])
                table = mvs._entry_table(eid)
                name = table.id if table is not None else eid
                path = self.cache / f"{name}.cif"
                frozen = grounding.structure_file(name)
                if frozen is None:
                    raise FileNotFoundError(f"no frozen structure file for {eid!r}")
                if not path.exists():
                    path.write_bytes(gzip.decompress(frozen.read_bytes()))
                node["params"]["url"] = f"http://127.0.0.1:{self._server.server_address[1]}/{name}.cif"
                found.append(eid)
            if node.get("kind") == "parse":
                node["params"]["format"] = "mmcif"
            for ch in node.get("children") or []:
                walk(ch)
        walk(root)
        return {"kind": "single", "root": root,
                "metadata": {"version": "1", "timestamp": "1970-01-01T00:00:00Z"}}, (found[0] if found else None)

    def state(self, tree: Any) -> dict[tuple, int] | str:
        """draw (type, rgb, opacity) -> atoms, as Mol* drew it; or an error string.
        Ribbon and carbohydrate draws are grown to whole residues, as in the grader."""
        state, eid = self._local(tree)
        if self._page is None or self._n >= 40:      # a fresh page now and then (memory)
            if self._page is not None:
                self._page.close()
            self._page = self._browser.new_page()
            self._page.set_default_timeout(240000)
            self._page.goto(self._html)
            self._n = 0
        self._n += 1
        got = self._page.evaluate(_STATE_JS, {"mvs": json.dumps(state)})
        if "error" in got:
            return got["error"]
        table = mvs._entry_table(eid)
        out: dict[tuple, int] = {}
        for rec in got["reps"]:
            rtype = _MOLSTAR_TYPES.get(rec["type"])
            if rtype is None:
                continue                 # labels and other helper representations
            for rgb, rows in rec["colors"].items():
                mask = atoms._mask(rows, table.n)
                if rtype in _RESIDUE_LEVEL:
                    mask = mvs._grow(table, mask)
                    if rtype != "carbohydrate":
                        mask &= table.static.get("polymer", 0)
                n = int(rgb)
                key = (rtype, ((n >> 16) & 255, (n >> 8) & 255, n & 255), round(float(rec["alpha"]), 3))
                if mask:
                    out[key] = out.get(key, 0) | mask
        return out


def grader_state(tree: Any) -> dict[tuple, int]:
    scene_ = mvs.resolve_scene(tree)
    out: dict[tuple, int] = {}
    for st in scene_.structures.values():
        for d, m in st.draws.items():
            out[d] = out.get(d, 0) | m
    return out


def states_equal(a: dict, b: dict, exact_colour: bool = False) -> bool:
    """Two drawn states as sets of classes; colours within the grader's tolerance, or
    exactly equal (what the viewer shows is compared exactly)."""
    pa, pb = drawn.partition(a), drawn.partition(b)
    if len(pa) != len(pb):
        return False
    left = list(pb)
    for m, look in pa:
        hit = next((x for x in left if x[0] == m and (
            sorted(look, key=repr) == sorted(x[1], key=repr) if exact_colour
            else drawn.look_eq(look, x[1]))), None)
        if hit is None:
            return False
        left.remove(hit)
    return True


def _grader_vs_viewer(tree: Any, seen: dict[tuple, int]) -> bool:
    """The grader's resolved state against Mol*'s. A theme colour has no fixed RGB in
    the grader, so draws with a theme token are compared by type, atoms and opacity."""
    mine = grader_state(tree)
    themed = {d for d in mine if not drawn._is_rgb(d[1])}
    if not themed:
        return states_equal(mine, seen, exact_colour=True)
    strip = lambda s: {(d[0], d[2]): 0 for d in s}  # noqa: E731
    a, b = strip(mine), strip(seen)
    for d, m in mine.items():
        a[(d[0], d[2])] |= m
    for d, m in seen.items():
        b[(d[0], d[2])] |= m
    return a == b


def rule_probes(e: Entry) -> dict:
    """One scene per entry that puts every representation type on several kinds of
    component, each in its own colour, so every draw can be told apart."""
    selectors: list[Any] = ["all", "polymer"]
    for s in ("ligand", "ion", "water", "branched"):
        if e.table.static.get(s, 0):
            selectors.append(s)
    plain = e.plain()
    if plain:
        r = plain[len(plain) // 2]
        selectors += [e.auth(r), {**e.auth(r), "label_atom_id": "CA"},
                      {"auth_asym_id": r["auth_asym_id"], "label_atom_id": "CB"}]
    comps = []
    n = 0
    for s in selectors:
        for t in mvs.REPRESENTATION_TYPES:
            n += 1
            comps.append(comp(s, rep(t, col(f"#{(n * 37) % 256:02x}{(n * 91) % 256:02x}{(n * 151) % 256:02x}"))))
    return scene(e, comps)


def viewer_check(controls: list[dict], cache: pathlib.Path, limit: int | None,
                 rules: bool = True) -> dict:
    """Check the MVS controls against Mol*: (1) the verdict - the viewer draws the same
    for a must-pass pair and something else for a must-fail pair; (2) the grader's
    resolved drawn state equals the viewer's, scene by scene; (3) the drawing rules,
    on every panel entry."""
    report: dict[str, Any] = {"molstar": (REPO / "molbench/static/molstar/VERSION").read_text().strip(),
                              "controls_checked": 0, "verdict_agrees": 0, "scenes_checked": 0,
                              "grader_state_agrees": 0, "problems": [], "skipped": 0}
    todo = [c for c in controls if c["viewer"]]
    report["skipped"] = len(controls) - len(todo)
    if limit:
        todo = todo[::max(1, len(todo) // limit)][:limit]
    cached: dict[str, Any] = {}
    with Molstar(cache) as viewer:
        def state_of(tree: Any) -> Any:
            key = json.dumps(tree, sort_keys=True)
            if key not in cached:
                try:
                    cached[key] = viewer.state(tree)
                except Exception as e:  # noqa: BLE001 - report it and go on
                    cached[key] = f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
                if not isinstance(cached[key], str):
                    report["scenes_checked"] += 1
                    ok = _grader_vs_viewer(tree, cached[key])
                    report["grader_state_agrees"] += ok
                    if not ok:
                        report["problems"].append({"what": "grader state differs from Mol*",
                                                   "scene": key[:300]})
            return cached[key]

        for i, c in enumerate(todo):
            a, b = state_of(c["reference"]), state_of(c["prediction"])
            if isinstance(a, str) or isinstance(b, str):
                report["problems"].append({"id": c["id"], "what": "viewer could not load",
                                           "detail": a if isinstance(a, str) else b})
                continue
            report["controls_checked"] += 1
            same = states_equal(a, b, exact_colour=False)
            if same == (c["expect"] == "pass"):
                report["verdict_agrees"] += 1
            else:
                report["problems"].append({"id": c["id"], "what": "viewer verdict differs",
                                           "viewer_same": same, "expect": c["expect"]})
            if (i + 1) % 50 == 0:
                print(f"  viewer: {i + 1}/{len(todo)} controls", flush=True)
        if rules:
            report["rule_probes"] = {"entries": 0, "draws_compared": 0, "agree": 0, "differ": []}
            rp = report["rule_probes"]
            for eid in panel_ids():
                tree = rule_probes(entry(eid))
                try:
                    seen = viewer.state(tree)
                except Exception as e:  # noqa: BLE001
                    seen = f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
                if isinstance(seen, str):
                    rp["differ"].append({"entry": eid, "error": seen})
                    continue
                rp["entries"] += 1
                mine = grader_state(tree)
                for key in sorted(set(mine) | set(seen), key=repr):
                    rp["draws_compared"] += 1
                    if mine.get(key, 0) == seen.get(key, 0):
                        rp["agree"] += 1
                    else:
                        rp["differ"].append({"entry": eid, "draw": drawn.show(key),
                                             "grader_atoms": mine.get(key, 0).bit_count(),
                                             "molstar_atoms": seen.get(key, 0).bit_count()})
                print(f"  rules: {eid} {'ok' if not any(d.get('entry') == eid for d in rp['differ']) else 'DIFFERS'}",
                      flush=True)
    return report


def viewer_check_api(controls: list[dict], n: int) -> dict:
    """Replay against real pdbe-molstar for a sample of API answers (both sides)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_api_refs", REPO / "scripts/check_api_refs.py")
    car = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(car)
    report = {"pdbe_molstar": getattr(car, "PDBE_VERSION", "?"), "lists_run": 0, "agree": 0,
              "problems": [], "note": "the replayed end state is compared with the real viewer's "
              "(selections atom for atom, components, representations, overpaint); focus, "
              "highlight and UniProt selections are not read back"}
    by_kind: dict[str, list[dict]] = {}
    for c in controls:
        by_kind.setdefault(c["kind"], []).append(c)
    picked: list[dict] = []
    for i in range(max(len(v) for v in by_kind.values())):
        for kind in sorted(by_kind):
            if i < len(by_kind[kind]) and len(picked) < n:
                picked.append(by_kind[kind][i])
    with car.Viewer() as viewer:
        for c in picked:
            for side in ("reference", "prediction"):
                actions = c[side]
                if any("uniprot_accession" in p for a in actions for p in a.get("data", []) or []
                       if isinstance(p, dict)) or any("custom_data" in a for a in actions):
                    continue                 # needs PDBe's updated file: checked by check_api_refs --uniprot
                try:
                    dump = viewer.run(actions)
                    bad = car.compare_with_viewer(actions, dump)
                except Exception as e:  # noqa: BLE001
                    bad = [f"failed to run: {str(e).splitlines()[0][:200]}"]
                report["lists_run"] += 1
                report["agree"] += not bad
                if bad:
                    report["problems"].append({"id": c["id"], "side": side, "detail": bad[:3]})
            print(f"  api viewer: {c['id']}", flush=True)
    return report


# --- October regrade -------------------------------------------------------------------

_TIERS = {"mvs": "translation", "generated": "translation", "grounded": "structure-grounded",
          "interactions": "structure-grounded", "resolve": "structure-grounded",
          "clinvar-variant": "clinical", "sifts-named": "clinical", "clinvar-hotspots": "clinical"}


def _highlight_target(reference: Any) -> dict | None:
    """A target by rule for a reference that draws context: the atoms of its components
    whose selector is an expression (not a static name such as 'polymer')."""
    sels: list = []
    static = False

    def walk(node: dict) -> None:
        nonlocal static
        if node.get("kind") == "component":
            sel = (node.get("params") or {}).get("selector", "all")
            if isinstance(sel, str):
                static = static or sel in ("all", "polymer", "protein", "nucleic")
            else:
                sels.extend(sel if isinstance(sel, list) else [sel])
        for ch in node.get("children") or []:
            if isinstance(ch, dict):
                walk(ch)
    walk(mvs.extract_root(reference))
    return {"selector": sels} if sels and static else None


def october_regrade(results: pathlib.Path) -> tuple[dict, dict]:
    """Old F1 (as stored in October), new F1, task success and target score for the
    October MVS predictions, per model and per tier. Reads the scorecards only."""
    from molbench.runner import load_tasks
    tasks = {t["id"]: t for t in load_tasks(["mvs"])}
    rows = []
    colours = {"n": 0, "exact": 0, "invalid": 0, "by_distance": {}, "nearest_inexact": []}

    def colour_values(x: Any, out: list) -> list:
        if isinstance(x, dict):
            if x.get("kind") == "color" and isinstance(x.get("params"), dict) and "color" in x["params"] \
                    and not (x.get("custom") or {}).get("molstar_color_theme_name"):
                out.append(x["params"]["color"])
            for v in x.values():
                colour_values(v, out)
        elif isinstance(x, list):
            for v in x:
                colour_values(v, out)
        return out

    for cond in ("spec", "spec_grounded", "bare"):
        for path in sorted((results / cond).glob("*.json")):
            card = json.loads(path.read_text())
            for model, m in card["models"].items():
                for t in m["tasks"]:
                    task = tasks.get(t["id"])
                    if task is None:
                        continue
                    valid = t.get("outcome") == "valid"
                    pred = t.get("predicted")
                    new = {"f1": 0.0, "success": False, "target_f1": 0.0}
                    old_regraded = 0.0
                    strict_focus = False
                    highlight = _highlight_target(task["reference_mvs"])
                    highlight_f1 = None if highlight is None else 0.0
                    if valid and isinstance(pred, dict):
                        g = grader.grade_task(task, pred)
                        new = {k: g[k] for k in new}
                        drawn.GRADE_UNREQUESTED_FOCUS = True
                        try:
                            strict_focus = bool(grader.grade_task(task, pred)["success"])
                        finally:
                            drawn.GRADE_UNREQUESTED_FOCUS = False
                        if highlight is not None:
                            highlight_f1 = grader.grade_task({**task, "target": highlight}, pred)["target_f1"]
                        old_regraded = mvs.grade_mvs_paths(task["reference_mvs"], pred,
                                                           task.get("accepted_ids"))["f1"]
                        ref_cols = [k for k in map(drawn.mvs_color, colour_values(task["reference_mvs"], []))
                                    if drawn._is_rgb(k)]
                        for raw in colour_values(pred, []):
                            colours["n"] += 1
                            k = drawn.mvs_color(raw)
                            if not drawn._is_rgb(k):
                                colours["invalid"] += 1
                            elif not ref_cols:
                                colours["no_reference_colour"] = colours.get("no_reference_colour", 0) + 1
                            else:
                                d = min(drawn.color_distance(k, r) for r in ref_cols)
                                colours["exact"] += d == 0
                                if d:
                                    b = ("1-16" if d <= 16 else "17-32" if d <= 32 else "33-48" if d <= 48
                                         else "49-64" if d <= 64 else "over 64")
                                    colours["by_distance"][b] = colours["by_distance"].get(b, 0) + 1
                                    colours["nearest_inexact"].append((d, str(raw)))
                    rows.append({"condition": cond, "model": model, "task": t["id"],
                                 "tier": _TIERS.get(task.get("source") or "mvs", "other"),
                                 "source": task.get("source") or "hand-written",
                                 "outcome": t.get("outcome"), "old_f1_stored": t["f1"],
                                 "old_f1": old_regraded, "new_f1": new["f1"],
                                 "success": bool(new["success"]), "target_f1": new["target_f1"],
                                 "success_if_any_focus_counts": strict_focus,
                                 "highlight_target_f1": highlight_f1})

    def mean(xs: list) -> float | None:
        return round(sum(xs) / len(xs), 4) if xs else None

    def cell(rs: list[dict]) -> dict:
        valid = [r for r in rs if r["outcome"] == "valid"]
        return {"n": len(rs), "valid": len(valid),
                "old_f1_stored": mean([r["old_f1_stored"] for r in rs]),
                "old_f1": mean([r["old_f1"] for r in rs]), "new_f1": mean([r["new_f1"] for r in rs]),
                "success": mean([float(r["success"]) for r in rs]),
                "target_f1": mean([r["target_f1"] for r in rs]),
                "success_if_any_focus_counts": mean([float(r["success_if_any_focus_counts"]) for r in rs]),
                "highlight_target_f1": mean([r["highlight_target_f1"] for r in rs
                                             if r["highlight_target_f1"] is not None]),
                "n_with_highlight_target": sum(r["highlight_target_f1"] is not None for r in rs),
                "highlight_exactly_right": mean([float(r["highlight_target_f1"] == 1.0) for r in rs
                                                 if r["highlight_target_f1"] is not None]),
                "old_f1_was_1": mean([float(r["old_f1"] >= 1.0) for r in rs]),
                "valid_only": {"old_f1": mean([r["old_f1"] for r in valid]),
                               "new_f1": mean([r["new_f1"] for r in valid]),
                               "success": mean([float(r["success"]) for r in valid]),
                               "target_f1": mean([r["target_f1"] for r in valid])}}

    out: dict[str, Any] = {
        "what": "October 2026 MVS predictions (results/r2x2, one sample per task) regraded. "
                "old_f1_stored: the F1 in the October scorecard. old_f1: the October path grader "
                "(mvs.grade_mvs_paths) run today on the same prediction and today's reference. "
                "new_f1, success, target_f1: the drawn-state grader. Strict scoring: a scene Mol* "
                "rejected, or a reply that is not a scene, scores 0 on every measure; valid_only "
                "averages over the scenes Mol* accepted. No task has a target field yet, so the "
                "target is everything the reference draws. highlight_target_f1 is the target score "
                "with the target set by rule to the atoms of the reference's components that are "
                "not a whole-structure selector ('polymer', 'all', ...): the residues or ligand the "
                "request is about, without the context cartoon (tasks with no such component are "
                "left out; n_with_highlight_target counts the rest). success_if_any_focus_counts: "
                "task success if a camera focus the request did not ask for is counted as wrong "
                "(drawn.GRADE_UNREQUESTED_FOCUS = True; the default is not to count it).",
        "references": "tasks/ as of this commit (the clinical and other references still draw "
                      "context the prompts do not ask for; decision 17 replaces them)",
        "conditions": {}}
    for cond in ("spec", "spec_grounded", "bare"):
        rs = [r for r in rows if r["condition"] == cond]
        if not rs:
            continue
        models = sorted({r["model"] for r in rs})
        tiers = sorted({r["tier"] for r in rs})
        out["conditions"][cond] = {
            "all": cell(rs),
            "by_model": {m: cell([r for r in rs if r["model"] == m]) for m in models},
            "by_tier": {t: cell([r for r in rs if r["tier"] == t]) for t in tiers},
            "by_model_and_tier": {m: {t: cell([r for r in rs if r["model"] == m and r["tier"] == t])
                                      for t in tiers} for m in models}}
    near = sorted(colours.pop("nearest_inexact"))[:10]
    palette = drawn.TASK_PALETTE
    pairs = sorted((drawn.color_distance(drawn.COLOR_NAMES[a], drawn.COLOR_NAMES[b]), a, b)
                   for a, b in itertools.combinations(palette, 2))
    evidence = {
        "tolerance": drawn.COLOR_TOLERANCE,
        "what": "Evidence for the colour tolerance. Distance = largest per-channel difference (0-255).",
        "palette": list(palette),
        "closest_palette_pairs": [{"distance": d, "a": a, "b": b} for d, a, b in pairs[:8]],
        "october_colours": {**colours, "what": "every colour value in a valid October MVS scene, by "
                            "its distance to the nearest colour of that task's reference",
                            "closest_inexact": [{"distance": d, "written": w} for d, w in near]}}
    return out, evidence


# --- main ------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if the files on disk are stale")
    ap.add_argument("--viewer", action="store_true", help="check MVS controls and drawing rules in Mol*")
    ap.add_argument("--limit", type=int, help="with --viewer: check about this many controls")
    ap.add_argument("--no-rules", action="store_true", help="with --viewer: skip the per-entry rule probes")
    ap.add_argument("--viewer-api", type=int, metavar="N", help="check N API controls in pdbe-molstar")
    ap.add_argument("--october", type=pathlib.Path, metavar="DIR",
                    help="regrade the October scorecards in DIR (e.g. results/r2x2)")
    ap.add_argument("--cache", type=pathlib.Path, default=REPO / "data" / "cif",
                    help="where to unpack structure files for the viewer (git-ignored)")
    args = ap.parse_args()

    if args.october:
        regrade, evidence = october_regrade(args.october)
        for name, data in (("october_regrade.json", regrade), ("colour_evidence.json", evidence)):
            (OUT / name).write_text(json.dumps(data, indent=1) + "\n")
            print(f"wrote tests/controls/{name}")
        return 0

    controls = build()
    if args.viewer or args.viewer_api:
        path = OUT / "viewer_check.json"
        report = json.loads(path.read_text()) if path.exists() else {}
        if args.viewer:
            report["mvs"] = viewer_check(controls["mvs"], args.cache, args.limit, not args.no_rules)
        if args.viewer_api:
            report["api"] = viewer_check_api(controls["api"], args.viewer_api)
        path.write_text(json.dumps(report, indent=1) + "\n")
        print(f"wrote {path.relative_to(REPO)}")
        for track, r in report.items():
            print(track, {k: v for k, v in r.items() if k not in ("problems", "rule_probes", "note")},
                  f"{len(r.get('problems', []))} problem(s)")
        return 0

    stale = write_all(controls, check=args.check)
    summary = json.loads((OUT / "summary.json").read_text()) if not args.check else summarise(controls)
    for track, s in summary["tracks"].items():
        print(f"{track}: {s['n_controls']} controls ({s['n_identical']} identical, "
              f"{s['n_equivalent']} equivalent in {s['n_equivalent_kinds']} kinds, "
              f"{s['n_wrong']} wrong in {s['n_wrong_kinds']} kinds) on {s['n_entries']} entries; "
              f"false pass {s['grader']['false_pass']['errors']}/{s['grader']['false_pass']['n']}, "
              f"false fail {s['grader']['false_fail']['errors']}/{s['grader']['false_fail']['n']}; "
              f"previous grader: false pass {s['previous_grader']['false_pass']['errors']}, "
              f"false fail {s['previous_grader']['false_fail']['errors']}")
        for m in s["mistakes"][:20]:
            print("   MISTAKE", m)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
