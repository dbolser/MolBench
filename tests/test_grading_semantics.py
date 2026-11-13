"""What "right" means, pinned case by case (decisions 17 and 18; GRADING.md).

Each test states one rule of the drawn-state grader in a way a reader can check
against the viewer. The rules themselves were read back from headless Mol* 5.9.0
(``scripts/grader_controls.py --viewer``; the result is ``tests/controls/viewer_check.json``).
"""

import copy
import itertools
import json
import pathlib

import pytest

from molbench import drawn, grader, mvs
from molbench import pdbe_state as ps

REPO = pathlib.Path(__file__).resolve().parent.parent


# --- helpers ---------------------------------------------------------------------------

def comp(selector, *children, custom=None):
    node = {"kind": "component", "params": {"selector": selector}, "children": list(children)}
    if custom:
        node["custom"] = custom
    return node


def rep(rtype, *children, **params):
    return {"kind": "representation", "params": {"type": rtype, **params}, "children": list(children)}


def col(color, selector=None, theme=None):
    node = {"kind": "color", "params": {"color": color}}
    if selector is not None:
        node["params"]["selector"] = selector
    if theme:
        node["custom"] = {"molstar_color_theme_name": theme}
    return node


def scene(entry, *comps, structure=None):
    return {"kind": "root", "children": [
        {"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{entry}.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": structure or {"type": "model"},
              "children": list(comps)}]}]}]}


R248 = {"auth_asym_id": "A", "auth_seq_id": 248}
GREY = comp("polymer", rep("cartoon", col("gray")))
FOCUS = {"kind": "focus", "params": {}}


def g(ref, pred, **kw):
    return mvs.grade_mvs(ref, pred, **kw)


def same(ref, pred):
    r = g(ref, pred)
    return r["success"] and r["f1"] == 1.0 and r["target_f1"] == 1.0


def highlight(sel=R248, colour="red", rtype="ball_and_stick"):
    return scene("1tup", copy.deepcopy(GREY), comp(sel, rep(rtype, col(colour))))


# --- decision 18: the same drawing, however it is written ------------------------------

def test_all_and_polymer_are_the_same_under_a_cartoon():
    # a cartoon draws polymer residues only, so 'all' adds nothing (1TUP has ions and water)
    assert same(scene("1tup", comp("polymer", rep("cartoon", col("gray")))),
                scene("1tup", comp("all", rep("cartoon", col("gray")))))


def test_all_and_polymer_differ_under_ball_and_stick():
    r = g(scene("1tup", comp("polymer", rep("ball_and_stick", col("gray")))),
          scene("1tup", comp("all", rep("ball_and_stick", col("gray")))))
    assert not r["success"] and r["recall"] == 1.0 and r["precision"] < 1.0


def test_ribbon_types_draw_residues_through_their_trace_atom():
    whole = scene("1tup", comp({"auth_asym_id": "A"}, rep("cartoon", col("red"))))
    ca_only = scene("1tup", comp({"auth_asym_id": "A", "label_atom_id": "CA"}, rep("cartoon", col("red"))))
    cb_only = scene("1tup", comp({"auth_asym_id": "A", "label_atom_id": "CB"}, rep("cartoon", col("red"))))
    assert same(whole, ca_only)
    assert g(whole, cb_only)["f1"] == 0.0          # no trace atom: Mol* draws nothing
    # a nucleotide's trace atom is O3', not P
    dna = scene("1tup", comp({"auth_asym_id": "E"}, rep("cartoon", col("red"))))
    assert same(dna, scene("1tup", comp({"auth_asym_id": "E", "label_atom_id": "O3'"}, rep("cartoon", col("red")))))
    assert g(dna, scene("1tup", comp({"auth_asym_id": "E", "label_atom_id": "P"}, rep("cartoon", col("red")))))["f1"] == 0.0


def test_a_ribbon_type_on_ions_is_drawn_as_ball_and_stick():
    # Mol* replaces a representation type that does not apply to the component
    for rtype in ("cartoon", "backbone", "putty", "carbohydrate"):
        assert same(scene("1tup", comp("ion", rep("ball_and_stick", col("orange")))),
                    scene("1tup", comp("ion", rep(rtype, col("orange"))))), rtype
    # ... and carbohydrate in a structure with no sugars is drawn as a cartoon
    assert same(scene("1tup", comp("polymer", rep("cartoon", col("gray")))),
                scene("1tup", comp("polymer", rep("carbohydrate", col("gray")))))


def test_residue_ranges_lists_and_label_addressing_are_the_same_atoms():
    rng = {"auth_asym_id": "A", "beg_auth_seq_id": 245, "end_auth_seq_id": 249}
    as_list = [{"auth_asym_id": "A", "auth_seq_id": n} for n in range(245, 250)]
    assert same(highlight(rng), highlight(as_list))
    assert same(highlight(rng), scene("1tup", copy.deepcopy(GREY),
                                      *(comp(s, rep("ball_and_stick", col("red"))) for s in as_list)))
    t = mvs._entry_table("1tup")
    row = (t.selector(R248) & -t.selector(R248)).bit_length() - 1
    label = {"label_asym_id": t.columns["label_asym_id"][row], "label_seq_id": t.columns["label_seq_id"][row]}
    assert label["label_asym_id"] != "A"            # 1TUP: author chain A is label chain C
    assert same(highlight(R248), highlight(label))
    # the same numbers in the other numbering are other atoms
    assert not g(highlight(R248), highlight({"label_asym_id": "A", "label_seq_id": 248}))["success"]


def test_nested_colour_and_flat_components_are_the_same_drawing():
    nested = scene("1tup", comp("polymer", rep("cartoon", col("gray"), col("red", {"auth_asym_id": "A"}))))
    flat = scene("1tup", *(comp({"auth_asym_id": c}, rep("cartoon", col("red" if c == "A" else "gray")))
                           for c in "ABCEF"))
    assert same(nested, flat)
    # colour nodes apply in order: a later one without a selector repaints everything
    undone = scene("1tup", comp("polymer", rep("cartoon", col("red", {"auth_asym_id": "A"}), col("gray"))))
    assert same(scene("1tup", comp("polymer", rep("cartoon", col("gray")))), undone)
    assert not g(nested, undone)["success"]


def test_no_colour_node_is_white_and_no_opacity_node_is_opaque():
    bare = scene("1tup", comp("polymer", rep("cartoon")))
    assert same(bare, scene("1tup", comp("polymer", rep("cartoon", col("white"),
                                                        {"kind": "opacity", "params": {"opacity": 1}}))))
    assert not g(bare, scene("1tup", comp("polymer", rep("cartoon", col("gray")))))["success"]
    half = scene("1tup", comp("polymer", rep("surface", col("white"), {"kind": "opacity", "params": {"opacity": 0.5}})))
    assert not g(half, scene("1tup", comp("polymer", rep("surface", col("white")))))["success"]
    assert g(half, scene("1tup", comp("polymer", rep("surface", col("white")))))["f1"] == drawn.PARTIAL


def test_two_representations_on_the_same_atoms_are_both_drawn():
    both = scene("1tup", comp("polymer", rep("cartoon", col("gray")), rep("surface", col("gray"))))
    one = scene("1tup", comp("polymer", rep("cartoon", col("gray"))))
    r = g(one, both)                                # the unrequested surface costs precision
    assert not r["success"] and r["recall"] == 1.0 and r["precision"] == 0.5
    r = g(both, one)                                # the missing surface costs recall
    assert not r["success"] and r["recall"] == 0.5 and r["precision"] == 1.0


def test_envelope_file_source_and_child_order_do_not_matter():
    ref = highlight()
    other = {"kind": "single", "metadata": {"version": "1", "timestamp": "2026-01-01T00:00:00Z"},
             "root": json.loads(json.dumps(ref).replace(
                 "https://files.rcsb.org/download/1tup.cif",
                 "https://www.ebi.ac.uk/pdbe/entry-files/download/1tup_updated.cif"))}
    other["root"]["children"][0]["children"][0]["children"][0]["children"].reverse()
    assert same(ref, other)


def test_a_chain_theme_is_matched_by_one_colour_per_chain_and_only_that_way():
    themed = scene("1tup", comp("polymer", rep("cartoon", col("white", theme="chain-id"))))
    colours = dict(zip("ABCEF", ("red", "blue", "green", "orange", "purple")))
    explicit = scene("1tup", *(comp({"auth_asym_id": c}, rep("cartoon", col(k))) for c, k in colours.items()))
    assert g(themed, themed)["success"]
    assert g(themed, explicit)["success"]           # every chain its own colour: "by chain"
    assert not g(explicit, themed)["success"]       # explicit colours are matched by those colours
    two_alike = scene("1tup", *(comp({"auth_asym_id": c}, rep("cartoon", col("red" if c in "AB" else k)))
                                for c, k in colours.items()))
    assert not g(themed, two_alike)["success"]
    assert not g(themed, scene("1tup", comp("polymer", rep("cartoon", col("red")))))["success"]
    # another theme is another colouring
    assert not g(themed, scene("1tup", comp("polymer", rep("cartoon", col("white", theme="element-symbol")))))["success"]


def test_a_chain_theme_on_one_chain_is_matched_only_by_the_theme():
    # 1CBS has one chain: "one colour per chain" would be any colour at all, even the
    # white of an answer that set no colour
    themed = scene("1cbs", comp("polymer", rep("cartoon", col("white", theme="chain-id"))))
    assert g(themed, themed)["success"]
    assert not g(themed, scene("1cbs", comp("polymer", rep("cartoon"))))["success"]
    assert not g(themed, scene("1cbs", comp("polymer", rep("cartoon", col("red")))))["success"]
    assert any("single group" in p for p in
               grader.check_task({"category": "mvs", "reference_mvs": themed}))


# --- wrong answers ---------------------------------------------------------------------

@pytest.mark.parametrize("pred", [
    highlight({"auth_asym_id": "A", "auth_seq_id": 249}),         # neighbour
    highlight({"auth_asym_id": "B", "auth_seq_id": 248}),         # other chain
    highlight(colour="blue"),                                      # wrong colour
    highlight(rtype="spacefill"),                                  # wrong representation
    scene("1tup", copy.deepcopy(GREY)),                            # highlight missing
    scene("1tup", comp(R248, rep("ball_and_stick", col("red")))),  # context missing
    scene("1tup", copy.deepcopy(GREY), comp(R248, rep("ball_and_stick", col("red"))),
          comp("ion", rep("spacefill", col("gray")))),             # something extra
], ids=["neighbour", "other-chain", "colour", "representation", "no-highlight", "no-context", "extra"])
def test_wrong_answers_fail_and_keep_partial_credit(pred):
    r = g(highlight(), pred)
    assert not r["success"] and 0 < r["f1"] < 1


def test_unrequested_drawing_costs_precision_and_missing_drawing_costs_recall():
    ref = scene("1tup", comp(R248, rep("ball_and_stick", col("red"))))
    extra = g(ref, highlight())
    assert extra["recall"] == 1.0 and extra["precision"] < 1.0 and not extra["success"]
    missing = g(highlight(), ref)
    assert missing["precision"] == 1.0 and missing["recall"] < 1.0 and not missing["success"]


def test_an_empty_drawing_scores_zero():
    ref = highlight()
    for nothing in (scene("1tup"), scene("1tup", comp("polymer")),
                    scene("1tup", comp({"auth_asym_id": "zz"}, rep("cartoon", col("gray"))))):
        r = g(ref, nothing)
        assert r["f1"] == r["target_f1"] == 0.0 and not r["success"]


def test_the_wrong_structure_scores_zero():
    r = g(highlight(), json.loads(json.dumps(highlight()).replace("1tup", "1lyz")))
    assert r["f1"] == 0.0 and not r["success"] and not r["same_structure"]


def test_a_file_that_is_loaded_and_never_drawn_changes_nothing():
    ref = highlight()
    unused = {"kind": "download", "params": {"url": "https://files.rcsb.org/download/1lyz.cif"},
              "children": [{"kind": "parse", "params": {"format": "mmcif"}}]}
    pred = copy.deepcopy(ref)
    pred["children"].append(unused)
    assert same(ref, pred)
    drawn_too = json.loads(json.dumps(scene("1lyz", copy.deepcopy(GREY))))["children"][0]
    pred = copy.deepcopy(ref)
    pred["children"].append(drawn_too)
    r = g(ref, pred)
    assert not r["success"] and r["recall"] == 1.0 and r["precision"] < 1.0
    # the right entry loaded but the drawing done on another one: nothing is right
    pred = json.loads(json.dumps(ref).replace("1tup", "1lyz"))
    pred["children"].append(json.loads(json.dumps(unused).replace("1lyz", "1tup")))
    r = g(ref, pred)
    assert r["f1"] == 0.0 and not r["success"]


def test_the_structure_type_is_a_fact():
    model = scene("1tup", copy.deepcopy(GREY))
    assembly = scene("1tup", copy.deepcopy(GREY), structure={"type": "assembly", "assembly_id": "1"})
    assert g(assembly, assembly)["success"]
    r = g(assembly, model)
    assert not r["success"] and 0 < r["f1"] < 1
    assert not g(model, assembly)["success"]
    assert g(assembly, scene("1tup", copy.deepcopy(GREY), structure={"type": "assembly"}))["success"]


# --- decision 17: the target score ------------------------------------------------------

TARGET = {"selector": R248}


def test_target_score_ignores_unrequested_context_but_not_the_target():
    ref = scene("1tup", comp(R248, rep("ball_and_stick", col("red"))))
    with_context = highlight()
    r = g(ref, with_context, target=TARGET)
    assert r["target_f1"] == 1.0 and not r["success"] and r["f1"] < 1.0
    # ... also when the task has no target field (the target is all the reference draws)
    assert g(ref, with_context)["target_f1"] == 1.0
    # and the other way round: the reference has context, the answer has none
    r = g(highlight(), ref, target=TARGET)
    assert r["target_f1"] == 1.0 and not r["success"]


def test_target_score_is_graded():
    ref = highlight()
    assert g(ref, highlight(colour="blue"), target=TARGET)["target_f1"] == drawn.PARTIAL
    assert g(ref, highlight(rtype="spacefill"), target=TARGET)["target_f1"] == 0.0
    assert g(ref, highlight({"auth_asym_id": "A", "auth_seq_id": 249}), target=TARGET)["target_f1"] == 0.0
    assert g(ref, scene("1tup", copy.deepcopy(GREY)), target=TARGET)["target_f1"] == 0.0


def test_target_score_counts_spill_onto_other_atoms():
    ref = highlight()
    everything = scene("1tup", copy.deepcopy(GREY), comp("polymer", rep("ball_and_stick", col("red"))))
    r = g(ref, everything, target=TARGET)
    assert r["target_recall"] == 1.0 and r["target_precision"] < 0.01
    two = [R248, {"auth_asym_id": "A", "auth_seq_id": 249}]
    r = g(ref, highlight(two), target=TARGET)
    assert r["target_recall"] == 1.0 and 0.3 < r["target_precision"] < 0.7


def test_target_score_counts_unrequested_drawing_of_the_target_itself():
    # red sticks were asked for; the answer also wraps the residue in a red surface.
    # That draw is confined to the target, so it is not context: it costs precision.
    ref = scene("1tup", comp(R248, rep("ball_and_stick", col("red"))))
    both = scene("1tup", comp(R248, rep("ball_and_stick", col("red")), rep("surface", col("red"))))
    r = g(ref, both, target=TARGET)
    assert r["target_recall"] == 1.0 and r["target_precision"] == 0.5
    # a cartoon of the whole chain passes through the residue and stays ignored
    assert g(ref, highlight(), target=TARGET)["target_f1"] == 1.0
    # the API track has the same rule: sticks added to a residue that was only to be coloured
    load = API_REF[0]
    sticks = [load, {"action": "color", "data": [{"auth_asym_id": "A", "auth_seq_id": 248, "color": "red",
                                                    "representation": "ball-and-stick",
                                                    "representationColor": "red"}]}]
    r = grader.grade_task(API_TASK, sticks)
    assert r["target_recall"] == 1.0 and r["target_precision"] < 1.0 and not r["success"]


def test_target_can_be_given_in_either_selection_language():
    ref = highlight()
    a = g(ref, highlight(colour="blue"), target={"selector": R248})
    b = g(ref, highlight(colour="blue"), target={"data": [{"auth_asym_id": "A", "auth_seq_id": 248}]})
    assert a["target_f1"] == b["target_f1"] == drawn.PARTIAL


# --- camera ----------------------------------------------------------------------------

def test_focus_is_graded_by_its_target_atoms_when_the_reference_has_one():
    def focused(sel, extra=()):
        return scene("1tup", copy.deepcopy(GREY), comp(sel, rep("ball_and_stick", col("red")), FOCUS), *extra)
    ref = focused(R248)
    assert g(ref, ref)["success"]
    # the focus may sit on another component, addressed another way, with camera hints
    elsewhere = scene("1tup", copy.deepcopy(GREY), comp(R248, rep("ball_and_stick", col("red"))),
                      comp([R248], {"kind": "focus", "params": {"direction": [0, 0, -1], "radius_factor": 2}}))
    assert g(ref, elsewhere)["success"]
    assert not g(ref, highlight())["success"]                    # no focus: the whole structure is framed
    other = scene("1tup", copy.deepcopy(GREY), comp(R248, rep("ball_and_stick", col("red"))),
                  comp({"auth_asym_id": "B", "auth_seq_id": 175}, FOCUS))
    assert not g(ref, other)["success"]
    # several focus nodes frame their union
    both = scene("1tup", copy.deepcopy(GREY), comp(R248, rep("ball_and_stick", col("red")), FOCUS),
                 comp({"auth_asym_id": "B", "auth_seq_id": 175}, FOCUS))
    assert not g(ref, both)["success"]


def test_an_unrequested_focus_is_not_counted_and_camera_numbers_never_are(monkeypatch):
    ref = highlight()
    zoomed = scene("1tup", copy.deepcopy(GREY), comp(R248, rep("ball_and_stick", col("red")), FOCUS))
    assert g(ref, zoomed)["success"]
    with_camera = copy.deepcopy(ref)
    with_camera["children"].append({"kind": "camera", "params": {
        "target": [0, 0, 0], "position": [0, 0, 100], "up": [0, 1, 0]}})
    assert g(ref, with_camera)["success"]
    # "show the whole molecule" can be asked for: a focus on everything is a focus fact
    whole = scene("1tup", comp("polymer", rep("cartoon", col("gray")), FOCUS),
                  comp(R248, rep("ball_and_stick", col("red"))))
    assert g(whole, ref)["success"] and not g(whole, zoomed)["success"]
    # the stricter reading is one switch away
    monkeypatch.setattr(drawn, "GRADE_UNREQUESTED_FOCUS", True)
    assert not g(ref, zoomed)["success"]


# --- other scene facts -------------------------------------------------------------------

def test_labels_tooltips_and_interaction_flags_are_facts():
    def labelled(text, sel=R248):
        return scene("1tup", comp(sel, rep("ball_and_stick", col("red")), {"kind": "label", "params": {"text": text}}))
    assert g(labelled("Arg 248"), labelled("  ARG  248 "))["success"]      # case and spaces
    assert not g(labelled("Arg 248"), labelled("Arg 249"))["success"]
    assert not g(labelled("Arg 248"), scene("1tup", comp(R248, rep("ball_and_stick", col("red")))))["success"]
    assert not g(scene("1tup", comp(R248, rep("ball_and_stick", col("red")))), labelled("Arg 248"))["success"]
    flag = {"molstar_show_non_covalent_interactions": True}
    with_flag = scene("1tup", comp(R248, rep("ball_and_stick", col("red")), custom=flag))
    assert g(with_flag, with_flag)["success"]
    assert not g(with_flag, scene("1tup", comp(R248, rep("ball_and_stick", col("red")))))["success"]


def test_representation_size_and_surface_kind_are_not_graded():
    a = scene("1tup", comp("polymer", rep("surface", col("gray"), surface_type="gaussian", size_factor=2)))
    assert same(scene("1tup", comp("polymer", rep("surface", col("gray")))), a)


# --- colour ------------------------------------------------------------------------------

def test_palette_colours_cannot_pass_for_one_another():
    names = drawn.TASK_PALETTE
    closest = min(drawn.color_distance(drawn.COLOR_NAMES[a], drawn.COLOR_NAMES[b])
                  for a, b in itertools.combinations(names, 2))
    assert closest == 55 and closest > drawn.COLOR_TOLERANCE
    for a, b in itertools.combinations(names, 2):
        assert not drawn.color_eq(drawn.COLOR_NAMES[a], drawn.COLOR_NAMES[b]), (a, b)


def test_every_colour_a_task_asks_for_is_in_the_palette():
    used = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("color", "non_selected_color", "representationColor") and isinstance(v, str) \
                        and not v.startswith("#"):
                    used.add("gray" if v == "grey" else v)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    for path in (REPO / "tasks").glob("*/*.json"):
        task = json.loads(path.read_text())
        walk(task.get("reference_mvs"))
        walk(task.get("reference"))
    assert used <= set(drawn.TASK_PALETTE), sorted(used - set(drawn.TASK_PALETTE))


def test_colour_spellings_mol_star_reads_and_rejects():
    red = (255, 0, 0)
    for ok in ("red", "#ff0000", "#FF0000", "#f00", " red "):
        assert drawn.mvs_color(ok) == red, ok
    assert drawn.mvs_color("grey") == drawn.mvs_color("gray") == (128, 128, 128)
    for bad in ("RED", "Red", "rgb(255,0,0)", "ff0000", 0xFF0000, [255, 0, 0], "", None):
        assert drawn.mvs_color(bad)[0] == "invalid", bad      # Mol* rejects the scene
    assert not g(highlight(), highlight(colour="RED"))["success"]


def test_one_tolerance_on_both_tracks():
    assert ps.COLOR_TOLERANCE is drawn.COLOR_TOLERANCE == 32
    assert ps.COLOR_NAMES is drawn.COLOR_NAMES and ps.color_eq is drawn.color_eq
    assert g(highlight(), highlight(colour="#e01010"))["success"]          # within 32 of red
    assert not g(highlight(), highlight(colour="#d02020"))["success"]      # 47 away
    assert not g(highlight(colour="gray"), highlight(colour="lightgray"))["success"]
    load = {"action": "load", "molecule_id": "1tup"}
    paint = lambda c: [load, {"action": "color", "data": [{"auth_asym_id": "A", "auth_seq_id": 248, "color": c}]}]  # noqa: E731
    assert grader.grade(paint("red"), paint("#e01010"))["success"]
    assert not grader.grade(paint("red"), paint("#d02020"))["success"]


# --- one entry point, one result shape ---------------------------------------------------

MVS_TASK = {"id": "t-mvs", "category": "mvs", "reference_mvs": highlight(), "target": TARGET}
API_REF = [{"action": "load", "molecule_id": "1tup"},
           {"action": "color", "data": [{"auth_asym_id": "A", "auth_seq_id": 248, "color": "red"}]}]
API_TASK = {"id": "t-api", "category": "api_calling", "reference": API_REF,
            "target": {"data": [{"auth_asym_id": "A", "auth_seq_id": 248}]}}


def test_grade_task_returns_the_same_keys_on_both_tracks():
    answers = [(MVS_TASK, highlight()), (MVS_TASK, highlight(colour="blue")), (MVS_TASK, [1, 2]),
               (MVS_TASK, {"kind": "component"}), (MVS_TASK, scene("1lyz")),
               (API_TASK, API_REF), (API_TASK, [{"action": "load", "molecule_id": "1tup"}]),
               (API_TASK, "nonsense"), (API_TASK, [{"action": "load", "molecule_id": "1lyz"}])]
    for task, answer in answers:
        r = grader.grade_task(task, answer)
        assert set(drawn.RESULT_KEYS) <= set(r), (task["id"], sorted(set(drawn.RESULT_KEYS) - set(r)))
        assert 0.0 <= r["f1"] <= 1.0 and 0.0 <= r["target_f1"] <= 1.0
        assert isinstance(r["success"], bool)
    assert grader.grade_task(MVS_TASK, highlight())["outcome"] == "unchecked"
    assert grader.grade_task(MVS_TASK, {"kind": "component"})["outcome"] == "not_mvs"
    assert grader.grade_task(API_TASK, API_REF)["outcome"] == "valid"
    assert grader.grade_task(API_TASK, [{"action": "no_such_action"}])["outcome"] == "invalid_api"
    assert grader.grade_task(MVS_TASK, highlight())["grader"] == "drawn"
    assert grader.grade_task(API_TASK, API_REF)["grader"] == "state"


def test_api_target_score_ignores_unrequested_changes_and_is_graded():
    load = API_REF[0]
    right = grader.grade_task(API_TASK, API_REF)
    assert right["success"] and right["target_f1"] == 1.0
    # an unrequested global style: not a success, the target is still right
    extra = [load, {"action": "set_property", "name": "spin", "value": True}, API_REF[1]]
    r = grader.grade_task(API_TASK, extra)
    assert not r["success"] and r["target_f1"] == 1.0
    blue = [load, {"action": "color", "data": [{"auth_asym_id": "A", "auth_seq_id": 248, "color": "blue"}]}]
    assert grader.grade_task(API_TASK, blue)["target_f1"] == drawn.PARTIAL
    neighbour = [load, {"action": "color", "data": [{"auth_asym_id": "A", "auth_seq_id": 249, "color": "red"}]}]
    assert grader.grade_task(API_TASK, neighbour)["target_f1"] == 0.0
    assert grader.grade_task(API_TASK, [load])["target_f1"] == 0.0
    chain = [load, {"action": "color", "data": [{"auth_asym_id": "A", "color": "red"}]}]
    r = grader.grade_task(API_TASK, chain)
    assert r["target_recall"] == 1.0 and r["target_precision"] < 0.05
    # without a target field the target is everything the reference changes
    no_field = {k: v for k, v in API_TASK.items() if k != "target"}
    assert grader.grade_task(no_field, extra)["target_f1"] == 1.0


def test_api_unrequested_focus_is_not_counted():
    load = API_REF[0]
    zoomed = API_REF + [{"action": "focus", "data": [{"auth_asym_id": "A", "auth_seq_id": 248}]}]
    assert grader.grade(API_REF, zoomed)["success"]
    assert not grader.grade(zoomed, API_REF)["success"]            # a requested focus is graded
    other = API_REF + [{"action": "focus", "data": [{"auth_asym_id": "B", "auth_seq_id": 175}]}]
    assert not grader.grade(zoomed, other)["success"]
    assert grader.grade([load], [load])["success"]
    assert grader.grade(API_REF, [load])["f1"] == 0.0              # a bare load still scores 0
    assert grader.grade(zoomed, [load])["f1"] == 0.0


def test_accepted_alternatives_take_the_best_match():
    alt = highlight({"auth_asym_id": "B", "auth_seq_id": 248})
    task = {**MVS_TASK, "accepted": [alt]}
    task.pop("target")
    r = grader.grade_task(task, alt)
    assert r["success"] and r["matched_reference"] == 1
    assert grader.grade_task(task, highlight())["matched_reference"] == 0
    assert not grader.grade_task(task, highlight({"auth_asym_id": "C", "auth_seq_id": 248}))["success"]
    api_alt = [API_REF[0], {"action": "color", "data": [{"auth_asym_id": "B", "auth_seq_id": 248, "color": "red"}]}]
    api_task = {"category": "api_calling", "reference": API_REF, "accepted": [api_alt]}
    assert grader.grade_task(api_task, api_alt)["matched_reference"] == 1


def test_an_accepted_alternative_is_scored_on_a_target_that_fits_it():
    # the task's target names Arg248 of chain A; the accepted alternative is about
    # chain B. An answer that is exactly the alternative has target score 1.
    alt = highlight({"auth_asym_id": "B", "auth_seq_id": 248})
    task = {**MVS_TASK, "accepted": [alt]}
    assert "target" in task
    r = grader.grade_task(task, alt)
    assert r["success"] and r["matched_reference"] == 1 and r["target_f1"] == 1.0
    # with its own target the alternative is scored on that: context is ignored again
    task["accepted_targets"] = [{"selector": {"auth_asym_id": "B", "auth_seq_id": 248}}]
    bare_alt = scene("1tup", comp({"auth_asym_id": "B", "auth_seq_id": 248}, rep("ball_and_stick", col("red"))))
    r = grader.grade_task(task, bare_alt)
    assert not r["success"] and r["matched_reference"] == 1 and r["target_f1"] == 1.0
    assert grader.check_task(task) == []
    task["accepted_targets"] = [{"selector": {"auth_asym_id": "Q", "auth_seq_id": 248}}]   # no such chain
    assert any("accepted_targets[0]" in p for p in grader.check_task(task))
    # an alternative about the same atoms keeps the task's target
    same_atoms = highlight(colour="blue")
    r = grader.grade_task({**MVS_TASK, "accepted": [same_atoms]},
                          scene("1tup", comp(R248, rep("ball_and_stick", col("blue")))))
    assert r["matched_reference"] == 1 and r["target_f1"] == 1.0 and not r["success"]
    # API track
    api_alt = [API_REF[0], {"action": "color", "data": [{"auth_asym_id": "B", "auth_seq_id": 248, "color": "red"}]}]
    r = grader.grade_task({**API_TASK, "accepted": [api_alt]}, api_alt)
    assert r["success"] and r["matched_reference"] == 1 and r["target_f1"] == 1.0


def test_a_bare_load_asked_for_and_given_is_right_on_every_score():
    load = [{"action": "load", "molecule_id": "1tup"}]
    r = grader.grade_task({"category": "api_calling", "reference": load}, load)
    assert r["success"] and r["f1"] == 1.0 and r["target_f1"] == 1.0
    assert grader.check_task({"category": "api_calling", "reference": load}) == []


def test_a_follow_up_is_graded_on_its_final_state_only():
    # the context (start scene) must load; it is not compared with anything
    start = scene("1tup", copy.deepcopy(GREY))
    task = {"id": "f", "category": "mvs", "context": start, "reference_mvs": highlight()}
    assert grader.check_task(task) == []
    assert grader.grade_task(task, highlight())["success"]
    assert not grader.grade_task(task, start)["success"]            # nothing was changed
    # "no change" is a valid answer when the reference is the start scene
    unchanged = {"id": "n", "category": "mvs", "context": start, "reference_mvs": copy.deepcopy(start)}
    assert grader.grade_task(unchanged, start)["success"]
    assert any("context" in p for p in grader.check_task({**task, "context": {"kind": "component"}}))
    api_task = {"category": "api_calling", "context": [API_REF[0]], "reference": API_REF}
    assert grader.check_task(api_task) == []
    # a rebuild that lands on the right state is right
    rebuilt = [API_REF[0], {"action": "color", "data": [{"auth_asym_id": "B", "color": "blue"}]}, API_REF[1]]
    assert grader.grade_task(api_task, rebuilt)["success"]
    assert any("context" in p for p in grader.check_task({**api_task, "context": [{"action": "focus"}]}))


def test_check_task_finds_ungradable_tasks():
    assert grader.check_task(MVS_TASK) == [] and grader.check_task(API_TASK) == []
    no_table = {"category": "mvs", "reference_mvs": json.loads(json.dumps(highlight()).replace("1tup", "9zzz"))}
    assert any("atom table" in p for p in grader.check_task(no_table))
    empty = {"category": "mvs", "reference_mvs": highlight({"auth_asym_id": "A", "auth_seq_id": 99999})}
    assert any("selects no atoms" in p for p in grader.check_task(empty))
    for nowhere in ({"auth_asym_id": "zz"}, "water"):     # no atoms; atoms the reference does not draw
        assert any("target" in p for p in grader.check_task({**MVS_TASK, "target": {"selector": nowhere}}))
    api_no_table = {"category": "api_calling", "reference": [{"action": "load", "molecule_id": "9zzz"},
                                                             {"action": "set_visual_style", "style": "cartoon"}]}
    assert any("atom table" in p for p in grader.check_task(api_no_table))


def test_every_task_in_the_corpus_is_gradable_and_its_reference_succeeds():
    from molbench.runner import load_tasks
    for task in load_tasks(None):
        if task.get("category") not in ("mvs", "api_calling"):
            continue
        ref = task.get("reference_mvs", task.get("reference"))
        r = grader.grade_task(task, ref)
        assert r["success"] and r["f1"] == 1.0 and r["target_f1"] == 1.0, task["id"]
        problems = grader.check_task(task)
        if task["id"] == "api-005":     # the superposition view: compared by its settings
            continue
        assert problems == [], (task["id"], problems)


def test_junk_never_raises():
    junk = [None, 5, "x", [], {}, {"root": 5}, {"kind": "root", "children": "x"},
            {"kind": "root", "children": [{"kind": "download", "params": {"url": 5}, "children": [
                {"kind": "structure", "children": [{"kind": "component", "params": {"selector": 7},
                                                    "children": [{"kind": "representation", "params": []},
                                                                 {"kind": "focus", "params": None}]}]}]}]},
            scene("1tup", comp([{"auth_seq_id": "248"}, 3, None], rep(None, col(None), {"kind": "opacity", "params": {"opacity": "x"}}))),
            scene("1tup", comp({"instance_id": "ASM_1"}, rep("cartoon")))]
    for j in junk:
        r = grader.grade_task(MVS_TASK, j)
        assert not r["success"] and set(drawn.RESULT_KEYS) <= set(r)
        assert not grader.grade_task(API_TASK, j)["success"]
