"""Call forms an API answer may take for what a request leaves unstated.

Ruling of 2026-11-15 (FINAL_PLAN.md): *unstated attributes are free; an API answer that
reaches the state by the viewer's default is right.* On the API track a bare ``load``
already draws everything, so the same words can be answered by call lists that end in
different viewer states. This module writes those lists from a reference, by rule, so
that every API generator accepts the same things (GRADING.md, "Unstated attributes are
free"):

``cartoon_forms``
    The request asks for a cartoon of the polymer. The viewer draws the polymer as a
    cartoon by default, so the cartoon style need not be set, and may be:

    ``default view, rest in the backdrop colour``
        the reference without ``set_visual_style``; a part asked for in the
        representation the viewer already gives it (a ligand as ball-and-stick) is
        painted instead of added; ``non_selected_color`` stays, so everything the
        request does not name is drawn as the viewer draws it, in the backdrop colour.
    ``default view, rest untouched``
        the same, with the backdrop colour given to the polymer chains by name
        instead of ``non_selected_color``; what the request does not name keeps the
        viewer's own colours.
    ``cartoon style set``
        the other way round, for a reference that relies on the default view: the
        style is set first, so only the polymer is drawn, and a ligand that was
        painted becomes an added representation.

``unhidden_forms``
    The request asks for the protein in one representation ("as a surface") and the
    reference hides water, ligands or sugars only so that it equals an MVS scene that
    lists the polymer alone. The request does not say to hide them, so the same list
    without those toggles is accepted.

``base_forms``
    The request asks for residues in a representation and colour and says nothing
    about the colour of the cartoon they sit in (the reference leaves it alone with
    ``"color": null``). That stretch may also take the viewer's select colour (no
    ``color`` key) or the highlight colour.

``accepted_forms`` keeps the forms that end in a state of their own and draw the
requested atoms as the reference does (target recall 1 against the reference: nothing
asked for is missing or drawn another way).
Nothing here is read at grade time: the lists are written into each task's ``accepted``.
"""

from __future__ import annotations

import copy
import pathlib
import sys
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import pdbe_state as ps  # noqa: E402

BACKDROP = "default view, rest in the backdrop colour"
UNTOUCHED = "default view, rest untouched"
STYLE = "cartoon style set"
UNHIDDEN = "nothing hidden: what the request does not name is drawn too"
SELECT_COLOUR = "the stretch under the added representation in the viewer's select colour"
HIGHLIGHT_COLOUR = "the stretch under the added representation in the highlight colour"
LOCATORS = ("color", "representation", "representationColor", "sideChain", "focus")


def _is(act: dict, action: str, **eq: Any) -> bool:
    return act.get("action") == action and all(act.get(k) == v for k, v in eq.items())


def _hides(reference: list[dict]) -> bool:
    return any(_is(a, "set_property") and str(a.get("name", "")).startswith("hide_")
               and a.get("value") for a in reference)


def _colour_calls(reference: list[dict]) -> list[int]:
    return [i for i, a in enumerate(reference) if _is(a, "color")]


def _bare(reference: list[dict]) -> ps.ViewerState:
    load = next(a for a in reference if _is(a, "load"))
    return ps.replay([{k: v for k, v in load.items()
                       if k in ("action", "molecule_id", "custom_data")}])


def _default_types(bare: ps.ViewerState, atoms: int) -> set[str]:
    """The representation types a bare load draws on *every* atom of ``atoms``."""
    types: set[str] | None = None
    for mask, draws in bare.display().items():
        if mask & atoms:
            mine = {rep for rep, _ in draws}
            types = mine if types is None else types & mine
    return types or set()


def whole_polymer_cartoon(reference: list[dict]) -> bool:
    """True when the reference ends with every polymer atom drawn as a cartoon: what a
    request for "a cartoon" of the structure or the protein comes to."""
    s = ps.replay(copy.deepcopy(reference))
    if s.table is None or not s.atomistic:
        return False
    polymer = s.table.static.get("polymer", 0)
    if not polymer:
        return False
    shown = 0
    for mask, draws in s.display().items():
        if any(rep == "cartoon" for rep, _ in draws):
            shown |= mask
    return polymer & ~shown == 0


def cartoon_forms(reference: list[dict]) -> list[tuple[str, list[dict]]]:
    """The other call forms of a reference whose request asks for a cartoon of the
    polymer (see the module docstring). Empty when the reference hides a component (the
    request then says what is to be seen), has more or less than one ``color`` call, or
    uses another style."""
    reference = copy.deepcopy(reference)
    calls = _colour_calls(reference)
    styles = [a for a in reference if _is(a, "set_visual_style")]
    if _hides(reference) or len(calls) != 1 or len(styles) > 1 \
            or any(a.get("style") != "cartoon" for a in styles):
        return []
    if any(a.get("keep_colors") or a.get("keep_representations") for a in reference):
        return []
    bare = _bare(reference)
    if bare.table is None:
        return []
    t = bare.table
    polymer = t.static.get("polymer", 0)
    out: list[tuple[str, list[dict]]] = []
    call = reference[calls[0]]
    if styles:
        data = []
        for p in call.get("data") or []:
            atoms = bare.select_one(p)
            rep = p.get("representation")
            if rep is not None and atoms and rep in _default_types(bare, atoms) \
                    and p.get("representationColor") is not None:
                q = {k: v for k, v in p.items() if k not in LOCATORS}
                data.append({**q, "color": p["representationColor"]})
            elif rep is not None and "color" not in p and p.get("representationColor") is not None:
                data.append({**p, "color": p["representationColor"]})
            else:
                data.append(dict(p))
        backdrop = [a for a in reference if not _is(a, "set_visual_style")]
        backdrop[backdrop.index(call)] = {**call, "data": data}
        out.append((BACKDROP, backdrop))
        if "non_selected_color" in call:
            chains = sorted({t.columns["label_asym_id"][i] for i in range(t.n) if polymer >> i & 1})
            named = [{"struct_asym_id": c, "color": call["non_selected_color"]} for c in chains]
            untouched = [a for a in reference if not _is(a, "set_visual_style")]
            untouched[untouched.index(call)] = {
                **{k: v for k, v in call.items() if k != "non_selected_color"}, "data": named + data}
            out.append((UNTOUCHED, untouched))
    else:
        data = []
        for p in call.get("data") or []:
            atoms = bare.select_one(p)
            if "representation" not in p and p.get("color") is not None and atoms \
                    and not atoms & polymer:
                types = sorted(_default_types(bare, atoms))
                if types:
                    q = {k: v for k, v in p.items() if k not in LOCATORS}
                    data.append({**q, "representation": types[0], "representationColor": p["color"]})
                    continue
            data.append(dict(p))
        styled = list(reference)
        styled[calls[0]] = {**call, "data": data}
        at = next(i for i, a in enumerate(styled) if _is(a, "load")) + 1
        styled.insert(at, {"action": "set_visual_style", "style": "cartoon"})
        out.append((STYLE, styled))
    return out


def unhidden_forms(reference: list[dict]) -> list[tuple[str, list[dict]]]:
    """The reference without its hide toggles, when they only take away components the
    request does not name (water, ligands and ions, sugars) so that the state equals an
    MVS scene that lists the polymer alone. A reference that hides polymer says which
    part of the polymer is to be seen ("only chain A"), and is left as it is."""
    hidden = [a for a in reference if _is(a, "set_property")
              and str(a.get("name", "")).startswith("hide_") and a.get("value")]
    if not hidden or any(a["name"] == "hide_polymer" for a in hidden):
        return []
    return [(UNHIDDEN, [copy.deepcopy(a) for a in reference if a not in hidden])]


def base_forms(reference: list[dict]) -> list[tuple[str, list[dict]]]:
    """The reference with the stretch under each added representation in the viewer's
    select colour, and in the highlight colour. Only params that add a representation
    and leave the default drawing alone (``"color": null``) are changed."""
    def rewrite(how: str) -> list[dict] | None:
        new, hit = copy.deepcopy(reference), False
        for act in new:
            if not _is(act, "color"):
                continue
            for p in act.get("data") or []:
                if "representation" in p and "color" in p and p["color"] is None \
                        and p.get("representationColor") is not None:
                    hit = True
                    if how == "omit":
                        del p["color"]
                    else:
                        p["color"] = p["representationColor"]
        return new if hit else None
    out = []
    for label, how in ((SELECT_COLOUR, "omit"), (HIGHLIGHT_COLOUR, "same")):
        new = rewrite(how)
        if new is not None:
            out.append((label, new))
    return out


def accepted_forms(reference: list[dict], forms: list[tuple[str, list[dict]]],
                   target: Any = None, accepted: list[list[dict]] | None = None,
                   ) -> list[tuple[str, list[dict]]]:
    """The forms worth listing under ``accepted``: each replays with nothing ignored or
    unresolved, draws the requested atoms as the reference does (target recall 1 against
    the reference; ``target`` in the grader's form, or None for a task without one),
    and ends in a state that neither the reference nor an earlier accepted list has."""
    seen = [reference] + list(accepted or [])
    out = []
    for label, calls in forms:
        state = ps.replay(copy.deepcopy(calls))
        if state.log or state.unresolved:
            continue
        if any(ps.grade_state(old, calls)["success"] for old in seen):
            continue
        # Recall, not the whole target score: the default view keeps the viewer's own
        # drawing of the requested atoms under the requested one (an ion's small ball
        # inside its sphere, the cartoon of a residue asked for as sticks), in the same
        # colour, and that is not a missing or a wrong drawing.
        if target is not None and ps.grade_state(reference, calls, target=target)["target_recall"] != 1.0:
            continue
        seen.append(calls)
        out.append((label, calls))
    return out
