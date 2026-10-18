"""
Selections graded by the atoms they select (``molbench/atoms.py`` + the frozen
tables in ``molbench/atom_tables/``).

The point is to be right on negatives as well as positives: equivalent namings of
the same atoms score 1.0, while a wrong residue, a neighbour, a wrong chain or a
selection that matches nothing earn no credit for the selection.

Run: ``python -m pytest tests/`` or ``python tests/test_atom_sets.py``.
"""

from __future__ import annotations

import copy
import json
import pathlib

from molbench import atoms, mvs
from molbench.runner import load_tasks

TASKS = pathlib.Path(__file__).resolve().parent.parent / "tasks"


def _scene(pdb: str, *children: dict, structure: dict | None = None) -> dict:
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{pdb}.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": structure or {"type": "model"},
              "children": list(children)}]}]}]}}


def _cartoon() -> dict:
    return _comp("polymer", "cartoon", "gray")


def _comp(selector, rep="ball_and_stick", color="yellow", **custom) -> dict:
    node = {"kind": "component", "params": {"selector": selector}, "children": [
        {"kind": "representation", "params": {"type": rep}, "children": [
            {"kind": "color", "params": {"color": color}}]}]}
    if custom:
        node["custom"] = custom
    return node


def _f1(ref: dict, pred: dict) -> float:
    return mvs.grade_mvs(ref, pred)["f1"]


def _selections(scene: dict) -> list:
    """The component selections of a scene's paths (one per merged component)."""
    return [seg[1][1] for path in mvs.flatten_paths(mvs.extract_root(scene))
            for seg in path if seg[0] == "component"]


# --- equivalent namings -----------------------------------------------------------

_LYZ_CYS = (6, 30, 64, 76, 80, 94, 115, 127)  # hen lysozyme's eight cysteines


def test_every_cys_equals_the_enumerated_cysteines():
    by_name = _scene("1lyz", _cartoon(), _comp({"label_comp_id": "CYS"}))
    as_list = _scene("1lyz", _cartoon(),
                     _comp([{"auth_asym_id": "A", "auth_seq_id": n} for n in _LYZ_CYS]))
    one_each = _scene("1lyz", _cartoon(),
                      *(_comp({"auth_asym_id": "A", "auth_seq_id": n}) for n in _LYZ_CYS))
    for a in (by_name, as_list, one_each):
        for b in (by_name, as_list, one_each):
            assert _f1(a, b) == 1.0
    # Merged into one component, and the polymer cartoon stays one path.
    assert mvs.grade_mvs(by_name, one_each)["n_pred_paths"] == 2


def test_missing_one_cysteine_is_partial_credit():
    ref = _scene("1lyz", _cartoon(), _comp({"label_comp_id": "CYS"}))
    seven = _scene("1lyz", _cartoon(),
                   _comp([{"auth_asym_id": "A", "auth_seq_id": n} for n in _LYZ_CYS[:-1]]))
    assert 0.9 < _f1(ref, seven) < 1.0


def _label_numbering(table: atoms.AtomTable, chain: str, seq: int) -> tuple[str, int]:
    c = table.columns
    i = next(i for i in range(table.n)
             if c["auth_asym_id"][i] == chain and c["auth_seq_id"][i] == seq)
    return c["label_asym_id"][i], c["label_seq_id"][i]


def test_auth_and_label_numbering_where_they_differ():
    # 1TUP: p53 chain A is label_asym_id C, and label_seq_id is offset from the
    # author numbering; label chain A is a DNA strand.
    label_asym, label_seq = _label_numbering(atoms.load_table("1tup"), "A", 281)
    assert (label_asym, label_seq) != ("A", 281)
    ref = _scene("1tup", _cartoon(), _comp({"auth_asym_id": "A", "auth_seq_id": 281}, color="red"))
    label = _scene("1tup", _cartoon(),
                   _comp({"label_asym_id": label_asym, "label_seq_id": label_seq}, color="red"))
    assert _f1(ref, label) == 1.0
    for swapped in ({"label_asym_id": "A", "label_seq_id": 281},
                    {"label_asym_id": "A", "auth_seq_id": 281},
                    {"auth_asym_id": "A", "label_seq_id": 281}):
        pred = _scene("1tup", _cartoon(), _comp(swapped, color="red"))
        assert _f1(ref, pred) < _f1(ref, label), swapped


def test_protein_and_polymer_differ_only_when_there_is_nucleic_acid():
    assert _f1(_scene("1lyz", _comp("polymer")), _scene("1lyz", _comp("protein"))) == 1.0
    assert _f1(_scene("1tup", _comp("polymer")), _scene("1tup", _comp("protein"))) < 1.0


# --- negatives ----------------------------------------------------------------------

def _d281() -> dict:
    return json.loads((TASKS / "mvs_clinical" / "clinvar-1tup-D281.json").read_text())["reference_mvs"]


def _with_selector(scene: dict, selector) -> dict:
    s = copy.deepcopy(scene)
    s["children"][0]["children"][0]["children"][0]["children"][1]["params"]["selector"] = selector
    return s


def test_wrong_residue_neighbour_and_chain_get_no_selection_credit():
    ref = _d281()
    assert _f1(ref, _with_selector(ref, [{"auth_asym_id": "A", "auth_seq_id": 281}])) == 1.0
    ref_sel = _selections(ref)[1]
    for wrong in ({"auth_asym_id": "A", "auth_seq_id": 175},   # wrong residue
                  {"auth_asym_id": "A", "auth_seq_id": 282},   # neighbour
                  {"auth_asym_id": "B", "auth_seq_id": 281}):  # same residue, other chain
        pred = _with_selector(ref, [wrong])
        assert _f1(ref, pred) < 1.0, wrong
        assert mvs._selection_similarity(ref_sel, _selections(pred)[1]) == 0.0, wrong


def test_empty_selection_scores_zero():
    ref = _d281()
    nothing = _with_selector(ref, [{"auth_asym_id": "A", "auth_seq_id": 999}])
    wrong = _with_selector(ref, [{"auth_asym_id": "A", "auth_seq_id": 175}])
    assert mvs._selection_similarity(_selections(ref)[1], _selections(nothing)[1]) == 0.0
    assert _f1(ref, nothing) == _f1(ref, wrong)
    # Lower-case names and string numbers match nothing in Mol* either.
    for bad in ({"auth_asym_id": "A", "auth_seq_id": "281"},
                {"auth_asym_id": "A", "auth_seq_id": 281, "label_comp_id": "asp"}):
        assert _f1(ref, _with_selector(ref, [bad])) == _f1(ref, wrong), bad


# --- primitive endpoints --------------------------------------------------------------

def _line(start: dict, end: dict) -> dict:
    return {"kind": "primitives", "children": [{"kind": "primitive", "params": {
        "kind": "distance_measurement", "start": start, "end": end}}]}


_HIS_NE2 = {"auth_asym_id": "A", "auth_seq_id": 58, "label_atom_id": "NE2"}
_OXY_O2 = {"auth_asym_id": "A", "label_comp_id": "OXY", "label_atom_id": "O2"}


def test_primitive_endpoints_resolve_to_atoms():
    ref = _scene("1hho", _cartoon(), _line(_HIS_NE2, _OXY_O2))
    by_number = {"auth_asym_id": "A", "auth_seq_id": 150, "label_atom_id": "O2"}
    assert _f1(ref, _scene("1hho", _cartoon(), _line(by_number, _HIS_NE2))) == 1.0
    no_atom = {**_HIS_NE2, "label_atom_id": "NE3"}  # no such atom: Mol* draws to the origin
    assert _f1(ref, _scene("1hho", _cartoon(), _line(no_atom, _OXY_O2))) < 1.0
    other_his = {**_HIS_NE2, "auth_seq_id": 87}
    assert _f1(ref, _scene("1hho", _cartoon(), _line(other_his, _OXY_O2))) < 1.0


# --- fallback ------------------------------------------------------------------------

def test_unknown_structure_falls_back_to_signatures():
    assert atoms.load_table("9zzz") is None
    auth = _comp({"auth_asym_id": "A", "auth_seq_id": 5})
    label = _comp({"label_asym_id": "A", "label_seq_id": 5})
    # No table: the old tolerance (auth and label on one axis) still applies...
    assert _f1(_scene("9zzz", auth), _scene("9zzz", label)) == 1.0
    assert _selections(_scene("9zzz", auth))[0].atoms is None
    # ...and so it does for an assembly of a known structure (tables hold model 1).
    assembly = {"type": "assembly", "assembly_id": "1"}
    assert _f1(_scene("1tup", auth, structure=assembly), _scene("1tup", label, structure=assembly)) == 1.0
    # With the table, the two namings are different atoms.
    assert _f1(_scene("1tup", auth), _scene("1tup", label)) < 1.0


# --- calibration ---------------------------------------------------------------------

# Templated prompts ("show the ligands") on entries that have none: the reference
# selection is empty, so it is graded by signature (see _selection_similarity).
_EMPTY_REFERENCES = {"gen-focus-1lyz", "gen-focus-4ins", "gen-ions-1cbs", "gen-ions-1lyz",
                     "gen-ligands-1lyz", "gen-ligands-4ins"}


def test_every_reference_selection_resolves():
    empty = set()
    for task in load_tasks(["mvs"]):
        for path in mvs.flatten_paths(mvs.extract_root(task["reference_mvs"])):
            for kind, sig in path:
                sels = [sig[1]] if kind == "component" else \
                    [p for _, p in sig[2]] if kind == "primitive" else []
                for s in sels:
                    if isinstance(s, mvs.Selection):
                        assert s.atoms is not None, f"{task['id']}: no atom table"
                        if not s.atoms[1]:
                            empty.add(task["id"])
    assert empty == _EMPTY_REFERENCES


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_") and callable(f)]
    for t in tests:
        t()
    print(f"all {len(tests)} atom-set checks passed")
