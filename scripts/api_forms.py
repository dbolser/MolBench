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

``stretch_forms``
    The request states a colour for the cartoon ("a grey cartoon, with Glu35 as green
    ball-and-stick") and the reference keeps the residue's own stretch of cartoon in
    that colour. The stretch may also take the highlight colour: that is the form the
    API prompt's own example teaches (``"color": "red", "representationColor": "red"``).

``chain_naming_forms``
    On the default view a chain named by its author id also selects the ligands, ions
    and waters filed under that chain; named by its label id it selects the polymer
    alone. The request names "chain A" and says nothing of those, so both are accepted.

``covered_forms``
    On the default view a ligand asked for as spheres or a surface keeps the viewer's
    own ball-and-stick underneath, where it cannot be seen: it may be painted in the
    requested colour, left alone (``"color": null``) or left to the select colour (no
    ``color`` key).

``all_forms`` applies these to a reference and to each of its cartoon forms, and adds
the hide toggle of every component class the request excludes in words ("no sugars")
to each default-view form, so that no accepted form draws what the request rules out.

``accepted_forms`` keeps the forms that end in a state of their own and draw the
requested atoms as the reference does (nothing asked for is missing or drawn another
way). ``free_hides`` names the hide toggles an answer may set on top of any accepted
list (``free_hide`` in the task file; GRADING.md): where both the cartoon style (ligands
and water gone) and the default view (ligands and water drawn) are right, so is every
state in between.
Apart from ``free_hide`` nothing here is read at grade time: the lists are written into
each task's ``accepted``.
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
PLAIN = "default view"
STRETCH = "the stretch under the added representation in the highlight colour, not the backdrop colour"
AUTHOR_CHAINS = "chains by author id: their ligands, ions and waters take the chain's colour"
LABEL_CHAINS = "chains by label id: the polymer chains alone are coloured"
COVERED = "the viewer's own drawing under the spheres or surface left as it is"
COVERED_SELECT = "the viewer's own drawing under the spheres or surface in the select colour"
LOCATORS = ("color", "representation", "representationColor", "sideChain", "focus")
STYLING = LOCATORS + ("tooltip",)
#: what a request can exclude in words -> the hide toggle and the components it hides
EXCLUDES = {"water": "hide_water", "heteroatoms": "hide_heteroatoms", "carbs": "hide_carbs"}
#: representation types that cover the viewer's own ball-and-stick of the same atoms
COVERING = ("spacefill", "gaussian-surface", "molecular-surface", "surface")
#: toggles an answer may set unasked where both the cartoon style and the default view are right
FREE_HIDE_FLAGS = ("hide_water", "hide_heteroatoms", "hide_carbs", "hide_non_standard")


def _is(act: dict, action: str, **eq: Any) -> bool:
    return act.get("action") == action and all(act.get(k) == v for k, v in eq.items())


def _hides(reference: list[dict]) -> bool:
    return any(_is(a, "set_property") and str(a.get("name", "")).startswith("hide_")
               and a.get("value") for a in reference)


def _colour_calls(reference: list[dict]) -> list[int]:
    return [i for i, a in enumerate(reference) if _is(a, "color")]


def _bare(reference: list[dict], hidden=()) -> ps.ViewerState:
    """A bare load of the reference's structure (with the toggles of ``hidden`` set)."""
    load = next(a for a in reference if _is(a, "load"))
    return ps.replay([{k: v for k, v in load.items()
                       if k in ("action", "molecule_id", "custom_data")}]
                     + [{"action": "set_property", "name": f, "value": True} for f in hidden])


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
    # every polymer residue a cartoon can draw: one with no trace atom (Pro552 of 3ERT,
    # of which only N is modelled) has no ribbon in any view
    return s._drawn("cartoon", polymer) & ~shown == 0


def cartoon_forms(reference: list[dict], hidden=()) -> list[tuple[str, list[dict]]]:
    """The other call forms of a reference whose request asks for a cartoon of the
    polymer (see the module docstring). Empty when the reference hides a component (the
    request then says what is to be seen), has more than one ``color`` call, or uses
    another style. A reference that sets the cartoon style and colours nothing ("load X
    as a cartoon and overlay ...") has one other form: the same list without the style."""
    reference = copy.deepcopy(reference)
    calls = _colour_calls(reference)
    styles = [a for a in reference if _is(a, "set_visual_style")]
    if _hides(reference) or len(calls) > 1 or len(styles) > 1 \
            or any(a.get("style") != "cartoon" for a in styles):
        return []
    if any(a.get("keep_colors") or a.get("keep_representations") for a in reference):
        return []
    # ``hidden``: toggles the default-view forms will carry (what the request excludes);
    # what the viewer "already draws" is judged with them set.
    bare = _bare(reference, hidden)
    if bare.table is None:
        return []
    if not calls:
        return [(PLAIN, [a for a in reference if not _is(a, "set_visual_style")])] if styles else []
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


def _default_view(calls: list[dict]) -> bool:
    return not any(_is(a, "set_visual_style") for a in calls)


def stretch_forms(calls: list[dict]) -> list[tuple[str, list[dict]]]:
    """``calls`` with the stretch of cartoon under each added representation in the
    highlight colour, where the list keeps it in the stated backdrop colour
    (``non_selected_color``). Only items on polymer atoms: a ligand has no stretch."""
    new, hit = copy.deepcopy(calls), False
    bare = _bare(calls)
    if bare.table is None:
        return []
    polymer = bare.table.static.get("polymer", 0)
    for act in new:
        if not _is(act, "color") or act.get("non_selected_color") is None:
            continue
        back = ps.normalize_color(act["non_selected_color"])
        for p in act.get("data") or []:
            if p.get("representation") is not None and p.get("representationColor") is not None \
                    and p.get("color") is not None \
                    and ps.normalize_color(p["color"]) == back \
                    and ps.normalize_color(p["representationColor"]) != back \
                    and (bare.select_one(p) or 0) & polymer:
                p["color"] = p["representationColor"]
                hit = True
    return [(STRETCH, new)] if hit else []


def chain_naming_forms(calls: list[dict]) -> list[tuple[str, list[dict]]]:
    """``calls`` on the default view with every whole-chain item named the other way:
    by author id where the list has label ids, and by label id where it has author ids.
    A chain converts when its polymer is exactly one author chain and one label chain."""
    if not _default_view(calls):
        return []
    bare = _bare(calls)
    t = bare.table
    if t is None:
        return []
    polymer = t.static.get("polymer", 0)
    label, auth = t.columns["label_asym_id"], t.columns["auth_asym_id"]
    pairs = {(label[i], auth[i]) for i in range(t.n) if polymer >> i & 1}
    to_auth = {lab: a for lab, a in pairs if sum(1 for x in pairs if x[0] == lab) == 1
               and sum(1 for x in pairs if x[1] == a) == 1}
    to_label = {a: lab for lab, a in to_auth.items()}
    out = []
    for key, other, table, label_ in (("struct_asym_id", "auth_asym_id", to_auth, AUTHOR_CHAINS),
                                      ("auth_asym_id", "struct_asym_id", to_label, LABEL_CHAINS)):
        new, hit, ok = copy.deepcopy(calls), False, True
        for act in new:
            if not _is(act, "color"):
                continue
            for p in act.get("data") or []:
                locators = {k for k in p if k not in STYLING}
                if locators == {key}:
                    if p[key] in table:
                        p[other] = table[p.pop(key)]
                        hit = True
                    else:
                        ok = False
        if hit and ok:
            out.append((label_, new))
    return out


def covered_forms(calls: list[dict]) -> list[tuple[str, list[dict]]]:
    """``calls`` on the default view with the viewer's own drawing of a ligand or ion
    left alone, or left to the select colour, where the requested spheres or surface
    cover it (see the module docstring)."""
    if not _default_view(calls):
        return []
    bare = _bare(calls)
    if bare.table is None:
        return []
    polymer = bare.table.static.get("polymer", 0)
    out = []
    for label, how in ((COVERED, "null"), (COVERED_SELECT, "omit")):
        new, hit = copy.deepcopy(calls), False
        for act in new:
            if not _is(act, "color"):
                continue
            for p in act.get("data") or []:
                atoms = bare.select_one(p) or 0
                if p.get("representation") in COVERING and p.get("representationColor") is not None \
                        and p.get("color") is not None and atoms and not atoms & polymer \
                        and ps.normalize_color(p["color"]) == ps.normalize_color(p["representationColor"]):
                    hit = True
                    if how == "omit":
                        del p["color"]
                    else:
                        p["color"] = None
        if hit:
            out.append((label, new))
    return out


def with_hidden(calls: list[dict], flags: list[str] | tuple[str, ...]) -> list[dict]:
    """``calls`` with each hide toggle of ``flags`` set right after the load (a toggle
    already set in the list is left where it is)."""
    have = {a.get("name") for a in calls if _is(a, "set_property") and a.get("value")}
    add = [{"action": "set_property", "name": f, "value": True} for f in flags if f not in have]
    if not add:
        return copy.deepcopy(calls)
    at = next((i for i, a in enumerate(calls) if _is(a, "load")), -1) + 1
    while at < len(calls) and _is(calls[at], "set_visual_style"):
        at += 1
    return copy.deepcopy(calls[:at]) + add + copy.deepcopy(calls[at:])


def excluded_atoms(state: ps.ViewerState, excludes) -> int:
    """The atoms of the component classes a request excludes that ``state`` draws."""
    if state.table is None or not excludes:
        return 0
    comps = state.components()
    want = 0
    for name in excludes:
        for comp in ps.HIDE_FLAGS[EXCLUDES[name]]:
            want |= comps.get(comp, 0)
    if "carbs" in excludes:      # a sugar is a sugar whichever component holds it
        want |= state.table.static.get("branched", 0)
    want &= ~state.table.static.get("polymer", 0)     # the residue a sugar is bonded to stays
    shown = 0
    for mask, draws in state.display().items():
        if draws:
            shown |= mask
    return want & shown


def all_forms(reference: list[dict], excludes=(), cartoon: bool = True,
              extra: list[tuple[str, list[dict]]] | None = None) -> list[tuple[str, list[dict]]]:
    """Every call form of a reference, labelled: its cartoon forms (when ``cartoon``:
    the request asks for a cartoon of the whole polymer), ``extra`` forms a generator
    adds, and the stretch, chain-naming and covered variants of the reference and of
    each of those. ``excludes`` (keys of ``EXCLUDES``): what the request rules out in
    words; each default-view form gets the matching hide toggle."""
    flags = [EXCLUDES[x] for x in excludes]
    forms = list(extra or []) + (cartoon_forms(reference, flags) if cartoon else [])
    if flags:
        forms = [(label, with_hidden(calls, flags) if _default_view(calls) else calls)
                 for label, calls in forms]
    done: list[tuple[str, list[dict]]] = [("", reference)] + forms
    seen = {repr(c) for _, c in done}
    grown = True
    rounds = 0
    while grown and rounds < 3:
        grown, rounds = False, rounds + 1
        for label, calls in list(done):
            for how in (stretch_forms, chain_naming_forms, covered_forms):
                for more, new in how(calls):
                    if repr(new) not in seen:
                        seen.add(repr(new))
                        done.append((f"{label}; {more}" if label else more, new))
                        grown = True
    return done[1:]


def _keeps_drawing(ref: ps.ViewerState, new: ps.ViewerState, atoms: int) -> bool:
    """Every drawing the reference gives the requested atoms is in ``new``: the same
    representation type in the same colour. A drawing the reference also has outside
    those atoms (the grey cartoon that passes through a residue shown as sticks) is
    context: there the type must be present, in any colour."""
    context: set = set()
    for mask, draws in ref.display().items():
        if mask & ~atoms:
            context |= set(draws)
    exact: dict[tuple, int] = {}
    typed: dict[str, int] = {}
    for mask, draws in new.display().items():
        for d in draws:
            exact[d] = exact.get(d, 0) | mask
            typed[d[0]] = typed.get(d[0], 0) | mask
    for mask, draws in ref.display().items():
        hit = mask & atoms
        if not hit:
            continue
        for d in draws:
            have = typed.get(d[0], 0) if d in context else exact.get(d, 0)
            if hit & ~have:
                return False
    return True


def keeps_requested(reference: list[dict], calls: list[dict], target: Any) -> bool:
    """``calls`` draws the requested atoms as the reference does: target recall 1 in
    the grader's sense, or (where the target also names atoms the reference does not
    draw, such as the waters of "chain A" under the cartoon style) every drawing of the
    reference on the target atoms is kept."""
    if target is None:
        return True
    if ps.grade_state(reference, calls, target=target)["target_recall"] == 1.0:
        return True
    ref, new = ps.replay(copy.deepcopy(reference)), ps.replay(copy.deepcopy(calls))
    atoms = ps.target_atoms(target, ref)
    if not atoms or new.table is None or ref.entry != new.entry:
        return False
    return _keeps_drawing(ref, new, atoms)


def free_hides(reference: list[dict], accepted: list[list[dict]], target: Any) -> list[str]:
    """The hide toggles an answer may set unasked (the task's ``free_hide``). Only where
    the request leaves it open whether ligands, ions and water are on screen at all: the
    task accepts a list that sets the cartoon style (they are gone) and one on the
    default view (they are drawn). A toggle is free when no accepted list sets it, it
    changes what at least one of them draws, and on every one of them the requested
    atoms stay drawn as they were."""
    lists = [reference] + list(accepted)
    if target is None or all(_default_view(c) for c in lists) \
            or not any(_default_view(c) for c in lists):
        return []
    states = [ps.replay(copy.deepcopy(c)) for c in lists]
    if any(st.table is None or st.log or st.unresolved for st in states):
        return []
    # What the request is about: the target atoms that every right list draws. (The
    # waters filed under "chain A" are in a chain target, but the cartoon-style list
    # does not draw them, so they are not part of what was asked for.)
    core = ps.target_atoms(target, states[0]) or 0
    for st in states:
        shown = 0
        for mask, draws in st.display().items():
            if draws:
                shown |= mask
        core &= shown
    if not core:
        return []
    out = []
    for flag in FREE_HIDE_FLAGS:
        if any(_is(a, "set_property", name=flag) for c in lists for a in c):
            continue
        changes, kept = False, True
        for c, st in zip(lists, states):
            hidden = ps.replay(with_hidden(c, [flag]))
            if hidden.display() == st.display():
                continue
            changes = True
            if not _keeps_drawing(st, hidden, core):
                kept = False
                break
        if changes and kept:
            out.append(flag)
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
                   excludes=()) -> list[tuple[str, list[dict]]]:
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
        if not keeps_requested(reference, calls, target):
            continue
        if excluded_atoms(state, excludes):      # the request rules that component out
            continue
        seen.append(calls)
        out.append((label, calls))
    return out
