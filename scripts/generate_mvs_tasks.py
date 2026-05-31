#!/usr/bin/env python3
"""
Tier-1 MVS task generator — coordinate/structural selections.

Generates Component-1 tasks whose references are correct *by construction*: the
prompt fully specifies a generic selector (ligand / ion / water / chain / residue
range) and a representation/colour, and we build the matching MVS tree with the
official ``molviewspec`` builder. No biological lookup is required, so nothing can
be wrong — we are grading natural-language -> selector translation.

What this deliberately does NOT do: identity selections like "ARG36", "the
disulfide bridge", "the catalytic triad". Those need the reference *extracted from
the real structure* (mmCIF struct_conn / SIFTS numbering) — that's the grounded
Tier-2 generator, tracked separately.

    python scripts/generate_mvs_tasks.py        # -> tasks/mvs_generated/*.json
"""

from __future__ import annotations

import json
import pathlib

from molviewspec import ComponentExpression, create_builder

from molbench.mvs import categorize

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "tasks" / "mvs_generated"
CIF = "https://files.rcsb.org/download/{}.cif"

# Real structures (so scenes also render later for Component 2), each annotated
# with a chain and a residue range it actually contains. Selector validity for
# grading does not depend on these being right, but realism helps downstream.
STRUCTURES = [
    {"pdb": "1hho", "name": "haemoglobin", "chain": "A", "range": (30, 90)},
    {"pdb": "4ins", "name": "insulin", "chain": "B", "range": (5, 25)},
    {"pdb": "1lyz", "name": "lysozyme", "chain": "A", "range": (40, 80)},
    {"pdb": "3ptb", "name": "trypsin", "chain": "A", "range": (50, 110)},
    {"pdb": "1cbs", "name": "cellular retinoic-acid binding protein", "chain": "A", "range": (20, 60)},
    {"pdb": "2hhb", "name": "deoxyhaemoglobin", "chain": "B", "range": (10, 70)},
]

COLORS = ["red", "blue", "green", "orange", "purple", "teal"]
SURF_COLORS = ["steelblue", "salmon", "khaki", "plum"]


def _struct(pdb):
    b = create_builder()
    s = b.download(url=CIF.format(pdb)).parse(format="mmcif").model_structure()
    return b, s


# Each template returns (prompt, builder, extra-notes). They cover distinct skills
# so the generated set is category-balanced for the leaderboard drill-down.

def t_cartoon(st, i):
    color = COLORS[i % len(COLORS)]
    b, s = _struct(st["pdb"])
    s.component(selector="polymer").representation(type="cartoon").color(color=color)
    return f"Load {st['name']} ({st['pdb'].upper()}) and show the protein as a {color} cartoon.", b


def t_surface(st, i):
    color = SURF_COLORS[i % len(SURF_COLORS)]
    b, s = _struct(st["pdb"])
    s.component(selector="polymer").representation(type="surface").color(color=color)
    return f"Load {st['pdb'].upper()}; render the protein as a {color} molecular surface.", b


def t_ligands(st, i):
    color = COLORS[i % len(COLORS)]
    b, s = _struct(st["pdb"])
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    s.component(selector="ligand").representation(type="ball_and_stick").color(color=color)
    return (f"Load {st['pdb'].upper()}; show the protein as a grey cartoon and the "
            f"ligands as {color} ball-and-stick."), b


def t_ions(st, i):
    b, s = _struct(st["pdb"])
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    s.component(selector="ion").representation(type="spacefill").color(color="purple")
    return (f"Load {st['pdb'].upper()}; protein as grey cartoon, and show the ions "
            f"as purple spheres."), b


def t_chain(st, i):
    color = COLORS[i % len(COLORS)]
    b, s = _struct(st["pdb"])
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    s.component(selector=ComponentExpression(auth_asym_id=st["chain"])) \
        .representation(type="cartoon").color(color=color)
    return (f"Load {st['pdb'].upper()}; show everything as a grey cartoon, then colour "
            f"chain {st['chain']} {color}."), b


def t_range(st, i):
    a, z = st["range"]
    b, s = _struct(st["pdb"])
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    s.component(selector=ComponentExpression(
        auth_asym_id=st["chain"], beg_auth_seq_id=a, end_auth_seq_id=z)) \
        .representation(type="ball_and_stick").color(color="orange")
    return (f"Load {st['pdb'].upper()}; protein as grey cartoon, and show residues "
            f"{a}-{z} of chain {st['chain']} as orange ball-and-stick."), b


def t_focus_ligand(st, i):
    b, s = _struct(st["pdb"])
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    lig = s.component(selector="ligand")
    lig.representation(type="ball_and_stick").color(color="magenta")
    lig.focus()
    return (f"Load {st['pdb'].upper()}; grey cartoon protein, magenta ball-and-stick "
            f"ligands, and focus the camera on the ligand."), b


TEMPLATES = {
    "cartoon": t_cartoon, "surface": t_surface, "ligands": t_ligands,
    "ions": t_ions, "chain": t_chain, "range": t_range, "focus": t_focus_ligand,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("gen-*.json"):
        stale.unlink()
    written = 0
    for i, st in enumerate(STRUCTURES):
        for tname, tfn in TEMPLATES.items():
            prompt, builder = tfn(st, i)
            root = json.loads(builder.get_state().dumps())["root"]
            doc = {
                "id": f"gen-{tname}-{st['pdb']}",
                "category": "mvs",
                "source": "generated",
                "template": tname,
                "prompt": prompt,
                "reference_mvs": root,
                "categories": categorize(root),
            }
            (OUT / f"{doc['id']}.json").write_text(json.dumps(doc, indent=2))
            written += 1
    print(f"wrote {written} generated tasks to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
