"""
Grading: the one entry point, and the API-calling track.

``grade_task(task, answer)`` grades one parsed answer against one task on either
track and returns the same keys for both (``drawn.RESULT_KEYS``): F1, task success, the
target score and the outcome class. MVS tasks are graded by ``mvs.grade_mvs`` (the drawn
state of a scene tree), API tasks by ``pdbe_state.grade_state`` (the final state of the
viewer after the calls are replayed with pdbe-molstar 3.3.2's semantics). GRADING.md is
the plain-language definition of every score. ``check_task(task)`` says whether a task
can be graded at all.

``grade(reference, predicted)`` is the API track's grader on its own. The older
**sequence** grader is kept as ``grade_sequence`` (also ``grade(..., mode="sequence")``)
for comparison with the July 2026 numbers. It is also what ``grade`` falls back to when
the reference loads no structure the state grader can resolve atoms on (no atom table);
the result's ``grader`` key says which one ran, and ``check_task`` reports such a task.

Sequence grader — design notes
------------------------------
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
    """How well two matched selections agree on *styling*: colour, representation,
    side-chain visibility, and tooltip text. Each attribute is only scored when at
    least one side asks for it, so a task that requires (say) a specific tooltip
    string or shown side chains is graded on it rather than getting it for free."""
    checks: list[bool] = []
    if "color" in a or "color" in b:
        checks.append(_color_eq(a.get("color"), b.get("color")))
    if "representation" in a or "representation" in b:
        checks.append(a.get("representation") == b.get("representation"))
    if "sideChain" in a or "sideChain" in b:
        checks.append(bool(a.get("sideChain")) == bool(b.get("sideChain")))
    if "tooltip" in a or "tooltip" in b:
        checks.append(_text_eq(a.get("tooltip"), b.get("tooltip")))
    if not checks:
        return 1.0
    return sum(checks) / len(checks)


def _text_eq(a: Any, b: Any) -> bool:
    """Whitespace- and case-insensitive text match (for tooltip labels)."""
    if isinstance(a, str) and isinstance(b, str):
        return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()
    return a == b


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
        id_match = (ref.get("molecule_id") is not None
                    and _norm_id(ref.get("molecule_id")) == _norm_id(pred.get("molecule_id")))
        if not id_match:
            return 0.6 if (ref.get("custom_data") and pred.get("custom_data")) else 0.0
        # Right structure. If the reference asked for load modifiers (a specific
        # biological assembly, the AlphaFold model, a preset), score whether the
        # prediction requested them too — otherwise "load 6vxx" would earn full
        # marks on a task whose whole point is "load assembly 1 of 6vxx".
        mods: list[bool] = []
        if ref.get("assembly_id") is not None:
            mods.append(str(ref.get("assembly_id")) == str(pred.get("assembly_id")))
        if ref.get("preset") is not None:
            mods.append(ref.get("preset") == pred.get("preset"))
        if ref.get("alphafold"):
            mods.append(bool(pred.get("alphafold")))
        if not mods:
            return 1.0
        # 70% for the right structure, 30% for the requested load modifiers.
        return 0.7 + 0.3 * (sum(mods) / len(mods))

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

def grade(reference: list[dict], predicted: Any, accepted: list[list] | None = None,
          mode: str = "state", target: Any = None) -> dict[str, Any]:
    """Grade a predicted action list against the reference.

    ``mode="state"`` (default): by final viewer state; the result has precision,
    recall, f1, ``success``, the target score and the facts compared. ``accepted`` lists
    further action lists that are equally right. ``mode="sequence"``: the legacy
    step-matching grader. A reference the state grader cannot place on a structure is
    graded by sequence (the result's ``grader`` key says so; ``check_task`` reports such
    a task as a problem).
    """
    if mode not in ("state", "sequence"):
        raise ValueError(f"unknown grading mode {mode!r}")
    if mode == "state":
        from . import pdbe_state
        if pdbe_state.gradable(reference):
            return pdbe_state.grade_state(reference, predicted, accepted=accepted, target=target)
    from . import drawn
    result = {**drawn.zero(), **grade_sequence(reference, predicted)}
    result["grader"] = "sequence"
    result["success"] = result["f1"] == 1.0
    # the sequence grader knows no atoms: its target score is its F1
    result.update(target_precision=result["precision"], target_recall=result["recall"],
                  target_f1=result["f1"])
    return result


def is_mvs_task(task: dict[str, Any]) -> bool:
    return task.get("category") == "mvs" or "reference_mvs" in task


def grade_task(task: dict[str, Any], predicted: Any, mode: str = "state") -> dict[str, Any]:
    """Grade one answer against one task, on either track. **The one entry point.**

    ``predicted`` is the parsed answer: an MVS scene tree for an MVS task
    (``reference_mvs``), a list of actions for an API task (``reference``). The answer is
    scored against the task's reference and every ``accepted`` alternative, and the best
    is returned. For a follow-up task the answer is the complete final scene / call list:
    only that final state is graded (the task's ``context`` is not).

    The result has the same keys on both tracks (``drawn.RESULT_KEYS``), among them:

    * ``f1``, ``precision``, ``recall`` - graded score over the facts of the final state;
    * ``success`` - the final state is exactly right (nothing missing, nothing extra);
    * ``target_f1`` (and ``target_precision``, ``target_recall``) - the same, for the
      atoms the request is about (``task["target"]``; without one, everything the
      reference draws or changes), ignoring unrequested context;
    * ``outcome`` - ``not_mvs`` / ``unchecked`` (MVS; Mol*'s validation later makes
      ``unchecked`` into ``valid`` or ``invalid_mvs``) or ``valid`` / ``invalid_api``
      (API). ``invalid_json`` is decided earlier, by whoever parses the raw reply.

    GRADING.md defines each of them in full.
    """
    if is_mvs_task(task):
        from . import mvs
        return mvs.grade_mvs_task(task, predicted)
    result = grade(task["reference"], predicted, accepted=task.get("accepted"), mode=mode,
                   target=task.get("target"))
    from . import schema
    try:
        schema_errors = schema.validate_actions(predicted)
    except Exception as e:  # noqa: BLE001 - arbitrary model output
        schema_errors = [f"schema check failed: {type(e).__name__}: {e}"]
    result["schema_errors"] = schema_errors
    result["outcome"] = "invalid_api" if result.get("error") or schema_errors else "valid"
    return result


def check_task(task: dict[str, Any]) -> list[str]:
    """Problems that would make a task ungradable or its scores misleading (empty list
    = fine). Task loaders and generators should call this on every task."""
    if is_mvs_task(task):
        from . import mvs
        return mvs.check_mvs_task(task)
    from . import pdbe_state
    problems: list[str] = []
    lists = [("reference", task.get("reference"))]
    lists += [(f"accepted[{i}]", a) for i, a in enumerate(task.get("accepted") or [])]
    if "context" in task:
        lists.append(("context", task["context"]))
    for name, actions in lists:
        if not isinstance(actions, list):
            problems.append(f"{name}: not a list of actions")
            continue
        state = pdbe_state.replay(actions)
        if not state.loaded:
            problems.append(f"{name}: loads no structure")
            continue
        if not pdbe_state.gradable(actions):
            problems.append(f"{name}: no frozen atom table for {state.entry!r} "
                            "(it would be graded by the legacy sequence grader)")
        if state.unresolved:
            problems.append(f"{name}: unresolved selection(s): {state.unresolved[:3]}")
        if name == "context":
            continue
        g = grade(actions, actions, target=task.get("target"))
        if not g["success"]:
            problems.append(f"{name}: does not succeed against itself")
        if name == "reference" and g["target_f1"] != 1.0:
            problems.append("target: the reference does not score 1 on its own target "
                            "(does the target name atoms the reference changes?)")
    return problems


def grade_sequence(reference: list[dict], predicted: Any) -> dict[str, Any]:
    """Legacy grader: greedy matching of reference and predicted actions.

    Returns a dict with precision, recall, f1, and a per-reference-op trace. Known
    weaknesses (the reason it is no longer the default): it ignores order, pools label
    and author numbering and chain ids, and never looks at the structure.
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
