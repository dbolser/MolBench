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
        return ("color", _color_signature(params["color"]))
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
        return ("sel", tuple(sorted(map(repr, x.sigs))), x.atoms)
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


def grade_mvs(reference: Any, predicted: Any,
              accepted_refs: set[str] | list[str] | None = None) -> dict[str, Any]:
    """Grade a predicted MVS scene against a reference. Returns precision/recall/f1.

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
        validate_state_tree(obj if obj.get("kind") in ("single", "multiple") else {"kind": "single", "root": root})
        return []
    except ImportError:
        return []  # library absent: skip deep validation, tree shape already checked
    except Exception as e:  # noqa: BLE001 - surface validation message to the report
        return [f"MVS validation: {e}"]
