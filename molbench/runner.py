"""
The harness: load tasks, run each model, grade, write a scorecard.

The benchmark run is described by one manifest file and started by one command::

    python -m molbench.runner --manifest run/final_run.toml --dry-run   # $0, mock model
    python -m molbench.runner --manifest run/final_run.toml             # plan + cost, no calls
    python -m molbench.runner --manifest run/final_run.toml --go        # the paid run

A manifest run is resumable (cells already in the archive are skipped), archives every
raw output with its token usage, latency, finish reason and prompt hash, stops when
projected spend passes the manifest's budget cap, and grades from the archive - so
grading can be redone later (``--grade-only``) without calling a model again.

The older ad-hoc form still works, with zero credentials::

    python -m molbench.runner --models baseline

Every run is archived; there is no way to switch that off.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import itertools
import json
import math
import os
import pathlib
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from . import grader as grader_mod
from . import manifest as manifest_mod
from . import mvs as mvs_mod
from . import schema
from . import tasks as tasks_mod
from .manifest import Budget, BudgetExceeded, Calibration, Manifest, ManifestError, ModelSpec
from .models import MockModel, Model, build_model
from .vlm_grader import StubVLMJudge

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
TASKS_DIR = REPO / "tasks"
RESULTS_DIR = REPO / "results"
RUNS_DIR = REPO / "runs"   # timestamped per-run archives (full raw outputs)


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True,
            stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001 - provenance is best-effort
        return None
PROMPT_API = REPO / "prompts" / "system_api.md"
PROMPT_MVS = REPO / "prompts" / "system_mvs.md"
API_REFERENCE = ROOT / "api_reference.md"
MVS_REFERENCE = ROOT / "mvs_reference.md"

# Prompting conditions for the scene-tree track. 'spec' hands the model the vendored
# MVS reference (the headline number); 'bare' gives only the output contract, so the
# gap between them measures what a model gains from documentation.
CONDITIONS = ("spec", "bare")

# --grounding appends a task's frozen grounding pack (scripts/build_grounding_packs.py)
# to the *user* message in this one fixed template; the system prompt is unchanged.
GROUNDING_TEMPLATE = "{prompt}\n\nFacts about the structures involved:\n{facts}"

# Categories whose tasks produce a numeric F1 (vs. visual_rubric, which is VLM-judged).
GRADED_CATEGORIES = ("mvs", "api_calling")

# LEGACY (``--models`` runs only): list prices in USD per 1,000,000 tokens (input,
# output), keyed by a substring of the model id. Several are out of date. A manifest
# run takes its prices from the manifest, with a source and a date; cost is just
# tokens x rate, so the token counts in a scorecard stay valid regardless.
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-opus-4": (15.0, 75.0),
    "gpt-4o": (2.5, 10.0),
    "gpt-5.4-nano": (0.05, 0.40),  # approximate
    "gpt-5-nano": (0.05, 0.40),    # approximate
    # Gemini prices are approximate (they change / vary by tier) — token counts are
    # exact, so cost just rescales if you correct the rate.
    "gemini-3.5-flash": (0.3, 2.5),
    "gemini-2.5-flash": (0.3, 2.5),
    "gemini-2.0-flash": (0.1, 0.4),
    # Open-weight models via OpenRouter (matched as substrings of the full slug).
    "qwen3-30b-a3b": (0.04, 0.17),
    "gemma-3-27b": (0.08, 0.16),
    "gpt-oss-20b": (0.03, 0.14),
    "deepseek-v3.2": (0.23, 0.34),
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
    """The corpus under ``tasks/``, read and validated by `molbench.tasks` (new-format
    files and, through its adapter, old ones). ``categories`` filters on the track's
    scorecard name (``mvs``, ``api_calling``); None also returns the old, ungraded
    ``visual_rubric`` files that the legacy ``--models`` path still elicits."""
    tasks = tasks_mod.load_corpus(TASKS_DIR, repo=REPO)
    if categories is None:
        for path in sorted(TASKS_DIR.rglob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            if "track" not in raw and raw.get("category") not in tasks_mod.TRACK_OF:
                raw["_path"] = str(path.relative_to(REPO))
                tasks.append(raw)
        return sorted(tasks, key=lambda t: t["_path"])
    return [t for t in tasks if t["category"] in categories]


def build_system_prompts(condition: str = "spec") -> dict[str, str]:
    """One assembled system prompt per task category.

    Each target speaks a different IR, so each gets its own instructions + vendored
    reference: pdbe-molstar calls for 'api_calling' (with the compact action list,
    `schema.schema_text`), the MolViewSpec scene tree for 'mvs' (also used to elicit a
    plan for 'visual_rubric'). One prompt per track serves single-turn and follow-up
    requests alike; the user message carries the difference (`user_message`).
    """
    api_prompt = (PROMPT_API.read_text(encoding="utf-8")
                  .replace("{{API_REFERENCE}}", API_REFERENCE.read_text(encoding="utf-8"))
                  .replace("{{SCHEMA_TEXT}}", schema.schema_text()))
    mvs_prompt = PROMPT_MVS.read_text(encoding="utf-8")
    if condition == "bare":
        mvs_prompt = mvs_prompt.replace("## MVS reference\n\n{{MVS_REFERENCE}}", "").rstrip() + "\n"
    else:
        mvs_prompt = mvs_prompt.replace("{{MVS_REFERENCE}}",
                                        MVS_REFERENCE.read_text(encoding="utf-8"))
    for name, text in (("system_api.md", api_prompt), ("system_mvs.md", mvs_prompt)):
        left = re.findall(r"\{\{[A-Z_]+\}\}", text)
        if left:
            raise RuntimeError(f"prompts/{name}: unfilled placeholder(s) {left}")
    return {"api_calling": api_prompt, "mvs": mvs_prompt, "visual_rubric": mvs_prompt}


# --- prediction parsing -----------------------------------------------------------

def _strip_fence(raw: str) -> str:
    """The text inside a leading ```json fence, or the text itself."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw


def extract_actions(raw: str) -> tuple[Any, str | None]:
    """Pull a JSON array of actions out of a model's raw text. Returns (obj, error).

    Takes the outermost ``[...]``, so a JSON-mode reply that wraps the array in an
    object (``{"actions": [...]}``) parses the same way.
    """
    raw = _strip_fence(raw)
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
    raw = _strip_fence(raw)
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

# What a follow-up request looks like to the model (decision 19): the state the viewer
# is in, then the new request. The answer is always the full new scene / call list.
FOLLOWUP_TEMPLATE = {
    "mvs": "Current scene (MolViewSpec JSON):\n{state}\n\nRequest: {prompt}",
    "api_calling": "Calls made so far (JSON array):\n{state}\n\nRequest: {prompt}",
}


def start_state(task: dict) -> Any:
    """A follow-up task's start state in the form the model must answer in: a full
    ``{"root": ...}`` scene, or the list of calls made so far. None on a single turn."""
    context = task.get("context")
    if not context:
        return None
    if task["category"] == "mvs":
        return {"root": tasks_mod.scene_root(context["scene"])}
    return context["calls"]


def user_message(task: dict, grounding: bool = False) -> str:
    """What the model is sent as the user turn: the task prompt; on a follow-up, the
    current scene / the calls made so far and then the request; plus the grounding
    pack when ``grounding`` is on and the task has one."""
    text = task["prompt"]
    state = start_state(task)
    if state is not None:
        text = FOLLOWUP_TEMPLATE[task["category"]].format(
            state=json.dumps(state, separators=(",", ":")), prompt=task["prompt"])
    pack = task.get("grounding")
    if not grounding or not pack:
        return text
    return GROUNDING_TEMPLATE.format(prompt=text, facts=pack["text"])


def task_skills(task: dict) -> list[str]:
    """A task's skill tags. MVS tasks call the field ``categories``, API tasks ``skills``."""
    return task.get("categories") or task.get("skills") or []


def is_success(sample: dict) -> bool:
    """Task success: the final state is exactly right. A grader may say so itself
    (``success``); otherwise it is a perfect F1."""
    if "success" in sample:
        return bool(sample["success"])
    return sample.get("f1", 0.0) >= 1.0


# Finish reasons that mean the provider cut the answer at the token limit ("length" on
# OpenAI-compatible routes, "max_tokens" on Anthropic's). A truncated answer is counted
# apart from a malformed one: it says the limit was too low, not that the model cannot
# write the format.
TRUNCATED_REASONS = ("length", "max_tokens")


def is_truncated(sample: dict) -> bool:
    return sample.get("finish_reason") in TRUNCATED_REASONS


class GradingError(RuntimeError):
    """A task cannot be graded the way the benchmark says it is graded (no atom table,
    or an API answer the state grader did not grade). Never scored around: the run's
    grading stops and names the task."""


_ZERO = {"f1": 0.0, "precision": 0.0, "recall": 0.0}


def _grader_crash(exc: Exception, outcome: str, predicted: Any, raw: str) -> dict[str, Any]:
    """The result for an output the grader itself could not handle. Model output is
    arbitrary JSON, and one reply that trips a grader bug must not stop a whole run
    from being graded: it scores 0 and is marked, and `grade_archive` reports the
    count so the bug gets fixed rather than hidden."""
    msg = f"{type(exc).__name__}: {exc}"
    return {**_ZERO, "success": False, "error": f"grader crashed: {msg}", "grader_crash": msg,
            "outcome": outcome, "predicted": predicted, "raw": raw, "schema_errors": []}


def action_schema_errors(actions: Any) -> list[str]:
    """`schema.validate_actions`, which raises on an action whose name is not a string
    (a list or an object cannot be looked up). That is a schema error, not a crash."""
    try:
        return schema.validate_actions(actions)
    except TypeError:
        bad = [i for i, a in enumerate(actions)
               if isinstance(a, dict) and not isinstance(a.get("action"), str)]
        return [f"action[{i}]: 'action' is not a string" for i in bad] or ["malformed action"]


def check_gradable(task: dict) -> None:
    """Raise `GradingError` unless the task can be graded on atoms: every structure it
    loads has a frozen atom table. Run for every task before a run is graded."""
    missing = [s for s in task.get("structures", []) if not tasks_mod.has_table(s)]
    if missing:
        raise GradingError(f"task {task['id']}: no atom table for {missing}; it cannot be "
                           "graded on atoms (scripts/build_atom_tables.py)")


def grader_grades_mvs() -> bool:
    """Whether `grader.grade_task` grades the MVS track too (on the drawn state, with a
    target score). It says so with ``GRADES_MVS = True`` or by having ``is_mvs_task``;
    the grader of the October runs has neither and takes call lists only."""
    return bool(getattr(grader_mod, "GRADES_MVS", False)
                or callable(getattr(grader_mod, "is_mvs_task", None)))


def grader_target(task: dict, target: Any) -> Any:
    """A task ``target`` in the form the grader reads: ``{"selector": ..., "entry": ...}``.

    TASK_FORMAT.md writes a target as a list of parts (``selector``, ``representation``,
    ``color``, ``structure``); the grader takes one object naming the atoms and reads the
    representation and colour off the reference. Handing it the list would be ignored
    without a word and the target score would silently become "everything the reference
    draws", so the list is translated here, and a target that cannot be translated
    raises `GradingError`. None and an object are passed through."""
    if target is None or isinstance(target, dict):
        return target
    parts = [p for p in target if isinstance(p, dict)] if isinstance(target, list) else []
    structures = {p.get("structure") for p in parts}
    selectors = [p.get("selector") for p in parts]
    if not parts or len(parts) != len(target) or len(structures) != 1:
        raise GradingError(f"task {task.get('id')}: a target on more than one structure (or "
                           "a malformed one) cannot be handed to the grader")
    if len(selectors) == 1:
        selector = selectors[0]
    elif all(isinstance(sel, (dict, list)) for sel in selectors):
        selector = [e for sel in selectors for e in (sel if isinstance(sel, list) else [sel])]
    else:
        raise GradingError(f"task {task.get('id')}: a target of several parts, one of them a "
                           "static selector name, cannot be handed to the grader as one "
                           "selector; write it as one part")
    out = {"selector": selector}
    structure = structures.pop()
    if structure and len(task.get("structures") or []) > 1:
        out["entry"] = structure
    return out


def _grader_view(task: dict, reference: Any, target: Any, accepted: list) -> dict:
    """The task as `grader.grade_task` is handed it: one reference, its alternatives and
    the target in the grader's own form."""
    out = {**task, "reference": reference, "accepted": accepted,
           "target": grader_target(task, target)}
    out.pop("accepted_targets", None)
    if task.get("category") == "mvs":
        out["reference_mvs"] = reference
    return out


def _grade_task(task: dict, prediction: Any) -> dict[str, Any]:
    """`grader.grade_task`, with the task's target translated (`grader_target`). When
    the alternatives have targets of their own (``accepted_targets``: "either copy will
    do") each right answer is graded with its own target and the best is kept; the
    grader knows one target per task, and would score the other copy's target 0."""
    reference = task["reference"] if "reference" in task else task["reference_mvs"]
    accepted = list(task.get("accepted") or [])
    alt_targets = task.get("accepted_targets")
    if not alt_targets:
        return grader_mod.grade_task(
            _grader_view(task, reference, task.get("target"), accepted), prediction)
    best, best_rank = None, None
    answers = [(reference, task.get("target"))] + list(zip(accepted, alt_targets))
    for i, (state, target) in enumerate(answers):
        res = grader_mod.grade_task(_grader_view(task, state, target, []), prediction)
        res["matched_reference"] = i
        rank = (bool(res.get("success")), res.get("f1") or 0.0, res.get("target_f1") or 0.0)
        if best is None or rank > best_rank:
            best, best_rank = res, rank
    return best


def grader_problems(task: dict) -> list[str]:
    """What the grader's own task check (`grader.check_task`, when the grader has one)
    says about a task: a selection that resolves to no atoms, a state it cannot place
    on an atom table, a target the reference does not draw. Empty = fine. The grader is
    handed the task in its own form: the target translated, and a follow-up's start
    state as the bare scene / call list."""
    check = getattr(grader_mod, "check_task", None)
    if not callable(check):
        return []
    try:
        view = _grader_view(task, task["reference"], task.get("target"),
                            list(task.get("accepted") or []))
    except GradingError as e:
        return [str(e)]
    state = start_state(task)
    if state is None:
        view.pop("context", None)
    else:
        view["context"] = state
    return [str(p) for p in check(view)]


def _mvs_grade(task: dict, tree: Any) -> dict[str, Any]:
    """Grade a parsed MVS scene. `grader.grade_task` is the one entry point; with a
    grader that does not grade the MVS track (`grader_grades_mvs`) the scene is scored
    by `mvs.grade_mvs` against the reference and each accepted alternative, keeping
    the best."""
    if grader_grades_mvs():
        return _grade_task(task, tree)
    reference = task["reference"] if "reference" in task else task["reference_mvs"]
    best = None
    for i, ref in enumerate([reference] + list(task.get("accepted") or [])):
        res = mvs_mod.grade_mvs(ref, tree, accepted_refs=task.get("accepted_ids"))
        res["matched_reference"] = i
        if best is None or res["f1"] > best["f1"]:
            best = res
    best.setdefault("success", best["f1"] >= 1.0 and not best.get("error"))
    best.setdefault("grader", "mvs-paths")
    return best


def grade_parsed(task: dict, prediction: Any) -> dict[str, Any]:
    """Grade an already-parsed answer (a scene tree or a call list) against a task:
    its reference and its accepted alternatives. Returns the grader's own result
    (``f1``, ``success``, ``target_f1`` when it reports one, ``grader``, ...).

    An API answer must have been graded by the final-state grader; anything else
    (the old sequence grader stepping in because no atom table was found) raises
    `GradingError` instead of quietly producing a different kind of score."""
    if task["category"] == "mvs":
        return _mvs_grade(task, prediction)
    result = _grade_task(task, prediction)
    if result.get("grader") != "state":
        raise GradingError(
            f"task {task['id']}: graded by {result.get('grader')!r}, not by the final-state "
            "grader (is the atom table of its structure missing?)")
    return result


def _grade_actions(task: dict, actions: Any, raw: str) -> dict[str, Any]:
    schema_errors = action_schema_errors(actions)
    try:
        result = grade_parsed(task, actions)
    except GradingError:
        raise
    except Exception as e:  # noqa: BLE001 - see _grader_crash
        return {**_grader_crash(e, "invalid_api", actions, raw), "track": "api_calling",
                "schema_errors": schema_errors}
    # The grader may classify the output itself; otherwise derive it: 'invalid_api' when
    # the grader reports an error or the action schema is broken. The score is whatever
    # the grader gave - this label does not change it.
    result.setdefault("outcome", "invalid_api" if result.get("error") or schema_errors
                      else "valid")
    result.update(schema_errors=schema_errors, predicted=actions, raw=raw, track="api_calling")
    return result


def grade_api_output(task: dict, raw: str) -> dict[str, Any]:
    """Parse + grade one raw API-track reply."""
    actions, err = extract_actions(raw)
    if err:
        return {**_ZERO, "success": False, "error": err, "raw": raw, "outcome": "invalid_json",
                "track": "api_calling"}
    return _grade_actions(task, actions, raw)


def _grade_tree(task: dict, tree: Any, raw: str) -> dict[str, Any]:
    try:
        result = grade_parsed(task, tree)
        schema_errors = mvs_mod.validate_mvs(tree)
    except GradingError:
        raise
    except Exception as e:  # noqa: BLE001 - see _grader_crash
        return {**_grader_crash(e, "not_mvs", tree, raw), "track": "mvs"}
    if result.get("outcome") not in ("not_mvs", "unchecked"):
        # Mol* has the last word on validity (`validate_samples`); until it has run a
        # parsed scene is 'unchecked', whatever the grader called it.
        result["outcome"] = "not_mvs" if result.get("error") else "unchecked"
    result.update(schema_errors=schema_errors, predicted=tree, raw=raw, track="mvs")
    return result


def grade_mvs_output(task: dict, raw: str) -> dict[str, Any]:
    """Parse + grade one raw MVS-track reply (Mol* validation comes later, in a batch)."""
    tree, err = extract_json_object(raw)
    if err:
        return {**_ZERO, "success": False, "error": err, "raw": raw, "outcome": "invalid_json",
                "track": "mvs"}
    return _grade_tree(task, tree, raw)


def grade_output(task: dict, raw: str) -> dict[str, Any]:
    return (grade_mvs_output if task["category"] == "mvs" else grade_api_output)(task, raw)


def repair_counterfactual(task: dict, sample: dict) -> dict[str, Any] | None:
    """What an ``invalid_json`` sample would have scored after the ``json-repair``
    library fixed its JSON. Offline and free; the strict score is never changed.

    Returns None when the sample parsed, or when nothing gradeable can be recovered.
    """
    if sample.get("outcome") != "invalid_json":
        return None
    try:
        import json_repair
    except ImportError:  # declared in pyproject; only missing in a bare checkout
        return None
    try:
        obj = json_repair.repair_json(_strip_fence(sample.get("raw") or ""),
                                      return_objects=True)
    except Exception:  # noqa: BLE001 - a repair that crashes is a repair that failed
        return None
    if task["category"] == "mvs":
        if not isinstance(obj, dict) or not obj:
            return None
        fixed = _grade_tree(task, obj, "")
    else:
        if isinstance(obj, dict) and isinstance(obj.get("actions"), list):
            obj = obj["actions"]
        if not isinstance(obj, list) or not obj:
            return None
        fixed = _grade_actions(task, obj, "")
    if "grader_crash" in fixed:
        return None  # nothing gradeable was recovered
    return {k: fixed[k] for k in ("f1", "precision", "recall", "outcome", "predicted", "error")
            if k in fixed}


def run_api_task(model, system: str, task: dict, user: str | None = None) -> dict[str, Any]:
    return grade_api_output(task, model.generate(system, task["prompt"] if user is None else user))


def run_mvs_task(model, system: str, task: dict, user: str | None = None) -> dict[str, Any]:
    return grade_mvs_output(task, model.generate(system, task["prompt"] if user is None else user))


# Why an MVS sample scored what it did. 'invalid_*', 'not_mvs' and 'load_failed' score
# 0: Mol* shows nothing for them. A parsed scene is 'unchecked' until Mol* validates it
# (``--validate``), then 'valid' or 'invalid_mvs'.
OUTCOMES = ("valid", "unchecked", "invalid_json", "not_mvs", "invalid_mvs", "load_failed")
# The API track's classes. No viewer is run, so there is no 'unchecked'/'load_failed'.
# 'invalid_api' = a JSON array that is not a schema-valid action list (still graded -
# see `_grade_actions`).
API_OUTCOMES = ("valid", "invalid_json", "invalid_api")


def _invalidate(sample: dict, outcome: str, detail: list[str] | str) -> None:
    """Mark a parsed scene that Mol* will not show: score 0 and record why."""
    sample.update(f1=0.0, precision=0.0, recall=0.0, outcome=outcome)
    if "success" in sample:  # a grader-supplied verdict must not outlive the zero
        sample["success"] = False
    if sample.get("target_f1") is not None:
        sample["target_f1"] = 0.0
    sample["mvs_issues" if outcome == "invalid_mvs" else "load_error"] = detail


def validate_samples(samples: list[dict]) -> None:
    """Run Mol*'s own validation over every parsed MVS sample, in one batch."""
    from .render import molstar_issues
    todo = [s for s in samples if s.get("outcome") == "unchecked"]
    for s, issues in zip(todo, molstar_issues([s["predicted"] for s in todo])):
        if issues:
            _invalidate(s, "invalid_mvs", issues)
        else:
            s["outcome"] = "valid"


def target_score(sample: dict) -> float | None:
    """The sample's target score (the requested atoms alone: selection, representation,
    colour - decision 17), or None when the grader reports none for this task."""
    v = sample.get("target_f1")
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _mean_or_none(values: list) -> float | None:
    values = list(values)
    if not values or any(v is None for v in values):
        return None
    return round(statistics.fmean(values), 4)


def _aggregate(samples: list[dict]) -> dict[str, Any]:
    """Reduce N graded samples of one task to mean/std/min/max + a representative.

    LLMs are stochastic, so a single sample is noisy. We score each task as the
    *mean over N samples* and keep the spread so the report can show mean±std and
    callers can tell a real gap from sampling noise. Task success is reported both
    ways: ``success`` is the mean over the samples, ``success_all`` says whether every
    sample was exactly right. ``target_f1`` is the mean target score (None when the
    grader reports none).
    """
    f1s = [s["f1"] for s in samples]
    ps = [s.get("precision", 0.0) for s in samples]
    rs = [s.get("recall", 0.0) for s in samples]
    wins = [is_success(s) for s in samples]
    targets = [target_score(s) for s in samples]
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
        "success": round(statistics.fmean(wins), 4),
        "success_all": all(wins),
        "target_f1": _mean_or_none(targets),
        "n_truncated": sum(is_truncated(s) for s in samples),
        "predicted": rep.get("predicted"),
        "error": rep.get("error"),
        "schema_errors": rep.get("schema_errors"),
        **{k: rep[k] for k in ("outcome", "mvs_issues", "load_error") if k in rep},
        **({"outcomes": [s.get("outcome") for s in samples]}
           if any("outcome" in s for s in samples) else {}),
    }


def run(models: list[str], categories: list[str] | None,
        samples: int = 1, escalate: bool = False,
        judge: str | None = None, condition: str = "spec",
        grounding: bool = False, validate: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (report, raw_samples).

    `report` is the lightweight scorecard (aggregates + best-sample prediction).
    `raw_samples` holds every sample's full raw model text and prediction, keyed
    by [model][task_id] — heavy, written only to the per-run archive.

    With `escalate=True`, each imperfect MVS prediction is run through the
    rendering cascade (`escalate.escalating_grade`): perfect trees short-circuit at
    the tree tier (no render), imperfect ones render reference+prediction for a
    visual diff, and genuinely-different images escalate to a VLM judge (if `judge`
    is a vision-model id). The per-task `escalation` field then records
    tree-F1-vs-what-the-image-shows — the "grader score vs human-visible" data.
    Requires the `execute` extra (Playwright + the Mol* bundle).
    """
    tasks = load_tasks(categories)
    if not tasks:
        sys.exit("no tasks matched; check tasks/ and --categories")
    prompts = build_system_prompts(condition)
    vlm = StubVLMJudge()

    report: dict[str, Any] = {
        "models": {}, "n_tasks": len(tasks), "samples": samples,
        "meta": {
            "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": uuid.uuid4().hex,  # ties a scorecard to its archive unambiguously
            "git_commit": _git_commit(),
            "models": models,
            "categories": categories,
            "escalate": escalate,
            "judge": judge,
            "condition": condition,
            "grounding": grounding,
            **(_grounding_meta(tasks) if grounding else {}),
            "validate": validate or escalate,
        },
    }

    # Escalation is opt-in and lazy so the core path stays browser-free.
    render_fn = vlm_fn = gallery = None
    escalating_grade = None
    if escalate:
        from .render import render_scene
        from .escalate import escalating_grade
        render_fn = lambda tree, png: render_scene(tree, png, width=600, height=450)
        if judge:
            from .vlm_grader import AnthropicImagePairJudge
            vlm_fn = AnthropicImagePairJudge(judge)
        gallery = RUNS_DIR / ("gallery_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))

    raw_samples: dict[str, Any] = {}
    for spec in models:
        model = build_model(spec)
        per_task = []
        pending = []  # (task, samples) for graded tasks, aggregated after validation
        raw_samples[model.name] = {}
        started = time.perf_counter()
        for task in tasks:
            cat = task.get("category")
            system = prompts.get(cat, prompts["mvs"])
            if cat == "visual_rubric":
                # Component 2: we still elicit a plan (useful signal), but scoring
                # needs a render + VLM judge (stubbed here).
                raw = model.generate(system, user_message(task, grounding))
                _, err = extract_json_object(raw)
                judged = vlm.score(image_path="", rubric=task.get("rubric", []),
                                   prompt=task["prompt"])
                per_task.append({"id": task["id"], "category": cat,
                                 "plan_parsed": err is None, "vlm": judged})
                raw_samples[model.name][task["id"]] = [{"raw": raw}]
            elif cat in GRADED_CATEGORIES:
                run_task = run_mvs_task if cat == "mvs" else run_api_task
                user = user_message(task, grounding)
                pending.append((task, [run_task(model, system, task, user)
                                       for _ in range(samples)]))
                per_task.append(None)  # placeholder keeps task order

        if validate or escalate:
            validate_samples([s for t, got in pending if t["category"] == "mvs" for s in got])
        slots = iter(i for i, t in enumerate(per_task) if t is None)
        for task, got in pending:
            cat = task["category"]
            pt = {"id": task["id"], "category": cat,
                  "categories": task_skills(task), **_aggregate(got)}
            while (escalate and cat == "mvs" and pt.get("outcome") == "valid"
                    and pt.get("predicted") is not None):
                wd = gallery / model.name.replace("/", "_") / task["id"]
                pt["escalation"] = esc = escalating_grade(
                    task["reference_mvs"], pt["predicted"], prompt=task.get("prompt"),
                    render=render_fn, vlm=vlm_fn, workdir=str(wd),
                    accepted_refs=task.get("accepted_ids"))
                if esc.get("decision") != "render-failed" or esc.get("failed_side") != "prediction":
                    break
                # Valid by Mol*'s rules, but Mol* still could not load it: score 0 and
                # escalate the next-best sample, if any, as the task's representative.
                best = max(got, key=lambda s: s["f1"])
                _invalidate(best, "load_failed", esc.get("note", ""))
                pt.update(_aggregate(got))
            per_task[next(slots)] = pt
            raw_samples[model.name][task["id"]] = [
                {"f1": g["f1"], "predicted": g.get("predicted"), "raw": g.get("raw"),
                 "error": g.get("error"),
                 **{k: g[k] for k in ("outcome", "mvs_issues", "load_error", "track")
                    if k in g}}
                for g in got]

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
            "by_skill": _means_by_skill(per_task),
            **_format_stats(raw_samples[model.name]),
            "tasks": per_task,
        }
    return report, raw_samples


def _grounding_meta(tasks: list[dict]) -> dict[str, Any]:
    """How many of the run's tasks carried a grounding pack (the rest ran unchanged)."""
    packs = [t["grounding"] for t in tasks if t.get("grounding")]
    return {"grounding_rules": sorted({p["rule"] for p in packs}),
            "n_tasks_with_pack": len(packs), "n_tasks_without_pack": len(tasks) - len(packs)}


def _format_stats(model_raw: dict) -> dict[str, Any]:
    """Separate output-format reliability from scene competence.

    `parse_success` = fraction of graded samples that produced valid output;
    `cond_f1` = mean F1 *conditional on* parsing. The gap between cond_f1 and the
    unconditional mean reveals how much a model's score is dragged by malformed
    output (a JSON-validity problem) versus genuine visualization error.
    """
    samples = [s for task in model_raw.values() for s in task if "f1" in s]
    if not samples:
        return {"parse_success": None, "cond_f1": None}
    parsed = [s for s in samples if not s.get("error")]
    out = {
        "parse_success": round(len(parsed) / len(samples), 4),
        "cond_f1": round(statistics.fmean(s["f1"] for s in parsed), 4) if parsed else 0.0,
    }
    mvs = [s for s in samples if "outcome" in s and s.get("track", "mvs") == "mvs"]
    if mvs:
        # With Mol* validation, cond_f1 is over scenes Mol* can show, and the outcome
        # counts say why the rest score 0.
        out["outcomes"] = {o: sum(s["outcome"] == o for s in mvs) for o in OUTCOMES}
        if not out["outcomes"]["unchecked"]:  # only claim validity Mol* confirmed
            valid = [s for s in mvs if s["outcome"] == "valid"]
            out["valid_scene"] = round(len(valid) / len(mvs), 4)
            out["cond_f1"] = round(statistics.fmean(s["f1"] for s in valid), 4) if valid else 0.0
    return out


def _means_by_skill(per_task: list[dict]) -> dict[str, dict]:
    """Mean F1 per skill category (selection, color, camera, ...).

    A task carries several categories, so it contributes to each. This is what
    powers the leaderboard drill-down: 'on selection, model X beats Y'. The per-task
    record's ``categories`` holds the skill tags of either track (see `task_skills`).
    """
    buckets: dict[str, list[float]] = {}
    for t in per_task:
        for skill in t.get("categories", []):
            buckets.setdefault(skill, []).append(t["f1"])
    return {skill: {"mean_f1": round(statistics.fmean(vs), 4), "n": len(vs)}
            for skill, vs in sorted(buckets.items())}


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


# --- manifest runs ----------------------------------------------------------------
#
# A manifest run is three separable steps:
#
#   plan      manifest x corpus -> the list of cells (model, condition, task, sample)
#   generate  call the model for every cell not yet in the archive; append raw output
#   grade     read the archive, grade every cell, write scorecards
#
# Only 'generate' can cost money, and it writes nothing but the archive. Grading is a
# pure function of (archive, corpus, grader), so it can be redone at any time.

# Appended to the API system prompt in a structured-output (JSON mode) condition:
# JSON mode returns an object, the API track's answer is an array. `extract_actions`
# unwraps it.
API_STRUCTURED_SUFFIX = (
    '\n\n## JSON mode\n\nReturn one JSON object of the form {"actions": [...]}, where '
    '"actions" is the JSON array described above.\n')

ARCHIVE_VERSION = 2   # 2: adds 'provider' and request.temperature = "provider-default"
# HTTP statuses that will fail the same way on a retry: bad request, bad key, no
# credit, unknown model. Everything else (rate limits, timeouts, 5xx) is retried.
NO_RETRY_STATUS = (400, 401, 402, 403, 404, 422)
# A model whose calls in one condition fail this many times in a row (after retries) is
# dropped from that condition for the rest of this start: a dead key or a hard rate limit
# should not be hammered for hours. Per condition, so a model whose provider rejects JSON
# mode still runs its other conditions. Its cells stay un-archived, so the next start
# tries them again.
MAX_CONSECUTIVE_FAILURES = 10


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def task_hash(task: dict) -> str:
    """SHA-256 of the task's file (of its content, for a task that was not loaded from one)."""
    if task.get("_sha256"):
        return task["_sha256"]
    return _sha(json.dumps({k: v for k, v in task.items() if not k.startswith("_")},
                           sort_keys=True))


def reference_chars(task: dict) -> int:
    """Size of the task's reference answer as compact JSON (drives the output estimate)."""
    ref = task.get("reference_mvs", task.get("reference"))
    return len(json.dumps(ref, separators=(",", ":"))) if ref is not None else 0


@dataclass(frozen=True)
class Cell:
    """One model call to make: a model, a condition, a task and a sample number."""
    model: ModelSpec
    condition: manifest_mod.Condition
    task: dict
    sample: int
    system: str
    user: str

    @property
    def key(self) -> tuple[str, str, str, int]:
        return (self.model.id, self.condition.name, self.task["id"], self.sample)

    @property
    def prompt_sha256(self) -> str:
        return _sha(self.system + "\n\x00\n" + self.user)

    @property
    def structured(self) -> str | None:
        return self.model.structured if self.condition.structured else None


def build_plan(manifest: Manifest, tasks: list[dict], panel: list[ModelSpec]) -> list[Cell]:
    """Every cell of the run, in the order it is run: condition (the headline first),
    then task, sample, model - so an interrupted run has whole conditions finished and
    every model at the same point."""
    ids = [t["id"] for t in tasks]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ManifestError(f"duplicate task ids in the corpus: {dup}")
    for task in tasks:
        check_gradable(task)  # before any call is paid for, not after
    prompts = {kind: build_system_prompts(kind) for kind in manifest_mod.PROMPTS}
    cells: list[Cell] = []
    for cond in manifest.conditions:
        if cond.prompt == "bare" and "api_calling" in cond.tracks:
            raise ManifestError(f"condition {cond.name!r}: the 'bare' prompt exists for the "
                                "MVS track only; set tracks = [\"mvs\"]")
        models = [m for m in panel if cond.takes_model(m)]
        for task in tasks:
            if not cond.takes_task(task):
                continue
            cat = task["category"]
            system = prompts[cond.prompt][cat]
            if cond.structured and cat == "api_calling":
                system += API_STRUCTURED_SUFFIX
            user = user_message(task, cond.grounding)
            for sample in range(manifest.samples):
                cells.extend(Cell(m, cond, task, sample, system, user) for m in models)
    return cells


class RunArchive:
    """The raw record of a run: append-only JSON lines, one per completed model call.

    ``<root>/cells/<model>/<condition>.jsonl`` holds the calls, ``errors.jsonl`` the
    calls that failed after every retry (they are retried on the next start), and
    ``run.json`` what the archive was made from. Nothing here is ever rewritten.
    """

    def __init__(self, root: pathlib.Path):
        self.root = pathlib.Path(root)
        self._lock = threading.Lock()
        self._held = 0          # depth of `exclusive` on this object
        self._lock_fh = None

    @contextlib.contextmanager
    def exclusive(self):
        """Hold the archive for writing. A second run on the same archive (another
        process, or another `RunArchive` in this one) is refused at once instead of
        archiving every cell twice. The lock is an OS file lock on ``<root>/LOCK``: it
        goes away with the process, so a crashed run leaves nothing to clean up."""
        if self._held:
            self._held += 1
            try:
                yield
            finally:
                self._held -= 1
            return
        self.root.mkdir(parents=True, exist_ok=True)
        fh = (self.root / "LOCK").open("a+", encoding="utf-8")
        try:
            try:
                import fcntl
            except ImportError:  # not POSIX: no lock available; say so
                print("warning: no file locking on this platform; do not start the same "
                      "run twice at once", file=sys.stderr)
            else:
                try:
                    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as e:
                    fh.seek(0)
                    raise ManifestError(
                        f"{self.root} is being written by another run ({fh.read().strip() or '?'}). "
                        "Two runs on one archive would archive every cell twice; wait for it "
                        "to finish.") from e
            fh.seek(0)
            fh.truncate()
            fh.write(f"pid {os.getpid()}, started {_now()}\n")
            fh.flush()
            self._held, self._lock_fh = 1, fh
            yield
        finally:
            self._held, self._lock_fh = 0, None
            fh.close()

    def _cell_file(self, model_slug: str, condition: str) -> pathlib.Path:
        return self.root / "cells" / model_slug / f"{condition}.jsonl"

    def open(self, manifest: Manifest, corpus_sha256: str, mock: bool,
             argv: list[str] | None = None) -> dict:
        """Create the archive, or check that an existing one belongs to this run."""
        lock_file = self.root / "run.json"
        session = {"started_at": _now(), "git_commit": _git_commit(),
                   "manifest_sha256": manifest.sha256, "argv": argv or []}
        if lock_file.exists():
            lock = json.loads(lock_file.read_text(encoding="utf-8"))
            for field, now in (("run", manifest.name), ("corpus_sha256", corpus_sha256),
                               ("mock", mock)):
                if lock.get(field) != now:
                    raise ManifestError(
                        f"{self.root} was made with {field} = {lock.get(field)!r}, this run "
                        f"has {now!r}. An archive is never mixed: use a new run name.")
            lock["sessions"].append(session)
        else:
            self.root.mkdir(parents=True, exist_ok=True)
            lock = {"archive_version": ARCHIVE_VERSION, "run": manifest.name,
                    "corpus_version": manifest.corpus_version, "corpus_sha256": corpus_sha256,
                    "mock": mock, "created_at": session["started_at"], "sessions": [session]}
        lock_file.write_text(json.dumps(lock, indent=2), encoding="utf-8")
        return lock

    def load(self) -> dict[tuple, dict]:
        """Every archived call, keyed (model, condition, task, sample)."""
        out: dict[tuple, dict] = {}
        for f in sorted((self.root / "cells").glob("*/*.jsonl")):
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    # A crash mid-write can leave one torn last line; the cell is
                    # simply not done and will be run again.
                    print(f"warning: {f}:{n}: unreadable line ignored", file=sys.stderr)
                    continue
                key = (r["model"], r["condition"], r["task_id"], r["sample"])
                if key in out:
                    raise ManifestError(f"{f}:{n}: cell {key} is archived twice")
                out[key] = r
        return out

    def append(self, model_slug: str, record: dict) -> None:
        f = self._cell_file(model_slug, record["condition"])
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with self._lock:
            f.parent.mkdir(parents=True, exist_ok=True)
            with f.open("a+b") as fh:
                # A crash mid-write can leave a torn last line with no newline; start
                # on a fresh line so this record is not glued to it and lost as well.
                if fh.tell() > 0:
                    fh.seek(-1, os.SEEK_END)
                    if fh.read(1) != b"\n":
                        line = "\n" + line
            with f.open("a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())

    def log_error(self, record: dict) -> None:
        with self._lock:
            with (self.root / "errors.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cell_estimate(manifest: Manifest, cell: Cell, calib: Calibration) -> dict[str, Any]:
    """Expected tokens and dollars for one cell, from its real prompt length."""
    max_tokens = manifest.max_tokens_for(cell.model)
    inp, out = manifest_mod.estimate_tokens(
        len(cell.system) + len(cell.user), reference_chars(cell.task),
        calib.rates(cell.model), max_tokens)
    price = cell.model.price
    return {"input_tokens": inp, "output_tokens": out,
            "cost_usd": manifest_mod.estimate_cost(price, inp, out),
            "worst_cost_usd": manifest_mod.estimate_cost(price, inp, max_tokens)}


def project_costs(manifest: Manifest, cells: list[Cell], calib: Calibration) -> list[dict]:
    """One row per (model, condition): calls, expected tokens, expected and worst-case
    dollars. Worst case = every call spends its full ``max_tokens``."""
    rows: dict[tuple, dict] = {}
    for c in cells:
        e = cell_estimate(manifest, c, calib)
        r = rows.setdefault((c.model.id, c.condition.name), {
            "model": c.model.id, "condition": c.condition.name, "optional": c.model.optional,
            "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
            "worst_cost_usd": 0.0, "priced": c.model.price is not None,
            "price_verified": bool(c.model.price and c.model.price.verified),
            "calibrated": calib.rates(c.model).calibrated})
        r["calls"] += 1
        r["input_tokens"] += e["input_tokens"]
        r["output_tokens"] += e["output_tokens"]
        r["cost_usd"] += e["cost_usd"] or 0.0
        r["worst_cost_usd"] += e["worst_cost_usd"] or 0.0
    return list(rows.values())


def print_projection(manifest: Manifest, rows: list[dict], out=None) -> dict[str, float]:
    """Print the cost table; return the totals."""
    out = out or sys.stdout
    conds = [c.name for c in manifest.conditions if any(r["condition"] == c.name for r in rows)]
    by_model: dict[str, dict] = {}
    for r in rows:
        by_model.setdefault(r["model"], {})[r["condition"]] = r
    w = max([len(m) for m in by_model] + [5])
    print(f"\nProjected cost of the real run ({manifest.name}, {manifest.samples} sample(s) "
          f"per task; tokens estimated from real prompt lengths)", file=out)
    print(f"{'model':<{w}}  {'calls':>6} {'input tok':>11} {'output tok':>10}  "
          + "  ".join(f"{c:>15}" for c in conds) + f"  {'total $':>9} {'worst $':>9}", file=out)
    totals = {"core": 0.0, "optional": 0.0, "core_worst": 0.0, "optional_worst": 0.0}
    calls = {"core": 0, "optional": 0}
    for model, per in by_model.items():
        any_row = next(iter(per.values()))
        group = "optional" if any_row["optional"] else "core"
        cost = sum(r["cost_usd"] for r in per.values())
        worst = sum(r["worst_cost_usd"] for r in per.values())
        totals[group] += cost
        totals[group + "_worst"] += worst
        calls[group] += sum(r["calls"] for r in per.values())
        flags = ("" if any_row["priced"] else " [no price]") + \
                ("" if any_row["price_verified"] or not any_row["priced"] else " [price unverified]") + \
                ("" if any_row["calibrated"] else " [tokens: pooled rate]") + \
                (" [optional]" if any_row["optional"] else "")
        print(f"{model:<{w}}  {sum(r['calls'] for r in per.values()):>6} "
              f"{sum(r['input_tokens'] for r in per.values()):>11,} "
              f"{sum(r['output_tokens'] for r in per.values()):>10,}  "
              + "  ".join(f"{('$%.2f' % per[c]['cost_usd']) if c in per else '-':>15}"
                          for c in conds)
              + f"  {cost:>9.2f} {worst:>9.2f}{flags}", file=out)
    print(f"\n  core panel:      {calls['core']:>7,} calls   expected ${totals['core']:.2f}   "
          f"worst case ${totals['core_worst']:.2f}", file=out)
    if calls["optional"]:
        print(f"  optional models: {calls['optional']:>7,} calls   expected "
              f"${totals['optional']:.2f}   worst case ${totals['optional_worst']:.2f}", file=out)
    total = totals["core"] + totals["optional"]
    verdict = "within" if total <= manifest.budget_usd else "ABOVE"
    print(f"  total expected ${total:.2f} is {verdict} the budget cap of "
          f"${manifest.budget_usd:.2f}", file=out)
    totals["total"] = total
    return totals


class CellFailed(RuntimeError):
    def __init__(self, attempts: int, error: str):
        super().__init__(error)
        self.attempts = attempts


def _retryable(exc: Exception) -> bool:
    if isinstance(exc, (KeyError, ValueError, TypeError, NotImplementedError, ImportError)):
        return False  # a missing key or a bug, not a transient provider error
    return getattr(exc, "status_code", None) not in NO_RETRY_STATUS


def call_cell(manifest: Manifest, cell: Cell, model: Model,
              sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Make one cell's call (with the manifest's retry policy) and return its archive record."""
    max_tokens = manifest.max_tokens_for(cell.model)
    started_at = _now()
    context = {"task": cell.task, "task_id": cell.task["id"], "sample": cell.sample,
               "condition": cell.condition.name}
    attempt = 0
    while True:
        attempt += 1
        try:
            done = model.complete(cell.system, cell.user, max_tokens=max_tokens,
                                  structured=cell.structured,
                                  timeout=manifest.retry.timeout_seconds, context=context)
            break
        except Exception as e:  # noqa: BLE001 - provider errors come in every shape
            if attempt >= manifest.retry.max_attempts or not _retryable(e):
                raise CellFailed(attempt, f"{type(e).__name__}: {e}") from e
            sleep(manifest.retry.delay(attempt))
    price = cell.model.price
    if done.cost_usd is not None:
        cost, cost_source = done.cost_usd, "provider"
    elif price is not None and done.input_tokens is not None and done.output_tokens is not None:
        cost, cost_source = price.cost(done.input_tokens, done.output_tokens), "price"
    else:
        cost, cost_source = None, None
    return {
        "v": ARCHIVE_VERSION, "run": manifest.name,
        "model": cell.model.id, "route": cell.model.route,
        "condition": cell.condition.name, "task_id": cell.task["id"], "sample": cell.sample,
        "track": cell.task["category"],
        "prompt_sha256": cell.prompt_sha256, "system_sha256": _sha(cell.system),
        "task_sha256": task_hash(cell.task),
        # No temperature is ever sent (decision 12): the provider's default applies.
        "request": {"max_tokens": max_tokens, "structured": cell.structured,
                    "temperature": "provider-default"},
        "raw": done.text, "finish_reason": done.finish_reason,
        "usage": {"input_tokens": done.input_tokens, "output_tokens": done.output_tokens,
                  "reasoning_tokens": done.reasoning_tokens},
        "cost_usd": cost, "cost_source": cost_source,
        "latency_s": done.latency_s, "attempts": attempt,
        "response_model": done.response_model, "response_id": done.response_id,
        "provider": done.provider,     # who served the call (OpenRouter names the host)
        "started_at": started_at, "mock": bool(getattr(model, "is_mock", False)),
    }


def generate(manifest: Manifest, cells: list[Cell], models: dict[str, Model],
             archive: RunArchive, calib: Calibration, *, enforce_budget: bool = True,
             stop_after: int | None = None, sleep: Callable[[float], None] = time.sleep,
             log: Callable[[str], None] = print) -> dict[str, Any]:
    """Run every cell that is not in the archive yet. Returns counts.

    Raises `BudgetExceeded` - before the first call if the plan cannot fit under the
    cap, or mid-run as soon as (spent + still-to-run estimate) passes it. Either way
    the archive keeps what was done and the next start resumes from it. The archive is
    held exclusively while this runs (`RunArchive.exclusive`).
    """
    with archive.exclusive():
        return _generate(manifest, cells, models, archive, calib, enforce_budget=enforce_budget,
                         stop_after=stop_after, sleep=sleep, log=log)


def _generate(manifest: Manifest, cells: list[Cell], models: dict[str, Model],
              archive: RunArchive, calib: Calibration, *, enforce_budget: bool,
              stop_after: int | None, sleep: Callable[[float], None],
              log: Callable[[str], None]) -> dict[str, Any]:
    done = archive.load()
    stale = [c.key for c in cells if c.key in done
             and done[c.key]["prompt_sha256"] != c.prompt_sha256]
    if stale:
        raise ManifestError(
            f"{len(stale)} archived cell(s) were made with a different prompt (first: "
            f"{stale[0]}). Prompts changed since this archive was started: use a new run name.")
    pending = [c for c in cells if c.key not in done]
    estimates = {c.key: (cell_estimate(manifest, c, calib)["cost_usd"] or 0.0) for c in pending}
    spent = sum(r.get("cost_usd") or 0.0 for r in done.values())
    budget = Budget(manifest.budget_usd if enforce_budget else math.inf,
                    spent=spent, remaining_estimate=sum(estimates.values()))
    stats = {"planned": len(cells), "already_archived": len(cells) - len(pending),
             "called": 0, "failed": 0, "skipped": 0, "stopped_early": False,
             "spent_usd": spent, "budget_exceeded": None}
    log(f"plan: {len(cells):,} cells, {stats['already_archived']:,} already archived, "
        f"{len(pending):,} to run   (spent so far ${spent:.2f}, still to run "
        f"~${budget.remaining:.2f}, cap ${manifest.budget_usd:.2f})")
    budget.check()  # pre-flight: abort before the first call

    stop = threading.Event()
    state_lock = threading.Lock()
    streak: Counter = Counter()   # consecutive failed cells per (model, condition)
    dropped: set[tuple[str, str]] = set()
    gates = {m: threading.Semaphore(spec.max_concurrency or manifest.per_model_concurrency)
             for m, spec in {c.model.id: c.model for c in pending}.items()}

    def work(cell: Cell) -> None:
        group = (cell.model.id, cell.condition.name)
        with gates[cell.model.id]:
            if stop.is_set() or group in dropped:
                with state_lock:
                    stats["skipped"] += 1
                    budget.remaining -= estimates[cell.key] if group in dropped else 0.0
                return
            try:
                record = call_cell(manifest, cell, models[cell.model.id], sleep)
            except CellFailed as e:
                archive.log_error({"at": _now(), "model": cell.model.id,
                                   "condition": cell.condition.name,
                                   "task_id": cell.task["id"], "sample": cell.sample,
                                   "attempts": e.attempts, "error": str(e)})
                with state_lock:
                    stats["failed"] += 1
                    budget.remaining -= estimates[cell.key]
                    streak[group] += 1
                    if streak[group] >= MAX_CONSECUTIVE_FAILURES and group not in dropped:
                        dropped.add(group)
                        log(f"  {cell.model.id} [{cell.condition.name}]: "
                            f"{MAX_CONSECUTIVE_FAILURES} calls failed in a row ({e}); leaving "
                            "this model and condition for the next start")
                return
            archive.append(cell.model.slug, record)
            with state_lock:
                streak[group] = 0
                stats["called"] += 1
                n = stats["called"]
                if stop_after is not None and n >= stop_after:
                    stats["stopped_early"] = True
                    stop.set()
            try:
                # A call with no known cost is charged at its estimate, never at zero.
                actual = record["cost_usd"]
                budget.charge(estimates[cell.key] if actual is None else actual,
                              estimates[cell.key])
            except BudgetExceeded as e:
                with state_lock:
                    stats["budget_exceeded"] = str(e)
                stop.set()
            if n % 500 == 0:
                log(f"  {n:,}/{len(pending):,} calls   spent ${budget.spent:.2f}")

    with ThreadPoolExecutor(max_workers=manifest.concurrency) as pool:
        for future in [pool.submit(work, c) for c in pending]:
            future.result()
    stats["spent_usd"] = budget.spent
    stats["dropped_models"] = sorted({m for m, _ in dropped})
    stats["dropped"] = sorted(dropped)
    if stats["budget_exceeded"]:
        raise BudgetExceeded(stats["budget_exceeded"] + f" - stopped after {stats['called']:,} "
                             "calls; the archive is intact and the run can be resumed")
    return stats


# --- grading a manifest run -------------------------------------------------------

VALIDATE_CHUNK = 400  # scenes per headless-browser batch


def validate_all(samples: list[dict], mode: str, log: Callable[[str], None] = print) -> bool:
    """Mol*-validate parsed MVS samples in batches. Returns whether validation ran.

    ``mode``: 'required' (fail without Mol*), 'auto' (use it if installed, else leave
    scenes 'unchecked' and say so), 'off'.
    """
    todo = [s for s in samples if s.get("outcome") == "unchecked"]
    if mode == "off" or not todo:
        return mode != "off" and not todo
    try:
        for i in range(0, len(todo), VALIDATE_CHUNK):
            validate_samples(todo[i:i + VALIDATE_CHUNK])
    except Exception as e:  # noqa: BLE001 - narrowed just below
        # Not available: the 'execute' extra or the Mol* bundle is missing (ImportError,
        # RuntimeError), or Playwright is installed without its browser (its own Error
        # class, which is neither). Anything else is a real failure.
        if not (isinstance(e, (ImportError, RuntimeError))
                or type(e).__module__.startswith("playwright")):
            raise
        if mode == "required":
            raise ManifestError(
                "Mol* validation is required (run.validate) but is not available: "
                f"{e}. Install the 'execute' extra, fetch the Mol* bundle and install "
                "Playwright's browser (playwright install chromium).") from e
        log(f"note: Mol* validation unavailable ({type(e).__name__}); parsed scenes stay "
            "'unchecked' and valid-scene rates are not reported")
        return False
    return True


# Outcomes that score 0 because nothing the viewer could show came back.
ZERO_OUTCOMES = ("invalid_json", "not_mvs", "invalid_mvs", "load_failed")


def check_reference(task: dict) -> bool:
    """Grade a task's reference against itself, before any answer to it is graded.
    Raises `GradingError` unless it is exactly right (and, on the API track, graded by
    the final-state grader). Returns whether the grader reports a target score for
    this task."""
    check_gradable(task)
    own = grade_parsed(task, task["reference"])
    if not (own.get("f1") == 1.0 and own.get("success", True) and not own.get("error")):
        raise GradingError(f"task {task['id']}: its own reference does not grade as exactly "
                           f"right (f1 {own.get('f1')}, success {own.get('success')})")
    target = target_score(own)
    if target is not None and target != 1.0:
        raise GradingError(f"task {task['id']}: its own reference has target score {target}")
    return target is not None


def grade_archive(cells: list[Cell], records: dict[tuple, dict], validate: str = "auto",
                  log: Callable[[str], None] = print) -> tuple[dict, bool]:
    """Grade every archived cell of the plan.

    Returns ``({(condition, model id): {task id: [sample, ...]}}, validated)``; each
    sample is the grader's result plus the call's finish reason, tokens and latency,
    and - for an invalid-JSON sample - its json-repair counterfactual. Every task's
    reference is graded against itself first (`check_reference`): a task that cannot
    be graded properly stops the grading, it is never scored some other way.
    """
    graded: dict[tuple, dict] = {}
    has_target: dict[str, bool] = {}
    for c in cells:
        r = records.get(c.key)
        if r is None:
            continue
        tid = c.task["id"]
        if tid not in has_target:
            has_target[tid] = check_reference(c.task)
        s = grade_output(c.task, r["raw"] or "")
        if has_target[tid] and target_score(s) is None:
            # The grader never saw it (unparseable) or could not place it: strict 0,
            # like the score itself. Left None when the grader reports no targets.
            s["target_f1"] = 0.0
        s["sample"] = c.sample
        s["finish_reason"] = r.get("finish_reason")
        s["truncated"] = is_truncated(r)
        s["usage"] = r.get("usage") or {}
        s["latency_s"] = r.get("latency_s")
        s["cost_usd"] = r.get("cost_usd")
        s["_record"] = r
        fixed = repair_counterfactual(c.task, s)
        if fixed:
            s["repair"] = fixed
        graded.setdefault((c.condition.name, c.model.id), {}).setdefault(tid, []).append(s)
    every = [s for per in graded.values() for got in per.values() for s in got]
    crashed = Counter(s["grader_crash"] for s in every if "grader_crash" in s)
    if crashed:
        log(f"WARNING: the grader crashed on {sum(crashed.values()):,} output(s); they score 0 "
            "and carry 'grader_crash'. Fix the grader and re-grade (--grade-only). Most common: "
            + "; ".join(f"{n}x {m}" for m, n in crashed.most_common(3)))
    mvs = [s for s in every if s.get("track", "mvs") == "mvs"]
    repaired = [s["repair"] for s in mvs if "repair" in s]
    validated = validate_all(mvs + repaired, validate, log)
    return graded, validated


def _repaired_f1(s: dict) -> float:
    """The sample's score if json-repair had been applied (its own score if it parsed)."""
    return s["repair"]["f1"] if "repair" in s else s["f1"]


def _track_stats(samples: list[dict], track: str, validated: bool) -> dict[str, Any]:
    """Strict score, task success, target score, validity, truncation and the two
    counterfactual scores of one track's samples."""
    names = OUTCOMES if track == "mvs" else API_OUTCOMES
    outcomes = {o: sum(s.get("outcome") == o for s in samples) for o in names}
    targets = [t for t in map(target_score, samples) if t is not None]
    not_valid = [s for s in samples if s.get("outcome") not in ("valid", "unchecked")]
    out: dict[str, Any] = {
        "n_samples": len(samples),
        "strict_f1": round(statistics.fmean(s["f1"] for s in samples), 4),
        "success": round(statistics.fmean(is_success(s) for s in samples), 4),
        "target_f1": round(statistics.fmean(targets), 4) if targets else None,
        "n_target_samples": len(targets),
        "outcomes": outcomes,
        # Truncation (the provider stopped at the token limit) apart from malformed
        # output: of the samples that are not valid, how many were cut off.
        "n_truncated": sum(is_truncated(s) for s in samples),
        "not_valid": {"truncated": sum(is_truncated(s) for s in not_valid),
                      "malformed": sum(not is_truncated(s) for s in not_valid)},
        "repair_f1": round(statistics.fmean(_repaired_f1(s) for s in samples), 4),
        "n_repaired": sum("repair" in s for s in samples),
        "n_grader_crashes": sum("grader_crash" in s for s in samples),
        "finish_reasons": dict(Counter(str(s.get("finish_reason")) for s in samples)),
    }
    if track == "api_calling" or validated:  # only claim validity that was checked
        valid = [s for s in samples if s.get("outcome") == "valid"]
        out["valid_rate"] = round(len(valid) / len(samples), 4)
        out["valid_f1"] = round(statistics.fmean(s["f1"] for s in valid), 4) if valid else None
    return out


def _sample_summary(s: dict) -> dict[str, Any]:
    out = {"sample": s["sample"], "f1": s["f1"], "outcome": s.get("outcome"),
           "success": is_success(s), "target_f1": target_score(s),
           "finish_reason": s.get("finish_reason"), "truncated": bool(s.get("truncated"))}
    for k in ("error", "mvs_issues", "load_error", "grader_crash", "matched_reference"):
        if s.get(k):
            out[k] = s[k]
    if "repair" in s:
        out["repair"] = {k: s["repair"].get(k) for k in ("f1", "outcome")}
    return out


# What a per-task scorecard entry says about the task itself, so tables can be broken
# down and confidence intervals clustered without opening the corpus again.
TASK_META = ("tier", "family", "structures", "split", "twin_of", "paraphrase_of", "style")


def _group_stats(rows: list[dict]) -> dict[str, Any]:
    """Task-level means of a group of per-task entries (each task counts once)."""
    return {"n_tasks": len(rows),
            "mean_f1": round(statistics.fmean(t["f1"] for t in rows), 4),
            "success": round(statistics.fmean(t["success"] for t in rows), 4),
            "success_all": round(statistics.fmean(t["success_all"] for t in rows), 4),
            "target_f1": (lambda v: round(statistics.fmean(v), 4) if v else None)(
                [t["target_f1"] for t in rows if t["target_f1"] is not None])}


def _breakdown(rows: list[dict], key: str) -> dict[str, dict]:
    groups: dict[str, list[dict]] = {}
    for t in rows:
        groups.setdefault(str(t.get(key)), []).append(t)
    return {name: _group_stats(got) for name, got in sorted(groups.items())}


def model_record(spec: ModelSpec, tasks: list[dict], per_task_samples: dict[str, list[dict]],
                 validated: bool) -> dict[str, Any]:
    """One model's scorecard entry for one condition (same shape as `run` writes, plus
    task success, the target score, per-track validity, truncation and the json-repair
    counterfactual).

    Task success is given two ways everywhere: ``success`` is the mean over tasks of
    the share of a task's samples that are exactly right (the headline), and
    ``success_all`` the share of tasks on which every sample is."""
    per_task = []
    for task in tasks:
        got = per_task_samples.get(task["id"])
        if not got:
            continue
        got = sorted(got, key=lambda s: s["sample"])
        per_task.append({"id": task["id"], "category": task["category"],
                         "categories": task_skills(task),
                         **{k: task.get(k) for k in TASK_META},
                         "cluster": tasks_mod.cluster_key(task),
                         **_aggregate(got),
                         "samples": [_sample_summary(s) for s in got]})
    samples = [s for got in per_task_samples.values() for s in got]
    by_cat = _means_by_category(per_task)
    for cat, d in by_cat.items():
        rows = [t for t in per_task if t["category"] == cat]
        d.update(_track_stats([s for s in samples if s.get("track", "mvs") == cat],
                              cat, validated))
        group = _group_stats(rows)
        d["success_tasks"] = group["success"]
        d["success_all"] = group["success_all"]
        d["target_f1_tasks"] = group["target_f1"]
        d["by_tier"] = _breakdown(rows, "tier")
        d["by_split"] = _breakdown(rows, "split")
    usage = {"input_tokens": sum(s["usage"].get("input_tokens") or 0 for s in samples),
             "output_tokens": sum(s["usage"].get("output_tokens") or 0 for s in samples),
             "reasoning_tokens": sum(s["usage"].get("reasoning_tokens") or 0 for s in samples),
             "calls": len(samples)}
    costs = [s["cost_usd"] for s in samples]
    latency = [s["latency_s"] for s in samples if s.get("latency_s") is not None]
    price = spec.price
    overall = _group_stats(per_task) if per_task else {}
    return {
        "spec": spec.route,
        "open_weights": spec.open_weights,
        "mean_f1": overall.get("mean_f1", 0.0),
        "success": overall.get("success", 0.0),
        "success_all": overall.get("success_all", 0.0),
        "target_f1": overall.get("target_f1"),
        "n_graded": len(per_task),
        "by_category": by_cat,
        "usage": usage,
        "cost_usd": None if any(c is None for c in costs) else round(sum(costs), 6),
        "price": None if price is None else {
            "input": price.input, "output": price.output, "source": price.source,
            "date": price.date, "verified": price.verified},
        "wall_seconds": round(sum(latency), 2),
        "sec_per_call": round(statistics.fmean(latency), 2) if latency else None,
        "by_skill": _means_by_skill(per_task),
        **_format_stats(per_task_samples),
        "tasks": per_task,
    }


def write_scorecards(manifest: Manifest, cells: list[Cell], graded: dict, validated: bool,
                     out_dir: pathlib.Path, meta: dict[str, Any]) -> list[pathlib.Path]:
    """One scorecard per (condition, model): ``<out>/<condition>/<model>.json``."""
    planned: dict[tuple, set] = {}
    for c in cells:
        planned.setdefault((c.condition.name, c.model.id), set()).add((c.task["id"], c.sample))
    specs = {c.model.id: c.model for c in cells}
    by_cond: dict[str, dict[str, dict]] = {}  # condition -> its tasks, in corpus order
    for c in cells:
        by_cond.setdefault(c.condition.name, {}).setdefault(c.task["id"], c.task)
    task_order = {cond: list(tasks.values()) for cond, tasks in by_cond.items()}
    written = []
    for (cond_name, model_id), per_task in sorted(graded.items()):
        cond = manifest.condition(cond_name)
        spec = specs[model_id]
        n_done = sum(len(v) for v in per_task.values())
        n_plan = len(planned[(cond_name, model_id)])
        card = {
            "n_tasks": len(task_order[cond_name]),
            "samples": manifest.samples,
            "meta": {**meta, "condition": cond.prompt, "condition_name": cond_name,
                     "grounding": cond.grounding, "structured": cond.structured,
                     "models": [spec.route], "validate": validated,
                     "cells_planned": n_plan, "cells_archived": n_done,
                     "complete": n_done == n_plan},
            "models": {model_id: model_record(spec, task_order[cond_name], per_task, validated)},
        }
        path = out_dir / cond_name / f"{spec.slug}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(card, indent=2), encoding="utf-8")
        written.append(path)
    return written


# Every field of a per-sample record (``results/<run>/samples/<condition>/<model>.jsonl``).
SAMPLE_RECORD_FIELDS = (
    "run", "model", "route", "condition", "task_id", "sample", "track", "tier", "split",
    "structures", "raw", "predicted", "f1", "precision", "recall", "success", "target_f1",
    "outcome", "error", "grader", "matched_reference", "finish_reason", "truncated",
    "input_tokens", "output_tokens", "reasoning_tokens", "cost_usd", "cost_source",
    "latency_s", "temperature", "max_tokens", "structured", "provider", "response_model",
    "prompt_sha256", "task_sha256", "repair")


def sample_record(cell: Cell, s: dict) -> dict[str, Any]:
    """Everything known about one sample, call and grade together: the text the model
    returned, what was parsed from it, its scores and outcome, and how the call went."""
    r = s.get("_record") or {}
    usage, request = r.get("usage") or {}, r.get("request") or {}
    task = cell.task
    out = {
        "run": r.get("run"), "model": cell.model.id, "route": cell.model.route,
        "condition": cell.condition.name, "task_id": task["id"], "sample": cell.sample,
        "track": task["category"], "tier": task.get("tier"), "split": task.get("split"),
        "structures": task.get("structures"),
        "raw": r.get("raw"), "predicted": s.get("predicted"),
        "f1": s["f1"], "precision": s.get("precision"), "recall": s.get("recall"),
        "success": is_success(s), "target_f1": target_score(s),
        "outcome": s.get("outcome"),
        "error": s.get("error") or s.get("mvs_issues") or s.get("load_error"),
        "grader": s.get("grader"), "matched_reference": s.get("matched_reference"),
        "finish_reason": r.get("finish_reason"), "truncated": is_truncated(r),
        "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": usage.get("reasoning_tokens"),
        "cost_usd": r.get("cost_usd"), "cost_source": r.get("cost_source"),
        "latency_s": r.get("latency_s"),
        "temperature": request.get("temperature"), "max_tokens": request.get("max_tokens"),
        "structured": request.get("structured"),
        "provider": r.get("provider"), "response_model": r.get("response_model"),
        "prompt_sha256": r.get("prompt_sha256"), "task_sha256": r.get("task_sha256"),
        "repair": ({k: s["repair"].get(k) for k in ("f1", "outcome")} if "repair" in s else None),
    }
    assert tuple(out) == SAMPLE_RECORD_FIELDS
    return out


def write_sample_records(cells: list[Cell], graded: dict,
                         out_dir: pathlib.Path) -> list[pathlib.Path]:
    """One JSON line per graded sample: ``<out>/samples/<condition>/<model>.jsonl``, in
    plan order. Rebuilt from the archive on every grading, like the scorecards."""
    lines: dict[pathlib.Path, list[str]] = {}
    index = {(cond, model, tid, s["sample"]): s for (cond, model), per in graded.items()
             for tid, got in per.items() for s in got}
    for c in cells:
        s = index.get((c.condition.name, c.model.id, c.task["id"], c.sample))
        if s is None:
            continue
        path = out_dir / "samples" / c.condition.name / f"{c.model.slug}.jsonl"
        lines.setdefault(path, []).append(json.dumps(sample_record(c, s), ensure_ascii=False))
    for path, rows in lines.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return sorted(lines)


def print_run_summary(manifest: Manifest, out_dir: pathlib.Path, graded: dict) -> None:
    print(f"\nScorecards ({manifest.name}): strict F1 / task success (mean over samples), "
          "per condition")
    conds = [c.name for c in manifest.conditions if any(k[0] == c.name for k in graded)]
    rows: dict[str, dict] = {}
    for (cond, model_id), per_task in graded.items():
        samples = [s for got in per_task.values() for s in got]
        rows.setdefault(model_id, {})[cond] = (
            statistics.fmean(statistics.fmean(s["f1"] for s in got) for got in per_task.values()),
            statistics.fmean(is_success(s) for s in samples))
    w = max([len(m) for m in rows] + [5])
    print(f"{'model':<{w}}  " + "  ".join(f"{c:>17}" for c in conds))
    for model_id, per in rows.items():
        print(f"{model_id:<{w}}  " + "  ".join(
            f"{'%.3f / %.3f' % per[c] if c in per else '-':>17}" for c in conds))
    print(f"\nscorecards -> {out_dir}")


# --- the manifest command ---------------------------------------------------------

DRYRUN_MARK = "DRYRUN"
# Tiny tasks of every kind the final corpus has (tests/fixtures/build_fixture_tasks.py).
# A dry run adds them when the corpus on disk lacks one of these kinds, so the whole
# path is rehearsed before the real tasks exist. They are never part of a real run.
FIXTURE_TASKS = REPO / "tests" / "fixtures" / "tasks"
TASK_KINDS = {
    "follow-up": lambda t: bool(t.get("context")),
    "follow-up with no change": lambda t: bool(t.get("context")) and t["context"]["noop"],
    "accept-set": lambda t: bool(t.get("accepted")),
    "twin": lambda t: bool(t.get("twin_of")),
    "paraphrase": lambda t: bool(t.get("paraphrase_of")),
    "held-back": lambda t: t.get("split") == "heldback",
}


def kinds_present(tasks: list[dict]) -> dict[str, dict[str, int]]:
    """How many tasks of each special kind there are, per track."""
    return {kind: {track: sum(test(t) for t in tasks if t["category"] == track)
                   for track in manifest_mod.TRACKS}
            for kind, test in TASK_KINDS.items()}


def with_fixtures(tasks: list[dict]) -> tuple[list[dict], int]:
    """The corpus, plus the fixture tasks if it lacks any special kind on any track.
    Returns ``(tasks, number of fixtures added)``."""
    if all(n for per in kinds_present(tasks).values() for n in per.values()):
        return tasks, 0
    if not FIXTURE_TASKS.is_dir():
        return tasks, 0
    fixtures = tasks_mod.load_corpus(FIXTURE_TASKS, repo=REPO)
    for t in fixtures:
        t["_fixture"] = True
    return tasks + fixtures, len(fixtures)


def _load_script(name: str):
    """Import ``scripts/<name>.py`` (the site builders are scripts, not a package)."""
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def build_site(results_dir: pathlib.Path, archive_dir: pathlib.Path,
               site_dir: pathlib.Path, extra_tasks: pathlib.Path | None = None) -> None:
    """Derive the leaderboard's data files and pages from a manifest run.
    ``extra_tasks``: a task directory besides ``tasks/`` (a dry run's fixtures)."""
    site_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / "docs" / "style.css", site_dir / "style.css")
    _load_script("build_site_data").main(
        ["--run", str(results_dir), "--runs", str(archive_dir), "--docs", str(site_dir)]
        + (["--extra-tasks", str(extra_tasks)] if extra_tasks else []))
    _load_script("build_leaderboard").build(site_dir / "scorecard.json", out_dir=site_dir)


def _mock_panel(panel: list[ModelSpec], calib: Calibration, seed: int) -> dict[str, Model]:
    return {m.id: MockModel(m.id, seed=seed,
                            chars_per_input_token=calib.rates(m).chars_per_input_token)
            for m in panel}


def _fresh_dryrun_dir(path: pathlib.Path) -> None:
    """Start a dry run's directory from empty. Only ever deletes a directory that a
    dry run made (it carries the marker file)."""
    if path.exists():
        if not (path / DRYRUN_MARK).exists():
            raise ManifestError(f"{path} exists and is not a dry-run directory; not touching it")
        shutil.rmtree(path)
    path.mkdir(parents=True)
    (path / DRYRUN_MARK).write_text("mock data from a dry run; safe to delete\n")


def run_meta(manifest: Manifest, corpus_sha: str, mock: bool, archive_dir: pathlib.Path,
             lock: dict) -> dict[str, Any]:
    try:
        cells_rel = str(archive_dir.relative_to(REPO))
    except ValueError:
        cells_rel = str(archive_dir)
    return {"run_name": manifest.name, "run_id": f"{manifest.name}:{lock['created_at']}",
            "started_at": lock["created_at"], "graded_at": _now(),
            "git_commit": _git_commit(), "manifest": str(manifest.path),
            "panel_rule": manifest.panel_rule,
            "manifest_sha256": manifest.sha256, "corpus_version": manifest.corpus_version,
            "corpus_sha256": corpus_sha, "mock": mock, "archive": cells_rel,
            "escalate": False, "judge": None}


def dry_run(manifest: Manifest, panel: list[ModelSpec], tasks: list[dict], corpus_sha: str,
            calib: Calibration, runs_dir: pathlib.Path, results_dir: pathlib.Path,
            seed: int = 0, site: bool = True) -> bool:
    """The whole pipeline at $0 with the mock model: plan, generate (interrupted half
    way, then resumed), archive, grade, scorecards, per-sample records, site build, and
    the cost of the real run. Returns whether every check passed.

    Follow-up, accept-set, twin, paraphrase and held-back tasks must all pass through
    it; when the corpus on disk has none of some kind the fixture tasks are added
    (`with_fixtures`). Fixtures are left out of the cost projection."""
    archive_dir = runs_dir / f"{manifest.name}.dryrun"
    out_dir = results_dir / f"{manifest.name}.dryrun"
    _fresh_dryrun_dir(archive_dir)
    _fresh_dryrun_dir(out_dir)
    n_corpus = len(tasks)
    tasks, n_fixtures = with_fixtures(tasks)
    cells = build_plan(manifest, tasks, panel)
    models = _mock_panel(panel, calib, seed)
    archive = RunArchive(archive_dir)
    lock = archive.open(manifest, corpus_sha, mock=True, argv=sys.argv[1:])
    checks: list[tuple[str, bool, str]] = []

    print(f"DRY RUN  {manifest.name}: {len(panel)} models x {len(manifest.conditions)} "
          f"conditions, {n_corpus} tasks"
          + (f" + {n_fixtures} fixture tasks (tests/fixtures/tasks)" if n_fixtures else "")
          + f", {manifest.samples} sample(s) -> {len(cells):,} "
          "cells, all answered by the mock model ($0)")
    planned_tasks = list({c.task["id"]: c.task for c in cells}.values())
    kinds = kinds_present(planned_tasks)
    checks.append(("the plan has follow-up (one with no change), accept-set, twin, paraphrase "
                   "and held-back tasks on both tracks",
                   all(n for per in kinds.values() for n in per.values()),
                   "; ".join(f"{k}: {per['mvs']} MVS, {per['api_calling']} API"
                             for k, per in kinds.items())))
    follow = [c for c in cells if c.task.get("context")]
    shown = all(json.dumps(start_state(c.task), separators=(",", ":")) in c.user
                and c.user.rstrip().split("Request: ")[-1].startswith(c.task["prompt"])
                for c in follow)
    checks.append(("a follow-up request shows the model the start state, then the request",
                   bool(follow) and shown, f"{len(follow):,} follow-up cells"))
    half = max(1, len(cells) // 2)
    first = generate(manifest, cells, models, archive, calib, enforce_budget=False,
                     stop_after=half)
    n_after_first = len(archive.load())
    checks.append(("interrupted run stops early and keeps its archive",
                   first["stopped_early"] and half <= n_after_first < len(cells),
                   f"{n_after_first:,} of {len(cells):,} cells archived"))
    archive.open(manifest, corpus_sha, mock=True, argv=sys.argv[1:])
    second = generate(manifest, cells, models, archive, calib, enforce_budget=False)
    checks.append(("resume runs only the missing cells",
                   second["already_archived"] == n_after_first
                   and second["called"] == len(cells) - n_after_first,
                   f"skipped {second['already_archived']:,}, ran {second['called']:,}"))
    third = generate(manifest, cells, models, archive, calib, enforce_budget=False)
    records = archive.load()
    checks.append(("a finished run makes no further calls",
                   third["called"] == 0 and len(records) == len(cells),
                   f"{len(records):,} cells archived"))
    try:
        with RunArchive(archive_dir).exclusive(), archive.exclusive():
            refused = False
    except ManifestError:
        refused = True
    checks.append(("a second run on the same archive is refused while one holds it",
                   refused, str(archive_dir / "LOCK")))
    need = ("raw", "usage", "finish_reason", "latency_s", "prompt_sha256", "task_sha256",
            "provider")
    complete = all(all(k in r and r[k] is not None for k in need)
                   and r["usage"].get("input_tokens") is not None
                   and r["request"].get("max_tokens") and r["request"].get("temperature")
                   for r in records.values())
    hashes_ok = all(records[c.key]["prompt_sha256"] == c.prompt_sha256 for c in cells)
    checks.append(("every cell archives raw text, tokens, latency, finish reason, token "
                   "limit, serving provider, prompt hash",
                   complete and hashes_ok, f"{len(records):,} records checked"))

    graded, validated = grade_archive(cells, records, "auto" if manifest.validate != "off" else "off")
    every = [s for per in graded.values() for got in per.values() for s in got]
    seen = Counter((s.get("track", "mvs"), s.get("outcome")) for s in every)
    want = [("mvs", "invalid_json"), ("mvs", "not_mvs"), ("api_calling", "valid"),
            ("api_calling", "invalid_json"), ("api_calling", "invalid_api")]
    want += [("mvs", "valid"), ("mvs", "invalid_mvs")] if validated else [("mvs", "unchecked")]
    present_tracks = {c.task["category"] for c in cells}
    want = [w for w in want if w[0] in present_tracks]
    checks.append(("grading meets every outcome class", all(seen[w] for w in want),
                   ", ".join(f"{t}:{o}={n}" for (t, o), n in sorted(seen.items()))))
    api = [s for s in every if s.get("track") == "api_calling"]
    checks.append(("every API answer that parsed was graded by the final-state grader",
                   all(s.get("grader") == "state" for s in api
                       if s.get("outcome") != "invalid_json" and "grader_crash" not in s),
                   f"{len(api):,} API samples"))
    alt = [s for s in every if s.get("matched_reference") and is_success(s)]
    checks.append(("an accepted alternative answer counts as exactly right", bool(alt),
                   f"{len(alt):,} samples matched an alternative"))
    cut = [s for s in every if s.get("truncated")]
    checks.append(("truncated output (finish reason 'length') is counted apart from malformed",
                   bool(cut) and any(not s.get("truncated") and s.get("outcome") == "invalid_json"
                                     for s in every),
                   f"{len(cut):,} truncated, "
                   f"{sum(s.get('outcome') == 'invalid_json' and not s.get('truncated') for s in every):,}"
                   " malformed-JSON samples"))
    checks.append(("json-repair counterfactual recorded for invalid JSON",
                   any("repair" in s for s in every),
                   f"{sum('repair' in s for s in every):,} of "
                   f"{sum(s.get('outcome') == 'invalid_json' for s in every):,} invalid-JSON "
                   "samples repairable"))
    written = write_scorecards(manifest, cells, graded, validated, out_dir,
                               run_meta(manifest, corpus_sha, True, archive_dir, lock))
    checks.append(("a scorecard per model and condition",
                   len(written) == len({(c.condition.name, c.model.id) for c in cells}),
                   f"{len(written)} files"))
    cards = [next(iter(json.loads(f.read_text(encoding="utf-8"))["models"].values()))
             for f in written]
    api_cards = [m["by_category"]["api_calling"] for m in cards
                 if "api_calling" in m["by_category"]]
    checks.append(("scorecards carry task success both ways, the split and tier breakdown and "
                   "the API valid-output rate",
                   all("success" in m and "success_all" in m and "target_f1" in m for m in cards)
                   and all({"by_tier", "by_split", "not_valid"} <= set(d)
                           for m in cards for d in m["by_category"].values())
                   and bool(api_cards) == ("api_calling" in present_tracks)
                   and all(d.get("valid_rate") is not None for d in api_cards),
                   f"{len(cards)} scorecards"))
    sample_files = write_sample_records(cells, graded, out_dir)
    n_lines = 0
    fields_ok = True
    for f in sample_files:
        for line in f.read_text(encoding="utf-8").splitlines():
            n_lines += 1
            fields_ok = fields_ok and tuple(json.loads(line)) == SAMPLE_RECORD_FIELDS
    checks.append(("a per-sample record for every cell, with every field",
                   n_lines == len(cells) and fields_ok,
                   f"{n_lines:,} records in {len(sample_files)} files"))
    targets = sum(target_score(s) is not None for s in every)
    print_run_summary(manifest, out_dir, graded)
    if site:
        try:
            build_site(out_dir, archive_dir, out_dir / "site",
                       FIXTURE_TASKS if n_fixtures else None)
            ok = all((out_dir / "site" / f).exists() for f in
                     ("scorecard.json", "conditions_data.json", "failures_data.json",
                      "index.html", "failures.html"))
            checks.append(("site data and leaderboard pages build from the run", ok,
                           str(out_dir / "site")))
        except Exception as e:  # noqa: BLE001 - a dry run reports every broken stage
            checks.append(("site data and leaderboard pages build from the run", False,
                           f"{type(e).__name__}: {e}"))

    real = [c for c in cells if not c.task.get("_fixture")]
    totals = print_projection(manifest, project_costs(manifest, real, calib))
    core = totals["core"]
    checks.append(("projected cost of the core panel is within the budget cap",
                   core <= manifest.budget_usd, f"${core:.2f} vs cap ${manifest.budget_usd:.2f}"
                   + (f"; the {n_fixtures} fixture tasks are not counted" if n_fixtures else "")))
    unpriced = [m.id for m in panel if m.price is None]
    checks.append(("every model has a price", not unpriced, ", ".join(unpriced) or "all priced"))

    print("\nDry-run checks")
    for label, ok, detail in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {label}  ({detail})")
    notes = []
    if n_fixtures:
        notes.append(f"{n_fixtures} fixture tasks were added: the corpus on disk has no task of "
                     "some kind yet (follow-up, accept-set, twin, paraphrase, held-back)")
    if not targets:
        notes.append("the grader reports no target score yet (target_f1): the target columns "
                     "are empty")
    if not grader_grades_mvs():
        notes.append("MVS scenes were graded by mvs.grade_mvs (grader.grade_task does not grade "
                     "the MVS track yet); success there is 'F1 = 1'")
    if not validated and "mvs" in present_tracks:
        notes.append("Mol* validation did not run here: MVS scenes are 'unchecked', not 'valid'")
    if not manifest.corpus_sha256:
        notes.append(f"corpus hash is not pinned in the manifest (on disk: {corpus_sha})")
    unverified = [m.id for m in panel if m.price is not None and not m.price.verified]
    if unverified:
        notes.append("unverified prices: " + ", ".join(unverified))
    for n in notes:
        print(f"  note: {n}")
    return all(ok for _, ok, _ in checks)


KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
           "openrouter": "OPENROUTER_API_KEY", "gemini": "GEMINI_API_KEY",
           "google": "GEMINI_API_KEY"}


def preflight(manifest: Manifest, panel: list[ModelSpec]) -> list[str]:
    """Reasons a paid run cannot finish, found before the first call: a missing API
    key, or Mol* validation required but not installed."""
    problems = []
    for env in sorted({KEY_ENV[p] for p in (m.route.split(":")[0] for m in panel)
                       if p in KEY_ENV}):
        if not os.environ.get(env):
            problems.append(f"{env} is not set")
    if manifest.validate == "required" and any("mvs" in c.tracks for c in manifest.conditions):
        from . import render
        if importlib.util.find_spec("playwright") is None:
            problems.append("run.validate = \"required\" but playwright is not installed "
                            "(uv sync --extra execute; playwright install chromium)")
        if not (render.STATIC / "molstar" / "molstar.js").exists():
            problems.append("run.validate = \"required\" but the Mol* bundle is missing "
                            "(python scripts/fetch_molstar.py)")
    return problems


def manifest_main(args: argparse.Namespace) -> int:
    manifest = manifest_mod.load_manifest(args.manifest)
    calib = Calibration.load(args.calibration)
    runs_dir = pathlib.Path(args.runs_dir) if args.runs_dir else RUNS_DIR
    results_dir = pathlib.Path(args.results_dir) if args.results_dir else RESULTS_DIR
    tasks = [t for t in load_tasks(list(manifest_mod.TRACKS))]

    if args.dry_run:
        corpus_sha = manifest_mod.check_corpus(manifest, TASKS_DIR, strict=False)
        panel = manifest.panel(include_optional=not args.core_only, only=args.only_models)
        ok = dry_run(manifest, panel, tasks, corpus_sha, calib, runs_dir, results_dir,
                     seed=args.seed, site=not args.no_site)
        print("\nDRY RUN " + ("PASSED" if ok else "FAILED"))
        return 0 if ok else 1

    panel = manifest.panel(include_optional=args.include_optional, only=args.only_models)
    archive_dir = runs_dir / manifest.name
    out_dir = results_dir / manifest.name
    cells = build_plan(manifest, tasks, panel)
    archive = RunArchive(archive_dir)

    if args.grade_only:
        corpus_sha = manifest_mod.check_corpus(manifest, TASKS_DIR, strict=False)
        lock = json.loads((archive_dir / "run.json").read_text(encoding="utf-8"))
        if lock["corpus_sha256"] != corpus_sha:
            raise ManifestError("the corpus on disk is not the corpus this archive was run on")
    else:
        print_projection(manifest, project_costs(manifest, cells, calib))
        if not args.go:
            print("\nNo model was called. This was the plan and its projected cost; add --go "
                  "to start the paid run, or --dry-run to rehearse it for $0.")
            return 0
        corpus_sha = manifest_mod.check_corpus(manifest, TASKS_DIR, strict=True)
        unpriced = [m.id for m in panel if m.price is None]
        if unpriced:
            raise ManifestError("no price for: " + ", ".join(unpriced) + ". The budget cap "
                                "cannot be enforced without one.")
        unverified = [m.id for m in panel if not m.price.verified]
        if unverified and not args.allow_unverified_prices:
            raise ManifestError("unverified price for: " + ", ".join(unverified) + ". Verify "
                                "them in the manifest, or pass --allow-unverified-prices.")
        load_dotenv()
        problems = preflight(manifest, panel)
        if problems:
            raise ManifestError("cannot start the run: " + "; ".join(problems))
        try:
            with archive.exclusive():  # refuses a second start on the same archive
                lock = archive.open(manifest, corpus_sha, mock=False, argv=sys.argv[1:])
                models = {m.id: build_model(m.route) for m in panel}
                stats = generate(manifest, cells, models, archive, calib)
        except BudgetExceeded as e:
            print(f"\nBUDGET ABORT: {e}", file=sys.stderr)
            return 3
        print(f"generate: {stats['called']:,} calls made, {stats['failed']:,} failed, "
              f"spent ${stats['spent_usd']:.2f}")
        if stats["failed"]:
            print(f"{stats['failed']:,} cell(s) failed after every retry (see "
                  f"{archive_dir / 'errors.jsonl'}). Run the same command again to retry "
                  "them; grading what is archived so far.", file=sys.stderr)

    records = archive.load()
    graded, validated = grade_archive(cells, records, manifest.validate)
    written = write_scorecards(manifest, cells, graded, validated, out_dir,
                               run_meta(manifest, corpus_sha, False, archive_dir, lock))
    write_sample_records(cells, graded, out_dir)
    print_run_summary(manifest, out_dir, graded)
    missing = len(cells) - sum(c.key in records for c in cells)
    if missing:
        print(f"INCOMPLETE: {missing:,} of {len(cells):,} cells are not archived yet.",
              file=sys.stderr)
    if not args.no_site and written:
        build_site(out_dir, archive_dir, out_dir / "site")
    return 2 if missing else 0


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
    g = ap.add_argument_group("manifest run (the benchmark)")
    g.add_argument("--manifest", default=None,
                   help="run everything the manifest names, e.g. run/final_run.toml. "
                        "Without --go or --dry-run it only prints the plan and its cost")
    g.add_argument("--dry-run", action="store_true",
                   help="rehearse the whole manifest with the mock model: $0, no network")
    g.add_argument("--go", action="store_true",
                   help="make the real (paid) model calls. Resumable: archived cells are skipped")
    g.add_argument("--grade-only", action="store_true",
                   help="re-grade the existing archive and rewrite the scorecards; no calls")
    g.add_argument("--include-optional", action="store_true",
                   help="also run the models the manifest marks optional")
    g.add_argument("--core-only", action="store_true",
                   help="dry run: leave the optional models out (they are in by default)")
    g.add_argument("--only-models", nargs="+", default=None, metavar="ID",
                   help="restrict the run to these manifest model ids")
    g.add_argument("--allow-unverified-prices", action="store_true",
                   help="start a paid run although some manifest prices are unverified")
    g.add_argument("--calibration", default=None,
                   help="token calibration file (default run/token_calibration.json)")
    g.add_argument("--runs-dir", default=None, help="where archives go (default runs/)")
    g.add_argument("--results-dir", default=None, help="where scorecards go (default results/)")
    g.add_argument("--no-site", action="store_true", help="skip the site-data build")
    g.add_argument("--seed", type=int, default=0, help="mock-model seed for --dry-run")
    ap.add_argument("--models", nargs="+", default=["baseline"],
                    help="model specs: baseline | anthropic:<id> | openai:<id>")
    ap.add_argument("--categories", nargs="*", default=None,
                    help="filter tasks, e.g. mvs api_calling visual_rubric")
    ap.add_argument("--samples", type=int, default=1,
                    help="runs per task (>1 to average out LLM sampling noise)")
    ap.add_argument("--escalate", action="store_true",
                    help="render imperfect MVS predictions for a visual-diff (+VLM) "
                         "cross-check; needs the 'execute' extra")
    ap.add_argument("--judge", default=None,
                    help="vision model id for the T2 VLM tier (e.g. claude-opus-4-8); "
                         "off by default (T0/T1 only)")
    ap.add_argument("--condition", choices=CONDITIONS, default="spec",
                    help="MVS prompting condition: 'spec' (with the MVS reference) or "
                         "'bare' (output contract only)")
    ap.add_argument("--validate", action="store_true",
                    help="check every parsed MVS scene with Mol*'s own validator (needs the "
                         "'execute' extra); scenes Mol* rejects score 0. Implied by --escalate")
    ap.add_argument("--grounding", action="store_true",
                    help="append each task's frozen grounding pack (facts about its "
                         "structures) to the user message; tasks without one run unchanged")
    ap.add_argument("--out", default=str(RESULTS_DIR / "scorecard.json"))
    # Removed on purpose. Kept as a recognised flag only so that an old command line
    # fails with the reason instead of "unrecognized arguments".
    ap.add_argument("--no-archive", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.no_archive:
        ap.error("--no-archive was removed: every run is archived (raw outputs are the "
                 "only record a result can be re-graded or audited from)")

    if args.manifest:
        try:
            sys.exit(manifest_main(args))
        except (ManifestError, GradingError, tasks_mod.TaskError) as e:
            sys.exit(f"error: {e}")
    if args.dry_run or args.go or args.grade_only:
        ap.error("--dry-run, --go and --grade-only need --manifest")

    load_dotenv()  # make keys in .env available before any model is built
    report, raw_samples = run(args.models, args.categories, samples=args.samples,
                              escalate=args.escalate, judge=args.judge,
                              condition=args.condition, grounding=args.grounding,
                              validate=args.validate)
    RESULTS_DIR.mkdir(exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(report, indent=2))
    print_scorecard(report)
    print(f"\nfull results -> {args.out}")

    # Archive the full run (incl. raw outputs + all samples) under a timestamped,
    # never-overwritten file, so any run can be drilled into later. The published
    # scorecard stays lightweight; this is the forensic copy.
    RUNS_DIR.mkdir(exist_ok=True)
    archive_path = _new_archive_path()
    archive_path.write_text(json.dumps({**report, "raw_samples": raw_samples}, indent=2))
    print(f"archived -> {archive_path}")


def _new_archive_path() -> pathlib.Path:
    """``runs/run_<UTC stamp>.json``, claimed atomically. Runs started in parallel can
    finish in the same second; the later one gets a ``-2``, ``-3``... suffix rather
    than overwriting the first (which once lost a whole run's raw outputs)."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for n in itertools.count(1):
        path = RUNS_DIR / (f"run_{stamp}.json" if n == 1 else f"run_{stamp}-{n}.json")
        try:
            path.open("x").close()
            return path
        except FileExistsError:
            continue


if __name__ == "__main__":
    main()
