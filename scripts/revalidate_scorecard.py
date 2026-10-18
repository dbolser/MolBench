#!/usr/bin/env python3
"""
Apply Mol* validation to a scorecard written before ``--validate`` existed.

Gives each MVS task an ``outcome`` (see ``runner.OUTCOMES``): a parse error is
``invalid_json``, a parsed object with no MVS root is ``not_mvs``, a scene Mol*'s
validator rejects is ``invalid_mvs`` (with its messages), and a scene that passed
validation but failed to render during escalation is ``load_failed`` — re-rendered
here on its own first, since older records don't say whether the prediction or the
reference failed. All but ``valid`` score 0. Then recomputes the model aggregates in place. No model calls.

Only single-sample scorecards: with N samples the per-task record keeps just the
best one, so the other samples can't be re-checked.

    python scripts/revalidate_scorecard.py results/r2x2/spec/*.json
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import runner  # noqa: E402


def _sample(t: dict) -> dict:
    s = {k: t[k] for k in ("f1", "precision", "recall", "predicted", "error") if k in t}
    if t.get("error"):
        s["outcome"] = "not_mvs" if "not an MVS" in t["error"] else "invalid_json"
    else:
        s["outcome"] = "unchecked"
    return s


def _prediction_render_error(tree: dict) -> str | None:
    """The error if Mol* can't render this scene on its own, else None."""
    import tempfile
    from molbench.render import render_scene
    with tempfile.TemporaryDirectory() as d:
        try:
            render_scene(tree, pathlib.Path(d) / "pred.png")
        except Exception as e:  # noqa: BLE001 - the error is the finding
            return str(e)
    return None


def revalidate(path: pathlib.Path) -> None:
    card = json.loads(path.read_text())
    if card.get("samples", 1) != 1:
        raise SystemExit(f"{path}: {card['samples']} samples per task; only 1 is supported")
    for m in card["models"].values():
        if any(t["category"] != "mvs" for t in m["tasks"]):
            raise SystemExit(f"{path}: MVS-only scorecards (the format stats span all tracks)")
        mvs = m["tasks"]
        samples = {t["id"]: _sample(t) for t in mvs}
        runner.validate_samples(list(samples.values()))
        for t in mvs:
            s = samples[t["id"]]
            esc = t.get("escalation") or {}
            if s["outcome"] == "valid" and esc.get("decision") == "render-failed":
                err = (esc.get("note", "") if esc.get("failed_side") == "prediction"
                       else None if esc.get("failed_side") == "reference"
                       else _prediction_render_error(s["predicted"]))
                if err:
                    runner._invalidate(s, "load_failed", err)
            t.update(runner._aggregate([s]))
        graded = [t for t in m["tasks"] if t["category"] in runner.GRADED_CATEGORIES]
        m["mean_f1"] = round(sum(t["f1"] for t in graded) / len(graded), 4) if graded else 0.0
        m["by_category"] = runner._means_by_category(m["tasks"])
        m["by_skill"] = runner._means_by_skill(m["tasks"])
        m.update(runner._format_stats({i: [s] for i, s in samples.items()}))
    card["meta"]["validate"] = True
    card["meta"]["revalidated"] = "scripts/revalidate_scorecard.py"
    path.write_text(json.dumps(card, indent=2))
    for name, m in card["models"].items():
        print(f"{path.name}: {name} mean_f1={m['mean_f1']} outcomes={m['outcomes']}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        revalidate(pathlib.Path(arg))
