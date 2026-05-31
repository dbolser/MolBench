#!/usr/bin/env python3
"""
Tier-2 grounded task generator (gemmi-only types: ligands, disulfides).

Unlike the Tier-1 generator (generic selectors), these tasks select by *identity*,
so each reference is built from facts extracted from the real structure via
``molbench.grounding``. The extracted facts are stored under ``provenance`` so the
answer key is auditable.

Covered now (no external annotations needed):
  * ligand-by-name    "show the HEM groups"        -> label_comp_id selector
  * disulfide-bonds   "highlight the disulfides"   -> the exact Cys residues

Coming next (need SIFTS / annotations): named-residue numbering, functional sites,
ClinVar pathogenic residues.

    pip install -e ".[authoring]"
    python scripts/generate_grounded_tasks.py     # -> tasks/mvs_grounded/*.json
"""

from __future__ import annotations

import json
import pathlib

from molviewspec import ComponentExpression, create_builder

from molbench import grounding
from molbench.mvs import categorize

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "tasks" / "mvs_grounded"
CIF = "https://files.rcsb.org/download/{}.cif"

# Structures with interesting ligands and/or disulfides.
PDBS = ["1hho", "4ins", "3ptb", "1cbs", "1lyz", "2hhb", "3ptb", "1ubq"]

# Ligands too ubiquitous/uninteresting to make a task out of on their own.
SKIP_LIGANDS = {"GOL", "EDO", "SO4", "PO4", "ACT", "PEG", "MPD"}


def _base(pdb):
    b = create_builder()
    s = b.download(url=CIF.format(pdb)).parse(format="mmcif").model_structure()
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    return b, s


def _root(builder) -> dict:
    return json.loads(builder.get_state().dumps())["root"]


def ligand_task(pdb, comp):
    b, s = _base(pdb)
    s.component(selector=ComponentExpression(label_comp_id=comp)) \
        .representation(type="ball_and_stick").color(color="orange")
    prompt = (f"Load {pdb.upper()}; show the protein as a grey cartoon and the "
              f"{comp} as orange ball-and-stick.")
    return prompt, _root(b)


def disulfide_task(pdb, residues):
    b, s = _base(pdb)
    sel = [ComponentExpression(auth_asym_id=r.auth_asym_id, auth_seq_id=r.auth_seq_id)
           for r in residues]
    s.component(selector=sel).representation(type="ball_and_stick").color(color="yellow")
    prompt = (f"Load {pdb.upper()}; protein as grey cartoon, and highlight the "
              f"disulfide-bonded cysteines as yellow ball-and-stick.")
    return prompt, _root(b)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("grd-*.json"):
        stale.unlink()
    written = 0
    for pdb in dict.fromkeys(PDBS):  # de-dup, keep order
        try:
            st = grounding.fetch_structure(pdb)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {pdb}: {e}")
            continue

        # one ligand task for the most interesting ligand present
        ligs = [r for r in grounding.ligands(st) if r.comp_id not in SKIP_LIGANDS]
        comps = list(dict.fromkeys(r.comp_id for r in ligs))
        if comps:
            comp = comps[0]
            prompt, root = ligand_task(pdb, comp)
            _write(f"grd-ligand-{pdb}-{comp.lower()}", pdb, prompt, root,
                   {"ligand": comp})
            written += 1

        # one disulfide task if the structure has any
        ss = grounding.disulfides(st)
        if ss:
            residues = grounding.unique_residues(ss)
            prompt, root = disulfide_task(pdb, residues)
            _write(f"grd-disulfide-{pdb}", pdb, prompt, root,
                   {"disulfides": [[list(a), list(b)] for a, b in ss]})
            written += 1

    print(f"wrote {written} grounded tasks to {OUT.relative_to(REPO)}")


def _write(task_id, pdb, prompt, root, provenance):
    doc = {
        "id": task_id,
        "category": "mvs",
        "source": "grounded",
        "pdb": pdb,
        "prompt": prompt,
        "reference_mvs": root,
        "categories": categorize(root),
        "provenance": provenance,   # the extracted facts the reference is built from
    }
    (OUT / f"{task_id}.json").write_text(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
