"""
The structure panel (``data/panel/``): every entry has its frozen files, the panel
covers what the benchmark plan asks for, and the frozen facts and clinical variants
agree with the atom tables.

Stdlib + pytest only (no gemmi, no network): everything is read from frozen files.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import pathlib
import re

import pytest

from molbench import grounding, sifts
from molbench.atoms import load_table
from molbench.mvs import _param_signature

REPO = pathlib.Path(__file__).resolve().parent.parent
PANEL_DIR = REPO / "data" / "panel"
PANEL = json.loads((PANEL_DIR / "panel.json").read_text())
ENTRIES = {e["id"]: e for e in PANEL["entries"]}
PROTEINS = PANEL["disease_proteins"]
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
       "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
       "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}


def _where(atoms, r: dict) -> int:
    return atoms.expression({"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["auth_seq_id"],
                             "pdbx_PDB_ins_code": r["pdbx_PDB_ins_code"],
                             "label_asym_id": r["label_asym_id"]})


def _comps(atoms, mask: int) -> set[str]:
    col = atoms.columns["label_comp_id"]
    return {col[i] for i in range(atoms.n) if mask >> i & 1}


# --- every entry has its frozen files ----------------------------------------------

def test_panel_size():
    pdb = [e for e in ENTRIES.values() if e["kind"] == "pdb"]
    assert len(pdb) >= 55
    assert 1 <= sum(e["kind"] == "alphafold" for e in ENTRIES.values()) <= 2
    assert len(ENTRIES) == len(PANEL["entries"])  # ids are unique


@pytest.mark.parametrize("entry", sorted(ENTRIES))
def test_entry_has_atom_table_facts_structure_file_and_sifts(entry):
    rec = ENTRIES[entry]
    atoms = load_table(entry)
    assert atoms is not None, "run scripts/build_atom_tables.py --panel"
    assert atoms.n == rec["atoms"]
    facts = grounding.facts(entry)
    assert facts and facts["n_atoms"] == atoms.n
    frozen = grounding.structure_file(entry)
    assert frozen is not None
    assert hashlib.sha256(gzip.decompress(frozen.read_bytes())).hexdigest() == rec["sha256"]
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", rec["retrieved"]) and rec["source"].startswith("https://")
    assert rec["why"] and rec["families"] and "basic" in rec["families"]
    # A SIFTS table wherever a UniProt mapping exists (and the panel says which).
    table = sifts.load(entry)
    assert (table is not None) == rec["sifts"]
    if table is None:
        # No mapping: nucleic acid only, or a designed peptide.
        assert all(c["polymer_type"] != "protein" or c["seqres_length"] <= 30
                   for c in facts["chains"]), entry
    else:
        # 'uniprot' lists the accessions with modelled residues (a cleaved tag may map too).
        assert sorted({r.accession for r in table.rows if r.observed}) == rec["uniprot"]
        assert set(rec["uniprot"]) <= set(table.accessions)


def test_every_structure_a_task_uses_is_in_the_panel():
    used: set[str] = set()

    def walk(x):
        if isinstance(x, dict):
            if x.get("kind") == "download" and isinstance(x.get("params"), dict):
                sig = _param_signature("download", x["params"])
                if sig and sig[0] == "ref":
                    used.add(sig[1])
            if isinstance(x.get("molecule_id"), str):
                mid = x["molecule_id"].lower()
                used.add(f"af-{mid}" if x.get("alphafold") else mid)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    for path in (REPO / "tasks").rglob("*.json"):
        task = json.loads(path.read_text())
        walk({k: v for k, v in task.items() if k != "grounding"})
    assert used
    for sid in sorted(used):
        if sid.startswith("af-"):  # loaded by accession: any frozen version of that model
            assert any(e.startswith(sid + "-") for e in ENTRIES), sid
        else:
            assert sid in ENTRIES, sid


def test_size_limit():
    for e in ENTRIES.values():
        if e["atoms"] > PANEL["max_atoms"]:
            assert e["over_size_limit"] and e["used_by_tasks"], e["id"]
    over = [e["id"] for e in ENTRIES.values() if e["over_size_limit"]]
    assert len(over) <= 2, over


# --- coverage the plan asks for ----------------------------------------------------

@pytest.mark.parametrize("feature,at_least", [
    ("ligand", 15), ("heme", 5), ("metal", 15), ("disulfide", 12), ("nucleic", 6),
    ("protein-dna", 4), ("assembly-differs", 8), ("glycan", 6), ("membrane", 6),
    ("insertion-codes", 4), ("auth-label-number", 10), ("auth-label-chain", 6),
    ("uniprot-offset", 20), ("cryo-em", 4), ("nmr", 2), ("alphafold", 1),
    ("modified-residue", 4), ("clinical", 20),
])
def test_feature_coverage(feature, at_least):
    have = [e["id"] for e in ENTRIES.values() if feature in e["features"]]
    assert len(have) >= at_least, (feature, have)


def test_fold_and_size_spread():
    sizes = sorted(e["atoms"] for e in ENTRIES.values())
    assert sizes[0] < 500 and sizes[len(sizes) // 2] < 5000 and sizes[-1] > 10000
    methods = {e["method"] for e in ENTRIES.values()}
    assert {"X-ray", "EM", "NMR"} <= methods
    xray = [e for e in ENTRIES.values() if e["method"] == "X-ray"]
    assert sum(e["resolution"] <= 2.5 for e in xray) / len(xray) > 0.8


def test_disease_proteins_and_numbering_offsets():
    good = [p for p in PROTEINS if p["verified_on_entry"] >= 3]
    assert len(good) >= 12
    assert sum(p["offset"] for p in good) >= 8
    assert sum(p["auth_chain_differs_from_label_chain"] for p in good) >= 3
    assert sum(p["verified_on_entry"] for p in good) >= 40
    for p in PROTEINS:
        assert p["entry"] in ENTRIES and p["accession"] in ENTRIES[p["entry"]]["uniprot"]


@pytest.mark.parametrize("protein", PROTEINS, ids=lambda p: p["gene"])
def test_offset_flag_is_what_the_sifts_table_says(protein):
    table = sifts.load(protein["entry"])
    rows = [r for r in table.rows if r.accession == protein["accession"] and r.observed]
    assert rows
    differs = any(r.auth_seq_id != r.unp_num or r.pdbx_PDB_ins_code for r in rows)
    assert differs == protein["offset"]
    assert any(r.auth_asym_id != r.label_asym_id for r in rows) == \
        protein["auth_chain_differs_from_label_chain"]


# --- clinical variants -------------------------------------------------------------

@pytest.mark.parametrize("protein", PROTEINS, ids=lambda p: p["gene"])
def test_variants_are_frozen_with_provenance_and_verified_identity(protein):
    doc = grounding.variants(protein["accession"])
    assert doc["accession"] == protein["accession"]
    assert doc["source"].startswith("https://www.ebi.ac.uk/proteins/api/variation/")
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", doc["retrieved"])
    assert doc["primary_entry"] == protein["entry"]
    assert len(doc["variants"]) == protein["variants"] > 0
    seen = set()
    n_verified = 0
    for v in doc["variants"]:
        assert v["variant"] == f"{v['wild_type']}{v['position']}{v['mutant']}"
        assert v["variant"] not in seen
        seen.add(v["variant"])
        assert v["wild_type"] != v["mutant"]
        assert set(v["significance"]) <= {"Pathogenic", "Likely pathogenic"} and v["significance"]
        assert v["clinvar"] and all(re.fullmatch(r"[RV]CV\d+", x) for x in v["clinvar"])
        n_verified += protein["entry"] in v["structures"]
        for entry, residues in v["structures"].items():
            atoms = load_table(entry)
            assert residues
            # Independent of the SIFTS join: the atom table itself has the wild-type
            # residue at the author position the variant was mapped to.
            everything = sifts.uniprot_atoms(entry, protein["accession"], v["position"])
            for r in residues:
                mask = _where(atoms, r)
                assert mask and mask & everything == mask, (v["variant"], entry, r)
                comps = _comps(atoms, mask)
                assert {AA3.get(c) for c in comps} == {v["wild_type"]}, (v["variant"], entry, r)
    assert n_verified == protein["verified_on_entry"]
    # Mismatches are recorded, and a mismatched residue is never offered as an answer.
    for m in doc["structure_mismatches"]:
        v = next(x for x in doc["variants"] if x["variant"] == m["variant"])
        assert AA3.get(m["structure_residue"]) != v["wild_type"]
        assert not any((r["auth_asym_id"], r["auth_seq_id"]) == (m["auth_asym_id"], m["auth_seq_id"])
                       for r in v["structures"].get(m["entry"], []))


def test_a_wild_type_mismatch_is_actually_caught():
    # The panel must contain at least one real mismatch, or the exclusion is untested.
    n = sum(len(grounding.variants(p["accession"])["structure_mismatches"]) for p in PROTEINS)
    assert n > 0


def test_known_variants():
    hbb = {v["variant"]: v for v in grounding.variants("P68871")["variants"]}
    sickle = hbb["E7V"]                      # sickle cell: Glu6 in the mature chain
    assert "Pathogenic" in sickle["significance"]
    assert [(r["auth_asym_id"], r["auth_seq_id"]) for r in sickle["structures"]["2hhb"]] == [
        ("B", 6), ("D", 6)]
    assert [r["auth_seq_id"] for r in sickle["structures"]["af-p68871-f1-model_v6"]] == [7]
    p53 = {v["variant"]: v for v in grounding.variants("P04637")["variants"]}
    for name, pos in (("R175H", 175), ("R248Q", 248), ("R273H", 273)):
        assert [(r["auth_asym_id"], r["label_asym_id"], r["auth_seq_id"])
                for r in p53[name]["structures"]["1tup"]] == [
                    ("A", "C", pos), ("B", "D", pos), ("C", "E", pos)]
    ttr = {v["variant"]: v for v in grounding.variants("P02766")["variants"]}
    assert {r["auth_seq_id"] for r in ttr["V50M"]["structures"]["8c86"]} == {30}  # "V30M"


# --- grounding facts agree with the atom tables ------------------------------------

@pytest.mark.parametrize("entry", sorted(ENTRIES))
def test_facts_agree_with_the_atom_table(entry):
    facts, atoms = grounding.facts(entry), load_table(entry)
    c = atoms.columns
    chains = {(c["auth_asym_id"][i], c["label_asym_id"][i]) for i in range(atoms.n)}
    for ch in facts["chains"]:
        assert (ch["auth_asym_id"], ch["label_asym_id"]) in chains
        mask = atoms.expression({"label_asym_id": ch["label_asym_id"]})
        assert mask and mask & atoms.static["polymer"] == mask
    polymer = 0
    for ch in facts["chains"]:
        polymer |= atoms.expression({"label_asym_id": ch["label_asym_id"]})
    assert polymer == atoms.static["polymer"]       # Mol*'s own answer
    for lig in facts["ligands"]:
        for copy in lig["copies"]:
            mask = _where(atoms, copy)
            assert mask and _comps(atoms, mask) == {lig["comp_id"]}
            assert not mask & atoms.static["polymer"]
    for bond in facts["disulfides"]:
        for end in (bond["a"], bond["b"]):
            mask = _where(atoms, end)
            assert mask and _comps(atoms, mask) <= {"CYS", "DCY", "CSO"}, (entry, end)
    # Mol*'s 'branched' selector is wider than the branched entities: it also takes
    # single-sugar ligands and the residue each sugar is bonded to.
    branched = 0
    for g in facts["glycans"]:
        branched |= atoms.expression({"label_asym_id": g["label_asym_id"]})
    assert branched & atoms.static["branched"] == branched
    for lig in facts["ligands"]:
        if lig["kind"] == "sugar":
            for copy in lig["copies"]:
                branched |= _where(atoms, copy)
    for site in facts["glycosylation_sites"]:
        branched |= _where(atoms, site["residue"])
    assert branched == atoms.static["branched"]     # Mol*'s own answer
    waters = atoms.static["water"].bit_count()
    assert waters >= facts["waters"]                # one water residue may hold alt atoms/H
    assert (facts["waters"] == 0) == (waters == 0)
    assert facts["numbering"]["auth_number_differs_from_uniprot"] == ENTRIES[entry]["offset"]


def test_known_facts():
    f = grounding.facts("3ptb")
    assert [l["comp_id"] for l in f["ligands"]] == ["BEN", "CA"]
    assert len(f["disulfides"]) == 6 and f["numbering"]["insertion_codes"]
    f = grounding.facts("4ins")
    assert len(f["disulfides"]) == 6
    assert f["assemblies"][0]["relation_to_deposited"] != "same as deposited"
    f = grounding.facts("2hhb")
    assert sum(len(l["copies"]) for l in f["ligands"] if l["heme"]) == 4
    assert f["assemblies"][0]["relation_to_deposited"] == "same as deposited"
    f = grounding.facts("1hho")   # one alpha-beta pair deposited, the tetramer is built
    assert f["assemblies"][0]["relation_to_deposited"] == "built by symmetry"
    assert f["assemblies"][0]["n_polymer_chains"] == 4
    f = grounding.facts("1tup")
    assert {(c["auth_asym_id"], c["label_asym_id"]) for c in f["chains"]
            if c["polymer_type"] == "protein"} == {("A", "C"), ("B", "D"), ("C", "E")}
    assert sum(1 for c in f["chains"] if c["polymer_type"] == "DNA") == 2
    f = grounding.facts("3ave")   # one N-glycan per Fc chain, on Asn297
    assert len(f["glycans"]) == 2
    assert {(g["attached_to"]["comp_id"], g["attached_to"]["auth_seq_id"])
            for g in f["glycans"]} == {("ASN", 297)}
    f = grounding.facts("1crn")
    assert len(f["disulfides"]) == 3 and not f["ligands"]


def test_loaders():
    assert grounding.facts("9zzz") is None and grounding.variants("P00000") is None
    assert grounding.structure_file("9zzz") is None
    clinical = grounding.panel_entries("clinical")
    assert {p["entry"] for p in PROTEINS} <= {e["id"] for e in clinical}
    assert len(grounding.panel_entries()) == len(ENTRIES)


def test_fetch_structure_reads_the_frozen_file_without_network(monkeypatch):
    pytest.importorskip("gemmi")
    import urllib.request

    def refuse(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    st = grounding.fetch_structure("3ptb")
    assert grounding.residue_at(st, "A", 195) == "SER"
    assert {r.comp_id for r in grounding.ligands(st)} == {"BEN", "CA"}
    assert len(grounding.disulfides(st)) == 6
    with pytest.raises(LookupError):
        grounding.fetch_structure("9zzz", allow_network=False)
