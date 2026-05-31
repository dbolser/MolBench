"""
Clinical variants — pathogenic ClinVar residues from the UniProt Variation API.

For a UniProt accession, returns the residue positions (UniProt numbering) that
carry a pathogenic variant cross-referenced to ClinVar. Combined with the SIFTS
bridge (``molbench.sifts``) and gemmi, this lets us author tasks like "highlight
the residue affected by the R175H pathogenic variant" whose answer key is the
actual structural residue — true by extraction from clinical data.
"""

from __future__ import annotations

import json
import urllib.request
from typing import NamedTuple

PROTEINS = "https://www.ebi.ac.uk/proteins/api/variation/{}"


class Variant(NamedTuple):
    unp_pos: int
    wild_type: str        # 1-letter
    alt: str              # 1-letter
    significance: str


def pathogenic_clinvar(acc: str) -> list[Variant]:
    """Pathogenic, ClinVar-cross-referenced single-residue variants for an accession."""
    req = urllib.request.Request(PROTEINS.format(acc),
                                 headers={"Accept": "application/json"})
    data = json.load(urllib.request.urlopen(req, timeout=60))
    out: list[Variant] = []
    for f in data.get("features", []):
        if f.get("type") != "VARIANT":
            continue
        sigs = f.get("clinicalSignificances") or []
        sig = next((s.get("type", "") for s in sigs if "athogenic" in s.get("type", "")), None)
        if not sig:
            continue
        if not any(x.get("name") == "ClinVar" for x in (f.get("xrefs") or [])):
            continue
        try:
            pos = int(f["begin"])
        except (KeyError, ValueError, TypeError):
            continue
        if f.get("begin") != f.get("end"):   # single-residue substitutions only
            continue
        out.append(Variant(pos, f.get("wildType", ""), f.get("alternativeSequence", ""), sig))
    return out
