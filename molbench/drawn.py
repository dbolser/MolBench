"""
What both graders share: colours, the task palette, and the comparison of drawn states.

A **drawn state** says, for every atom, how it is drawn: a set of *draws*, each a
``(representation type, colour, opacity)`` triple. The MVS grader (``mvs.py``) resolves
a scene tree to one; the API grader (``pdbe_state.py``) replays a call list to one.
Sets of atoms are int bitmasks over the rows of a frozen atom table, or (for a
structure with no table) frozensets of selector descriptions; the helpers here work
on both.

Three things are defined here and nowhere else, so the two tracks cannot drift:

* ``COLOR_TOLERANCE`` and ``color_eq`` — when two colours count as the same;
* ``look_similarity`` — how alike two atoms' drawings are (1 = the same);
* ``target_score`` — the target score of decision 17.

GRADING.md is the plain-language version of all of it.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

# --- colours ----------------------------------------------------------------------

#: Largest per-channel difference (0-255 scale) at which two colours count as the same.
#: Evidence for the value is in GRADING.md ("Colour") and tests/controls/colour_evidence.json:
#: every pair of palette colours is at least 55 apart, and of the 2,303 colour values in
#: valid October scenes that could be compared with a reference colour, 2,227 were
#: exactly one and none of the other 76 was closer than 58 to one. Any tolerance from
#: 0 to 54 therefore gives the same verdicts on that evidence; 32 leaves room for a
#: hand-mixed shade of a named colour without letting one palette colour pass for
#: another.
COLOR_TOLERANCE = 32

# Mol*'s ColorNames (mol-util/color/names). The same table is in Mol* 5.9.0 (MVS
# ``color`` accepts exactly these lower-case names, checked in the viewer) and in the
# pdbe-molstar 3.3.2 bundle (``normalizeColor``).
_COLOR_NAMES_TEXT = (
    "aliceblue:f0f8ff antiquewhite:faebd7 aqua:00ffff aquamarine:7fffd4 azure:f0ffff "
    "beige:f5f5dc bisque:ffe4c4 black:000000 blanchedalmond:ffebcd blue:0000ff blueviolet:8a2be2 "
    "brown:a52a2a burlywood:deb887 cadetblue:5f9ea0 chartreuse:7fff00 chocolate:d2691e "
    "coral:ff7f50 cornflower:6495ed cornflowerblue:6495ed cornsilk:fff8dc crimson:dc143c "
    "cyan:00ffff darkblue:00008b darkcyan:008b8b darkgoldenrod:b8860b darkgray:a9a9a9 "
    "darkgreen:006400 darkgrey:a9a9a9 darkkhaki:bdb76b darkmagenta:8b008b darkolivegreen:556b2f "
    "darkorange:ff8c00 darkorchid:9932cc darkred:8b0000 darksalmon:e9967a darkseagreen:8fbc8f "
    "darkslateblue:483d8b darkslategray:2f4f4f darkslategrey:2f4f4f darkturquoise:00ced1 "
    "darkviolet:9400d3 deeppink:ff1493 deepskyblue:00bfff dimgray:696969 dimgrey:696969 "
    "dodgerblue:1e90ff firebrick:b22222 floralwhite:fffaf0 forestgreen:228b22 fuchsia:ff00ff "
    "gainsboro:dcdcdc ghostwhite:f8f8ff gold:ffd700 goldenrod:daa520 gray:808080 green:008000 "
    "greenyellow:adff2f grey:808080 honeydew:f0fff0 hotpink:ff69b4 indianred:cd5c5c "
    "indigo:4b0082 ivory:fffff0 khaki:f0e68c laserlemon:ffff54 lavender:e6e6fa "
    "lavenderblush:fff0f5 lawngreen:7cfc00 lemonchiffon:fffacd lightblue:add8e6 "
    "lightcoral:f08080 lightcyan:e0ffff lightgoldenrod:fafad2 lightgoldenrodyellow:fafad2 "
    "lightgray:d3d3d3 lightgreen:90ee90 lightgrey:d3d3d3 lightpink:ffb6c1 lightsalmon:ffa07a "
    "lightseagreen:20b2aa lightskyblue:87cefa lightslategray:778899 lightslategrey:778899 "
    "lightsteelblue:b0c4de lightyellow:ffffe0 lime:00ff00 limegreen:32cd32 linen:faf0e6 "
    "magenta:ff00ff maroon:800000 mediumaquamarine:66cdaa mediumblue:0000cd mediumorchid:ba55d3 "
    "mediumpurple:9370db mediumseagreen:3cb371 mediumslateblue:7b68ee mediumspringgreen:00fa9a "
    "mediumturquoise:48d1cc mediumvioletred:c71585 midnightblue:191970 mintcream:f5fffa "
    "mistyrose:ffe4e1 moccasin:ffe4b5 navajowhite:ffdead navy:000080 oldlace:fdf5e6 olive:808000 "
    "olivedrab:6b8e23 orange:ffa500 orangered:ff4500 orchid:da70d6 palegoldenrod:eee8aa "
    "palegreen:98fb98 paleturquoise:afeeee palevioletred:db7093 papayawhip:ffefd5 "
    "peachpuff:ffdab9 peru:cd853f pink:ffc0cb plum:dda0dd powderblue:b0e0e6 purple:800080 "
    "rebeccapurple:663399 red:ff0000 rosybrown:bc8f8f royalblue:4169e1 saddlebrown:8b4513 "
    "salmon:fa8072 sandybrown:f4a460 seagreen:2e8b57 seashell:fff5ee sienna:a0522d silver:c0c0c0 "
    "skyblue:87ceeb slateblue:6a5acd slategray:708090 slategrey:708090 snow:fffafa "
    "springgreen:00ff7f steelblue:4682b4 tan:d2b48c teal:008080 thistle:d8bfd8 tomato:ff6347 "
    "turquoise:40e0d0 violet:ee82ee wheat:f5deb3 white:ffffff whitesmoke:f5f5f5 yellow:ffff00 "
    "yellowgreen:9acd32 "
)
COLOR_NAMES: dict[str, tuple[int, int, int]] = {}
for _item in _COLOR_NAMES_TEXT.split():
    _name, _hex = _item.split(":")
    COLOR_NAMES[_name] = (int(_hex[0:2], 16), int(_hex[2:4], 16), int(_hex[4:6], 16))

#: The colour names a task may ask for. Any two are more than ``COLOR_TOLERANCE``
#: apart in at least one channel (in fact at least 55; ``tests/test_grading_semantics.py``
#: checks it), so one palette colour can never pass for another. Names outside the
#: palette are still understood in answers; they are just not used in prompts.
#: "gray" and "grey" are one colour, as are "cyan"/"aqua" and "magenta"/"fuchsia".
TASK_PALETTE = ("red", "orange", "yellow", "green", "blue", "purple", "magenta", "cyan",
                "teal", "gray", "white", "black", "salmon", "steelblue", "khaki", "plum",
                "limegreen", "hotpink", "brown")

RGB = tuple  # (r, g, b)
WHITE = (255, 255, 255)


def color_distance(a: RGB, b: RGB) -> int:
    """Largest per-channel difference between two RGB colours."""
    return max(abs(int(x) - int(y)) for x, y in zip(a, b))


def color_eq(a: Any, b: Any) -> bool:
    """Two colours are the same if every channel is within ``COLOR_TOLERANCE``. A colour
    that is not an RGB triple (a colour-theme token such as ``("theme", "chain-id")``)
    equals only itself."""
    if _is_rgb(a) and _is_rgb(b):
        return color_distance(a, b) <= COLOR_TOLERANCE
    return a == b


def _is_rgb(c: Any) -> bool:
    return isinstance(c, tuple) and len(c) == 3 and all(isinstance(v, int) for v in c)


def mvs_color(value: Any) -> Any:
    """An MVS ``color`` value as Mol* 5.9.0 reads it: a lower-case Mol* colour name,
    ``#rrggbb`` or ``#rgb`` in either case. Anything else (``"RED"``, ``"rgb(...)"``, a
    number) is rejected by Mol* with the whole scene; it becomes an ``("invalid", …)``
    token here, which matches no real colour. Checked in the viewer."""
    if isinstance(value, str):
        v = value.strip()
        if v in COLOR_NAMES:
            return COLOR_NAMES[v]
        if v[:1] == "#" and len(v) in (4, 7):
            h = v[1:]
            try:
                int(h, 16)
            except ValueError:
                return ("invalid", value)
            if len(h) == 3:
                h = "".join(c * 2 for c in h)
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return ("invalid", str(value))


# --- atom sets (bitmask or frozenset) ---------------------------------------------

def size(m: Any) -> int:
    return m.bit_count() if isinstance(m, int) else len(m)


def minus(a: Any, b: Any) -> Any:
    return a & ~b if isinstance(a, int) else a - b


def empty_like(m: Any) -> Any:
    return 0 if isinstance(m, int) else frozenset()


def jaccard(a: Any, b: Any) -> float:
    union = size(a | b)
    return size(a & b) / union if union else 1.0


# --- the camera -------------------------------------------------------------------

#: Is a focus the request did not ask for counted against the answer? No: the camera is
#: where one looks from, not what is drawn, and the rating study frames both renders
#: alike (decision 24). The focus is graded when the reference has one: then the
#: answer's focus target (the whole structure, if it has no focus) must be the same
#: residues. Set to True to make any focus a fact on both sides (the October regrade
#: reports task success both ways).
GRADE_UNREQUESTED_FOCUS = False

# --- draws and looks --------------------------------------------------------------

#: Credit for a draw whose representation type is right but whose colour or opacity
#: is not ("right atoms, right representation, wrong colour").
PARTIAL = 0.5
#: Two opacities within this are the same.
OPACITY_TOLERANCE = 0.05


def draw_eq(a: tuple, b: tuple) -> bool:
    """Two draws ``(type, colour[, opacity])`` are the same drawing."""
    if a[0] != b[0] or not color_eq(a[1], b[1]):
        return False
    oa = a[2] if len(a) > 2 else 1.0
    ob = b[2] if len(b) > 2 else 1.0
    try:
        return abs(float(oa) - float(ob)) <= OPACITY_TOLERANCE
    except (TypeError, ValueError):
        return oa == ob


def look_eq(a: Iterable[tuple], b: Iterable[tuple]) -> bool:
    return look_similarity(a, b) == 1.0


def look_similarity(a: Iterable[tuple], b: Iterable[tuple]) -> float:
    """How alike two atoms are drawn, in [0, 1].

    Each side is a collection of draws. Draws are paired off: an identical pair
    scores 1, a pair with the same representation type but another colour or opacity
    scores ``PARTIAL``, an unpaired draw scores 0. The total is divided by the larger
    number of draws, so a missing draw and an extra draw both cost. Two undrawn atoms
    are alike (1); a drawn and an undrawn atom are not (0).
    """
    a, b = list(a), list(b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    left = list(b)
    got = 0.0
    rest = []
    for d in a:
        hit = next((x for x in left if draw_eq(d, x)), None)
        if hit is None:
            rest.append(d)
        else:
            left.remove(hit)
            got += 1.0
    for d in rest:
        hit = next((x for x in left if x[0] == d[0]), None)
        if hit is not None:
            left.remove(hit)
            got += PARTIAL
    return got / max(len(a), len(b))


def partition(draws: dict[tuple, Any]) -> list[tuple[Any, tuple]]:
    """Split the drawn atoms into classes of atoms drawn the same way.

    ``draws`` maps a draw to the atoms that carry it. Returns ``[(atoms, look)]``
    where ``look`` is the sorted tuple of all draws on those atoms; undrawn atoms are
    in no class.
    """
    parts: list[tuple[Any, tuple]] = []
    for draw, mask in sorted(draws.items(), key=lambda kv: repr(kv[0])):
        if not size(mask):
            continue
        nxt = []
        left = mask
        for m, look in parts:
            hit = m & left
            if size(hit):
                nxt.append((hit, look + (draw,)))
                out = minus(m, hit)
                if size(out):
                    nxt.append((out, look))
                left = minus(left, hit)
            else:
                nxt.append((m, look))
        if size(left):
            nxt.append((left, (draw,)))
        parts = nxt
    merged: dict[tuple, Any] = {}
    for m, look in parts:
        key = tuple(sorted(look, key=repr))
        merged[key] = merged[key] | m if key in merged else m
    return [(m, look) for look, m in merged.items()]


def class_score(mask: Any, look: tuple, theirs: list[tuple[Any, tuple]]) -> float:
    """The share of a class's atoms that the other side draws the same way (graded by
    ``look_similarity``; an atom the other side does not draw counts 0)."""
    n = size(mask)
    if not n:
        return 0.0
    return sum(size(mask & om) * look_similarity(look, olook) for om, olook in theirs) / n


# --- the target score -------------------------------------------------------------

def target_display(ref: dict[tuple, Any], pred: dict[tuple, Any], target: Any
                   ) -> list[dict[str, Any]]:
    """Score the answer's drawing of the target atoms (decision 17).

    ``ref`` and ``pred`` map a draw to the atoms that carry it (for the API track the
    draws are the *changes* from a bare load, see ``pdbe_state.changes``); ``target`` is
    the atom set the request is about. The reference's drawing of the target (the
    draws that lie wholly inside it) is cut into classes (atoms drawn the same way).
    For each class, in units of
    (atom, draw) items:

    * ``wanted``   the reference's items on the class;
    * ``credit``   1 for each of them the answer has, ``PARTIAL`` for one the answer
                   draws with the right representation type but another colour or
                   opacity;
    * ``attempted`` how many of them the answer drew at all (right type);
    * ``spill``    answer items *outside* the target that repeat what the answer drew
                   on this class, where the reference draws no such thing: the answer
                   did to other atoms what was asked for these.

    ``recall = credit / wanted`` and ``precision = credit / (attempted + spill)``.
    Anything else the answer draws (context the request did not mention, in another
    style) is ignored: that is the difference from F1 and task success.
    """
    out = []
    # The target's drawing is what the reference draws on the target atoms *only*: a
    # draw confined to them (the red sticks of the residue), not one that merely
    # passes through (the grey cartoon of the whole chain). If nothing is confined to
    # the target, it is everything drawn on it.
    ref_on_target = {d: m for d, m in ref.items() if size(m) and not size(minus(m, target))}
    if not ref_on_target:
        ref_on_target = {d: m & target for d, m in ref.items() if size(m & target)}
    for mask, look in partition(ref_on_target):
        wanted = size(mask) * len(look)
        credit = 0.0
        attempted = 0
        own_style: list[tuple] = []          # what the answer drew on this class, by type
        for d in look:
            left = mask
            for pd, pm in pred.items():      # identical draws first
                if draw_eq(d, pd):
                    hit = left & pm
                    n = size(hit)
                    if n:
                        credit += n
                        attempted += n
                        left = minus(left, hit)
                        if pd not in own_style:
                            own_style.append(pd)
            for pd, pm in pred.items():      # then the right type in another colour
                if pd[0] == d[0] and not draw_eq(d, pd):
                    hit = left & pm
                    n = size(hit)
                    if n:
                        credit += n * PARTIAL
                        attempted += n
                        left = minus(left, hit)
                        if pd not in own_style:
                            own_style.append(pd)
        spill = 0
        for pd in own_style:
            outside = minus(pred[pd], target)
            for rd, rm in ref.items():       # where the reference draws the same, it is not spill
                if draw_eq(pd, rd):
                    outside = minus(outside, rm)
            spill += size(outside)
        denom = attempted + spill
        out.append({"fact": "target", "value": _show_look(look), "atoms": size(mask),
                    "recall": credit / wanted if wanted else 0.0,
                    "precision": credit / denom if denom else 0.0,
                    "spill": spill})
    return out


def target_summary(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Target precision, recall and F1 from per-fact parts (each weight 1)."""
    if not parts:
        return {"target_precision": 0.0, "target_recall": 0.0, "target_f1": 0.0, "target_facts": []}
    r = sum(p["recall"] for p in parts) / len(parts)
    p = sum(p["precision"] for p in parts) / len(parts)
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"target_precision": round(p, 4), "target_recall": round(r, 4),
            "target_f1": round(f, 4),
            "target_facts": [{**x, "recall": round(x["recall"], 3),
                              "precision": round(x["precision"], 3)} for x in parts]}


def _show_look(look: Iterable[tuple]) -> list:
    return [[_show(x) for x in d] for d in look]


def _show(v: Any) -> Any:
    if isinstance(v, frozenset):
        return sorted(map(str, v))
    if isinstance(v, tuple):
        return [_show(x) for x in v]
    return v


show = _show
show_look = _show_look

#: The keys every grading result has, on both tracks (``grader.grade_task``).
RESULT_KEYS = ("precision", "recall", "f1", "success", "target_precision", "target_recall",
               "target_f1", "outcome", "grader", "matched_reference", "same_structure",
               "structure", "n_ref", "n_pred", "reference_facts", "predicted_facts",
               "target_facts")

ZERO = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "success": False,
        "target_precision": 0.0, "target_recall": 0.0, "target_f1": 0.0}


def zero(**extra: Any) -> dict[str, Any]:
    """A zero result with every shared key present, except ``outcome``: that is set
    by ``grader.grade_task`` (callers that classify outputs themselves rely on its
    absence)."""
    out: dict[str, Any] = {**ZERO, "grader": None, "matched_reference": 0,
                           "same_structure": False, "structure": [None, None], "n_ref": 0,
                           "n_pred": 0, "reference_facts": [], "predicted_facts": [],
                           "target_facts": []}
    out.update(extra)
    return out
