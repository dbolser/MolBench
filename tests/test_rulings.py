"""The rulings after the corpus merge (FINAL_PLAN.md, 2026-11-15), pinned on the corpus
on disk. Unstated attributes are in tests/test_grading_semantics.py (MVS) and
tests/test_api_forms.py (API); paraphrases in tests/test_paraphrases.py."""

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import additives  # noqa: E402

from molbench import grader, grounding, tasks as T  # noqa: E402

TASKS = {t["id"]: t for t in T.load_corpus()}
ORIGINALS = [t for t in TASKS.values() if not t["paraphrase_of"]]
HELD = set(json.loads((REPO / "data" / "panel" / "heldback.json").read_text()))


def test_tasks_that_need_no_lookup_are_in_the_translation_tier():
    nucleic = [t for t in ORIGINALS if t["family"] == "tr-nucleic"]
    assert len(nucleic) == 10 and {t["tier"] for t in nucleic} == {"translation"}
    assert not any(t["family"] == "gr-nucleic" for t in TASKS.values())
    for t in nucleic:
        if t["track"] == "mvs":
            assert '"nucleic"' in json.dumps(t["reference"])          # Mol*'s own selection
            assert t["provenance"]["difficulty"]["needs_structure_lookup"] is False


def test_no_change_tasks_are_clear_requests_not_questions():
    noops = [t for t in ORIGINALS if t["context"] and t["context"]["noop"]]
    assert len(noops) >= 16
    for t in noops:
        assert not t["prompt"].rstrip().endswith("?") or "spin" in t["prompt"], t["id"]
        assert t["provenance"]["noop_kind"] != "question", t["id"]


def test_main_ligand_is_a_biological_ligand():
    """Follow-up and accept-set requests about "the ligand" never mean a crystallisation
    additive, a buffer, a detergent or a lipid (data/corpus/additives.json)."""
    assert {"TLA", "C8E", "P33", "LI1", "GOL", "SO4"} <= additives.ADDITIVES
    assert not {"HEM", "RET", "ATP", "BTN"} & additives.ADDITIVES
    for t in ORIGINALS:
        if t["tier"] not in ("followup", "accept_set") or "ligand" not in t["prompt"].lower():
            continue
        text = json.dumps([t["reference"], t["accepted"], t["target"]])
        named = {c for c in additives.ADDITIVES if f'"label_comp_id": "{c}"' in text}
        assert not named, (t["id"], named)
        for word in t["prompt"].replace("(", " ").replace(")", " ").split():
            assert word not in additives.ADDITIVES, (t["id"], word)


def test_an_undo_task_does_not_pass_without_the_undo():
    undo = [t for t in ORIGINALS if t["family"] == "api-undo"]
    assert len(undo) == 4
    for t in undo:
        assert any(c.startswith("wrong answer fails: every step but the undo")
                   for c in t["provenance"]["checks"]), t["id"]
    # spelled out for the three kinds whose undo used to change nothing
    t = next(x for x in undo if x["provenance"]["difficulty"]["undo_step"] == "tooltips")
    both = next(a for a in t["reference"] if a["action"] == "tooltips")
    assert len(both["data"]) == 2
    assert not grader.grade_task(t, t["reference"][:-1])["success"]
    t = next(x for x in undo if x["provenance"]["difficulty"]["undo_step"] == "highlight")
    assert t["reference"][-1] == {"action": "clear_highlight"}
    assert not grader.grade_task(t, t["reference"][:-1])["success"]
    assert grader.grade_task(t, t["reference"][:-2])["success"]       # never highlighted: same state


def test_clinical_offset_pairs_rest_on_four_proteins_and_stay_in_one_split():
    clin = [t for t in ORIGINALS if t["tier"] == "clinical" and t["track"] == "mvs"]
    by_id = {t["id"]: t for t in clin}
    offset_pairs: dict[str, int] = {}
    for t in clin:
        pair = t["provenance"]["clinical"]["pair"]
        if not pair:
            continue
        other = by_id[pair["with"]]
        assert t["split"] == other["split"] == "public", t["id"]          # no pair across the split
        if pair["this_structure"] == "author numbers differ from UniProt numbers":
            assert other["provenance"]["clinical"]["pair"]["this_structure"] == "author numbers are UniProt numbers"
            gene = t["provenance"]["clinical"]["gene"]
            offset_pairs[gene] = offset_pairs.get(gene, 0) + 1
            a, = t["provenance"]["clinical"]["variants"]
            b, = other["provenance"]["clinical"]["variants"]
            assert a["uniprot_position"] == b["uniprot_position"]
            assert {r["auth_seq_id"] for r in a["residues"]} != {r["auth_seq_id"] for r in b["residues"]}
            assert {r["auth_seq_id"] for r in b["residues"]} == {b["uniprot_position"]}
    assert set(offset_pairs) == {"HBB", "LYZ", "CRYGD", "CALM1"}, offset_pairs


def test_apoe_r158c_is_not_asked_about():
    for t in TASKS.values():
        if t["tier"] == "clinical":
            assert "R158C" not in t["prompt"] and "Arg176Cys" not in t["prompt"], t["id"]
    for t in ORIGINALS:
        if t["tier"] == "clinical" and t["provenance"]["clinical"]["accession"] == "P02649":
            assert "R176C" not in [v["variant"] for v in t["provenance"]["clinical"]["variants"]], t["id"]


def test_helix_and_strand_tasks_are_flagged_for_separate_reporting():
    clin = [t for t in ORIGINALS if t["tier"] == "clinical"]
    flagged = [t for t in clin if t["provenance"]["clinical"]["report_apart"]]
    assert {t["family"] for t in flagged} == {"clin-sse-helix", "clin-sse-strand"}
    assert len(flagged) == 20                                           # ten per track
    assert all(t["provenance"]["clinical"]["report_apart"] is None
               for t in clin if not t["family"].startswith("clin-sse"))


def test_added_alphafold_models_are_public_and_numbered_as_uniprot():
    panel = {e["id"]: e for e in grounding.panel()["entries"]}
    added = [e for e in panel.values() if e.get("public_only")]
    assert {e["id"] for e in added} == {"af-p61626-f1-model_v6", "af-p07320-f1-model_v6",
                                        "af-p0dp23-f1-model_v6"}
    for e in added:
        assert e["id"] not in HELD and e["kind"] == "alphafold" and not e["offset"]
        assert T.table_for(e["id"]) is not None


def test_api_tasks_cover_insertion_codes_and_label_chain_ids():
    ins = [t for t in ORIGINALS if t["family"] == "api-inscode"]
    lab = [t for t in ORIGINALS if t["family"] == "api-label-chain"]
    assert len(ins) == 5 and len(lab) == 5
    for t in ins:
        (item,) = t["reference"][1]["data"]
        assert set(item) == {"struct_asym_id", "residue_number", "color"}
        table = T.table_for(t["structures"][0])
        atoms = table.selector(t["target"][0]["selector"])
        cols = table.columns
        rows = [i for i in range(table.n) if atoms >> i & 1]
        assert {cols["pdbx_PDB_ins_code"][i] for i in rows} - {"", None}        # it has a code
        by_author = [{"action": "load", "molecule_id": t["structures"][0]},
                     {"action": "color", "data": [{"auth_asym_id": cols["auth_asym_id"][rows[0]],
                                                   "auth_seq_id": cols["auth_seq_id"][rows[0]],
                                                   "color": item["color"]}]}]
        assert not grader.grade_task(t, by_author)["success"], t["id"]           # also paints 52 when 52A is meant
    for t in lab:
        (item,) = t["reference"][1]["data"]
        assert set(item) == {"struct_asym_id", "color"}
        chain = next(c for c in grounding.facts(t["structures"][0])["chains"]
                     if c["label_asym_id"] == item["struct_asym_id"])
        assert chain["auth_asym_id"] != chain["label_asym_id"]
        wrong = [t["reference"][0], {"action": "color", "data": [{"auth_asym_id": item["struct_asym_id"],
                                                                  "color": item["color"]}]}]
        assert not grader.grade_task(t, wrong)["success"], t["id"]


def test_no_uniprot_task_on_a_tandem_repeat_entry():
    for t in ORIGINALS:
        if t["family"].startswith("api-uniprot"):
            assert "P0CG48" not in json.dumps(t["reference"]) and "P0CG48" not in t["prompt"], t["id"]


def test_corpus_md_is_what_the_report_script_writes():
    import corpus_report
    assert corpus_report.main(["--check"]) == 0
