"""
The follow-up tier (``tasks/mvs_followup``, ``tasks/api_followup``).

The generator checks every task against the grader before it writes a file
(``scripts/generate_followup_tasks.py``, `verify`); these tests run that once, hold
the files on disk to what the generator writes, and pin the properties the paper
leans on: the caps on reuse, the held-back split, the no-change tasks, and that the
*preserved* parts recorded in ``provenance`` really do tell a clobbering answer from
a careful one.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import re
from collections import Counter

import pytest

from molbench import runner
from molbench import tasks as T

REPO = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "generate_followup_tasks", REPO / "scripts" / "generate_followup_tasks.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


@pytest.fixture(scope="module")
def built():
    """Every task and its spec (start, reference, controls), built and verified."""
    tasks, specs = gen.build(gen.heldback_ids())
    return gen.verify(tasks, specs), specs


@pytest.fixture(scope="module")
def on_disk():
    return {p.stem: json.loads(p.read_text(encoding="utf-8"))
            for out in gen.OUT.values() for p in sorted(out.glob("*.json"))}


def _loaded(task: dict) -> dict:
    return T._with_aliases({**task, "_path": f"tasks/{task['track']}_followup/{task['id']}.json"})


def _preserved_scores(task: dict, answer) -> list[float]:
    full = _loaded(task)
    return [runner.grade_parsed({**full, "target": [p], "accepted": []}, answer)["target_f1"]
            for p in task["provenance"]["preserved"] or []]


def test_the_files_are_what_the_generator_writes(built, on_disk):
    tasks, _ = built
    assert {t["id"] for t in tasks} == set(on_disk)
    for t in tasks:
        path = gen.OUT[t["track"]] / f"{t['id']}.json"
        assert path.read_text(encoding="utf-8") == json.dumps(t, indent=1) + "\n", t["id"]
    for track, out in gen.OUT.items():
        assert (out / "README.md").read_text(encoding="utf-8") == gen.readme(track, tasks)


def test_a_second_build_is_identical(built):
    again, _ = gen.build(gen.heldback_ids())
    again = gen.verify(again, gen.build(gen.heldback_ids())[1])
    assert json.dumps(again) == json.dumps(built[0])


def test_size_and_mix(on_disk):
    mvs = [t for t in on_disk.values() if t["track"] == "mvs"]
    api = [t for t in on_disk.values() if t["track"] == "api"]
    assert len(mvs) >= 50 and len(api) >= 40
    for mine in (mvs, api):
        assert sum(t["context"]["noop"] for t in mine) >= 8          # decision 19
        assert all(t["tier"] == "followup" and t["style"] == "full" for t in mine)
        per_structure = Counter(t["structures"][0] for t in mine)
        assert max(per_structure.values()) <= gen.MAX_PER_TRACK <= 6
        share = max(Counter(t["family"] for t in mine).values()) / len(mine)
        assert share <= 0.12
    kinds = {t["provenance"]["edit"] for t in on_disk.values()}
    for wanted in ("recolour one existing component", "change a representation",
                   "add a component (a residue), keeping the rest", "remove / hide something",
                   "narrow to one component", "undo-like recolour", "pronoun: recolour",
                   "ellipsis: colour the component not yet coloured", "no change: already true",
                   "no change: the format cannot express the request"):
        assert wanted in kinds, wanted


def test_no_task_uses_the_worked_example(on_disk):
    for t in on_disk.values():
        assert "1hsg" not in json.dumps(t).lower(), t["id"]


def test_held_back_structures_are_in_no_public_task(on_disk):
    for track in ("mvs", "api"):
        mine = [t for t in on_disk.values() if t["track"] == track]
        held = {t["structures"][0] for t in mine if t["split"] == "heldback"}
        public = {t["structures"][0] for t in mine if t["split"] == "public"}
        assert held and not held & public
        assert held <= gen.heldback_ids()
        assert 0.10 <= len(held) / len(held | public) <= 0.30
    # the rule looks at the structure alone, so it is the same fifth for any tier
    ids = gen.heldback_ids()
    assert len(ids) == round(0.2 * sum(
        r["kind"] == "pdb" and r["id"] != T.WORKED_EXAMPLE
        for r in gen.grounding.panel()["entries"]))


SYNTAX = re.compile(r"label_|auth_|struct_asym|_seq_id|comp_id|selector|keep_colors|set_visual|"
                    r"MolViewSpec|\bMVS\b|\bnode\b|JSON", re.I)


def test_prompts_are_plain_requests(on_disk):
    for t in on_disk.values():
        assert not SYNTAX.search(t["prompt"]), (t["id"], t["prompt"])
        assert "limegreen" not in t["prompt"] and "hotpink" not in t["prompt"]
    # within a family, no two tasks of a track share a prompt
    for track in ("mvs", "api"):
        seen = Counter((t["family"], t["prompt"]) for t in on_disk.values() if t["track"] == track)
        assert max(seen.values()) == 1


def test_twins_are_mutual_and_ask_the_same(on_disk):
    twins = [t for t in on_disk.values() if t["twin_of"]]
    assert len(twins) >= 60
    for t in twins:
        other = on_disk[t["twin_of"]]
        assert other["twin_of"] == t["id"] and other["track"] != t["track"]
        for key in ("prompt", "structures", "split", "family"):
            assert other[key] == t[key], (t["id"], key)
        assert other["context"]["noop"] == t["context"]["noop"]
        assert T.target_atoms(_loaded(other)) == T.target_atoms(_loaded(t))


def test_reference_start_state_and_noop(on_disk):
    for t in on_disk.values():
        full = _loaded(t)
        start = t["context"][T.CONTEXT_STATE[t["track"]]]
        res = runner.grade_parsed(full, t["reference"])
        assert res["success"] and res["f1"] == 1.0, t["id"]
        if t["target"]:
            assert res["target_f1"] == 1.0, t["id"]
        unchanged = runner.grade_parsed(full, start)
        assert bool(unchanged["success"]) == t["context"]["noop"], t["id"]
        if t["context"]["noop"]:
            assert t["reference"] == start, t["id"]
        else:
            assert t["reference"] != start, t["id"]


def test_provenance_records_what_the_paper_needs(on_disk):
    for t in on_disk.values():
        prov = t["provenance"]
        assert set(prov["difficulty"]) == {
            "needs_numbering_offset", "author_chain_differs_from_label",
            "needs_ligand_identity", "needs_uniprot_mapping", "needs_referent_from_context"}
        assert prov["edit"] and "preserved" in prov and "removed" in prov
        assert (prov["noop_kind"] is not None) == t["context"]["noop"]
        if prov["difficulty"]["needs_referent_from_context"]:
            assert prov["referent"]
        for p in prov["preserved"] or []:
            assert set(p) == {"selector", "representation", "color"}
        if t["context"]["noop"]:
            assert prov["preserved"], "a no-change task preserves everything that was set"
    assert any(t["provenance"]["difficulty"]["needs_numbering_offset"] for t in on_disk.values())


def test_preserved_parts_hold_on_the_reference_and_the_start_state(on_disk):
    for t in on_disk.values():
        start = t["context"][T.CONTEXT_STATE[t["track"]]]
        assert all(s == 1.0 for s in _preserved_scores(t, t["reference"])), t["id"]
        assert all(s == 1.0 for s in _preserved_scores(t, start)), t["id"]


def test_a_clobbering_answer_keeps_the_target_and_loses_the_preserved_part(built):
    """The point of ``provenance.preserved``: the edit made on an empty viewer gets the
    target right and the earlier choices wrong."""
    tasks, specs = built
    seen = 0
    for t, side in zip(tasks, specs):
        if t["family"] != "fu-recolour-ligand":
            continue
        clobber = side["wrong"][0]                    # only the recoloured ligand
        res = runner.grade_parsed(_loaded(t), clobber)
        assert not res["success"] and res["target_f1"] == 1.0, t["id"]
        assert min(_preserved_scores(t, clobber)) < 1.0, t["id"]
        seen += 1
    assert seen >= 4


def test_whole_chain_edits_do_not_depend_on_the_chain_id_scheme(built):
    """API track: under the cartoon style the author chain and the polymer chain are the
    same picture, so an answer in label chain ids is as right as the reference."""
    tasks, specs = built
    seen = 0
    for t, side in zip(tasks, specs):
        if t["track"] != "api" or "chain" not in t["provenance"]["edit"] + t["family"]:
            continue
        ref = t["reference"]
        if not any("auth_asym_id" in p and "auth_seq_id" not in p
                   for c in ref for p in c.get("data") or []):
            continue
        entry = next(e for e in gen.entries() if e.id == t["structures"][0])
        other = gen.by_label(entry, ref)
        assert other != ref
        assert runner.grade_parsed(_loaded(t), other)["success"], t["id"]
        assert {"action": "set_visual_style", "style": "cartoon"} in ref \
            or t["family"] == "fu-api-style"
        seen += 1
    assert seen >= 6


def test_the_generator_refuses_a_bad_task(built):
    """`verify` is what stands between a template slip and a task file."""
    tasks, specs = copy.deepcopy(built[0]), copy.deepcopy(built[1])
    i = next(i for i, t in enumerate(tasks) if t["family"] == "fu-recolour-ligand" and t["track"] == "mvs")
    tasks[i]["context"]["noop"] = True                # claims no change is needed
    with pytest.raises(SystemExit):
        gen.verify(tasks, specs)
    tasks, specs = copy.deepcopy(built[0]), copy.deepcopy(built[1])
    specs[i]["wrong"] = [specs[i]["ref"]]            # a "wrong" control that is right
    with pytest.raises(SystemExit):
        gen.verify(tasks, specs)


def test_a_residue_is_added_without_repainting_its_cartoon(on_disk):
    """API track, "add Thr348 in red ball-and-stick": the vendored API reference's own
    example also paints the residue's cartoon (``"color": "red"``), which is another
    final state than leaving it (``"color": null``). The request therefore says the
    cartoon keeps its colour, and only the answer that leaves it is right."""
    seen = 0
    for t in on_disk.values():
        if t["family"] != "fu-add-residue":
            continue
        assert "cartoon" in t["prompt"], t["id"]
        if t["track"] != "api":
            continue
        full = _loaded(t)
        ref = t["reference"]
        new = ref[-1]["data"][0]["representationColor"]
        assert ref[-1]["data"][0]["color"] is None and t["accepted"] == []
        painted = copy.deepcopy(ref)
        painted[-1]["data"][0]["color"] = new
        no_stick_colour = copy.deepcopy(painted)
        del no_stick_colour[-1]["data"][0]["representationColor"]
        default_orange = copy.deepcopy(ref)
        del default_orange[-1]["data"][0]["color"]
        for wrong in (painted, no_stick_colour, default_orange):
            assert not runner.grade_parsed(full, wrong)["success"], t["id"]
        seen += 1
    assert seen == 4


def test_a_chain_named_by_its_colour_is_one_of_exactly_two(on_disk):
    for t in on_disk.values():
        if t["family"] in ("fu-referent-colour", "fu-swap-colours", "fu-other-chain"):
            assert len(gen.grounding.facts(t["structures"][0])["chains"]) == 2, t["id"]


def test_the_chain_difficulty_flag_follows_the_answer_not_the_wording(on_disk):
    """``author_chain_differs_from_label`` is set when the final state picks a chain by
    its author id on an entry whose author and label chain ids differ: "the blue one"
    (2P4E) picks a chain without the word, "hide the waters" (1ATP) picks none."""
    flag = lambda tid: on_disk[tid]["provenance"]["difficulty"]["author_chain_differs_from_label"]
    for track in T.TRACKS:
        assert flag(f"fu-referent-colour-2p4e-{track}")
        assert not flag(f"fu-noop-hidden-1atp-{track}")
    for t in on_disk.values():
        differs = gen.grounding.facts(t["structures"][0])["numbering"]["auth_chain_differs_from_label_chain"]
        picks = '"auth_asym_id"' in json.dumps(t["reference"]) or (
            t["twin_of"] and '"auth_asym_id"' in json.dumps(on_disk[t["twin_of"]]["reference"]))
        assert t["provenance"]["difficulty"]["author_chain_differs_from_label"] == bool(differs and picks), t["id"]
