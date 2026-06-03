"""
Escalating C1 grader — tree-match → visual diff → VLM judge.

Each tier is more expensive than the last, so we only escalate when the cheaper
tier is inconclusive:

  T0  tree-match (free)        F1 >= tree_threshold        -> "correct"
  T1  visual diff (cheap)      sim >= visual_threshold     -> "rendering-equivalent"
  T2  VLM judge (expensive)    semantic verdict on images  -> "vlm:same"/"vlm:different"

This rescues semantically-equivalent trees that strict tree-matching under-scores
(e.g. `all` vs `polymer`), and concentrates any human review on the genuinely
ambiguous cases that reach T2.

`render` is a callable (tree -> png path), `vlm` is a callable
(ref_png, pred_png, prompt -> {label, score, reason}); both optional, so the
function degrades gracefully to whatever tiers are wired.
"""

from __future__ import annotations

import tempfile
import pathlib
from typing import Any, Callable

from .mvs import grade_mvs
from .visual import image_similarity


def escalating_grade(
    reference_tree: dict,
    predicted_tree: Any,
    *,
    prompt: str | None = None,
    render: Callable[[dict, str], Any] | None = None,
    vlm: Callable[..., dict] | None = None,
    tree_threshold: float = 0.999,
    visual_threshold: float = 0.97,
    workdir: str | pathlib.Path | None = None,
) -> dict[str, Any]:
    g = grade_mvs(reference_tree, predicted_tree)
    out: dict[str, Any] = {"tree_f1": g["f1"], "tier": "tree"}

    # T0 — tree match is conclusive (identical / normalised-equivalent).
    if g["f1"] >= tree_threshold:
        return {**out, "decision": "correct"}
    # A prediction that doesn't even parse can't be rendered — stop at the tree tier.
    if render is None or g.get("error"):
        return {**out, "decision": "tree-only", "note": g.get("error")}

    # T1 — visual diff.
    wd = pathlib.Path(workdir or tempfile.mkdtemp(prefix="molbench_esc_"))
    wd.mkdir(parents=True, exist_ok=True)
    ref_png, pred_png = wd / "ref.png", wd / "pred.png"
    try:
        render(reference_tree, str(ref_png))
        render(predicted_tree, str(pred_png))
    except Exception as e:  # noqa: BLE001 - a render failure is itself informative
        return {**out, "decision": "render-failed", "note": str(e)}
    sim = image_similarity(ref_png, pred_png)
    out.update(tier="visual", visual_sim=round(sim, 4),
               ref_png=str(ref_png), pred_png=str(pred_png))
    if sim >= visual_threshold:
        return {**out, "decision": "rendering-equivalent"}

    # T2 — VLM judge on the image pair.
    if vlm is None:
        return {**out, "decision": "visually-different"}
    verdict = vlm(str(ref_png), str(pred_png), prompt)
    return {**out, "tier": "vlm", "vlm": verdict,
            "decision": "vlm:" + str(verdict.get("label", "?"))}
