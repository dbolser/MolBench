"""The accept-set tier (scripts/generate_accept_set_tasks.py): the files are what the
generator writes, the accept rules hold when graded, and the caps are respected."""

import copy
import importlib.util
import json
import pathlib
import re
from collections import Counter

import pytest

from molbench import drawn, runner, tasks as T

REPO = pathlib.Path(__file__).resolve().parent.parent
DIRS = [REPO / "tasks" / "mvs_accept", REPO / "tasks" / "api_accept"]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _load("generate_accept_set_tasks")
TASKS = {t["id"]: t for d in DIRS for p in sorted(d.glob("*.json")) for t in [T.load_task(p)]}


def grade(tid, answer):
    return runner.grade_parsed(TASKS[tid], answer)


def test_files_are_what_the_generator_writes():
    assert gen.main(["--check"]) == 0


def test_counts_and_shape():
    per = Counter(t["track"] for t in TASKS.values())
    assert per == {"mvs": 26, "api": 15}
    # no template over ~12% of the MVS tier; the API tier has five templates of three
    assert max(Counter(t["family"] for t in TASKS.values() if t["track"] == "mvs").values()) <= 3
    assert max(Counter(t["family"] for t in TASKS.values() if t["track"] == "api").values()) <= 3
    for t in TASKS.values():
        assert t["tier"] == "accept_set" and t["accepted"] and t["style"] == "full"
        assert len(t["accepted_targets"]) == len(t["accepted"])
        prov = t["provenance"]
        assert len(prov["accepted_states"]) == 1 + len(t["accepted"])
        assert prov["rule"] and prov["not_accepted"] and prov["slots"]
        assert set(prov["difficulty"]) >= {"needs_numbering_offset", "needs_ligand_identity",
                                           "author_chain_differs_from_label",
                                           "needs_uniprot_mapping", "n_accepted_states"}
        assert T.WORKED_EXAMPLE not in json.dumps(t).lower()
        # the prompt names no selector field and no numbering scheme
        for word in ("label_", "auth_", "asym", "seq_id", "struct_asym", "comp_id"):
            assert word not in t["prompt"]
    api = [t for t in TASKS.values() if t["track"] == "api"]
    assert all(t["twin_of"] in TASKS for t in api)        # every API task is a twin


def test_caps_and_split():
    used = Counter(t["structures"][0] for t in TASKS.values())
    assert max(used.values()) <= gen.MAX_PER_STRUCTURE
    held = {t["structures"][0] for t in TASKS.values() if t["split"] == "heldback"}
    public = {t["structures"][0] for t in TASKS.values() if t["split"] == "public"}
    assert held and not held & public
    assert held <= gen.heldback_structures()
    share = len(held) / len(held | public)
    assert 0.15 <= share <= 0.25, share                    # ~20% of the tier's structures
    for track in ("mvs", "api"):
        mine = [t for t in TASKS.values() if t["track"] == track]
        assert 0.15 <= sum(t["split"] == "heldback" for t in mine) / len(mine) <= 0.25
    colours = {p["color"] for t in TASKS.values()
               for tg in [t["target"]] + t["accepted_targets"] for p in tg}
    assert colours <= set(drawn.TASK_PALETTE)


def test_heldback_rule_is_a_fifth_of_the_panel_and_stable():
    held = gen.heldback_structures()
    assert len(held) == 15 and T.WORKED_EXAMPLE not in held
    assert held == gen.heldback_structures()


def _components(scene):
    return scene["root"]["children"][0]["children"][0]["children"][0]["children"]


def test_any_one_copy_or_all_but_not_two_of_four():
    tid = "acc-metal-copy-8eph-mvs"
    t = TASKS[tid]
    assert len(t["accepted"]) == 4                         # 4 single ions + all four
    singles = [t["reference"]] + t["accepted"][:3]
    for s in singles + [t["accepted"][3]]:
        assert grade(tid, s)["success"]
    two = copy.deepcopy(singles[0])
    _components(two)[1]["params"]["selector"] = [
        _components(s)[1]["params"]["selector"] for s in singles[:2]]
    res = grade(tid, two)
    assert not res["success"] and res["f1"] < 1


def test_wrong_colour_and_wrong_representation_fail():
    tid = "acc-ligand-copy-1iep-mvs"
    bad = copy.deepcopy(TASKS[tid]["reference"])
    _components(bad)[1]["children"][0]["children"][0]["params"]["color"] = "white"
    assert not grade(tid, bad)["success"]
    bad = copy.deepcopy(TASKS[tid]["reference"])
    _components(bad)[1]["children"][0]["params"]["type"] = "spacefill"
    assert not grade(tid, bad)["success"]


def test_chain_colours_accept_both_assignments_only():
    tid = "acc-chain-colours-2ptc-mvs"
    t = TASKS[tid]
    assert len(t["accepted"]) == 1
    assert grade(tid, t["accepted"][0])["matched_reference"] == 1
    same = copy.deepcopy(t["reference"])
    paints = _components(same)[0]["children"][0]["children"]
    paints[1]["params"]["color"] = paints[0]["params"]["color"]
    assert not grade(tid, same)["success"]
    # one coloured component per chain is the same picture as colour nodes on one cartoon
    a, b = (p["params"] for p in _components(t["reference"])[0]["children"][0]["children"])
    split = copy.deepcopy(t["reference"])
    _components(split)[:] = [
        {"kind": "component", "params": {"selector": p["selector"]}, "children": [
            {"kind": "representation", "params": {"type": "cartoon"}, "children": [
                {"kind": "color", "params": {"color": p["color"]}}]}]} for p in (a, b)]
    assert grade(tid, split)["success"]


def test_the_ligand_accepts_the_viewers_own_ligand_selection():
    for tid in ("acc-ligand-which-1rx2-mvs", "acc-ligand-which-9gio-mvs",
                "acc-ligand-which-2cpp-mvs"):
        t = TASKS[tid]
        answer = copy.deepcopy(t["reference"])
        _components(answer)[1]["params"]["selector"] = "ligand"
        assert grade(tid, answer)["success"], tid
        # ... but not everything that is not protein
        answer = copy.deepcopy(t["reference"])
        _components(answer)[1]["params"]["selector"] = {"label_asym_id": "A"}
        assert not grade(tid, answer)["success"]


def test_representation_open_accepts_what_the_viewer_draws_for_a_cartoon_on_a_ligand():
    tid = "acc-representation-open-1hrc-mvs"
    t = TASKS[tid]
    assert len(t["accepted"]) == 3
    as_cartoon = copy.deepcopy(t["reference"])
    _components(as_cartoon)[1]["children"][0]["params"]["type"] = "cartoon"
    assert grade(tid, as_cartoon)["success"]               # drawn as ball-and-stick
    both = copy.deepcopy(t["reference"])
    _components(both).append(copy.deepcopy(_components(t["accepted"][0])[1]))
    assert not grade(tid, both)["success"]                 # two drawings at once


def test_api_answer_written_another_way_is_accepted():
    tid = "acc-residue-colour-1lmb-api"
    t = TASKS[tid]
    colour = t["reference"][1]["data"][0]["color"]
    number = t["reference"][1]["data"][0]["auth_residue_number"]
    name = t["provenance"]["residues"][0]["comp_id"]
    # no chain given: the residue in every chain that has it (the "both copies" state)
    answer = [t["reference"][0], {"action": "color", "data": [
        {"auth_residue_number": number, "color": colour}]}]
    res = grade(tid, answer)
    by_number = res["success"]
    # the same request for the neighbouring residue is wrong
    answer = [t["reference"][0], {"action": "color", "data": [
        {"auth_residue_number": number + 1, "color": colour}]}]
    assert not grade(tid, answer)["success"]
    # label_comp_id overrides the number in pdbe-molstar: every residue of that type
    answer = [t["reference"][0], {"action": "color", "data": [
        {"label_comp_id": name, "auth_residue_number": number, "color": colour}]}]
    assert not grade(tid, answer)["success"]
    # 1LMB has DNA chains with their own numbering; residue 84 exists only in the protein
    assert by_number


def test_api_references_pass_the_api_reference_check():
    """scripts/check_api_refs.py resolves each selection of an API reference a second
    time from an author-numbered description with the residue name (provenance.targets).
    Its one remaining complaint is by design: it expects an `accepted` alternative to be
    the same state as the reference, and in this tier each one is a different state."""
    check = _load("check_api_refs")
    api = [t for t in TASKS.values() if t["track"] == "api"]
    assert len(api) == 15
    for t in api:
        problems = check.check_task(t)
        assert len(t["provenance"]["targets"]) == len(t["reference"][1]["data"])
        other = [p for p in problems if not re.fullmatch(
            r"accepted\[\d+\] does not grade as success \(f1 [\d.]+\)", p)]
        assert other == [], (t["id"], other)
        assert len(problems) <= len(t["accepted"])       # (none once the check knows the tier)
        assert t["provenance"]["accepted_differ"]
        broken = copy.deepcopy(t)
        target = broken["provenance"]["targets"][0]["atoms"]
        if "auth_seq_id" in target:
            target["auth_seq_id"] += 1                   # the neighbour: must be noticed
            assert any("intended set" in p or "cannot be resolved" in p
                       for p in check.check_task(broken)), t["id"]


def test_twins_have_the_same_words_and_target_atoms():
    for t in TASKS.values():
        if t["track"] == "mvs" and t["twin_of"]:
            other = TASKS[t["twin_of"]]
            assert other["prompt"] == t["prompt"] and other["split"] == t["split"]
            assert T.target_atoms(t) == T.target_atoms(other)


def test_read_back_notices_a_state_that_draws_other_atoms():
    e = next(x for x in gen.entries() if x.id == "1iep")
    spec = gen.spec_ligand_copy(e)
    state = spec["states"][0]
    assert gen.read_back("mvs", "1iep", state, gen.mvs_scene("1iep", state)) is None
    assert gen.read_back("api", "1iep", state, gen.api_calls("1iep", state)) is None
    wrong = spec["states"][1]
    assert gen.read_back("mvs", "1iep", state, gen.mvs_scene("1iep", wrong))
    assert gen.read_back("api", "1iep", state, gen.api_calls("1iep", wrong))


@pytest.mark.parametrize("template", [p[0] for p in gen.PLAN])
def test_every_template_has_rule_wordings_and_readme_row(template):
    assert template in gen.RULES and template in gen.OPEN and template in gen.DERIVED
    assert len(gen.WORDINGS[template]) >= 3
    assert any(t["family"] == template for t in TASKS.values())


def test_a_shared_heldback_list_replaces_the_hash_rule(tmp_path, capsys):
    """The corpus-wide list (data/panel/heldback.json, or --heldback-file): the tier
    still builds and passes its own checks on it; only the files differ."""
    shared = tmp_path / "heldback.json"
    shared.write_text(json.dumps(["1RX2", "2ptc", "1lmb", "8k7f", "1igt"]))
    assert gen.main(["--heldback-file", str(shared), "--check"]) == 1
    assert "out of date" in capsys.readouterr().out
    assert not gen.HELDBACK_FILE.exists() or gen.main(["--check"]) == 0
