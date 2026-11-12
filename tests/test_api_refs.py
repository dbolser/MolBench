"""
Every API-track reference, checked against the structure it talks about.

The checks themselves live in ``scripts/check_api_refs.py`` (so they can also be run
by hand, and with ``--viewer`` against the real pdbe-molstar); this file runs the
offline ones for every task.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

from molbench import grader, schema
from molbench import pdbe_state as ps

REPO = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_api_refs", REPO / "scripts" / "check_api_refs.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

TASKS = check.load_api_tasks()


def test_there_are_tasks_with_unique_ids():
    assert len(TASKS) >= 20
    assert len({t["id"] for t in TASKS}) == len(TASKS)


@pytest.mark.parametrize("task", TASKS, ids=[t["id"] for t in TASKS])
def test_reference_is_right_for_its_structure(task):
    assert check.check_task(task) == []


@pytest.mark.parametrize("task", TASKS, ids=[t["id"] for t in TASKS])
def test_task_shape(task):
    assert task["category"] == "api_calling"
    assert task["skills"] and task["skills"] == task["categories"]   # the runner reads `categories`
    prov = task["provenance"]
    assert prov["july_task"] in ("unchanged", "reworded", "replaced")
    assert prov["derived"] and prov["source"] and prov["checked_by"]
    res = grader.grade_task(task, task["reference"])
    assert res["grader"] == "state" and res["success"] and res["f1"] == 1.0
    assert grader.grade_sequence(task["reference"], task["reference"])["f1"] > 0   # legacy still runs
    for alt in task.get("accepted", []):
        assert grader.grade_task(task, alt)["success"]


def test_prompt_example_is_not_a_task():
    assert check.check_prompt_example(TASKS) == []


def test_the_check_catches_the_july_mistakes():
    """The checker must fail on the kinds of error it exists to catch."""
    triad = next(t for t in TASKS if t["id"] == "api-019")
    import copy
    bad = copy.deepcopy(triad)
    for act in bad["reference"]:
        for p in act.get("data", []):            # the July reference: label numbering
            p["residue_number"] = p.pop("auth_seq_id")
    problems = check.check_task(bad)
    assert any("intended set (His57)" in p for p in problems)

    water = next(t for t in TASKS if t["id"] == "api-001")
    bad = copy.deepcopy(water)
    bad["reference"][0]["molecule_id"] = "1mbn"     # the July entry: no waters to hide
    bad["provenance"]["structure"] = "1mbn"
    assert any("no such component" in p for p in check.check_task(bad))

    bad = copy.deepcopy(triad)
    bad["reference"][2]["data"][0]["color"] = "Magenta"
    assert any("not a Mol* colour name" in p for p in check.check_task(bad))

    bad = copy.deepcopy(triad)
    del bad["provenance"]["targets"][0]
    assert any("no provenance target" in p for p in check.check_task(bad))


def test_schema_knows_the_real_options():
    for key in ("auth_residue_number", "start_auth_residue_number", "uniprot_residue_number", "atom_id"):
        assert key in schema.SELECTION_LOCATOR_FIELDS
    for name in ("superposition_params", "map_settings", "sequence_panel"):
        assert name in schema.SETTABLE_PROPERTIES
    assert "ligand_view" in schema.ACTION_SPECS["load"]["optional"]
    assert set(schema.SELECTION_LOCATOR_FIELDS) == set(ps.LOCATOR_KEYS)
    assert set(schema.REPRESENTATIONS) == set(ps.REPRESENTATIONS)
    # every settable property is something the replay understands
    for name in schema.SETTABLE_PROPERTIES:
        state = ps.replay([{"action": "set_property", "name": name, "value": True}])
        assert not state.log, name
    text = schema.schema_text()
    assert all(a in text for a in schema.ACTION_SPECS) and len(text) < 3000


def test_reference_doc_names_only_real_keys():
    doc = (REPO / "molbench" / "api_reference.md").read_text()
    for key in schema.SELECTION_LOCATOR_FIELDS:
        if "ins_code" in key or key == "atom_id":
            continue                                  # accepted by the viewer, deliberately undocumented
        assert f"`{key}`" in doc, key
    for name in schema.SETTABLE_PROPERTIES:
        assert f"`{name}`" in doc, name
