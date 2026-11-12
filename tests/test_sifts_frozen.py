"""
Frozen SIFTS tables: grading-time UniProt lookups never touch the network, and the
tables agree with the frozen atom tables and with residue numbers known from the
literature.

Stdlib + pytest only (no gemmi, no network).
"""

from __future__ import annotations

import ast
import json
import pathlib
import socket
import urllib.request

import pytest

from molbench import sifts
from molbench.atoms import load_table

REPO = pathlib.Path(__file__).resolve().parent.parent
PANEL = json.loads((REPO / "data" / "panel" / "panel.json").read_text())
MAPPED = [e["id"] for e in PANEL["entries"] if e["sifts"]]
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
       "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
       "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}


class NetworkUsed(AssertionError):
    pass


@pytest.fixture
def no_network(monkeypatch):
    """Any attempt to open a connection fails the test."""
    calls = []

    def refuse(*args, **kwargs):
        calls.append(args)
        raise NetworkUsed(f"network access attempted: {args[:1]}")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    return calls


# --- the offline guarantee ---------------------------------------------------------

def test_lookups_for_every_panel_entry_are_offline(no_network):
    sifts.load.cache_clear()
    load_table.cache_clear()
    for entry in MAPPED:
        table = sifts.load(entry)
        assert table is not None and table.rows, entry
        maps = sifts.mappings(entry)
        acc = next(iter(maps))
        first = next(r for r in table.rows if r.accession == acc and r.observed)
        assert sifts.uniprot_residues(entry, acc, first.unp_num)
        assert sifts.uniprot_atoms(entry, acc, first.unp_num), entry
    assert no_network == []


def test_an_entry_without_a_table_raises_instead_of_fetching(no_network):
    with pytest.raises(sifts.NetworkNotAllowed):
        sifts.mappings("9zzz")
    assert sifts.load("9zzz") is None
    assert sifts.uniprot_residues("9zzz", "P04637", 175) is None
    assert sifts.uniprot_atoms("9zzz", "P04637", 175) is None
    assert no_network == []          # nothing above even tried
    with pytest.raises(NetworkUsed):  # the one network path, and only when asked for
        sifts.mappings("9zzz", allow_network=True)
    assert len(no_network) == 1


def test_grading_a_clinical_task_is_offline(no_network):
    from molbench.mvs import grade_mvs
    paths = sorted((REPO / "tasks" / "mvs_clinical").glob("*.json"))
    assert paths
    for path in paths:
        task = json.loads(path.read_text())
        result = grade_mvs(task["reference_mvs"], task["reference_mvs"])
        assert result is not None
    assert no_network == []


def test_sifts_module_only_imports_the_network_inside_the_opt_in_function():
    tree = ast.parse((REPO / "molbench" / "sifts.py").read_text())
    for node in tree.body:  # module level
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
            assert not any(n.split(".")[0] in ("urllib", "http", "socket", "requests")
                           for n in names), ast.dump(node)
    users = [f.name for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)
             and "urllib" in ast.dump(f)]
    assert users == ["_fetch_mappings"]


# --- the tables agree with the atom tables -----------------------------------------

@pytest.mark.parametrize("entry", MAPPED)
def test_every_observed_row_names_a_real_residue(entry):
    table, atoms = sifts.load(entry), load_table(entry)
    assert atoms is not None, f"{entry}: no atom table"
    c = atoms.columns
    same = total = 0
    for r in table.rows:
        if not r.observed:
            continue
        mask = atoms.expression({"label_asym_id": r.label_asym_id, "label_seq_id": r.label_seq_id,
                                 "pdbx_PDB_ins_code": r.pdbx_PDB_ins_code,
                                 "label_comp_id": r.comp_id})
        assert mask, (entry, r)
        i = (mask & -mask).bit_length() - 1
        assert (c["auth_asym_id"][i], c["auth_seq_id"][i]) == (r.auth_asym_id, r.auth_seq_id)
        total += 1
        same += AA3.get(r.comp_id) == r.unp_res
    # The structure's residues are the UniProt residues, bar mutations and modifications.
    assert total and same / total > 0.9, (entry, same, total)


def test_a_range_is_the_union_of_its_positions():
    one = [sifts.uniprot_atoms("2hhb", "P68871", n) for n in range(5, 9)]
    both = sifts.uniprot_atoms("2hhb", "P68871", 5, 8)
    assert all(one) and both
    union = 0
    for m in one:
        union |= m
    assert both == union
    assert sifts.uniprot_atoms("2hhb", "P68871", 9999) == 0
    assert sifts.uniprot_atoms("2hhb", "P00000", 7) == 0


def test_numbers_from_a_model_cannot_crash_or_stall_the_lookup():
    # The numbers may be a model's output. A huge range costs nothing extra, and a
    # non-number selects nothing (the PDBe viewer compares with ===).
    whole = sifts.uniprot_atoms("1tup", "P04637", 1, 10 ** 15)
    assert whole == sifts.uniprot_atoms("1tup", "P04637", 1, 393)
    one = sifts.uniprot_atoms("1tup", "P04637", 175)
    assert one and sifts.uniprot_atoms("1tup", "P04637", 175.0) == one
    for bad in ("175", None, True, 175.5, float("nan")):
        assert sifts.uniprot_atoms("1tup", "P04637", bad) == 0, bad
    assert sifts.uniprot_atoms("1tup", "P04637", 180, 170) == 0
    assert sifts.uniprot_atoms("1TUP", "P04637", 175) == one   # ids are case-insensitive


# --- residue numbers known from the literature -------------------------------------
# (entry, accession, UniProt number) -> (author chains, author number, residue). Each is a
# textbook residue whose two numberings are both published, so none of this comes from
# the builder: sickle-cell Glu6 (p.Glu7), TTR Val30 (p.Val50), SOD1 Ala4 (p.Ala5),
# alpha-1-antitrypsin Glu342 (p.Glu366, the Z allele), lysozyme Ile56 (p.Ile74),
# trypsin's Ser195/His57/Asp102 (UniProt 200/63/107), insulin B-chain Phe1 and A-chain
# Gly1 (pre-proinsulin 25 and 90), calmodulin Asn97 (p.Asn98), p53 Arg175/248/273.
KNOWN = [
    ("2hhb", "P68871", 7, ["B", "D"], 6, "GLU"),
    ("1hho", "P68871", 7, ["B"], 6, "GLU"),
    ("af-p68871-f1-model_v6", "P68871", 7, ["A"], 7, "GLU"),
    ("2hhb", "P69905", 59, ["A", "C"], 58, "HIS"),
    ("1tup", "P04637", 175, ["A", "B", "C"], 175, "ARG"),
    ("1tup", "P04637", 248, ["A", "B", "C"], 248, "ARG"),
    ("1tup", "P04637", 273, ["A", "B", "C"], 273, "ARG"),
    ("3ptb", "P00760", 200, ["A"], 195, "SER"),
    ("3ptb", "P00760", 63, ["A"], 57, "HIS"),
    ("3ptb", "P00760", 107, ["A"], 102, "ASP"),
    ("8c86", "P02766", 50, ["A", "B"], 30, "VAL"),
    ("2c9v", "P00441", 5, ["A", "F"], 4, "ALA"),
    ("8pi2", "P01009", 366, ["A"], 342, "GLU"),
    ("2nwd", "P61626", 74, ["X"], 56, "ILE"),
    ("6tc2", "P01308", 25, None, 1, "PHE"),
    ("6tc2", "P01308", 90, None, 1, "GLY"),
    ("6m7h", "P0DP23", 98, ["A"], 97, "ASN"),
]


@pytest.mark.parametrize("entry,acc,unp,chains,auth,comp", KNOWN)
def test_known_residues(entry, acc, unp, chains, auth, comp):
    hits = sifts.uniprot_residues(entry, acc, unp)
    assert hits, (entry, acc, unp)
    assert {(r.auth_seq_id, r.comp_id) for r in hits} == {(auth, comp)}
    if chains is not None:
        assert sorted(r.auth_asym_id for r in hits) == chains
    # ... and the atoms are that residue's atoms in the atom table.
    atoms = load_table(entry)
    mask = sifts.uniprot_atoms(entry, acc, unp)
    want = 0
    for r in hits:
        want |= atoms.expression({"auth_asym_id": r.auth_asym_id, "auth_seq_id": auth,
                                  "auth_comp_id": comp})
    assert mask == want and mask.bit_count() >= len(hits) * 4


def test_author_chain_can_differ_from_label_chain():
    hits = sifts.uniprot_residues("1tup", "P04637", 175)
    assert sorted((r.auth_asym_id, r.label_asym_id) for r in hits) == [
        ("A", "C"), ("B", "D"), ("C", "E")]
    assert {r.label_seq_id for r in hits} == {82}  # label numbering restarts at 1


def test_segment_interface_matches_the_old_shape():
    maps = sifts.mappings("2hhb")
    assert {s["offset"] for s in maps["P68871"]["segments"]} == {-1}
    assert maps["P68871"]["name"] == "HBB_HUMAN"
    assert sorted(sifts.unp_to_auth(maps, "P68871", 7)) == [("B", 6), ("D", 6)]
    assert sorted(sifts.unp_to_auth(sifts.mappings("1tup"), "P04637", 175)) == [
        ("A", 175), ("B", 175), ("C", 175)]
    # Chymotrypsinogen numbering: the offset changes along the chain, so several segments.
    assert len({s["offset"] for s in sifts.mappings("3ptb")["P00760"]["segments"]}) > 1
    assert sifts.unp_to_auth(sifts.mappings("3ptb"), "P00760", 200) == [("A", 195)]


def test_insertion_codes_are_kept():
    rows = [r for r in sifts.load("3ptb").rows if r.pdbx_PDB_ins_code]
    assert rows and all(r.observed for r in rows)
    r = rows[0]
    got = sifts.uniprot_residues("3ptb", r.accession, r.unp_num)
    assert [(x.auth_seq_id, x.pdbx_PDB_ins_code) for x in got] == [
        (r.auth_seq_id, r.pdbx_PDB_ins_code)]
    # One UniProt position, one residue: the insertion-coded neighbour is not swept in.
    atoms = load_table("3ptb")
    mask = sifts.uniprot_atoms("3ptb", r.accession, r.unp_num)
    assert mask == atoms.expression({"auth_asym_id": r.auth_asym_id, "auth_seq_id": r.auth_seq_id,
                                     "pdbx_PDB_ins_code": r.pdbx_PDB_ins_code})


def test_alphafold_models_are_numbered_as_uniprot():
    ids = [e["id"] for e in PANEL["entries"] if e["kind"] == "alphafold"]
    assert ids
    for entry in ids:
        table = sifts.load(entry)
        assert table.rows and all(
            r.observed and r.unp_num == r.auth_seq_id == r.label_seq_id for r in table.rows)
        assert [e for e in PANEL["entries"] if e["id"] == entry][0]["offset"] is False


def test_unobserved_residues_are_listed_but_select_nothing():
    table = sifts.load("5uak")   # CFTR: long disordered regions
    missing = [r for r in table.rows if not r.observed]
    assert missing
    r = missing[0]
    assert sifts.uniprot_residues("5uak", r.accession, r.unp_num) == []
    assert table.residues(r.accession, r.unp_num, observed_only=False) == [r]
    assert sifts.uniprot_atoms("5uak", r.accession, r.unp_num) == 0
