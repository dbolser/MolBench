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

from molbench import grader, schema
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


if __name__ == "__main__":
    test_all_reference_answers_are_schema_valid()
    test_self_grading_is_perfect()
    test_wrong_prediction_scores_low()
    test_partial_credit_for_right_residues_wrong_colour()
    print("all sanity checks passed")
