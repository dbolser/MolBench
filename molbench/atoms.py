"""
Frozen atom tables, and MVS selections resolved to the atoms they pick.

The MVS grader used to compare selectors as strings, so two namings of the same
atoms ("every CYS" vs the twelve cysteines listed one by one) scored as different,
and a selection that matched nothing could still score. Here a selector is resolved
against a per-structure atom table and graded by the atom set it selects.

Grading stays stdlib-only and offline: ``scripts/build_atom_tables.py`` (gemmi +
headless Mol*) freezes one table per structure a task references into
``molbench/atom_tables/<id>.json.gz``. A structure with no table returns ``None`` here and
the grader falls back to string signatures. Nothing is fetched at grade time.

Selection semantics follow Mol* 5.9.0, which renders the scenes:

* An expression is ``StructureElement.Schema.toExpression``
  (``mol-model/structure/structure/element/schema.js``): its fields are AND-ed, and
  a list of expressions is their union (an empty list selects nothing).
* Fields are compared exactly: ``label_comp_id`` is case-sensitive, ``type_symbol``
  is upper-cased first. ``label_seq_id`` of a non-polymer residue ('.' in the file)
  reads as 0, so ``end_label_seq_id`` ranges also catch waters and ligands.
  ``beg_label_seq_id``/``end_label_seq_id`` use ``ihm.overlapsSeqIdRange``, the auth
  ranges plain ``>=``/``<=``.
* Unknown keys are ignored (the MVS schema is an io-ts ``partial``, so they pass
  validation and add no test). A value of the wrong type (``"64"`` for an int)
  fails Mol*'s tree validation and nothing is drawn, so it selects nothing here.
* Static selectors (``polymer``, ``ligand``, ...) are Mol*'s own queries
  (``mol-plugin-state/helpers/structure-selection-query.js``; ``ligand`` includes
  covalently/metal-bonded neighbours). They depend on entity types and bonds, so
  the builder records Mol*'s answer for each instead of re-implementing them.

Sets are int bitmasks over the table's rows (model 1 of the asymmetric unit, in
file order). Each row's identity (auth chain, auth seq, ins code, comp, atom name,
alt id) is unique, so a set means the same atoms however the selector named them.
"""

from __future__ import annotations

import functools
import gzip
import json
import pathlib
from typing import Any

TABLES = pathlib.Path(__file__).resolve().parent / "atom_tables"  # shipped in the wheel

# The MVS ComponentExpression fields, by type (``extensions/mvs/tree/mvs/param-types.js``).
_STR_FIELDS = ("label_entity_id", "label_asym_id", "auth_asym_id", "pdbx_PDB_ins_code",
               "label_comp_id", "auth_comp_id", "label_atom_id", "auth_atom_id", "type_symbol")
_INT_FIELDS = ("label_seq_id", "auth_seq_id", "beg_label_seq_id", "end_label_seq_id",
               "beg_auth_seq_id", "end_auth_seq_id", "residue_index", "atom_id", "atom_index")
# Fields whose meaning depends on symmetry instances, which a model-1 table can't answer.
_UNSUPPORTED = ("instance_id", "operator_name")
# Exact-match fields -> table column.
_EQ_COLUMNS = {f: f for f in ("label_entity_id", "label_asym_id", "auth_asym_id", "label_seq_id",
                              "auth_seq_id", "pdbx_PDB_ins_code", "label_comp_id", "auth_comp_id",
                              "label_atom_id", "auth_atom_id", "residue_index", "atom_id")}
_RANGES = (("beg_label_seq_id", "end_label_seq_id", "label_seq_id"),
           ("beg_auth_seq_id", "end_auth_seq_id", "auth_seq_id"))

STATIC_SELECTORS = ("all", "polymer", "protein", "nucleic", "branched", "ligand", "ion",
                    "water", "coarse")


def _mask(indices, n: int) -> int:
    bits = bytearray((n + 7) // 8)
    for i in indices:
        bits[i >> 3] |= 1 << (i & 7)
    return int.from_bytes(bits, "little")


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) or isinstance(v, float) and v.is_integer()


class AtomTable:
    """One structure's atoms (model 1, asymmetric unit) and Mol*'s static selections."""

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.columns: dict[str, list] = data["columns"]
        self.n: int = len(self.columns["auth_atom_id"])
        self.static: dict[str, int] = {}
        for name, ranges in data["static"].items():
            m = 0
            for a, b in ranges:
                m |= ((1 << (b - a)) - 1) << a
            self.static[name] = m
        self._index: dict[str, dict[Any, int]] = {}

    def index(self, column: str) -> dict[Any, int]:
        """value -> mask of the rows holding it."""
        if column not in self._index:
            rows: dict[Any, list[int]] = {}
            for i, v in enumerate(self.columns[column]):
                rows.setdefault(v, []).append(i)
            self._index[column] = {v: _mask(r, self.n) for v, r in rows.items()}
        return self._index[column]

    def identity(self, row: int) -> tuple:
        c = self.columns
        return (c["auth_asym_id"][row], c["auth_seq_id"][row], c["pdbx_PDB_ins_code"][row],
                c["auth_comp_id"][row], c["auth_atom_id"][row], c["label_alt_id"][row])

    def expression(self, e: Any) -> int | None:
        """Atoms matched by one ComponentExpression, or None if it can't be resolved here."""
        if not isinstance(e, dict):
            return 0  # not an expression: fails Mol*'s validation
        if any(e.get(f) is not None for f in _UNSUPPORTED):
            return None
        for f, v in e.items():
            if f in _STR_FIELDS and not isinstance(v, str) or f in _INT_FIELDS and not _is_int(v):
                return 0  # wrong type (incl. null): Mol* rejects the tree, nothing is drawn
        sel = (1 << self.n) - 1
        for f, column in _EQ_COLUMNS.items():
            if f in e:
                v = int(e[f]) if f in _INT_FIELDS else e[f]
                sel &= self.index(column).get(v, 0)
        if "atom_index" in e:  # the row in the source file; model 1 comes first
            i = int(e["atom_index"])
            sel &= (1 << i) if 0 <= i < self.n else 0
        if "type_symbol" in e:
            sel &= self.index("type_symbol").get(e["type_symbol"].upper(), 0)
        for beg_f, end_f, column in _RANGES:
            if beg_f in e or end_f in e:
                lo = e.get(beg_f, float("-inf"))
                hi = e.get(end_f, float("inf"))
                in_range = 0
                for v, m in self.index(column).items():
                    if lo <= v <= hi:
                        in_range |= m
                sel &= in_range
        return sel

    def selector(self, sel: Any) -> int | None:
        """Atoms matched by an MVS selector: a static name, an expression, or a list (union)."""
        if isinstance(sel, str):
            return self.static.get(sel, 0)  # an unknown name fails validation
        out = 0
        for e in (sel if isinstance(sel, list) else [sel]):
            m = self.expression(e)
            if m is None:
                return None
            out |= m
        return out


@functools.lru_cache(maxsize=None)
def load_table(structure_id: str | None) -> AtomTable | None:
    """The frozen table for a structure id (e.g. '1tup'), or None if there isn't one."""
    if not structure_id:
        return None
    path = TABLES / f"{structure_id.lower()}.json.gz"
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return AtomTable(json.load(f))
