"""Pinned tests for the findings of the four corpus audits of 2026-11-16.

Each test names the finding it pins. The control set (tests/controls) carries the
matching control kinds: `unstated_stretch_in_highlight_colour`, `unstated_hide_water`,
`unstated_hide_polymer`, `uniprot_number_on_alphafold_model`,
`uniprot_number_on_a_file_without_sifts`, `file_that_loads_nothing`.
"""

from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import api_forms  # noqa: E402
from molbench import grader, mvs, pdbe_state as ps, runner, schema, sifts, variants as V  # noqa: E402
from molbench import tasks as T  # noqa: E402

CORPUS = T.load_corpus()
BY_ID = {t["id"]: t for t in CORPUS}
ORIGINALS = [t for t in CORPUS if not t["paraphrase_of"]]
API = [t for t in ORIGINALS if t["track"] == "api"]
MVS = [t for t in ORIGINALS if t["track"] == "mvs"]


def ok(task: dict, answer) -> bool:
    return bool(runner.grade_parsed(task, answer)["success"])


# --- UniProt keys on an AlphaFold model (blocker, two audits) ---------------------------

AF_CLINICAL = [t for t in API if t["tier"] == "clinical" and "-af-" in t["id"]]


def test_sifts_lookup_takes_the_version_free_alphafold_name():
    assert sifts.frozen_name("af-p68871-f1") == "af-p68871-f1-model_v6"
    assert sifts.uniprot_atoms("af-p68871-f1", "P68871", 67) == \
        sifts.uniprot_atoms("af-p68871-f1-model_v6", "P68871", 67) != 0
    assert sifts.frozen_name("1tup") == "1tup" and sifts.frozen_name("af-zzzzzz-f1") == "af-zzzzzz-f1"


@pytest.mark.parametrize("task", AF_CLINICAL, ids=lambda t: t["id"])
def test_alphafold_clinical_task_takes_uniprot_and_author_numbering(task):
    """The reference names the residue by UniProt accession and number, as on a PDB
    entry; the model is numbered as UniProt, so the author number says the same."""
    items = [p for a in task["reference"] if a["action"] == "color" for p in a["data"]
             if "representation" in p]
    assert items and all("uniprot_accession" in p for p in items)
    by_author = copy.deepcopy(task["reference"])
    for a in by_author:
        for p in a.get("data") or []:
            if "uniprot_accession" in p:
                p.pop("uniprot_accession")
                p["auth_asym_id"], p["auth_seq_id"] = "A", p.pop("uniprot_residue_number")
    assert ok(task, by_author)


def test_there_are_alphafold_clinical_tasks():
    assert len(AF_CLINICAL) >= 9


def test_uniprot_keys_select_nothing_on_a_file_without_sifts_columns():
    data = [{"uniprot_accession": "P04637", "uniprot_residue_number": 248, "color": "red"}]
    ref = [{"action": "load", "molecule_id": "1tup"}, {"action": "color", "data": data}]

    def by_url(url):
        return [{"action": "load", "custom_data": {"url": url, "format": "cif", "binary": False}},
                {"action": "color", "data": data}]
    assert ps.grade_state(ref, by_url("https://www.ebi.ac.uk/pdbe/entry-files/download/1tup_updated.cif"))["success"]
    assert not ps.grade_state(ref, by_url("https://files.rcsb.org/download/1tup.cif"))["success"]
    assert ps.has_sifts_columns(None) and ps.has_sifts_columns(
        {"url": "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v4.cif"})


# --- the reply parser (major) ---------------------------------------------------------

HUGE, DEEP = "9" * 4301, 100000


@pytest.mark.parametrize("track,raw", [
    ("api", '[{"action":"color","data":[{"auth_seq_id": ' + HUGE + "}]}]"),
    ("api", "[" * DEEP + "]" * DEEP),
    ("mvs", '{"a":' * DEEP + "1" + "}" * DEEP),
    ("mvs", '{"root": {"kind": "root", "children": [], "x": ' + HUGE + "}}"),
], ids=["api-huge-number", "api-deep-nesting", "mvs-deep-nesting", "mvs-huge-number"])
def test_a_reply_no_json_parser_can_read_is_invalid_json_not_a_crash(track, raw):
    task = BY_ID["api-002"] if track == "api" else next(t for t in MVS if t["tier"] == "translation")
    got = runner.grade_output(task, raw)
    assert got["outcome"] == "invalid_json" and got["f1"] == 0.0


def test_a_bracket_in_the_prose_does_not_hide_the_answer():
    raw = 'Here you go [see notes]: [{"action":"load","molecule_id":"1cbs"}] ... [auth].'
    assert runner.extract_actions(raw) == ([{"action": "load", "molecule_id": "1cbs"}], None)
    assert runner.extract_actions("no list here [not json]")[0] is None


def test_validity_labels_follow_the_viewer():
    bad = [{"action": "load", "molecule_id": "1cbs"},
           {"action": "color", "data": [{"label_comp_id": "REA", "representation": "sticks"}]}]
    assert any("representation" in e for e in schema.validate_actions(bad))
    bad[1]["data"][0]["representation"] = "ball-and-stick"
    assert schema.validate_actions(bad) == []


# --- an MVS scene that loads nothing (major) --------------------------------------------

TR = next(t for t in MVS if t["id"] == "tr-surface-5cj6")


def _resourced(tree, url=None, fmt=None):
    tree = copy.deepcopy(tree)
    for node in _walk(mvs.extract_root(tree)):
        if node.get("kind") == "download" and url:
            node["params"]["url"] = url
        if node.get("kind") == "parse" and fmt:
            node["params"]["format"] = fmt
    return tree


def _walk(node):
    yield node
    for child in node.get("children") or []:
        yield from _walk(child)


@pytest.mark.parametrize("url,fmt", [
    (None, "bcif"), (None, "pdb"), ("https://www.rcsb.org/structure/5CJ6", None),
    ("https://example.org/5cj6.cif", None), ("5cj6.cif", None),
    ("https://files.rcsb.org/download/5cj6.pdb", "mmcif"), ("https://models.rcsb.org/5cj6.bcif", "mmcif")])
def test_mvs_scene_on_an_unreadable_source_scores_zero(url, fmt):
    got = runner.grade_parsed(TR, _resourced(TR["reference"], url, fmt))
    assert got["outcome"] == "load_failed" and not got["success"] and got["f1"] == 0.0


@pytest.mark.parametrize("url,fmt", [
    ("https://files.rcsb.org/download/5CJ6.cif", "mmcif"), ("https://models.rcsb.org/5cj6.bcif", "bcif"),
    ("https://www.ebi.ac.uk/pdbe/entry-files/download/5cj6_updated.cif", "mmcif"),
    ("https://files.rcsb.org/download/5cj6.cif.gz", "mmcif")])
def test_mvs_scene_on_another_real_source_is_still_right(url, fmt):
    assert ok(TR, _resourced(TR["reference"], url, fmt))


def test_no_task_scene_trips_the_load_check():
    for t in CORPUS:
        if t["track"] != "mvs":
            continue
        scenes = [t["reference"]] + list(t["accepted"]) + ([t["context"]["scene"]] if t["context"] else [])
        for s in scenes:
            assert mvs.load_problem(s) is None, t["id"]


# --- API call forms (two blockers, three majors) ----------------------------------------

def _stretch_in_highlight(reference):
    """The form the API prompt's example teaches: residue coloured and drawn in one colour."""
    new, hit = copy.deepcopy(reference), False
    for a in new:
        if a.get("action") == "color" and a.get("non_selected_color") is not None:
            for p in a.get("data") or []:
                if p.get("representation") and p.get("representationColor") \
                        and p.get("color") == a["non_selected_color"] != p["representationColor"]:
                    p["color"] = p["representationColor"]
                    hit = True
    return new if hit else None


def test_the_api_prompts_example_form_is_accepted_everywhere():
    """36 grounded and 9 translation twins failed this form before the fix."""
    n = 0
    for t in API:
        if t["context"]:
            continue
        answer = _stretch_in_highlight(t["reference"])
        if answer is not None:
            n += 1
            assert ok(t, answer), t["id"]
    assert n >= 70


def test_the_api_reference_example_is_that_form():
    text = (REPO / "molbench" / "api_reference.md").read_text()
    assert '"color": "red"' in text and '"representationColor": "red"' in text


EXCLUDING = [t for t in API if t["provenance"].get("excludes")]


def test_requests_that_exclude_a_component_are_flagged():
    fams = {t["family"] for t in EXCLUDING}
    assert fams == {"gr-glyco-sites", "tr-nucleic"}
    assert len([t for t in EXCLUDING if t["family"] == "gr-glyco-sites"]) == 5
    for t in EXCLUDING:
        assert BY_ID[t["twin_of"]]["provenance"]["excludes"] == t["provenance"]["excludes"]


@pytest.mark.parametrize("task", EXCLUDING, ids=lambda t: t["id"])
def test_no_accepted_form_draws_what_the_request_excludes(task):
    for calls in [task["reference"]] + task["accepted"]:
        state = ps.replay(copy.deepcopy(calls))
        assert api_forms.excluded_atoms(state, task["provenance"]["excludes"]) == 0
    load = next(a for a in task["reference"] if a["action"] == "load")
    colour = next(a for a in task["reference"] if a["action"] == "color")
    assert not ok(task, [load, colour])            # the default view, everything on screen


def test_glycosylation_sites_answered_with_the_sugars_hidden():
    t = BY_ID["gr-glyco-sites-3ave-api"]
    asn = [{"auth_asym_id": c, "auth_seq_id": 297, "color": "gray", "representation": "ball-and-stick",
            "representationColor": "plum"} for c in "AB"]
    hidden = [{"action": "load", "molecule_id": "3ave"},
              {"action": "set_property", "name": "hide_carbs", "value": True},
              {"action": "color", "data": asn, "non_selected_color": "gray"}]
    assert ok(t, hidden)
    assert not ok(t, [hidden[0], hidden[2]])        # sugars drawn: "no sugars"
    assert not ok(BY_ID["tr-nucleic-1kf1-api"],
                  [{"action": "load", "molecule_id": "1kf1"},
                   {"action": "color", "data": [{"color": "steelblue"}]}])


def test_chains_by_author_id_on_the_default_view():
    """gr-entity twins failed author ids on a bare load, where label ids passed."""
    n = 0
    for t in API:
        if t["family"] != "gr-entity":
            continue
        for form in api_forms.chain_naming_forms([a for a in t["reference"]
                                                  if a["action"] != "set_visual_style"]):
            n += 1
            assert ok(t, form[1]), t["id"]
    assert n >= 5
    t = BY_ID["tr-chains-named-5ni1-api"]
    assert ok(t, [a for a in t["reference"] if a["action"] != "set_visual_style"])


# Requests whose words say what is on screen ("only chain A", "hide the waters",
# "nothing else", "without chain C"), or where "cartoon" is not the request: there the
# cartoon style and the default view are different answers, and one is the reference.
ONE_FORM_ONLY = {"api-010", "api-013", "api-keep-sticks", "gr-all-but-chain", "tr-chain-only", "tr-strands"}


def test_cartoon_by_style_and_by_default_are_both_accepted():
    """Every single-turn API task whose prompt asks for a cartoon (and not for "the
    cartoon style") accepts its other call form, or is on the list above."""
    missing = set()
    for t in API:
        prompt = t["prompt"].lower()
        if t["context"] or t["tier"] == "accept_set" or "cartoon" not in prompt \
                or "cartoon style" in prompt:
            continue
        excludes = t["provenance"].get("excludes") or ()
        forms = [calls for label, calls in api_forms.all_forms(t["reference"], excludes)
                 if api_forms._default_view(calls) != api_forms._default_view(t["reference"])]
        if not any(ok(t, calls) for calls in forms):
            missing.add(t["id"] if t["id"] in ONE_FORM_ONLY else t["family"])
    assert missing <= ONE_FORM_ONLY, sorted(missing - ONE_FORM_ONLY)


def test_the_three_twins_on_residues_without_a_trace_atom_are_plain_now():
    for tid in ("tr-het-code-3ert-api", "gr-secstruct-3ert-api", "gr-attachment-1hrc-hec-api"):
        t = BY_ID[tid]
        assert not any(a.get("name") == "hide_polymer" for a in t["reference"]), tid
        assert t["accepted"], tid
    t = BY_ID["tr-het-code-3ert-api"]
    assert ok(t, [{"action": "load", "molecule_id": "3ert"},
                  {"action": "set_visual_style", "style": "cartoon"},
                  {"action": "color", "non_selected_color": "gray", "data": [
                      {"label_comp_id": "OHT", "representation": "ball-and-stick",
                       "representationColor": "limegreen"}]}])


def test_free_hide_is_written_only_where_style_and_default_view_are_both_right():
    with_free = [t for t in CORPUS if t.get("free_hide")]
    assert len([t for t in with_free if not t["paraphrase_of"]]) >= 100
    for t in with_free:
        lists = [t["reference"]] + t["accepted"]
        styled = [any(a.get("action") == "set_visual_style" for a in c) for c in lists]
        assert t["track"] == "api" and t["context"] is None and any(styled) and not all(styled), t["id"]
        for c in lists:
            if api_forms._default_view(c):
                assert ok(t, api_forms.with_hidden(c, t["free_hide"])), t["id"]
                assert not ok(t, api_forms.with_hidden(c, ["hide_polymer"])), t["id"]


def test_a_requested_ligand_cannot_be_hidden_for_free():
    t = BY_ID["gr-heme-5ni1-api"]
    assert "hide_heteroatoms" not in (t.get("free_hide") or [])
    default = next(c for c in t["accepted"] if api_forms._default_view(c))
    assert not ok(t, api_forms.with_hidden(default, ["hide_heteroatoms"]))


def test_spheres_cover_the_default_drawing_of_a_ligand():
    t = BY_ID["gr-heme-5ni1-api"]
    assert ok(t, [{"action": "load", "molecule_id": "5ni1"},
                  {"action": "color", "non_selected_color": "gray", "data": [
                      {"label_comp_id": "HEM", "representation": "spacefill",
                       "representationColor": "teal"}]}])


def test_insertion_code_tasks_state_the_label_position():
    tasks = [t for t in API if t["family"] == "api-inscode"]
    assert len(tasks) == 5
    for t in tasks:
        item = next(p for a in t["reference"] if a["action"] == "color" for p in a["data"])
        assert f"residue {item['residue_number']} of label chain {item['struct_asym_id']}" in t["prompt"]
    assert "auth_ins_code_id" in (REPO / "molbench" / "api_reference.md").read_text()


# --- the MVS prompt's worked example (blocker) ------------------------------------------

def _example():
    text = (REPO / "molbench" / "mvs_reference.md").read_text()
    block = text.split("## Worked example", 1)[1]
    prompt = re.search(r'Prompt: \*"(.+?)"\*', block).group(1)
    scene = json.loads(block.split("```json", 1)[1].split("```", 1)[0])
    return prompt, scene


def test_mvs_worked_example_is_right_by_the_grader_and_is_no_task():
    """The example used to teach the selector "ligand" for a named compound, which the
    generators' references (by component code) mark wrong."""
    prompt, scene = _example()
    assert "1HSG" in prompt and "MK1" in prompt
    assert all("1hsg" not in t["structures"] for t in CORPUS)
    sys.path.insert(0, str(REPO / "scripts"))
    import mvscore_common as C
    built = C.scene("1hsg", [C.drawn_comp("polymer", "cartoon", "gray"),
                              C.drawn_comp({"label_comp_id": "MK1"}, "ball_and_stick", "orange")])
    got = mvs.grade_mvs_task({"reference_mvs": built}, scene)
    assert got["success"] and got["f1"] == 1.0
    assert '"selector": "ligand"' not in json.dumps(scene)


# --- clinical statements (five majors) --------------------------------------------------

CLIN = [t for t in MVS if t["tier"] == "clinical"]


def _generator():
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_clin", REPO / "scripts" / "generate_clinical_tasks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_clinical_variant_has_a_clinvar_record_of_its_own():
    """Of the named gene, about that one variant, classified pathogenic, with assertion
    criteria (the named exceptions apart)."""
    gen = _generator()
    records = V.clinvar_records()
    for t in CLIN:
        c = t["provenance"]["clinical"]
        for v in c["variants"]:
            assert (c["accession"], v["variant"]) not in gen.NOT_USED, t["id"]
            assert v["clinvar_vcv"], t["id"]
            for vcv in v["clinvar_vcv"]:
                rec = records[vcv]
                assert V.record_gene(rec) == c["gene"] or c["gene"] in V.record_gene(rec).split("-"), t["id"]
                assert rec["kind"] != "Haplotype" and "c.[" not in rec["title"], t["id"]
                assert rec["classification"].split(";")[0] in (
                    "Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"), t["id"]
            if all(records[x]["review_status"] == V.NO_CRITERIA for x in v["clinvar_vcv"]):
                assert (c["accession"], v["variant"]) in gen.ZERO_STAR_KEPT, t["id"]


def test_the_variants_the_audit_named_are_gone():
    names = {(t["provenance"]["clinical"]["gene"], v["variant"])
             for t in CLIN for v in t["provenance"]["clinical"]["variants"]}
    for gone in [("CALM1", "D96V"), ("CALM1", "D94A"), ("CALM1", "E141K"), ("HBA1", "F44V"),
                 ("HBA1", "D95Y"), ("APOE", "L46P"), ("APOE", "A170P"), ("APOE", "R154S"),
                 ("APOE", "R176C"), ("CA2", "K18E"), ("TPI1", "F241S"), ("LYZ", "F75I")]:
        assert gone not in names, gone
    assert {v["variant"] for v in V.not_confirmed("P0DP23")} >= {"D96V", "D94A", "E141K"}
    assert len(V.not_confirmed("P0DP23")) == 17 and len(V.not_confirmed("P69905")) == 25


def test_offset_pairs_still_rest_on_four_proteins():
    genes = {t["provenance"]["clinical"]["gene"] for t in CLIN
             if (t["provenance"]["clinical"].get("pair") or {}).get("this_structure", "").startswith("author numbers differ")}
    assert genes >= {"HBB", "LYZ", "CRYGD", "CALM1"}


def test_one_letter_names_in_uniprot_numbering_carry_the_hgvs_prefix():
    n = 0
    for t in CLIN:
        c = t["provenance"]["clinical"]
        for v in c["variants"]:
            if c["naming"] == "short":
                n += 1
                assert v["name_in_prompt"].startswith("p.") and v["name_in_prompt"] in t["prompt"]
            if c["naming"] == "legacy":
                assert not v["name_in_prompt"].startswith("p.")
    assert n >= 20


def test_clinical_readme_gives_the_snapshot_date_and_no_stale_claim():
    text = (REPO / "tasks" / "mvs_clinical" / "README.md").read_text()
    assert V.clinvar_snapshot() in text
    assert "is split between public and held back" not in text


# --- follow-ups without a target (major) ------------------------------------------------

def test_the_start_state_never_gets_a_full_target_score_on_an_edit():
    """Returning the start state unchanged scored target 1.0 on 13 removal tasks."""
    n = 0
    for t in CORPUS:
        if not t["context"] or t["context"]["noop"]:
            continue
        start = t["context"].get("scene", t["context"].get("calls"))
        got = runner.grade_parsed(t, start)
        assert not got["success"], t["id"]
        if t["target"] is None:
            n += 1
            assert got["target_f1"] is None, t["id"]
        else:
            assert got["target_f1"] < 1.0, t["id"]
    assert n >= 13


# --- grounded tier (minors) -------------------------------------------------------------

def test_annotation_tasks_of_the_grounded_tier_are_flagged():
    for t in ORIGINALS:
        if t["family"] in ("gr-longest-helix", "gr-secstruct"):
            assert "helix and strand records" in t["provenance"]["report_apart"], t["id"]


def test_the_named_ligand_is_part_of_the_target():
    t = BY_ID["gr-attachment-1c3w-ret"]
    assert len(t["target"]) == 2
    scene = copy.deepcopy(t["reference"])
    root = mvs.extract_root(scene)
    for node in _walk(root):
        if node.get("kind") == "structure":
            node["children"] = [c for c in node["children"]
                                if c["params"].get("selector") != {"label_comp_id": "RET"}]
    got = runner.grade_parsed(t, scene)
    assert not got["success"] and got["target_f1"] < 1.0
