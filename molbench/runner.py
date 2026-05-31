"""
The harness: load tasks, run each model, grade, write a scorecard.

Run with zero credentials::

    python -m molbench.runner --models baseline

Add a real model (needs the matching SDK + API key)::

    python -m molbench.runner --models baseline anthropic:claude-opus-4-8

Everything is plain stdlib so the baseline path has no install step.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

from . import grader as grader_mod
from . import schema
from .models import build_model
from .vlm_grader import StubVLMJudge

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
TASKS_DIR = REPO / "tasks"
RESULTS_DIR = REPO / "results"
PROMPT_TEMPLATE = REPO / "prompts" / "system_api.md"
API_REFERENCE = ROOT / "api_reference.md"


# --- task loading -----------------------------------------------------------------

def load_tasks(categories: list[str] | None) -> list[dict[str, Any]]:
    tasks = []
    for path in sorted(TASKS_DIR.rglob("*.json")):
        task = json.loads(path.read_text())
        task["_path"] = str(path.relative_to(REPO))
        if categories and task.get("category") not in categories:
            continue
        tasks.append(task)
    return tasks


def build_system_prompt() -> str:
    """Assemble the model context: instructions + vendored API ref + JSON schema."""
    template = PROMPT_TEMPLATE.read_text()
    api_ref = API_REFERENCE.read_text()
    json_schema = json.dumps(schema.build_json_schema(), indent=2)
    return (template
            .replace("{{API_REFERENCE}}", api_ref)
            .replace("{{JSON_SCHEMA}}", json_schema))


# --- prediction parsing -----------------------------------------------------------

def extract_actions(raw: str) -> tuple[Any, str | None]:
    """Pull a JSON array of actions out of a model's raw text. Returns (obj, error)."""
    raw = raw.strip()
    # Strip ```json fences if present.
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
    except ValueError:
        return None, "no JSON array found in output"
    try:
        return json.loads(raw[start:end]), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


# --- running ----------------------------------------------------------------------

def run_api_task(model, system: str, task: dict) -> dict[str, Any]:
    raw = model.generate(system, task["prompt"])
    actions, err = extract_actions(raw)
    if err:
        return {"f1": 0.0, "precision": 0.0, "recall": 0.0,
                "error": err, "raw": raw[:500]}
    schema_errors = schema.validate_actions(actions)
    result = grader_mod.grade(task["reference"], actions)
    result["schema_errors"] = schema_errors
    result["predicted"] = actions
    return result


def run(models: list[str], categories: list[str] | None) -> dict[str, Any]:
    tasks = load_tasks(categories)
    if not tasks:
        sys.exit("no tasks matched; check tasks/ and --categories")
    system = build_system_prompt()
    vlm = StubVLMJudge()

    report: dict[str, Any] = {"models": {}, "n_tasks": len(tasks)}
    for spec in models:
        model = build_model(spec)
        per_task = []
        for task in tasks:
            if task.get("category") == "visual_rubric":
                # Component 2: we still ask the model for a plan (useful signal),
                # but scoring needs a render + VLM judge (stubbed here).
                raw = model.generate(system, task["prompt"])
                actions, err = extract_actions(raw)
                judged = vlm.score(image_path="", rubric=task.get("rubric", []),
                                   prompt=task["prompt"])
                per_task.append({
                    "id": task["id"], "category": "visual_rubric",
                    "plan_parsed": err is None, "vlm": judged,
                    "predicted": actions,
                })
            else:
                res = run_api_task(model, system, task)
                per_task.append({"id": task["id"], "category": "api_calling", **res})

        graded = [t for t in per_task if t["category"] == "api_calling"]
        mean_f1 = sum(t["f1"] for t in graded) / len(graded) if graded else 0.0
        report["models"][model.name] = {
            "spec": spec,
            "mean_f1": round(mean_f1, 4),
            "n_graded": len(graded),
            "tasks": per_task,
        }
    return report


# --- presentation -----------------------------------------------------------------

def print_scorecard(report: dict[str, Any]) -> None:
    print(f"\nMolBench scorecard  ({report['n_tasks']} tasks)\n" + "=" * 48)
    for name, m in report["models"].items():
        print(f"\n{name}   mean F1 = {m['mean_f1']:.3f}  (over {m['n_graded']} API tasks)")
        for t in m["tasks"]:
            if t["category"] == "api_calling":
                flag = "  !" + t["error"] if t.get("error") else ""
                print(f"    {t['id']:<14} f1={t['f1']:.2f}  "
                      f"P={t['precision']:.2f} R={t['recall']:.2f}{flag}")
            else:
                status = t["vlm"]["status"]
                print(f"    {t['id']:<14} [visual] plan_parsed={t['plan_parsed']} vlm={status}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Run the MolBench harness.")
    ap.add_argument("--models", nargs="+", default=["baseline"],
                    help="model specs: baseline | anthropic:<id> | openai:<id>")
    ap.add_argument("--categories", nargs="*", default=None,
                    help="filter tasks, e.g. api_calling visual_rubric")
    ap.add_argument("--out", default=str(RESULTS_DIR / "scorecard.json"))
    args = ap.parse_args(argv)

    report = run(args.models, args.categories)
    RESULTS_DIR.mkdir(exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(report, indent=2))
    print_scorecard(report)
    print(f"\nfull results -> {args.out}")


if __name__ == "__main__":
    main()
