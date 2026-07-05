"""
Calibration / sanity tests for the harness itself.

These don't test a model — they test that the *measuring instrument* is sound:

* Every reference answer in the corpus is schema-valid (catches task typos).
* Grading a reference against itself yields F1 == 1.0 (the grader's ceiling is real).
* A clearly-wrong prediction scores low (the grader's floor discriminates).

Run: ``python -m pytest tests/`` or just ``python tests/test_harness.py``.
"""

from __future__ import annotations

import json
import pathlib

from molbench import grader, mvs, schema
from molbench.runner import load_tasks


def test_all_reference_answers_are_schema_valid():
    for task in load_tasks(["api_calling"]):
        errors = schema.validate_actions(task["reference"])
        assert not errors, f"{task['id']} reference invalid: {errors}"


def test_self_grading_is_perfect():
    for task in load_tasks(["api_calling"]):
        result = grader.grade(task["reference"], task["reference"])
        assert result["f1"] == 1.0, f"{task['id']} self-F1={result['f1']} (expected 1.0)"


def test_wrong_prediction_scores_low():
    ref = [{"action": "load", "molecule_id": "1hho"},
           {"action": "set_visual_style", "style": "cartoon"}]
    wrong = [{"action": "load", "molecule_id": "9zzz"},
             {"action": "set_property", "name": "spin", "value": True}]
    assert grader.grade(ref, wrong)["f1"] < 0.3


def test_partial_credit_for_right_residues_wrong_colour():
    ref = [{"action": "color", "data": [
        {"auth_asym_id": "A", "residue_number": 35, "color": {"r": 255, "g": 0, "b": 0}}]}]
    pred = [{"action": "color", "data": [
        {"auth_asym_id": "A", "residue_number": 35, "color": {"r": 0, "g": 0, "b": 255}}]}]
    f1 = grader.grade(ref, pred)["f1"]
    assert 0.6 < f1 < 1.0, f"expected partial credit, got {f1}"


def test_load_modifiers_are_scored():
    # A task about loading a specific assembly must not be satisfied by a bare load.
    ref = [{"action": "load", "molecule_id": "6vxx", "assembly_id": "1"}]
    assert grader.grade(ref, ref)["f1"] == 1.0
    bare = [{"action": "load", "molecule_id": "6vxx"}]
    assert grader.grade(ref, bare)["f1"] < 1.0, "bare load must not fully satisfy an assembly task"
    # Same for the AlphaFold flag.
    ref_af = [{"action": "load", "molecule_id": "P04637", "alphafold": True}]
    assert grader.grade(ref_af, ref_af)["f1"] == 1.0
    assert grader.grade(ref_af, [{"action": "load", "molecule_id": "P04637"}])["f1"] < 1.0


def test_tooltip_text_is_scored():
    ref = [{"action": "tooltips", "data": [
        {"auth_asym_id": "A", "residue_number": 35, "tooltip": "catalytic glutamate"}]}]
    right = [{"action": "tooltips", "data": [
        {"auth_asym_id": "A", "residue_number": 35, "tooltip": "Catalytic  Glutamate"}]}]
    wrong = [{"action": "tooltips", "data": [
        {"auth_asym_id": "A", "residue_number": 35, "tooltip": "something else"}]}]
    assert grader.grade(ref, right)["f1"] == 1.0, "case/whitespace should still match"
    assert grader.grade(ref, wrong)["f1"] < 1.0, "wrong tooltip text must lose credit"


def test_sidechain_flag_is_scored():
    ref = [{"action": "color", "data": [
        {"auth_asym_id": "A", "residue_number": 57, "sideChain": True,
         "color": {"r": 220, "g": 0, "b": 220}}]}]
    without = [{"action": "color", "data": [
        {"auth_asym_id": "A", "residue_number": 57, "color": {"r": 220, "g": 0, "b": 220}}]}]
    assert grader.grade(ref, ref)["f1"] == 1.0
    assert grader.grade(ref, without)["f1"] < 1.0, "omitting required side chains must lose credit"


# --- MVS (scene-tree) grader calibration -----------------------------------------

def _scene(color="gray"):
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": "https://files.rcsb.org/download/1hho.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
           {"kind": "structure", "params": {"type": "model"}, "children": [
             {"kind": "component", "params": {"selector": "polymer"}, "children": [
               {"kind": "representation", "params": {"type": "cartoon"}, "children": [
                 {"kind": "color", "params": {"color": color}}]}]}]}]}]}]}}


def test_mvs_self_grading_is_perfect():
    for task in load_tasks(["mvs"]):
        g = mvs.grade_mvs(task["reference_mvs"], task["reference_mvs"])
        assert g["f1"] == 1.0, f"{task['id']} mvs self-F1={g['f1']}"


def test_mvs_is_metadata_insensitive():
    a = _scene()
    b = {"kind": "single", "root": a["root"],
         "metadata": {"timestamp": "2026-01-01T00:00:00Z", "version": "1.8"}}
    assert mvs.grade_mvs(a, b)["f1"] == 1.0


def test_mvs_partial_credit_for_wrong_colour():
    f1 = mvs.grade_mvs(_scene("gray"), _scene("red"))["f1"]
    assert 0.6 < f1 < 1.0, f"expected partial credit, got {f1}"


def test_mvs_grey_gray_fold():
    assert mvs.grade_mvs(_scene("gray"), _scene("grey"))["f1"] == 1.0


def test_mvs_non_tree_scores_zero():
    assert mvs.grade_mvs(_scene(), [{"action": "load"}])["f1"] == 0.0


def test_mvs_grader_survives_non_dict_params():
    # A model may emit a structurally-odd tree (params as a list, not a dict).
    # Grading must degrade gracefully, not crash the whole run on one bad node.
    bad = {"root": {"kind": "root", "children": [
        {"kind": "component", "params": [{"selector": "polymer"}], "children": [
            {"kind": "representation", "params": {"type": "cartoon"}}]}]}}
    g = mvs.grade_mvs(_scene(), bad)
    assert 0.0 <= g["f1"] <= 1.0, "malformed params must be scored, not raised"


def _scene_pdb(pdb="1hho"):
    s = _scene()
    s["root"]["children"][0]["params"]["url"] = f"https://x/{pdb}.cif"
    return s


def test_mvs_download_variant_is_normalised():
    # 1cbs vs 1cbs_updated are the same structure -> identical score.
    assert mvs.grade_mvs(_scene_pdb("1cbs"), _scene_pdb("1cbs_updated"))["f1"] == 1.0


def test_mvs_downstream_credit_survives_upstream_mismatch():
    # Right representation+colour but a genuinely different structure should still
    # earn substantial (not ~zero) credit — position-wise, not prefix-only.
    f1 = mvs.grade_mvs(_scene_pdb("1abc"), _scene_pdb("9zzz"))["f1"]
    assert 0.5 < f1 < 1.0, f"expected downstream credit, got {f1}"


def test_escalate_tree_tier():
    # CI-safe: only the T0 (tree) tier, which needs no renderer/VLM.
    from molbench.escalate import escalating_grade
    same = escalating_grade(_scene(), _scene())            # identical trees
    assert same["decision"] == "correct" and same["tier"] == "tree"
    diff = escalating_grade(_scene("gray"), _scene("red"))  # differ, no render wired
    assert diff["decision"] == "tree-only"                 # cannot escalate without render


def test_render_state_wrapping():
    # Pure (no browser): a root node wraps into a valid single-state .mvsj payload.
    from molbench.render import to_mvs_state
    import json as _json
    root = _scene()["root"]
    state = _json.loads(to_mvs_state(root))
    assert state["kind"] == "single"
    assert state["root"]["kind"] == "root"


def test_run_archives_raw_samples_and_meta():
    from molbench.runner import run
    report, raw = run(["baseline"], ["api_calling"], samples=2)
    assert report["meta"]["models"] == ["baseline"]
    tasks = raw["baseline-rules"]
    tid = next(iter(tasks))
    assert len(tasks[tid]) == 2, "every sample must be retained for drill-in"
    assert "raw" in tasks[tid][0], "raw model output must be archived"


if __name__ == "__main__":
    test_all_reference_answers_are_schema_valid()
    test_self_grading_is_perfect()
    test_wrong_prediction_scores_low()
    test_partial_credit_for_right_residues_wrong_colour()
    test_load_modifiers_are_scored()
    test_tooltip_text_is_scored()
    test_sidechain_flag_is_scored()
    test_mvs_self_grading_is_perfect()
    test_mvs_is_metadata_insensitive()
    test_mvs_partial_credit_for_wrong_colour()
    test_mvs_grey_gray_fold()
    test_mvs_non_tree_scores_zero()
    test_mvs_grader_survives_non_dict_params()
    test_mvs_download_variant_is_normalised()
    test_mvs_downstream_credit_survives_upstream_mismatch()
    test_escalate_tree_tier()
    test_render_state_wrapping()
    test_run_archives_raw_samples_and_meta()
    print("all sanity checks passed")
