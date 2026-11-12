"""
MolViewSpec (MVS) support — the v0.2 primary grading target.

Where the imperative IR (``schema.py``) grades a flat list of PDBeMolstar calls,
MVS grades a **declarative scene tree**: ``root -> download -> parse -> structure
-> component -> representation -> color`` (+ ``focus``, ``label``, ...). The model
under test emits an MVS state as JSON; we normalise it and compare tree shape +
parameters against a reference authored with the official ``molviewspec`` builder.

Why trees, and why this grader:
* The *meaning* of a scene is the set of root-to-leaf **paths** — "the polymer is a
  grey cartoon", "residue A/35 is red ball-and-stick". Comparing the set of paths
  is naturally order-independent (children can be emitted in any order) and yields
  graceful partial credit (a path matching 5 of 6 segments is nearly right).
* ``metadata.timestamp`` is non-deterministic, so we strip metadata before
  comparing — otherwise no two builds would ever match.

Grading reuses the precision/recall/F1 + greedy-bipartite shape from
``grader.py`` so scores are comparable in spirit across both tracks.
"""

from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from .atoms import AtomTable, load_table

# --- selection normalisation (the ComponentExpression sub-language) ---------------
# Selections are graded by the atoms they pick (``atoms.py``) when the structure has a
# frozen atom table. Without one (a structure no task references, an assembly) we
# fall back to these string signatures, which treat author/label chain ids as
# interchangeable and the residue-number spellings as one "resnum" axis.
_CHAIN_FIELDS = ("auth_asym_id", "label_asym_id")
_RESNUM_FIELDS = ("auth_seq_id", "label_seq_id", "residue_index")
_BEG_FIELDS = ("beg_auth_seq_id", "beg_label_seq_id")
_END_FIELDS = ("end_auth_seq_id", "end_label_seq_id")


def _first(d: dict, fields) -> Any:
    return next((d[f] for f in fields if d.get(f) is not None), None)


def _selector_signature(sel: Any) -> Any:
    """Canonicalise a component selector (string like 'polymer', or an expression)."""
    if isinstance(sel, str):
        return sel
    exprs = sel if isinstance(sel, list) else [sel]
    sigs = []
    for e in exprs:
        if not isinstance(e, dict):
            sigs.append(("raw", str(e)))
            continue
        chain = _first(e, _CHAIN_FIELDS)
        resnum = _first(e, _RESNUM_FIELDS)
        beg, end = _first(e, _BEG_FIELDS), _first(e, _END_FIELDS)
        comp = e.get("label_comp_id") or e.get("auth_comp_id")
        comp = comp.upper() if isinstance(comp, str) else comp
        atom = e.get("label_atom_id") or e.get("auth_atom_id")
        element = e.get("type_symbol")
        element = element.upper() if isinstance(element, str) else element
        sigs.append((
            ("chain", str(chain) if chain is not None else None),
            ("resnum", resnum),
            ("range", (beg, end) if (beg is not None or end is not None) else None),
            ("comp", comp),
            ("atom", atom),
            ("element", element),
        ))
    return tuple(sorted(map(str, sigs)))


@dataclass(frozen=True)
class Selection:
    """What a component or primitive end selects.

    ``atoms`` is (structure id, bitmask) when resolved against a frozen atom table;
    ``sigs`` holds one string signature per expression, used when either side of a
    comparison couldn't be resolved.
    """
    sigs: frozenset
    atoms: tuple[str, int] | None = None


def _selection(selectors: list, table: AtomTable | None) -> Selection:
    """The union of several selectors (a component's, or a merged group's)."""
    sigs = frozenset(_selector_signature(e) for s in selectors
                     for e in (s if isinstance(s, list) else [s]))
    if table is None:
        return Selection(sigs)
    mask = 0
    for s in selectors:
        m = table.selector(s)
        if m is None:
            return Selection(sigs)
        mask |= m
    return Selection(sigs, (table.id, mask))


def _selection_similarity(a: Selection, b: Selection) -> float:
    """Jaccard overlap of the selected atoms (else of the signatures).

    An empty selection overlaps nothing, so it never earns credit: Mol* draws
    nothing for it (or, for a primitive end, a point at the origin). The exception
    is a reference that is itself empty (a templated "show the ligands" on an entry
    with none): atoms can't grade that, so both sides fall back to signatures.
    """
    if a.atoms and b.atoms and a.atoms[0] == b.atoms[0] and (a.atoms[1] or b.atoms[1]):
        x, y = a.atoms[1], b.atoms[1]
        both = (x & y).bit_count()
        return both / (x | y).bit_count() if both else 0.0
    either = a.sigs | b.sigs
    return len(a.sigs & b.sigs) / len(either) if either else 0.0


def _color_signature(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip().lower().lstrip("#")
        return "grey" if v == "gray" else v   # fold the common spelling split
    return value


_PRIMITIVE_POINTS = ("start", "end", "position", "a", "b", "c")
_UNDIRECTED_PRIMITIVES = {"tube", "distance_measurement"}


def _point_signature(point: Any, table: AtomTable | None = None) -> Any:
    """A primitive position: an [x, y, z] coordinate (order matters) or an atom selection."""
    if isinstance(point, list) and all(isinstance(v, (int, float)) for v in point):
        return ("xyz", tuple(float(v) for v in point))
    if isinstance(point, dict) and "expressions" in point:
        # {structure_ref, expressions}: a union. Another structure's ref isn't resolved.
        exprs = point["expressions"] if isinstance(point["expressions"], list) else []
        return _selection([exprs], None if point.get("structure_ref") else table)
    return _selection([point], table)


def _points_match(p: Any, q: Any) -> bool:
    if isinstance(p, Selection) and isinstance(q, Selection):
        return _selection_similarity(p, q) == 1.0
    return p == q


def _interactions_flag(custom: dict) -> tuple:
    # Mol* computes and draws the interactions itself when this flag is set, so
    # it is part of what the component shows, not a styling detail.
    if not custom.get("molstar_show_non_covalent_interactions"):
        return ()
    # The radius decides which neighbours are drawn; Mol*'s default is 5 Å.
    radius = custom.get("molstar_non_covalent_interactions_radius_ang", 5)
    try:
        radius = round(float(radius), 1)
    except (TypeError, ValueError):
        pass
    return ("interactions", radius)


def _param_signature(kind: str, params: dict | None, custom: dict | None = None,
                     table: AtomTable | None = None) -> Any:
    params = params or {}
    custom = custom if isinstance(custom, dict) else {}
    if kind == "component" and "selector" in params:
        return ("selector", _selection([params["selector"]], table)) + _interactions_flag(custom)
    if kind == "primitive":
        # Key on the shape and the atoms it joins. Radius, dash length and label text
        # are styling. A line or distance is the same whichever end comes first; an
        # arrow's direction and an angle's vertex are not, so those keep their roles.
        pkind = params.get("kind")
        points = tuple((k, _point_signature(params[k], table)) for k in _PRIMITIVE_POINTS
                       if k in params)
        # A 3D label's text is its content (unlike a measurement's label template).
        text = (" ".join(str(params.get("text", "")).split()).casefold(),) if pkind == "label" else ()
        return ("primitive", pkind, points) + text
    if kind == "primitives":
        return ()  # a grouping node; its colour is styling
    if kind == "color" and custom.get("molstar_color_theme_name"):
        # The theme overrides the placeholder colour, so grade the theme (and where it applies).
        sig = ("theme", custom["molstar_color_theme_name"])
        if "selector" in params:
            sig += (_selector_signature(params["selector"]),)
        return sig
    if kind == "representation":
        # Key on the representation *type* only. The builder injects secondary
        # defaults (e.g. surface_type='molecular') that a model shouldn't be
        # required to reproduce; the benchmark asks "did you pick 'surface'?".
        return ("type", params.get("type"))
    if kind == "color" and "color" in params:
        # A colour may apply to part of the representation; where it lands is content.
        sig = ("color", _color_signature(params["color"]))
        if "selector" in params:
            sig += (("on", _selection([params["selector"]], table)),)
        return sig
    if kind == "download" and "url" in params:
        # Compare on the structure id, not the exact host/path (rcsb vs ebi etc) or
        # file variant (1cbs vs 1cbs_updated vs 1cbs-assembly1).
        url = str(params["url"]).lower()
        ident = url.rsplit("/", 1)[-1].split(".")[0]
        ident = re.sub(r"[_-](updated|full|bcif|cif|assembly\d*|model\d*)$", "", ident)
        return ("ref", ident)
    return tuple(sorted((k, _color_signature(v) if k == "color" else v)
                        for k, v in params.items()))


# --- tree handling ----------------------------------------------------------------

def extract_root(obj: Any) -> dict | None:
    """Accept a full MVS state, a {'root': ...} wrapper, or a bare root node."""
    if not isinstance(obj, dict):
        return None
    if obj.get("kind") == "root":
        return obj
    if isinstance(obj.get("root"), dict):
        return obj["root"]
    return None


def _structure_source(kind: str, params: dict, source: str | None) -> str | None:
    """Track which frozen atom table (if any) the selections below a node refer to."""
    if kind == "download":
        url = str(params.get("url", "")).lower()
        name = url.rsplit("/", 1)[-1]
        if "." in name and not re.search(r"\.(cif|mmcif|bcif)(\.gz)?$", name):
            return None  # e.g. a .pdb file: Mol* derives its label_* fields differently
        sig = _param_signature("download", params)
        return sig[1] if sig and sig[0] == "ref" else None
    if kind == "parse" and params.get("format") not in (None, "mmcif", "bcif"):
        return None
    return source


def _structure_table(params: dict, source: str | None) -> AtomTable | None:
    # Tables hold model 1 of the asymmetric unit; an assembly, symmetry mates or
    # another model keep the string signatures.
    if params.get("type", "model") != "model" or params.get("model_index") not in (None, 0):
        return None
    return load_table(source)


def _canon(x: Any) -> Any:
    """A deterministic, comparable form of a path (for grouping identical ones)."""
    if isinstance(x, Selection):
        # hex, not the int itself: the caller takes repr(), and Python refuses to print
        # an int of more than 4300 digits (a structure of more than about 14,000 atoms)
        return ("sel", tuple(sorted(map(repr, x.sigs))),
                (x.atoms[0], hex(x.atoms[1])) if x.atoms else None)
    if isinstance(x, tuple):
        return tuple(_canon(v) for v in x)
    return x


def flatten_paths(root: dict) -> list[tuple]:
    """Return every root-to-leaf path as a tuple of (kind, param_signature) segments.

    Under one structure, component paths that do the same thing below the component
    (same representation, colour, ...) are merged into one path whose selection is
    the union of their atoms: "one component listing six residues", "six components
    with the same style" and "one expression covering the same atoms" are the same
    scene, so they become the same single path. A residue that also gets its own
    label keeps that label as a separate path, so the shared style still merges.
    """

    def paths(node: dict, source: str | None, table: AtomTable | None) -> list[tuple]:
        kind = node.get("kind")
        params = node.get("params")
        # A model may emit a structurally-odd tree (e.g. params as a list, not a
        # dict). Grade it gracefully — treat malformed params as empty — rather
        # than crashing the whole run on one bad node.
        if not isinstance(params, dict):
            params = {}
        children = [c for c in node.get("children") or [] if isinstance(c, dict)]
        source = _structure_source(kind, params, source)
        if kind == "structure":
            table = _structure_table(params, source)
            below = merged_children(children, source, table)
        else:
            below = [p for c in children for p in paths(c, source, table)]
        here = ((kind, _param_signature(kind, params, node.get("custom"), table)),)
        return [here + p for p in below] or [here]

    def merged_children(children: list[dict], source: str | None,
                        table: AtomTable | None) -> list[tuple]:
        # Group the components' paths by what is done to the atoms (the rest of the
        # path below the component), and union the atoms per group.
        out: list[tuple] = []
        groups: dict[tuple, tuple] = {}
        for c in children:
            params = c.get("params")
            if c.get("kind") != "component" or not isinstance(params, dict) \
                    or "selector" not in params:
                out.extend(paths(c, source, table))
                continue
            custom = c.get("custom") if isinstance(c.get("custom"), dict) else {}
            flag = _interactions_flag(custom)
            below = [p for cc in c.get("children") or [] if isinstance(cc, dict)
                     for p in paths(cc, source, table)]
            for p in below or [()]:
                key = (flag, repr(_canon(p)))
                groups.setdefault(key, (flag, p, []))[2].append(params["selector"])
        for flag, below, selectors in groups.values():
            out.append((("component", ("selector", _selection(selectors, table)) + flag),) + below)
        return out

    return paths(root, None, None)


# Boilerplate nodes carry little signal (almost every scene parses mmcif into a
# model), so they're down-weighted; the root is structural scaffolding worth 0.
# Everything else (download target, component, representation, color, focus...)
# is the discriminating content and keeps full weight.
_SEG_WEIGHT = {"root": 0.0, "parse": 0.25, "structure": 0.25}


def _primitives_match(x: tuple, y: tuple) -> bool:
    (_, kind, p, *text), (_, kind_y, q, *text_y) = x, y
    if kind != kind_y or text != text_y or len(p) != len(q):
        return False
    if kind in _UNDIRECTED_PRIMITIVES:
        ends = [v for _, v in p]
        return any(all(_points_match(a, b) for a, b in zip(ends, perm))
                   for perm in itertools.permutations(v for _, v in q))
    return all(k == k_y and _points_match(a, b) for (k, a), (k_y, b) in zip(p, q))


def _segment_similarity(a: tuple | None, b: tuple | None) -> float:
    """1 for the same node, 0 for a different one; a component's selection can score between."""
    if a is None or b is None or a[0] != b[0]:
        return 0.0
    kind, x, y = a[0], a[1], b[1]
    if kind == "component" and x[:1] == y[:1] == ("selector",):
        return _selection_similarity(x[1], y[1]) if x[2:] == y[2:] else 0.0
    if kind == "color" and x[:1] == y[:1] == ("color",) and len(x) == len(y) == 3:
        # Same colour on part of the structure: credit the share of atoms it covers.
        return _selection_similarity(x[2][1], y[2][1]) if x[1] == y[1] else 0.0
    if kind == "primitive" and x[:1] == y[:1] == ("primitive",):
        return float(_primitives_match(x, y))
    return float(x == y)


def _path_similarity(p: tuple, q: tuple) -> float:
    """Weighted position-wise segment agreement.

    Earlier this used longest-common-*prefix*, which let an incidental mismatch
    near the root (e.g. a file-variant in the download node) zero out credit for
    a correct representation/colour further down. Position-wise scoring keeps that
    downstream credit; boilerplate nodes are down-weighted so they neither dominate
    nor mask the real differences. A component's selection earns the share of
    atoms it gets right (see ``_selection_similarity``).
    """
    num = den = 0.0
    for i in range(max(len(p), len(q))):
        a = p[i] if i < len(p) else None
        b = q[i] if i < len(q) else None
        kind = (a or b)[0]
        w = _SEG_WEIGHT.get(kind, 1.0)
        den += w
        num += w * _segment_similarity(a, b)
    return num / den if den else 0.0


# --- grading ----------------------------------------------------------------------

def _download_id(seg: tuple) -> str | None:
    """The structure id in a ``download`` path segment, or None (a download node with
    no/malformed params has an empty signature — a model can emit that)."""
    kind, sig = seg
    if kind == "download" and isinstance(sig, tuple) and len(sig) == 2 and sig[0] == "ref":
        return sig[1]
    return None


def _fold_accepted_refs(ref_paths: list[tuple], pred_paths: list[tuple],
                        accepted: set[str]) -> list[tuple]:
    """Treat any accepted structure id in the prediction as the reference's own.

    A prompt that names a protein ("a structure of PDE5A") has many right answers;
    the task lists them in ``accepted_ids``. The reference carries one canonical id,
    so a prediction that downloaded another accepted entry is rewritten to that id
    before matching. An id outside the set (a made-up one, say) stays as it is and
    mismatches the download segment like any other wrong answer.
    """
    ref_ids = {_download_id(seg) for path in ref_paths for seg in path} - {None}
    if len(ref_ids) != 1:
        return pred_paths  # several structures: no single canonical id to fold onto
    canonical = next(iter(ref_ids))
    accepted = {a.lower() for a in accepted}

    def fold(seg: tuple) -> tuple:
        if _download_id(seg) in accepted:
            return ("download", ("ref", canonical))
        return seg

    return [tuple(fold(seg) for seg in path) for path in pred_paths]


def grade_mvs_paths(reference: Any, predicted: Any,
                    accepted_refs: set[str] | list[str] | None = None) -> dict[str, Any]:
    """The October 2026 grader ("old F1"): greedy matching of root-to-leaf paths.

    Kept only for comparison with the October numbers (``tests/controls/
    october_regrade.json``); ``grade_mvs`` below, on the drawn state, replaced it.

    ``accepted_refs``: other structure ids that count as the reference's (see
    ``_fold_accepted_refs``); used by tasks that name a protein instead of an id.
    """
    ref_root, pred_root = extract_root(reference), extract_root(predicted)
    if ref_root is None:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "error": "bad reference tree"}
    if pred_root is None:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0,
                "error": "prediction is not an MVS state tree"}

    ref_paths = flatten_paths(ref_root)
    pred_paths = flatten_paths(pred_root)
    if accepted_refs:
        pred_paths = _fold_accepted_refs(ref_paths, pred_paths, set(accepted_refs))
    n_ref, n_pred = len(ref_paths), len(pred_paths)
    if n_ref == 0:
        f1 = 1.0 if n_pred == 0 else 0.0
        return {"precision": f1, "recall": 1.0, "f1": f1}

    pairs = sorted(
        ((_path_similarity(r, p), i, j)
         for i, r in enumerate(ref_paths) for j, p in enumerate(pred_paths)),
        reverse=True,
    )
    used_ref: set[int] = set()
    used_pred: set[int] = set()
    matched = 0.0
    for s, i, j in pairs:
        if s == 0 or i in used_ref or j in used_pred:
            continue
        used_ref.add(i)
        used_pred.add(j)
        matched += s

    precision = matched / n_pred if n_pred else 0.0
    recall = matched / n_ref
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "n_ref_paths": n_ref,
        "n_pred_paths": n_pred,
    }


def categorize(root: dict) -> list[str]:
    """Derive skill categories from a scene tree, for leaderboard drill-down.

    The categories *are* the tree's content: what node kinds and selector shapes
    appear. This means every task — hand-authored or ingested — gets consistent,
    objective tags without manual labelling.
    """
    kinds: dict[str, int] = {}
    has_expr = False
    reps: set[str] = set()
    interactions = False

    def walk(node: dict) -> None:
        nonlocal has_expr, interactions
        k = node.get("kind")
        kinds[k] = kinds.get(k, 0) + 1
        params = node.get("params") or {}
        if k == "component" and not isinstance(params.get("selector"), str):
            has_expr = True
        if k == "color" and "selector" in params and not isinstance(params["selector"], str):
            has_expr = True  # recolouring part of a representation is a selection too
        custom = node.get("custom")
        if k == "component" and isinstance(custom, dict) \
                and custom.get("molstar_show_non_covalent_interactions"):
            interactions = True
        if k == "representation":
            reps.add(params.get("type"))
        for c in node.get("children") or []:
            if isinstance(c, dict):
                walk(c)

    walk(root)
    cats: list[str] = []
    if "download" in kinds:
        cats.append("load")
    if has_expr:
        cats.append("selection")
    if "representation" in kinds:
        cats.append("representation")
    if "color" in kinds:
        cats.append("color")
    if kinds.get("focus") or kinds.get("camera"):
        cats.append("camera")
    if kinds.get("component", 0) > 1:
        cats.append("multi-component")
    if kinds.get("label") or kinds.get("tooltip"):
        cats.append("annotation")
    if reps & {"surface", "isosurface", "gaussian-surface", "molecular-surface"}:
        cats.append("surface")
    if kinds.get("opacity"):
        cats.append("transparency")
    if kinds.get("primitive"):
        cats.append("measurement")
    if interactions:
        cats.append("interactions")
    if kinds.get("volume"):
        cats.append("volume")
    return cats


def validate_mvs(obj: Any) -> list[str]:
    """Structural validation via the molviewspec library if available; else minimal."""
    root = extract_root(obj)
    if root is None:
        return ["not an MVS state tree (need a 'root' node)"]
    try:
        from molviewspec import validate_state_tree  # type: ignore
        state = obj if obj.get("kind") in ("single", "multiple") else {"kind": "single", "root": root}
        # Models are asked for the tree only; the envelope's metadata is the caller's job.
        meta = state.get("metadata") if isinstance(state.get("metadata"), dict) else {}
        state = {**state, "metadata": {"version": "1", "timestamp": "1970-01-01T00:00:00Z", **meta}}
        validate_state_tree(json.dumps(state))  # it parses JSON text, not a dict
        return []
    except ImportError:
        return []  # library absent: skip deep validation, tree shape already checked
    except Exception as e:  # noqa: BLE001 - surface validation message to the report
        return [f"MVS validation: {e}"]


# ==================================================================================
# The drawn state: what Mol* would show for a scene, and the grader built on it
# ==================================================================================
#
# Everything below resolves a scene tree to its *drawn state* and compares two drawn
# states. The rules are those of Mol* 5.9.0's MVS extension, read back from the
# headless viewer (``scripts/grader_controls.py --viewer`` re-checks them):
#
# * A representation draws atoms of its component. ``ball_and_stick``, ``line``,
#   ``spacefill`` and ``surface`` draw every atom. ``cartoon``, ``backbone`` and
#   ``putty`` draw **polymer residues whose trace atom is in the component** (CA for
#   a protein residue, O3' for a nucleotide), and nothing else: under a cartoon,
#   ``all`` and ``polymer`` are the same drawing, and so are a residue and its CA.
#   ``carbohydrate`` draws the sugar residues of the component and the polymer
#   residues they are bonded to.
# * A type that does not apply to its component is silently replaced: a ribbon type
#   on a component with no polymer atoms (a ligand, an ion, water) is drawn as
#   ball-and-stick; ``carbohydrate`` in a structure with no sugars is drawn as a
#   cartoon (or ball-and-stick). A component that selects nothing draws nothing.
# * Colour: a representation with no ``color`` child is white. ``color`` children
#   apply in order, each to its ``selector`` (default: everything), later ones over
#   earlier ones. A ribbon residue takes the colour of its trace atom. A ``color``
#   whose ``custom.molstar_color_theme_name`` is set applies that Mol* colour theme
#   instead of the colour (to its selector).
# * ``opacity`` (child of a representation) sets the opacity of the whole
#   representation; the default is 1.
# * Two representations on overlapping components are both drawn: an atom can carry
#   several draws.
# * ``focus`` nodes: the camera frames the union of the components that carry one.
# * ``color`` names are Mol*'s lower-case names; ``#rrggbb`` and ``#rgb`` in either
#   case. Anything else makes Mol* reject the whole scene.

from . import drawn as _drawn  # noqa: E402
from .drawn import (class_score, color_eq, empty_like, jaccard, minus, mvs_color,  # noqa: E402
                    partition, size)

RIBBON_TYPES = ("cartoon", "backbone", "putty")
ATOMIC_TYPES = ("ball_and_stick", "line", "spacefill", "surface")
REPRESENTATION_TYPES = RIBBON_TYPES + ATOMIC_TYPES + ("carbohydrate",)
#: Colour themes that colour by a category the atom table holds. A reference that uses
#: one is matched by an answer that gives every group its own single colour.
PARTITION_THEMES = {"chain-id": "auth_asym_id", "entity-id": "label_entity_id"}
DEFAULT_BACKGROUND = (255, 255, 255)

# node kinds that are scaffolding or handled explicitly; anything else is a generic fact
_IGNORED_KINDS = {"camera"}          # explicit camera numbers are not graded


def entry_of_url(url: Any) -> str | None:
    """The structure a download URL names, written one way: a lower-case PDB id, or
    ``af-<accession>-f<n>`` for an AlphaFold DB file of any model version. The host and
    the file variant (``1cbs``, ``1cbs_updated``, ``pdb1cbs``, ``.cif``/``.bcif``) do not
    matter."""
    if not isinstance(url, str) or not url.strip():
        return None
    name = url.strip().lower().split("?")[0].split("#")[0].rsplit("/", 1)[-1]
    ident = name.split(".")[0]
    m = re.fullmatch(r"(af-[a-z0-9]+-f\d+)(-model_v\d+)?", ident)
    if m:
        return m.group(1)
    ident = re.sub(r"[_-](updated|full|bcif|cif|assembly\d*|model\d*)$", "", ident)
    m = re.fullmatch(r"pdb([0-9][a-z0-9]{3})", ident)
    return m.group(1) if m else ident or None


def _entry_table(entry: str | None) -> AtomTable | None:
    if not entry or not re.fullmatch(r"[a-z0-9_-]+", entry):
        return None
    from .pdbe_state import _table_for
    return _table_for(entry, load_table)


def _table_extras(table: AtomTable) -> dict[str, Any]:
    """Per-table masks the drawing rules need (cached on the table)."""
    ex = getattr(table, "_drawn_extras", None)
    if ex is None:
        poly = table.static.get("polymer", 0)
        nucleic = table.static.get("nucleic", 0)
        names = table.index("label_atom_id")
        ca = names.get("CA", 0)
        o3 = names.get("O3'", 0) | names.get("O3*", 0)
        trace = poly & ((ca & ~nucleic) | (o3 & nucleic))
        branched = table.static.get("branched", 0)
        elements = table.index("type_symbol")
        ex = {"polymer": poly, "trace": trace, "sugar": branched & ~poly,
              "linked": branched & poly,
              "hydrogen": elements.get("H", 0) | elements.get("D", 0),
              "residues": list(table.index("residue_index").values()),
              "all": (1 << table.n) - 1}
        table._drawn_extras = ex
    return ex


def _grow(table: AtomTable, mask: int) -> int:
    """The mask grown to whole residues."""
    if not mask:
        return 0
    out = 0
    for rm in _table_extras(table)["residues"]:
        if rm & mask:
            out |= rm
    return out


def _opacity(v: Any) -> Any:
    try:
        return round(float(v), 3)
    except (TypeError, ValueError):
        return ("invalid", str(v))


class DrawnStructure:
    """What is drawn of one structure (entry). Atom sets are bitmasks over ``table``
    rows, or frozensets of selector descriptions when ``table`` is None."""

    def __init__(self, entry: str, table: AtomTable | None):
        self.entry = entry
        self.table = table
        self.draws: dict[tuple, Any] = {}        # (type, colour, opacity) -> atoms
        self.kinds: set[tuple] = set()           # non-default structure types that draw
        self.labels: dict[str, Any] = {}         # text -> atoms
        self.tooltips: dict[str, Any] = {}
        self.focus: Any = None                   # union of the focused components
        self.interactions: dict[Any, Any] = {}   # radius -> atoms
        self.other: list[tuple] = []             # nodes with no special handling
        self._classes: list | None = None

    @property
    def none(self) -> Any:
        return 0 if self.table is not None else frozenset()

    def add(self, store: dict, key: Any, atoms: Any) -> None:
        if size(atoms):
            store[key] = store[key] | atoms if key in store else atoms
            self._classes = None

    def classes(self) -> list[tuple[Any, tuple]]:
        if self._classes is None:
            self._classes = partition(self.draws)
        return self._classes

    def drawn_atoms(self) -> Any:
        out = self.none
        for m in self.draws.values():
            out = out | m
        return out

    def residues(self, atoms: Any) -> Any:
        return _grow(self.table, atoms) if self.table is not None else atoms


class DrawnScene:
    def __init__(self) -> None:
        self.structures: dict[str, DrawnStructure] = {}
        self.primitives: list[tuple] = []        # (entry, primitive signature)
        self.background: Any = None
        self.other: list[tuple] = []
        self.unresolved: set[str] = set()        # entries with a selector no table can answer
        self.downloads: set[str] = set()         # entries loaded, drawn or not
        self.notes: list[str] = []

    def draws_anything(self) -> bool:
        return any(st.draws for st in self.structures.values())

    def entries(self) -> set[str]:
        return set(self.structures) | self.downloads


def _structure_kind(params: dict) -> tuple:
    """The structure node's type, as a comparable fact (``("model", 0)`` is the default)."""
    t = params.get("type", "model")
    mi = params.get("model_index") or 0
    if t == "model":
        return ("model", mi)
    if t == "assembly":
        asm = params.get("assembly_id")
        return ("assembly", str(asm) if asm is not None else "1", mi)
    rest = tuple(sorted((k, json.dumps(v, sort_keys=True)) for k, v in params.items()
                        if k not in ("type", "model_index", "block_header", "block_index")))
    return (str(t), mi) + rest


def _freeze_params(v: Any) -> Any:
    if isinstance(v, dict):
        return tuple(sorted((str(k), _freeze_params(x)) for k, x in v.items() if x is not None))
    if isinstance(v, list):
        return tuple(_freeze_params(x) for x in v)
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _symbolic(selector: Any) -> frozenset:
    """A selector as its own description (used when no atom table can resolve it)."""
    if isinstance(selector, str):
        return frozenset([f"static:{selector}"])
    return frozenset(str(_selector_signature(e)) for e in
                     (selector if isinstance(selector, list) else [selector]))


def resolve_scene(tree: Any, symbolic: set[str] | frozenset = frozenset(),
                  rename: dict[str, str] | None = None) -> DrawnScene | None:
    """Resolve a scene tree to its drawn state, or None if it is not a scene tree.

    ``symbolic``: entries to resolve without their atom table (both sides of a
    comparison must be resolved the same way). ``rename``: entry id -> the entry to
    resolve it on instead (a reference re-pointed at another accepted structure).
    """
    root = extract_root(tree)
    if root is None:
        return None
    scene = DrawnScene()
    rename = rename or {}

    def kids(node: dict) -> list[dict]:
        c = node.get("children")
        return [x for x in c if isinstance(x, dict)] if isinstance(c, list) else []

    def params_of(node: dict) -> dict:
        p = node.get("params")
        return p if isinstance(p, dict) else {}

    def custom_of(node: dict) -> dict:
        c = node.get("custom")
        return c if isinstance(c, dict) else {}

    def structure_for(entry: str | None, usable: bool) -> DrawnStructure:
        entry = rename.get(entry, entry) if entry else "?"
        st = scene.structures.get(entry)
        if st is None:
            table = None if (entry in symbolic or not usable) else _entry_table(entry)
            if table is None:
                scene.unresolved.add(entry)
            st = scene.structures[entry] = DrawnStructure(entry, table)
        return st

    def select(st: DrawnStructure, selector: Any) -> Any:
        if st.table is None:
            return _symbolic(selector)
        m = st.table.selector(selector)
        if m is None:                    # instance_id / operator_name: not answerable
            scene.unresolved.add(st.entry)
            return 0
        return m

    def walk(node: dict, entry: str | None, usable: bool) -> None:
        kind = node.get("kind")
        p = params_of(node)
        if kind == "download":
            entry = entry_of_url(p.get("url"))
            if entry:
                scene.downloads.add(rename.get(entry, entry))
            name = str(p.get("url", "")).lower().split("?")[0].rsplit("/", 1)[-1]
            usable = not ("." in name and not re.search(r"\.(cif|mmcif|bcif)(\.gz)?$", name))
        elif kind == "parse":
            if p.get("format") not in (None, "mmcif", "bcif"):
                usable = False           # e.g. PDB format: Mol* derives label_* differently
        elif kind == "structure":
            structure(node, structure_for(entry, usable))
            return
        elif kind == "canvas":
            if "background_color" in p:
                scene.background = mvs_color(p["background_color"])
        elif kind == "primitives":
            primitives(node, None)
            return
        elif kind not in ("root", None) and kind not in _IGNORED_KINDS:
            scene.other.append((kind, _freeze_params(p)))
        for c in kids(node):
            walk(c, entry, usable)

    def primitives(node: dict, st: DrawnStructure | None) -> None:
        for c in kids(node):
            if c.get("kind") == "primitive":
                sig = _param_signature("primitive", params_of(c), None,
                                       st.table if st is not None else None)
                scene.primitives.append((st.entry if st is not None else None, sig))
            else:
                scene.other.append((c.get("kind"), _freeze_params(params_of(c))))

    def structure(node: dict, st: DrawnStructure) -> None:
        kind = _structure_kind(params_of(node))
        used = False
        for c in kids(node):
            ck = c.get("kind")
            if ck == "component":
                component(c, st)
                used = True
            elif ck == "primitives":
                primitives(c, st)
                used = True
            elif ck not in _IGNORED_KINDS:
                st.other.append((ck, _freeze_params(params_of(c))))
                used = True
        if used and kind != ("model", 0):
            st.kinds.add(kind)

    def component(node: dict, st: DrawnStructure) -> None:
        p = params_of(node)
        atoms = select(st, p.get("selector", "all"))
        flag = _interactions_flag(custom_of(node))
        if flag:
            st.add(st.interactions, flag[1], atoms)
        for c in kids(node):
            ck = c.get("kind")
            cp = params_of(c)
            if ck == "representation":
                representation(c, st, atoms)
            elif ck == "label":
                st.add(st.labels, " ".join(str(cp.get("text", "")).split()).casefold(), atoms)
            elif ck == "tooltip":
                st.add(st.tooltips, " ".join(str(cp.get("text", "")).split()).casefold(), atoms)
            elif ck == "focus":
                if size(atoms):
                    st.focus = atoms if st.focus is None else st.focus | atoms
            elif ck not in _IGNORED_KINDS:
                st.other.append((ck, _freeze_params(cp), _canon_atoms(atoms)))

    def representation(node: dict, st: DrawnStructure, atoms: Any) -> None:
        p = params_of(node)
        rtype = p.get("type")
        layers: list[tuple[Any, Any]] = []       # (selector or None, colour token)
        opacity: Any = 1.0
        for c in kids(node):
            ck, cp, cc = c.get("kind"), params_of(c), custom_of(c)
            if ck == "color":
                if cc.get("molstar_color_theme_name"):
                    token: Any = ("theme", str(cc["molstar_color_theme_name"]))
                elif cc.get("molstar_use_default_coloring"):
                    token = ("theme", "default")
                else:
                    token = mvs_color(cp.get("color"))
                layers.append((cp.get("selector"), token))
            elif ck in ("color_from_uri", "color_from_source"):
                layers.append((None, ("annotation", ck, _freeze_params(cp))))
            elif ck == "opacity":
                opacity = _opacity(cp.get("opacity", 1.0))
            elif ck not in _IGNORED_KINDS:
                st.other.append((ck, _freeze_params(cp), _canon_atoms(atoms)))
        if not size(atoms):
            return
        if st.table is None:
            if not isinstance(rtype, str):
                rtype = f"invalid:{rtype!r}"
            if any(sel is not None and sel != "all" for sel, _ in layers):
                colour: Any = ("layers", tuple((_canon_atoms(_symbolic(sel)) if sel is not None
                                                else "all", tok) for sel, tok in layers))
            else:
                colour = layers[-1][1] if layers else _drawn.WHITE
            st.add(st.draws, (rtype, colour, opacity), atoms)
            return
        t = st.table
        ex = _table_extras(t)
        actual, level, drawn_atoms = _what_is_drawn(t, rtype, atoms)
        if p.get("ignore_hydrogens") and level == "atom":
            drawn_atoms &= ~ex["hydrogen"]
        if not drawn_atoms:
            return
        # the unit a colour is decided on: the atom itself, or the residue's trace atom
        if level == "trace":
            units = drawn_atoms & ex["trace"] & atoms
        elif level == "residue":
            units = drawn_atoms
        else:
            units = drawn_atoms
        left = units
        regions: list[tuple[int, Any]] = []
        for sel, token in reversed(layers):      # the last layer covering a unit wins
            covered = ex["all"] if sel is None else (select(st, sel) or 0)
            if level == "residue":
                covered = _grow(t, covered)
            hit = left & covered
            if hit:
                regions.append((hit, token))
                left &= ~hit
        if left:
            regions.append((left, _drawn.WHITE))
        for mask, token in regions:
            if level == "trace":
                mask = _grow(t, mask) & drawn_atoms
            st.add(st.draws, (actual, token, opacity), mask)

    walk(root, None, True)
    return scene


def _canon_atoms(atoms: Any) -> Any:
    return atoms if isinstance(atoms, int) else tuple(sorted(atoms))


def _what_is_drawn(table: AtomTable, rtype: Any, atoms: int) -> tuple[str, str, int]:
    """(type really drawn, colour level, atoms drawn) for a representation type on a
    component, following Mol* 5.9.0 (see the notes at the top of this section)."""
    ex = _table_extras(table)
    if not isinstance(rtype, str) or rtype not in REPRESENTATION_TYPES:
        return (f"invalid:{rtype!r}", "atom", atoms)   # Mol* rejects the scene
    if rtype == "carbohydrate":
        if not ex["sugar"]:                      # no sugars in the model: not applicable
            rtype = "cartoon"
        else:
            sugars = atoms & ex["sugar"]
            if not sugars:
                return ("carbohydrate", "residue", 0)
            return ("carbohydrate", "residue",
                    _grow(table, sugars) | _grow(table, atoms & ex["linked"]))
    if rtype in RIBBON_TYPES:
        if not atoms & ex["polymer"]:            # not applicable: Mol* falls back
            return ("ball_and_stick", "atom", atoms)
        return (rtype, "trace", _grow(table, atoms & ex["trace"]) & ex["polymer"])
    return (rtype, "atom", atoms)


# --- comparing two drawn states ---------------------------------------------------

def _reconcile_themes(ref: DrawnStructure, pred: DrawnStructure) -> dict[tuple, Any]:
    """The answer's draws, with explicit per-group colours rewritten to a categorical
    theme where the reference used that theme.

    A theme has no fixed colours, so "colour by chain" (the reference's ``chain-id``
    theme) is matched by an answer that gives every chain one colour of its own. Only
    this direction: explicit colours in the reference are matched by those colours.
    """
    draws = dict(pred.draws)
    if ref.table is None or pred.table is None:
        return draws
    t = ref.table
    for (rtype, colour, opacity), mask in ref.draws.items():
        if not (isinstance(colour, tuple) and len(colour) == 2 and colour[0] == "theme"
                and colour[1] in PARTITION_THEMES):
            continue
        groups = [gm & mask for gm in t.index(PARTITION_THEMES[colour[1]]).values() if gm & mask]
        chosen: list[tuple[tuple, int]] = []
        ok = True
        for g in groups:
            hits = [(d, m & g) for d, m in draws.items()
                    if d[0] == rtype and m & g and _drawn._is_rgb(d[1])
                    and _drawn.draw_eq((rtype, d[1], opacity), d)]
            if len(hits) != 1 or hits[0][1] != g:
                ok = False
                break
            chosen.append((hits[0][0], g))
        if not ok:
            continue
        cols = [d[1] for d, _ in chosen]
        if any(color_eq(a, b) for i, a in enumerate(cols) for b in cols[i + 1:]):
            continue                              # two groups share a colour: not "by chain"
        for d, g in chosen:
            draws[d] = draws[d] & ~g
            key = (rtype, colour, opacity)
            draws[key] = draws.get(key, 0) | g
        draws = {d: m for d, m in draws.items() if m}
    return draws


def _share(mine: Any, theirs: Any) -> float:
    n = size(mine)
    return size(mine & theirs) / n if n else 0.0


def _focus_score(st: DrawnStructure, other: DrawnStructure | None) -> float:
    """Overlap of two focus targets, as whole residues. A scene with no focus node
    frames everything it draws, so (unless every focus is graded) that is its target."""
    if other is None:
        return 0.0
    theirs = other.focus
    if theirs is None:
        if _drawn.GRADE_UNREQUESTED_FOCUS:
            return 0.0
        theirs = other.drawn_atoms()         # the default camera frames what is drawn
    return jaccard(st.residues(st.focus), other.residues(theirs))


def _side(mine: DrawnScene, theirs: DrawnScene, their_classes: dict[str, list],
          my_classes: dict[str, list], is_reference: bool) -> tuple[float, float, list]:
    """Total credit, number of facts, and the trace, for one direction of a comparison.
    ``is_reference``: ``mine`` is the reference (a focus the reference lacks is not a
    fact of the answer; see ``drawn.GRADE_UNREQUESTED_FOCUS``)."""
    got = total = 0.0
    trace: list[dict] = []

    def fact(name: str, score: float, **more: Any) -> None:
        nonlocal got, total
        total += 1
        got += score
        trace.append({"fact": name, **more, "score": round(score, 3)})

    for entry, st in mine.structures.items():
        other = theirs.structures.get(entry)
        for mask, look in my_classes[entry]:
            fact("display", class_score(mask, look, their_classes.get(entry, [])),
                 value=_drawn.show_look(look), atoms=size(mask), structure=entry)
        for kind in sorted(st.kinds, key=repr):
            fact("structure", float(other is not None and kind in other.kinds),
                 value=_drawn.show(kind), structure=entry)
        for name, store in (("label", "labels"), ("tooltip", "tooltips"),
                            ("interactions", "interactions")):
            for key, atoms in getattr(st, store).items():
                theirs_atoms = getattr(other, store).get(key) if other is not None else None
                fact(name, _share(atoms, theirs_atoms) if theirs_atoms is not None else 0.0,
                     value=key, atoms=size(atoms), structure=entry)
        if st.focus is not None and (is_reference or _drawn.GRADE_UNREQUESTED_FOCUS
                                     or (other is not None and other.focus is not None)):
            fact("focus", _focus_score(st, other), atoms=size(st.focus), structure=entry)
        left = list(other.other) if other is not None else []
        for item in st.other:
            hit = item in left
            if hit:
                left.remove(item)
            fact(f"node:{item[0]}", float(hit), structure=entry)
    left_p = list(theirs.primitives)
    for entry, sig in mine.primitives:
        hit = next((x for x in left_p if x[0] == entry and _primitives_match(sig, x[1])), None)
        if hit is not None:
            left_p.remove(hit)
        fact("primitive", float(hit is not None), value=sig[1], structure=entry)
    if mine.background is not None and not color_eq(mine.background, DEFAULT_BACKGROUND):
        theirs_bg = theirs.background if theirs.background is not None else DEFAULT_BACKGROUND
        fact("canvas:background", float(color_eq(mine.background, theirs_bg)))
    left_o = list(theirs.other)
    for item in mine.other:
        hit = item in left_o
        if hit:
            left_o.remove(item)
        fact(f"node:{item[0]}", float(hit))
    return got, total, trace


def _target_atoms(target: Any, st: DrawnStructure) -> Any:
    """The atoms a task's ``target`` names on one structure (see GRADING.md)."""
    if not isinstance(target, dict):
        return None
    if target.get("entry") and str(target["entry"]).lower() != st.entry:
        return st.none
    out = st.none
    if "selector" in target:
        out = out | (st.table.selector(target["selector"]) or 0 if st.table is not None
                     else _symbolic(target["selector"]))
    if "data" in target and st.table is not None:
        from .pdbe_state import resolve_param
        for prm in target["data"] if isinstance(target["data"], list) else []:
            if isinstance(prm, dict):
                try:
                    out |= resolve_param(st.table, prm, st.entry)
                except NotImplementedError:
                    pass
    return out


def compare_scenes(ref: DrawnScene, pred: DrawnScene, target: Any = None) -> dict[str, Any]:
    """Precision, recall, F1, success and the target score of ``pred`` against ``ref``."""
    structure = [sorted(ref.entries()), sorted(pred.entries())]
    shared = ref.entries() & pred.entries()
    base = {"same_structure": bool(ref.entries()) and ref.entries() == pred.entries(),
            "structure": structure}
    if not shared:
        return _drawn.zero(**base, note="the answer loads none of the reference's structures")
    if ref.draws_anything() and not pred.draws_anything():
        return _drawn.zero(**base, note="the answer draws nothing")

    ref_classes = {e: st.classes() for e, st in ref.structures.items()}
    pred_draws = {e: (_reconcile_themes(ref.structures[e], st) if e in ref.structures
                      else st.draws) for e, st in pred.structures.items()}
    pred_classes = {e: partition(d) for e, d in pred_draws.items()}

    r_got, r_total, r_trace = _side(ref, pred, pred_classes, ref_classes, True)
    p_got, p_total, p_trace = _side(pred, ref, ref_classes, pred_classes, False)
    if not r_total and not p_total:
        precision = recall = 1.0             # nothing was asked for and nothing given
    else:
        recall = r_got / r_total if r_total else 0.0
        precision = p_got / p_total if p_total else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    success = bool(base["same_structure"] and precision > 1 - 1e-9 and recall > 1 - 1e-9)

    # the target score
    parts: list[dict] = []
    for entry, st in ref.structures.items():
        other = pred.structures.get(entry)
        t_atoms = _target_atoms(target, st)
        whole = t_atoms is None
        if whole:
            t_atoms = st.drawn_atoms()
        parts += _drawn.target_display(st.draws, pred_draws.get(entry, {}), t_atoms)
        wanted = set(target.get("facts") or []) if isinstance(target, dict) else set()
        for name, store in (("label", "labels"), ("tooltip", "tooltips"),
                            ("interactions", "interactions")):
            for key, atoms in getattr(st, store).items():
                if whole or size(atoms & t_atoms) or name in wanted:
                    theirs = getattr(other, store).get(key) if other is not None else None
                    sc = jaccard(atoms, theirs) if theirs is not None else 0.0
                    parts.append({"fact": name, "value": key, "recall": sc, "precision": sc})
        if st.focus is not None and (whole or size(st.focus & t_atoms) or "focus" in wanted):
            sc = _focus_score(st, other)
            parts.append({"fact": "focus", "recall": sc, "precision": sc})
    wanted = set(target.get("facts") or []) if isinstance(target, dict) else None
    for row in r_trace:                      # facts that are not about atoms of a class
        name = row["fact"]
        if name in ("display", "label", "tooltip", "interactions", "focus"):
            continue
        if wanted is None or name in wanted or name.split(":")[0] in wanted:
            parts.append({"fact": name, "recall": row["score"], "precision": row["score"]})

    tgt = _drawn.target_summary(parts)
    if not parts and not r_total and not p_total:
        tgt.update(target_precision=1.0, target_recall=1.0, target_f1=1.0)
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
            "success": success, **tgt, **base,
            "n_ref": len(r_trace), "n_pred": len(p_trace),
            "reference_facts": r_trace, "predicted_facts": p_trace}


def _grade_one(reference: Any, predicted: Any, accepted_refs: Iterable[str] | None,
               target: Any) -> dict[str, Any]:
    ref_root = extract_root(reference)
    if ref_root is None:
        return _drawn.zero(error="bad reference tree")
    symbolic: set[str] = set()
    rename: dict[str, str] = {}
    ref = pred = None
    for _ in range(3):                       # settle which entries have to be symbolic
        pred = resolve_scene(predicted, symbolic)
        ref = resolve_scene(reference, symbolic, rename)
        if accepted_refs and not rename and len(ref.entries()) == 1:
            ok = {a.lower() for a in accepted_refs}
            (canonical,) = ref.entries()
            other = sorted(e for e in pred.entries() if e in ok and e != canonical)
            if other and canonical not in pred.entries():
                # a prompt that names a protein has many right entries: grade the
                # reference's drawing on the accepted entry the answer loaded
                rename = {canonical: other[0]}
                continue
        need = (ref.unresolved | pred.unresolved) & (ref.entries() | pred.entries())
        if need <= symbolic:
            break
        symbolic |= need
    out = compare_scenes(ref, pred, target)
    if rename:
        out["accepted_structure"] = next(iter(rename.values()))
    return out


def grade_mvs(reference: Any, predicted: Any,
              accepted_refs: set[str] | list[str] | None = None,
              accepted: list | None = None, target: Any = None) -> dict[str, Any]:
    """Grade a predicted MVS scene against a reference **by what Mol* would draw**.

    Returns ``precision``/``recall``/``f1`` over the facts of the drawn state,
    ``success`` (every fact right and nothing extra), the target score
    (``target_f1``; see ``drawn.target_display``), and a per-fact trace. GRADING.md
    defines every number.

    ``accepted_refs``: other structure ids that count as the reference's (tasks that
    name a protein instead of an id). ``accepted``: further scenes that are equally
    right; the answer is scored against the one it matches best. ``target``: the
    task's ``target`` (the atoms the request is about); without it the target is
    everything the reference draws.
    """
    if extract_root(predicted) is None:
        return _drawn.zero(error="prediction is not an MVS state tree", grader="drawn")
    best: dict[str, Any] | None = None
    for i, ref in enumerate([reference] + list(accepted or [])):
        try:
            res = _grade_one(ref, predicted, accepted_refs, target)
        except Exception as e:  # noqa: BLE001 - an answer must never crash the grader
            res = _drawn.zero(error=f"could not compare scenes ({type(e).__name__}: {e})")
        res["matched_reference"] = i
        if best is None or (res["success"], res["f1"]) > (best["success"], best["f1"]):
            best = res
    best["grader"] = "drawn"
    return best


def grade_mvs_task(task: dict[str, Any], predicted: Any) -> dict[str, Any]:
    """Grade an answer against an MVS task: ``reference_mvs``, plus ``accepted`` scenes,
    ``accepted_ids`` and ``target`` when the task has them. ``outcome`` is ``not_mvs``
    for something that is not a scene tree, else ``unchecked`` (Mol*'s own validation,
    ``render.molstar_issues``, turns that into ``valid`` or ``invalid_mvs``)."""
    res = grade_mvs(task["reference_mvs"], predicted, accepted_refs=task.get("accepted_ids"),
                    accepted=task.get("accepted"), target=task.get("target"))
    res["outcome"] = "not_mvs" if extract_root(predicted) is None else "unchecked"
    return res


def check_mvs_task(task: dict[str, Any]) -> list[str]:
    """Problems that would make an MVS task ungradable (empty list = fine): the
    reference, every accepted scene and the follow-up ``context`` must resolve on a
    frozen atom table, the reference must draw something or state a fact, it must
    succeed against itself, and a ``target`` must name atoms the reference draws."""
    problems: list[str] = []
    scenes = [("reference_mvs", task.get("reference_mvs"))]
    scenes += [(f"accepted[{i}]", s) for i, s in enumerate(task.get("accepted") or [])]
    if "context" in task:
        scenes.append(("context", task["context"]))
    for name, tree in scenes:
        scene = resolve_scene(tree)
        if scene is None:
            problems.append(f"{name}: not an MVS scene tree")
            continue
        if not scene.structures:
            problems.append(f"{name}: loads no structure")
        if name == "reference_mvs" and isinstance(task.get("target"), dict):
            if not any(size(_target_atoms(task["target"], st) or st.none)
                       for st in scene.structures.values()):
                problems.append("target: selects no atoms of the reference's structure")
        for entry, st in scene.structures.items():
            if st.table is None:
                problems.append(f"{name}: no frozen atom table for {entry!r}")
        if scene.unresolved - {e for e, st in scene.structures.items() if st.table is None}:
            problems.append(f"{name}: a selector cannot be resolved on the atom table")
        if name != "context" and not scene.draws_anything() and not scene.primitives:
            problems.append(f"{name}: draws nothing")
        if name != "context":
            for bad in _empty_components(tree):
                problems.append(f"{name}: selector selects no atoms: {bad}")
            g = grade_mvs(tree, tree, target=task.get("target"))
            if not g["success"]:
                problems.append(f"{name}: does not succeed against itself")
            if name == "reference_mvs" and g["target_f1"] != 1.0:
                problems.append("target: the reference does not score 1 on its own target "
                                "(does the target name atoms the reference draws?)")
    return problems


def _empty_components(tree: Any) -> list[str]:
    out: list[str] = []

    def walk(node: dict, entry: str | None) -> None:
        p = node.get("params") if isinstance(node.get("params"), dict) else {}
        if node.get("kind") == "download":
            entry = entry_of_url(p.get("url"))
        if node.get("kind") in ("component", "color") and "selector" in p:
            table = _entry_table(entry)
            if table is not None and table.selector(p["selector"]) == 0:
                out.append(json.dumps(p["selector"], sort_keys=True))
        for c in node.get("children") or []:
            if isinstance(c, dict):
                walk(c, entry)

    root = extract_root(tree)
    if root is not None:
        walk(root, None)
    return out
