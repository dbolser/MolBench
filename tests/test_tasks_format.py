"""The task format (TASK_FORMAT.md, molbench/tasks.py): the schema every task file is
checked against at load, the adapter for old files, and the whole-corpus checks of
scripts/validate_tasks.py. Uses the fixture tasks, which are built by script from the
frozen panel (tests/fixtures/build_fixture_tasks.py)."""

import copy
import importlib.util
import json
import pathlib
import re

import pytest

from molbench import runner
from molbench import tasks as T

REPO = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "tasks"


def _script(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, REPO / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fixtures():
    return T.load_corpus(FIXTURES)


def _raw(tid: str) -> dict:
    return json.loads((FIXTURES / f"{tid}.json").read_text())


def _check(tasks):
    return T.check_corpus(tasks, grade=runner.grade_parsed)[0]


def _edited(fixtures, tid: str, **change) -> list[dict]:
    """The fixture corpus with one task changed (aliases kept in step)."""
    out = copy.deepcopy(fixtures)
    task = next(t for t in out if t["id"] == tid)
    task.update(change)
    T._with_aliases(task)
    return out


# --- the documents agree ------------------------------------------------------------

def test_the_format_document_names_every_field_tier_and_value():
    text = (REPO / "TASK_FORMAT.md").read_text()
    for name in T.REQUIRED + T.OPTIONAL + T.TIERS + T.STYLES + T.SPLITS + T.PROVENANCE_KEYS:
        assert f"`{name}`" in text, name
    assert f"Format version {T.FORMAT_VERSION}" in text


def test_fixture_files_are_what_their_builder_writes():
    assert _script("build_fixture_tasks", "tests/fixtures/build_fixture_tasks.py").main(["--check"]) == 0


# --- loading ------------------------------------------------------------------------

def test_fixtures_load_with_every_field_and_the_names_older_code_reads(fixtures):
    assert len(fixtures) >= 15
    for t in fixtures:
        assert set(T.REQUIRED) <= set(t) and t["_path"].startswith("tests/fixtures/tasks/")
        assert t["category"] == T.CATEGORY[t["track"]] and t["categories"] is t["skills"]
        assert len(t["_sha256"]) == 64
        assert ("reference_mvs" in t) == (t["track"] == "mvs")
        assert T.validate_task(t) == []
        assert T.cluster_key(t) == t["structures"][0]


def test_old_task_files_load_through_the_adapter():
    corpus = T.load_corpus()
    assert corpus and {t["track"] for t in corpus} == set(T.TRACKS)
    old = [t for t in corpus if t.get("_legacy")]
    for t in old:
        assert t["split"] == "public" and t["style"] == "full" and t["context"] is None
        assert t["structures"] == T.loaded_entries(t["track"], t["reference"])
    by_source = {t.get("source"): t["tier"] for t in old if t["track"] == "mvs"}
    for source, tier in by_source.items():
        assert tier == T.LEGACY_TIER[source]
    assert all(t["tier"] == T.LEGACY_API_TIER for t in old if t["track"] == "api")
    # The ungraded visual_rubric files are not tasks of either track.
    assert not any("vis-" in t["id"] for t in corpus)
    assert {t["id"] for t in runner.load_tasks(None)} > {t["id"] for t in corpus}


def test_tracks_filter_takes_either_name():
    assert T.load_corpus(FIXTURES, tracks=["api"]) == T.load_corpus(FIXTURES, tracks=["api_calling"])
    assert {t["track"] for t in T.load_corpus(FIXTURES, tracks=["mvs"])} == {"mvs"}


def test_a_bad_file_stops_the_load_and_names_the_file(tmp_path):
    good = _raw("fx-ligand-1cbs-mvs")
    (tmp_path / "a.json").write_text(json.dumps(good))
    (tmp_path / "b.json").write_text(json.dumps({**good, "tier": "easy"}))
    with pytest.raises(T.TaskError, match=r"b\.json: tier: one of"):
        T.load_corpus(tmp_path)
    (tmp_path / "b.json").write_text(json.dumps(good))
    with pytest.raises(T.TaskError, match="already used by"):
        T.load_corpus(tmp_path)
    (tmp_path / "b.json").write_text("{not json")
    with pytest.raises(T.TaskError, match="not valid JSON"):
        T.load_corpus(tmp_path)
    (tmp_path / "b.json").write_text(json.dumps({**good, "id": "x", "category": "mvs"}))
    with pytest.raises(T.TaskError, match="old format or the loader"):
        T.load_corpus(tmp_path)


# --- the schema ---------------------------------------------------------------------

CASES = [
    ("fx-ligand-1cbs-mvs", {"id": "has space"}, "id:"),
    ("fx-ligand-1cbs-mvs", {"track": "pymol"}, "track: one of"),
    ("fx-ligand-1cbs-mvs", {"tier": "hard"}, "tier: one of"),
    ("fx-ligand-1cbs-mvs", {"family": ""}, "family:"),
    ("fx-ligand-1cbs-mvs", {"prompt": "  "}, "prompt:"),
    ("fx-ligand-1cbs-mvs", {"reference": [{"action": "load", "molecule_id": "1cbs"}]},
     "reference: not an MVS scene"),
    ("fx-ligand-1cbs-api", {"reference": {"root": {"kind": "root"}}}, "reference: not a JSON array"),
    ("fx-ligand-1cbs-api", {"reference": [{"action": "fly"}]}, "unknown action 'fly'"),
    ("fx-ligand-1cbs-api", {"accepted": [[{"action": ["x"]}]]}, r"accepted\[0\]: malformed action"),
    ("fx-ligand-1cbs-mvs", {"structures": ["1CBS"]}, "structures: a list of distinct lower-case"),
    ("fx-ligand-1cbs-mvs", {"structures": ["1stp"]}, "is not what the reference loads"),
    ("fx-ligand-1cbs-mvs", {"context": {"scene": {"kind": "root"}}}, "context: null, or an object"),
    ("fx-ligand-1cbs-mvs", {"tier": "followup"}, "exactly the tasks with a context"),
    ("fx-follow-colour-1stp-api", {"tier": "translation"}, "exactly the tasks with a context"),
    ("fx-follow-colour-1stp-api", {"context": {"calls": [{"action": "fly"}], "noop": False}},
     r"context\.calls: .*unknown action"),
    ("fx-follow-colour-1stp-api", {"context": {"calls": [], "noop": "no"}}, "context.noop"),
    ("fx-ligand-1cbs-mvs", {"tier": "accept_set"}, "needs at least one accepted alternative"),
    ("fx-ligand-1cbs-mvs", {"tier": "tool_only"}, "API track only and has no twin"),
    ("fx-ligand-1cbs-mvs", {"target": []}, "target: null"),
    ("fx-ligand-1cbs-mvs", {"target": [{"representation": "cartoon"}]}, r"target\[0\]: an object with"),
    ("fx-ligand-1cbs-mvs", {"target": [{"selector": "polymer", "colour": "red"}]}, "unknown key"),
    ("fx-ligand-1cbs-mvs", {"target": [{"selector": "polymer", "structure": "1stp"}]},
     "is not one of the task's"),
    ("fx-anycopy-4ins-mvs", {"accepted_targets": []}, "one entry per accepted alternative"),
    ("fx-ligand-1cbs-mvs", {"twin_of": "fx-ligand-1cbs-mvs"}, "twin_of: null or the id of another"),
    ("fx-ligand-1cbs-mvs", {"style": "chatty"}, "style: one of"),
    ("fx-ligand-1cbs-mvs", {"style": "terse"}, "'terse' or 'indirect' on a paraphrase"),
    ("fx-ligand-terse-1stp-mvs", {"style": "full"}, "'full' on the original phrasing"),
    ("fx-ligand-1cbs-mvs", {"split": "test"}, "split: one of"),
    ("fx-ligand-1cbs-mvs", {"grounding": {"rule": "r6-v1", "text": ""}}, "grounding: null, or"),
    ("fx-ligand-1cbs-mvs", {"skills": []}, "skills: at least one"),
    ("fx-ligand-1cbs-mvs", {"provenance": {"script": "x.py"}}, "provenance: an object with"),
    ("fx-ligand-1cbs-mvs", {"provenance": {"script": "x.py", "inputs": ["a"], "date": "12 Nov",
                                           "checks": ["c"]}}, "provenance.date"),
    ("fx-ligand-1cbs-mvs", {"provenance": {"script": "x.py", "inputs": ["a"],
                                           "date": "2026-11-12", "checks": []}}, "provenance.checks"),
    ("fx-ligand-1cbs-mvs", {"difficulty_guess": 3}, "unknown field"),
]


@pytest.mark.parametrize("tid, change, message", CASES,
                         ids=[f"{c[0]}:{c[2][:28]}" for c in CASES])
def test_the_schema_rejects(tid, change, message):
    errors = T.validate_task({**_raw(tid), **change})
    assert any(re.search(message, e) for e in errors), errors


def test_every_field_is_required_even_when_null():
    for field in T.REQUIRED:
        task = _raw("fx-ligand-1cbs-mvs")
        del task[field]
        assert T.validate_task(task) == [f"missing field(s): ['{field}']"]


# --- what a reference loads ---------------------------------------------------------

def test_loaded_entries_reads_both_tracks():
    scene = _raw("fx-ligand-1cbs-mvs")["reference"]
    assert T.loaded_entries("mvs", scene) == ["1cbs"]
    assert T.loaded_entries("api", [{"action": "load", "molecule_id": "1CBS"}]) == ["1cbs"]
    alphafold = [{"action": "load", "custom_data": {
        "url": "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v6.cif", "format": "cif"}}]
    assert T.loaded_entries("api", alphafold) == ["af-p04637-f1"]
    assert T.resolve_entry("af-p04637-f1", T.panel_ids()) == "af-p04637-f1-model_v6"
    assert T.has_table("af-p04637-f1") and T.table_for("af-p04637-f1") is not None
    superposition = [{"action": "load", "molecule_id": "P69905"},
                     {"action": "set_property", "name": "superposition", "value": True}]
    assert T.loaded_entries("api", superposition) == []       # a UniProt accession
    assert not T.has_table("9zzz") and T.resolve_entry("9zzz", T.panel_ids()) is None


def test_twins_select_the_same_target_atoms(fixtures):
    by_id = {t["id"]: t for t in fixtures}
    pairs = [(t, by_id[t["twin_of"]]) for t in fixtures if t["twin_of"] and t["track"] == "mvs"]
    assert len(pairs) >= 5
    for mvs, api in pairs:
        atoms = T.target_atoms(mvs)
        assert atoms == T.target_atoms(api) and all(atoms.values())
        assert mvs["prompt"] == api["prompt"] and api["twin_of"] == mvs["id"]


# --- whole-corpus checks ------------------------------------------------------------

def test_the_fixture_corpus_and_the_real_corpus_pass(fixtures):
    assert _check(fixtures) == []
    errors, notes = T.check_corpus(T.load_corpus(), grade=runner.grade_parsed)
    assert errors == []
    validate = _script("validate_tasks", "scripts/validate_tasks.py")
    assert validate.main([]) == 0 and validate.main([str(FIXTURES)]) == 0


def test_final_refuses_old_format_tasks():
    errors, _ = T.check_corpus(T.load_corpus(), grade=None, final=True)
    assert any("old format" in e for e in errors)


BROKEN = [
    ("fx-ligand-1cbs-mvs", {"twin_of": None}, "twin_of is not mutual"),
    ("fx-ligand-1cbs-mvs", {"twin_of": "nobody"}, "twin_of 'nobody' is not a task"),
    ("fx-ligand-1cbs-mvs", {"twin_of": "fx-ligand-1stp-mvs"}, "twins are on the same track"),
    ("fx-ligand-1cbs-mvs", {"prompt": "Load 1CBS."}, "twins differ in prompt"),
    ("fx-ligand-1cbs-mvs", {"target": [{"selector": "polymer", "representation": "cartoon",
                                        "color": None}]}, "twins do not have the same target atoms"),
    ("fx-ligand-1cbs-mvs", {"target": [{"selector": {"label_comp_id": "XXX"}}]},
     "a part of target selects no atoms"),
    ("fx-ligand-terse-1stp-mvs", {"paraphrase_of": "nobody"}, "paraphrase_of is not a task"),
    ("fx-ligand-terse-1stp-mvs", {"split": "heldback"}, "differs from its original in split"),
    ("fx-ligand-terse-1stp-mvs", {"paraphrase_of": "fx-ligand-indirect-1stp-mvs"},
     "must name the original"),
    ("fx-ligand-1cbs-mvs", {"split": "heldback"}, "used by both the public and the held-back"),
    ("fx-ligand-1cbs-mvs", {"provenance": {"script": "scripts/no_such.py", "inputs": ["x"],
                                           "date": "2026-11-12", "checks": ["x"]}},
     "is not a file in the repo"),
    ("fx-follow-colour-1stp-api", {"context": {"calls": [{"action": "load", "molecule_id": "1stp"}],
                                               "noop": True}},
     "context.noop is True but the start state is not"),
    ("fx-follow-noop-1cbs-mvs", {"context": {"scene": None, "noop": False}}, None),
]


@pytest.mark.parametrize("tid, change, message", BROKEN[:-1],
                         ids=[c[2][:40] for c in BROKEN[:-1]])
def test_the_corpus_checks_catch(fixtures, tid, change, message):
    errors = _check(_edited(fixtures, tid, **change))
    assert any(message in e for e in errors), errors


def test_a_wrong_noop_flag_is_caught_both_ways(fixtures):
    task = next(t for t in fixtures if t["id"] == "fx-follow-noop-1cbs-mvs")
    flipped = {**task["context"], "noop": False}
    errors = _check(_edited(fixtures, task["id"], context=flipped))
    assert any("context.noop is False but the start state already is" in e for e in errors)


def test_a_structure_outside_the_panel_or_the_worked_example_is_caught(fixtures):
    scene = json.loads(json.dumps(_raw("fx-ligand-1cbs-mvs")["reference"]).replace("1cbs", "1hsg"))
    errors = _check(_edited(fixtures, "fx-ligand-1cbs-mvs", reference=scene, structures=["1hsg"]))
    assert any("uses 1HSG, the API prompt's worked example" in e for e in errors)
    errors = _check(_edited(fixtures, "fx-ligand-1cbs-mvs", structures=["9zzz"]))
    assert any("'9zzz' is not in the panel" in e for e in errors)
    said = _edited(fixtures, "fx-ligand-1cbs-mvs", prompt="As in 1HSG, show the ligand.")
    assert any("uses 1HSG" in e for e in _check(said))
    assert not T._mentions_worked_example({"prompt": "the 21hsgx set"})


def test_a_reference_or_alternative_that_is_not_right_is_caught(fixtures):
    # An accept-set alternative that is the reference again adds nothing.
    task = _raw("fx-anycopy-4ins-mvs")
    errors = _check(_edited(fixtures, task["id"], accepted=[task["reference"]]))
    assert any("accepted[0] is the same final state as the reference" in e for e in errors)

    def reference_wrong(t, answer):
        res = runner.grade_parsed(t, answer)
        return {**res, "f1": 0.8, "success": False} if t["id"] == "fx-ligand-1cbs-api" else res

    errors, _ = T.check_corpus(fixtures, grade=reference_wrong)
    assert errors == ["fx-ligand-1cbs-api: its own reference does not grade as exactly right "
                      "(f1 0.8, success False)"]

    def off_target(t, answer):
        return {**runner.grade_parsed(t, answer), "target_f1": 0.5}

    errors, _ = T.check_corpus(fixtures[:1], grade=off_target)
    assert any("has target score 0.5" in e for e in errors)
    errors, notes = T.check_corpus(fixtures, grade=None)
    assert errors == [] and any("self-grading checks skipped" in n for n in notes)
