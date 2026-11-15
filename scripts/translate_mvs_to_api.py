#!/usr/bin/env python3
"""
Translate MVS tasks into API twins: the same request, answered as pdbe-molstar 3.3.2
calls, ending in the same picture. $0, no network.

    uv run python scripts/translate_mvs_to_api.py --all           # write tasks/api_twins/
    uv run python scripts/translate_mvs_to_api.py --all --check   # write nothing; fail if a file would change
    uv run python scripts/translate_mvs_to_api.py --all --report  # write nothing; print what would happen
    uv run python scripts/translate_mvs_to_api.py ID [ID ...]     # only these MVS tasks

What a twin is
--------------
The twin of an MVS task has the same ``prompt``, ``structures``, ``split``, ``style``,
``tier``, ``family`` and target atoms, and a reference call list whose **replayed final
state is the MVS reference's drawn state**: every atom carries the same
representations in the same colours, nothing else is drawn, and the camera focus,
tooltips, assembly and background agree. ``twin_of`` is set on both tasks (in the MVS
file only that one value is rewritten; the rest of the file is left byte for byte).

How a call list is found
------------------------
Not by rewriting the scene tree node by node: the two formats start from opposite
ends (an MVS scene draws only what it lists, a ``load`` already draws everything). The
MVS reference is resolved to its drawn state (``molbench.mvs.resolve_scene``, the MVS
grader's own resolver), and a call list is assembled that reaches that state:

1. the base: the default view, or one global style, whichever keeps most of what the
   scene draws; every default component the scene does not draw as the base draws it
   is switched off with its hide toggle;
2. one ``color`` call: the colours of what the base draws (the largest colour class as
   ``non_selected_color``, the others as selections over it), and an added
   representation with ``representationColor`` for everything the scene draws that
   the base does not;
3. ``focus``, ``tooltips`` and the background colour, when the scene has them.

Selections are written with the scene's own selectors where one names the atoms
(``label_asym_id`` becomes ``struct_asym_id``, ``auth_seq_id`` stays, ...), and
otherwise as entities, chains, component codes, author- or label-numbered ranges,
residues and atom names, each resolved by the API grader's own selection code and
used only if it selects exactly the atoms meant.

The equivalence check
---------------------
``state_differences`` compares the two states and is independent of how the call list
was made: it resolves the scene with the MVS grader, replays the calls with the API
grader, and lists every difference. A candidate call list that differs is never
written; ``--check`` re-runs the comparison for every twin on disk and exits non-zero
on any difference. A twin must also pass the task format, ``scripts/check_api_refs.py``,
the grader's own task check, and grade itself as exactly right (success, F1 1, target
score 1), and select the same target atoms as its MVS task.

What cannot be translated
-------------------------
Listed, with the reason, in ``tasks/api_twins/README.md`` (written by this script):
distance lines and other primitives, 3D labels, the computed-interactions request,
transparency, the ``line`` and ``backbone`` representations, colour themes (see
``ALLOW_THEMES``), annotation colouring,
other models of an ensemble, several structures in one scene; a task that names its
structure by protein and accepts entries outside the panel; a task that already has
a twin from its own generator (clinical, follow-up, accept-set), or was left without
one by a generator that writes both tracks; a no-change follow-up; and a task in the old
format, which has no ``twin_of`` field (for those the report says whether a twin
could be made, and none is written).

Order
-----
Run it after every MVS generator. Because ``twin_of`` is written into the MVS files, an
MVS generator re-run afterwards drops the links (run this script again), and a
generator's byte-for-byte rebuild check must ignore ``twin_of``.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import pathlib
import re
import sys
from collections import Counter
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import drawn, mvs, runner  # noqa: E402
from molbench import pdbe_state as ps  # noqa: E402
from molbench import tasks as T  # noqa: E402

_spec = importlib.util.spec_from_file_location("check_api_refs", REPO / "scripts" / "check_api_refs.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

SCRIPT = "scripts/translate_mvs_to_api.py"
OUT = REPO / "tasks" / "api_twins"

#: MVS representation type -> the pdbe-molstar type that draws the same thing. ``line``
#: and ``backbone`` have no counterpart. MVS does not grade the surface kind; the API
#: twin uses the molecular surface, the kind MVS draws by default.
REP = {"cartoon": "cartoon", "ball_and_stick": "ball-and-stick", "spacefill": "spacefill",
       "putty": "putty", "surface": "molecular-surface", "carbohydrate": "carbohydrate"}
#: MVS selector key -> API selector key (same column, same meaning)
KEY = {"label_entity_id": "entity_id", "label_asym_id": "struct_asym_id", "auth_asym_id": "auth_asym_id",
       "label_seq_id": "residue_number", "auth_seq_id": "auth_seq_id", "label_comp_id": "label_comp_id",
       "beg_label_seq_id": "start_residue_number", "end_label_seq_id": "end_residue_number",
       "beg_auth_seq_id": "start_auth_residue_number", "end_auth_seq_id": "end_auth_residue_number"}
#: facts an API twin may have (everything else would be something the scene has not)
TWIN_FACTS = {"display", "scene", "focus", "tooltip", "assembly", "canvas:bg_color", "_changed", "_all"}


#: A scene coloured by a Mol* theme ("colour by chain") is not given a twin. A call
#: list reaching the same state exists (the cartoon style is coloured by chain), and
#: `build` can find it, but the two graders would then judge the same request by
#: different rules: the MVS grader takes any set of distinct chain colours for a
#: chain-id theme in the reference (GRADING.md, "Colour themes"), the API grader only
#: the viewer's own theme colours. A pair like that says nothing about the formats.
ALLOW_THEMES = False

PALETTE_NAME = {drawn.COLOR_NAMES[n]: n for n in reversed(drawn.TASK_PALETTE)}


class Untranslatable(Exception):
    """The task has no twin. ``reason`` is one of a small set of phrases (they are
    counted in the README); ``detail`` says more."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(reason + (f": {detail}" if detail else ""))
        self.reason, self.detail = reason, detail


class NoWay(Exception):
    """This base (default view or style) cannot reach the state."""


# --------------------------------------------------------------------------- #
# The MVS side: what the scene draws
# --------------------------------------------------------------------------- #
class Wanted:
    """The drawn state of one MVS scene, in the API's vocabulary."""

    def __init__(self) -> None:
        self.entry: str = ""
        self.table: Any = None
        self.draws: dict[tuple, int] = {}       # (API representation, colour) -> atoms
        self.focus: int | None = None           # atoms of the focused components
        self.tooltips: dict[str, int] = {}      # normalised text -> atoms
        self.assembly: str = ""
        self.background: Any = None
        self.words: dict[Any, str] = {}         # colour / tooltip text as the scene writes it
        self.hints: list[dict] = []             # the scene's selectors as API locators
        self.base_colour: Any = None            # a colour laid under selective colours


def _api_colour(token: Any) -> Any:
    """An MVS colour token in the form `ViewerState.display` uses: an RGB triple, or the
    name of a Mol* colour theme (``("theme", "chain-id")`` -> ``"chain-id"``)."""
    if isinstance(token, tuple) and len(token) == 2 and token[0] == "theme":
        return token[1]
    return token


def _is_rgb(c: Any) -> bool:
    return isinstance(c, tuple) and len(c) == 3 and all(isinstance(v, int) for v in c)


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for c in node.get("children") or []:
            yield from _walk(c)


def _hint(expr: Any) -> dict | None:
    """One MVS component expression as an API locator, or None if a key has no
    counterpart. (Whether it selects the same atoms is checked where it is used.)"""
    if not isinstance(expr, dict) or not expr:
        return None
    out: dict[str, Any] = {}
    for k, v in expr.items():
        if k == "label_atom_id":
            out["atoms"] = [v]
        elif k in KEY:
            out[KEY[k]] = v
        else:
            return None
    return out


def scene_state(tree: Any, rename: dict[str, str] | None = None) -> Wanted:
    """Resolve an MVS scene to what it draws, or say why the API cannot draw it."""
    scene = mvs.resolve_scene(tree, rename=rename)
    if scene is None:
        raise Untranslatable("not a scene tree")
    if len(scene.entries()) != 1:
        raise Untranslatable("several structures in one scene", ", ".join(sorted(scene.entries())))
    (entry,) = scene.entries()
    st = scene.structures.get(entry)
    if st is None or st.table is None or scene.unresolved:
        raise Untranslatable("a selection the atom tables cannot answer", entry)
    if scene.primitives:
        raise Untranslatable("a distance line or another drawn primitive")
    if st.labels:
        raise Untranslatable("a 3D text label")
    if st.interactions:
        raise Untranslatable("the computed non-covalent interactions request")
    if st.other or scene.other:
        kinds = sorted({str(o[0]) for o in list(st.other) + list(scene.other)})
        raise Untranslatable("a node kind with no API counterpart", ", ".join(kinds))
    w = Wanted()
    w.entry, w.table = entry, st.table
    for kind in st.kinds:
        if kind[0] == "assembly" and kind[2] == 0 and not w.assembly:
            w.assembly = kind[1]
        else:
            raise Untranslatable("another model of the entry, or a symmetry-built structure", str(kind))
    for (rtype, colour, opacity), mask in st.draws.items():
        if opacity != 1.0:
            raise Untranslatable("transparency (the API has no opacity)")
        if rtype not in REP:
            raise Untranslatable("a representation with no API counterpart", str(rtype))
        colour = _api_colour(colour)
        if isinstance(colour, str) and not ALLOW_THEMES:
            raise Untranslatable("a colour theme (colour by chain)", colour)
        if not (_is_rgb(colour) or isinstance(colour, str)):
            raise Untranslatable("annotation colouring or an invalid colour", str(colour))
        key = (REP[rtype], colour)
        w.draws[key] = w.draws.get(key, 0) | mask
    w.focus = st.focus
    w.tooltips = dict(st.tooltips)
    w.background = scene.background
    if not (w.draws or w.focus or w.tooltips):
        raise Untranslatable("the scene draws nothing")
    for node in _walk(mvs.extract_root(tree)):
        p = node.get("params") if isinstance(node.get("params"), dict) else {}
        if node.get("kind") in ("color", "canvas"):
            value = p.get("color", p.get("background_color"))
            token = drawn.mvs_color(value)
            if _is_rgb(token) and isinstance(value, str):
                w.words.setdefault(token, value)
        if node.get("kind") == "representation" and w.base_colour is None:
            layers = [c.get("params") or {} for c in node.get("children") or []
                      if isinstance(c, dict) and c.get("kind") == "color"]
            plain = [x for x in layers if x.get("selector") in (None, "all")]
            if plain and len(plain) < len(layers) and _is_rgb(drawn.mvs_color(plain[0].get("color"))):
                w.base_colour = drawn.mvs_color(plain[0].get("color"))
        if node.get("kind") == "tooltip":
            w.words.setdefault(" ".join(str(p.get("text", "")).split()).casefold(), str(p.get("text", "")))
        sel = p.get("selector")
        for expr in (sel if isinstance(sel, list) else [sel]):
            h = _hint(expr)
            if h is not None and h not in w.hints:
                w.hints.append(h)
    return w


# --------------------------------------------------------------------------- #
# Naming a set of atoms in the API's selection language
# --------------------------------------------------------------------------- #
class Namer:
    """Writes API selections for atom sets of one structure. Every locator is resolved
    by ``pdbe_state.resolve_param`` (the API grader's port of the viewer's selection
    code) and used only if it stays inside what it may select."""

    def __init__(self, table: Any, entry: str, hints: list[dict]):
        self.t, self.entry, self.hints = table, entry, hints
        c = table.columns
        self.poly = table.static.get("polymer", 0)
        by_res: dict[int, dict] = {}
        for i, ri in enumerate(c["residue_index"]):
            r = by_res.get(ri)
            if r is None:
                r = by_res[ri] = {"ac": c["auth_asym_id"][i], "an": c["auth_seq_id"][i],
                                  "lc": c["label_asym_id"][i], "ls": c["label_seq_id"][i], "mask": 0}
            r["mask"] |= 1 << i
        self.residues = list(by_res.values())
        for r in self.residues:
            r["poly"] = bool(r["mask"] & self.poly)
        self.atom_names = c["label_atom_id"]
        self._cache: dict[str, int] = {}

        def unique(col: str) -> list:
            seen: dict[Any, None] = {}
            for v in c[col]:
                seen.setdefault(v)
            return list(seen)

        self.entities, self.auth_chains = unique("label_entity_id"), unique("auth_asym_id")
        self.label_chains, self.comps = unique("label_asym_id"), unique("label_comp_id")

    def mask(self, param: dict) -> int:
        key = json.dumps(param, sort_keys=True)
        if key not in self._cache:
            try:
                self._cache[key] = ps.resolve_param(self.t, param, self.entry)
            except NotImplementedError:
                self._cache[key] = 0
        return self._cache[key]

    def cover(self, need: int, allowed: int, everything_ok: bool = True) -> list[dict]:
        """Locators whose union holds every atom of ``need`` and none outside
        ``allowed``; the broadest that fit, the scene's own selectors first.
        ``everything_ok``: the locator with no keys (everything) may be used."""
        assert not need & ~allowed
        out: list[dict] = []
        left = need

        def take(param: dict, must: int = 0) -> bool:
            nonlocal left
            m = self.mask(param)
            if not m or not m & left or m & ~allowed or must & ~m:
                return False
            out.append(param)
            left &= ~m
            return True

        if everything_ok:
            take({})
        for h in sorted(self.hints, key=lambda h: -(self.mask(h) & need).bit_count()):
            if left:
                take(h)
        for key, values in (("entity_id", self.entities), ("auth_asym_id", self.auth_chains),
                            ("struct_asym_id", self.label_chains), ("label_comp_id", self.comps)):
            for v in values:
                if left:
                    take({key: v})
        if not left:
            return out
        # residue by residue: runs of consecutive polymer residues become ranges
        run: list[dict] = []

        def flush() -> None:
            if not run:
                return
            want = 0
            for r in run:
                want |= r["mask"]
            a, b = run[0], run[-1]
            if len(run) > 1 and want & left:
                for param in ({"auth_asym_id": a["ac"], "start_auth_residue_number": a["an"],
                               "end_auth_residue_number": b["an"]},
                              {"struct_asym_id": a["lc"], "start_residue_number": a["ls"],
                               "end_residue_number": b["ls"]}):
                    if take(param, must=want & left):
                        break
            for r in run:
                if r["mask"] & left:
                    self._residue(r, r["mask"] & left, take)
            run.clear()

        for r in self.residues:
            if not r["mask"] & left:
                continue
            whole = not r["mask"] & ~allowed
            if (whole and r["poly"] and run and run[-1]["lc"] == r["lc"]
                    and isinstance(r["ls"], int) and run[-1]["ls"] + 1 == r["ls"]):
                run.append(r)
                continue
            flush()
            if whole and r["poly"] and isinstance(r["ls"], int):
                run.append(r)
            else:
                self._residue(r, r["mask"] & left, take)
        flush()
        if left:
            raise NoWay("a set of atoms the selection language cannot name exactly")
        return out

    def _residue(self, r: dict, atoms: int, take: Any) -> None:
        """One residue, or some of its atoms. Author chain and number as papers write
        them when that names the residue exactly, else the label form."""
        locators = [{"auth_asym_id": r["ac"], "auth_seq_id": r["an"]}]
        if r["poly"] and isinstance(r["ls"], int):
            locators.append({"struct_asym_id": r["lc"], "residue_number": r["ls"]})
        locators.append({"struct_asym_id": r["lc"], "auth_seq_id": r["an"]})
        for loc in locators:
            if take(loc, must=atoms):
                return
        names: list[str] = []
        for i in check.rows(atoms):
            if self.atom_names[i] not in names:
                names.append(self.atom_names[i])
        for loc in locators:
            if take({**loc, "atoms": names}, must=atoms):
                return


# --------------------------------------------------------------------------- #
# The API side: a call list that reaches the state
# --------------------------------------------------------------------------- #
def load_action(structure: str, assembly: str = "") -> dict:
    """The ``load`` of a panel structure id (a PDB id, or ``af-<acc>-f<n>-model_v<k>``)."""
    more = {"assembly_id": assembly} if assembly else {}
    m = re.fullmatch(r"af-([a-z0-9]+)-f(\d+)-model_v(\d+)", structure)
    if m:
        acc, frag, version = m.groups()
        return {"action": "load", "custom_data": {
            "url": f"https://alphafold.ebi.ac.uk/files/AF-{acc.upper()}-F{frag}-model_v{version}.cif",
            "format": "cif", "binary": False}, **more}
    return {"action": "load", "molecule_id": structure, **more}


def _hex(rgb: tuple) -> str:
    return "#%02X%02X%02X" % rgb


def build(w: Wanted, structure: str, style: str | None) -> tuple[list[dict], dict]:
    """A call list for ``w`` on the default view (``style`` None) or under one global
    style, and notes on how it was made. Raises `NoWay` if this base cannot work."""
    start = [load_action(structure, w.assembly)] + (
        [{"action": "set_visual_style", "style": style}] if style else [])
    s = ps.replay(copy.deepcopy(start))
    if s.table is not w.table:
        raise Untranslatable("the structure cannot be loaded by the API", structure)
    comps = s.components()
    everything = (1 << w.table.n) - 1
    wanted_rep: dict[str, int] = {}
    for (rep, _), m in w.draws.items():
        wanted_rep[rep] = wanted_rep.get(rep, 0) | m

    def reprs(name: str) -> tuple:
        return ((style, ps.STYLE_THEME),) if style else ps.DEFAULT_REPRS[name]

    hidden: list[str] = []
    while True:
        kept: dict[str, int] = {}                 # representation -> atoms the base draws and keeps
        base_theme: dict[tuple, int] = {}         # (representation, theme) -> kept atoms
        for flag, names in ps.HIDE_FLAGS.items():
            if flag in hidden:
                continue
            draws_any, fits = False, True
            for n in names:
                for rep, _theme in reprs(n) if n in comps else ():
                    d = s._drawn(rep, comps[n])
                    draws_any |= bool(d)
                    fits &= not d & ~wanted_rep.get(rep, 0)
            if draws_any and not fits:
                hidden.append(flag)
                continue
            for n in names:
                for rep, theme in reprs(n) if n in comps else ():
                    d = s._drawn(rep, comps[n])
                    kept[rep] = kept.get(rep, 0) | d
                    base_theme[(rep, theme)] = base_theme.get((rep, theme), 0) | d
        # one overpaint colour per atom, whatever default representation it is in; and
        # a theme-coloured draw has to be the base's own theme, left unpainted
        colour_of: dict[Any, int] = {}
        for (rep, colour), m in w.draws.items():
            hit = m & kept.get(rep, 0)
            if hit:
                colour_of[colour] = colour_of.get(colour, 0) | hit
        clash = 0
        cols = list(colour_of.items())
        for i, (_, a) in enumerate(cols):
            for _, b in cols[i + 1:]:
                clash |= a & b
        for (rep, colour), m in w.draws.items():
            if isinstance(colour, str):
                for (brep, theme), bm in base_theme.items():
                    if brep == rep and theme != colour:
                        clash |= m & bm
        if not clash:
            break
        # take away the smallest default component in the clash; it is drawn again below
        options = [(sum(comps[n].bit_count() for n in names if n in comps), flag)
                   for flag, names in ps.HIDE_FLAGS.items() if flag not in hidden
                   and any(n in comps and comps[n] & clash for n in names)]
        if not options:
            raise NoWay("two colours on one atom of the default view")
        hidden.append(min(options)[1])

    calls = list(start)
    calls += [{"action": "set_property", "name": flag, "value": True}
              for flag in ps.HIDE_FLAGS if flag in hidden]
    namer = Namer(w.table, s.entry or "", w.hints)
    drawn_by_base = 0
    for m in kept.values():
        drawn_by_base |= m
    free = everything & ~drawn_by_base           # painting these changes nothing on screen
    unpainted = 0                                # kept in the base's own theme colours
    paint: dict[tuple, int] = {}
    for colour, m in colour_of.items():
        if isinstance(colour, str):
            unpainted |= m
        else:
            paint[colour] = m
    free &= ~unpainted

    def word(rgb: tuple) -> str:
        return w.words.get(rgb) or PALETTE_NAME.get(rgb) or _hex(rgb)

    # what the scene draws and the base does not: added representations
    added: list[dict] = []
    painted_by_added: dict[tuple, int] = {}
    n_added = 0
    for (rep, colour), m in sorted(w.draws.items(), key=lambda kv: (kv[0][0], repr(kv[0][1]))):
        rest = m & ~kept.get(rep, 0)
        if not rest:
            continue
        n_added += 1
        for loc in namer.cover(rest, rest):
            pm = namer.mask(loc) & ~free
            param = dict(loc)
            here = [c for c, cm in paint.items() if cm & pm]
            if pm & unpainted or len(here) > 1:
                param["color"] = None                 # leave the default view's colours alone
            elif here:
                param["color"] = word(here[0])
                painted_by_added[here[0]] = painted_by_added.get(here[0], 0) | pm
            param["representation"] = rep
            if _is_rgb(colour):
                param["representationColor"] = word(colour)
            added.append(param)

    # the colours of what the base draws. Later selections paint over earlier ones, so
    # a class may also cover atoms that a later one repaints. Each class in turn is
    # tried as `non_selected_color` (the others over it), and so is naming every class
    # outright.
    by_size = sorted(paint, key=lambda c: (-paint[c].bit_count(), c))
    repainted = 0
    for cm in painted_by_added.values():
        repainted |= cm

    def paint_params(order: list, rest: Any) -> tuple[list[dict], dict]:
        out: list[dict] = []
        later = 0
        for c in order:
            later |= paint[c]
        if rest is not None:
            if (free | later | paint[rest] | repainted) != everything or unpainted:
                raise NoWay("non_selected_color would paint atoms that keep their own colours")
        for c in order:
            later &= ~paint[c]
            need = paint[c] & ~painted_by_added.get(c, 0)
            if need:
                allowed = (need | free | later | repainted) & ~unpainted
                out += [{**loc, "color": word(c)}
                        for loc in namer.cover(need, allowed, everything_ok=len(paint) == 1)]
        return out, ({"non_selected_color": word(rest)} if rest is not None else {})

    # Which way to write it, most natural first: the scene's own background colour (a
    # colour node with no selector under selective ones) as `non_selected_color`; a
    # single colour under added representations likewise; otherwise every class named
    # outright; and failing those, whichever class as `non_selected_color` works.
    tries: list[tuple[list, Any]] = []
    if w.base_colour in paint and len(paint) > 1:
        tries.append(([c for c in by_size if c != w.base_colour], w.base_colour))
    if len(paint) == 1 and added:
        tries.append(([], by_size[0]))
    tries.append((by_size, None))
    tries += [([c for c in by_size if c != rest], rest) for rest in by_size]
    data, more, failed = None, {}, None
    for order, rest in tries:
        try:
            data, more = paint_params(order, rest)
            break
        except NoWay as e:
            failed = e
    if data is None:
        raise failed or NoWay("a set of atoms the selection language cannot name exactly")
    if data or added or more:
        calls.append({"action": "color", "data": data + added, **more})
    if w.focus:
        calls.append({"action": "focus", "data": namer.cover(w.focus, ps.residues_of(w.table, w.focus))})
    if w.tooltips:
        tips = []
        for text, m in w.tooltips.items():
            tips += [{**loc, "tooltip": w.words.get(text, text)} for loc in namer.cover(m, m)]
        calls.append({"action": "tooltips", "data": tips})
    if w.background is not None:
        calls.append({"action": "set_property", "name": "bg_color", "value": _hex(w.background)})
    return calls, {"base": f"the {style} style" if style else "the default view",
                   "switched_off": [f for f in ps.HIDE_FLAGS if f in hidden],
                   "added_representations": n_added, "colour_classes": len(paint)}


def state_differences(tree: Any, calls: list[dict], rename: dict[str, str] | None = None) -> list[str]:
    """Every way the replayed final state of ``calls`` differs from the drawn state of
    the MVS scene ``tree`` (empty = the same picture). Independent of `build`: the scene
    is resolved by the MVS grader, the calls are replayed by the API grader."""
    try:
        w = scene_state(tree, rename)
    except Untranslatable as e:
        return [f"the scene has something the API cannot state: {e}"]
    s = ps.replay(copy.deepcopy(calls))
    out = [f"a call did nothing: {m}" for m in s.log] + [f"unresolved: {m}" for m in s.unresolved]
    if s.table is None or s.table is not w.table or not s.atomistic:
        return out + [f"the calls load {s.entry!r}, the scene draws {w.entry!r}"]
    api: dict[tuple, int] = {}
    for m, look in s.display().items():
        for d in look:
            api[d] = api.get(d, 0) | m
    for key in sorted(set(api) | set(w.draws), key=repr):
        a, b = api.get(key, 0), w.draws.get(key, 0)
        if a != b:
            out.append(f"{key[0]} in {key[1]}: {(a & ~b).bit_count()} atom(s) only in the call list's "
                       f"state, {(b & ~a).bit_count()} only in the scene")
    facts = ps.facts(s)
    extra = sorted(set(facts) - TWIN_FACTS)
    if extra:
        out.append(f"the call list also states {extra}")
    if facts.get("assembly", "") != w.assembly:
        out.append(f"assembly {facts.get('assembly', '')!r} != {w.assembly!r}")
    want_focus = ps.residues_of(w.table, w.focus) if w.focus else None
    if facts.get("focus") != want_focus:
        out.append("the camera focus is on other residues")
    if (facts.get("tooltip") or {}) != {ps._norm_text(t): m for t, m in w.tooltips.items()}:
        out.append("the tooltips differ")
    if facts.get("canvas:bg_color") != (w.background if w.background != ps.DEFAULT_BG else None):
        out.append("the background differs")
    return out


def translate_scene(tree: Any, structure: str, rename: dict[str, str] | None = None
                    ) -> tuple[list[dict], dict]:
    """The call list for one MVS scene and the notes on how it was made. Tries the
    default view and each global style the scene could be drawn under, keeps those
    whose final state equals the scene's, and returns the shortest (the default view
    on a tie). Raises `Untranslatable`."""
    w = scene_state(tree, rename)
    found: list[tuple[tuple, list[dict], dict]] = []
    why: list[str] = []
    styles = [None] + sorted({rep for rep, _ in w.draws})
    for n, style in enumerate(styles):
        try:
            calls, notes = build(w, structure, style)
        except NoWay as e:
            why.append(f"{style or 'default view'}: {e}")
            continue
        diff = state_differences(tree, calls, rename)
        if diff:
            why.append(f"{style or 'default view'}: {diff[0]}")
            continue
        size = len(calls) + sum(len(a.get("data") or []) for a in calls)
        found.append(((size, n), calls, notes))
    if not found:
        raise Untranslatable("no call list gives this drawing", "; ".join(why))
    return min(found, key=lambda f: f[0])[1:]


# --------------------------------------------------------------------------- #
# A twin task
# --------------------------------------------------------------------------- #
def twin_id(mvs_id: str) -> str:
    """``x-mvs`` -> ``x-api`` (also before a paraphrase suffix: ``x-mvs.terse`` ->
    ``x-api.terse``); any other id gets ``-api`` appended."""
    new, n = re.subn(r"-mvs(?=$|\.)", "-api", mvs_id, count=1)
    return new if n else mvs_id + "-api"


def _api_target(target: Any) -> Any:
    if not isinstance(target, list):
        return target
    return [{**p, "representation": REP.get(p.get("representation"), p.get("representation"))}
            if isinstance(p, dict) else p for p in target]


def _numbering(reference: list[dict], table: Any, entry: str) -> dict:
    """Which selector keys the twin's reference uses, and whether author and label
    numbers (or chain ids) differ on the atoms they select."""
    c = table.columns
    keys: Counter = Counter()
    offset = chain = False
    for act in reference:
        for p in act.get("data") or []:
            keys.update(k for k in p if k in ps.LOCATOR_KEYS)
            if not any(k in ps.LOCATOR_KEYS for k in p):
                continue
            for i in check.rows(ps.resolve_param(table, p, entry)):
                chain |= c["auth_asym_id"][i] != c["label_asym_id"][i]
                if (1 << i) & table.static.get("polymer", 0):
                    offset |= c["auth_seq_id"][i] != c["label_seq_id"][i]
    return {"selector_keys": dict(sorted(keys.items())), "numbering_offset": offset,
            "auth_label_chain": chain}


def other_entries(task: dict, structure: str) -> list[str]:
    """The other entries a protein-named task accepts. The MVS grader re-resolves the
    reference on any of them; the API grader needs a call list, and so an atom table,
    for each: a task that accepts entries outside the panel has no twin."""
    others = [o for o in task.get("accepted_structures") or [] if o != structure]
    missing = sum(mvs._entry_table(o) is None for o in others)
    if missing:
        raise Untranslatable("the structure is named by protein and entries outside the panel are accepted",
                             f"{missing} of {len(others)} other accepted entries have no atom table")
    return others


def make_twin(task: dict, twins: dict[str, str]) -> dict:
    """The API twin of an MVS task (new format), checked. Raises `Untranslatable`."""
    if len(task["structures"]) != 1:
        raise Untranslatable("several structures in one scene", ", ".join(task["structures"]))
    structure = task["structures"][0]
    reference, notes = translate_scene(task["reference"], structure)
    scenes = [("reference", task["reference"], reference, None)]
    accepted = []
    for i, alt in enumerate(task.get("accepted") or []):
        calls, _ = translate_scene(alt, structure)
        accepted.append(calls)
        scenes.append((f"accepted[{i}]", alt, calls, None))
    entry = scene_state(task["reference"]).entry
    others = other_entries(task, structure)
    for other in others:
        rename = {entry: scene_state(task["reference"], {entry: other}).entry}
        calls, _ = translate_scene(task["reference"], other, rename)
        accepted.append(calls)
        scenes.append((f"on {other}", task["reference"], calls, rename))
    context = None
    if task.get("context") and task["context"].get("noop"):
        raise Untranslatable("a no-change follow-up (what cannot be done differs between the formats)")
    if task.get("context"):
        calls, _ = translate_scene(task["context"]["scene"], structure)
        context = {"calls": calls, "noop": task["context"]["noop"]}
        scenes.append(("start state", task["context"]["scene"], calls, None))
    paraphrase_of = None
    if task.get("paraphrase_of"):
        paraphrase_of = twins.get(task["paraphrase_of"])
        if paraphrase_of is None:
            raise Untranslatable("its original phrasing has no twin", task["paraphrase_of"])
    table = T.table_for(structure)
    old = task.get("provenance") or {}
    hinges = ["added_representation_colour"] if any(
        "representationColor" in p for a in reference for p in a.get("data") or []) else []
    prov = {
        "script": SCRIPT,
        "inputs": [task["_path"]] + [f"molbench/atom_tables/{s}.json.gz" for s in
                                     [structure] + [o for o in task.get("accepted_structures") or []
                                                    if o != structure]],
        "date": old.get("date", ""), "checks": [],
        "twin": {"of": task["id"], **notes},
        "difficulty": {**(old.get("difficulty") or {}),
                       **_numbering(reference, table, ps.replay(copy.deepcopy(reference)).entry or ""),
                       "hinges_on": hinges, "order_matters": notes["base"] != "the default view",
                       "context_switched_off": notes["switched_off"]},
    }
    twin = {"id": twin_id(task["id"]), "track": "api", "tier": task["tier"], "family": task["family"],
            "structures": list(task["structures"]), "prompt": task["prompt"], "reference": reference,
            "accepted": accepted, "context": context, "target": _api_target(task["target"]),
            "twin_of": task["id"], "paraphrase_of": paraphrase_of, "style": task["style"],
            "split": task["split"], "grounding": copy.deepcopy(task["grounding"]),
            "provenance": prov, "skills": list(task["skills"])}
    if task.get("accepted_targets"):
        twin["accepted_targets"] = [_api_target(t) for t in task["accepted_targets"]]
    verify(twin, task, scenes)
    return twin


def verify(twin: dict, task: dict, scenes: list[tuple]) -> None:
    """Every check a twin passes before it is written (raises `Untranslatable`); the
    checks are written, in words, to ``provenance.checks``."""
    done = twin["provenance"]["checks"]
    for name, tree, calls, rename in scenes:
        diff = state_differences(tree, calls, rename)
        if diff:
            raise Untranslatable("the twin failed its checks", f"{name}: {diff[0]}")
    done.append("the replayed final state of the call list is the drawn state of the MVS reference: "
                "every atom carries the same representations in the same colours, and focus, tooltips, "
                "assembly and background agree (scripts/translate_mvs_to_api.py, state_differences)"
                + (f"; also for {', '.join(s[0] for s in scenes[1:])}" if scenes[1:] else ""))
    errors = T.validate_task(twin)
    if errors:
        raise Untranslatable("the twin failed its checks", f"format: {errors[0]}")
    view = T._with_aliases(dict(twin))
    problems = check.check_task(view) + runner.grader_problems(view)
    if problems:
        raise Untranslatable("the twin failed its checks", problems[0])
    done.append("schema-valid; replays with nothing ignored or unresolved; every selection selects atoms; "
                "every hide toggle hides a component the entry has (scripts/check_api_refs.py)")
    res = runner.grade_parsed(view, twin["reference"])
    if not (res["success"] and res["f1"] == 1.0 and res["target_f1"] == 1.0 and res["grader"] == "state"):
        raise Untranslatable("the twin failed its checks",
                             f"own reference: f1 {res['f1']}, success {res['success']}, target {res['target_f1']}")
    done.append("the reference grades as exactly right against the task (F1 1, success, target score 1)")
    if T.target_atoms(twin) != T.target_atoms(task):
        raise Untranslatable("the twin failed its checks", "the target atoms differ from the MVS task's")
    done.append("same prompt, structures, split, style and tier as the MVS task, and the same target atoms")
    for key in ("prompt", "structures", "split", "style", "tier"):
        assert twin[key] == task[key], key
    if T._mentions_worked_example(twin):
        raise Untranslatable("the twin failed its checks", "uses 1HSG, the prompt's worked example")


# --------------------------------------------------------------------------- #
# The corpus
# --------------------------------------------------------------------------- #
def plan(only: list[str] | None = None) -> tuple[list[dict], list[dict], list[dict]]:
    """(twins to write, one row per MVS task, the corpus). A row is ``{id, tier,
    family, format, twin, reason, detail}``; ``twin`` is the twin's id when one is
    written, ``reason`` is why not (or None)."""
    corpus = T.load_corpus()
    by_id = {t["id"]: t for t in corpus}
    todo = [t for t in corpus if t["track"] == "mvs" and (not only or t["id"] in only)]
    todo.sort(key=lambda t: (bool(t.get("paraphrase_of")), t["id"]))    # originals first
    # generators that write both tracks themselves decide which of their MVS tasks have
    # an API counterpart (a follow-up "start it spinning" changes nothing in MVS and
    # sets `spin` in the API: the same final state would be the wrong twin)
    two_track = {(t.get("provenance") or {}).get("script") for t in corpus
                 if t["track"] == "api" and not t.get("_legacy")} - {SCRIPT, None}
    twins: list[dict] = []
    made: dict[str, str] = {}
    rows = []
    for t in todo:
        row = {"id": t["id"], "tier": t["tier"], "family": t.get("family") or "",
               "format": "old" if t.get("_legacy") else "new", "twin": None, "reason": None, "detail": ""}
        rows.append(row)
        ours = twin_id(t["id"])
        other = by_id.get(t.get("twin_of") or "")
        if t.get("twin_of") and not (t["twin_of"] == ours and (
                other is None or (other.get("provenance") or {}).get("script") == SCRIPT)):
            row["reason"] = PAIRED
            row["detail"] = t["twin_of"]
            continue
        script = (t.get("provenance") or {}).get("script")
        if not t.get("_legacy") and script in two_track:
            row["reason"] = TWO_TRACK
            row["detail"] = script
            continue
        try:
            if t.get("_legacy"):
                structures = t["structures"]
                if len(structures) != 1:
                    raise Untranslatable("several structures in one scene", ", ".join(structures))
                other_entries(t, structures[0])
                translate_scene(t["reference"], structures[0])
                row["reason"] = OLD
                continue
            twin = make_twin(t, made)
        except Untranslatable as e:
            row["reason"], row["detail"] = e.reason, e.detail
            continue
        if ours in by_id and (by_id[ours].get("provenance") or {}).get("script") != SCRIPT:
            row["reason"], row["detail"] = "the twin's id is already taken", ours
            continue
        twins.append(twin)
        made[t["id"]] = row["twin"] = twin["id"]
    rows.sort(key=lambda r: r["id"])
    return twins, rows, corpus


def coverage(twins: list[dict]) -> list[str]:
    cov: Counter = Counter()
    for t in twins:
        seen = set()
        for act in t["reference"]:
            seen.add(("action", act["action"]))
            if act["action"] == "set_property":
                seen.add(("property", act["name"]))
            if act["action"] == "set_visual_style":
                seen.add(("visual style", act["style"]))
            if act["action"] == "color" and "non_selected_color" in act:
                seen.add(("call option", "color.non_selected_color"))
            for p in act.get("data") or []:
                seen |= {("selector key" if k in ps.LOCATOR_KEYS else "selection attribute", k) for k in p}
        cov.update(seen)
    return [f"| {kind} | `{name}` | {n} |" for (kind, name), n in sorted(cov.items())]


PAIRED = "already has a twin from its own generator"
TWO_TRACK = "left without an API counterpart by its own two-track generator"
OLD = "old task format (no twin_of field); a twin could be made"


def shares(rows: list[dict]) -> dict[str, int]:
    """The counts the report and the README give. ``candidates`` are the MVS tasks this
    script is the one to pair: in the task format, and not from a generator that writes
    both tracks itself."""
    n = Counter(r["reason"] for r in rows)
    old = sum(r["format"] == "old" for r in rows)
    candidates = [r for r in rows if r["format"] == "new" and r["reason"] not in (PAIRED, TWO_TRACK)]
    return {"read": len(rows), "paired_elsewhere": n[PAIRED], "two_track_unpaired": n[TWO_TRACK],
            "old_format": old, "old_format_expressible": n[OLD], "candidates": len(candidates),
            "twins": sum(bool(r["twin"]) for r in rows)}


def readme(twins: list[dict], rows: list[dict]) -> str:
    c = shares(rows)
    pct = lambda a, b: f"{100 * a / b:.0f}%" if b else "n/a"  # noqa: E731
    lines = ["# API twins of MVS tasks", "",
             "Written by `scripts/translate_mvs_to_api.py --all`; do not edit by hand. A twin has the "
             "prompt, structures, split, style, tier, family and target atoms of its MVS task, and a call "
             "list whose replayed final state is the MVS reference's drawn state (same atoms, "
             "representations and colours; nothing else drawn). `twin_of` links the two both ways.", "",
             "Run this script last, after every MVS generator: it writes `twin_of` into the MVS task files, "
             "so re-running an MVS generator afterwards removes those links (run this script again), and an "
             "MVS generator's own byte-for-byte rebuild check has to leave `twin_of` out of its comparison.", "",
             f"- MVS tasks read: {c['read']}",
             f"- already paired by their own generator (clinical, follow-up, accept-set, paraphrases): "
             f"{c['paired_elsewhere']}",
             f"- left without an API counterpart by a generator that writes both tracks: "
             f"{c['two_track_unpaired']}",
             f"- in the old task format (no `twin_of` field, so no twin is written): {c['old_format']}, of "
             f"which the API could express {c['old_format_expressible']}",
             f"- left for this script: {c['candidates']}; **twins written: {c['twins']} "
             f"({pct(c['twins'], c['candidates'])})**",
             f"- MVS tasks with an API twin, all generators together: {c['twins'] + c['paired_elsewhere']} of "
             f"{c['read']} ({pct(c['twins'] + c['paired_elsewhere'], c['read'])})", ""]
    mine = [r for r in rows if r["format"] == "new" and r["reason"] not in (PAIRED, TWO_TRACK)]
    if mine:
        lines += ["## Twins by template", "", "| tier | family | MVS tasks | twins |", "|---|---|---:|---:|"]
        per: dict[tuple, list[int]] = {}
        for r in mine:
            k = per.setdefault((r["tier"], r["family"]), [0, 0])
            k[0] += 1
            k[1] += bool(r["twin"])
        lines += [f"| {tier} | `{fam}` | {a} | {b} |" for (tier, fam), (a, b) in sorted(per.items())]
    if twins:
        bases = Counter(t["provenance"]["twin"]["base"] for t in twins)
        off = Counter(f for t in twins for f in t["provenance"]["twin"]["switched_off"])
        hinge = sum(bool(t["provenance"]["difficulty"]["hinges_on"]) for t in twins)
        plain = sum(not t["provenance"]["twin"]["switched_off"]
                    and t["provenance"]["twin"]["base"] == "the default view" for t in twins)
        lines += ["", "## How the twins reach the picture", "",
                  "An MVS scene draws only what it lists; a `load` draws the whole entry. So a twin has to "
                  "take away what the scene does not draw: with hide toggles (`provenance.twin.switched_off`) "
                  "or with a global style that draws polymer only (`provenance.twin.base`). The request says "
                  "what to show, not what to remove, so task success on a twin also asks the model to know "
                  "what a load draws by default. The paired analysis should report twins with and without "
                  "such steps separately (`provenance.difficulty.context_switched_off`, `order_matters`); "
                  "the target score does not depend on them.", "",
                  "- base: " + "; ".join(f"{k} {v}" for k, v in sorted(bases.items())),
                  "- hide toggles: " + ("; ".join(f"`{k}` {v}" for k, v in sorted(off.items())) or "none"),
                  f"- twins on the default view with nothing switched off: {plain}",
                  f"- twins with an added, coloured representation (`representationColor`): {hinge}", "",
                  "| surface | name | twins |", "|---|---|---:|", *coverage(twins)]
    missing = [r for r in rows if not r["twin"]]
    if missing:
        counts = Counter(r["reason"] for r in missing)
        lines += ["", "## MVS tasks without a twin from this script", "", "| reason | tasks |", "|---|---:|"]
        lines += [f"| {reason} | {k} |" for reason, k in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
        listed = [r for r in missing if r["reason"] != PAIRED]
        if listed:
            lines += ["", "| MVS task | tier | reason | detail |", "|---|---|---|---|"]
            lines += [f"| `{r['id']}` | {r['tier']} | {r['reason']} | {r['detail'][:160].replace('|', '/')} |"
                      for r in listed]
    return "\n".join(lines) + "\n"


def wanted_files(twins: list[dict], rows: list[dict], corpus: list[dict], whole: bool
                 ) -> dict[pathlib.Path, str]:
    """Path -> text of every file this run owns: the twins, the README (only when the
    whole corpus was translated), and each MVS file with its ``twin_of`` set."""
    out: dict[pathlib.Path, str] = {}
    for t in twins:
        out[OUT / f"{t['id']}.json"] = json.dumps(T.public_form(t), indent=2, ensure_ascii=False) + "\n"
    if whole:
        out[OUT / "README.md"] = readme(twins, rows)
    by_id = {t["id"]: t for t in corpus}
    for r in rows:
        if r["format"] != "new":
            continue
        path = REPO / by_id[r["id"]]["_path"]
        text = path.read_text()
        value = json.dumps(r["twin"]) if r["twin"] else None
        if value is None:
            # clear the link only if it points at a twin this script wrote earlier
            old = by_id.get(by_id[r["id"]].get("twin_of") or "")
            if old is None or (old.get("provenance") or {}).get("script") != SCRIPT:
                continue
        new, k = re.subn(r'("twin_of":\s*)(null|"[^"]*")', lambda m: m.group(1) + (value or "null"),
                         text, count=1)
        assert k == 1, f"{path}: no twin_of field"
        if new != text:
            out[path] = new
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ids", nargs="*", help="MVS task ids (default with --all: every MVS task)")
    ap.add_argument("--all", action="store_true", help="every MVS task under tasks/")
    ap.add_argument("--check", action="store_true", help="write nothing; fail if a file would change")
    ap.add_argument("--report", action="store_true", help="write nothing; print one line per MVS task")
    a = ap.parse_args(argv)
    if not a.all and not a.ids:
        ap.error("give task ids, or --all")
    twins, rows, corpus = plan(None if a.all else a.ids)
    for r in rows:
        if a.report or (not r["twin"] and r["reason"] != PAIRED):
            print(f"{r['id']:44} {r['twin'] or '-':44} {r['reason'] or 'twin'}"
                  + (f" ({r['detail'][:120]})" if r["detail"] else ""))
    c = shares(rows)
    print(f"{c['read']} MVS tasks: {c['paired_elsewhere']} already paired by their own generator, "
          f"{c['two_track_unpaired']} left unpaired by a two-track generator, {c['old_format']} in the old "
          f"format (the API could express {c['old_format_expressible']}); of the other {c['candidates']}, "
          f"{c['twins']} get a twin ({100 * c['twins'] / max(1, c['candidates']):.0f}%)")
    files = wanted_files(twins, rows, corpus, whole=a.all)
    stale = sorted(p for p in OUT.glob("*.json") if p not in files) if a.all and OUT.is_dir() else []
    changed = [p for p, text in files.items() if not p.exists() or p.read_text() != text]
    if a.check or a.report:
        for p in changed + stale:
            print(f"would change: {p.relative_to(REPO)}")
        print(f"{len(files)} files, {len(changed)} would change, {len(stale)} stale")
        return 1 if a.check and (changed or stale) else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text)
    print(f"wrote {len(twins)} twins ({len(changed)} files changed, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
