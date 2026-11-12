"""
The task format: one schema for every task of the final corpus, checked at load.

``TASK_FORMAT.md`` is the prose version of this module; the two must agree. A task is
one JSON file under ``tasks/``. ``load_corpus()`` reads them all, validates each
against the schema and returns plain dicts. Files written before the format existed
(no ``track`` key) are read through ``adapt_legacy`` and marked ``_legacy``; the final
corpus has none (``scripts/validate_tasks.py --final`` refuses them).

``check_corpus()`` holds the checks that need the whole corpus, the structure panel
or the grader: unique ids, twin and paraphrase links, every structure in the panel
with an atom table, every reference grading itself as exactly right, follow-up start
states consistent with their references, and the API prompt's worked example (1HSG)
unused. Nothing here touches the network.

A loaded task also carries the names older code reads, so it keeps working:
``category`` (``"mvs"`` | ``"api_calling"``), ``categories`` (= ``skills``) and, on the
MVS track, ``reference_mvs`` (= ``reference``) and ``accepted_ids``
(= ``accepted_structures``). Keys starting with ``_`` are loader bookkeeping.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Callable, Iterable

from . import schema
from .atoms import load_table

REPO = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = REPO / "tasks"

FORMAT_VERSION = 1
TRACKS = ("mvs", "api")
# The name each track has in scorecards, manifests and older code.
CATEGORY = {"mvs": "mvs", "api": "api_calling"}
TRACK_OF = {v: k for k, v in CATEGORY.items()}
TIERS = ("translation", "grounded", "interactions", "resolve", "clinical", "followup",
         "accept_set", "tool_only")
# Tiers whose answer needs a fact looked up outside the request (FINAL_PLAN decision
# 10): the only ones the grounding-pack condition runs on.
LOOKUP_TIERS = ("resolve", "clinical")
STYLES = ("full", "terse", "indirect")
SPLITS = ("public", "heldback")
# The structure of the API prompt's worked example. No task may use it (decision 10).
WORKED_EXAMPLE = "1hsg"

REQUIRED = ("id", "track", "tier", "family", "structures", "prompt", "reference",
            "accepted", "context", "target", "twin_of", "paraphrase_of", "style", "split",
            "grounding", "provenance", "skills")
OPTIONAL = ("title", "notes", "accepted_structures", "accepted_targets")
PROVENANCE_KEYS = ("script", "inputs", "date", "checks")
TARGET_KEYS = ("selector", "representation", "color", "structure")
CONTEXT_STATE = {"mvs": "scene", "api": "calls"}

# How an old file's ``source`` maps to a tier. Old API tasks had no tier.
LEGACY_TIER = {
    None: "translation", "curated": "translation", "generated": "translation",
    "grounded": "grounded", "interactions": "interactions", "resolve": "resolve",
    "clinvar-variant": "clinical", "clinvar-hotspots": "clinical", "sifts-named": "clinical",
}
LEGACY_API_TIER = "unclassified"

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_DATE = re.compile(r"\d{4}-\d\d-\d\d")
_PDB_ID = re.compile(r"(?:pdb_0000)?([0-9][a-z0-9]{3})")
_AF_URL = re.compile(r"AF-([A-Za-z0-9]+)-F(\d+)", re.I)
_PDB_URL = re.compile(
    r"/(?:pdb)?([0-9][A-Za-z0-9]{3})(?:_updated|-assembly\d+)?\.(?:b?cif|pdb|ent)(?:\.gz)?(?:[?#].*)?$")


class TaskError(ValueError):
    """A task file, or the corpus, breaks the format. The message names the file."""


# --------------------------------------------------------------------------- #
# What a reference loads
# --------------------------------------------------------------------------- #
def _entry_of_url(url: str) -> str | None:
    m = _AF_URL.search(url)
    if m:
        return f"af-{m.group(1).lower()}-f{m.group(2)}"
    m = _PDB_URL.search(url)
    return m.group(1).lower() if m else None


def scene_root(scene: Any) -> dict | None:
    """The root node of an MVS scene given as a state, a ``{"root": ...}`` wrapper or a
    bare root node."""
    if not isinstance(scene, dict):
        return None
    if scene.get("kind") == "root":
        return scene
    root = scene.get("root")
    return root if isinstance(root, dict) and root.get("kind") == "root" else None


def loaded_entries(track: str, state: Any) -> list[str]:
    """The structure entries a scene or call list loads, in order of first use: a
    lower-case PDB id, or ``af-<accession>-f<n>`` for an AlphaFold DB model. Anything
    else (a UniProt accession in the superposition view, another URL) is left out."""
    out: list[str] = []

    def add(entry: str | None) -> None:
        if entry and entry not in out:
            out.append(entry)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            params = node.get("params")
            if node.get("kind") == "download" and isinstance(params, dict):
                add(_entry_of_url(str(params.get("url", ""))))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    if track == "mvs":
        walk(state)
        return out
    superposed = any(isinstance(a, dict) and a.get("action") == "set_property"
                     and a.get("name") == "superposition" and a.get("value")
                     for a in state or [])
    for act in state or []:
        if not isinstance(act, dict) or act.get("action") != "load":
            continue
        custom = act.get("custom_data")
        if isinstance(custom, dict) and custom.get("url"):
            add(_entry_of_url(str(custom["url"])))
        elif isinstance(act.get("molecule_id"), str) and not superposed:
            m = _PDB_ID.fullmatch(act["molecule_id"].strip().lower())
            add(m.group(1) if m else None)
    return out


def panel_ids() -> set[str]:
    from . import grounding
    return {e["id"].lower() for e in grounding.panel()["entries"]}


def resolve_entry(entry: str, known: Iterable[str]) -> str | None:
    """The panel id an entry means: itself, or - for an AlphaFold model named without
    its file version - the one frozen version of it."""
    known = set(known)
    if entry in known:
        return entry
    hits = sorted(k for k in known if k.startswith(entry + "-"))
    return hits[0] if len(hits) == 1 else None


def table_for(entry: str):
    """The frozen atom table of a panel entry (AlphaFold ids resolved as above)."""
    table = load_table(entry)
    if table is None and entry.startswith("af-"):
        from .atoms import TABLES
        hits = sorted(TABLES.glob(f"{entry}-*.json.gz"))
        if len(hits) == 1:
            table = load_table(hits[0].name[:-len(".json.gz")])
    return table


def has_table(entry: str) -> bool:
    """Whether a frozen atom table exists for the entry (without reading it)."""
    from .atoms import TABLES
    if (TABLES / f"{entry.lower()}.json.gz").exists():
        return True
    return entry.startswith("af-") and len(list(TABLES.glob(f"{entry}-*.json.gz"))) == 1


def cluster_key(task: dict) -> str:
    """What confidence intervals are clustered on: the task's first structure (its own
    id when it loads none)."""
    return task["structures"][0] if task.get("structures") else f"task:{task['id']}"


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
def _state_errors(track: str, state: Any, what: str) -> list[str]:
    """Why a scene / call list is not a well-formed answer of its track."""
    if track == "mvs":
        root = scene_root(state)
        if root is None:
            return [f"{what}: not an MVS scene (a root node, or an object with 'root')"]
        if not isinstance(root.get("children", []), list):
            return [f"{what}: root.children is not a list"]
        return []
    if not isinstance(state, list):
        return [f"{what}: not a JSON array of calls"]
    try:
        errors = schema.validate_actions(state)
    except TypeError as e:  # an action name that is not a string
        errors = [f"malformed action ({e})"]
    return [f"{what}: {e}" for e in errors]


def _target_errors(task: dict, target: Any = None, name: str = "target") -> list[str]:
    target = task["target"] if name == "target" else target
    if target is None:
        return []
    if not isinstance(target, list) or not target:
        return [f"{name}: null (no separate target) or a non-empty list of parts"]
    errors = []
    for i, part in enumerate(target):
        where = f"{name}[{i}]"
        if not isinstance(part, dict) or "selector" not in part:
            errors.append(f"{where}: an object with a 'selector'")
            continue
        unknown = sorted(set(part) - set(TARGET_KEYS))
        if unknown:
            errors.append(f"{where}: unknown key(s) {unknown}")
        sel = part["selector"]
        if not (isinstance(sel, (str, dict)) or isinstance(sel, list) and sel
                and all(isinstance(e, dict) for e in sel)):
            errors.append(f"{where}: selector is a static name, an expression or a list of them")
        for key in ("representation", "color", "structure"):
            if part.get(key) is not None and not isinstance(part[key], str):
                errors.append(f"{where}: {key} is a string or null")
        structure = part.get("structure")
        if structure is None and len(task["structures"]) != 1:
            errors.append(f"{where}: name its 'structure' (the task loads "
                          f"{len(task['structures'])})")
        elif structure is not None and structure not in task["structures"]:
            errors.append(f"{where}: structure {structure!r} is not one of the task's")
    return errors


def validate_task(task: dict) -> list[str]:
    """Every way one task breaks the format (empty = valid). Checks only the task
    itself; `check_corpus` checks links, the panel and the grader."""
    if not isinstance(task, dict):
        return ["not a JSON object"]
    errors: list[str] = []
    legacy = bool(task.get("_legacy"))
    public = {k for k in task if not k.startswith("_")} - _ALIASES
    missing = [k for k in REQUIRED if k not in public]
    if missing:
        return [f"missing field(s): {missing}"]
    unknown = sorted(public - set(REQUIRED) - set(OPTIONAL))
    if unknown and not legacy:
        errors.append(f"unknown field(s): {unknown}")

    if not isinstance(task["id"], str) or not _ID.fullmatch(task["id"]):
        errors.append("id: letters, digits, '.', '_' and '-' only")
    track = task["track"]
    if track not in TRACKS:
        return errors + [f"track: one of {TRACKS}"]
    tiers = TIERS + ((LEGACY_API_TIER,) if legacy else ())
    if task["tier"] not in tiers:
        errors.append(f"tier: one of {TIERS}")
    if not isinstance(task["family"], str) or not task["family"]:
        errors.append("family: the id of the template or generator family (a string)")
    if not isinstance(task["prompt"], str) or not task["prompt"].strip():
        errors.append("prompt: a non-empty string")

    errors += _state_errors(track, task["reference"], "reference")
    accepted = task["accepted"]
    if not isinstance(accepted, list):
        errors.append("accepted: a list of alternative references (may be empty)")
        accepted = []
    for i, alt in enumerate(accepted):
        errors += _state_errors(track, alt, f"accepted[{i}]")

    structures = task["structures"]
    if not (isinstance(structures, list) and all(isinstance(s, str) and s == s.lower()
                                                 for s in structures)
            and len(set(structures)) == len(structures)):
        errors.append("structures: a list of distinct lower-case structure ids")
        structures = []
    elif not errors and not legacy:
        loads = loaded_entries(track, task["reference"])
        known = structures
        if [resolve_entry(e, known) or e for e in loads] != structures:
            errors.append(f"structures: {structures} is not what the reference loads ({loads})")

    context = task["context"]
    state_key = CONTEXT_STATE[track]
    if context is not None:
        if not isinstance(context, dict) or set(context) != {state_key, "noop"}:
            errors.append(f"context: null, or an object with exactly '{state_key}' and 'noop'")
        else:
            errors += _state_errors(track, context[state_key], f"context.{state_key}")
            if not isinstance(context["noop"], bool):
                errors.append("context.noop: true or false")
    if not legacy:
        if (task["tier"] == "followup") != (context is not None):
            errors.append("tier 'followup' is exactly the tasks with a context")
        if task["tier"] == "accept_set" and not accepted:
            errors.append("tier 'accept_set' needs at least one accepted alternative")
        if task["tier"] == "tool_only" and (track != "api" or task["twin_of"] is not None):
            errors.append("tier 'tool_only' is API track only and has no twin")

    if not errors:
        errors += _target_errors(task)
        alt_targets = task.get("accepted_targets")
        if alt_targets is not None:
            if not isinstance(alt_targets, list) or len(alt_targets) != len(accepted):
                errors.append("accepted_targets: one entry per accepted alternative")
            else:
                for i, alt in enumerate(alt_targets):
                    errors += _target_errors(task, alt, f"accepted_targets[{i}]")
    for key in ("twin_of", "paraphrase_of"):
        if task[key] is not None and (not isinstance(task[key], str) or task[key] == task["id"]):
            errors.append(f"{key}: null or the id of another task")
    if task["style"] not in STYLES:
        errors.append(f"style: one of {STYLES}")
    elif (task["paraphrase_of"] is not None) != (task["style"] != "full"):
        errors.append("style: 'full' on the original phrasing (paraphrase_of null); "
                      "'terse' or 'indirect' on a paraphrase (paraphrase_of set)")
    if task["split"] not in SPLITS:
        errors.append(f"split: one of {SPLITS}")

    pack = task["grounding"]
    if pack is not None and not (isinstance(pack, dict) and isinstance(pack.get("rule"), str)
                                 and isinstance(pack.get("text"), str) and pack["text"].strip()):
        errors.append("grounding: null, or an object with 'rule' and a non-empty 'text'")
    skills = task["skills"]
    if not (isinstance(skills, list) and all(isinstance(s, str) and s for s in skills)):
        errors.append("skills: a list of strings")
    elif not skills and not legacy:
        errors.append("skills: at least one")
    extra = task.get("accepted_structures")
    if extra is not None and not (isinstance(extra, list)
                                  and all(isinstance(s, str) for s in extra)):
        errors.append("accepted_structures: a list of structure ids")

    prov = task["provenance"]
    if legacy:
        return errors
    if not isinstance(prov, dict) or any(k not in prov for k in PROVENANCE_KEYS):
        errors.append(f"provenance: an object with {list(PROVENANCE_KEYS)}")
    else:
        if not isinstance(prov["script"], str) or not prov["script"]:
            errors.append("provenance.script: the path of the script that built the task")
        if not isinstance(prov["inputs"], (list, dict)) or not prov["inputs"]:
            errors.append("provenance.inputs: the frozen files the reference was built from")
        if not isinstance(prov["date"], str) or not _DATE.fullmatch(prov["date"]):
            errors.append("provenance.date: YYYY-MM-DD")
        if not (isinstance(prov["checks"], list) and prov["checks"]
                and all(isinstance(c, str) for c in prov["checks"])):
            errors.append("provenance.checks: the checks the reference passed (at least one)")
    return errors


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
_ALIASES = {"category", "categories", "reference_mvs", "accepted_ids", "source",
            "template", "pdb", "difficulty"}


def adapt_legacy(raw: dict) -> dict | None:
    """An old task file (``category`` / ``reference_mvs`` / ``source``) in the new
    format. Returns None for a category that is not a graded track."""
    track = TRACK_OF.get(raw.get("category"))
    if track is None:
        return None
    reference = raw.get("reference_mvs") if track == "mvs" else raw.get("reference")
    accepted = raw.get("accepted") or []
    source = raw.get("source")
    task = {
        "id": raw.get("id"), "track": track,
        "tier": LEGACY_TIER.get(source, "translation") if track == "mvs" else LEGACY_API_TIER,
        "family": raw.get("template") or source or "curated",
        "structures": loaded_entries(track, reference) if reference is not None else [],
        "prompt": raw.get("prompt"), "reference": reference,
        "accepted": accepted, "context": None, "target": None,
        "twin_of": None, "paraphrase_of": None, "style": "full", "split": "public",
        "grounding": raw.get("grounding"), "provenance": raw.get("provenance"),
        "skills": (raw.get("skills") if track == "api" else raw.get("categories")) or [],
        "_legacy": True,
    }
    for key in ("title", "notes"):
        if key in raw:
            task[key] = raw[key]
    if raw.get("accepted_ids"):
        task["accepted_structures"] = raw["accepted_ids"]
    for key in ("source", "template", "pdb"):  # still read by older scripts and tests
        if key in raw:
            task[key] = raw[key]
    return task


def _with_aliases(task: dict) -> dict:
    task["category"] = CATEGORY[task["track"]]
    task["categories"] = task["skills"]
    if task["track"] == "mvs":
        task["reference_mvs"] = task["reference"]
        if task.get("accepted_structures"):
            task["accepted_ids"] = task["accepted_structures"]
    return task


def load_task(path: pathlib.Path, repo: pathlib.Path = REPO) -> dict | None:
    """One task file, validated. None for an old file of an ungraded category."""
    path = pathlib.Path(path)
    data = path.read_bytes()
    try:
        raw = json.loads(data)
    except json.JSONDecodeError as e:
        raise TaskError(f"{path}: not valid JSON: {e}") from e
    if not isinstance(raw, dict):
        raise TaskError(f"{path}: a task file holds one JSON object")
    if "track" in raw:
        clash = sorted(k for k in raw if k in _ALIASES or k.startswith("_"))
        if clash:
            raise TaskError(f"{path}: field(s) {clash} belong to the old format or the loader")
        task = dict(raw)
    else:
        task = adapt_legacy(raw)
        if task is None:
            return None
    errors = validate_task(task)
    if errors:
        raise TaskError(f"{path}: " + "; ".join(errors))
    try:
        task["_path"] = str(path.resolve().relative_to(repo))
    except ValueError:
        task["_path"] = str(path)
    task["_sha256"] = hashlib.sha256(data).hexdigest()
    return _with_aliases(task)


def load_corpus(tasks_dir: pathlib.Path | None = None, tracks: Iterable[str] | None = None,
                repo: pathlib.Path = REPO) -> list[dict]:
    """Every graded task under ``tasks_dir`` (default ``tasks/``), sorted by path.
    ``tracks`` filters by track (either naming: ``api`` or ``api_calling``). Raises
    `TaskError` on the first file that breaks the format, and on a duplicate id."""
    tasks_dir = pathlib.Path(tasks_dir) if tasks_dir else TASKS_DIR
    want = None if tracks is None else {TRACK_OF.get(t, t) for t in tracks}
    out, seen = [], {}
    for path in sorted(tasks_dir.rglob("*.json")):
        task = load_task(path, repo)
        if task is None:
            continue
        if task["id"] in seen:
            raise TaskError(f"{path}: id {task['id']!r} is already used by {seen[task['id']]}")
        seen[task["id"]] = path
        if want is None or task["track"] in want:
            out.append(task)
    return out


def public_form(task: dict) -> dict:
    """The task as its file holds it: no aliases, no loader keys."""
    return {k: v for k, v in task.items()
            if not k.startswith("_") and (k not in _ALIASES or task.get("_legacy"))}


# --------------------------------------------------------------------------- #
# Whole-corpus checks
# --------------------------------------------------------------------------- #
def target_atoms(task: dict, target: Any = None) -> dict[str, int] | None:
    """A target (the task's own by default) as atom sets: ``{structure id: bitmask over
    its atom table}``. None when there is no target or a selector cannot be resolved."""
    target = task.get("target") if target is None else target
    if not target:
        return None
    out: dict[str, int] = {}
    for part in target:
        entry = part.get("structure") or task["structures"][0]
        table = table_for(entry)
        mask = table.selector(part["selector"]) if table is not None else None
        if mask is None:
            return None
        out[entry] = out.get(entry, 0) | mask
    return out


def _mentions_worked_example(task: dict) -> bool:
    text = json.dumps({k: task.get(k) for k in ("prompt", "reference", "accepted", "context",
                                                "structures", "target", "grounding",
                                                "accepted_structures")})
    return re.search(rf"(?<![A-Za-z0-9]){WORKED_EXAMPLE}(?![A-Za-z0-9])", text, re.I) is not None


def check_corpus(tasks: list[dict], grade: Callable[[dict, Any], dict] | None = None,
                 final: bool = False, repo: pathlib.Path = REPO,
                 check: Callable[[dict], list[str]] | None = None) -> tuple[list[str], list[str]]:
    """The checks that need more than one task file. Returns ``(errors, notes)``.

    ``grade(task, prediction)`` is the benchmark's grader (``runner.grade_parsed``);
    without it the self-grading checks are skipped and a note says so. ``check(task)``
    is the grader's own task check (``runner.grader_problems``): a reference that grades
    as itself can still select no atoms at all, and only the grader sees that. ``final`` adds
    what only the frozen corpus must satisfy: no old-format task, and a target score
    reported for every reference.
    """
    errors: list[str] = []
    notes: list[str] = []
    by_id: dict[str, dict] = {}
    for t in tasks:
        if t["id"] in by_id:
            errors.append(f"{t['id']}: id used twice ({by_id[t['id']]['_path']}, {t['_path']})")
        by_id[t["id"]] = t
    known = panel_ids()

    legacy = [t["id"] for t in tasks if t.get("_legacy")]
    if legacy:
        msg = f"{len(legacy)} task(s) are in the old format (read through the adapter)"
        (errors if final else notes).append(msg + (f": {legacy[:5]} ..." if final else ""))

    for t in tasks:
        tid = t["id"]
        if _mentions_worked_example(t):
            errors.append(f"{tid}: uses {WORKED_EXAMPLE.upper()}, the API prompt's worked example")
        for entry in t["structures"]:
            if resolve_entry(entry, known) is None:
                errors.append(f"{tid}: structure {entry!r} is not in the panel")
            elif table_for(entry) is None:
                errors.append(f"{tid}: structure {entry!r} has no atom table")
        script = (t.get("provenance") or {}).get("script") if not t.get("_legacy") else None
        if script and not (repo / script).is_file():
            errors.append(f"{tid}: provenance.script {script!r} is not a file in the repo")
        for name, target in [("target", t["target"])] + [
                (f"accepted_targets[{i}]", alt)
                for i, alt in enumerate(t.get("accepted_targets") or [])]:
            if not target:
                continue
            atoms = target_atoms(t, target)
            if atoms is None:
                errors.append(f"{tid}: {name} cannot be resolved on the atom table")
            elif not all(atoms.values()):
                errors.append(f"{tid}: a part of {name} selects no atoms")

    # Twins: the same request on the other track.
    for t in tasks:
        other = by_id.get(t["twin_of"]) if t["twin_of"] else None
        if t["twin_of"] and other is None:
            errors.append(f"{t['id']}: twin_of {t['twin_of']!r} is not a task")
        if other is None:
            continue
        pair = f"{t['id']} / {other['id']}"
        if other["twin_of"] != t["id"]:
            errors.append(f"{pair}: twin_of is not mutual")
        if other["track"] == t["track"]:
            errors.append(f"{pair}: twins are on the same track")
        for key in ("prompt", "structures", "split", "style", "tier"):
            if other[key] != t[key]:
                errors.append(f"{pair}: twins differ in {key}")
        if (other["context"] is None) != (t["context"] is None):
            errors.append(f"{pair}: one twin is a follow-up and the other is not")
        elif t["context"] and other["context"]["noop"] != t["context"]["noop"]:
            errors.append(f"{pair}: twins differ in context.noop")
        if t["id"] < other["id"] and target_atoms(t) != target_atoms(other):
            errors.append(f"{pair}: twins do not have the same target atoms")

    # Paraphrases: other wordings of one request, same track, same answer.
    for t in tasks:
        if not t["paraphrase_of"]:
            continue
        base = by_id.get(t["paraphrase_of"])
        pair = f"{t['id']} -> {t['paraphrase_of']}"
        if base is None:
            errors.append(f"{pair}: paraphrase_of is not a task")
            continue
        if base["paraphrase_of"] is not None:
            errors.append(f"{pair}: paraphrase_of must name the original ('full') phrasing")
        for key in ("track", "reference", "accepted", "context", "target", "structures",
                    "split", "tier", "family"):
            if base[key] != t[key]:
                errors.append(f"{pair}: a paraphrase differs from its original in {key}")
        if base["prompt"] == t["prompt"]:
            errors.append(f"{pair}: a paraphrase has the same prompt as its original")
    styles: dict[tuple, list[str]] = {}
    for t in tasks:
        styles.setdefault((t["paraphrase_of"] or t["id"], t["style"]), []).append(t["id"])
    for (base_id, style), ids in styles.items():
        if len(ids) > 1:
            errors.append(f"{base_id}: more than one '{style}' phrasing ({ids})")

    # Held-back structures are never public ones (decision 21).
    used = {s: {t["split"] for t in tasks if s in t["structures"] and not t.get("_legacy")}
            for t in tasks for s in t["structures"]}
    both = sorted(s for s, splits in used.items() if len(splits) > 1)
    if both:
        errors.append(f"structure(s) used by both the public and the held-back split: {both}")

    if grade is None:
        notes.append("no grader given: self-grading checks skipped")
        return errors, notes
    def alone(t: dict, state: Any) -> dict:
        """The task with ``state`` as its only right answer."""
        return {**t, "reference": state, "accepted": [], "target": None,
                "accepted_targets": None,
                **({"reference_mvs": state} if t["track"] == "mvs" else {})}

    no_target = 0
    for t in tasks:
        tid = t["id"]
        if check is not None:
            try:
                errors += [f"{tid}: grader check: {p}" for p in check(t)]
            except Exception as e:  # noqa: BLE001 - report it against the task
                errors.append(f"{tid}: the grader's task check failed: {type(e).__name__}: {e}")
        try:
            res = grade(t, t["reference"])
        except Exception as e:  # noqa: BLE001 - report it against the task
            errors.append(f"{tid}: grading its own reference failed: {type(e).__name__}: {e}")
            continue
        if not (res.get("success") is True and res.get("f1") == 1.0):
            errors.append(f"{tid}: its own reference does not grade as exactly right "
                          f"(f1 {res.get('f1')}, success {res.get('success')})")
        if res.get("target_f1") is None:
            no_target += t["target"] is not None  # no atom target: none to report
        elif res["target_f1"] != 1.0:
            errors.append(f"{tid}: its own reference has target score {res['target_f1']}")
        # An alternative is in the accept set, so grading it against the task proves
        # nothing. Check instead that it is a state the grader can stand on (it grades
        # as itself), that the task accepts it with a full target score, and - in the
        # accept-set tier - that it is a different final state from the reference.
        only_reference = {**t, "accepted": [], "accepted_targets": None}
        for i, alt in enumerate(t["accepted"]):
            label = f"accepted[{i}]"
            try:
                own, in_task = grade(alone(t, alt), alt), grade(t, alt)
                same = bool(grade(only_reference, alt).get("success"))
            except Exception as e:  # noqa: BLE001
                errors.append(f"{tid}: grading {label} failed: {type(e).__name__}: {e}")
                continue
            if not (own.get("success") is True and own.get("f1") == 1.0):
                errors.append(f"{tid}: {label} does not grade as itself")
            if not in_task.get("success"):
                errors.append(f"{tid}: {label} is not accepted by its own task")
            if in_task.get("target_f1") not in (None, 1.0):
                errors.append(f"{tid}: {label} has target score {in_task['target_f1']}")
            if same and t["tier"] == "accept_set":
                errors.append(f"{tid}: {label} is the same final state as the reference; an "
                              "accept-set alternative must be a different one")
        if t["context"]:
            start = t["context"][CONTEXT_STATE[t["track"]]]
            try:
                same = bool(grade(t, start).get("success"))
                own = grade(alone(t, start), start)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{tid}: grading its start state failed: {type(e).__name__}: {e}")
                continue
            if not own.get("success"):
                errors.append(f"{tid}: its start state does not grade as itself")
            if same != t["context"]["noop"]:
                errors.append(
                    f"{tid}: context.noop is {t['context']['noop']} but the start state "
                    + ("already is" if same else "is not") + " the requested final state")
    if no_target:
        msg = (f"the grader reported no target score (target_f1) for {no_target} "
               f"reference(s) of the {sum(t['target'] is not None for t in tasks)} "
               "task(s) that have a target")
        (errors if final else notes).append(msg)
    return errors, notes
