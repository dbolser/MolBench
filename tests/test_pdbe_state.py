"""
The API-track state grader: selections, replay semantics and scoring.

Every behaviour asserted here was read from pdbe-molstar 3.3.2's source and then
checked in the running viewer (``scripts/check_api_refs.py --viewer`` runs the same
kinds of action lists in headless Chromium and compares atom for atom). These tests
are the offline, browser-free record of those results.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from molbench import grader
from molbench import pdbe_state as ps
from molbench.atoms import load_table

TASKS = pathlib.Path(__file__).resolve().parent.parent / "tasks" / "api_calling"


def L(entry, **kw):
    return {"action": "load", "molecule_id": entry, **kw}


def C(data, **kw):
    return {"action": "color", "data": data, **kw}


def STYLE(s):
    return {"action": "set_visual_style", "style": s}


def PROP(n, v):
    return {"action": "set_property", "name": n, "value": v}


def comps(entry, param):
    """(residue name, author number) of the residues a selection hits."""
    t = load_table(entry)
    m = ps.resolve_param(t, param, entry)
    c = t.columns
    return {(c["label_comp_id"][i], c["auth_seq_id"][i]) for i in range(t.n) if m >> i & 1}


def n(entry, param):
    return ps.resolve_param(load_table(entry), param, entry).bit_count()


def task(num):
    return json.loads(next(TASKS.glob(f"{num}_*.json")).read_text())


# --- selections (getQueryObject) -----------------------------------------------------

def test_residue_number_is_label_numbering_auth_seq_id_is_author():
    # 3PTB: author His57 is label_seq_id 40; label 57 is author Val75.
    assert comps("3ptb", {"residue_number": 57}) == {("VAL", 75)}
    assert comps("3ptb", {"auth_seq_id": 57}) == {("HIS", 57)}
    assert comps("3ptb", {"auth_residue_number": 57}) == {("HIS", 57)}
    assert comps("3ptb", {"residue_number": 40}) == {("HIS", 57)}
    assert n("3ptb", {"auth_seq_id": 57}) == 10


def test_label_and_author_chains_are_not_pooled_and_label_wins():
    # 1TUP: label chain A is DNA (author chain E); author chain A is p53 (label chain C).
    t = load_table("1tup")
    label_a = ps.resolve_param(t, {"struct_asym_id": "A"})
    auth_a = ps.resolve_param(t, {"auth_asym_id": "A"})
    assert label_a and auth_a and not (label_a & auth_a)
    assert ps.resolve_param(t, {"struct_asym_id": "A", "auth_asym_id": "A"}) == label_a


def test_comp_id_overrides_residue_numbers():
    every_his = n("3ptb", {"label_comp_id": "HIS"})
    assert every_his > 10
    assert n("3ptb", {"label_comp_id": "HIS", "auth_seq_id": 57}) == every_his
    assert n("3ptb", {"label_comp_id": "his"}) == 0          # case-sensitive


def test_ranges():
    assert {c for _, c in comps("3ptb", {"auth_asym_id": "A", "start_auth_residue_number": 55,
                                         "end_auth_residue_number": 57})} == {55, 56, 57}
    label = comps("3ptb", {"struct_asym_id": "A", "start_residue_number": 38, "end_residue_number": 40})
    assert {c for _, c in label} == {55, 56, 57}
    # start == end is one residue; a reversed range is not a residue test at all, so the
    # next key that applies (here auth_seq_id) decides
    assert comps("3ptb", {"start_residue_number": 40, "end_residue_number": 40}) == {("HIS", 57)}
    assert comps("3ptb", {"start_residue_number": 40, "end_residue_number": 30,
                          "auth_seq_id": 195}) == {("SER", 195)}
    assert n("3ptb", {"start_residue_number": 40, "end_residue_number": 30}) == load_table("3ptb").n


def test_values_are_compared_strictly():
    assert n("3ptb", {"auth_seq_id": "57"}) == 0             # a string is not a number
    assert n("3ptb", {"auth_seq_id": None}) == 0             # null is defined, and equals nothing
    assert n("3ptb", {"entity_id": 1}) == 0                  # entity ids are strings
    assert n("3ptb", {"entity_id": "1"}) == n("3ptb", {"struct_asym_id": "A"})
    assert n("3ptb", {}) == load_table("3ptb").n             # no test: everything
    assert n("3ptb", {"residue_number": 0}) == 72            # non-polymer residues read as 0


def test_atoms_and_atom_id():
    assert n("3ptb", {"auth_seq_id": 57, "atoms": ["CA", "CB"]}) == 2
    assert n("3ptb", {"atom_id": [1, 2, 3], "atoms": ["CA"]}) == 3     # atom_id overrides atoms


def test_uniprot_selectors_wait_for_frozen_sifts(monkeypatch):
    ref = [L("1tup"), C([{"uniprot_accession": "P04637", "uniprot_residue_number": 248, "color": "red"}])]
    t = load_table("1tup")
    arg248 = ps.resolve_param(t, {"auth_seq_id": 248, "label_comp_id": None}) & ps.resolve_param(t, {"label_comp_id": "ARG"})
    assert arg248.bit_count() == 33                           # Arg248 of chains A, B and C
    state = ps.replay(ref)
    from molbench import sifts
    if hasattr(sifts, "uniprot_atoms") and sifts.uniprot_atoms("1tup", "P04637", 248) is not None:
        # the frozen SIFTS tables are in: the hook resolves by itself
        assert not state.unresolved and state.paint[0][0] == arg248
    else:
        assert state.unresolved and "SIFTS" in state.unresolved[0]
        assert not state.paint                                # unresolved selects nothing
    # another mapping can be plugged in with one assignment
    monkeypatch.setattr(ps, "uniprot_residue_atoms",
                        lambda entry, acc, num: arg248 if (entry, acc, num) == ("1tup", "P04637", 248) else 0)
    state = ps.replay(ref)
    assert not state.unresolved and state.paint[0][0] == arg248
    rng = [L("1tup"), C([{"uniprot_accession": "P04637", "start_uniprot_residue_number": 247,
                          "end_uniprot_residue_number": 249, "color": "red"}])]
    assert ps.replay(rng).paint[0][0] == arg248


# --- colours -------------------------------------------------------------------------

def test_colour_formats():
    red = (255, 0, 0)
    assert ps.normalize_color({"r": 255, "g": 0, "b": 0}) == red
    assert ps.normalize_color("#ff0000") == ps.normalize_color("#FF0000") == red
    assert ps.normalize_color("red") == red
    assert ps.normalize_color("green") == (0, 128, 0)        # the CSS/Mol* value
    assert ps.normalize_color("Red") == ps.GREY               # names are lower-case
    assert ps.normalize_color("ff0000") == ps.GREY
    assert ps.normalize_color("#f00") == (0, 15, 0)           # Number('0xf00'), not CSS shorthand
    assert ps.css_color("#f00") == red                        # bg_color is parsed as CSS
    assert ps.css_color("White") == (255, 255, 255)
    assert len(ps.COLOR_NAMES) > 140


def test_colour_formats_are_equivalent_answers():
    def ans(colour):
        return [L("1bna"), STYLE("cartoon"), C([{"auth_asym_id": "A", "color": colour}])]
    ref = ans("blue")
    for same in ({"r": 0, "g": 0, "b": 255}, "#0000ff", {"r": 10, "g": 20, "b": 235}):
        assert ps.grade_state(ref, ans(same))["success"]
    for other in ("red", {"r": 30, "g": 90, "b": 220}, "Blue"):
        res = ps.grade_state(ref, ans(other))
        assert not res["success"] and 0 < res["f1"] < 1     # right atoms, wrong colour: partial


# --- select() semantics ----------------------------------------------------------------

def test_a_second_colour_call_wipes_the_first_unless_kept():
    one = C([{"auth_asym_id": "A", "color": "blue"}])
    two = C([{"auth_asym_id": "B", "color": "red"}])
    both = [L("1bna"), C(one["data"] + two["data"])]
    assert not ps.grade_state(both, [L("1bna"), one, two])["success"]
    assert ps.grade_state(both, [L("1bna"), one, dict(two, keep_colors=True)])["success"]
    assert ps.grade_state([L("1bna"), two], [L("1bna"), one, two])["success"]


def test_added_representations_are_cleared_or_kept():
    a = C([{"auth_seq_id": 57, "color": "red", "representation": "ball-and-stick"}])
    b = C([{"auth_seq_id": 195, "color": "red", "representation": "ball-and-stick"}])
    s = ps.replay([L("3ptb"), a, b])
    assert len(s.added) == 1 and len(s.paint) == 1
    s = ps.replay([L("3ptb"), a, dict(b, keep_representations=True)])
    assert len(s.added) == 2 and len(s.paint) == 1
    assert not ps.replay([L("3ptb"), a, {"action": "clear_selection"}]).added


def test_colour_paints_existing_representations_not_added_ones():
    ref = task("003")
    july = [L("1hho"), STYLE("cartoon"), C([{"label_comp_id": "HEM", "representation": "ball-and-stick",
                                             "color": {"r": 255, "g": 165, "b": 0}}])]
    res = grader.grade(ref["reference"], july)
    assert not res["success"]            # the added ball-and-stick stays element-coloured
    # ... while without a global style the heme's own ball-and-stick takes the colour
    default_view = [L("1hho"), PROP("hide_water", True), C([{"label_comp_id": "HEM", "color": "orange"}])]
    cartoon_view = [L("1hho"), PROP("hide_water", True), C([
        {"label_comp_id": "HEM", "color": "orange", "representation": "ball-and-stick",
         "representationColor": "orange"}])]
    assert ps.grade_state(default_view, cartoon_view)["success"]


def test_missing_colour_is_default_orange_and_null_is_no_paint():
    absent = ps.replay([L("3ptb"), C([{"auth_seq_id": 57, "sideChain": True}])])
    assert absent.paint[0][1] == ps.DEFAULT_SELECT_PAINT and absent.added[0][1] == "ball-and-stick"
    null = ps.replay([L("3ptb"), C([{"auth_seq_id": 57, "sideChain": True, "color": None}])])
    assert not null.paint and null.added
    assert not ps.compare(absent, null)["success"]


def test_inapplicable_added_type_falls_back():
    s = ps.replay([L("3ptb"), C([{"label_comp_id": "BEN", "representation": "cartoon", "color": None}])])
    atoms, rep, _ = s.added[0]
    assert s.added_type(rep, atoms) == "ball-and-stick"       # a ligand has no cartoon
    his = ps.resolve_param(s.table, {"auth_seq_id": 57})
    assert s.added_type("ellipsoid", his) == "cartoon"         # no anisotropic B-factors
    assert s.added_type("molecular-surface", his) == "molecular-surface"


# --- order and reloads -------------------------------------------------------------------

def test_order_matters_style_after_colour_reloads_and_loses_it():
    colour = C([{"auth_asym_id": "A", "color": "blue"}, {"auth_asym_id": "B", "color": "red"}])
    ref = [L("1bna"), STYLE("cartoon"), colour]
    late_style = [L("1bna"), colour, STYLE("cartoon")]
    res = ps.grade_state(ref, late_style)
    assert not res["success"] and res["f1"] < 1
    assert grader.grade_sequence(ref, late_style)["f1"] == 1.0   # the legacy grader cannot see it
    # the same style twice is no change, so no reload
    assert ps.grade_state(ref, [L("1bna"), STYLE("cartoon"), colour, STYLE("cartoon")])["success"]


def test_calls_before_load_do_nothing_and_a_new_load_starts_clean():
    colour = C([{"auth_asym_id": "A", "color": "blue"}])
    assert ps.grade_state([L("1bna")], [colour, L("1bna")])["success"]
    assert ps.grade_state([L("1bna")], [L("3ptb"), colour, L("1bna")])["success"]
    # tooltips and hide flags are traits: they survive the reload
    tip = {"action": "tooltips", "data": [{"auth_seq_id": 5, "tooltip": "x"}]}
    assert ps.grade_state([L("1bna"), STYLE("cartoon"), tip], [L("1bna"), tip, STYLE("cartoon")])["success"]


# --- what counts as a fact --------------------------------------------------------------------

def test_hiding_a_component_the_structure_lacks_states_nothing():
    assert "water" not in ps.replay([L("1mbn")]).components()    # the July api-001 entry
    assert ps.grade_state([L("1mbn")], [L("1mbn"), PROP("hide_water", True)])["success"]
    assert not ps.grade_state([L("1a6m")], [L("1a6m"), PROP("hide_water", True)])["success"]


def test_same_picture_same_score():
    # under a cartoon style waters are not drawn, so hide_water changes nothing
    a = [L("1ubq"), STYLE("cartoon"), PROP("hide_water", True)]
    assert ps.grade_state(a, [L("1ubq"), STYLE("cartoon")])["success"]
    # a default view is cartoon for polymer already; the style still removes the waters
    assert not ps.grade_state(a, [L("1ubq")])["success"]
    assert ps.grade_state([L("1ubq"), PROP("hide_water", True)], [L("1ubq"), STYLE("cartoon")])["success"]


def test_ui_colours_by_method_or_property_and_clear_highlight():
    by_method = [L("1hho"), {"action": "set_color", "highlight": {"r": 255, "g": 255, "b": 0}, "select": "cyan"}]
    by_prop = [L("1hho"), PROP("highlight_color", "#ffff00"), PROP("select_color", "#00FFFF")]
    assert ps.grade_state(by_method, by_prop)["success"]
    cleared = ps.replay(by_method + [{"action": "clear_highlight"}])
    assert cleared.highlight_color == ps.DEFAULT_HIGHLIGHT and cleared.select_color == (0, 255, 255)
    reset = ps.replay(by_method + [{"action": "reset", "selectColor": True}])
    assert reset.select_color == ps.DEFAULT_SELECT


def test_tooltip_text_and_focus_tolerances():
    def tip(text, **sel):
        return [L("1aki"), {"action": "tooltips", "data": [{**sel, "tooltip": text}]}]
    ref = tip("catalytic glutamate", auth_asym_id="A", auth_seq_id=35)
    assert ps.grade_state(ref, tip("Catalytic  Glutamate", struct_asym_id="A", residue_number=35))["success"]
    assert not ps.grade_state(ref, tip("glutamate", auth_asym_id="A", auth_seq_id=35))["success"]
    assert not ps.grade_state(ref, tip("catalytic glutamate", auth_asym_id="A", auth_seq_id=36))["success"]

    def focus(**sel):
        return [L("1aki"), {"action": "focus", "data": [sel]}]
    whole = focus(auth_asym_id="A", auth_seq_id=35)
    assert ps.grade_state(whole, focus(auth_asym_id="A", auth_seq_id=35, atoms=["CA"]))["success"]
    assert not ps.grade_state(whole, focus(auth_asym_id="A", auth_seq_id=52))["success"]
    # a camera reset undoes the focus; an empty focus leaves the camera alone
    assert ps.grade_state([L("1aki")], whole + [{"action": "reset", "camera": True}])["success"]
    assert ps.grade_state(whole, whole + [{"action": "focus", "data": [{"label_comp_id": "XXX"}]}])["success"]


def test_structure_identity():
    assert ps.canonical_entry("1HHO", None) == "1hho"
    af = "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v{}.{}"
    assert ps.canonical_entry(None, {"url": af.format(4, "cif"), "format": "cif"}) == "af-p04637-f1"
    assert ps.canonical_entry("x", {"url": af.format(6, "bcif"), "format": "bcif"}) == "af-p04637-f1"
    assert ps.canonical_entry(None, {"url": "https://files.rcsb.org/download/3PTB.cif", "format": "cif"}) == "3ptb"
    assert ps.canonical_entry(None, {"url": "https://www.ebi.ac.uk/pdbe/entry-files/3ptb_updated.cif",
                                     "format": "cif"}) == "3ptb"
    assert ps.canonical_entry(None, {"url": af.format(6, "cif")}) is None      # no format: nothing loads


def test_alphafold_model_needs_custom_data():
    t = task("016")
    july = [{"action": "load", "molecule_id": "P04637", "alphafold": True}, STYLE("cartoon")]
    assert not grader.grade(t["reference"], july)["success"]
    assert grader.grade(t["reference"], july)["f1"] < 0.5
    # an AlphaFold DB identifier is not a PDB id either: PDBe's model server has no such entry
    by_af_id = [{"action": "load", "molecule_id": "AF-P04637-F1", "alphafold": True}]
    assert not grader.grade(t["reference"], by_af_id)["success"]
    assert ps.canonical_entry("AF-P04637-F1", None) == "id:af-p04637-f1"
    flag_only = [a for a in t["reference"] if a["action"] == "load"]
    assert not grader.grade(t["reference"], flag_only)["success"]     # loaded but not pLDDT-coloured


def test_assembly_is_a_fact():
    ref = [L("1hho", assembly_id="1")]
    assert ps.grade_state(ref, [L("1hho", assembly_id="preferred")])["success"]
    assert ps.grade_state(ref, [L("1hho", assembly_id=1)])["success"]
    assert not ps.grade_state(ref, [L("1hho")])["success"]
    # set after the load it is never read
    assert not ps.grade_state(ref, [L("1hho"), PROP("assembly_id", "1")])["success"]


def test_superposition_is_compared_by_settings():
    t = task("005")
    assert grader.grade(t["reference"], t["reference"])["grader"] == "state"
    assert not grader.grade(t["reference"], [L("2hhb"), PROP("superposition", True),
                                             PROP("bg_color", "#FFFFFF")])["success"]
    assert grader.grade(t["reference"], [PROP("bg_color", "white"), PROP("superposition", True),
                                         L("p69905")])["success"]
    assert ps.replay(t["reference"]).entry == "id:p69905"


# --- scoring ------------------------------------------------------------------------------

def test_trypsin_triad_author_numbering_succeeds_label_57_fails():
    t = task("019")
    ref = t["reference"]

    def answer(key, nums, chain_key="auth_asym_id"):
        sel = [{chain_key: "A", key: x} for x in nums]
        return [L("3ptb"), STYLE("cartoon"),
                C([{**s, "color": "magenta", "representation": "ball-and-stick",
                    "representationColor": "magenta"} for s in sel]),
                {"action": "focus", "data": sel}]
    assert grader.grade(ref, answer("auth_seq_id", (57, 102, 195)))["success"]
    assert grader.grade(ref, answer("auth_residue_number", (57, 102, 195)))["success"]
    assert grader.grade(ref, answer("residue_number", (40, 84, 177), "struct_asym_id"))["success"]
    wrong = grader.grade(ref, answer("residue_number", (57, 102, 195)))
    assert not wrong["success"] and wrong["f1"] < 0.5         # Val75/Ser120/Ser217
    assert grader.grade_sequence(ref, answer("residue_number", (57, 102, 195)))["f1"] == 1.0


def test_trivial_answers_do_not_succeed_on_any_task_with_a_selection():
    for path in sorted(TASKS.glob("*.json")):
        t = json.loads(path.read_text())
        ref = t["reference"]
        if not any(a["action"] in ("color", "focus", "highlight", "tooltips") for a in ref):
            continue
        load = [a for a in ref if a["action"] == "load"]
        style = [a for a in ref if a["action"] == "set_visual_style"]
        for trivial in (load, load + style):
            res = grader.grade_task(t, trivial)
            assert not res["success"], t["id"]
            assert res["f1"] <= 0.75, (t["id"], res["f1"])
        assert grader.grade_task(t, [])["f1"] == 0.0


def test_wrong_structure_scores_low():
    ref = task("008")["reference"]
    other = json.loads(json.dumps(ref).replace("3ptb", "1hho"))
    res = grader.grade(ref, other)
    assert not res["success"] and res["f1"] == 0.0


def test_partial_credit_is_graded():
    ref = [L("1bna"), STYLE("cartoon"), C([{"auth_asym_id": "A", "color": "blue"},
                                           {"auth_asym_id": "B", "color": "red"}])]
    half = [L("1bna"), STYLE("cartoon"), C([{"auth_asym_id": "A", "color": "blue"}])]
    extra = ref + [PROP("spin", True)]
    r_half, r_extra = ps.grade_state(ref, half), ps.grade_state(ref, extra)
    assert r_half["precision"] == 1.0 and r_half["recall"] < 1.0
    assert r_extra["recall"] == 1.0 and r_extra["precision"] < 1.0
    assert not r_half["success"] and not r_extra["success"]


def test_accepted_alternatives():
    ref = [L("1ubq"), C([{"auth_seq_id": 76, "color": "red"}])]
    alt = [L("1ubq"), C([{"auth_seq_id": 75, "color": "red"}])]
    assert not grader.grade(ref, alt)["success"]
    res = grader.grade(ref, alt, accepted=[alt])
    assert res["success"] and res["matched_reference"] == 1


def test_grade_dispatch_and_legacy():
    ref = task("013")["reference"]
    assert grader.grade(ref, ref)["grader"] == "state"
    assert grader.grade(ref, ref, mode="sequence")["grader"] == "sequence"
    assert "success" in grader.grade(ref, ref, mode="sequence")
    # no atom table and not a settings-only view: the legacy grader takes over
    unknown = [L("9zzz"), C([{"auth_seq_id": 1, "color": "red"}])]
    assert grader.grade(unknown, unknown)["grader"] == "sequence"
    with pytest.raises(ValueError):
        grader.grade(ref, ref, mode="nope")


@pytest.mark.parametrize("junk", [
    None, "load 1hho", 7, {}, [None], [[]], ["x"], [{"action": "color"}], [{"action": "color", "data": "A"}],
    [{"action": "load"}], [{"action": "load", "molecule_id": 5}], [{"action": "load", "custom_data": "url"}],
    [L("3ptb"), {"action": "color", "data": [None, 3, {"atoms": 5, "atom_id": "x", "entity_id": []}]}],
    [L("3ptb"), C([{"start_residue_number": "a", "end_residue_number": None, "color": {"r": "x"}}])],
    [L("3ptb"), {"action": "set_property"}, {"action": "set_property", "name": [], "value": {}}],
    [L("3ptb"), {"action": "reset"}, {"action": "focus"}, {"action": "tooltips", "data": [{}]}, {"action": "nope"}],
    [L("3ptb"), C([{"uniprot_accession": "P00760", "uniprot_residue_number": 1.5}])],
    # a view compared by its settings, on an entry that has an atom table
    [L("3ptb"), PROP("superposition", True), STYLE("cartoon"), PROP("hide_water", True),
     C([{"auth_seq_id": 57, "color": "red", "representation": "spacefill", "representationColor": "red"}]),
     {"action": "tooltips", "data": [{"auth_seq_id": 57, "tooltip": "x"}]}],
    [L("3ptb", ligand_view={"label_comp_id": "BEN"}), C([{"auth_seq_id": 57}])],
    [L("3ptb", ligand_view="BEN", preset=["x"], assembly_id={"a": 1})],
    [L("3ptb"), {"action": "tooltips", "data": [{"auth_seq_id": float("inf"), "tooltip": 3}]},
     {"action": "set_color", "highlight": float("inf"), "select": [1]}, PROP("bg_color", {"r": "x"})],
])
def test_bad_input_never_raises(junk):
    ref = task("019")["reference"]
    res = grader.grade(ref, junk)
    assert res["success"] is False and 0.0 <= res["f1"] < 1.0


def test_ligand_view_is_compared_by_the_ligand_it_names():
    by_name = [L("3ptb", ligand_view={"label_comp_id": "BEN"})]
    by_number = [L("3ptb", ligand_view={"auth_asym_id": "A", "auth_seq_id": 1})]
    other = [L("3ptb", ligand_view={"label_comp_id": "CA"})]
    assert ps.grade_state(by_name, by_number)["success"]
    assert not ps.grade_state(by_name, other)["success"]
    assert not ps.grade_state(by_name, [L("3ptb")])["success"]
