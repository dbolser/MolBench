"""
SIFTS bridge — UniProt <-> PDB author numbering (PDBe API).

This is the keystone for clinical/identity tasks: literature, ClinVar and UniProt
all number residues in the *canonical UniProt* frame, while a structure uses its
own *author* numbering, and the two can differ by an offset (or per-chain). SIFTS
is the authoritative residue-level mapping between them — exactly the thing that
answers "Arg36 in which numbering?".

Used at task-authoring time; the resolved residues are frozen into the task JSON,
so there is no live dependency at grading time.
"""

from __future__ import annotations

import json
import urllib.request

PDBE = "https://www.ebi.ac.uk/pdbe/api/mappings/{}"


def mappings(pdb: str) -> dict:
    """{accession: {'name': str, 'segments': [{chain, unp_start, unp_end, offset}]}}.

    offset = author_residue_number - unp_residue_number for the segment, so
    auth = unp + offset for any UniProt position within [unp_start, unp_end].
    """
    pdb = pdb.lower()
    data = json.load(urllib.request.urlopen(PDBE.format(pdb), timeout=30))
    unp = data[pdb]["UniProt"]
    out: dict[str, dict] = {}
    for acc, info in unp.items():
        segs = []
        for m in info["mappings"]:
            auth_start = m["start"].get("author_residue_number")
            if auth_start is None:
                continue
            segs.append({
                "chain": m["chain_id"],
                "unp_start": m["unp_start"],
                "unp_end": m["unp_end"],
                "offset": auth_start - m["unp_start"],
            })
        if segs:
            out[acc] = {"name": info.get("identifier"), "segments": segs}
    return out


def unp_to_auth(maps: dict, acc: str, unp_resnum: int) -> list[tuple[str, int]]:
    """Map a UniProt position to (auth_chain, auth_seq_id) across covering segments."""
    res = []
    for s in maps.get(acc, {}).get("segments", []):
        if s["unp_start"] <= unp_resnum <= s["unp_end"]:
            res.append((s["chain"], unp_resnum + s["offset"]))
    return res
