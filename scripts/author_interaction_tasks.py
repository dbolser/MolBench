#!/usr/bin/env python3
"""
Author the interaction / measurement MVS tasks (``tasks/mvs_interactions/``).

These exercise the parts of MVS the original corpus never asked for: ``primitives``
(dashed lines between named atoms, labelled with their length), Mol*'s computed
non-covalent interactions (``custom.molstar_show_non_covalent_interactions``) and
``opacity``. A user asking to "show the hydrogen bond" is a common viewer request
that the old reference could not express.

Like ``author_mvs_tasks.py``, each reference is built with the ``molviewspec``
builder. In addition, every ComponentExpression in a reference is resolved against
the real mmCIF with gemmi before the task is written: a selection that matches no
atom is not an error in Mol* (a primitive end silently lands at the origin), so the
ground truth must be checked here. Each measured distance is recorded in the task's
provenance.

    python scripts/author_interaction_tasks.py   # (re)generate tasks/mvs_interactions/*.json
"""

from __future__ import annotations

import json
import pathlib
import urllib.request

import gemmi
from molviewspec import ComponentExpression, create_builder

from molbench.mvs import categorize

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "tasks" / "mvs_interactions"
CACHE = REPO / "data" / "cif"
CIF = "https://files.rcsb.org/download/{}.cif"


def _structure(pdb: str):
    b = create_builder()
    s = b.download(url=CIF.format(pdb)).parse(format="mmcif").model_structure()
    return b, s


def _atom(chain: str, atom: str, seq: int | None = None, comp: str | None = None) -> dict:
    """A ComponentExpression naming one atom (by residue number or by ligand code)."""
    e = {"auth_asym_id": chain, "label_atom_id": atom}
    if seq is not None:
        e["auth_seq_id"] = seq
    if comp is not None:
        e["label_comp_id"] = comp
    return e


def _sticks(s, chain: str, seq: int | None = None, comp: str | None = None) -> None:
    kw = {"auth_seq_id": seq} if seq is not None else {"label_comp_id": comp}
    s.component(selector=ComponentExpression(auth_asym_id=chain, **kw)) \
        .representation(type="ball_and_stick")


def _cartoon(s) -> None:
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")


# --- task definitions -------------------------------------------------------------

def t_his64_o2():
    b, s = _structure("1a6m")
    _cartoon(s)
    _sticks(s, "A", seq=64)
    _sticks(s, "A", comp="OXY")
    s.primitives().distance(start=_atom("A", "NE2", seq=64), end=_atom("A", "O2", comp="OXY"),
                            dash_length=0.15, label_template="{{distance}}")
    return b


def t_fe_his93():
    b, s = _structure("1a6m")
    _cartoon(s)
    _sticks(s, "A", comp="HEM")
    _sticks(s, "A", seq=93)
    s.primitives().distance(start=_atom("A", "FE", comp="HEM"), end=_atom("A", "NE2", seq=93),
                            dash_length=0.15, label_template="{{distance}}")
    return b


def t_triad():
    b, s = _structure("3ptb")
    _cartoon(s)
    for r in (57, 102, 195):
        _sticks(s, "A", seq=r)
    p = s.primitives()
    p.distance(start=_atom("A", "OG", seq=195), end=_atom("A", "NE2", seq=57),
               dash_length=0.15, label_template="{{distance}}")
    p.distance(start=_atom("A", "ND1", seq=57), end=_atom("A", "OD2", seq=102),
               dash_length=0.15, label_template="{{distance}}")
    return b


def t_o2_interactions():
    b, s = _structure("1a6m")
    _cartoon(s)
    s.component(selector=ComponentExpression(label_comp_id="OXY"),
                custom={"molstar_show_non_covalent_interactions": True})
    return b


def t_benzamidine_interactions():
    b, s = _structure("3ptb")
    _cartoon(s)
    s.component(selector=ComponentExpression(label_comp_id="BEN"),
                custom={"molstar_show_non_covalent_interactions": True})
    return b


def t_transparent_surface():
    b, s = _structure("1hho")
    s.component(selector="polymer").representation(type="surface").opacity(opacity=0.5)
    s.component(selector="ligand").representation(type="ball_and_stick")
    return b


TASKS = [
    {"id": "int-001", "pdb": "1a6m", "build": t_his64_o2,
     "title": "H-bond: distal His64 to bound O2",
     "prompt": "In oxymyoglobin 1A6M, show the protein as a grey cartoon, His64 and the bound "
               "O2 as ball-and-stick, and draw the hydrogen bond from His64 NE2 to the O2 "
               "molecule's terminal oxygen (atom O2) as a dashed line labelled with its length.",
     "skills": ["primitives", "atom-selection", "hbond"]},
    {"id": "int-002", "pdb": "1a6m", "build": t_fe_his93,
     "title": "Distance: heme iron to proximal histidine",
     "prompt": "Load 1A6M with the protein as a grey cartoon. Show the heme and the proximal "
               "histidine as ball-and-stick and measure the distance from the heme iron to the "
               "histidine's coordinating nitrogen.",
     "skills": ["primitives", "atom-selection", "domain-knowledge"]},
    {"id": "int-003", "pdb": "3ptb", "build": t_triad,
     "title": "Catalytic-triad H-bonds in trypsin",
     "prompt": "In trypsin (3PTB), show the protein as a grey cartoon and the catalytic triad "
               "(His57, Asp102, Ser195) as ball-and-stick. Draw the two triad hydrogen bonds as "
               "dashed lines with their lengths.",
     "skills": ["primitives", "atom-selection", "hbond", "domain-knowledge"]},
    {"id": "int-004", "pdb": "1a6m", "build": t_o2_interactions,
     "title": "Computed interactions around bound O2",
     "prompt": "Load 1A6M with the protein as a grey cartoon and show all the non-covalent "
               "interactions (hydrogen bonds, metal contacts) around the bound oxygen molecule.",
     "skills": ["interactions"]},
    {"id": "int-005", "pdb": "3ptb", "build": t_benzamidine_interactions,
     "title": "Computed interactions around benzamidine",
     "prompt": "Show trypsin 3PTB as a grey cartoon and display the interactions between the "
               "benzamidine inhibitor and the protein.",
     "skills": ["interactions"]},
    {"id": "int-006", "pdb": "1hho", "build": t_transparent_surface,
     "title": "Half-transparent surface over the hemes",
     "prompt": "Load haemoglobin 1HHO; show the protein as a 50% transparent surface and the "
               "heme groups as ball-and-stick.",
     "skills": ["opacity", "surface"]},
]


# --- ground-truth checks ----------------------------------------------------------

def _load(pdb: str) -> gemmi.Structure:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{pdb}.cif"
    if not path.exists():
        urllib.request.urlretrieve(CIF.format(pdb), path)
    return gemmi.read_structure(str(path))


def _match(st: gemmi.Structure, e: dict) -> list[gemmi.Atom]:
    """Atoms a ComponentExpression selects (the fields this script uses)."""
    if not isinstance(e, dict):
        return []  # an [x, y, z] coordinate, not a selection
    out = []
    for chain in st[0]:
        if e.get("auth_asym_id") not in (None, chain.name):
            continue
        for res in chain:
            if e.get("auth_seq_id") not in (None, res.seqid.num):
                continue
            if e.get("label_comp_id") not in (None, res.name):
                continue
            out += [a for a in res if e.get("label_atom_id") in (None, a.name)]
    return out


def _check(root: dict, st: gemmi.Structure, task_id: str) -> list[dict]:
    """Fail on any selection that matches nothing; return each measured distance."""
    measured = []

    def walk(node: dict) -> None:
        params = node.get("params") or {}
        sel = params.get("selector")
        if node.get("kind") == "component" and isinstance(sel, dict):
            assert _match(st, sel), f"{task_id}: selector matches nothing: {sel}"
        if node.get("kind") == "primitive":
            points = {k: params[k] for k in ("start", "end", "position", "a", "b", "c")
                      if isinstance(params.get(k), dict)}
            atoms = {k: _match(st, e) for k, e in points.items()}
            assert all(atoms.values()), f"{task_id}: primitive point matches nothing: {params}"
            if "start" in atoms and "end" in atoms:
                # Mol* uses the centre of an end's atoms (alt locs included); record the first.
                measured.append({"start": params["start"], "end": params["end"],
                                 "distance_A": round(atoms["start"][0].pos.dist(atoms["end"][0].pos), 2)})
        for c in node.get("children") or []:
            walk(c)

    walk(root)
    return measured


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for t in TASKS:
        root = json.loads(t["build"]().get_state().dumps())["root"]
        measured = _check(root, _load(t["pdb"]), t["id"])
        doc = {
            "id": t["id"],
            "category": "mvs",
            "source": "interactions",
            "pdb": t["pdb"],
            "title": t["title"],
            "prompt": t["prompt"],
            "reference_mvs": root,
            "categories": categorize(root),
            "skills": t["skills"],
            "provenance": {"checked_against": CIF.format(t["pdb"]), "measured": measured},
        }
        path = OUT / f"{t['id'].replace('-', '_')}.json"
        path.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote {path.relative_to(REPO)}  {[m['distance_A'] for m in measured]}")


if __name__ == "__main__":
    main()
