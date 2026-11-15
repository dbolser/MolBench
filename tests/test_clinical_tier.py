"""
The clinical-variant tier (``tasks/mvs_clinical`` and its twins in
``tasks/api_clinical``) and the frozen variant data behind it
(``molbench/variants.py``).

What the paper's lead claim rests on is pinned here: only ClinVar-confirmed variants
are called pathogenic, the prompt never gives the answer away, the target is the
wild-type residue at the variant's UniProt position, and the recorded difficulty
facts are true of the structure. Stdlib + pytest; no network.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import socket
import urllib.request
from collections import Counter

import pytest

from molbench import grounding, sifts, tasks as T, variants as V
from molbench.atoms import load_table

REPO = pathlib.Path(__file__).resolve().parent.parent
TIER = [t for t in T.load_corpus() if t["tier"] == "clinical"]
MVS = [t for t in TIER if t["track"] == "mvs"]
API = [t for t in TIER if t["track"] == "api"]
BY_ID = {t["id"]: t for t in TIER}


def _generator():
    spec = importlib.util.spec_from_file_location(
        "generate_clinical_tasks", REPO / "scripts" / "generate_clinical_tasks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _clin(task: dict) -> dict:
    return task["provenance"]["clinical"]


# --- the frozen variant data -------------------------------------------------------

def test_variants_are_read_without_the_network(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    V.confirmed.cache_clear()
    V.processing.cache_clear()
    proteins = V.proteins()
    assert len(proteins) == 27
    for p in proteins:
        assert V.confirmed(p["accession"]), p["gene"]
        V.mature_numbering(p["accession"], 50)
    assert V.confirmed("Q00000") == ()        # not a panel protein: empty, not a download


def test_every_frozen_variant_is_one_clinvar_calls_pathogenic():
    for p in V.proteins():
        for v in V.confirmed(p["accession"]):
            assert v.vcv and all(x.startswith("VCV") for x in v.vcv)
            assert V.classification_words(v) in (
                "pathogenic", "likely pathogenic", "pathogenic/likely pathogenic",
                "pathogenic or likely pathogenic")


def test_classification_words_refuse_anything_else():
    v = V.confirmed("P04637")[0]
    for bad in ("Conflicting classifications of pathogenicity", "Uncertain significance",
                "Benign", "not provided"):
        with pytest.raises(ValueError):
            V.classification_words(v._replace(classification=(bad,)))
    with pytest.raises(ValueError):
        V.classification_words(v._replace(classification=()))
    both = [v._replace(classification=("Pathogenic",)),
            v._replace(classification=("Likely pathogenic",))]
    assert V.classification_words(both) == "pathogenic or likely pathogenic"
    assert V.classification_words(both[0]) == "pathogenic"


def test_names():
    r175h = next(v for v in V.confirmed("P04637") if (v.position, v.mutant) == (175, "H"))
    assert V.short(r175h) == "R175H" and V.hgvs(r175h) == "p.Arg175His"
    assert V.short(r175h, 3) == "R3H"


@pytest.mark.parametrize("accession, position, number, what", [
    ("P02766", 50, 30, "the 20-residue signal peptide"),          # TTR V30M = p.Val50Met
    ("P68871", 7, 6, "the initiator methionine"),                 # HBB E6V = p.Glu7Val
    ("P01009", 366, 342, "the 24-residue signal peptide"),        # SERPINA1 Z: E342K
    ("P02649", 176, 158, "the 18-residue signal peptide"),        # APOE R158C
    ("P00441", 5, 4, "the initiator methionine"),                 # SOD1 A4V
])
def test_mature_numbering_gives_the_literature_names(accession, position, number, what):
    m = V.mature_numbering(accession, position)
    assert m and m["number"] == number and m["what"] == what
    assert m["removed"] == position - number


def test_mature_numbering_refuses_where_there_is_no_single_one():
    assert V.mature_numbering("P01308", 32) is None     # insulin: first product is a peptide
    assert V.mature_numbering("P04637", 175) is None    # p53: nothing is removed
    assert V.mature_numbering("P02766", 10) is None     # inside the signal peptide
    assert V.mature_numbering("Q00000", 10) is None     # no frozen features


# --- the tier as a whole -----------------------------------------------------------

def test_the_task_files_are_what_the_generator_writes():
    """Seeded and deterministic: a rebuild gives every file byte for byte."""
    assert _generator().main(["--check"]) == 0


def test_size_and_coverage():
    assert len(MVS) == len(API) >= 60
    genes = {_clin(t)["gene"] for t in MVS}
    assert genes == {p["gene"] for p in V.proteins()} and len(genes) == 27
    d = [_clin(t)["difficulty"] for t in MVS]
    assert sum(x["structure_has_offset"] for x in d) * 2 >= len(MVS)
    assert sum(x["needs_numbering_offset"] for x in d) * 2 >= len(MVS)
    assert sum(x["author_chain_differs_from_label_chain"] for x in d) >= len(MVS) // 5
    # Half ask for the residue alone, half also ask for context.
    alone = sum(_clin(t)["context"] == "none" for t in MVS)
    assert abs(alone - len(MVS) / 2) <= len(MVS) * 0.1
    # Some prompts leave the accession out: the API answer then has to supply it.
    with_acc = sum(x["accession_in_prompt"] for x in d)
    assert len(MVS) // 3 <= with_acc <= 2 * len(MVS) // 3


def test_reuse_caps():
    for mine in (MVS, API):
        assert max(Counter(t["structures"][0] for t in mine).values()) <= 6
        assert max(Counter(t["family"] for t in mine).values()) / len(mine) <= 0.125


def test_no_task_uses_the_worked_example():
    assert all("1hsg" not in json.dumps(t).lower() for t in TIER)


def test_twins():
    for t in MVS:
        twin = BY_ID[t["twin_of"]]
        assert twin["track"] == "api" and twin["twin_of"] == t["id"]
        for key in ("prompt", "structures", "split", "family"):
            assert twin[key] == t[key], (t["id"], key)
        # The same atoms and colour; the representation is in each track's own word.
        assert [(p["selector"], p["color"]) for p in twin["target"]] == \
               [(p["selector"], p["color"]) for p in t["target"]]
        a, b = _clin(t), dict(_clin(twin))
        assert "pdbe-molstar resolves uniprot_accession" in b.pop("api_note")
        if a["pair"]:       # a pair is linked within its own track
            assert BY_ID[a["pair"]["with"]]["twin_of"] == b["pair"]["with"]
            a, b = {**a, "pair": None}, {**b, "pair": None}
        assert a == b


def test_heldback_structures_are_in_no_public_task():
    held = {t["structures"][0] for t in TIER if t["split"] == "heldback"}
    public = {t["structures"][0] for t in TIER if t["split"] == "public"}
    assert held and not held & public
    share = len(held) / len(held | public)
    assert 0.15 <= share <= 0.25
    # ... and in no public task of any other tier either (the validator's rule).
    others = {s for t in T.load_corpus() if t["split"] == "public" for s in t["structures"]}
    assert not held & others


def test_pairs_point_at_each_other_and_ask_the_same_variant():
    paired = [t for t in MVS if _clin(t)["pair"]]
    assert len(paired) >= 8
    kinds = set()
    for t in paired:
        other = BY_ID[_clin(t)["pair"]["with"]]
        assert _clin(other)["pair"]["with"] == t["id"]
        assert [v["variant"] for v in _clin(other)["variants"]] == \
               [v["variant"] for v in _clin(t)["variants"]]
        assert other["structures"] != t["structures"] and other["family"] == t["family"]
        kinds.add((_clin(t)["difficulty"]["needs_numbering_offset"],
                   _clin(other)["difficulty"]["needs_numbering_offset"]))
    assert (True, False) in kinds       # the offset effect: same variant, with and without


# --- every task ----------------------------------------------------------------------

@pytest.mark.parametrize("task", MVS, ids=lambda t: t["id"])
def test_variants_are_confirmed_and_named_truthfully(task):
    c = _clin(task)
    frozen = {(v.position, v.wild_type, v.mutant): v for v in V.confirmed(c["accession"])}
    used = []
    for rec in c["variants"]:
        m = re.fullmatch(r"([A-Z])(\d+)([A-Z])", rec["variant"])
        v = frozen[(int(m.group(2)), m.group(1), m.group(3))]       # KeyError = not confirmed
        used.append(v)
        assert rec["uniprot_position"] == v.position and rec["hgvs"] == V.hgvs(v)
        assert tuple(rec["clinvar_vcv"]) == v.vcv
        assert tuple(rec["clinvar_classification"]) == v.classification
        assert rec["name_in_prompt"] in task["prompt"]
        if c["naming"] == "legacy":
            mature = V.mature_numbering(c["accession"], v.position)
            assert rec["name_in_prompt"] == V.short(v, mature["number"])
            assert "mature-protein numbering" in task["prompt"] and mature["what"] in task["prompt"]
            assert V.hgvs(v) not in task["prompt"]
        else:
            assert rec["name_in_prompt"] in (V.hgvs(v), V.short(v))
    # The only claim about pathogenicity is ClinVar's own classification, in its words.
    words = V.classification_words(used)
    assert words in task["prompt"] and "ClinVar" in task["prompt"]
    for claim in re.findall(r"(?:likely )?pathogenic(?:/likely pathogenic| or likely pathogenic)?",
                            task["prompt"]):
        assert claim == words, claim
    assert "hotspot" not in task["prompt"].lower()


@pytest.mark.parametrize("task", MVS, ids=lambda t: t["id"])
def test_prompt_names_the_structure_and_not_the_answer(task):
    c, prompt = _clin(task), task["prompt"]
    entry = task["structures"][0]
    shown = entry.upper() if not entry.startswith("af-") else f"AF-{c['accession']}-F1"
    assert shown in prompt and c["gene"] in prompt
    assert (c["accession"] in prompt) == c["difficulty"]["accession_in_prompt"]
    for word in ("label_", "auth_", "seq_id", "asym_id", "selector", "SIFTS", "struct_asym",
                 "residue_number"):
        assert word not in prompt, word
    # Where the structure's number is not the number in the name, it is not in the prompt.
    in_names = {int(n) for v in c["variants"] for n in re.findall(r"\d+", v["name_in_prompt"])}
    for v in c["variants"]:
        for r in v["residues"]:
            if r["auth_seq_id"] not in in_names:
                assert not re.search(rf"(?<![\w-]){r['auth_seq_id']}(?![\w-])", prompt), prompt


@pytest.mark.parametrize("task", MVS, ids=lambda t: t["id"])
def test_target_is_the_wild_type_residue_at_the_uniprot_position(task):
    c = _clin(task)
    entry = task["structures"][0]
    table = load_table(entry)
    target = table.selector(task["target"][0]["selector"])
    assert target and len(task["target"]) == 1
    by_uniprot = by_author = 0
    for v in c["variants"]:
        wild = V.AA3[v["variant"][0]].upper()
        by_uniprot |= sifts.uniprot_atoms(entry, c["accession"], v["uniprot_position"]) or 0
        frozen = grounding.variants(c["accession"])["variants"]
        rec = next(x for x in frozen if x["position"] == v["uniprot_position"]
                   and x["mutant"] == v["variant"][-1])
        for r in v["residues"]:
            assert r["comp_id"] == wild
            assert r in rec["structures"][entry]
            sel = {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["auth_seq_id"]}
            if r["pdbx_PDB_ins_code"]:
                sel["pdbx_PDB_ins_code"] = r["pdbx_PDB_ins_code"]
            by_author |= table.selector(sel)
    assert by_author == target
    if c["chain"] is None:
        assert by_uniprot == target             # every copy of the protein
    else:
        chain = table.selector({"label_asym_id": c["chain"]["label_asym_id"]})
        assert by_uniprot & chain == target and by_uniprot != target


@pytest.mark.parametrize("task", MVS, ids=lambda t: t["id"])
def test_recorded_difficulty_is_true_of_the_structure(task):
    c = _clin(task)
    d = c["difficulty"]
    res = [r for v in c["variants"] for r in v["residues"]]
    offsets = {r["auth_seq_id"] - v["uniprot_position"]
               for v in c["variants"] for r in v["residues"]}
    assert d["needs_uniprot_mapping"] is True and d["needs_ligand_identity"] is False
    assert d["needs_numbering_offset"] == (offsets != {0})
    assert d["author_minus_uniprot"] == sorted(offsets)
    assert d["author_chain_differs_from_label_chain"] == any(
        r["auth_asym_id"] != r["label_asym_id"] for r in res)
    assert d["author_number_differs_from_label_number"] == any(
        r["auth_seq_id"] != r["label_seq_id"] for r in res)
    assert d["insertion_code"] == any(r["pdbx_PDB_ins_code"] for r in res)
    assert d["target_residues"] == len(res)
    assert d["alphafold_model"] == task["structures"][0].startswith("af-")
    assert d["name_in_mature_numbering"] == (c["naming"] == "legacy")
    if d["needs_numbering_offset"]:
        assert d["structure_has_offset"]


@pytest.mark.parametrize("task", MVS, ids=lambda t: t["id"])
def test_a_bare_one_letter_name_has_no_same_amino_acid_decoy(task):
    """Read straight off the atom table's columns: is the residue whose author number is
    the number in the name a different residue of the wild-type amino acid? If so the
    prompt must say which numbering it means (an HGVS name, or a stated mature one)."""
    c = _clin(task)
    cols = load_table(task["structures"][0]).columns
    rows = set(zip(cols["auth_asym_id"], cols["auth_seq_id"], cols["pdbx_PDB_ins_code"],
                   cols["label_comp_id"]))
    decoy = False
    for v in c["variants"]:
        number = int(re.search(r"\d+", v["name_in_prompt"]).group())
        for r in v["residues"]:
            if r["auth_seq_id"] == number and not r["pdbx_PDB_ins_code"]:
                continue
            decoy = decoy or any(ch == r["auth_asym_id"] and n == number and comp == r["comp_id"]
                                 for ch, n, _ins, comp in rows)
    assert c["difficulty"]["number_in_name_as_author_number_is_same_amino_acid"] == decoy
    if decoy:
        assert c["naming"] in ("hgvs", "legacy"), task["id"]


@pytest.mark.parametrize("task", MVS, ids=lambda t: t["id"])
def test_reference_holds_only_what_is_requested(task):
    """Decision 17: one component for the residue(s), plus one for the context the
    prompt asks for in words, and nothing else."""
    c = _clin(task)
    comps = [n for n in _walk(task["reference"]["root"]) if n["kind"] == "component"]
    assert len(comps) == (1 if c["context"] == "none" else 2)
    if c["context"] == "none":
        assert "cartoon" not in task["prompt"]
    else:
        assert "cartoon" in task["prompt"]
    look = c["look"]
    assert look["color"] in task["prompt"]
    assert ("spacefill" if look["rep"] == "spacefill" else "ball-and-stick") in task["prompt"]


def _walk(node):
    yield node
    for child in node.get("children", []):
        yield from _walk(child)


@pytest.mark.parametrize("task", API, ids=lambda t: t["id"])
def test_api_twin_selects_by_uniprot_number(task):
    """The API reference uses the viewer's own UniProt selector (so the twin tests
    knowing it exists), except on an AlphaFold model, whose residue numbers already
    are UniProt numbers."""
    c = _clin(task)
    items = [d for call in task["reference"] if call["action"] == "color"
             for d in call["data"] if "representation" in d]
    assert items
    if c["difficulty"]["alphafold_model"]:
        assert all("uniprot_accession" not in d for d in items)
    else:
        assert all(d["uniprot_accession"] == c["accession"] for d in items)
        assert {d["uniprot_residue_number"] for d in items} == \
               {v["uniprot_position"] for v in c["variants"]}


@pytest.mark.parametrize("task", TIER, ids=lambda t: t["id"])
def test_grounding_pack_states_the_frozen_facts(task):
    c = _clin(task)
    pack = task["grounding"]
    assert pack["rule"] == "clinical-v1"
    text = pack["text"]
    assert c["accession"] in text and "UniProt mapping (SIFTS" in text
    for v in c["variants"]:
        assert f"UniProt position {v['uniprot_position']}" in text
        for r in v["residues"]:
            assert f"{r['auth_asym_id']} {r['auth_seq_id']}{r['pdbx_PDB_ins_code']} " \
                   f"{r['comp_id']}" in text
    # Facts only: no scene, no calls, no instruction.
    for word in ('"kind"', '"action"', "selector", "should", "must", "use "):
        assert word not in text, word
