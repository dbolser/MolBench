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
import os
import pathlib
import statistics
import sys
import time
from typing import Any

from . import grader as grader_mod
from . import mvs as mvs_mod
from . import schema
from .models import build_model
from .vlm_grader import StubVLMJudge

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
TASKS_DIR = REPO / "tasks"
RESULTS_DIR = REPO / "results"
PROMPT_API = REPO / "prompts" / "system_api.md"
PROMPT_MVS = REPO / "prompts" / "system_mvs.md"
API_REFERENCE = ROOT / "api_reference.md"
MVS_REFERENCE = ROOT / "mvs_reference.md"

# Categories whose tasks produce a numeric F1 (vs. visual_rubric, which is VLM-judged).
GRADED_CATEGORIES = ("mvs", "api_calling")

# Published list prices in USD per 1,000,000 tokens (input, output), no caching.
# Keyed by a substring of the model id. Update as prices change — cost is just
# tokens x rate, so the token counts in the scorecard stay valid regardless.
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-opus-4": (15.0, 75.0),
    "gpt-4o": (2.5, 10.0),
    # Gemini prices are approximate (they change / vary by tier) — token counts are
    # exact, so cost just rescales if you correct the rate.
    "gemini-3.5-flash": (0.3, 2.5),
    "gemini-2.5-flash": (0.3, 2.5),
    "gemini-2.0-flash": (0.1, 0.4),
}


def price_for(model_id: str) -> tuple[float, float] | None:
    for key, rate in PRICING.items():
        if key in model_id:
            return rate
    return None


def cost_usd(model_id: str, usage: dict[str, int]) -> float | None:
    rate = price_for(model_id)
    if rate is None:
        return None
    inp, out = rate
    return (usage["input_tokens"] * inp + usage["output_tokens"] * out) / 1_000_000


# --- environment ------------------------------------------------------------------

def load_dotenv(path: pathlib.Path = REPO / ".env") -> None:
    """Minimal, dependency-free .env loader.

    Reads KEY=VALUE lines from the repo-root .env (if present). Existing
    environment variables win, so `export FOO=...` still overrides the file.
    Avoids pulling in python-dotenv just to read a handful of API keys.
    """
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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


def build_system_prompts() -> dict[str, str]:
    """One assembled system prompt per task category.

    Each target speaks a different IR, so each gets its own instructions + vendored
    reference: the imperative PDBeMolstar API for 'api_calling', the MolViewSpec
    scene tree for 'mvs' (also used to elicit a plan for 'visual_rubric').
    """
    api_prompt = (PROMPT_API.read_text()
                  .replace("{{API_REFERENCE}}", API_REFERENCE.read_text())
                  .replace("{{JSON_SCHEMA}}", json.dumps(schema.build_json_schema(), indent=2)))
    mvs_prompt = PROMPT_MVS.read_text().replace("{{MVS_REFERENCE}}", MVS_REFERENCE.read_text())
    return {"api_calling": api_prompt, "mvs": mvs_prompt, "visual_rubric": mvs_prompt}


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


def extract_json_object(raw: str) -> tuple[Any, str | None]:
    """Pull a single JSON object (e.g. an MVS state tree) out of model text."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
    except ValueError:
        return None, "no JSON object found in output"
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


def run_mvs_task(model, system: str, task: dict) -> dict[str, Any]:
    raw = model.generate(system, task["prompt"])
    tree, err = extract_json_object(raw)
    if err:
        return {"f1": 0.0, "precision": 0.0, "recall": 0.0,
                "error": err, "raw": raw[:500]}
    result = mvs_mod.grade_mvs(task["reference_mvs"], tree)
    result["schema_errors"] = mvs_mod.validate_mvs(tree)
    result["predicted"] = tree
    return result


def _aggregate(samples: list[dict]) -> dict[str, Any]:
    """Reduce N graded samples of one task to mean/std/min/max + a representative.

    LLMs are stochastic, so a single sample is noisy. We score each task as the
    *mean over N samples* and keep the spread so the report can show mean±std and
    callers can tell a real gap from sampling noise.
    """
    f1s = [s["f1"] for s in samples]
    ps = [s.get("precision", 0.0) for s in samples]
    rs = [s.get("recall", 0.0) for s in samples]
    rep = max(samples, key=lambda s: s["f1"])  # keep the best sample's detail to show
    return {
        "f1": round(statistics.fmean(f1s), 4),
        "f1_std": round(statistics.pstdev(f1s), 4) if len(f1s) > 1 else 0.0,
        "f1_min": round(min(f1s), 4),
        "f1_max": round(max(f1s), 4),
        "precision": round(statistics.fmean(ps), 4),
        "recall": round(statistics.fmean(rs), 4),
        "n_samples": len(samples),
        "samples_f1": [round(x, 4) for x in f1s],
        "predicted": rep.get("predicted"),
        "error": rep.get("error"),
        "schema_errors": rep.get("schema_errors"),
    }


def run(models: list[str], categories: list[str] | None,
        samples: int = 1) -> dict[str, Any]:
    tasks = load_tasks(categories)
    if not tasks:
        sys.exit("no tasks matched; check tasks/ and --categories")
    prompts = build_system_prompts()
    vlm = StubVLMJudge()

    report: dict[str, Any] = {"models": {}, "n_tasks": len(tasks), "samples": samples}
    for spec in models:
        model = build_model(spec)
        per_task = []
        started = time.perf_counter()
        for task in tasks:
            cat = task.get("category")
            system = prompts.get(cat, prompts["mvs"])
            if cat == "visual_rubric":
                # Component 2: we still elicit a plan (useful signal), but scoring
                # needs a render + VLM judge (stubbed here).
                _, err = extract_json_object(model.generate(system, task["prompt"]))
                judged = vlm.score(image_path="", rubric=task.get("rubric", []),
                                   prompt=task["prompt"])
                per_task.append({"id": task["id"], "category": cat,
                                 "plan_parsed": err is None, "vlm": judged})
            elif cat in GRADED_CATEGORIES:
                run_task = run_mvs_task if cat == "mvs" else run_api_task
                got = [run_task(model, system, task) for _ in range(samples)]
                per_task.append({"id": task["id"], "category": cat, **_aggregate(got)})

        wall_seconds = time.perf_counter() - started
        graded = [t for t in per_task if t["category"] in GRADED_CATEGORIES]
        mean_f1 = sum(t["f1"] for t in graded) / len(graded) if graded else 0.0
        by_cat = _means_by_category(per_task)
        calls = model.usage.get("calls", 0)
        report["models"][model.name] = {
            "spec": spec,
            "mean_f1": round(mean_f1, 4),
            "n_graded": len(graded),
            "by_category": by_cat,
            "usage": model.usage,
            "cost_usd": cost_usd(model.name, model.usage),
            "wall_seconds": round(wall_seconds, 2),
            "sec_per_call": round(wall_seconds / calls, 2) if calls else None,
            "tasks": per_task,
        }
    return report


def _means_by_category(per_task: list[dict]) -> dict[str, dict]:
    """Per-category mean F1 + count, so the leaderboard can break scores down."""
    out: dict[str, dict] = {}
    for cat in GRADED_CATEGORIES:
        rows = [t["f1"] for t in per_task if t["category"] == cat]
        if rows:
            out[cat] = {"mean_f1": round(statistics.fmean(rows), 4),
                        "std": round(statistics.pstdev(rows), 4) if len(rows) > 1 else 0.0,
                        "n": len(rows)}
    return out


# --- presentation -----------------------------------------------------------------

def print_scorecard(report: dict[str, Any]) -> None:
    n = report.get("samples", 1)
    print(f"\nMolBench scorecard  ({report['n_tasks']} tasks, {n} sample(s)/task)\n" + "=" * 52)
    for name, m in report["models"].items():
        u = m["usage"]
        cost = m["cost_usd"]
        cost_str = f"${cost:.4f}" if cost is not None else "n/a (no price set)"
        cat_str = "  ".join(f"{c}={d['mean_f1']:.3f}({d['n']})"
                            for c, d in m.get("by_category", {}).items())
        print(f"\n{name}   mean F1 = {m['mean_f1']:.3f}  (over {m['n_graded']} graded tasks)")
        if cat_str:
            print(f"    by track: {cat_str}")
        if u["calls"]:
            spc = m.get("sec_per_call")
            rt = f"{m.get('wall_seconds', 0):.1f}s total" + (f" ({spc:.2f}s/call)" if spc else "")
            print(f"    tokens: {u['input_tokens']:,} in / {u['output_tokens']:,} out "
                  f"over {u['calls']} calls   cost: {cost_str}   runtime: {rt}")
        for t in m["tasks"]:
            if t["category"] in GRADED_CATEGORIES:
                flag = "  !" + t["error"] if t.get("error") else ""
                spread = f" ±{t['f1_std']:.2f}" if t.get("n_samples", 1) > 1 else ""
                print(f"    {t['id']:<14} [{t['category']:<11}] f1={t['f1']:.2f}{spread}  "
                      f"P={t['precision']:.2f} R={t['recall']:.2f}{flag}")
            else:
                status = t["vlm"]["status"]
                print(f"    {t['id']:<14} [visual] plan_parsed={t['plan_parsed']} vlm={status}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Run the MolBench harness.")
    ap.add_argument("--models", nargs="+", default=["baseline"],
                    help="model specs: baseline | anthropic:<id> | openai:<id>")
    ap.add_argument("--categories", nargs="*", default=None,
                    help="filter tasks, e.g. mvs api_calling visual_rubric")
    ap.add_argument("--samples", type=int, default=1,
                    help="runs per task (>1 to average out LLM sampling noise)")
    ap.add_argument("--out", default=str(RESULTS_DIR / "scorecard.json"))
    args = ap.parse_args(argv)

    load_dotenv()  # make keys in .env available before any model is built
    report = run(args.models, args.categories, samples=args.samples)
    RESULTS_DIR.mkdir(exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(report, indent=2))
    print_scorecard(report)
    print(f"\nfull results -> {args.out}")


if __name__ == "__main__":
    main()
