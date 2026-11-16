"""Unstated attributes are free on the API track (rulings of 2026-11-15; GRADING.md,
"Unstated attributes are free"): the call forms of ``scripts/api_forms.py``, and that
the tasks on disk accept them and still refuse what a request does state."""

import copy
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import api_forms  # noqa: E402

from molbench import grader, tasks as T  # noqa: E402

TASKS = {t["id"]: t for t in T.load_corpus()}
L = {"action": "load", "molecule_id": "1cbs"}
STYLE = {"action": "set_visual_style", "style": "cartoon"}
REF = [L, STYLE, {"action": "color", "non_selected_color": "gray", "data": [
    {"label_comp_id": "REA", "representation": "ball-and-stick", "representationColor": "teal"}]}]


def ok(tid, answer):
    return grader.grade_task(TASKS[tid], answer)["success"]


def test_cartoon_by_default_or_by_style():
    """'1CBS as a grey cartoon with REA in teal ball-and-stick': the cartoon style set
    (the reference), or the default view, where the ligand is already ball-and-stick."""
    forms = dict(api_forms.cartoon_forms(REF))
    assert forms[api_forms.BACKDROP] == [L, {"action": "color", "non_selected_color": "gray", "data": [
        {"label_comp_id": "REA", "color": "teal"}]}]
    assert forms[api_forms.UNTOUCHED] == [L, {"action": "color", "data": [
        {"struct_asym_id": "A", "color": "gray"}, {"label_comp_id": "REA", "color": "teal"}]}]
    # and back: a reference on the default view gets the style form
    (label, styled), = api_forms.cartoon_forms(forms[api_forms.BACKDROP])
    assert label == api_forms.STYLE and styled == REF
    # a reference that hides something says what is to be seen: no forms
    hidden = REF[:2] + [{"action": "set_property", "name": "hide_polymer", "value": True}] + REF[2:]
    assert api_forms.cartoon_forms(hidden) == []


def test_accepted_forms_keeps_new_states_that_draw_the_target():
    target = {"selector": {"label_comp_id": "REA"}}
    kept = api_forms.accepted_forms(REF, api_forms.cartoon_forms(REF), target)
    assert [label for label, _ in kept] == [api_forms.BACKDROP, api_forms.UNTOUCHED]
    again = api_forms.accepted_forms(REF, api_forms.cartoon_forms(REF), target, [c for _, c in kept])
    assert again == []                                     # nothing listed twice
    wrong = [L, {"action": "color", "non_selected_color": "gray", "data": [{"label_comp_id": "REA", "color": "red"}]}]
    assert api_forms.accepted_forms(REF, [("wrong colour", wrong)], target) == []


def test_base_forms_only_where_the_reference_leaves_the_cartoon_alone():
    item = {"auth_asym_id": "A", "auth_seq_id": 30, "representation": "ball-and-stick",
            "representationColor": "red"}
    ref = [L, {"action": "color", "data": [{**item, "color": None}]}]
    forms = dict(api_forms.base_forms(ref))
    assert forms[api_forms.SELECT_COLOUR][1]["data"] == [item]
    assert forms[api_forms.HIGHLIGHT_COLOUR][1]["data"] == [{**item, "color": "red"}]
    assert api_forms.base_forms([L, {"action": "color", "data": [{**item, "color": "gray"}]}]) == []


def test_twins_accept_the_default_view_and_refuse_what_is_stated():
    tid = "tr-het-code-1cbs-api"
    t = TASKS[tid]
    assert t["provenance"]["twin"]["call_forms"] == [api_forms.BACKDROP, api_forms.UNTOUCHED]
    colour = next(a for a in t["reference"] if a["action"] == "color")
    comp, c, grey = colour["data"][0]["label_comp_id"], colour["data"][0]["representationColor"], \
        colour["non_selected_color"]
    load = t["reference"][0]
    assert ok(tid, [load, {"action": "color", "data": [{"label_comp_id": comp, "color": c}],
                           "non_selected_color": grey}])
    # the added representation as well as the paint: the same final state
    assert ok(tid, [load, {"action": "color", "non_selected_color": grey, "data": [
        {"label_comp_id": comp, "color": c, "representation": "ball-and-stick", "representationColor": c}]}])
    # stated things still have to match: the colour, the backdrop, the representation
    other = "red" if c != "red" else "blue"
    assert not ok(tid, [load, {"action": "color", "data": [{"label_comp_id": comp, "color": other}],
                               "non_selected_color": grey}])
    assert not ok(tid, [load, {"action": "color", "data": [{"label_comp_id": comp, "color": c}]}])
    assert not ok(tid, [load, {"action": "set_visual_style", "style": "spacefill"},
                        {"action": "color", "data": [{"label_comp_id": comp, "color": c}],
                         "non_selected_color": grey}])
    # the ligand drawn twice in two colours is not the request
    assert not ok(tid, [load, {"action": "color", "non_selected_color": grey, "data": [
        {"label_comp_id": comp, "representation": "ball-and-stick", "representationColor": c}]}])
    # and something nobody asked for stays wrong
    assert not ok(tid, t["accepted"][0] + [{"action": "set_property", "name": "bg_color", "value": "black"}])


def test_a_surface_request_does_not_require_hiding_the_water():
    for tid, t in TASKS.items():
        forms = (t["provenance"].get("twin") or {}).get("call_forms") or []
        if api_forms.UNHIDDEN in forms and t["family"] == "tr-surface":
            unhidden = [a for a in t["reference"] if not (a["action"] == "set_property"
                                                         and a["name"].startswith("hide_"))]
            assert ok(tid, unhidden) and ok(tid, t["reference"])
            assert not ok(tid, unhidden[:1])                 # a bare load is not a surface
            break
    else:
        raise AssertionError("no surface twin with the form")


def test_clinical_residue_only_requests_leave_the_cartoon_colour_open():
    """No colour is stated for the cartoon, so the residue's stretch may stay as it is
    (reference), take the highlight colour, or the viewer's select colour (no `color`
    key). With a stated backdrop the select colour is wrong."""
    seen = set()
    for tid, t in TASKS.items():
        if t["track"] != "api" or t["tier"] != "clinical" or t["paraphrase_of"]:
            continue
        context = t["provenance"]["clinical"]["context"]
        if context in seen or t["structures"][0].startswith("af-"):
            continue
        seen.add(context)
        omitted = copy.deepcopy(t["reference"])
        for item in omitted[1]["data"]:
            if "representation" in item:
                item.pop("color", None)
        assert ok(tid, t["reference"])
        assert ok(tid, omitted) == (context == "none"), (tid, context)
        recoloured = copy.deepcopy(t["reference"])
        for item in recoloured[1]["data"]:
            if "representationColor" in item:
                item["representationColor"] = "black"
        assert not ok(tid, recoloured), tid
    assert seen == {"none", "structure", "sse"}


def test_a_request_for_the_cartoon_style_itself_gets_no_default_form():
    styled = [t for t in TASKS.values() if t["track"] == "api" and not t["paraphrase_of"]
              and "cartoon style" in t["prompt"].lower() and not t["twin_of"]]
    assert styled and not any(t["provenance"].get("call_forms") for t in styled)


def test_every_listed_form_is_a_state_of_its_own():
    n = 0
    for t in TASKS.values():
        forms = t["provenance"].get("call_forms") or (t["provenance"].get("twin") or {}).get("call_forms")
        if t["track"] != "api" or not forms or t["tier"] == "accept_set" or t["paraphrase_of"]:
            continue
        n += 1
        lists = [t["reference"]] + t["accepted"]
        keys = {json.dumps(x, sort_keys=True) for x in lists}
        assert len(keys) == len(lists), t["id"]
        for alt in t["accepted"][-len(forms):]:
            assert ok(t["id"], alt), t["id"]
            assert not grader.grade_task({**t, "accepted": []}, alt)["success"], t["id"]
    assert n >= 80
