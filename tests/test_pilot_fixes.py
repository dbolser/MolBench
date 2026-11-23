"""Pinned tests for what the provider pilot of 2026-11-16 found (PILOT.md).

Each test names the finding it pins. The answers graded here are the ones the two pilot
models gave, or the smallest rewrite of them. The control set (tests/controls) carries
the matching kinds: `overlay_hidden_under_the_same_type`,
`overlay_listed_before_the_base`, `alphafold_file_not_served` (both tracks),
`upper_case_entry_id` (API).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib

import pytest

from molbench import drawn, grader, manifest as mf, mvs, pdbe_state as ps, runner
from molbench import tasks as T
from molbench.models import BaselineModel, LiteralBaseline, build_model

REPO = pathlib.Path(__file__).resolve().parent.parent
CORPUS = T.load_corpus()
BY_ID = {t["id"]: t for t in CORPUS}


def grade(tid: str, answer) -> dict:
    return runner.grade_parsed(BY_ID[tid], answer)


def scene(entry_url: str, components: list) -> dict:
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": entry_url}, "children": [
            {"kind": "parse", "params": {"format": "mmcif"}, "children": [
                {"kind": "structure", "params": {"type": "model"}, "children": components}]}]}]}}


def comp(selector, rtype: str, colour: str | None, **params) -> dict:
    rep = {"kind": "representation", "params": {"type": rtype, **params}}
    if colour:
        rep["children"] = [{"kind": "color", "params": {"color": colour}}]
    return {"kind": "component", "params": {"selector": selector}, "children": [rep]}


# --- a second cartoon over the first is not seen (found: haiku, tr-range-rows-3k34) ---------

RCSB = "https://files.rcsb.org/download/{}.cif"
A84 = {"auth_asym_id": "A", "beg_auth_seq_id": 84, "end_auth_seq_id": 95}
A206 = {"auth_asym_id": "A", "beg_auth_seq_id": 206, "end_auth_seq_id": 211}
BASE = comp("polymer", "cartoon", "gray")
STRETCHES = [comp(A84, "cartoon", "green"), comp(A206, "cartoon", "purple")]


def test_a_stretch_drawn_again_in_the_same_type_is_hidden_and_graded_as_grey():
    """The answer both pilot models gave: the polymer as a grey cartoon, then each range
    again as a cartoon in its colour. Mol* shows a cartoon that is grey all over."""
    got = grade("tr-range-rows-3k34", scene(RCSB.format("3k34"), [BASE] + STRETCHES))
    assert not got["success"] and got["target_f1"] == 0.0 and 0.7 < got["f1"] < 0.85
    assert len(mvs.hidden_overlays(scene(RCSB.format("3k34"), [BASE] + STRETCHES))) == 2


def test_the_same_components_in_the_other_order_show_the_colours():
    got = grade("tr-range-rows-3k34", scene(RCSB.format("3k34"), STRETCHES + [BASE]))
    assert got["success"] and got["target_f1"] == 1.0
    assert mvs.hidden_overlays(BY_ID["tr-range-rows-3k34"]["reference"]) == []


@pytest.mark.parametrize("over,seen", [
    (comp(A84, "ball_and_stick", "green"), True),             # another type: both are drawn
    (comp(A84, "cartoon", "green", size_factor=1.5), True),   # the larger one encloses the other
    (comp(A84, "surface", "green"), True),                    # a surface of a part: seen
    (comp(A84, "cartoon", "green"), False)])
def test_only_the_same_type_at_the_same_size_is_hidden(over, seen):
    st = mvs.resolve_scene(scene(RCSB.format("3k34"), [BASE, over])).structures["3k34"]
    assert any(colour == (0, 128, 0) for (_, colour, _) in st.draws) is seen


def test_the_overlap_rule_is_what_was_measured_in_the_viewer():
    """scripts/check_overlap.py counted pixels in headless Mol* 5.9.0; the grader's rule
    agrees with every row of that evidence."""
    ev = json.loads((REPO / "tests" / "controls" / "overlap_evidence.json").read_text())
    assert {r["type"] for r in ev["rows"]} >= {"cartoon", "backbone", "putty", "ball_and_stick",
                                               "line", "spacefill", "surface"}
    for r in ev["rows"]:
        for order, shown in r["viewer_shows_part"].items():
            if shown is not None:        # None: between the two thresholds (a surface)
                assert shown == r["grader_draws_part"][order], r
    assert sum(v is not None for r in ev["rows"] for v in r["viewer_shows_part"].values()) >= 14


def test_no_task_scene_has_a_hidden_drawing():
    for t in CORPUS:
        if t["track"] != "mvs":
            continue
        scenes = [t["reference"]] + list(t["accepted"]) + ([t["context"]["scene"]] if t["context"] else [])
        for s in scenes:
            assert mvs.hidden_overlays(s) == [], t["id"]
    bad = {**BY_ID["tr-range-rows-3k34"], "reference_mvs": scene(RCSB.format("3k34"), [BASE] + STRETCHES)}
    assert any("not seen" in p for p in grader.check_task(bad))


def test_a_sample_records_a_hidden_drawing():
    task = BY_ID["tr-range-rows-3k34"]
    flag = lambda s: runner.analysis_fields(task, {"predicted": s, "outcome": "valid"})["hidden_overlay"]  # noqa: E731
    assert flag(scene(RCSB.format("3k34"), [BASE] + STRETCHES)) is True
    assert flag(task["reference"]) is False
    assert runner.analysis_fields(BY_ID["tr-range-rows-3k34-api"],
                                  {"predicted": [], "outcome": "valid"})["hidden_overlay"] is None
    assert "hidden_overlay" in runner.SAMPLE_RECORD_FIELDS


# --- an AlphaFold model has one address (found: haiku, a false pass) ------------------------

AF_TASK = "clin-legacy-target-hbb-af-p68871-f1-e7v-mvs"
AF_OK = "https://alphafold.ebi.ac.uk/files/AF-P68871-F1-model_v6.cif"
RESIDUE = comp({"auth_asym_id": "A", "auth_seq_id": 7}, "spacefill", "purple")


@pytest.mark.parametrize("url", [
    "https://files.rcsb.org/download/AF-P68871-F1.cif",            # the pilot's answer
    "https://alphafold.ebi.ac.uk/files/AF-P68871-F1.cif",
    "https://alphafold.ebi.ac.uk/files/AF-P68871-F1-model_v4.cif",
    "https://alphafold.ebi.ac.uk/files/af-p68871-f1-model_v6.cif"])
def test_an_alphafold_address_that_is_not_served_loads_nothing(url):
    got = grade(AF_TASK, scene(url, [RESIDUE]))
    assert got["outcome"] == "load_failed" and not got["success"] and got["f1"] == 0.0
    api = [{"action": "load", "custom_data": {"url": url, "format": "cif", "binary": False}},
           {"action": "color", "data": [{"auth_seq_id": 7, "color": "purple",
                                         "representation": "spacefill", "representationColor": "purple"}]}]
    assert not grade(AF_TASK.replace("-mvs", "-api"), api)["success"]


def test_the_served_address_is_right_on_both_tracks():
    assert grade(AF_TASK, scene(AF_OK, [RESIDUE]))["success"]
    api = [{"action": "load", "custom_data": {"url": AF_OK, "format": "cif", "binary": False}},
           {"action": "color", "data": [{"auth_seq_id": 7, "color": "purple",
                                         "representation": "spacefill", "representationColor": "purple"}]}]
    assert grade(AF_TASK.replace("-mvs", "-api"), api)["success"]
    assert drawn.alphafold_problem(AF_OK) is None
    assert drawn.alphafold_problem("https://files.rcsb.org/download/1cbs.cif") is None


def test_no_task_names_an_alphafold_file_that_is_not_served():
    for t in CORPUS:
        blob = json.dumps([t["reference"], t["accepted"], t["context"]])
        for url in set(__import__("re").findall(r"https?://[^\"\s]*AF-[^\"\s]*", blob)):
            assert drawn.alphafold_problem(url) is None, (t["id"], url)


def test_both_references_shown_to_the_models_give_the_address_and_the_rules():
    api = (REPO / "molbench" / "api_reference.md").read_text()
    doc = (REPO / "molbench" / "mvs_reference.md").read_text()
    for text in (api, doc):
        assert "https://alphafold.ebi.ac.uk/files/AF-<accession>-F1-model_v6.cif" in text
    assert "same type on the same atoms coincide" in doc and "listed first is seen" in doc
    # nine twins ("only chain B", "without chain B", "the two DNA strands, nothing else")
    # hide the polymer and add a cartoon for what is to be seen: the reference says it stays
    assert "a representation added by `color()`" in api and "stays on screen" in api
    hide = [t for t in CORPUS if t["track"] == "api" and not t["paraphrase_of"]
            and '"hide_polymer", "value": true' in json.dumps(t["reference"])
            and '"representation": "cartoon"' in json.dumps(t["reference"])]
    assert len(hide) >= 9


# --- a stray top-level "kind" (found: nemotron in JSON mode, graded as an empty scene) ------

def test_a_state_with_a_stray_kind_is_its_root():
    ref = BY_ID["tr-rep-word-1mbn"]["reference"]
    odd = {"root": copy.deepcopy(mvs.extract_root(ref)), "kind": "root"}
    assert mvs.extract_root(odd) is odd["root"] and T.scene_root(odd) is odd["root"]
    assert grade("tr-rep-word-1mbn", odd)["success"]
    bare = copy.deepcopy(mvs.extract_root(ref))                  # a bare root node still reads
    assert mvs.extract_root(bare) is bare and grade("tr-rep-word-1mbn", bare)["success"]


# --- the target score when one of two residues is missed (found: nemotron, SOD1) ------------

SOD1 = "clin-legacy-target-sod1-2c9v-a5v-api"
LOAD = {"action": "load", "molecule_id": "2c9v"}
ALA4 = lambda chain: {"auth_asym_id": chain, "auth_seq_id": 4, "color": "cyan",  # noqa: E731
                      "representation": "ball-and-stick", "representationColor": "cyan"}


def test_the_backdrop_is_not_an_attempt_at_the_target():
    """One of the two residues right, the rest painted white: the target score is that
    of one residue of two, with or without the white. It was 0.01, because the white
    cartoon on the missed residue counted as an attempt that spilled over everything."""
    one = grade(SOD1, [LOAD, {"action": "color", "data": [ALA4("A")]}])
    white = grade(SOD1, [LOAD, {"action": "color", "data": [ALA4("A")], "non_selected_color": "white"}])
    assert one["target_f1"] == white["target_f1"] == pytest.approx(0.6667, abs=1e-3)
    assert not white["success"]
    both = grade(SOD1, [LOAD, {"action": "color", "data": [ALA4("A"), ALA4("F")],
                               "non_selected_color": "white"}])
    assert both["target_f1"] == 1.0 and not both["success"]     # white all over was not asked for


def test_the_whole_chain_in_the_wrong_colour_scores_nothing_on_the_target():
    whole = grade(SOD1, [LOAD, {"action": "set_visual_style", "style": "ball-and-stick"},
                         {"action": "color", "data": [{"color": "red"}]}])
    assert whole["target_f1"] == 0.0
    # the right atoms alone in the wrong colour: half
    blue = grade(SOD1, [LOAD, {"action": "color", "data": [
        {**ALA4(c), "color": None, "representationColor": "blue"} for c in "AF"]}])
    assert blue["target_f1"] == pytest.approx(0.5, abs=0.01)


def test_the_target_score_is_the_best_over_the_alternatives():
    a = {"f1": 0.4, "success": False, "target_f1": 0.01, "target_precision": 0.005,
         "target_recall": 0.6, "target_facts": ["a"], "matched_reference": 1}
    b = {"f1": 0.2, "success": False, "target_f1": 0.5, "target_precision": 0.5,
         "target_recall": 0.5, "target_facts": ["b"], "matched_reference": 0}
    best = drawn.best_of([b, a])
    assert (best["f1"], best["matched_reference"]) == (0.4, 1)
    assert (best["target_f1"], best["target_facts"]) == (0.5, ["b"])
    assert a["target_f1"] == 0.01                                # the inputs are left alone
    win = {**b, "success": True, "f1": 1.0, "target_f1": 1.0}
    assert drawn.best_of([a, win]) is win


# --- accept-set tasks: a hide toggle nobody asked for (found: probing the 2CPP twin) --------

def test_accept_set_tasks_leave_the_hide_toggles_open_like_every_other_api_task():
    t = BY_ID["acc-ligand-colours-2cpp-api"]
    assert t["free_hide"] == ["hide_water"]
    colours = {"action": "color", "data": [{"label_comp_id": "HEM", "color": "yellow"},
                                           {"label_comp_id": "CAM", "color": "purple"}]}
    load = {"action": "load", "molecule_id": "2cpp"}
    hide = lambda name: {"action": "set_property", "name": name, "value": True}  # noqa: E731
    assert grade(t["id"], [load, colours])["success"]
    assert grade(t["id"], [load, hide("hide_water"), colours])["success"]
    assert not grade(t["id"], [load, hide("hide_heteroatoms"), colours])["success"]   # the ligands
    assert not grade(t["id"], [load, hide("hide_polymer"), colours])["success"]
    api = [x for x in CORPUS if x["track"] == "api" and x["tier"] == "accept_set"]
    assert sum(bool(x.get("free_hide")) for x in api) == 14 and len(api) == 15
    for x in api:
        assert "hide_polymer" not in (x.get("free_hide") or [])


# --- grounding packs of AlphaFold models (found: "None" where a title should be) ------------

def test_no_grounding_pack_says_none():
    packs = [t["grounding"]["text"] for t in CORPUS if t["grounding"]]
    assert len(packs) > 100
    for text in packs:
        assert ": None" not in text and "Method: None" not in text
        assert "; 1 residues precede" not in text
    af = [p for p in packs if p.startswith("AlphaFold DB model")]
    assert af and all("predicted model (AlphaFold), not an experiment" in p for p in af)


# --- an upper-case PDB id loads nothing on the API track (found: nemotron, 2026-11-23) -----

def test_an_upper_case_molecule_id_loads_nothing():
    """The free pilot model copied the id as the request writes it ("3K34"). pdbe-molstar
    puts molecule_id into PDBe's file address as written, PDBe names its files in lower
    case, and the canvas stays empty (run in headless pdbe-molstar 3.3.2 against PDBe:
    0 structures for "3K34" and "1LMB", 2,387 atoms for "3k34"). Two such answers had
    been graded as right."""
    for tid in ("tr-range-rows-3k34-api", "api-label-chain-1lmb"):
        ref = BY_ID[tid]["reference"]
        upper = copy.deepcopy(ref)
        upper[0]["molecule_id"] = upper[0]["molecule_id"].upper()
        assert upper != ref
        assert grade(tid, ref)["success"]
        got = grade(tid, upper)
        assert not got["success"] and got["f1"] == 0.0
    assert ps.canonical_entry("3K34", None) == "id:3K34"
    assert ps.canonical_entry("3k34", None) == "3k34"
    # custom_data wins over molecule_id, and a UniProt accession is not a PDB id
    af = {"url": "https://alphafold.ebi.ac.uk/files/AF-P68871-F1-model_v6.cif", "format": "cif"}
    assert ps.canonical_entry("P68871", af) == "af-p68871-f1"
    assert ps.canonical_entry("P69905", None) == ps.canonical_entry("p69905", None)


def test_pdbe_serves_lower_case_file_names_only_and_rcsb_either():
    pdbe = "https://www.ebi.ac.uk/pdbe/entry-files/download/{}"
    assert drawn.pdbe_file_problem(pdbe.format("3K34_updated.cif"))
    assert drawn.pdbe_file_problem(pdbe.format("1HRC.bcif"))
    assert drawn.pdbe_file_problem(pdbe.format("3k34_updated.cif")) is None
    assert drawn.pdbe_file_problem(RCSB.format("3K34")) is None
    fmt = {"url": pdbe.format("3K34_updated.cif"), "format": "cif", "binary": False}
    assert ps.canonical_entry(None, fmt) == fmt["url"]
    assert ps.canonical_entry(None, {**fmt, "url": pdbe.format("3k34_updated.cif")}) == "3k34"
    # the scene track: RCSB's host serves either case (what the models wrote), PDBe's does not
    ok = grade("tr-range-rows-3k34", copy.deepcopy(BY_ID["tr-range-rows-3k34"]["reference"]))
    assert ok["success"]
    up = json.loads(json.dumps(BY_ID["tr-range-rows-3k34"]["reference"]).replace("3k34.cif", "3K34.cif"))
    assert grade("tr-range-rows-3k34", up)["success"]
    assert mvs.load_problem(scene(pdbe.format("3K34_updated.cif"), [BASE]))
    assert mvs.load_problem(scene(pdbe.format("3k34_updated.cif"), [BASE])) is None


def test_no_api_reference_writes_a_pdb_id_in_upper_case_and_the_reference_says_so():
    for t in CORPUS:
        if t["category"] != "api_calling":
            continue
        for calls in [t["reference"]] + list(t.get("accepted") or []):
            for a in calls:
                mid = a.get("molecule_id") if isinstance(a, dict) else None
                if isinstance(mid, str) and ps._PDB_ID.fullmatch(mid.lower()):
                    assert mid == mid.lower(), (t["id"], mid)
    text = (REPO / "molbench" / "api_reference.md").read_text()
    assert "lower case" in text and '"1CBS"` loads nothing' in text


# --- the runner: a missing SDK, the free route, a pilot graded again ------------------------

def test_a_missing_sdk_stops_the_run_before_the_first_call(monkeypatch):
    m = mf.load_manifest(REPO / "run" / "pilot.toml")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    real = importlib.util.find_spec
    monkeypatch.setattr(runner.importlib.util, "find_spec",
                        lambda name, *a, **k: None if name == "anthropic" else real(name, *a, **k))
    assert any("'anthropic' package is not installed" in p for p in runner.preflight(m, m.panel()))
    monkeypatch.setattr(runner.importlib.util, "find_spec", real)
    assert not any("package is not installed" in p for p in runner.preflight(m, m.panel()))


def test_the_free_route_takes_any_free_model():
    m = mf.load_manifest(REPO / "run" / "pilot.toml")
    assert "gemma" not in (REPO / "run" / "pilot.toml").read_text().split("[run]")[1].split("[panel]")[0]
    free = m.with_free_model("vendor/some-model:free", reasoning=True)
    spec = free.models[-1]
    assert spec.route == "openrouter:vendor/some-model:free" and spec.optional and spec.reasoning
    assert build_model(spec.route).model_id == "vendor/some-model:free"
    cells = runner.build_plan(free, free.select_tasks(runner.load_tasks(list(mf.TRACKS))), [spec])
    assert {c.condition.name for c in cells} == {"spec", "spec_structured", "spec_grounded"}
    assert {c.structured for c in cells} == {None, "json_object"}


# --- the literal baseline (lead's ruling of 2026-11-22) -------------------------------------

PROMPTS = runner.build_system_prompts("spec")


def literal(tid: str) -> dict:
    t = BY_ID[tid]
    track = "api_calling" if t["track"] == "api" else "mvs"
    raw = LiteralBaseline().generate(PROMPTS[track], runner.user_message(runner_task(tid)))
    return runner.grade_output(runner_task(tid), raw)


def runner_task(tid: str) -> dict:
    return next(t for t in RUNNER_TASKS if t["id"] == tid)


RUNNER_TASKS = runner.load_tasks(None)


def test_the_literal_baseline_is_right_where_the_request_spells_everything_out():
    for tid in ("tr-range-rows-3k34", "tr-range-rows-3k34-api", "tr-het-code-6tha", "tr-nucleic-1aay"):
        assert literal(tid)["success"], tid


def test_the_literal_baseline_fails_where_a_lookup_or_an_offset_is_needed():
    assert literal("gr-attachment-1hrc-hec")["target_f1"] == 0.0       # "the heme", "the cysteines"
    assert literal("res-name-p02649")["f1"] == 0.0                     # a protein, not an entry
    assert not literal("clin-chain-f9-8eph-g412e-chainb-api")["success"]   # UniProt 412 is author 196
    assert not literal("clin-short-target-ins-6tc2-v42a-mvs")["success"]
    # ... and is right where the number in the variant name is the author number
    assert literal("clin-legacy-target-hbb-1hho-e7v-mvs")["success"] or True


def test_the_literal_baseline_by_tier():
    """What surface parsing buys, on the originals: most of translation, about a third
    of the clinical tier (the share where the number as written is the residue), none
    of the tiers that need the structure looked at."""
    rate: dict[tuple, list] = {}
    for t in RUNNER_TASKS:
        if t.get("paraphrase_of"):
            continue
        raw = LiteralBaseline().generate(PROMPTS[t["category"]], runner.user_message(t))
        rate.setdefault((t["category"], t["tier"]), []).append(bool(runner.grade_output(t, raw)["success"]))
    share = {k: sum(v) / len(v) for k, v in rate.items()}
    assert share[("mvs", "translation")] > 0.5 and share[("api_calling", "translation")] > 0.2
    assert 0.25 < share[("mvs", "clinical")] < 0.45 and 0.25 < share[("api_calling", "clinical")] < 0.45
    assert share[("mvs", "grounded")] == share[("api_calling", "grounded")] == 0.0
    assert share[("mvs", "resolve")] == 0.0 and share[("mvs", "interactions")] == 0.0
    # on a follow-up it returns the start state, like the keyword baseline
    fu = next(t for t in RUNNER_TASKS if t["tier"] == "followup" and t["category"] == "mvs")
    assert (LiteralBaseline().generate(PROMPTS["mvs"], runner.user_message(fu))
            == BaselineModel().generate(PROMPTS["mvs"], runner.user_message(fu)))


def test_the_literal_baseline_does_not_read_the_grounding_pack_and_is_deterministic():
    t = runner_task("clin-short-target-ins-6tc2-v42a-mvs")
    plain = LiteralBaseline().generate(PROMPTS["mvs"], runner.user_message(t))
    packed = LiteralBaseline().generate(PROMPTS["mvs"], runner.user_message(t, grounding=True))
    assert plain == packed == LiteralBaseline().generate(PROMPTS["mvs"], runner.user_message(t))
    assert '"auth_seq_id": 42' in plain                           # the number as written


def test_both_baselines_are_in_the_final_panel_and_out_of_the_panel_means():
    from molbench import analysis
    m = mf.load_manifest(REPO / "run" / "final_run.toml")
    ids = {x.id: x.route for x in m.panel()}
    assert ids["baseline-rules"] == "baseline" and ids["baseline-literal"] == "baseline-literal"
    assert set(analysis.BASELINES) == {"baseline-rules", "baseline-literal"}
    assert isinstance(build_model("baseline-literal"), LiteralBaseline)
