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

import re
from typing import Any, Iterable

# --- selection normalisation (the ComponentExpression sub-language) ---------------
# Treat author/label chain ids as interchangeable, and the various residue-number
# spellings as one "resnum" axis — same tolerance philosophy as the imperative grader.
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
        sigs.append((
            ("chain", str(chain) if chain is not None else None),
            ("resnum", resnum),
            ("range", (beg, end) if (beg is not None or end is not None) else None),
            ("comp", comp),
            ("atom", atom),
        ))
    return tuple(sorted(map(str, sigs)))


def _color_signature(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip().lower().lstrip("#")
        return "grey" if v == "gray" else v   # fold the common spelling split
    return value


def _param_signature(kind: str, params: dict | None) -> Any:
    params = params or {}
    if kind == "component" and "selector" in params:
        return ("selector", _selector_signature(params["selector"]))
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


def flatten_paths(root: dict) -> list[tuple]:
    """Return every root-to-leaf path as a tuple of (kind, param_signature) segments."""
    paths: list[tuple] = []

    def walk(node: dict, prefix: tuple) -> None:
        kind = node.get("kind")
        params = node.get("params")
        # A model may emit a structurally-odd tree (e.g. params as a list, not a
        # dict). Grade it gracefully — treat malformed params as empty — rather
        # than crashing the whole run on one bad node.
        if not isinstance(params, dict):
            params = {}
        children = node.get("children") or []

        # A component selecting N residues via a list selector is equivalent to N
        # single-residue components with the same children. Expand it so that
        # "group residues in one component" and "one component each" score alike.
        if kind == "component" and isinstance(params.get("selector"), list) \
                and len(params["selector"]) > 1:
            variants = [("selector", _selector_signature(e)) for e in params["selector"]]
        else:
            variants = [_param_signature(kind, params)]

        for vsig in variants:
            here = prefix + ((kind, vsig),)
            if not children:
                paths.append(here)
            for child in children:
                if isinstance(child, dict):
                    walk(child, here)

    walk(root, ())
    return paths


# Boilerplate nodes carry little signal (almost every scene parses mmcif into a
# model), so they're down-weighted; the root is structural scaffolding worth 0.
# Everything else (download target, component, representation, color, focus...)
# is the discriminating content and keeps full weight.
_SEG_WEIGHT = {"root": 0.0, "parse": 0.25, "structure": 0.25}


def _path_similarity(p: tuple, q: tuple) -> float:
    """Weighted position-wise segment agreement.

    Earlier this used longest-common-*prefix*, which let an incidental mismatch
    near the root (e.g. a file-variant in the download node) zero out credit for
    a correct representation/colour further down. Position-wise scoring keeps that
    downstream credit; boilerplate nodes are down-weighted so they neither dominate
    nor mask the real differences.
    """
    num = den = 0.0
    for i in range(max(len(p), len(q))):
        a = p[i] if i < len(p) else None
        b = q[i] if i < len(q) else None
        kind = (a or b)[0]
        w = _SEG_WEIGHT.get(kind, 1.0)
        den += w
        if a == b:
            num += w
    return num / den if den else 0.0


# --- grading ----------------------------------------------------------------------

def grade_mvs(reference: Any, predicted: Any) -> dict[str, Any]:
    """Grade a predicted MVS scene against a reference. Returns precision/recall/f1."""
    ref_root, pred_root = extract_root(reference), extract_root(predicted)
    if ref_root is None:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "error": "bad reference tree"}
    if pred_root is None:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0,
                "error": "prediction is not an MVS state tree"}

    ref_paths = flatten_paths(ref_root)
    pred_paths = flatten_paths(pred_root)
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

    def walk(node: dict) -> None:
        nonlocal has_expr
        k = node.get("kind")
        kinds[k] = kinds.get(k, 0) + 1
        params = node.get("params") or {}
        if k == "component" and not isinstance(params.get("selector"), str):
            has_expr = True
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
    if kinds.get("volume") or kinds.get("primitives"):
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
