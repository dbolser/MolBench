"""
Structure grounding for Tier-2 tasks (gemmi).

Tier-2 tasks select things by *identity* — "the heme", "the disulfide bonds",
"Arg36" — so their references cannot be invented; they must be **extracted from
the real structure**. This module reads the mmCIF with gemmi and returns the
facts a generator needs, so a task's answer key is true by extraction.

gemmi-only facts (no network annotations): ligands, disulfides, residue identity.
The SIFTS UniProt<->auth numbering bridge and ClinVar/functional-site annotations
layer on top of this (separate modules) for the harder task types.

Requires the ``authoring`` extra (``pip install -e ".[authoring]"``).
"""

from __future__ import annotations

import urllib.request
from typing import NamedTuple

CIF = "https://files.rcsb.org/download/{}.cif"
WATER = {"HOH", "DOD"}


class Residue(NamedTuple):
    auth_asym_id: str
    auth_seq_id: int
    comp_id: str


def fetch_structure(pdb: str):
    """Download + parse an mmCIF into a gemmi Structure (entities set up)."""
    import gemmi
    data = urllib.request.urlopen(CIF.format(pdb.lower()), timeout=30).read().decode()
    st = gemmi.make_structure_from_block(gemmi.cif.read_string(data).sole_block())
    st.setup_entities()
    return st


def ligands(st) -> list[Residue]:
    """Non-polymer, non-water residues (heme, ATP, metal ions, ...)."""
    out: list[Residue] = []
    for chain in st[0]:
        for r in chain.get_ligands():
            if r.name not in WATER:
                out.append(Residue(chain.name, r.seqid.num, r.name))
    return out


def disulfides(st) -> list[tuple[Residue, Residue]]:
    """Cys-Cys bonds, read straight from struct_conn (conn_type 'disulf')."""
    import gemmi
    out: list[tuple[Residue, Residue]] = []
    for c in st.connections:
        if c.type == gemmi.ConnectionType.Disulf:
            a, b = c.partner1, c.partner2
            out.append((
                Residue(a.chain_name, a.res_id.seqid.num, "CYS"),
                Residue(b.chain_name, b.res_id.seqid.num, "CYS"),
            ))
    return out


def residue_at(st, auth_asym_id: str, auth_seq_id: int) -> str | None:
    """The 3-letter code at an author chain/number — for validating 'Arg36' tasks."""
    for chain in st[0]:
        if chain.name != auth_asym_id:
            continue
        for r in chain:
            if r.seqid.num == auth_seq_id:
                return r.name
    return None


def unique_residues(pairs: list[tuple[Residue, Residue]]) -> list[Residue]:
    """Flatten bond pairs to the distinct residues involved (order-stable)."""
    seen: dict[tuple, Residue] = {}
    for a, b in pairs:
        for r in (a, b):
            seen.setdefault((r.auth_asym_id, r.auth_seq_id), r)
    return list(seen.values())
