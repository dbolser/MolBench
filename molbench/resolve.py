"""
What kind of answer an entry id is on a resolve task (LEDGER L-041).

A resolve task names a protein, not a PDB entry, and many entries are right. A wrong
answer is one of two different failures: the id of a real entry of something else, or
an id that does not exist. The rule and the frozen list of every current PDB id live in
the generator, ``scripts/generate_resolve_tasks.py`` (`answer_outcome`,
``data/mvscore/pdb_ids.txt.gz``); this module is the library door to it, so the runner
and the paper tables use the generator's own function and not a copy. Nothing here
touches the network.

    entry_outcome(task, scene)   -> one of ENTRY_OUTCOMES, or None off the resolve tier
"""

from __future__ import annotations

import functools
import importlib.util
import pathlib
import sys
from typing import Any

from . import tasks as tasks_mod

REPO = pathlib.Path(__file__).resolve().parent.parent
GENERATOR = REPO / "scripts" / "generate_resolve_tasks.py"

# The generator's three outcomes for an entry id, plus the two ways an answer can name
# no PDB entry at all.
ENTRY_OUTCOMES = (
    "accepted",       # one of the task's accepted entries
    "wrong_entry",    # a real PDB entry that is not one of them
    "no_such_entry",  # not a PDB id on the day the list was frozen: made up
    "other_source",   # loads something that is not a PDB entry (an AlphaFold model, another URL)
    "no_entry",       # nothing loaded, or no answer that could be read
)
ENTRY_OUTCOME_LABEL = {
    "accepted": "an accepted entry",
    "wrong_entry": "a real entry of something else",
    "no_such_entry": "an id that does not exist",
    "other_source": "not a PDB entry",
    "no_entry": "no entry loaded",
}


@functools.lru_cache(maxsize=None)
def generator():
    """``scripts/generate_resolve_tasks.py`` as a module. Imported on first use, not at
    import time: the script imports ``molbench.runner``, which imports this module."""
    name = "generate_resolve_tasks"
    if name in sys.modules:
        return sys.modules[name]
    scripts = str(GENERATOR.parent)
    if scripts not in sys.path:  # the script imports its neighbours by bare name
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return mod


def answer_outcome(task: dict, pdb_id: str) -> str:
    """The generator's three-way outcome for one PDB id: ``accepted``, ``wrong_entry``
    or ``no_such_entry``."""
    view = {"accepted_structures": task.get("accepted_structures") or task.get("accepted_ids")
            or [], "structures": task.get("structures") or []}
    return generator().answer_outcome(view, pdb_id)


def pdb_ids_date() -> str:
    """The day the list of current PDB ids was frozen."""
    return generator().pdb_ids()[1]


def missing_id() -> str:
    """A well-formed PDB id that no entry has (for controls and the mock model)."""
    ids = generator().pdb_ids()[0]
    return next(f"{d}zzz" for d in "987654321" if f"{d}zzz" not in ids)


def other_real_id(task: dict) -> str:
    """A real PDB entry that is not one of the task's (for controls and the mock model)."""
    ids = generator().pdb_ids()[0]
    own = set(task.get("accepted_structures") or task.get("accepted_ids") or [])
    own |= set(task.get("structures") or [])
    return next(i for i in ("1crn", "2lzm", "4hhb", "1ubq", "1mbn") if i in ids and i not in own)


def repoint(scene: Any, task: dict, other: str) -> Any:
    """The scene with the task's reference entry replaced by ``other`` (the generator's
    own `repoint`)."""
    return generator().repoint(scene, task["structures"][0], other)


def entry_outcome(task: dict, prediction: Any) -> str | None:
    """Which kind of entry a parsed MVS answer to a resolve task loads (the first one,
    if it loads several). None when the task is not on the resolve tier."""
    if task.get("tier") != "resolve":
        return None
    if not isinstance(prediction, dict):
        return "no_entry"
    entries = tasks_mod.loaded_entries("mvs", prediction)
    if not entries:
        return "other_source" if tasks_mod.unidentified_loads("mvs", prediction) else "no_entry"
    if entries[0].startswith("af-"):
        own = set(task.get("accepted_structures") or []) | set(task.get("structures") or [])
        return "accepted" if entries[0] in own else "other_source"
    return answer_outcome(task, entries[0])
