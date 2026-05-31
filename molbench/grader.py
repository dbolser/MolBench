"""
Structured grader for Component 1 (API-calling tasks).

We compare two ordered lists of canonical actions (reference vs. predicted) and
produce a precision / recall / F1 in [0, 1] plus a human-readable trace.

Design notes
------------
* Grading is **field-aware and tolerant**. Exact-string equality would punish a
  model for harmless phrasing differences (e.g. `auth_asym_id` vs `struct_asym_id`
  pointing at the same chain, or selections listed in a different order). So each
  action type has its own similarity function returning a partial score in [0, 1].
* Matching is **greedy bipartite**: build the ref x pred similarity matrix, then
  repeatedly take the highest-scoring unused pair. This rewards getting the right
  set of operations regardless of order, while still penalising extras (precision)
  and omissions (recall).
* Selections are scored with **Jaccard over residue locators**, multiplied by an
  attribute-agreement factor (colour/representation). So "right residues, wrong
  colour" earns partial credit — exactly the gradient you want from a benchmark.
"""

from __future__ import annotations

from typing import Any

Number = float


# --- selection comparison ---------------------------------------------------------

# Treat these chain-id fields as interchangeable when forming a residue's identity:
# a model that says auth_asym_id="A" and one that says struct_asym_id="A" are, for
# grading purposes at this altitude, pointing at the same place.
_CHAIN_FIELDS = ("auth_asym_id", "struct_asym_id")
_RESNUM_FIELDS = ("residue_number", "auth_seq_id", "auth_residue_number")


def _selection_signature(sel: dict[str, Any]) -> tuple:
    """Reduce a selection to a hashable 'where' fingerprint for set comparison."""
    chain = next((str(sel[f]) for f in _CHAIN_FIELDS if sel.get(f) is not None), None)
    resnum = next((sel[f] for f in _RESNUM_FIELDS if sel.get(f) is not None), None)
    rng = None
    if sel.get("start_residue_number") is not None or sel.get("end_residue_number") is not None:
        rng = (sel.get("start_residue_number"), sel.get("end_residue_number"))
    comp = sel.get("label_comp_id")
    comp = comp.upper() if isinstance(comp, str) else comp
    entity = str(sel["entity_id"]) if sel.get("entity_id") is not None else None
    atoms = tuple(sorted(a.upper() for a in sel["atoms"])) if isinstance(sel.get("atoms"), list) else None
    return (chain, resnum, rng, comp, entity, atoms)


def _attr_agreement(a: dict[str, Any], b: dict[str, Any]) -> Number:
    """How well two matched selections agree on *styling* (colour/representation)."""
    checks: list[bool] = []
    if "color" in a or "color" in b:
        checks.append(_color_eq(a.get("color"), b.get("color")))
    if "representation" in a or "representation" in b:
        checks.append(a.get("representation") == b.get("representation"))
    if not checks:
        return 1.0
    return sum(checks) / len(checks)


def _color_eq(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return a == b
    try:
        return all(abs(int(a[k]) - int(b[k])) <= 8 for k in ("r", "g", "b"))
    except (TypeError, KeyError, ValueError):
        return a == b


def _selection_set_similarity(ref: list, pred: list) -> Number:
    """Jaccard over locator signatures, weighted by attribute agreement on overlap."""
    if not isinstance(ref, list) or not isinstance(pred, list):
        return 0.0
    if not ref and not pred:
        return 1.0
    ref_sigs = {_selection_signature(s): s for s in ref if isinstance(s, dict)}
    pred_sigs = {_selection_signature(s): s for s in pred if isinstance(s, dict)}
    inter = ref_sigs.keys() & pred_sigs.keys()
    union = ref_sigs.keys() | pred_sigs.keys()
    if not union:
        return 0.0
    jaccard = len(inter) / len(union)
    if inter:
        attr = sum(_attr_agreement(ref_sigs[k], pred_sigs[k]) for k in inter) / len(inter)
    else:
        attr = 1.0
    # 80% for pointing at the right residues, 20% for styling them right.
    return jaccard * (0.8 + 0.2 * attr)


# --- per-action similarity --------------------------------------------------------

def _norm_id(v: Any) -> Any:
    return v.casefold() if isinstance(v, str) else v


def action_similarity(ref: dict[str, Any], pred: dict[str, Any]) -> Number:
    """Similarity in [0, 1] between two actions; 0 if action types differ."""
    a = ref.get("action")
    if a != pred.get("action"):
        return 0.0

    if a == "load":
        if _norm_id(ref.get("molecule_id")) == _norm_id(pred.get("molecule_id")) \
                and ref.get("molecule_id") is not None:
            return 1.0
        if ref.get("custom_data") and pred.get("custom_data"):
            return 0.6
        return 0.0

    if a == "set_visual_style":
        return 1.0 if ref.get("style") == pred.get("style") else 0.0

    if a == "set_property":
        if ref.get("name") != pred.get("name"):
            return 0.0
        return 1.0 if _values_eq(ref.get("value"), pred.get("value")) else 0.4

    if a in ("color", "focus", "highlight", "tooltips"):
        return _selection_set_similarity(ref.get("data", []), pred.get("data", []))

    if a == "set_color":
        keys = [k for k in ("highlight", "select") if k in ref or k in pred]
        if not keys:
            return 1.0
        return sum(_color_eq(ref.get(k), pred.get(k)) for k in keys) / len(keys)

    if a == "reset":
        keys = [k for k in ("camera", "theme", "highlightColor", "selectColor")
                if k in ref or k in pred]
        if not keys:
            return 1.0
        return sum(bool(ref.get(k)) == bool(pred.get(k)) for k in keys) / len(keys)

    # clear_* and anything else with no fields: matching the action name is enough.
    return 1.0


def _values_eq(a: Any, b: Any) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        return a.casefold().lstrip("#") == b.casefold().lstrip("#")
    return a == b


# --- top-level grading ------------------------------------------------------------

def grade(reference: list[dict], predicted: Any) -> dict[str, Any]:
    """Grade a predicted action list against the reference.

    Returns a dict with precision, recall, f1, and a per-reference-op trace.
    """
    if not isinstance(predicted, list):
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0,
                "error": "prediction is not a list", "matches": []}

    n_ref, n_pred = len(reference), len(predicted)
    if n_ref == 0:
        # Degenerate task: full credit only for an empty prediction.
        f1 = 1.0 if n_pred == 0 else 0.0
        return {"precision": f1, "recall": 1.0, "f1": f1, "matches": []}

    # Build similarity matrix and greedily match highest pairs.
    pairs = []
    for i, r in enumerate(reference):
        for j, p in enumerate(predicted):
            if isinstance(p, dict):
                s = action_similarity(r, p)
                if s > 0:
                    pairs.append((s, i, j))
    pairs.sort(reverse=True)

    used_ref: set[int] = set()
    used_pred: set[int] = set()
    matched_score = 0.0
    trace = []
    for s, i, j in pairs:
        if i in used_ref or j in used_pred:
            continue
        used_ref.add(i)
        used_pred.add(j)
        matched_score += s
        trace.append({"ref_index": i, "pred_index": j, "score": round(s, 3),
                      "action": reference[i].get("action")})

    for i, r in enumerate(reference):
        if i not in used_ref:
            trace.append({"ref_index": i, "pred_index": None, "score": 0.0,
                          "action": r.get("action"), "miss": True})

    precision = matched_score / n_pred if n_pred else 0.0
    recall = matched_score / n_ref
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "n_ref": n_ref,
        "n_pred": n_pred,
        "matches": trace,
    }
