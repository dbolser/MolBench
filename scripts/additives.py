"""The one list of components that are not biological ligands (``data/corpus/additives.json``).

"Main ligand" and "the ligand" mean a biological ligand: a substrate, cofactor, inhibitor
or drug. Crystallisation additives, buffers, salts, detergents and lipids are real
components of an entry, but not what such a request is about (ruling of 2026-11-15,
FINAL_PLAN.md). Every generator reads this list; none keeps its own.
"""

from __future__ import annotations

import json
import pathlib

FILE = pathlib.Path(__file__).resolve().parent.parent / "data" / "corpus" / "additives.json"
INPUT = "data/corpus/additives.json"

_doc = json.loads(FILE.read_text(encoding="utf-8"))
#: component code -> what it is
NAMES: dict[str, str] = {code: name for group in _doc["classes"].values() for code, name in group.items()}
ADDITIVES: frozenset[str] = frozenset(NAMES)


def is_biological(ligand: dict) -> bool:
    """A record of ``facts["ligands"]``: a ligand (not an ion or a sugar) that is not an additive."""
    return ligand.get("kind") == "ligand" and ligand["comp_id"] not in ADDITIVES
