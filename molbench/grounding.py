"""
Structure grounding for Tier-2 tasks (gemmi).

Tier-2 tasks select things by *identity* — "the heme", "the disulfide bonds",
"Arg36" — so their references cannot be invented; they must be **extracted from
the real structure**. This module reads the mmCIF with gemmi and returns the
facts a generator needs, so a task's answer key is true by extraction.

gemmi-only facts (no network annotations): ligands, disulfides, residue identity.
The SIFTS UniProt<->auth numbering bridge and ClinVar/functional-site annotations
layer on top of this (separate modules) for the harder task types.

The structure panel (``data/panel/``, built by ``scripts/build_panel.py``) freezes
all of this, so a generator can run with no network: :func:`panel_entries` lists the
entries, :func:`facts` returns one entry's extracted facts (chains and numbering
offsets, ligands, metals, disulfides, glycans, assemblies, ...), :func:`variants`
the verified ClinVar variants of a disease protein, and :func:`fetch_structure`
reads a panel entry's frozen mmCIF instead of downloading it. These loaders are
stdlib-only; only the gemmi helpers need the ``authoring`` extra
(``pip install -e ".[authoring]"``). The panel lives in the repository, not in the
wheel: it is authoring data, and grading does not read it.
"""

from __future__ import annotations

import functools
import json
import pathlib
import urllib.request
from typing import NamedTuple

CIF = "https://files.rcsb.org/download/{}.cif"
WATER = {"HOH", "DOD"}
PANEL = pathlib.Path(__file__).resolve().parent.parent / "data" / "panel"


# --- the frozen panel (no network, no gemmi) --------------------------------------

@functools.lru_cache(maxsize=None)
def panel() -> dict:
    """``data/panel/panel.json``: ``entries`` (one record per structure: id, title,
    method, atoms, features, families, why, ...) and ``disease_proteins``."""
    return json.loads((PANEL / "panel.json").read_text())


def panel_entries(family: str | None = None) -> list[dict]:
    """The panel's entries, optionally only those that can serve a task family
    ('ligand', 'disulfide', 'clinical', 'numbering', 'assembly', 'glycan', ...)."""
    return [e for e in panel()["entries"] if family is None or family in e["families"]]


@functools.lru_cache(maxsize=None)
def facts(entry: str) -> dict | None:
    """Frozen facts for a panel entry (see ``data/panel/README.md`` for the fields),
    or None if the entry is not in the panel."""
    path = PANEL / "facts" / f"{entry.lower()}.json"
    return json.loads(path.read_text()) if path.exists() else None


@functools.lru_cache(maxsize=None)
def variants(accession: str) -> dict | None:
    """Frozen pathogenic ClinVar missense variants for a disease protein, each with
    the residues it maps to in every panel structure that holds the protein
    (``variant["structures"][entry]``; only residues whose identity matches the wild
    type are listed). None if the accession is not a panel disease protein."""
    path = PANEL / "variants" / f"{accession}.json"
    return json.loads(path.read_text()) if path.exists() else None


def structure_file(entry: str) -> pathlib.Path | None:
    """The panel's frozen mmCIF (gzip) for an entry, or None."""
    path = PANEL / "cif" / f"{entry.lower()}.cif.gz"
    return path if path.exists() else None



class Residue(NamedTuple):
    auth_asym_id: str
    auth_seq_id: int
    comp_id: str


def fetch_structure(pdb: str, allow_network: bool = True):
    """Parse an entry's mmCIF into a gemmi Structure (entities set up): the panel's
    frozen file if there is one, otherwise a download (unless ``allow_network`` is false)."""
    import gemmi
    frozen = structure_file(pdb)
    if frozen is not None:
        block = gemmi.cif.read(str(frozen)).sole_block()
    elif allow_network:
        data = urllib.request.urlopen(CIF.format(pdb.lower()), timeout=30).read().decode()
        block = gemmi.cif.read_string(data).sole_block()
    else:
        raise LookupError(f"{pdb!r} is not in the frozen panel and the network is not allowed")
    st = gemmi.make_structure_from_block(block)
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
