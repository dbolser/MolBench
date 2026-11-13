"""The grader control set (plan gap G3): the grader's own error rate, kept at zero.

``tests/controls/{mvs,api}.jsonl`` are (reference, answer) pairs with a known verdict,
built by ``scripts/grader_controls.py`` from the frozen structure panel. These tests
re-grade every pair, check the files are what the builder produces today, and check
that ``summary.json`` (the numbers the paper quotes) says what the grader does.
"""

import importlib.util
import json
import pathlib

import pytest

from molbench import grader

REPO = pathlib.Path(__file__).resolve().parent.parent
CONTROLS = REPO / "tests" / "controls"

_spec = importlib.util.spec_from_file_location("grader_controls", REPO / "scripts" / "grader_controls.py")
gc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gc)

# The wrong answers the plan names (G3); each must be a kind in the set, on both tracks.
REQUIRED_WRONG = {
    "mvs": {"residue_off_by_one", "wrong_chain", "label_number_as_author_number", "wrong_colour",
            "wrong_representation", "missing_component", "extra_component", "wrong_ligand_copy",
            "wrong_entry", "uniprot_number_as_author_number"},
    "api": {"residue_off_by_one", "wrong_chain", "author_number_as_label_number", "wrong_colour",
            "wrong_representation", "missing_step", "extra_step", "wrong_ligand_copy",
            "wrong_entry", "uniprot_number_as_author_number"},
}


@pytest.fixture(scope="module")
def controls():
    return {track: gc.load_controls(track) for track in ("mvs", "api")}


@pytest.fixture(scope="module")
def built():
    return gc.build()


@pytest.mark.parametrize("track", ["mvs", "api"])
def test_every_control_gets_its_verdict(controls, track):
    wrong = []
    for c in controls[track]:
        r = grader.grade_task(gc.as_task(c), c["prediction"])
        want = c["expect"] == "pass"
        if bool(r["success"]) != want:
            wrong.append((c["id"], c["expect"], r["f1"]))
        elif want and (r["f1"] != 1.0 or r["target_f1"] != 1.0):
            wrong.append((c["id"], "a pass must score f1 = target_f1 = 1", r["f1"], r["target_f1"]))
        elif not want and r["f1"] >= 1.0:
            wrong.append((c["id"], "a fail must score f1 < 1", r["f1"]))
    assert not wrong, wrong[:10]


@pytest.mark.parametrize("track", ["mvs", "api"])
def test_the_set_is_as_wide_as_the_plan_asks(controls, track):
    ctls = controls[track]
    kinds = {g: {c["kind"] for c in ctls if c["group"] == g} for g in ("equivalent", "wrong")}
    assert len(kinds["equivalent"]) >= 12 and len(kinds["wrong"]) >= 10
    assert REQUIRED_WRONG[track] <= kinds["wrong"], REQUIRED_WRONG[track] - kinds["wrong"]
    assert sum(c["group"] == "identical" for c in ctls) >= 100
    per_kind: dict[str, int] = {}
    for c in ctls:
        if c["group"] != "identical":
            per_kind[c["kind"]] = per_kind.get(c["kind"], 0) + 1
    assert min(per_kind.values()) >= 8, {k: v for k, v in per_kind.items() if v < 8}
    assert len({c["entry"] for c in ctls}) >= 50
    assert not any(c["entry"] == "1hsg" for c in ctls)      # the API prompt's worked example
    assert len({c["id"] for c in ctls}) == len(ctls)
    for c in ctls:                                           # a rewrite is a rewrite, not a copy
        if c["group"] == "equivalent":
            assert c["reference"] != c["prediction"], c["id"]


def test_files_on_disk_are_what_the_builder_makes(controls, built):
    for track in ("mvs", "api"):
        assert gc.dump_jsonl(built[track]) == (CONTROLS / f"{track}.jsonl").read_text(), \
            f"tests/controls/{track}.jsonl is stale: run scripts/grader_controls.py"


def test_summary_is_what_the_grader_does_today(built):
    on_disk = json.loads((CONTROLS / "summary.json").read_text())
    assert on_disk == json.loads(json.dumps(gc.summarise(built))), \
        "tests/controls/summary.json is stale: run scripts/grader_controls.py"
    for track, s in on_disk["tracks"].items():
        assert s["grader"]["false_pass"]["errors"] == 0, track
        assert s["grader"]["false_fail"]["errors"] == 0, track
        assert s["mistakes"] == []
        assert s["grader"]["false_pass"]["n"] == s["n_wrong"] >= 200
        assert s["grader"]["false_fail"]["n"] == s["n_identical"] + s["n_equivalent"] >= 400


def test_the_previous_graders_do_make_these_mistakes():
    """The set is not vacuous: the graders it replaces fail it in the expected way (the
    October path grader rejects equivalent scenes; the July sequence grader also
    accepts wrong call lists)."""
    s = json.loads((CONTROLS / "summary.json").read_text())["tracks"]
    assert s["mvs"]["previous_grader"]["false_fail"]["errors"] > 100
    assert s["api"]["previous_grader"]["false_fail"]["errors"] > 100
    assert s["api"]["previous_grader"]["false_pass"]["errors"] > 20


def test_the_viewer_check_on_record_found_no_disagreement():
    """``--viewer`` needs a browser, so it is not run here; its last result is on
    record. It must be clean: every checked MVS verdict is what Mol* draws, every
    checked scene resolves to the state Mol* reports, and every representation type
    draws the atoms the grader says, on every panel entry."""
    path = CONTROLS / "viewer_check.json"
    if not path.exists():
        pytest.skip("no viewer check on record")
    report = json.loads(path.read_text())
    m = report["mvs"]
    assert m["controls_checked"] >= 800
    assert m["verdict_agrees"] == m["controls_checked"]
    assert m["scenes_checked"] >= 1400 and m["grader_state_agrees"] == m["scenes_checked"]
    assert m["problems"] == []
    rules = m["rule_probes"]
    assert rules["entries"] == 75 and rules["differ"] == []
    assert rules["agree"] == rules["draws_compared"] >= 3500
    api = report["api"]
    assert api["lists_run"] >= 100
    assert api["problems"] == [] and api["agree"] == api["lists_run"]
    bare = api["bare_loads"]
    assert bare["entries"] >= 70
    assert bare["differ"] == [] and bare["agree"] == bare["entries"]


def test_october_regrade_reproduces_the_stored_october_f1():
    path = CONTROLS / "october_regrade.json"
    if not path.exists():
        pytest.skip("no October regrade on record")
    spec = json.loads(path.read_text())["conditions"]["spec"]
    assert spec["all"]["n"] == 1050
    # the kept October grader, run today, gives the F1 stored in October ...
    assert abs(spec["all"]["old_f1"] - spec["all"]["old_f1_stored"]) < 0.001
    for m in spec["by_model"].values():
        assert abs(m["old_f1"] - m["old_f1_stored"]) < 0.005
        # ... and success can never exceed the share of valid scenes
        assert m["success"] <= m["valid"] / m["n"] + 1e-9
        assert m["success_if_any_focus_counts"] <= m["success"] + 1e-9


def test_grading_md_quotes_the_current_numbers(built):
    """GRADING.md carries the control-set table that the paper lifts; it must be the
    one in summary.json."""
    text = (REPO / "GRADING.md").read_text()
    for track, s in json.loads((CONTROLS / "summary.json").read_text())["tracks"].items():
        g, old = s["grader"], s["previous_grader"]
        n_pass = s["n_identical"] + s["n_equivalent"]
        row = (f"| {s['n_controls']:,} on {s['n_entries']} entries | {s['n_equivalent_kinds']} / "
               f"{s['n_wrong_kinds']} | {g['false_pass']['errors']} of {s['n_wrong']} | "
               f"{g['false_fail']['errors']} of {n_pass} | {old['false_pass']['errors']} of "
               f"{s['n_wrong']} / {old['false_fail']['errors']} of {n_pass} ")
        assert row in text, (track, row)
