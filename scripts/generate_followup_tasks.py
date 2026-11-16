#!/usr/bin/env python3
"""
Generate the follow-up tier (issue #5): two-turn tasks on both tracks.

A follow-up task is a start state (an MVS scene, or the calls made so far), an edit
request, and the complete final state as the reference. Everything is built by this
script from the frozen panel (``data/panel/facts``, ``molbench/atom_tables``): the
start state is put together from a handful of components, the edit is applied to
that same component list, and both are written out as a scene / a call list. Nothing
is typed by hand and nothing is fetched.

    uv run python scripts/generate_followup_tasks.py           # rewrite the files
    uv run python scripts/generate_followup_tasks.py --check   # fail if they would change
    uv run python scripts/generate_followup_tasks.py --heldback-file ids.txt
    uv run python scripts/generate_followup_tasks.py --viewer  # states against the real viewers

Outputs ``tasks/mvs_followup/*.json``, ``tasks/api_followup/*.json`` and a README in
each directory (templates, counts, how every reference is derived). The run is
deterministic: every choice (structure, colours, wording, residue) comes from
``SEED`` and the task's family and number, so a rerun reproduces the files byte for
byte.

Rules the script enforces on itself, and fails on:

* every task passes ``molbench.tasks.validate_task`` and the corpus checks
  (``check_corpus`` with the benchmark grader): the reference grades as exactly
  right with target score 1, the start state grades as itself, ``noop`` agrees with
  the grader, twins select the same target atoms;
* every *preserved* part (``provenance.preserved``: what the edit must leave alone)
  scores 1 as a target on both the start state and the reference;
* on a task with a target that is not a no-op, the start state does not already
  score 1 on the target;
* each *control* written next to a template grades as the template says: an
  equivalent way of writing the final state succeeds, a clobbering answer (the edit
  made on an empty viewer, the earlier choices lost) does not;
* no structure in more than ``MAX_PER_TRACK`` tasks of a track, no family twice on
  one structure, no family above ``MAX_FAMILY_SHARE`` of a track, 1HSG never.

Held-back split: a structure is held back when it is among the fifth of the panel
with the smallest SHA-256 of ``"molbench-heldback-v1:<id>"``. The rule depends on the
structure alone, not on this tier, so any other generator can apply it and agree;
``--heldback-file`` (one id per line) replaces it with a list agreed elsewhere.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import sys
from collections import Counter
from typing import Any, Callable

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import additives  # noqa: E402
from molbench import drawn, grounding, runner, tasks as T  # noqa: E402
from molbench.atoms import load_table  # noqa: E402

SCRIPT = "scripts/generate_followup_tasks.py"
SEED = 20261113
DATE = "2026-11-13"       # fixed, so a rebuild is byte-identical
OUT = {"mvs": REPO / "tasks" / "mvs_followup", "api": REPO / "tasks" / "api_followup"}
MAX_ATOMS = 15000         # the panel's own size limit; the two exempt entries are left out
MAX_PER_TRACK = 3         # tasks of one track on one structure (so at most 6 in the tier)
MAX_FAMILY_SHARE = 0.12
HELDBACK_SHARE = 0.20
HELDBACK_SALT = "molbench-heldback-v1"
HELDBACK_FILE = REPO / "data" / "panel" / "heldback.json"   # a JSON list; replaces the rule

# Colours a request may name: the task palette, without white (an MVS representation
# with no colour node is white, so "white" would not be a visible change), black (kept
# for the background template) and limegreen (said aloud it is "lime green", which an
# answer could as well write "lime", another colour).
COLOURS = tuple(c for c in drawn.TASK_PALETTE if c not in ("white", "black", "limegreen"))
# how a British-English request says a palette name
SAY = {"gray": "grey", "hotpink": "hot pink", "steelblue": "steel blue"}
AMINO = ("ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "HIS", "ILE", "LEU", "LYS", "MET",
         "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL")   # the 20 without glycine


def rng(*key: Any) -> random.Random:
    return random.Random("|".join(str(k) for k in (SEED,) + key))


def say(colour: str) -> str:
    return SAY.get(colour, colour)


# --------------------------------------------------------------------------- #
# The panel, as this tier sees it
# --------------------------------------------------------------------------- #
class Entry:
    """One panel structure and the facts the templates need, all from frozen files."""

    def __init__(self, record: dict):
        self.id: str = record["id"]
        self.facts: dict = grounding.facts(self.id)
        self.table = load_table(self.id)
        self.chains: list[dict] = self.facts["chains"]          # polymer chains
        kinds = {c["polymer_type"] for c in self.chains}
        self.noun = {frozenset(["protein"]): "protein", frozenset(["RNA"]): "RNA",
                     frozenset(["DNA"]): "DNA"}.get(frozenset(kinds))
        self.has_water = bool(self.table.static.get("water"))
        self.ligand = self._main_ligand()
        # A polymer residue bonded to a ligand, ion or sugar (a heme's histidine, a
        # glycosylated asparagine) is drawn as ball-and-stick with it by the PDBe viewer.
        self.bonded = bool(self.facts["covalent_links"] or self.facts["metal_bonds"])
        self.numbering = self.facts["numbering"]

    def _main_ligand(self) -> dict | None:
        """The structure's main ligand: its biological ligand with the most heavy atoms
        (at least 9); ties go to the component code. A biological ligand is a
        non-polymer component of kind ``ligand`` that is not on the corpus list of
        crystallisation additives, buffers, detergents and lipids
        (``data/corpus/additives.json``): tartrate in 1D5R, the detergent of 2OMF and
        the PEG fragment of 6THA are not what "the ligand" means."""
        hits = [x for x in self.facts["ligands"] if additives.is_biological(x)
                and x["n_heavy_atoms"] >= 9 and self.table.selector({"label_comp_id": x["comp_id"]})]
        return min(hits, key=lambda x: (-x["n_heavy_atoms"], x["comp_id"])) if hits else None

    # --- how a request names things -------------------------------------------
    def ligand_words(self) -> str:
        lig = self.ligand
        name, comp, many = lig["name"].strip().lower(), lig["comp_id"], len(lig["copies"]) > 1
        plain = re.fullmatch(r"[a-z]+( [a-z]+)?", name) is not None and len(name) <= 24
        if plain:
            return f"the {name} molecules ({comp})" if many else f"the {name} ({comp})"
        return f"the {comp} ligands" if many else f"the ligand {comp}"

    def chain_pair(self) -> tuple[dict, dict] | None:
        """The two chains the chain templates work on: the first two protein chains,
        else the first two polymer chains, by author chain id as the file lists them."""
        proteins = [c for c in self.chains if c["polymer_type"] == "protein"]
        pool = proteins if len(proteins) >= 2 else self.chains
        if len(pool) < 2 or pool[0]["auth_asym_id"] == pool[1]["auth_asym_id"]:
            return None
        return pool[0], pool[1]

    def residue(self, r: random.Random) -> dict | None:
        """A residue of the first protein chain that a request can name as "Arg45 of
        chain A": a standard amino acid other than glycine, no insertion code, and
        author chain + author number select exactly that residue's atoms. Where the
        chain's author numbers differ from the file's sequence positions, one of those
        residues is taken, so the numbering offset matters."""
        chain = next((c for c in self.chains if c["polymer_type"] == "protein"), None)
        if chain is None:
            return None
        col = self.table.columns
        rows: dict[tuple, list[int]] = {}
        for i in range(self.table.n):
            if col["label_asym_id"][i] == chain["label_asym_id"]:
                rows.setdefault((col["auth_seq_id"][i], col["pdbx_PDB_ins_code"][i],
                                 col["label_seq_id"][i], col["label_comp_id"][i]), []).append(i)
        good = []
        for (auth, ins, label, comp), idx in rows.items():
            sel = {"auth_asym_id": chain["auth_asym_id"], "auth_seq_id": auth}
            if ins == "" and comp in AMINO and \
                    self.table.selector(sel) == sum(1 << i for i in idx):
                good.append({"auth_asym_id": chain["auth_asym_id"], "auth_seq_id": auth,
                             "label_asym_id": chain["label_asym_id"], "label_seq_id": label,
                             "comp": comp})
        shifted = [g for g in good if g["auth_seq_id"] != g["label_seq_id"]]
        pool = sorted(shifted or good, key=lambda g: g["auth_seq_id"])
        return r.choice(pool) if pool else None


def entries() -> list[Entry]:
    out = []
    for rec in grounding.panel()["entries"]:
        if rec["kind"] != "pdb" or rec["id"] == T.WORKED_EXAMPLE or rec["models"] != 1 \
                or rec["atoms"] > MAX_ATOMS or load_table(rec["id"]) is None:
            continue
        out.append(Entry(rec))
    return sorted(out, key=lambda e: e.id)


def heldback_ids(listed: set[str] | None = None) -> set[str]:
    """The held-back structures: a rule on the structure id alone (see the module
    docstring), or the list given with ``--heldback-file``."""
    if listed is not None:
        return listed
    if HELDBACK_FILE.exists():      # the corpus-wide list, frozen at integration
        return {str(i).lower() for i in json.loads(HELDBACK_FILE.read_text(encoding="utf-8"))}
    ids = sorted(rec["id"] for rec in grounding.panel()["entries"]
                 if rec["kind"] == "pdb" and rec["id"] != T.WORKED_EXAMPLE)
    ranked = sorted(ids, key=lambda i: hashlib.sha256(f"{HELDBACK_SALT}:{i}".encode()).hexdigest())
    return set(ranked[:round(len(ids) * HELDBACK_SHARE)])


# --------------------------------------------------------------------------- #
# Writing the two formats
# --------------------------------------------------------------------------- #
def comp(selector: Any, rep: str, colour: str | None = None, *, opacity: float | None = None,
         label: str | None = None, focus: bool = False) -> dict:
    """One drawn component of an MVS scene, as a plain record (see `mvs_scene`)."""
    return {"selector": selector, "rep": rep, "colour": colour, "opacity": opacity,
            "label": label, "focus": focus}


def mvs_scene(entry: str, comps: list[dict], background: str | None = None) -> dict:
    nodes = []
    for c in comps:
        rep = {"kind": "representation", "params": {"type": c["rep"]}}
        inner = []
        if c["colour"]:
            inner.append({"kind": "color", "params": {"color": c["colour"]}})
        if c["opacity"] is not None:
            inner.append({"kind": "opacity", "params": {"opacity": c["opacity"]}})
        if inner:
            rep["children"] = inner
        children = [rep]
        if c["label"]:
            children.append({"kind": "label", "params": {"text": c["label"]}})
        if c["focus"]:
            children.append({"kind": "focus"})
        nodes.append({"kind": "component", "params": {"selector": c["selector"]},
                      "children": children})
    root = [{"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{entry}.cif"},
             "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
                 {"kind": "structure", "params": {"type": "model"}, "children": nodes}]}]}]
    if background:
        root.append({"kind": "canvas", "params": {"background_color": background}})
    return {"root": {"kind": "root", "children": root}}


def load(entry: str) -> dict:
    return {"action": "load", "molecule_id": entry}


def paint(params: list[dict], keep: bool = False) -> dict:
    call = {"action": "color", "data": params}
    if keep:
        call.update(keep_colors=True, keep_representations=True)
    return call


def prop(name: str, value: Any) -> dict:
    return {"action": "set_property", "name": name, "value": value}


def part(selector: Any, rep: str | None = None, colour: str | None = None) -> dict:
    """One part of a target (or of ``provenance.preserved``), in the task format."""
    return {"selector": selector, "representation": rep, "color": colour}


# --- the pieces the templates share --------------------------------------------
def lig_sel(e: Entry) -> dict:
    return {"label_comp_id": e.ligand["comp_id"]}


def api_polymer(e: Entry, colour: str) -> list[dict]:
    """The whole polymer in one colour on the API track: one selection per polymer
    chain, by label chain id (``struct_asym_id``), so no ligand or water is caught."""
    return [{"struct_asym_id": c["label_asym_id"], "color": colour} for c in e.chains]


def api_polymer_part(e: Entry, colour: str) -> dict:
    return part([{"label_asym_id": c["label_asym_id"]} for c in e.chains], None, colour)


def polymer_without(e: Entry, res: dict, rep: str | None, colour: str) -> dict:
    """The polymer except one residue, as a preserved part: the other chains whole, and
    the residue's chain as the label-number ranges before and after it."""
    sels = []
    for c in e.chains:
        chain = {"label_asym_id": c["label_asym_id"]}
        if c["label_asym_id"] != res["label_asym_id"]:
            sels.append(chain)
            continue
        for side in ({**chain, "end_label_seq_id": res["label_seq_id"] - 1},
                     {**chain, "beg_label_seq_id": res["label_seq_id"] + 1}):
            if e.table.selector(side):
                sels.append(side)
    return part(sels, rep, colour)


def chain_sel(chain: dict) -> dict:
    return {"auth_asym_id": chain["auth_asym_id"]}


class Pair:
    """Protein + main ligand, the commonest start state. MVS: polymer as a cartoon in
    ``c1``, the ligand as ball-and-stick in ``c2``. API: a load, then one ``color``
    call painting the polymer chains ``c1`` and the ligand ``c2``."""

    def __init__(self, e: Entry, c1: str, c2: str):
        self.e, self.c1, self.c2 = e, c1, c2

    def mvs(self, c1=None, c2=None, **lig) -> list[dict]:
        return [comp("polymer", "cartoon", c1 or self.c1),
                comp(lig_sel(self.e), lig.pop("rep", "ball_and_stick"), c2 or self.c2, **lig)]

    def api(self, c1=None, c2=None) -> list[dict]:
        return [load(self.e.id), paint(api_polymer(self.e, c1 or self.c1)
                                       + [{**lig_sel(self.e), "color": c2 or self.c2}])]

    def kept(self, track: str, polymer: bool = True, ligand: bool = True) -> list[dict]:
        out = []
        if polymer:
            out.append(part("polymer", "cartoon", self.c1) if track == "mvs"
                       else api_polymer_part(self.e, self.c1))
        if ligand:
            out.append(part(lig_sel(self.e), "ball_and_stick" if track == "mvs" else None, self.c2))
        return out


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
# A template takes (entry, rng) and returns a spec:
#   prompt     the request (one of several wordings, chosen by the seed)
#   mvs / api  per track: start, ref (states), target, preserved (lists of parts or
#              None), and controls: {"equivalent": [states that must succeed],
#              "wrong": [states that must not]}
#   noop       True when the start state already is the right answer
#   edit       the edit kind; referent: why a pronoun / description is unambiguous;
#   removed    the selector of what the edit takes away (it cannot be a target on the
#              MVS track, where the reference draws nothing there)
#   residue    the residue a request names, when it names one
# A template returns None when the structure cannot carry it.
def pick(r: random.Random, options: list[str], **words: Any) -> str:
    """One of a template's wordings. Within a family the wordings are taken in turn
    from a seeded starting point (``r.turn``, set in `build`), so two tasks of a family
    are not worded alike while there are wordings left."""
    return options[r.turn % len(options)].format(**words)


def art(word: str) -> str:
    return ("an " if word[0] in "aeiou" else "a ") + word


def colours(r: random.Random, n: int, without: tuple = ()) -> list[str]:
    return r.sample([c for c in COLOURS if c not in without], n)


def needs_pair(e: Entry) -> bool:
    return e.ligand is not None and e.noun is not None and len(e.chains) <= 4


def recolour_ligand(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2, new = colours(r, 3)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Colour {lig} {new}.", "Make {lig} {new} instead.",
                           "Change the colour of {lig} to {new}.",
                           "Could you turn {lig} {new}?"], lig=e.ligand_words(), new=say(new)),
        "edit": "recolour one existing component", "skills": ["edit", "color"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs(c2=new)),
                "target": [part(lig_sel(e), None, new)], "preserved": p.kept("mvs", ligand=False),
                "wrong": [mvs_scene(e.id, [comp(lig_sel(e), "ball_and_stick", new)])]},
        "api": {"start": p.api(), "ref": p.api(c2=new),
                "target": [part(lig_sel(e), None, new)], "preserved": p.kept("api", ligand=False),
                "equivalent": [p.api() + [paint([{**lig_sel(e), "color": new}], keep=True)]],
                "wrong": [[load(e.id), paint([{**lig_sel(e), "color": new}])]]},
    }


def undo_grey(e: Entry, r: random.Random):
    """Undo-like: the protein is grey and the ligand stands out; the request puts the
    ligand back to grey. The model sees no history, so the colour is named."""
    if not needs_pair(e) or e.bonded:
        return None
    (c2,) = colours(r, 1, without=("gray",))
    p = Pair(e, "gray", c2)
    return {
        "prompt": pick(r, ["Make {lig} grey again.", "Put {lig} back to grey.",
                           "Undo the {c2} on {lig}: grey again, please."],
                       lig=e.ligand_words(), c2=say(c2)),
        "edit": "undo-like recolour", "skills": ["edit", "color"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs(c2="gray")),
                "target": [part(lig_sel(e), None, "gray")], "preserved": p.kept("mvs", ligand=False),
                "wrong": [mvs_scene(e.id, [comp(lig_sel(e), "ball_and_stick", "gray")])]},
        "api": {"start": p.api(), "ref": p.api(c2="gray"),
                "target": [part(lig_sel(e), None, "gray")], "preserved": p.kept("api", ligand=False),
                "wrong": [[load(e.id), paint([{**lig_sel(e), "color": "gray"}])]]},
    }


def same_as(e: Entry, r: random.Random):
    if not needs_pair(e) or e.bonded:
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Give {lig} the same colour as the {noun}.",
                           "Colour {lig} to match the {noun}.",
                           "Make {lig} the same colour as the {noun}."],
                       lig=e.ligand_words(), noun=e.noun),
        "edit": "recolour by reference to the scene", "skills": ["edit", "color", "referent"],
        "referent": f"\"the same colour as the {e.noun}\": the start state gives the whole "
                    f"{e.noun} exactly one colour ({c1})",
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs(c2=c1)),
                "target": [part(lig_sel(e), None, c1)], "preserved": p.kept("mvs", ligand=False)},
        "api": {"start": p.api(), "ref": p.api(c2=c1),
                "target": [part(lig_sel(e), None, c1)], "preserved": p.kept("api", ligand=False)},
    }


def focus_ligand(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Zoom in on {lig}.", "Centre the view on {lig}.",
                           "Now focus the camera on {lig}."], lig=e.ligand_words()),
        "edit": "also: camera focus", "skills": ["edit", "focus"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs(focus=True)),
                "target": [part(lig_sel(e))], "preserved": p.kept("mvs", ligand=False),
                "wrong": [mvs_scene(e.id, [comp(lig_sel(e), "ball_and_stick", focus=True)])]},
        "api": {"start": p.api(), "ref": p.api() + [{"action": "focus", "data": [lig_sel(e)]}],
                "target": [part(lig_sel(e))], "preserved": p.kept("api", ligand=False),
                "wrong": [[load(e.id), {"action": "focus", "data": [lig_sel(e)]}]]},
    }


def add_residue(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    res = e.residue(r)
    if res is None:
        return None
    c1, c2, new = colours(r, 3)
    p = Pair(e, c1, c2)
    sel = {"auth_asym_id": res["auth_asym_id"], "auth_seq_id": res["auth_seq_id"]}
    name = f"{res['comp'].capitalize()}{res['auth_seq_id']}"
    added = {**sel, "color": None, "representation": "ball-and-stick", "representationColor": new}
    # The API reference's own worked example writes a residue "in red ball-and-stick" with
    # "color": "red" as well, which also paints the residue's stretch of cartoon: another
    # final state. So every wording says that the cartoon keeps its colour, and that
    # answer is a "wrong" control.
    painted = {**added, "color": new}
    return {
        "prompt": pick(r, ["Also show {res} of chain {ch} as {new} ball-and-stick; leave the "
                           "cartoon as it is.",
                           "Add {res} (chain {ch}) in {new} ball-and-stick, without recolouring "
                           "the cartoon.",
                           "Now draw {res} of chain {ch} as ball-and-stick too, in {new}; the "
                           "cartoon keeps its colour.",
                           "Show the side chain and backbone of {res} in chain {ch} as {new} "
                           "ball-and-stick, on top of the cartoon, which stays as it is."],
                       res=name, ch=res["auth_asym_id"], new=say(new)),
        "edit": "add a component (a residue), keeping the rest",
        "skills": ["edit", "selection", "representation", "color"], "residue": res,
        "mvs": {"start": mvs_scene(e.id, p.mvs()),
                "ref": mvs_scene(e.id, p.mvs() + [comp(sel, "ball_and_stick", new)]),
                "target": [part(sel, "ball_and_stick", new)],
                "preserved": [polymer_without(e, res, "cartoon", c1)] + p.kept("mvs", polymer=False),
                "wrong": [mvs_scene(e.id, [comp(sel, "ball_and_stick", new)])]},
        # "color": null leaves the cartoon under the residue as it is; without it the
        # viewer paints the residue's cartoon orange (the first "wrong" control).
        "api": {"start": p.api(), "ref": p.api() + [paint([added], keep=True)],
                "target": [part(sel, "ball-and-stick", new)],
                "preserved": [polymer_without(e, res, None, c1)] + p.kept("api", polymer=False),
                "equivalent": [[load(e.id), paint(p.api()[1]["data"] + [added])]],
                "wrong": [p.api() + [paint([{k: v for k, v in added.items() if k != "color"}],
                                           keep=True)],
                          p.api() + [paint([added])],
                          # the residue's cartoon painted too (the API example's way)
                          p.api() + [paint([painted], keep=True)],
                          # ... and the sticks in element colours, not the colour asked for
                          p.api() + [paint([{k: v for k, v in painted.items()
                                             if k != "representationColor"}], keep=True)]]},
    }


def hide_water(e: Entry, r: random.Random):
    if not (e.has_water and e.noun):
        return None
    c1, c3 = colours(r, 2)
    polymer = comp("polymer", "cartoon", c1)
    start_api = [load(e.id), paint(api_polymer(e, c1))]
    return {
        "prompt": pick(r, ["Hide the waters.", "Remove the water molecules from the view.",
                           "Get rid of the waters, please."]),
        "edit": "remove / hide something", "skills": ["edit", "visibility"], "removed": "water",
        "mvs": {"start": mvs_scene(e.id, [polymer, comp("water", "ball_and_stick", c3)]),
                "ref": mvs_scene(e.id, [polymer]), "target": None,
                "preserved": [part("polymer", "cartoon", c1)]},
        "api": {"start": start_api, "ref": start_api + [prop("hide_water", True)],
                "target": None, "preserved": [api_polymer_part(e, c1)],
                "equivalent": [[load(e.id), prop("hide_water", True), paint(api_polymer(e, c1))]],
                "wrong": [[load(e.id), prop("hide_water", True)]]},
    }


def background(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Make the background black.", "Switch to a black background.",
                           "Black background, please."]),
        "edit": "also: a scene setting", "skills": ["edit", "canvas"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs(), "black"),
                "target": None, "preserved": p.kept("mvs")},
        "api": {"start": p.api(), "ref": p.api() + [prop("bg_color", "black")],
                "target": None, "preserved": p.kept("api"),
                "wrong": [[load(e.id), prop("bg_color", "black")]]},
    }


# --- two chains -------------------------------------------------------------------
def two_chains(e: Entry, exactly_two: bool = False):
    pair = e.chain_pair()
    if pair is None or (exactly_two and len(e.chains) != 2):
        return None
    return pair


def chains_mvs(e: Entry, a: dict, b: dict, ca: str | None, cb: str | None) -> dict:
    return mvs_scene(e.id, [comp(chain_sel(a), "cartoon", ca), comp(chain_sel(b), "cartoon", cb)])


CARTOON = {"action": "set_visual_style", "style": "cartoon"}


def chains_api(e: Entry, a: dict, b: dict, ca: str, cb: str | None, style: bool = True) -> list[dict]:
    """Two chains coloured on the API track, under the cartoon style. The style matters:
    an author chain id also covers that chain's ligands, ions and waters, which the
    default view draws, so there "chain B" as the author chain and "chain B" as the
    polymer chain alone would be two different pictures. Under the cartoon style only
    polymer is drawn and the two readings are one final state (the `by_label` control)."""
    data = [{**chain_sel(a), "color": ca}] + ([{**chain_sel(b), "color": cb}] if cb else [])
    return [load(e.id)] + ([CARTOON] if style else []) + [paint(data)]


def by_label(e: Entry, calls: list[dict]) -> list[dict]:
    """The same calls with every whole-chain selection written as the polymer chain's
    label chain id (``struct_asym_id``) instead of the author chain id."""
    out = json.loads(json.dumps(calls))
    for call in out:
        params = []
        for param in call.get("data") or []:
            if "auth_asym_id" in param and "auth_seq_id" not in param:
                author = param.pop("auth_asym_id")
                params += [{"struct_asym_id": c["label_asym_id"], **param}
                           for c in e.chains if c["auth_asym_id"] == author]
            else:
                params.append(param)
        if "data" in call:
            call["data"] = params
    return out


def recolour_chain(e: Entry, r: random.Random):
    pair = two_chains(e)
    if pair is None:
        return None
    a, b = pair
    ca, cb, new = colours(r, 3)
    return {
        "prompt": pick(r, ["Colour chain {b} {new}.", "Make chain {b} {new} instead.",
                           "Change chain {b} to {new}."], b=b["auth_asym_id"], new=say(new)),
        "edit": "recolour one existing component", "skills": ["edit", "color", "selection"],
        "mvs": {"start": chains_mvs(e, a, b, ca, cb), "ref": chains_mvs(e, a, b, ca, new),
                "target": [part(chain_sel(b), None, new)],
                "preserved": [part(chain_sel(a), "cartoon", ca)],
                "wrong": [mvs_scene(e.id, [comp(chain_sel(b), "cartoon", new)])]},
        "api": {"start": chains_api(e, a, b, ca, cb), "ref": chains_api(e, a, b, ca, new),
                "target": [part(chain_sel(b), None, new)],
                "preserved": [part(chain_sel(a), None, ca)],
                "equivalent": [chains_api(e, a, b, ca, cb)
                               + [paint([{**chain_sel(b), "color": new}], keep=True)],
                               by_label(e, chains_api(e, a, b, ca, new))],
                "wrong": [[load(e.id), CARTOON, paint([{**chain_sel(b), "color": new}])]]},
    }


def also_colour(e: Entry, r: random.Random):
    pair = two_chains(e)
    if pair is None:
        return None
    a, b = pair
    ca, new = colours(r, 2)
    return {
        "prompt": pick(r, ["Also colour chain {b} {new}.", "Now colour chain {b} as well, in {new}.",
                           "And chain {b} in {new}, please."], b=b["auth_asym_id"], new=say(new)),
        "edit": "also: colour a second component", "skills": ["edit", "color", "selection"],
        "mvs": {"start": chains_mvs(e, a, b, ca, None), "ref": chains_mvs(e, a, b, ca, new),
                "target": [part(chain_sel(b), None, new)],
                "preserved": [part(chain_sel(a), "cartoon", ca)],
                "wrong": [mvs_scene(e.id, [comp(chain_sel(b), "cartoon", new)])]},
        "api": {"start": chains_api(e, a, b, ca, None),
                "ref": chains_api(e, a, b, ca, None)
                + [paint([{**chain_sel(b), "color": new}], keep=True)],
                "target": [part(chain_sel(b), None, new)],
                "preserved": [part(chain_sel(a), None, ca)],
                "equivalent": [chains_api(e, a, b, ca, new),
                               by_label(e, chains_api(e, a, b, ca, new))],
                # the commonest slip: a second color call without keep_colors
                "wrong": [chains_api(e, a, b, ca, None) + [paint([{**chain_sel(b), "color": new}])]]},
    }


def other_chain(e: Entry, r: random.Random):
    """Ellipsis: one of exactly two chains is coloured; "the other chain" is the one
    that is not. The same edit as `also_colour`, with the chain left unnamed."""
    spec = also_colour(e, r) if len(e.chains) == 2 else None
    if spec is None:
        return None
    a, b = e.chain_pair()
    new = spec["mvs"]["target"][0]["color"]
    spec.update(
        prompt=pick(r, ["Now the other chain in {new}.", "Colour the other chain {new}.",
                        "And the other chain {new}, please."], new=say(new)),
        edit="ellipsis: colour the component not yet coloured",
        skills=["edit", "color", "referent"],
        referent=f"\"the other chain\": the structure has exactly two polymer chains and the "
                 f"start state colours only one (author chain {a['auth_asym_id']}), so the other "
                 f"is author chain {b['auth_asym_id']}")
    return spec


def referent_colour(e: Entry, r: random.Random):
    # exactly two chains: on the API track every other chain would be drawn in a viewer
    # default colour, and one of those could look like the colour the request names
    pair = two_chains(e, exactly_two=True)
    if pair is None:
        return None
    a, b = pair
    ca, cb, new = colours(r, 3)
    first = r.random() < 0.5            # which of the two chains the request points at
    old = ca if first else cb
    hit, other = (a, b) if first else (b, a)
    na, nb = (new, cb) if first else (ca, new)
    return {
        "prompt": pick(r, ["Make the {old} chain {new}.", "Change the {old} chain to {new}.",
                           "The {old} one should be {new} instead."], old=say(old), new=say(new)),
        "edit": "recolour a component named by its current colour",
        "skills": ["edit", "color", "referent"],
        "referent": f"\"the {say(old)} chain\": exactly one chain of the start state is {old} "
                    f"(author chain {hit['auth_asym_id']})",
        "mvs": {"start": chains_mvs(e, a, b, ca, cb), "ref": chains_mvs(e, a, b, na, nb),
                "target": [part(chain_sel(hit), None, new)],
                "preserved": [part(chain_sel(other), "cartoon", cb if first else ca)]},
        "api": {"start": chains_api(e, a, b, ca, cb), "ref": chains_api(e, a, b, na, nb),
                "target": [part(chain_sel(hit), None, new)],
                "preserved": [part(chain_sel(other), None, cb if first else ca)],
                "equivalent": [by_label(e, chains_api(e, a, b, na, nb))],
                "wrong": [[load(e.id), CARTOON, paint([{**chain_sel(hit), "color": new}])]]},
    }


def swap_colours(e: Entry, r: random.Random):
    pair = two_chains(e, exactly_two=True)
    if pair is None:
        return None
    a, b = pair
    ca, cb = colours(r, 2)
    target = [part(chain_sel(a), None, cb), part(chain_sel(b), None, ca)]
    return {
        "prompt": pick(r, ["Swap the colours of the two chains.",
                           "Exchange the two chain colours.",
                           "Switch the colours of the two chains around."]),
        "edit": "recolour by reference to the scene", "skills": ["edit", "color", "referent"],
        "referent": f"\"the two chains\": the structure has exactly two polymer chains, and the "
                    f"start state colours each ({ca}, {cb})",
        "mvs": {"start": chains_mvs(e, a, b, ca, cb), "ref": chains_mvs(e, a, b, cb, ca),
                "target": target, "preserved": None},
        "api": {"start": chains_api(e, a, b, ca, cb), "ref": chains_api(e, a, b, cb, ca),
                "target": target, "preserved": None,
                "equivalent": [by_label(e, chains_api(e, a, b, cb, ca))]},
    }


# --- requests that need no change --------------------------------------------------
def noop_colour(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Colour {lig} {c2}.", "Make {lig} {c2}.",
                           "Show {lig} in {c2}."], lig=e.ligand_words(), c2=say(c2)),
        "edit": "no change: already true", "noop": True, "noop_kind": "already true",
        "skills": ["edit", "color", "noop"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs()),
                "target": [part(lig_sel(e), None, c2)], "preserved": p.kept("mvs")},
        "api": {"start": p.api(), "ref": p.api(),
                "target": [part(lig_sel(e), None, c2)], "preserved": p.kept("api")},
    }


def noop_shown(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Show the {noun} as a cartoon.", "Draw the {noun} as a cartoon.",
                           "Cartoon for the {noun}, please."], noun=e.noun),
        "edit": "no change: already true", "noop": True, "noop_kind": "already true",
        "skills": ["edit", "representation", "noop"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs()),
                "target": None, "preserved": p.kept("mvs")},
        "api": {"start": p.api(), "ref": p.api(), "target": None, "preserved": p.kept("api")},
    }


def noop_hidden(e: Entry, r: random.Random):
    if not (needs_pair(e) and e.has_water):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    api = [load(e.id), prop("hide_water", True), p.api()[1]]
    return {
        "prompt": pick(r, ["Hide the waters.", "Hide the water molecules.",
                           "Make sure no waters are shown."]),
        "edit": "no change: already true", "noop": True, "noop_kind": "already true",
        "skills": ["edit", "visibility", "noop"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs()),
                "target": None, "preserved": p.kept("mvs")},
        "api": {"start": api, "ref": api, "target": None, "preserved": p.kept("api")},
    }


def noop_ligand_rep(e: Entry, r: random.Random):
    """A clear request for something the start state already has: the ligand is drawn
    as ball-and-stick. (Question prompts, "How many chains does this structure have?",
    are not used as no-change tasks: a question is not a request to the viewer, and
    what the right reply to one is cannot be graded as a scene. Ruling of 2026-11-15.)"""
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Show {lig} as ball-and-stick.", "Draw {lig} as ball-and-stick.",
                           "Ball-and-stick for {lig}, please."], lig=e.ligand_words()),
        "edit": "no change: already true", "noop": True, "noop_kind": "already true",
        "skills": ["edit", "representation", "noop"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs()),
                "target": [part(lig_sel(e), "ball_and_stick", None)], "preserved": p.kept("mvs")},
        "api": {"start": p.api(), "ref": p.api(),
                "target": [part(lig_sel(e), "ball-and-stick", None)], "preserved": p.kept("api")},
    }


def noop_spin(e: Entry, r: random.Random):
    """The MVS reference given to the model has no motion (multi-snapshot animation is
    left out of it). The request itself says what to do then: leave the scene as it is."""
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Can you make it spin? If the scene cannot do that, leave it "
                           "exactly as it is.",
                           "Make the structure spin slowly, or leave the scene as it is if "
                           "spinning is not possible here.",
                           "Start the molecule spinning; if that cannot be done in the scene, "
                           "change nothing."]),
        "edit": "no change: the format cannot express the request", "noop": True,
        "noop_kind": "not expressible in the format", "skills": ["edit", "noop"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs()),
                "target": None, "preserved": p.kept("mvs")},
    }


# --- MVS only ----------------------------------------------------------------------
def it_colour(e: Entry, r: random.Random):
    if e.ligand is None or len(e.ligand["copies"]) != 1:
        return None
    c2, new = colours(r, 2)
    return {
        "prompt": pick(r, ["Colour it {new}.", "Make it {new}.", "Turn it {new}, please."],
                       new=say(new)),
        "edit": "pronoun: recolour", "skills": ["edit", "color", "referent"],
        "referent": "\"it\": the start scene draws one component only (the ligand "
                    f"{e.ligand['comp_id']}, one copy)",
        "mvs": {"start": mvs_scene(e.id, [comp(lig_sel(e), "ball_and_stick", c2)]),
                "ref": mvs_scene(e.id, [comp(lig_sel(e), "ball_and_stick", new)]),
                "target": [part(lig_sel(e), None, new)], "preserved": None},
    }


def it_surface(e: Entry, r: random.Random):
    if e.noun is None:
        return None
    (c1,) = colours(r, 1)
    return {
        "prompt": pick(r, ["Show it as a surface instead.", "Make it a surface instead of a cartoon.",
                           "Switch it to a surface."]),
        "edit": "pronoun: change a representation",
        "skills": ["edit", "representation", "referent"],
        "referent": "\"it\": the start scene draws one component only (the whole polymer)",
        "mvs": {"start": mvs_scene(e.id, [comp("polymer", "cartoon", c1)]),
                "ref": mvs_scene(e.id, [comp("polymer", "surface", c1)]),
                "target": [part("polymer", "surface", None)], "preserved": None,
                # the colour is an earlier choice: a surface that lost it is not right
                "wrong": [mvs_scene(e.id, [comp("polymer", "surface")])]},
    }


def rep_ligand(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Show {lig} as spacefill instead of ball-and-stick.",
                           "Switch {lig} to spacefill.", "Draw {lig} as spacefill instead."],
                       lig=e.ligand_words()),
        "edit": "change a representation", "skills": ["edit", "representation"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs(rep="spacefill")),
                "target": [part(lig_sel(e), "spacefill", None)],
                "preserved": p.kept("mvs", ligand=False),
                "wrong": [mvs_scene(e.id, p.mvs() + [comp(lig_sel(e), "spacefill", c2)]),
                          mvs_scene(e.id, [comp(lig_sel(e), "spacefill", c2)])]},
    }


def rep_polymer(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    ref = [comp("polymer", "surface", c1), p.mvs()[1]]
    return {
        "prompt": pick(r, ["Show the {noun} as a surface instead of a cartoon.",
                           "Switch the {noun} from cartoon to surface.",
                           "Replace the {noun} cartoon with a surface."], noun=e.noun),
        "edit": "change a representation", "skills": ["edit", "representation"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, ref),
                "target": [part("polymer", "surface", None)],
                "preserved": p.kept("mvs", polymer=False),
                "wrong": [mvs_scene(e.id, [comp("polymer", "surface", c1)])]},
    }


def add_ligand(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, new = colours(r, 2)
    polymer = comp("polymer", "cartoon", c1)
    ligand = comp(lig_sel(e), "ball_and_stick", new)
    return {
        "prompt": pick(r, ["Add {lig} as {new} ball-and-stick.",
                           "Also show {lig}, as ball-and-stick in {new}.",
                           "Now bring in {lig} in {new} ball-and-stick."],
                       lig=e.ligand_words(), new=say(new)),
        "edit": "add a component (the ligand), keeping the rest",
        "skills": ["edit", "selection", "representation", "color"],
        "mvs": {"start": mvs_scene(e.id, [polymer]), "ref": mvs_scene(e.id, [polymer, ligand]),
                "target": [part(lig_sel(e), "ball_and_stick", new)],
                "preserved": [part("polymer", "cartoon", c1)],
                "wrong": [mvs_scene(e.id, [ligand])]},
    }


def add_chain(e: Entry, r: random.Random):
    pair = two_chains(e)
    if pair is None:
        return None
    a, b = pair
    ca, new = colours(r, 2)
    return {
        "prompt": pick(r, ["Also show chain {b} as {a_new} cartoon.",
                           "Add chain {b} too, as a cartoon in {new}.",
                           "Now bring in chain {b} as {a_new} cartoon."],
                       b=b["auth_asym_id"], new=say(new), a_new=art(say(new))),
        "edit": "add a component (a chain), keeping the rest",
        "skills": ["edit", "selection", "representation", "color"],
        "mvs": {"start": mvs_scene(e.id, [comp(chain_sel(a), "cartoon", ca)]),
                "ref": chains_mvs(e, a, b, ca, new),
                "target": [part(chain_sel(b), "cartoon", new)],
                "preserved": [part(chain_sel(a), "cartoon", ca)],
                "wrong": [mvs_scene(e.id, [comp(chain_sel(b), "cartoon", new)])]},
    }


def remove_ligand(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Hide {lig}.", "Remove {lig} from the view.",
                           "Take {lig} out of the picture."], lig=e.ligand_words()),
        "edit": "remove / hide something", "skills": ["edit", "visibility"],
        "removed": lig_sel(e),
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs()[:1]),
                "target": None, "preserved": p.kept("mvs", ligand=False)},
    }


def only_chain(e: Entry, r: random.Random):
    pair = two_chains(e)
    if pair is None:
        return None
    a, b = pair
    ca, cb = colours(r, 2)
    return {
        "prompt": pick(r, ["Show only chain {a} now.", "Keep just chain {a}.",
                           "Only chain {a}, please."], a=a["auth_asym_id"]),
        "edit": "narrow to one component", "skills": ["edit", "visibility", "selection"],
        "removed": chain_sel(b),
        "mvs": {"start": chains_mvs(e, a, b, ca, cb),
                "ref": mvs_scene(e.id, [comp(chain_sel(a), "cartoon", ca)]),
                "target": None, "preserved": [part(chain_sel(a), "cartoon", ca)],
                # narrowed, but the chain's colour was lost
                "wrong": [mvs_scene(e.id, [comp(chain_sel(a), "cartoon")])]},
    }


def add_label(e: Entry, r: random.Random):
    if not needs_pair(e) or len(e.ligand["copies"]) != 1:
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    text = r.choice([e.ligand["comp_id"], "ligand", "site 1"])
    return {
        "prompt": pick(r, ["Label {lig} with the text \"{text}\".",
                           "Add a label reading \"{text}\" to {lig}.",
                           "Put a \"{text}\" label on {lig}."], lig=e.ligand_words(), text=text),
        "edit": "also: a label", "skills": ["edit", "label"],
        "mvs": {"start": mvs_scene(e.id, p.mvs()), "ref": mvs_scene(e.id, p.mvs(label=text)),
                "target": [part(lig_sel(e))], "preserved": p.kept("mvs", ligand=False),
                "wrong": [mvs_scene(e.id, [comp(lig_sel(e), "ball_and_stick", label=text)])]},
    }


def remove_label(e: Entry, r: random.Random):
    if not needs_pair(e) or len(e.ligand["copies"]) != 1:
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Remove the label.", "Hide the label.", "Take the label off."]),
        "edit": "remove / hide something", "skills": ["edit", "label", "referent"],
        "referent": "\"the label\": the start scene has exactly one label (on the ligand)",
        "mvs": {"start": mvs_scene(e.id, p.mvs(label=e.ligand["comp_id"])),
                "ref": mvs_scene(e.id, p.mvs()), "target": None, "preserved": p.kept("mvs")},
    }


def opacity(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    value, words = r.choice([(0.5, "50% transparent"), (0.5, "half transparent"),
                             (0.3, "70% transparent")])
    start = [comp("polymer", "surface", c1), p.mvs()[1]]
    ref = [comp("polymer", "surface", c1, opacity=value), p.mvs()[1]]
    return {
        "prompt": pick(r, ["Make the {noun} surface {words}.",
                           "The {noun} surface should be {words}.",
                           "Can you make the surface of the {noun} {words}?"],
                       noun=e.noun, words=words),
        "edit": "change one property of an existing component (opacity)",
        "skills": ["edit", "opacity"],
        "mvs": {"start": mvs_scene(e.id, start), "ref": mvs_scene(e.id, ref),
                "target": [part("polymer", "surface", None)],
                "preserved": p.kept("mvs", polymer=False)},
    }


# --- API only ----------------------------------------------------------------------
def api_style(e: Entry, r: random.Random):
    """A global style reloads the structure and drops earlier colouring, so the colour
    call has to come after it: the final list is not the old one plus one call."""
    pair = two_chains(e)
    if pair is None:
        return None
    a, b = pair
    ca, cb = colours(r, 2)
    # Only the two polymer-only styles: under any other, the ligands and waters filed
    # under an author chain id are drawn, and "the chain" has two readings (`chains_api`).
    style, words = [("putty", "the putty style"),
                    ("cartoon", "the cartoon-only style (no ligands or waters)")][r.turn % 2]
    start = chains_api(e, a, b, ca, cb, style=False)
    restyle = {"action": "set_visual_style", "style": style}
    return {
        "prompt": pick(r, ["Switch the whole structure to {words} and keep the two chain colours.",
                           "Draw everything in {words} instead; chains {a} and {b} keep their colours.",
                           "Change the display to {words}, with the same colours on the two "
                           "chains."], words=words, a=a["auth_asym_id"], b=b["auth_asym_id"]),
        "edit": "change the representation (order-sensitive on this track)",
        "skills": ["edit", "representation", "color"],
        "api": {"start": start, "ref": [start[0], restyle, start[1]], "target": None,
                "preserved": None,
                "equivalent": [by_label(e, [start[0], restyle, start[1]])],
                "wrong": [start + [restyle], [load(e.id), restyle]]},
    }


def api_uncolour(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Remove the colouring from {lig}, but keep the {noun} {c1}.",
                           "Put {lig} back to its default colours; the {noun} stays {c1}.",
                           "Undo the {c2} on {lig} and leave the {noun} as it is."],
                       lig=e.ligand_words(), noun=e.noun, c1=say(c1), c2=say(c2)),
        "edit": "undo one earlier choice", "skills": ["edit", "color"],
        "api": {"start": p.api(), "ref": [load(e.id), paint(api_polymer(e, c1))],
                "target": None, "preserved": p.kept("api", ligand=False),
                "wrong": [[load(e.id)], p.api() + [{"action": "clear_selection"}]]},
    }


def api_show_water(e: Entry, r: random.Random):
    if not (e.has_water and e.noun):
        return None
    (c1,) = colours(r, 1)
    colour = paint(api_polymer(e, c1))
    return {
        "prompt": pick(r, ["Show the waters again.", "Bring the water molecules back.",
                           "Unhide the waters."]),
        "edit": "undo one earlier choice (a hidden component)", "skills": ["edit", "visibility"],
        "api": {"start": [load(e.id), prop("hide_water", True), colour],
                "ref": [load(e.id), colour], "target": None,
                "preserved": [api_polymer_part(e, c1)],
                "equivalent": [[load(e.id), prop("hide_water", True), colour,
                                prop("hide_water", False)]],
                "wrong": [[load(e.id)]]},
    }


def api_clear(e: Entry, r: random.Random):
    if not (needs_pair(e) and e.has_water):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Clear all the colouring, but keep the waters hidden.",
                           "Go back to the default colours; the waters stay hidden."]),
        "edit": "undo earlier choices (all colouring)", "skills": ["edit", "color"],
        "api": {"start": [load(e.id), prop("hide_water", True), p.api()[1]],
                "ref": [load(e.id), prop("hide_water", True)], "target": None,
                "preserved": [part("water")],
                "equivalent": [[load(e.id), prop("hide_water", True), p.api()[1],
                                {"action": "clear_selection"}]],
                "wrong": [[load(e.id)]]},
    }


def api_stop_spin(e: Entry, r: random.Random):
    if not needs_pair(e):
        return None
    c1, c2 = colours(r, 2)
    p = Pair(e, c1, c2)
    return {
        "prompt": pick(r, ["Stop the spinning.", "Stop it spinning.", "Turn the spin off."]),
        "edit": "undo one earlier choice (a setting)", "skills": ["edit", "canvas"],
        "api": {"start": [load(e.id), prop("spin", True), p.api()[1]], "ref": p.api(),
                "target": None, "preserved": p.kept("api"),
                "equivalent": [[load(e.id), prop("spin", True), p.api()[1], prop("spin", False)]],
                "wrong": [[load(e.id)]]},
    }


# family id -> (template, how many, tracks)
FAMILIES: list[tuple[str, Callable, int, tuple[str, ...]]] = [
    ("fu-recolour-ligand", recolour_ligand, 3, ("mvs", "api")),
    ("fu-recolour-chain", recolour_chain, 2, ("mvs", "api")),
    ("fu-also-colour-chain", also_colour, 2, ("mvs", "api")),
    ("fu-other-chain", other_chain, 2, ("mvs", "api")),
    ("fu-referent-colour", referent_colour, 3, ("mvs", "api")),
    ("fu-same-colour-as", same_as, 2, ("mvs", "api")),
    ("fu-swap-colours", swap_colours, 2, ("mvs", "api")),
    ("fu-add-residue", add_residue, 4, ("mvs", "api")),
    ("fu-hide-water", hide_water, 2, ("mvs", "api")),
    ("fu-undo-grey", undo_grey, 2, ("mvs", "api")),
    ("fu-focus-ligand", focus_ligand, 2, ("mvs", "api")),
    ("fu-background", background, 2, ("mvs", "api")),
    ("fu-noop-colour", noop_colour, 2, ("mvs", "api")),
    ("fu-noop-shown", noop_shown, 2, ("mvs", "api")),
    ("fu-noop-hidden", noop_hidden, 2, ("mvs", "api")),
    ("fu-noop-ligand-rep", noop_ligand_rep, 2, ("mvs", "api")),
    ("fu-noop-spin", noop_spin, 2, ("mvs",)),
    ("fu-it-colour", it_colour, 2, ("mvs",)),
    ("fu-it-surface", it_surface, 1, ("mvs",)),
    ("fu-rep-ligand", rep_ligand, 2, ("mvs",)),
    ("fu-rep-polymer", rep_polymer, 2, ("mvs",)),
    ("fu-add-ligand", add_ligand, 2, ("mvs",)),
    ("fu-add-chain", add_chain, 2, ("mvs",)),
    ("fu-remove-ligand", remove_ligand, 2, ("mvs",)),
    ("fu-only-chain", only_chain, 2, ("mvs",)),
    ("fu-add-label", add_label, 2, ("mvs",)),
    ("fu-remove-label", remove_label, 1, ("mvs",)),
    ("fu-opacity", opacity, 2, ("mvs",)),
    ("fu-api-style", api_style, 2, ("api",)),
    ("fu-api-uncolour", api_uncolour, 2, ("api",)),
    ("fu-api-show-water", api_show_water, 2, ("api",)),
    ("fu-api-clear-colours", api_clear, 1, ("api",)),
    ("fu-api-stop-spin", api_stop_spin, 1, ("api",)),
]

# One line per family for the README: how the reference is derived.
DERIVED = {
    "fu-recolour-ligand": "start: polymer + main ligand, each one colour; the ligand's colour replaced",
    "fu-recolour-chain": "start: two chains, each one colour; the second chain's colour replaced",
    "fu-also-colour-chain": "start: first chain coloured, second not; a colour added to the second",
    "fu-other-chain": "start: first of exactly two chains coloured, second not; a colour added to the second, which the request calls \"the other chain\"",
    "fu-referent-colour": "start: two chains in two colours (entries with exactly two polymer chains); the chain that has the named colour is recoloured",
    "fu-same-colour-as": "start: polymer + ligand; the ligand takes the polymer's colour, read from the start state",
    "fu-swap-colours": "start: two chains in two colours (entries with exactly two polymer chains); colours exchanged",
    "fu-add-residue": "start: polymer + ligand; one residue (author chain + number, checked to select exactly that residue) added as coloured ball-and-stick; the request says the cartoon keeps its colour (on the API track painting the residue's cartoon too is another final state, and is not right)",
    "fu-hide-water": "start: polymer (+ waters drawn, MVS); MVS drops the water component, API sets hide_water",
    "fu-undo-grey": "start: grey polymer, coloured ligand; the ligand set to grey",
    "fu-focus-ligand": "start: polymer + ligand; a camera focus on the ligand added",
    "fu-background": "start: polymer + ligand; a black background added (MVS canvas node, API bg_color)",
    "fu-noop-colour": "the ligand already has the requested colour: reference = start state",
    "fu-noop-shown": "the polymer already is a cartoon: reference = start state",
    "fu-noop-hidden": "no water is drawn (MVS) / hide_water is already set (API): reference = start state",
    "fu-noop-ligand-rep": "the ligand asked for as ball-and-stick, which it already is: reference = start state",
    "fu-noop-spin": "the MVS reference has no motion, and the request says to change nothing in that case: reference = start state",
    "fu-it-colour": "start: the ligand alone (one copy); \"it\" recoloured",
    "fu-it-surface": "start: the polymer alone; \"it\" changed from cartoon to surface, colour kept",
    "fu-rep-ligand": "start: polymer + ligand; the ligand's representation set to spacefill, colour kept",
    "fu-rep-polymer": "start: polymer + ligand; the polymer's representation set to surface, colour kept",
    "fu-add-ligand": "start: polymer alone; the main ligand added as coloured ball-and-stick",
    "fu-add-chain": "start: first chain alone; the second chain added as a coloured cartoon",
    "fu-remove-ligand": "start: polymer + ligand; the ligand component dropped",
    "fu-only-chain": "start: two chains; the second chain's component dropped",
    "fu-add-label": "start: polymer + ligand; a label with the quoted text added to the ligand",
    "fu-remove-label": "start: polymer + labelled ligand; the label dropped",
    "fu-opacity": "start: polymer surface + ligand; an opacity added to the surface",
    "fu-api-style": "start: two coloured chains, default view; set_visual_style (putty or cartoon, the polymer-only styles) inserted before the colour call (a style reloads and drops colouring)",
    "fu-api-uncolour": "start: polymer + ligand coloured; the ligand's selection removed from the colour call",
    "fu-api-show-water": "start: waters hidden, polymer coloured; the hide_water call removed",
    "fu-api-clear-colours": "start: waters hidden, polymer + ligand coloured; the colour call removed",
    "fu-api-stop-spin": "start: spinning, polymer + ligand coloured; the spin call removed",
}


# --------------------------------------------------------------------------- #
# Building the corpus
# --------------------------------------------------------------------------- #
def difficulty(e: Entry, spec: dict) -> dict:
    """The facts that make a task harder, for the paper's breakdowns. They describe
    the request: a follow-up names residues and chains as the paper does (author
    numbering) and gives the ligand's code, so nothing has to be looked up."""
    res = spec.get("residue")
    # The answer has to pick a chain when a final state selects one by its author chain
    # id (the chain and residue families). Read from the states, not from the wording:
    # "the blue one" picks a chain without saying "chain", and "how many chains?" says
    # it without picking one.
    picks_chain = any('"auth_asym_id"' in json.dumps(spec[t]["ref"]) for t in T.TRACKS if t in spec)
    return {
        "needs_numbering_offset": bool(res and res["auth_seq_id"] != res["label_seq_id"]),
        "author_chain_differs_from_label": bool(
            picks_chain and e.numbering["auth_chain_differs_from_label_chain"]),
        "needs_ligand_identity": False,
        "needs_uniprot_mapping": False,
        "needs_referent_from_context": spec.get("referent") is not None,
    }


def intended(e: Entry, param: dict, residue: dict | None) -> tuple[str, Any]:
    """The atoms one API selection is meant to pick, written a second time from the
    frozen facts rather than from the selection: in author numbering, with the residue
    name. ``scripts/check_api_refs.py`` resolves both and fails if they differ, so a
    residue number that lands on another residue cannot pass."""
    if "label_comp_id" in param:
        lig = next(x for x in e.facts["ligands"] if x["comp_id"] == param["label_comp_id"])
        return (f"every copy of {lig['comp_id']}",
                [{"auth_asym_id": c["auth_asym_id"], "auth_seq_id": c["auth_seq_id"],
                  "auth_comp_id": lig["comp_id"],
                  **({"pdbx_PDB_ins_code": c["pdbx_PDB_ins_code"]} if c["pdbx_PDB_ins_code"] else {})}
                 for c in lig["copies"]])
    if "struct_asym_id" in param:
        c = next(c for c in e.chains if c["label_asym_id"] == param["struct_asym_id"])
        return (f"polymer chain {c['auth_asym_id']} (entity {c['entity_id']})",
                {"auth_asym_id": c["auth_asym_id"], "label_entity_id": c["entity_id"]})
    if "auth_seq_id" in param:
        assert residue and residue["auth_seq_id"] == param["auth_seq_id"]
        return (f"{residue['comp'].capitalize()}{residue['auth_seq_id']} of chain "
                f"{residue['auth_asym_id']}",
                {"auth_asym_id": param["auth_asym_id"], "auth_seq_id": param["auth_seq_id"],
                 "auth_comp_id": residue["comp"]})
    col = e.table.columns       # everything the file files under that author chain id
    labels = sorted({col["label_asym_id"][i] for i in range(e.table.n)
                     if col["auth_asym_id"][i] == param["auth_asym_id"]})
    return (f"author chain {param['auth_asym_id']} (label chains {', '.join(labels)})",
            [{"label_asym_id": x} for x in labels])


def api_targets(e: Entry, calls: list[dict], residue: dict | None) -> list[dict]:
    out = []
    for ai, call in enumerate(calls):
        for pi, param in enumerate(call.get("data") or []):
            what, atoms = intended(e, param, residue)
            out.append({"action": ai, "param": pi, "what": what, "atoms": atoms,
                        "n_atoms": bin(e.table.selector(atoms)).count("1")})
    return out


def build(held: set[str]) -> tuple[list[dict], list[dict]]:
    """Every task (as file content, checks not yet filled in) and, in step, its spec."""
    pool = entries()
    use = {"mvs": Counter(), "api": Counter()}
    built, specs = [], []
    for family, template, count, tracks in FAMILIES:
        order = sorted(pool, key=lambda e: rng(family, "order", e.id).random())
        first_wording = rng(family, "wording").randrange(60)
        taken: list[str] = []
        for n in range(1, count + 1):
            choice = None
            # least-used structure first, so the tier spreads over the panel
            for e in sorted(order, key=lambda e: sum(use[t][e.id] for t in tracks)):
                if e.id in taken or any(use[t][e.id] >= MAX_PER_TRACK for t in tracks):
                    continue
                r = rng(family, n, e.id)
                r.turn = first_wording + n
                spec = template(e, r)
                if spec is not None:
                    choice = (e, spec)
                    break
            if choice is None:
                raise SystemExit(f"{family}: no structure left for task {n}")
            e, spec = choice
            taken.append(e.id)
            ids = {t: f"{family}-{e.id}-{t}" for t in tracks}
            for t in tracks:
                use[t][e.id] += 1
                side = spec[t]
                prov = {
                    "script": SCRIPT,
                    "inputs": ["data/panel/panel.json", f"data/panel/facts/{e.id}.json",
                               f"molbench/atom_tables/{e.id}.json.gz"],
                    "date": DATE, "checks": [], "seed": f"{SEED}|{family}|{n}|{e.id}",
                    "edit": spec["edit"], "noop_kind": spec.get("noop_kind"),
                    "referent": spec.get("referent"),
                    "preserved": side["preserved"], "removed": spec.get("removed"),
                    "difficulty": difficulty(e, spec),
                }
                if t == "api":      # what scripts/check_api_refs.py reads
                    prov.update(
                        structure=e.id,
                        derived="start state and final state written by the generator from "
                                "one component list; see README.md in this directory",
                        checked_by="scripts/generate_followup_tasks.py (grader checks listed "
                                   "under checks) and scripts/check_api_refs.py (each "
                                   "selection against the intended atoms under targets)",
                        targets=api_targets(e, side["ref"], spec.get("residue")))
                built.append({
                    "id": ids[t], "track": t, "tier": "followup", "family": family,
                    "structures": [e.id], "prompt": spec["prompt"], "reference": side["ref"],
                    "accepted": side.get("accepted", []),
                    "context": {T.CONTEXT_STATE[t]: side["start"], "noop": bool(spec.get("noop"))},
                    "target": side["target"],
                    "twin_of": ids[next(o for o in tracks if o != t)] if len(tracks) == 2 else None,
                    "paraphrase_of": None, "style": "full",
                    "split": "heldback" if e.id in held else "public", "grounding": None,
                    "provenance": prov, "skills": spec["skills"],
                })
                specs.append(side)
    return built, specs


def verify(built: list[dict], specs: list[dict]) -> list[dict]:
    """Check every task (module docstring) and record what each one passed."""
    loaded = []
    for t in built:
        t["provenance"]["checks"] = ["(filled in below, once passed)"]
        errors = T.validate_task(t)
        if errors:
            raise SystemExit(f"{t['id']}: " + "; ".join(errors))
        loaded.append(T._with_aliases({**t, "_path": f"tasks/{t['track']}_followup/{t['id']}.json"}))
    errors, _ = T.check_corpus(loaded, grade=runner.grade_parsed, check=runner.grader_problems)
    problems = list(errors)

    for t, full, side in zip(built, loaded, specs):
        tid, start, ref = t["id"], side["start"], side["ref"]
        noop = t["context"]["noop"]
        checks = ["reference grades as exactly right against the task (success, F1 1"
                  + (", target score 1)" if t["target"] else "; no atom target)"),
                  "start state grades as itself; "
                  + ("it already is the requested final state (no change needed)" if noop
                     else "it is not the requested final state")]
        if t["target"]:
            n_atoms = sum(bin(m).count("1") for m in T.target_atoms(full).values())
            checks.append(f"target selects {n_atoms} atoms on the frozen atom table")
            got = runner.grade_parsed(full, start)["target_f1"]
            if not noop and got == 1.0:
                problems.append(f"{tid}: the start state already scores 1 on the target")
            elif not noop:
                checks.append(f"start state scores {got} on the target (below 1)")
        for p in t["provenance"]["preserved"] or []:
            view = {**full, "target": [p], "accepted": []}
            for name, state in (("reference", ref), ("start state", start)):
                got = runner.grade_parsed(view, state)["target_f1"]
                if got != 1.0:
                    problems.append(f"{tid}: preserved part {p['selector']} scores {got} on the {name}")
        if t["provenance"]["preserved"]:
            checks.append(f"each of the {len(t['provenance']['preserved'])} preserved part(s) "
                          "scores 1 as a target on both the start state and the reference")
        for state in side.get("equivalent", []):
            if not runner.grade_parsed(full, state)["success"]:
                problems.append(f"{tid}: an equivalent final state does not succeed")
        if t["accepted"]:
            checks.append(f"{len(t['accepted'])} accepted alternative final state(s): each "
                          "grades as itself and is accepted by the task (corpus check)")
        if side.get("equivalent"):
            checks.append(f"{len(side['equivalent'])} other way(s) of writing the final state "
                          "grade as exactly right")
        lost = 0
        for state in side.get("wrong", []):
            res = runner.grade_parsed(full, state)
            if res["success"]:
                problems.append(f"{tid}: a wrong control answer succeeds")
            lost += any(runner.grade_parsed({**full, "target": [p], "accepted": []},
                                            state)["target_f1"] < 1.0
                        for p in t["provenance"]["preserved"] or [])
        if side.get("wrong"):
            checks.append(f"{len(side['wrong'])} wrong control answer(s) (the edit on an empty "
                          "viewer, or a known slip) do not grade as right"
                          + (f"; {lost} of them lose a preserved part" if lost else ""))
        if t["twin_of"]:
            checks.append("twin selects the same target atoms")
        res = t["provenance"]["difficulty"]
        if t["provenance"].get("referent"):
            checks.append("referent is unambiguous in the start state: " + t["provenance"]["referent"])
        if res["needs_numbering_offset"]:
            checks.append("the residue's author number differs from its label number; author "
                          "chain + number select exactly that residue's atoms")
        t["provenance"]["checks"] = checks

    # caps on reuse
    for track in T.TRACKS:
        mine = [t for t in built if t["track"] == track]
        per_structure = Counter(t["structures"][0] for t in mine)
        over = {s: n for s, n in per_structure.items() if n > MAX_PER_TRACK}
        if over:
            problems.append(f"{track}: structure(s) over the cap of {MAX_PER_TRACK}: {over}")
        for family, n in Counter(t["family"] for t in mine).items():
            if n / len(mine) > MAX_FAMILY_SHARE:
                problems.append(f"{track}: family {family} is {n}/{len(mine)} of the track")
    if problems:
        raise SystemExit("follow-up tasks fail their checks:\n  " + "\n  ".join(problems))
    return built


def readme(track: str, built: list[dict]) -> str:
    mine = [t for t in built if t["track"] == track]
    other = "api" if track == "mvs" else "mvs"
    name = {"mvs": "MVS", "api": "API"}[track]
    state = {"mvs": "an MVS scene", "api": "the list of calls made so far"}[track]
    structures = sorted({t["structures"][0] for t in mine})
    held = sorted({t["structures"][0] for t in mine if t["split"] == "heldback"})
    lines = [
        f"# Follow-up turns, {name} track (generated; do not edit)",
        "",
        f"Written by `{SCRIPT}` (seed {SEED}); rerun it to rebuild these files byte for byte.",
        f"Each task is a start state ({state}), an edit request, and the complete final state",
        "as the reference. Start state and reference are built from the same component list,",
        "from the frozen panel only. Only the final state is graded.",
        "",
        f"- **{len(mine)} tasks** on {len(structures)} structures, at most {MAX_PER_TRACK} per "
        f"structure; {sum(t['split'] == 'heldback' for t in mine)} held back "
        f"(structures: {', '.join(held) or 'none'}).",
        f"- **{sum(t['context']['noop'] for t in mine)} need no change** (`context.noop`): the "
        "reference is the start state.",
        f"- **{sum(t['twin_of'] is not None for t in mine)} have a twin** on the {other.upper()} "
        "track (`twin_of`): same request, same structure, same target atoms.",
        "",
        "| family | tasks | edit | how the reference is derived |",
        "|---|---:|---|---|",
    ]
    for family, _, _, tracks in FAMILIES:
        if track not in tracks:
            continue
        rows = [t for t in mine if t["family"] == family]
        twin = "" if len(tracks) == 2 else f" ({name} only)"
        lines.append(f"| `{family}` | {len(rows)} | {rows[0]['provenance']['edit']}{twin} | "
                     f"{DERIVED[family]} |")
    lines += [
        "",
        "## What each task records (`provenance`)",
        "",
        "- `edit`: the edit kind; `noop_kind`: why no change is right (already true,",
        "  not expressible in the format); `referent`: why a pronoun or description (\"it\", \"the",
        "  red chain\") names one thing only in the start state.",
        "- `preserved`: the parts of the start state the edit must leave alone, in the form of",
        "  `target` parts. Handing one part to the grader as the task's target gives a",
        "  *preserved* score for it; the reference and the start state both score 1 on every",
        "  part (checked). An answer that rebuilds the scene and loses an earlier choice scores",
        "  below 1 there. `null` when the edit touches everything that was set.",
        "- `removed`: what the edit takes away. On the MVS track the reference draws nothing",
        "  there, so it cannot be a target; such tasks have `target: null`.",
        "- `difficulty`: whether the residue's author number differs from its label number,",
        "  whether the entry's author chain ids differ from its label chain ids, whether the",
        "  request leans on the start state for a referent. Requests give the ligand's code and",
        "  use author numbering, so no ligand identity or UniProt mapping has to be looked up.",
        "- `checks`: what the generator verified before writing the file, with the controls it",
        "  graded (other ways of writing the same final state must succeed; the edit made on an",
        "  empty viewer, and known slips, must not).",
        "",
        "## Left out, and why",
        "",
        "- **Switch to another structure** (\"now show 4HHB instead\"): the task format refuses a",
        "  start state that loads a structure the reference does not (`molbench/tasks.py`), so",
        "  such a task cannot be written yet.",
        "- **A component the user named earlier** (issue #5): the vendored MVS reference and the",
        "  API have no component names to refer back to.",
        "- **\"It\" on the API track**: a bare load already draws everything, so no start state",
        "  has a single thing \"it\" could mean. The API twins of the pronoun tasks are the ones",
        "  that name a component by its colour or as \"the other chain\".",
        "- **Requests the format cannot express**, other than spinning on the MVS track: for a",
        "  distance-based selection or a superposition the unchanged state is not the only",
        "  defensible answer, so they are not tasks here.",
        "- **A target for something removed, on the MVS track**: see `removed` above.",
        "",
        "## Whole chains on the API track",
        "",
        "An author chain id also covers that chain's ligands, ions and waters, which the default",
        "view draws; \"chain B\" as the author chain and as the polymer chain alone would then be",
        "two pictures. Every API start state that colours whole chains therefore sets the",
        "cartoon style first (polymer only), as the MVS twin draws cartoons, and the generator",
        "checks that the same answer written with label chain ids grades as exactly right.",
        "",
        "Held-back structures are the fifth of the panel with the smallest SHA-256 of",
        f"`\"{HELDBACK_SALT}:<id>\"` (a rule on the structure alone), unless the generator was",
        "given a list.",
        "",
    ]
    return "\n".join(lines)


def _script(name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def viewer_check(built: list[dict], specs: list[dict]) -> int:
    """Run the states in the real viewers (needs the ``execute`` extra and Chromium;
    structure files come from the frozen panel). Returns the number of disagreements.

    MVS: every start scene and reference passes Mol* 5.9.0's own validation, and what
    Mol* draws (atoms, representation, colour, opacity per representation object) is what
    the grader resolves the scene to. Labels, focus and background are not drawn state
    and are not read back. API: every start state and every "equivalent" control is
    replayed in pdbe-molstar 3.3.2 and compared with the grader's replay
    (``scripts/check_api_refs.py --viewer`` does the same for the references)."""
    import copy

    from molbench import pdbe_state, render
    bad = 0
    scenes: list[tuple[str, dict]] = []
    lists: list[tuple[str, list]] = []
    for t, side in zip(built, specs):
        states = [("start", side["start"])] + ([] if t["context"]["noop"] else [("reference", side["ref"])])
        if t["track"] == "mvs":
            scenes += [(f"{t['id']} {name}", s) for name, s in states]
        else:
            lists += [(f"{t['id']} start", side["start"])]
            lists += [(f"{t['id']} equivalent[{i}]", s) for i, s in enumerate(side.get("equivalent", []))]
            lists += [(f"{t['id']} accepted[{i}]", s) for i, s in enumerate(side.get("accepted", []))]
    issues = render.molstar_issues([s for _, s in scenes])
    for (name, _), found in zip(scenes, issues):
        if found:
            bad += 1
            print(f"mol*  {name}: INVALID: {found[:2]}")
    print(f"mol*: {len(scenes)} scenes validated by Mol*, {sum(bool(i) for i in issues)} invalid")
    controls = _script("grader_controls")
    with controls.Molstar(REPO / "data" / "cif") as molstar:
        differ = 0
        for name, tree in scenes:
            seen = molstar.state(tree)
            if isinstance(seen, str) or not controls._grader_vs_viewer(tree, seen):
                differ += 1
                print(f"mol*  {name}: DIFFERS from the grader's state"
                      + (f" ({seen[:120]})" if isinstance(seen, str) else ""))
    bad += differ
    print(f"mol*: {len(scenes)} scenes drawn in Mol*, {differ} differ from the grader's resolved state")
    refs = _script("check_api_refs")
    differ = n_sel = 0
    with refs.Viewer() as viewer:
        for name, actions in lists:
            dump = viewer.run(copy.deepcopy(actions))
            found = refs.compare_with_viewer(actions, dump)
            n_sel += sum(len(x["params"]) for x in dump.get("selections", []))
            if found or pdbe_state.replay(copy.deepcopy(actions)).unresolved:
                differ += 1
                print(f"pdbe  {name}: DIFFERS: {found[:2]}")
    bad += differ
    print(f"pdbe-molstar: {len(lists)} call lists run, {n_sel} selections compared atom for atom, "
          f"{differ} differ from the grader's replay")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the files would change")
    ap.add_argument("--heldback-file", type=pathlib.Path,
                    help="structure ids to hold back, one per line (replaces the hash rule)")
    ap.add_argument("--viewer", action="store_true",
                    help="also run every state in headless Mol* / pdbe-molstar and compare "
                         "with the grader (writes nothing)")
    a = ap.parse_args(argv)
    listed = None
    if a.heldback_file:
        listed = {x.strip().lower() for x in a.heldback_file.read_text().split() if x.strip()}
    built, specs = build(heldback_ids(listed))
    built = verify(built, specs)
    if a.viewer:
        bad = viewer_check(built, specs)
        print("viewer check:", "all states agree" if not bad else f"{bad} problem(s)")
        return 1 if bad else 0
    files = {OUT[t["track"]] / f"{t['id']}.json": json.dumps(t, indent=1) + "\n" for t in built}
    for track, out in OUT.items():
        files[out / "README.md"] = readme(track, built)
    existing = {p for out in OUT.values() for p in list(out.glob("*.json")) + list(out.glob("README.md"))}
    stale = sorted(existing - set(files))
    changed = [p for p, text in files.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text]
    counts = Counter(t["track"] for t in built)
    if a.check:
        if changed or stale:
            print("follow-up tasks are out of date:", *[p.name for p in changed + stale])
            return 1
        print(f"{len(built)} follow-up tasks are up to date ({dict(counts)})")
        return 0
    for out in OUT.values():
        out.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"wrote {len(built)} follow-up tasks ({dict(counts)}); {len(changed)} files changed, "
          f"{len(stale)} removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
