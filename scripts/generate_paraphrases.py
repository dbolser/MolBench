#!/usr/bin/env python3
"""
Write paraphrases of existing tasks (FINAL_PLAN decision 20): the same request in
three phrasings - the original full sentence, a terse command the way people really
type into the chat box ("1tup chain A red", "hide water"), and an indirect, polite
one. Same reference, same accepted alternatives, same target; only the prompt, the
``style`` and ``paraphrase_of`` differ, so any change in score is due to the wording.

    uv run python scripts/generate_paraphrases.py ID [ID ...]        # these tasks
    uv run python scripts/generate_paraphrases.py --select-seeded 30 # a seeded, stratified 30
    uv run python scripts/generate_paraphrases.py                    # rebuild the recorded selection
    uv run python scripts/generate_paraphrases.py --check            # fail if files would change
    uv run python scripts/generate_paraphrases.py --list-families    # what can be paraphrased

Each source task gets two new files in ``tasks/paraphrases/`` (``<id>.terse.json``,
``<id>.indirect.json``); with the original that makes three phrasings. A task with a
twin on the other track is one *request*: both twins are paraphrased with the same
words, and the paraphrases are twins of each other (TASK_FORMAT.md). The selection is
recorded in ``tasks/paraphrases/SELECTION.txt`` so a bare re-run reproduces the
directory byte for byte. No network; nothing here calls a model.

Where the words come from. Phrasings are scripted templates per task family, never
free text:

1. ``TEMPLATES[family]`` below: several terse and several indirect wordings, filled
   from the task's ``provenance.slots`` (the same slots its generator filled the full
   prompt from). One wording is chosen by seed.
2. A generator may instead ship the wordings with the task, as
   ``provenance.paraphrases = {"terse": "...", "indirect": "..."}`` (already filled).
3. For families with neither, a generic rewrite of the full prompt: the terse form is
   the prompt with words from a fixed list of function words deleted (every other word
   is kept, in order), the indirect form is the prompt turned into a polite question
   ("Could you ...? Then please ...") or, when it is not a chain of imperatives, the
   prompt word for word inside a polite frame. Mechanical, so every such phrasing is
   marked ``generic`` in the README table and should be read before the corpus is
   frozen. ``--templates-only`` turns this off.

A paraphrase must still determine the reference. Two scripted guards: every slot value
must appear in every phrasing (a terse form cannot drop the colour or the residue), and
the generic terse form may only delete words from a fixed list of function words
(a prompt that is already terse cannot be shortened and is not paraphrased).
The terse forms are modelled on the anonymised real-user request categories in
LEDGER.md (U1 colour by chain, U6 terse range specs, U13 hide/show, U14 representation
names): lower-case id first, no verbs or articles, comma-separated.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import pathlib
import re
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import runner, tasks as T  # noqa: E402

SCRIPT = "scripts/generate_paraphrases.py"
SEED = "molbench-paraphrases-v1"
DATE = "2026-11-13"                      # fixed, so a rebuild is byte-identical
OUT = REPO / "tasks" / "paraphrases"
SELECTION = "SELECTION.txt"
STYLES = ("terse", "indirect")
API_CHECK_KEYS = ("structure", "derived", "checked_by", "accepted_differ", "targets")

# --------------------------------------------------------------------------- #
# Wordings per family. Slots are the task's provenance.slots.
# --------------------------------------------------------------------------- #
_HIGHLIGHT_TERSE = [
    "{id} {poly} cartoon, {thing} {colour} ball-and-stick",
    "{id}: {poly} cartoon + {thing} {colour} ball-and-stick",
]
TEMPLATES: dict[str, dict[str, list[str]]] = {
    "acc-chain-colours": {
        "terse": ["{id} cartoon, {n} chains {colours}",
                  "{id}: cartoon, colour {n} chains {colours}"],
        "indirect": [
            "I'd like to tell the {n} chains of {ID} apart. Could you draw it as a cartoon "
            "and give the chains the colours {colours}?",
            "Would it be possible to see {ID} as a cartoon, with its {n} chains in {colours}?",
        ]},
    "acc-ligand-which": {
        "terse": ["{id} {poly} cartoon, ligand {colour} ball-and-stick",
                  "{id}: {poly} cartoon + ligand {colour} ball-and-stick"],
        "indirect": [
            "I'm curious what is bound in {ID}. Could you draw the {poly} as a cartoon and "
            "pick out the ligand in {colour} ball-and-stick?",
            "It would help me to see {ID} with the {poly} as a cartoon and the ligand "
            "standing out as {colour} ball-and-stick.",
        ]},
    "acc-ligand-colours": {
        "terse": ["{id} {poly} cartoon, two ligands ball-and-stick, one {colour} one {colour2}",
                  "{id}: {poly} cartoon + the two ligands ball-and-stick, {colour} and {colour2}"],
        "indirect": [
            "Could you show {ID} with the {poly} as a cartoon and its two ligands as "
            "ball-and-stick, one in {colour} and the other in {colour2}, so that I can tell "
            "them apart?",
            "I'd like to tell the two ligands of {ID} apart: would you draw the {poly} as a "
            "cartoon and the ligands as ball-and-stick, one {colour} and one {colour2}?",
        ]},
    "acc-ligand-copy": {
        "terse": _HIGHLIGHT_TERSE,
        "indirect": [
            "Could you bring up {ID} with the {poly} as a cartoon, and let me see the {thing} "
            "as {colour} ball-and-stick?",
            "I'd like to look at the {thing} in {ID}. Would you draw the {poly} as a cartoon "
            "and the {thing} as {colour} ball-and-stick?",
        ]},
    "acc-residue-copy": {
        "terse": _HIGHLIGHT_TERSE,
        "indirect": [
            "Could you bring up {ID} with the {poly} as a cartoon, and let me see {thing} as "
            "{colour} ball-and-stick?",
            "I'd like to look at {thing} in {ID}. Would you draw the {poly} as a cartoon and "
            "{thing} as {colour} ball-and-stick?",
        ]},
    "acc-residue-colour": {
        "terse": ["{id} {poly} cartoon, {thing} {colour}",
                  "{id}: {poly} cartoon, colour {thing} {colour}"],
        "indirect": [
            "Could you show {ID} with the {poly} as a cartoon and make {thing} {colour}, so "
            "that I can see where it sits?",
            "I'd like to see where {thing} is in {ID}. Would you draw the {poly} as a cartoon "
            "and colour {thing} {colour}?",
        ]},
    "acc-metal-copy": {
        "terse": ["{id} {poly} cartoon, {thing} ion {colour} spacefill",
                  "{id}: {poly} cartoon + {thing} ion {colour} spacefill"],
        "indirect": [
            "I'd like to find the {thing} ion in {ID}. Could you show the {poly} as a cartoon "
            "and the {thing} ion as {colour} spacefill?",
            "Would it be possible to see {ID} with the {poly} as a cartoon and the {thing} "
            "ion as {colour} spacefill?",
        ]},
    "acc-metal-which": {
        "terse": ["{id} {poly} cartoon, metal ion {colour} spacefill",
                  "{id}: {poly} cartoon + metal ion {colour} spacefill"],
        "indirect": [
            "I'd like to find the metal ion in {ID}. Could you show the {poly} as a cartoon "
            "and the metal ion as {colour} spacefill?",
            "Would it be possible to see {ID} with the {poly} as a cartoon and the metal ion "
            "as {colour} spacefill?",
        ]},
    "acc-representation-open": {
        "terse": ["{id} {poly} cartoon, show {thing} {colour}",
                  "{id}: {poly} cartoon, {thing} shown {colour}"],
        "indirect": [
            "I'd like to look at the {thing} in {ID}. Could you draw the {poly} as a cartoon "
            "and show the {thing} in {colour}?",
            "Would you bring up {ID} with the {poly} as a cartoon and show me the {thing} in "
            "{colour}?",
        ]},
}

# --------------------------------------------------------------------------- #
# The generic fallback (opt-in): mechanical rewrites of the full prompt.
# --------------------------------------------------------------------------- #
# Words whose deletion cannot change what is asked for. Deliberately short: negations,
# quantifiers ("only", "all", "both", "each", "other", "except"), referents ("it",
# "that"), prepositions that carry a relation ("between", "within", "by", "to",
# "from", "near", "around") and "also" / "too" (on a follow-up turn they say "add to
# what is there") are NOT here.
FUNCTION_WORDS = frozenset(
    "the a an please as in of with its is are be on at for then me us we "
    "would like want could can you so".split())
DISPLAY_VERBS = frozenset("load open fetch show display draw render".split())
KEEP_VERBS_NEAR = frozenset("not no without except hide remove only nothing".split())
IMPERATIVES = frozenset(
    "load open fetch show display draw render colour color hide highlight label zoom focus "
    "make set add remove select turn spin keep give mark measure put use change switch".split())
# Words that are only sometimes empty. "on" is a state after a toggle verb ("turn on
# the annotation", "switched on"); "as" and "so" head phrases that fall apart without
# them ("as it is", "so that only ..."); "as well" goes as a pair.
TOGGLES = frozenset("turn turns turned turning switch switches switched switching "
                    "toggle toggled".split())
KEEP_AS_BEFORE = frozenset("it is they are before deposited".split())
# A request opener that carries nothing ("I want the ligand view ..." -> "ligand view ...").
_OPENER = re.compile(r"^(?:I want|I need|I would like|I'd like)(?: to (?:see|have|look at))?\s+")
_PDB_WORD = re.compile(r"[0-9][A-Za-z0-9]{3}")
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WORD = re.compile(r"[^\s,;:]+|[,;:]")


def _words(sentence: str) -> list[str]:
    return _WORD.findall(_OPENER.sub("", sentence.rstrip(".!?"), count=1))


def _deletions(words: list[str], drop_verbs: bool) -> list[bool]:
    """For each word of one sentence: may it be deleted? ``_droppable`` plus the words
    that are empty only in some places (see TOGGLES, KEEP_AS_BEFORE)."""
    low = [w.lower() for w in words]
    toggled = bool(TOGGLES & set(low))
    out = []
    for n, w in enumerate(words):
        nxt = low[n + 1] if n + 1 < len(words) else ""
        ok = _droppable(w, n == 0, drop_verbs)
        if low[n] == "on" and toggled:
            ok = False
        elif low[n] == "as" and nxt in KEEP_AS_BEFORE:
            ok = False
        elif low[n] == "so" and nxt == "that":
            ok = False
        elif low[n] in ("is", "are") and n > 1 and low[n - 2] == "as":
            ok = False                    # "as it is", "as they are"
        elif low[n] == "well" and n and low[n - 1] == "as":
            ok = True
        elif w == "I" and nxt in ("want", "would"):
            ok = True                     # "...; I want the stretch ..." -> "...; stretch ..."
        out.append(ok)
    return out


def _droppable(word: str, first: bool, drop_verbs: bool) -> bool:
    """May this word be deleted? Only a plain function word (or display verb): all
    lower case, or capitalised at the start of a sentence. A word with a bracket, a
    digit or an inner capital is never deleted, nor is a single capital letter: "A" in
    "chain A" is a chain, not an article."""
    if not word.isalpha() or not (word.islower() or first and word.istitle() and len(word) > 1):
        return False
    low = word.lower()
    return low in FUNCTION_WORDS or drop_verbs and low in DISPLAY_VERBS


def critical_tokens(text: str) -> list[str]:
    """The tokens a rewrite must keep exactly: anything with a digit or a capital that
    is not just a sentence-initial ordinary word (ids, residues, chains, codes), plus
    every word that is not on the deletable lists. Compared ignoring case only for PDB
    ids, which terse users type in lower case."""
    out = []
    for sentence in _SENTENCE.split(text.strip()):
        words = _words(sentence)
        for n, (w, gone) in enumerate(zip(words, _deletions(words, True))):
            if w in ",;:" or gone or w.lower() == "and":
                continue
            w = w.strip("()\"'")
            out.append(w.lower() if _PDB_WORD.fullmatch(w) or n == 0 and w.istitle() else w)
    return out


def generic_terse(prompt: str) -> str | None:
    """The prompt with function words deleted; display verbs ("show", "load") go too
    unless the sentence has a negation or a hide/remove next to them. None when nothing
    would be shortened."""
    pieces = []
    for sentence in _SENTENCE.split(prompt.strip()):
        words = _words(sentence)
        lowered = {w.lower().strip("()\"'") for w in words}
        drop_verbs = not (lowered & KEEP_VERBS_NEAR)
        kept = []
        for n, (w, gone) in enumerate(zip(words, _deletions(words, drop_verbs))):
            if gone:
                # "Load X and show the protein ..." -> "X, protein ...": the "and" that
                # joined two display verbs joins nothing once they are gone.
                if w.lower() in DISPLAY_VERBS and kept and kept[-1].lower() == "and":
                    kept.pop()
                    if kept and kept[-1] not in ",;:":
                        kept.append(",")
                continue
            if w in ",;:":
                if kept and kept[-1] not in ",;:":
                    kept.append(w)
                continue
            kept.append(w.lower() if _PDB_WORD.fullmatch(w.strip("()")) else w)
        while kept and kept[-1] in ",;:":
            kept.pop()
        text = ""
        for w in kept:
            text += w if w in ",;:" or not text else " " + w
        if text:
            pieces.append(text)
    terse = "; ".join(pieces)
    have = Counter(w.lower() if _PDB_WORD.fullmatch(w) else w
                   for w in (x.strip("()\"'") for x in _WORD.findall(terse)))
    have.update(w.lower() for w in list(have) if w.istitle())
    lost = [w for w in critical_tokens(prompt) if not have[w]]
    if lost or not terse or len(_WORD.findall(terse)) >= len(_WORD.findall(prompt)):
        return None                      # something needed went, or nothing went at all
    return terse


# Polite frames for a prompt that is not a chain of imperatives ("In trypsin (3PTB),
# show ...", "9GIO, cartoon, colour by chain."): the request itself is left word for
# word, so nothing it states can be lost; only the way of asking changes.
FRAMES = (
    "I'd be grateful for your help with a figure, if you have a moment. This is what I need: {body}",
    "Would you mind setting something up for me? Here is what I'm after: {body}",
    "If it isn't too much trouble, could you help me with the following? {body}",
)
QUESTION_FRAMES = (
    "I was wondering if you could tell me something. {body}",
    "Sorry to interrupt, but could I ask: {body}",
)


def generic_indirect(prompt: str, key: str = "") -> str | None:
    """The prompt as a polite question. If every sentence starts with an imperative
    verb: "Could you <first sentence>? Then please <next>." Otherwise the prompt, word
    for word, inside a polite frame chosen by seed (``key``). None for an empty prompt."""
    text = prompt.strip()
    if not text:
        return None
    out = []
    for i, sentence in enumerate(_SENTENCE.split(text)):
        body = sentence.rstrip(".!?")
        first = body.split(" ", 1)[0]
        if first.lower() not in IMPERATIVES or sentence.endswith("?"):
            break
        body = first.lower() + body[len(first):]
        out.append(f"Could you {body}?" if i == 0 else f"Then please {body}.")
    else:
        return " ".join(out)
    frames = QUESTION_FRAMES if text.endswith("?") else FRAMES
    return frames[int(rank("frame", key or text), 16) % len(frames)].format(body=text)


# --------------------------------------------------------------------------- #
# Corpus
# --------------------------------------------------------------------------- #
def rank(*key) -> str:
    return hashlib.sha256("|".join([SEED, *map(str, key)]).encode()).hexdigest()


def load_sources(tasks_dir: pathlib.Path, out: pathlib.Path) -> dict[str, dict]:
    """Every new-format original under ``tasks_dir`` (not the paraphrases this script
    writes, not old-format files), by id, with its repository path in ``_file``."""
    sources = {}
    for path in sorted(tasks_dir.rglob("*.json")):
        if out in path.parents:
            continue
        task = T.load_task(path)
        if task is None or task.get("_legacy") or task["paraphrase_of"] is not None:
            continue
        try:
            task["_file"] = str(path.resolve().relative_to(REPO))
        except ValueError:
            task["_file"] = str(path)
        sources[task["id"]] = task
    return sources


def request_of(task: dict) -> tuple[str, ...]:
    """The ids of one request: a task and, if it has one, its twin; sorted."""
    return tuple(sorted(filter(None, [task["id"], task["twin_of"]])))


def phrasings(task: dict, key: str, generic: bool) -> tuple[dict[str, str] | None, str]:
    """``({"terse": ..., "indirect": ...}, method)`` for a task, or ``(None, why not)``.
    ``key`` seeds the choice of wording (the request, so that twins get the same)."""
    prov = task.get("provenance") or {}
    shipped = prov.get("paraphrases")
    if isinstance(shipped, dict) and all(isinstance(shipped.get(s), str) for s in STYLES):
        return {s: shipped[s] for s in STYLES}, "shipped with the task (provenance.paraphrases)"
    table = TEMPLATES.get(task["family"])
    if table is not None:
        slots = prov.get("slots")
        if not isinstance(slots, dict):
            return None, f"family {task['family']!r} has templates but the task has no provenance.slots"
        out = {}
        for style in STYLES:
            options = table[style]
            wording = options[int(rank("wording", key, style), 16) % len(options)]
            try:
                out[style] = wording.format(**slots)
            except KeyError as e:
                return None, f"template of {task['family']!r} needs slot {e} the task does not have"
            used = set(re.findall(r"{(\w+)}", wording))
            dropped = [k for k, v in slots.items() if k.lower() != "id" and k not in used
                       and str(v).lower() not in out[style].lower()]
            if dropped:
                return None, f"{style} wording of {task['family']!r} drops slot(s) {dropped}"
        return out, "family template (scripts/generate_paraphrases.py TEMPLATES)"
    if generic:
        terse, indirect = generic_terse(task["prompt"]), generic_indirect(task["prompt"], key)
        if terse and indirect:
            return ({"terse": terse, "indirect": indirect},
                    "generic rewrite of the full prompt (terse: function words deleted, every "
                    "other word kept; indirect: turned into a polite question, or put word for "
                    "word inside a polite frame)")
        return None, ("the generic rewrite cannot shorten this prompt (it is already terse, or a "
                      "needed word would go)")
    return None, f"no paraphrase templates for family {task['family']!r}"


def select_seeded(sources: dict[str, dict], n: int, generic: bool,
                  tiers: list[str] | None, public_only: bool = False) -> list[str]:
    """``n`` requests, spread over tiers and then families: round-robin over the tiers,
    inside a tier round-robin over its families (those with an MVS task and the API-only
    ones in turn), inside a family by seed. Only requests
    that can be paraphrased are eligible; with ``public_only``, only requests of the
    public split. Returns one id per request (its first)."""
    by_tier: dict[str, dict[str, list[tuple[str, ...]]]] = {}
    seen = set()
    for task in sources.values():
        req = request_of(task)
        if req in seen or (tiers and task["tier"] not in tiers):
            continue
        if public_only and task["split"] != "public":
            continue
        seen.add(req)
        if any(i not in sources or phrasings(sources[i], req[0], generic)[0] is None for i in req):
            continue
        by_tier.setdefault(task["tier"], {}).setdefault(task["family"], []).append(req)
    queues = []
    for tier in sorted(by_tier):
        fams = by_tier[tier]
        for reqs in fams.values():
            reqs.sort(key=lambda r: rank("select", r[0]))
        # Families whose requests include an MVS task, and API-only families, taken in
        # turn, so that a tier with both kinds is paraphrased on both tracks.
        with_mvs = [f for f in sorted(fams)
                    if any(sources[i]["track"] == "mvs" for i in fams[f][0])]
        api_only = [f for f in sorted(fams) if f not in with_mvs]
        names = [f for pair in itertools.zip_longest(with_mvs, api_only) for f in pair if f]
        order = []
        for depth in range(max(map(len, fams.values()))):
            order += [fams[f][depth] for f in names if depth < len(fams[f])]
        queues.append(order)
    chosen: list[str] = []
    depth = 0
    while len(chosen) < n and any(depth < len(q) for q in queues):
        for q in queues:
            if depth < len(q) and len(chosen) < n:
                chosen.append(q[depth][0])
        depth += 1
    return sorted(chosen)


def paraphrase(task: dict, style: str, prompt: str, method: str, twin: str | None) -> dict:
    src = T.public_form(task)
    src.pop("_file", None)
    out = {**src, "id": f"{task['id']}.{style}", "prompt": prompt, "twin_of": twin,
           "paraphrase_of": task["id"], "style": style,
           "provenance": {
               "script": SCRIPT,
               "inputs": [task["_file"]],
               "date": DATE,
               "checks": ["(filled in below, once passed)"],
               "seed": SEED,
               "method": method,
               "original_prompt": task["prompt"],
               "source": src["provenance"],
               # An API original's own check record (scripts/check_api_refs.py reads it at
               # the top level): the reference is the same, so the record is too.
               **{k: src["provenance"][k] for k in API_CHECK_KEYS if k in src["provenance"]},
           }}
    return out


def build(sources: dict[str, dict], ids: list[str], generic: bool) -> tuple[list[dict], list[str]]:
    built, skipped, done = [], [], set()
    for tid in ids:
        if tid not in sources:
            skipped.append(f"{tid}: not an original new-format task under tasks/")
            continue
        req = request_of(sources[tid])
        if req in done:
            continue
        done.add(req)
        missing = [i for i in req if i not in sources]
        if missing:
            skipped.append(f"{tid}: its twin {missing} is not in the corpus")
            continue
        words = {i: phrasings(sources[i], req[0], generic) for i in req}
        bad = [f"{i}: {why}" for i, (w, why) in words.items() if w is None]
        if bad:
            skipped += bad
            continue
        if len({json.dumps(w, sort_keys=True) for w, _ in words.values()}) != 1:
            skipped.append(f"{tid}: its twins would get different words")
            continue
        for style in STYLES:
            for i in req:
                other = [j for j in req if j != i]
                w, method = words[i]
                built.append(paraphrase(sources[i], style, w[style], method,
                                        f"{other[0]}.{style}" if other else None))
    return built, skipped


def verify(built: list[dict], sources: dict[str, dict]) -> None:
    """Schema, links and grading of the paraphrases together with their originals."""
    loaded = []
    for t in built:
        errors = T.validate_task(t)
        if errors:
            raise SystemExit(f"{t['id']}: " + "; ".join(errors))
        loaded.append(T._with_aliases({**t, "_path": f"paraphrases/{t['id']}.json"}))
    needed = {t["paraphrase_of"] for t in built}
    originals = [sources[i] for i in sorted(needed)]
    errors, _ = T.check_corpus(originals + loaded, grade=runner.grade_parsed,
                               check=runner.grader_problems)
    if errors:
        raise SystemExit("paraphrases fail the corpus checks:\n  " + "\n  ".join(errors))
    prompts: dict[tuple, str] = {}
    for t in built:
        src = sources[t["paraphrase_of"]]
        key = (src["track"], t["prompt"])
        if key in prompts and prompts[key] != t["paraphrase_of"]:
            raise SystemExit(f"{t['id']}: the same words as a paraphrase of {prompts[key]}")
        prompts[key] = t["paraphrase_of"]
        t["provenance"]["checks"] = [
            "same reference, accepted alternatives, target, structures, split, tier and "
            "family as the original (molbench.tasks.check_corpus)",
            "the reference grades as exactly right against the paraphrase (runner.grade_parsed)",
            "every slot value of the original appears in the wording (nothing needed is dropped)"
            if t["provenance"]["method"].startswith("family")
            else "wording checked by the rule of its method (see 'method')",
        ]
        if t["twin_of"]:
            checks = t["provenance"]["checks"]
            checks.append("its twin on the other track has the same words and the same style")


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def readme(built: list[dict], skipped: list[str], command: str) -> str:
    originals = sorted({t["paraphrase_of"] for t in built})
    requests = {tuple(sorted(filter(None, [t["paraphrase_of"],
                                           (t["twin_of"] or "").rsplit(".", 1)[0] or None])))
                for t in built}
    fam = Counter(t["family"] for t in built if t["style"] == "terse")
    lines = [
        "# Paraphrases",
        "",
        "Generated by `scripts/generate_paraphrases.py` (seed `" + SEED + "`); do not edit.",
        "Each task here rewords one original task (`paraphrase_of`): same reference, same",
        "accepted alternatives, same target, another `prompt` and `style`. With the original",
        "(`full`) that gives three phrasings per request: full sentence, terse command, and",
        "indirect/polite. Wordings are scripted: `family` = a template of the task's family,",
        "filled from the original's `provenance.slots`; `shipped` = written by the task's own",
        "generator; `generic` = a mechanical rewrite of the full prompt (function words",
        "deleted; polite question or frame), to be read before the corpus is frozen. See the",
        "script's docstring for the rules.",
        "",
        f"{len(built)} paraphrase tasks of {len(originals)} originals "
        f"({len(requests)} requests; a twin pair is one request). Rebuild with:",
        "",
        "```bash",
        "uv run python scripts/generate_paraphrases.py            # the recorded selection",
        f"uv run python scripts/generate_paraphrases.py {command}".rstrip(),
        "```",
        "",
        "| family | originals paraphrased |", "|---|---:|",
    ]
    lines += [f"| `{f}` | {n} |" for f, n in sorted(fam.items())]
    lines += ["", "## The three phrasings", "",
              "| original | wording | full | terse | indirect |", "|---|---|---|---|---|"]
    by = {(t["paraphrase_of"], t["style"]): t for t in built}
    shown = set()
    for tid in originals:
        full = by[(tid, "terse")]["provenance"]["original_prompt"]
        if full in shown:              # the twin on the other track: same words
            continue
        shown.add(full)
        how = by[(tid, "terse")]["provenance"]["method"].split(" ", 1)[0]
        lines.append(f"| `{tid}` | {how} | {cell(full)} | {cell(by[(tid, 'terse')]['prompt'])} | "
                     f"{cell(by[(tid, 'indirect')]['prompt'])} |")
    if skipped:
        lines += ["", "## Asked for but not paraphrased", ""] + [f"- {s}" for s in skipped]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ids", nargs="*", help="ids of the tasks to paraphrase")
    ap.add_argument("--select-seeded", type=int, metavar="N",
                    help="choose N requests by seed, spread over tiers and families")
    ap.add_argument("--tiers", nargs="+", help="with --select-seeded: only these tiers")
    ap.add_argument("--public-only", action="store_true",
                    help="with --select-seeded: only requests of the public split")
    ap.add_argument("--templates-only", action="store_true",
                    help="skip families without templates (no generic rewrite of the prompt)")
    ap.add_argument("--list-families", action="store_true",
                    help="say which families can be paraphrased, and stop")
    ap.add_argument("--check", action="store_true", help="fail if the files would change")
    ap.add_argument("--tasks-dir", type=pathlib.Path, default=T.TASKS_DIR)
    ap.add_argument("--out", type=pathlib.Path, default=None,
                    help="where to write (default: <tasks-dir>/paraphrases)")
    a = ap.parse_args(argv)
    out = (a.out or a.tasks_dir / "paraphrases").resolve()
    sources = load_sources(a.tasks_dir.resolve(), out)

    if a.list_families:
        per: dict[tuple, Counter] = {}
        for t in sources.values():
            ok, why = phrasings(t, request_of(t)[0], not a.templates_only)
            per.setdefault((t["tier"], t["family"]), Counter())[
                "yes: " + why if ok else "no: " + why] += 1
        for (tier, family), counts in sorted(per.items()):
            for why, n in sorted(counts.items()):
                print(f"{tier:<12} {family:<28} {n:>4}  {why}")
        return 0

    record = out / SELECTION
    generic = not a.templates_only
    if a.select_seeded is not None:
        ids = select_seeded(sources, a.select_seeded, generic, a.tiers, a.public_only)
        command = f"--select-seeded {a.select_seeded}" + (
            " --tiers " + " ".join(a.tiers) if a.tiers else "") + (
            " --public-only" if a.public_only else "")
        if len(ids) < a.select_seeded:
            print(f"note: only {len(ids)} of {a.select_seeded} requests can be paraphrased "
                  "(see --list-families)")
    elif a.ids:
        ids, command = sorted(a.ids), " ".join(sorted(a.ids))
    elif record.exists():
        lines = record.read_text(encoding="utf-8").splitlines()
        head = [x[1:].strip() for x in lines if x.startswith("#")]
        command = next((x[len("command:"):].strip() for x in head if x.startswith("command:")), "")
        generic = generic and "--templates-only" not in command
        ids = [x.strip() for x in lines if x.strip() and not x.startswith("#")]
    else:
        ap.error("give task ids or --select-seeded N (no recorded selection yet)")
    if not generic and "--templates-only" not in command:
        command = (command + " --templates-only").strip()

    built, skipped = build(sources, ids, generic)
    verify(built, sources)
    files = {out / f"{t['id']}.json": json.dumps(t, indent=1) + "\n" for t in built}
    files[record] = (f"# command: {command}\n# one request per line (its first task id); "
                     "a twin is paraphrased with it\n" + "".join(f"{i}\n" for i in ids))
    files[out / "README.md"] = readme(built, skipped, command)
    stale = sorted(p for p in out.glob("*") if p not in files) if out.exists() else []
    changed = [p for p, text in files.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text]
    for s in skipped:
        print(f"skipped: {s}")
    if a.check:
        if changed or stale:
            print("paraphrases are out of date:", *[p.name for p in changed + stale])
            return 1
        print(f"{len(built)} paraphrase tasks are up to date")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"wrote {len(built)} paraphrase tasks of {len({t['paraphrase_of'] for t in built})} "
          f"originals to {out} ({len(changed)} files changed, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
