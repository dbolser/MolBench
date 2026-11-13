"""
The MVS -> API twin translator (``scripts/translate_mvs_to_api.py``).

The corpus on this branch has no MVS task in the task format yet (the MVS generators
are merged later), so the translator is exercised on scenes built here from the frozen
panel, on the fixture tasks, and on the old-format MVS tasks' references.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import sys

import pytest

from molbench import mvs, runner
from molbench import pdbe_state as ps
from molbench import tasks as T

REPO = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("translate_mvs_to_api", REPO / "scripts" / "translate_mvs_to_api.py")
tr = importlib.util.module_from_spec(_spec)
sys.modules["translate_mvs_to_api"] = tr
_spec.loader.exec_module(tr)


def scene(entry: str, components: list[dict], structure: dict | None = None, extra: list | None = None) -> dict:
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{entry}.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": structure or {"type": "model"}, "children": components}]}]},
        *(extra or [])]}}


def comp(selector, rep: str | None, color: str | None = None, layers: list | None = None,
         more: list | None = None, opacity: float | None = None) -> dict:
    kids = []
    if rep:
        node = {"kind": "representation", "params": {"type": rep}, "children": []}
        if color:
            node["children"].append({"kind": "color", "params": {"color": color}})
        for sel, c in layers or []:
            node["children"].append({"kind": "color", "params": {"color": c, "selector": sel}})
        if opacity is not None:
            node["children"].append({"kind": "opacity", "params": {"opacity": opacity}})
        kids.append(node)
    return {"kind": "component", "params": {"selector": selector}, "children": kids + (more or [])}


GREY = comp("polymer", "cartoon", "gray")
SCENES = {
    "whole protein, one colour": ("1cbs", scene("1cbs", [comp("polymer", "cartoon", "purple")])),
    "cartoon and a ligand by code": ("1cbs", scene("1cbs", [GREY, comp({"label_comp_id": "REA"}, "ball_and_stick", "teal")])),
    "author-numbered residues as sticks (numbering offset)": ("3ptb", scene("3ptb", [GREY, comp(
        [{"auth_asym_id": "A", "auth_seq_id": n} for n in (57, 102, 195)], "ball_and_stick", "magenta")])),
    "layered colours on a range": ("3ptb", scene("3ptb", [comp("polymer", "cartoon", "gray", layers=[
        ({"auth_asym_id": "A", "beg_auth_seq_id": 40, "end_auth_seq_id": 60}, "yellow"),
        ({"auth_asym_id": "A", "auth_seq_id": 57}, "red")])])),
    "chains in different colours": ("4ins", scene("4ins", [
        comp({"auth_asym_id": c}, "cartoon", col) for c, col in zip("ABCD", ("magenta", "cyan", "plum", "red"))])),
    "only the ligand": ("1cbs", scene("1cbs", [comp({"label_comp_id": "REA"}, "spacefill", "orange")])),
    "surface": ("1aki", scene("1aki", [comp("polymer", "surface", "steelblue")])),
    "ions as spheres": ("4ins", scene("4ins", [GREY, comp("ion", "spacefill", "hotpink")])),
    "waters shown": ("1iro", scene("1iro", [comp("polymer", "cartoon", "blue"), comp("water", "spacefill", "teal")])),
    "focus and tooltip": ("1ema", scene("1ema", [GREY, comp(
        {"auth_asym_id": "A", "auth_seq_id": 196}, "ball_and_stick", "orange",
        more=[{"kind": "focus", "params": {}}, {"kind": "tooltip", "params": {"text": "Residue 196"}}])])),
    "assembly": ("1hho", scene("1hho", [comp("polymer", "cartoon", "green")],
                               structure={"type": "assembly", "assembly_id": "1"})),
    "background": ("1cbs", scene("1cbs", [GREY], extra=[{"kind": "canvas", "params": {"background_color": "black"}}])),
    "atoms of a residue": ("3ptb", scene("3ptb", [GREY, comp(
        [{"auth_asym_id": "A", "auth_seq_id": 195, "label_atom_id": a} for a in ("CB", "OG")], "spacefill", "red")])),
    "a modified residue inside the chain": ("1ema", scene("1ema", [GREY, comp(
        {"label_comp_id": "CRO"}, "ball_and_stick", "orange")])),
}


@pytest.mark.parametrize("name", SCENES)
def test_a_scene_becomes_calls_with_the_same_final_state(name):
    entry, tree = SCENES[name]
    calls, notes = tr.translate_scene(tree, entry)
    assert tr.state_differences(tree, calls) == []
    # checked a second way, with nothing of the translator's: per atom, the API grader's
    # display equals the MVS grader's draws
    st = mvs.resolve_scene(tree).structures[entry]
    want = {}
    for (rtype, colour, opacity), mask in st.draws.items():
        assert opacity == 1.0
        want[(tr.REP[rtype], colour)] = want.get((tr.REP[rtype], colour), 0) | mask
    got = {}
    for mask, look in ps.replay(copy.deepcopy(calls)).display().items():
        for d in look:
            got[d] = got.get(d, 0) | mask
    assert got == want
    assert notes["base"] and isinstance(notes["switched_off"], list)


def test_the_equivalence_check_is_not_vacuous():
    entry, tree = SCENES["author-numbered residues as sticks (numbering offset)"]
    calls, _ = tr.translate_scene(tree, entry)
    assert tr.state_differences(tree, calls) == []

    def changed(edit):
        bad = copy.deepcopy(calls)
        edit(bad)
        return tr.state_differences(tree, bad)

    paint = next(i for i, a in enumerate(calls) if a["action"] == "color")
    assert changed(lambda c: c[paint]["data"][0].update(representationColor="red"))       # another colour
    assert changed(lambda c: c[paint]["data"][0].update(auth_seq_id=58))                  # the neighbour
    assert changed(lambda c: c[paint]["data"][0].update(representation="spacefill"))      # another type
    assert changed(lambda c: c[paint]["data"].pop())                                      # a residue missing
    assert changed(lambda c: c.append({"action": "set_property", "name": "spin", "value": True}))
    assert changed(lambda c: c.append({"action": "focus", "data": [{"auth_seq_id": 57}]}))
    assert changed(lambda c: c.__setitem__(slice(1, None), []))                           # a bare load
    # the July mistake: the author number in the label key
    def label_key(c):
        for p in c[paint]["data"]:
            p["residue_number"] = p.pop("auth_seq_id")
    assert changed(label_key)


@pytest.mark.parametrize("name,tree,reason", [
    ("opacity", scene("1cbs", [comp("polymer", "surface", "brown", opacity=0.5)]), "transparency"),
    ("line", scene("1cbs", [comp("polymer", "line", "brown")]), "no API counterpart"),
    ("label", scene("1cbs", [GREY, comp({"label_comp_id": "REA"}, None, more=[
        {"kind": "label", "params": {"text": "retinoic acid"}}])]), "label"),
    ("distance", scene("1cbs", [GREY, {"kind": "primitives", "params": {}, "children": [
        {"kind": "primitive", "params": {"kind": "distance_measurement",
                                         "start": {"auth_asym_id": "A", "auth_seq_id": 10, "label_atom_id": "CA"},
                                         "end": {"auth_asym_id": "A", "auth_seq_id": 20, "label_atom_id": "CA"}}}]}]),
     "primitive"),
    ("theme", scene("1cbs", [{"kind": "component", "params": {"selector": "polymer"}, "children": [
        {"kind": "representation", "params": {"type": "cartoon"}, "children": [
            {"kind": "color", "params": {"color": "white"}, "custom": {"molstar_color_theme_name": "chain-id"}}]}]}]),
     "colour theme"),
    ("other model", scene("1d3z", [GREY], structure={"type": "model", "model_index": 2}), "another model"),
])
def test_what_the_api_cannot_draw_is_refused_with_a_reason(name, tree, reason):
    with pytest.raises(tr.Untranslatable) as e:
        tr.translate_scene(tree, "1cbs" if name != "other model" else "1d3z")
    assert reason in e.value.reason


def _fixture(tid: str) -> dict:
    return next(t for t in T.load_corpus(REPO / "tests" / "fixtures" / "tasks") if t["id"] == tid)


def test_a_twin_task_of_a_fixture():
    """A whole twin: format, links, target, self-grading, provenance."""
    task = _fixture("fx-ligand-1cbs-mvs")
    twin = tr.make_twin(task, {})
    assert twin["id"] == "fx-ligand-1cbs-api" and twin["twin_of"] == task["id"] and twin["track"] == "api"
    for key in ("prompt", "structures", "split", "style", "tier", "family"):
        assert twin[key] == task[key]
    assert T.validate_task(twin) == []
    assert T.target_atoms(twin) == T.target_atoms(task)
    assert twin["target"][0]["representation"] == "ball-and-stick"       # the API's word for it
    view = T._with_aliases(dict(twin))
    res = runner.grade_parsed(view, twin["reference"])
    assert res["success"] and res["f1"] == 1.0 and res["target_f1"] == 1.0
    # the scene draws polymer and ligand only: the waters a load would draw are gone
    assert not runner.grade_parsed(view, [{"action": "load", "molecule_id": "1cbs"}])["success"]
    prov = twin["provenance"]
    assert prov["script"] == tr.SCRIPT and prov["twin"]["of"] == task["id"] and len(prov["checks"]) >= 4
    assert "context_switched_off" in prov["difficulty"] and "numbering_offset" in prov["difficulty"]


def test_a_follow_up_twin_translates_its_start_state():
    task = _fixture("fx-follow-colour-1stp-mvs")
    twin = tr.make_twin(task, {})
    assert twin["context"]["noop"] == task["context"]["noop"]
    assert tr.state_differences(task["context"]["scene"], twin["context"]["calls"]) == []
    assert tr.state_differences(task["reference"], twin["reference"]) == []


def test_a_paraphrase_twin_points_at_the_twin_of_its_original():
    para = _fixture("fx-ligand-terse-1stp-mvs")
    with pytest.raises(tr.Untranslatable):
        tr.make_twin(para, {})                                # its original has no twin yet
    twin = tr.make_twin(para, {para["paraphrase_of"]: "fx-ligand-1stp-api"})
    assert twin["paraphrase_of"] == "fx-ligand-1stp-api"
    original = tr.make_twin(_fixture(para["paraphrase_of"]), {})
    assert twin["reference"] == original["reference"]


def test_old_format_references_translate_or_say_why():
    """Every MVS reference of the corpus on disk: a call list with the same final state,
    or a reason from the documented list."""
    reasons = set()
    n = 0
    for task in T.load_corpus(tracks=["mvs"]):
        if len(task["structures"]) != 1:
            continue
        try:
            calls, _ = tr.translate_scene(task["reference"], task["structures"][0])
        except tr.Untranslatable as e:
            reasons.add(e.reason)
            continue
        n += 1
        assert tr.state_differences(task["reference"], calls) == [], task["id"]
        assert not any(tr.T.WORKED_EXAMPLE in json.dumps(a) for a in calls)
    assert n >= 50
    assert reasons <= {"a distance line or another drawn primitive", "transparency (the API has no opacity)",
                       "the computed non-covalent interactions request", "a 3D text label",
                       "a representation with no API counterpart", "a colour theme (colour by chain)",
                       "a node kind with no API counterpart", "no call list gives this drawing"}


def test_the_readme_on_disk_is_what_the_script_writes():
    twins, rows, corpus = tr.plan()
    files = tr.wanted_files(twins, rows, corpus, whole=True)
    for path, text in files.items():
        assert path.read_text() == text, path
    assert {p for p in tr.OUT.glob("*.json")} == {p for p in files if p.suffix == ".json" and p.parent == tr.OUT}


def test_twin_ids():
    assert tr.twin_id("tr-cartoon-1c3w") == "tr-cartoon-1c3w-api"
    assert tr.twin_id("fx-ligand-1cbs-mvs") == "fx-ligand-1cbs-api"
    assert tr.twin_id("acc-x-1aay-mvs.terse") == "acc-x-1aay-api.terse"


def test_a_no_change_follow_up_gets_no_twin():
    """'Start it spinning' changes nothing in an MVS scene and sets `spin` in the API:
    the same final state would be the wrong answer on the other track."""
    with pytest.raises(tr.Untranslatable) as e:
        tr.make_twin(_fixture("fx-follow-noop-1cbs-mvs"), {})
    assert "no-change" in e.value.reason


def test_the_corpus_plan_leaves_other_generators_pairs_alone(monkeypatch):
    """Tasks already paired by their own generator, and the unpaired MVS tasks of a
    generator that writes both tracks, are not given twins; their files are not touched."""
    fixtures = T.load_corpus(REPO / "tests" / "fixtures" / "tasks")
    monkeypatch.setattr(tr.T, "load_corpus", lambda *a, **k: copy.deepcopy(fixtures))
    twins, rows, corpus = tr.plan()
    assert twins == []
    reasons = {r["id"]: r["reason"] for r in rows}
    assert reasons["fx-ligand-1cbs-mvs"] == tr.PAIRED
    assert reasons["fx-anycopy-1hvr-mvs"] == tr.TWO_TRACK          # MVS-only by its generator's choice
    assert not [p for p in tr.wanted_files(twins, rows, corpus, whole=False)]
    # the same tasks from a generator that writes MVS only: now they are this script's to pair
    solo = copy.deepcopy(fixtures)
    for t in solo:
        if t["track"] == "mvs":
            t["twin_of"] = None
            t["provenance"]["script"] = "scripts/some_mvs_only_generator.py"
    solo = [t for t in solo if t["track"] == "mvs"]
    monkeypatch.setattr(tr.T, "load_corpus", lambda *a, **k: copy.deepcopy(solo))
    twins, rows, corpus = tr.plan()
    made = {t["id"] for t in twins}
    assert "fx-ligand-1cbs-api" in made and "fx-ligand-terse-1stp-api" in made
    assert "fx-follow-noop-1cbs-api" not in made
    files = tr.wanted_files(twins, rows, corpus, whole=False)
    mvs_file = REPO / "tests" / "fixtures" / "tasks" / "fx-ligand-1cbs-mvs.json"
    assert json.loads(files[tr.OUT / "fx-ligand-1cbs-api.json"])["twin_of"] == "fx-ligand-1cbs-mvs"
    assert mvs_file not in files          # its twin_of already names fx-ligand-1cbs-api: no rewrite
