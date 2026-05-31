#!/usr/bin/env python3
"""
Author MVS benchmark tasks from builder code.

Each task is defined once as (prompt + a builder function). We run the builder to
produce the canonical MVS tree and write it into ``tasks/mvs/<id>.json`` as the
reference. Authoring with the real ``molviewspec`` builder means the ground truth
is correct *by construction* — you can never commit a malformed reference, which
is what makes scaling to hundreds of tasks safe.

    python scripts/author_mvs_tasks.py        # (re)generate tasks/mvs/*.json

Add a structure here, get a task. This is the seam where MolViewStories /
Proteopedia scraping will eventually plug in (their .mvsj scenes become the
reference trees directly).
"""

from __future__ import annotations

import json
import pathlib

from molviewspec import ComponentExpression, create_builder

from molbench.mvs import categorize

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "tasks" / "mvs"
CIF = "https://files.rcsb.org/download/{}.cif"


def _structure(pdb: str):
    b = create_builder()
    s = b.download(url=CIF.format(pdb)).parse(format="mmcif").model_structure()
    return b, s


def reference_root(build) -> dict:
    """Run a builder function, return the canonical root node (metadata stripped)."""
    b = build()
    return json.loads(b.get_state().dumps())["root"]


# --- task definitions -------------------------------------------------------------
# Each: id, title, prompt, builder thunk, skills, notes.

def t_load_cartoon():
    b, s = _structure("1hho")
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    return b


def t_heme():
    b, s = _structure("1hho")
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    lig = s.component(selector="ligand")
    lig.representation(type="ball_and_stick").color(color="orange")
    return b


def t_active_site():
    b, s = _structure("1lyz")
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    for r in (35, 52):
        c = s.component(selector=ComponentExpression(auth_asym_id="A", auth_seq_id=r))
        c.representation(type="ball_and_stick").color(color="red")
    return b


def t_ligand_focus():
    b, s = _structure("1hvr")
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    lig = s.component(selector="ligand")
    lig.representation(type="ball_and_stick").color(color="magenta")
    lig.focus()
    return b


def t_surface():
    b, s = _structure("4ins")
    s.component(selector="polymer").representation(type="surface").color(color="steelblue")
    return b


TASKS = [
    dict(id="mvs-001", title="Load and cartoon",
         prompt="Load haemoglobin (PDB 1HHO) and show the protein as a grey cartoon.",
         build=t_load_cartoon, skills=["download", "component", "representation", "color"],
         notes="Minimal scene: one polymer cartoon component."),
    dict(id="mvs-002", title="Heme ball-and-stick",
         prompt="Load haemoglobin (1HHO); show the protein as a grey cartoon and the "
                "heme groups as orange ball-and-stick.",
         build=t_heme, skills=["multi-component", "ligand-selector", "color"],
         notes="Heme is selected via the 'ligand' component selector."),
    dict(id="mvs-003", title="Catalytic residues",
         prompt="Load hen egg-white lysozyme (1LYZ) as a grey cartoon, and show the two "
                "catalytic residues Glu35 and Asp52 on chain A as red ball-and-stick.",
         build=t_active_site, skills=["residue-selection", "ComponentExpression", "color"],
         notes="Tests the ComponentExpression selection sub-language (auth_asym_id/auth_seq_id)."),
    dict(id="mvs-004", title="Focus the inhibitor",
         prompt="Load HIV-1 protease (1HVR); protein as grey cartoon, the bound inhibitor "
                "as magenta ball-and-stick, and focus the camera on the inhibitor.",
         build=t_ligand_focus, skills=["ligand-selector", "focus", "color"],
         notes="Adds a focus node under the ligand component."),
    dict(id="mvs-005", title="Surface representation",
         prompt="Load insulin (4INS) and render the protein as a steel-blue molecular surface.",
         build=t_surface, skills=["representation-surface", "color"],
         notes="Uses the 'surface' representation type."),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for t in TASKS:
        root = reference_root(t["build"])
        doc = {
            "id": t["id"],
            "category": "mvs",
            "title": t["title"],
            "prompt": t["prompt"],
            "reference_mvs": root,
            "categories": categorize(root),   # same auto-tagger as the ingested tasks
            "skills": t["skills"],
            "notes": t["notes"],
        }
        path = OUT / f"{t['id'].replace('-', '_')}.json"
        path.write_text(json.dumps(doc, indent=2))
        print(f"wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
