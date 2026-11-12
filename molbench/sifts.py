"""
SIFTS bridge — UniProt residue numbers <-> structure residues, from frozen tables.

Literature, ClinVar and UniProt number residues in the canonical UniProt frame; a
structure has its own *author* numbering (``auth_asym_id`` / ``auth_seq_id``) and
its *label* numbering (``label_asym_id`` / ``label_seq_id``), and all three can
differ. SIFTS is the residue-level mapping between them.

Grading never touches the network. ``scripts/build_panel.py`` freezes one table per
structure into ``molbench/sifts_tables/<id>.json.gz``, taken from the
``_atom_site.pdbx_sifts_xref_db_*`` columns of PDBe's "updated" mmCIF — the columns
Mol*'s SIFTS mapping reads, and so what the PDBe viewer's ``uniprot_accession``
selections resolve against. Everything here reads those tables. The one network
path, :func:`mappings` with ``allow_network=True``, is for authoring against an
entry outside the panel and must be asked for explicitly.

A table row is one residue of one chain mapped to one UniProt position:

    accession, unp_num, unp_res      UniProt accession, residue number, one-letter code
    label_asym_id, label_seq_id      label chain and residue number (SEQRES index)
    auth_asym_id, auth_seq_id,       author chain, residue number and insertion code
      pdbx_PDB_ins_code
    comp_id                          the residue actually in the structure (three-letter)
    observed                         False if the residue is in the construct but not modelled

For graders: :func:`uniprot_atoms` ``(entry, accession, uniprot_resnum) -> atoms``,
as a bitmask over the rows of the entry's frozen atom table (``molbench.atoms``).
"""

from __future__ import annotations

import bisect
import functools
import gzip
import json
import pathlib
from typing import NamedTuple

TABLES = pathlib.Path(__file__).resolve().parent / "sifts_tables"  # shipped in the wheel

PDBE = "https://www.ebi.ac.uk/pdbe/api/mappings/{}"


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


class NetworkNotAllowed(LookupError):
    """No frozen table for the entry, and the caller did not allow a network lookup."""


class Residue(NamedTuple):
    accession: str
    unp_num: int
    unp_res: str
    label_asym_id: str
    label_seq_id: int
    comp_id: str
    auth_asym_id: str | None
    auth_seq_id: int | None
    pdbx_PDB_ins_code: str
    observed: bool


class SiftsTable:
    """One structure's frozen per-residue UniProt mapping."""

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.source: str = data.get("source", "")
        self.retrieved: str = data.get("retrieved", "")
        self.source_sha256: str = data.get("source_sha256", "")
        self.accessions: dict[str, dict] = data.get("accessions", {})
        c = data["columns"]
        self.rows: list[Residue] = [
            Residue(*(c[f][i] for f in Residue._fields[:-1]), bool(c["observed"][i]))
            for i in range(len(c["accession"]))]
        self._by_pos: dict[tuple[str, int], list[Residue]] = {}
        for r in self.rows:
            self._by_pos.setdefault((r.accession, r.unp_num), []).append(r)
        self._positions: dict[str, list[int]] = {}
        for acc, n in sorted(self._by_pos):
            self._positions.setdefault(acc, []).append(n)

    def residues(self, accession: str, unp_num: int, end: int | None = None,
                 observed_only: bool = True) -> list[Residue]:
        """Residues mapped to a UniProt position, or to the range ``unp_num..end``
        (in position order). The numbers may come straight from a model's output:
        anything that is not a number selects nothing, and the cost does not grow
        with the width of the range."""
        hi = unp_num if end is None else end
        if not (_is_number(unp_num) and _is_number(hi)):
            return []
        mapped = self._positions.get(accession, [])
        out: list[Residue] = []
        for n in mapped[bisect.bisect_left(mapped, unp_num):bisect.bisect_right(mapped, hi)]:
            out += [r for r in self._by_pos[(accession, n)]
                    if r.observed or not observed_only]
        return out

    def segments(self, accession: str) -> list[dict]:
        """Observed residues as runs of constant author-minus-UniProt offset:
        ``[{chain, unp_start, unp_end, offset}]`` (``chain`` is the author chain).
        Residues with an insertion code have no integer author number of their own
        and are left out; use :meth:`residues` for those."""
        segs: list[dict] = []
        last: dict[str, dict] = {}
        for r in self.rows:
            if r.accession != accession or not r.observed or r.pdbx_PDB_ins_code:
                continue
            off = r.auth_seq_id - r.unp_num
            s = last.get(r.label_asym_id)
            if s and s["offset"] == off and r.unp_num == s["unp_end"] + 1:
                s["unp_end"] = r.unp_num
            else:
                s = {"chain": r.auth_asym_id, "unp_start": r.unp_num, "unp_end": r.unp_num,
                     "offset": off}
                last[r.label_asym_id] = s
                segs.append(s)
        return segs


@functools.lru_cache(maxsize=None)
def load(entry: str | None) -> SiftsTable | None:
    """The frozen table for a structure id (e.g. '1tup'), or None if there isn't one."""
    if not entry:
        return None
    path = TABLES / f"{entry.lower()}.json.gz"
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return SiftsTable(json.load(f))


def uniprot_residues(entry: str, accession: str, unp_num: int,
                     end: int | None = None) -> list[Residue] | None:
    """Observed residues of ``entry`` at a UniProt position (or range); None if the
    entry has no frozen table. Never uses the network."""
    table = load(entry)
    return None if table is None else table.residues(accession, unp_num, end)


def uniprot_atoms(entry: str, accession: str, unp_num: int, end: int | None = None) -> int | None:
    """Atoms of ``entry`` at a UniProt position (or the range ``unp_num..end``), as a
    bitmask over the entry's frozen atom table — the same kind of set
    ``AtomTable.selector`` returns. None if the entry lacks either frozen table; 0 if
    nothing maps there. Never uses the network.

    This is what the PDBe viewer selects for ``{uniprot_accession, uniprot_residue_number}``
    (or ``start_``/``end_uniprot_residue_number``): every atom of each residue whose
    SIFTS accession and number match, in every chain.
    """
    from .atoms import load_table
    table, atoms = load(entry), load_table(entry)
    if table is None or atoms is None:
        return None
    out = 0
    for r in table.residues(accession, unp_num, end):
        out |= atoms.expression({
            "label_asym_id": r.label_asym_id, "label_seq_id": r.label_seq_id,
            "auth_seq_id": r.auth_seq_id, "pdbx_PDB_ins_code": r.pdbx_PDB_ins_code,
            "label_comp_id": r.comp_id}) or 0
    return out


# --- the older segment interface (task generators) ---------------------------------

def mappings(pdb: str, allow_network: bool = False) -> dict:
    """{accession: {'name': str, 'segments': [{chain, unp_start, unp_end, offset}]}}.

    ``offset = author_residue_number - unp_residue_number``, so ``auth = unp + offset``
    inside a segment. Read from the frozen table. Only if there is none **and**
    ``allow_network`` is true is the PDBe mappings API asked instead (authoring against
    an entry outside the panel); otherwise :class:`NetworkNotAllowed` is raised.
    """
    pdb = pdb.lower()
    table = load(pdb)
    if table is not None:
        return {acc: {"name": info.get("entry_name"), "segments": table.segments(acc)}
                for acc, info in table.accessions.items()}
    if not allow_network:
        raise NetworkNotAllowed(
            f"no frozen SIFTS table for {pdb!r} in {TABLES.name}/; add the entry to the panel "
            f"(scripts/build_panel.py) or pass allow_network=True when authoring")
    return _fetch_mappings(pdb)


def _fetch_mappings(pdb: str) -> dict:
    """Segment-level mapping from the PDBe API (covers unobserved residues too)."""
    import urllib.request
    data = json.load(urllib.request.urlopen(PDBE.format(pdb), timeout=30))
    out: dict[str, dict] = {}
    for acc, info in data[pdb]["UniProt"].items():
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
