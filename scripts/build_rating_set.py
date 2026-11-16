#!/usr/bin/env python3
"""
Build the A4 human-agreement rating set from the VLM-judged pairs of a run.

Every pair the T2 judge saw (reference render vs a model's render) is a candidate,
except those the public gallery already shows with their verdict (--public). At most
--max-per-task are kept per task, so raters don't see one prompt a dozen times;
ids listed in --keep (pairs already rated) are kept first. Plus two kinds of attention check with a known answer that doesn't depend on the judge:

  control-same       a T1 rescue: the two renders differ by <= 2 pixels
  control-different  one task's reference vs another task's, on a different structure

Writes two things, kept apart so raters stay blind:

  <out>/items.json + <out>/img/   PUBLIC — prompt and two images per item, opaque ids,
                                  no model name or verdict. Copied to the rating site.
  <key>                           PRIVATE answer key — model, task, VLM verdict, control
                                  type per id, and the secret the ids are keyed with
                                  (reused on rebuild, so ids stay stable). Read by
                                  scripts/agreement.py. Also holds `population`:
                                  how many judged pairs the run has per task and
                                  judge label, so agreement.py can weight the
                                  sample back to the run (the set over-samples the
                                  judge's "same" calls and caps pairs per task).

    python scripts/build_rating_set.py results/r2x2/spec \\
        --out ../molstar-chat-driver/site/rate/a4-v1 --key results/a4/a4-v1/key.json

For a set built before the key held `population`, write just those counts (no
images, key untouched):

    python scripts/build_rating_set.py results/r2x2/spec \
        --population-only results/a4/a4-v1/population.json

Design v2 (set a4-v2; decisions 23 and 24 of FINAL_PLAN.md)
------------------------------------------------------------
Given a finished manifest run (a directory with ``samples/<condition>/<model>.jsonl``)
the set is built to check the GRADER against people, not only the image judge:

  pairs    one answer per (task, model), MVS track, valid scenes only, drawn in three
           classes of the grader's verdict: right (task success), close (success
           false, target score 1) and wrong; an equal share per tier inside each
           class, models taken in turn, at most --per-task pairs per task. Each pair is
           four pictures: reference and answer, whole and framed on the target atoms,
           the answer always from the reference's camera.
  checks   a pool of known answers of three kinds: the reference against itself
           (check-same), against another structure's reference (check-different), and
           against a copy of itself changed by script in one way the grader fails
           (check-calibrated).
  order    one fixed order of the pairs in which every prefix is balanced over
           class x tier; the rating site opens pairs in that order and gives a pair
           its second rater before it opens a new one.

Scene track only: an API answer is a call list, graded by replaying it to a final
viewer state; no picture of it is made by the run, and one taken in pdbe-molstar
would test that viewer's defaults (see paper/a4/FINAL_CALL.md).

    python scripts/build_rating_set.py results/final-v1 --set a4-v2 \\
        --out ../molstar-chat-driver/site/rate/a4-v2 --key results/a4/a4-v2/key.json --jobs 8

Writes the public items (ids, prompts, pictures: nothing else) and, next to the
private key, ``seed_rating_items.sql`` (which id is a pair or a check, and the order:
the rating site's serving plan) and ``review/`` (one sheet per item, for a look before
launch). The key must lie outside git or in a git-ignored place; the build refuses
otherwise. ``--plan-only`` prints the sample by class and tier without a render.
"""

from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import hmac
import json
import pathlib
import random
import secrets
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import runner  # noqa: E402
from molbench.escalate import _download_ids  # noqa: E402

QUESTION = (
    "Ignore camera angle, zoom and orientation. Does the model's scene show the SAME "
    "visualization as the reference: same structure, same parts shown, equivalent "
    "representations (cartoon / surface / ball-and-stick), equivalent colours, and the "
    "same region highlighted or focused?"
)


def item_id(secret: str, set_id: str, *parts: str) -> str:
    """Keyed, so a rater can't recompute ids from the public model and task lists."""
    msg = ":".join((set_id, *parts)).encode()
    return hmac.new(bytes.fromhex(secret), msg, hashlib.sha256).hexdigest()[:12]


def judged_pairs(results: pathlib.Path) -> list[dict]:
    """One record per escalated task that has both renders: T2-judged or a T1 rescue."""
    out = []
    for path in sorted(results.glob("*.json")):
        card = json.loads(path.read_text())
        for model, m in card["models"].items():
            for t in m["tasks"]:
                e = t.get("escalation") or {}
                if e.get("decision") not in ("vlm:same", "vlm:different", "rendering-equivalent"):
                    continue
                out.append({"model": model, "task": t["id"], "decision": e["decision"],
                            "tree_f1": e.get("tree_f1"), "changed_pixels": e.get("changed_pixels"),
                            "vlm": e.get("vlm"), "ref_png": e["ref_png"], "pred_png": e["pred_png"]})
    return out


def _short(model: str) -> str:
    """The model name without its provider prefix; the gallery uses both forms."""
    return model.split("/")[-1]


def public_pairs(gallery: pathlib.Path | None) -> set[tuple[str, str]]:
    """(model, task) pairs on the public gallery page, which shows the judge's verdict."""
    if gallery is None:
        return set()
    return {(_short(r["model"]), r["id"]) for r in json.loads(gallery.read_text())["rows"]}


def population(results: pathlib.Path, public: set[tuple[str, str]] = frozenset()) -> dict:
    """Judged pairs of the run per (task, judge label): what the rating set is sampled from."""
    cells = collections.Counter(
        (p["task"], p["vlm"]["label"]) for p in judged_pairs(results)
        if p["decision"].startswith("vlm:") and (_short(p["model"]), p["task"]) not in public)
    return {"frame": "VLM-judged pairs of the run, minus pairs shown on the public gallery",
            "cells": [[task, label, n] for (task, label), n in sorted(cells.items())]}


def build(results: pathlib.Path, set_id: str, n_controls: int, seed: int,
          secret: str, public: set[tuple[str, str]] = frozenset(),
          max_per_task: int | None = None, keep: set[str] = frozenset()) -> tuple[list[dict], dict]:
    """(items, key). Items carry source image paths under `_ref`/`_out` until written."""
    tasks = {t["id"]: t for t in runner.load_tasks(None)}
    pairs = [p for p in judged_pairs(results) if (_short(p["model"]), p["task"]) not in public]
    if not pairs:
        raise SystemExit(f"{results}: no escalated pairs with renders")
    rng = random.Random(seed)
    items, key = [], {}

    def add(kind: str, task: str, ref: str, out: str, ident: tuple[str, ...], **info) -> None:
        i = item_id(secret, set_id, kind, *ident)
        items.append({"id": i, "prompt": tasks[task]["prompt"], "_ref": ref, "_out": out})
        key[i] = {"kind": kind, "task": task, **info}

    judged = collections.defaultdict(list)
    for p in pairs:
        if p["decision"].startswith("vlm:"):
            judged[p["task"]].append(p)
    for task, ps in judged.items():
        # Already-rated pairs first; then alternate the judge's "same" and "different"
        # calls so the cap keeps both, each in keyed-id order (fixed, unpredictable).
        ident = {id(p): item_id(secret, set_id, "vlm", p["model"], task) for p in ps}
        by_label = {lab: sorted((p for p in ps if p["vlm"]["label"] == lab), key=lambda p: ident[id(p)])
                    for lab in ("same", "different")}
        rank = {id(p): n for lab in by_label for n, p in enumerate(by_label[lab])}
        ps.sort(key=lambda p: (ident[id(p)] not in keep, rank.get(id(p), len(ps)), p["vlm"]["label"] != "same"))
        for p in ps[:max_per_task]:
            add("vlm", p["task"], p["ref_png"], p["pred_png"], (p["model"], p["task"]),
                model=p["model"], vlm_label=p["vlm"]["label"], vlm_score=p["vlm"].get("score"),
                judge=p["vlm"].get("judge"), tree_f1=p["tree_f1"], changed_pixels=p["changed_pixels"])

    t1 = [p for p in pairs if p["decision"] == "rendering-equivalent"]
    for p in rng.sample(t1, min(n_controls, len(t1))):
        add("control-same", p["task"], p["ref_png"], p["pred_png"], (p["model"], p["task"]),
            model=p["model"], expected="same", changed_pixels=p["changed_pixels"])

    refs = {p["task"]: p["ref_png"] for p in pairs}  # one reference render per task
    structure = {t: frozenset(_download_ids(tasks[t]["reference_mvs"])) for t in refs}
    names = sorted(refs)
    for a in rng.sample(names, min(n_controls, len(names))):
        others = [t for t in names if structure[t].isdisjoint(structure[a])]
        if not others:
            raise SystemExit(f"no reference on a different structure to pair with {a}")
        b = rng.choice(others)
        add("control-different", a, refs[a], refs[b], (a, b), other_task=b, expected="different")

    rng.shuffle(items)
    return items, key


def write(items: list[dict], key: dict, set_id: str, secret: str, out: pathlib.Path, key_path: pathlib.Path,
          quality: int = 85, population: dict | None = None) -> None:
    from PIL import Image
    (out / "img").mkdir(parents=True, exist_ok=True)
    public = []
    for it in items:
        rec = {"id": it["id"], "prompt": it["prompt"]}
        for side, src in (("ref", it["_ref"]), ("out", it["_out"])):
            rel = f"img/{it['id']}-{side}.jpg"
            with Image.open(src) as im:  # flatten any transparency onto white, not black
                rgba = im.convert("RGBA")
                flat = Image.new("RGB", rgba.size, (255, 255, 255))
                flat.paste(rgba, mask=rgba.getchannel("A"))
                flat.save(out / rel, "JPEG", quality=quality)
            rec[side] = rel
        public.append(rec)
    (out / "items.json").write_text(json.dumps(
        {"set": set_id, "question": QUESTION, "items": public}, indent=1) + "\n")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    full = {"set": set_id, "secret": secret, "items": key, **({"population": population} if population else {})}
    key_path.write_text(json.dumps(full, indent=1, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# Design v2: the grader against people (a manifest run's sample files)
# --------------------------------------------------------------------------- #
DESIGN_V2 = "v2"
CLASSES = ("right", "close", "wrong")
CHECK_KINDS = ("check-same", "check-different", "check-calibrated")
# One sitting: 27 pairs + 6 checks + 2 repeats of the rater's own earlier pairs = 35.
PER_RATER = {"goal": 35, "pairs": 27, "repeats": 2,
             "checks": {"check-same": 3, "check-different": 2, "check-calibrated": 1},
             "checks_in_first": 8}
# Name-resolution requests ("show me lysozyme") accept any sensible view and are graded
# on the entry chosen, so "is it the same picture?" is not the question there.
EXCLUDED_TIERS = ("resolve",)
QUESTIONS_V2 = {
    "whole": (
        "Whole scene. Judged against the request, does the model's scene show the same "
        "thing as the reference: the same parts of the structure, drawn and coloured as "
        "the request says? Both pictures are taken from the same place. A difference in "
        "something the request leaves open (a colour it does not name, say) does not "
        "count. Something extra that the request did not ask for does count."),
    "target": (
        "Zoomed view. Look only at the part the request is about: is it picked out the "
        "same way in both pictures (the same atoms, the same drawing style, the same "
        "colour where the request names one)? Ignore everything else in view."),
}
FOLLOWUP_NOTE = ("This request changes a scene that was already on screen (shown as "
                 "\"Before the request\"). Compare the two results.")
_FAR_COLOUR = {"red": "blue", "blue": "red", "green": "magenta", "magenta": "green",
               "orange": "blue", "yellow": "blue", "purple": "orange", "cyan": "red"}
_OTHER_REP = {"cartoon": "ball_and_stick", "ball_and_stick": "spacefill",
              "spacefill": "ball_and_stick", "surface": "cartoon", "line": "spacefill"}


def grader_class(sample: dict) -> str:
    """right: task success. close: not a success, target score 1. wrong: the rest."""
    if sample.get("success"):
        return "right"
    return "close" if sample.get("target_f1") == 1.0 else "wrong"


def read_run(run: pathlib.Path, condition: str = "spec") -> list[dict]:
    """Every sample line of one condition of a manifest run."""
    files = sorted((run / "samples" / condition).glob("*.jsonl"))
    if not files:
        raise SystemExit(f"{run}: no sample files under samples/{condition}/")
    return [json.loads(line) for f in files for line in f.read_text().splitlines() if line.strip()]


def frame(samples: list[dict], corpus: dict[str, dict]) -> tuple[list[dict], dict]:
    """The samples a person can be shown a picture of, and why the others are left out.

    Kept: MVS track, a tier that is not excluded, a task in today's corpus, an answer
    that parsed to a scene the grader took as valid. Each kept record gains ``cls``
    (the grader's class) and ``base`` (the task, or the original a paraphrase rewords:
    they share a reference, so they are capped and resampled together).
    """
    why = collections.Counter()
    kept = []
    for s in samples:
        task = corpus.get(s["task_id"])
        if s.get("track") != "mvs":
            why["API track (no picture of a call list)"] += 1
        elif task is None:
            why["task not in the corpus"] += 1
        elif s.get("tier") in EXCLUDED_TIERS:
            why[f"tier {s['tier']} (any view accepted)"] += 1
        elif s.get("outcome") != "valid" or not isinstance(s.get("predicted"), dict):
            why[f"no scene to draw ({s.get('outcome')})"] += 1
        else:
            kept.append({**s, "cls": grader_class(s), "base": task.get("paraphrase_of") or task["id"]})
    return kept, dict(sorted(why.items()))


def population_v2(kept: list[dict]) -> dict:
    """Answers of the run per (tier, grader class): what the pairs are weighted back to."""
    cells = collections.Counter((s["tier"], s["cls"]) for s in kept)
    return {"frame": "valid MVS scenes of the run's spec condition, every sample, "
                     f"tiers other than {', '.join(EXCLUDED_TIERS)}",
            "cells": [[tier, cls, n] for (tier, cls), n in sorted(cells.items())]}


def one_per_task_and_model(kept: list[dict], secret: str, set_id: str) -> list[dict]:
    """One sample per (task, model): the one whose keyed id sorts first. Each record
    gains ``id``, the item id it would have."""
    best: dict[tuple[str, str], dict] = {}
    for s in kept:
        s = {**s, "id": item_id(secret, set_id, "pair", s["model"], s["task_id"], str(s["sample"]))}
        k = (s["model"], s["task_id"])
        if k not in best or s["id"] < best[k]["id"]:
            best[k] = s
    return sorted(best.values(), key=lambda s: s["id"])


def select_pairs(cands: list[dict], n: int, mix: dict[str, float], per_task: int,
                 model_share: float, banned: frozenset[str] = frozenset()) -> list[dict]:
    """``n`` candidates: ``mix`` over the grader's classes, inside a class the tiers in
    turn, inside a tier the models in turn (fewest taken so far first), never more than
    ``per_task`` of one task or ``model_share`` of the set from one model. A class that
    runs short hands its places to the others. Everything is in keyed-id order, so the
    same key gives the same set."""
    model_cap = max(1, int(model_share * n))
    queues: dict[tuple[str, str], dict[str, list[dict]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in cands:
        if s["id"] not in banned:
            queues[s["cls"], s["tier"]][s["model"]].append(s)
    task_n, model_n, cell_n = collections.Counter(), collections.Counter(), collections.Counter()
    chosen: list[dict] = []

    def take(cls: str) -> bool:
        tiers = sorted((t for c, t in queues if c == cls), key=lambda t: (cell_n[cls, t], t))
        for tier in tiers:
            by_model = queues[cls, tier]
            for model in sorted(by_model, key=lambda m: (model_n[m], by_model[m][0]["id"] if by_model[m] else "")):
                q = by_model[model]
                while q and (task_n[q[0]["base"]] >= per_task or model_n[model] >= model_cap):
                    q.pop(0)   # both counts only grow, so this candidate is out for good
                if q:
                    s = q.pop(0)
                    chosen.append(s)
                    task_n[s["base"]] += 1
                    model_n[model] += 1
                    cell_n[cls, tier] += 1
                    return True
        return False

    want = {c: int(n * mix[c] / sum(mix.values())) for c in CLASSES}
    for c in CLASSES[: n - sum(want.values())]:
        want[c] += 1
    open_classes = {c for c in CLASSES if want[c]}
    got = collections.Counter()
    while len(chosen) < n and open_classes:
        # the class furthest below its share, among those that still have candidates
        cls = min(open_classes, key=lambda c: (got[c] >= want[c], got[c] / max(want[c], 1e-9), CLASSES.index(c)))
        if take(cls):
            got[cls] += 1
        else:
            open_classes.discard(cls)
    return chosen


def balanced_order(chosen: list[dict]) -> list[dict]:
    """The pairs in one fixed order whose every prefix holds the class x tier cells in
    (nearly) the proportions of the whole set, keyed-id order inside a cell."""
    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for s in sorted(chosen, key=lambda s: s["id"]):
        cells[s["cls"], s["tier"]].append(s)
    size = {c: len(v) for c, v in cells.items()}
    taken = collections.Counter()
    out = []
    while len(out) < len(chosen):
        cell = min((c for c in cells if taken[c] < size[c]),
                   key=lambda c: ((taken[c] + 0.5) / size[c], cells[c][taken[c]]["id"]))
        out.append(cells[cell][taken[cell]])
        taken[cell] += 1
    return out


def _walk(node):
    if isinstance(node, dict):
        yield node
        for child in node.get("children") or []:
            yield from _walk(child)


def calibrated_variants(scene: dict):
    """Copies of a scene changed in ONE way a careful person sees: a stated colour
    swapped for a far one, or a representation swapped for another. Yields (what,
    scene); the caller keeps the first one the grader fails."""
    root = scene.get("root", scene)
    nodes = list(_walk(root))
    for kind, table in (("color", _FAR_COLOUR), ("representation", _OTHER_REP)):
        for i in reversed(range(len(nodes))):       # last first: the highlight, not the backdrop
            node = nodes[i]
            key = "color" if kind == "color" else "type"
            value = (node.get("params") or {}).get(key)
            if node.get("kind") != kind or not isinstance(value, str) or value.lower() not in table:
                continue
            changed = copy.deepcopy(scene)
            twin = list(_walk(changed.get("root", changed)))[i]
            twin["params"][key] = table[value.lower()]
            yield f"{kind}: {value} -> {table[value.lower()]}", changed


def target_rows_of(task: dict, matched: int = 0) -> list[int] | None:
    """Atom-table rows of the task's target (of the accepted answer ``matched`` when the
    alternatives have targets of their own). None without a target."""
    from molbench import tasks as tasks_mod
    target = task.get("target")
    alts = task.get("accepted_targets")
    if matched and alts and matched - 1 < len(alts):
        target = alts[matched - 1]
    atoms = tasks_mod.target_atoms(task, target) if target else None
    if not atoms:
        return None
    mask = atoms.get(task["structures"][0]) or next(iter(atoms.values()))
    return [i for i in range(mask.bit_length()) if mask >> i & 1] or None


def reference_of(task: dict, matched: int = 0) -> dict:
    """The right answer the grader matched: the reference, or accepted answer ``matched``."""
    states = [task["reference"], *(task.get("accepted") or [])]
    return states[matched] if matched and matched < len(states) else states[0]


# --- pictures ---------------------------------------------------------------------
def _sha(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:20]


class MolstarRenderer:
    """Pictures by headless Mol* (molbench.render). ``ref`` works the two cameras out on
    the reference; ``answer`` takes its pictures from those cameras. Results are kept in
    ``cache`` under a hash of the scene and camera, so a rebuild renders nothing twice."""

    def __init__(self, cache: pathlib.Path, width: int = 800, height: int = 600, network: bool = True):
        self.cache, self.width, self.height, self.network = cache, width, height, network

    def _frame(self, scene, out, **kw):
        from molbench import render
        return render.render_framed(scene, out, width=self.width, height=self.height,
                                    network=self.network, **kw)

    def ref(self, scene: dict, rows: list[int] | None) -> dict:
        d = self.cache / _sha("ref", scene, rows, self.width, self.height)
        done = d / "done.json"
        if done.exists():
            return json.loads(done.read_text())
        d.mkdir(parents=True, exist_ok=True)
        out = {"whole": str(d / "whole.png"), "target": None, "target_camera": None, "framed": None}
        out["whole_camera"] = self._frame(scene, d / "whole.png")["camera"]
        if rows:
            t = self._frame(scene, d / "target.png", rows=rows)
            out.update(target=str(d / "target.png"), target_camera=t["camera"], framed=t["framed"])
        done.write_text(json.dumps(out))
        return out

    def answer(self, scene: dict, ref: dict) -> dict:
        d = self.cache / _sha("answer", scene, ref["whole_camera"], ref["target_camera"], self.width, self.height)
        done = d / "done.json"
        if done.exists():
            return json.loads(done.read_text())
        d.mkdir(parents=True, exist_ok=True)
        out = {"whole": str(d / "whole.png"), "target": None}
        self._frame(scene, d / "whole.png", camera=ref["whole_camera"])
        if ref["target_camera"]:
            self._frame(scene, d / "target.png", camera=ref["target_camera"])
            out["target"] = str(d / "target.png")
        done.write_text(json.dumps(out))
        return out


def _call(job):
    """(renderer, method, args) -> (result, None) or (None, error text). Top level, so a
    process pool can run it."""
    renderer, method, args = job
    try:
        return getattr(renderer, method)(*args), None
    except Exception as e:  # noqa: BLE001 - a model's scene may fail to draw; say why
        return None, f"{type(e).__name__}: {e}"[:500]


def render_all(renderer, method: str, jobs: list[tuple], workers: int) -> list[tuple]:
    work = [(renderer, method, args) for args in jobs]
    if workers <= 1 or len(work) <= 1:
        return [_call(w) for w in work]
    import concurrent.futures
    with concurrent.futures.ProcessPoolExecutor(workers) as pool:
        return list(pool.map(_call, work))


def differing_share(a: str, b: str, tolerance: int = 48) -> float:
    """Share of pixels where any channel differs by more than ``tolerance``."""
    from PIL import Image, ImageChops
    with Image.open(a) as ia, Image.open(b) as ib:
        ia, ib = ia.convert("RGB"), ib.convert("RGB")
        if ia.size != ib.size:
            return 1.0
        r, g, bl = ImageChops.difference(ia, ib).split()
    worst = ImageChops.lighter(ImageChops.lighter(r, g), bl)
    return sum(worst.histogram()[tolerance + 1:]) / (ia.size[0] * ia.size[1])


def is_blank(path: str) -> bool:
    """A picture with nothing drawn: one flat colour."""
    from PIL import Image
    with Image.open(path) as im:
        return all(lo == hi for lo, hi in im.convert("RGB").getextrema())


# --- the build --------------------------------------------------------------------
def build_v2(samples: list[dict], corpus: dict[str, dict], set_id: str, secret: str, renderer, *,
             n_pairs: int = 300, mix: dict[str, float] | None = None, per_task: int = 2,
             model_share: float = 0.12, n_checks: int = 10, workers: int = 1,
             judge: dict | None = None, grade=None, log=print) -> tuple[list[dict], dict]:
    """(public items with picture sources under ``_img``, private key). ``renderer`` has
    ``ref(scene, rows)`` and ``answer(scene, ref)``; ``grade(task, scene)`` is the
    benchmark's grader (default `runner.grade_parsed`), used only to make sure a
    calibrated check is a scene the grader fails. ``judge`` maps (model, task, sample)
    to an image-judge verdict, if the judge was run."""
    if grade is None:
        grade = runner.grade_parsed
    mix = mix or dict.fromkeys(CLASSES, 1.0)
    kept, left_out = frame(samples, corpus)
    if not kept:
        raise SystemExit("no valid MVS scene in the run to make a pair from")
    cands = one_per_task_and_model(kept, secret, set_id)

    # Pairs. An answer whose picture cannot be made is dropped and the sample redrawn
    # without it, until every chosen pair has its pictures.
    banned: set[str] = set()
    failures: list[dict] = []
    refs: dict[tuple[str, int], dict] = {}
    for _ in range(20):
        chosen = select_pairs(cands, n_pairs, mix, per_task, model_share, frozenset(banned))
        need = sorted({(s["task_id"], s.get("matched_reference") or 0) for s in chosen} - set(refs))
        got = render_all(renderer, "ref", [(reference_of(corpus[t], m), target_rows_of(corpus[t], m))
                                           for t, m in need], workers)
        for (t, m), (res, err) in zip(need, got):
            if err:
                raise SystemExit(f"the reference of {t} did not render: {err}")
            refs[t, m] = res
        todo = [s for s in chosen if "_pics" not in s]
        got = render_all(renderer, "answer",
                         [(s["predicted"], refs[s["task_id"], s.get("matched_reference") or 0]) for s in todo], workers)
        bad = 0
        for s, (res, err) in zip(todo, got):
            if err:
                banned.add(s["id"])
                failures.append({"task": s["task_id"], "model": s["model"], "class": s["cls"], "error": err})
                bad += 1
            else:
                s["_pics"] = res
        log(f"  pairs: {len(chosen)} chosen, {len(todo)} answers drawn, {bad} could not be drawn")
        if not bad:
            break
    else:
        raise SystemExit("answers kept failing to render; see the errors above")

    items, key = [], {}

    def add(i: str, task: dict, ref: dict, pics: dict, info: dict, start: str | None = None) -> None:
        img = {"ref": ref["whole"], "out": pics["whole"]}
        if ref.get("target") and pics.get("target"):
            img.update(ref_target=ref["target"], out_target=pics["target"])
        if start:
            img["start"] = start
        item = {"id": i, "prompt": task["prompt"], "_img": img}
        if start:
            item["note"] = FOLLOWUP_NOTE
        items.append(item)
        key[i] = {**info, "task": task["id"], "has_target": "ref_target" in img}

    # A follow-up's scene before the request, from the reference's camera.
    ordered = balanced_order(chosen)
    with_start = []
    for s in ordered:
        ctx = corpus[s["task_id"]].get("context")
        if isinstance(ctx, dict) and isinstance(ctx.get("scene"), dict):
            with_start.append((s["id"], ctx["scene"], refs[s["task_id"], s.get("matched_reference") or 0]))
    got = render_all(renderer, "answer", [(scene, {**ref, "target_camera": None}) for _, scene, ref in with_start], workers)
    starts = {i: res["whole"] for (i, _, _), (res, err) in zip(with_start, got) if not err}

    for s in ordered:
        task = corpus[s["task_id"]]
        matched = s.get("matched_reference") or 0
        ref = refs[task["id"], matched]
        info = {"kind": "pair", "base_task": s["base"], "tier": s["tier"], "split": s.get("split"),
                "family": task.get("family"), "structure": (task.get("structures") or [None])[0],
                "model": s["model"], "sample": s["sample"], "success": bool(s.get("success")),
                "f1": s.get("f1"), "target_f1": s.get("target_f1"), "grader_class": s["cls"],
                "matched_reference": matched, "answer_blank": is_blank(s["_pics"]["whole"])}
        verdict = (judge or {}).get((s["model"], s["task_id"], s["sample"]))
        if verdict:
            info.update(judge_label=verdict["label"], judge_score=verdict.get("score"), judge=verdict.get("judge"))
        add(s["id"], task, ref, s["_pics"], info, starts.get(s["id"]))
    order = [it["id"] for it in items]

    # Checks: a pool per kind, on tasks with a target, tiers in turn, keyed order.
    pool = sorted((t for t in corpus.values()
                   if t["track"] == "mvs" and t["tier"] not in EXCLUDED_TIERS and t.get("target")
                   and not t.get("paraphrase_of") and target_rows_of(t)),
                  key=lambda t: item_id(secret, set_id, "check-task", t["id"]))
    by_tier = collections.defaultdict(list)
    for t in pool:
        by_tier[t["tier"]].append(t)
    turn = [t for group in zip(*(v for _, v in sorted(by_tier.items()))) for t in group] if by_tier else []
    turn += [t for t in pool if t not in turn]
    made = collections.Counter()
    rejected = collections.Counter()
    for n, task in enumerate(turn):
        if all(made[k] >= n_checks for k in CHECK_KINDS):
            break
        kind = min(CHECK_KINDS, key=lambda k: (made[k] >= n_checks, made[k], CHECK_KINDS.index(k)))
        ref, err = _call((renderer, "ref", (task["reference"], target_rows_of(task))))
        if err:
            rejected[f"{kind}: reference did not render"] += 1
            continue
        info: dict = {"kind": kind, "tier": task["tier"], "expected": "same" if kind == "check-same" else "different"}
        if kind == "check-same":
            other, ident = task["reference"], (task["id"],)
        elif kind == "check-different":
            far = next((o for o in turn[n + 1:] + turn[:n]
                        if set(o["structures"]).isdisjoint(task["structures"])), None)
            if far is None:
                rejected[f"{kind}: no task on another structure"] += 1
                continue
            other, ident = far["reference"], (task["id"], far["id"])
            info["other_task"] = far["id"]
        else:
            other = None
            for what, variant in calibrated_variants(task["reference"]):
                res = grade(task, variant)
                if not res.get("success") and (res.get("target_f1") is None or res["target_f1"] < 1.0):
                    other, ident, info["change"] = variant, (task["id"], what), what
                    break
            if other is None:
                rejected[f"{kind}: no single change the grader fails"] += 1
                continue
        if kind == "check-different":   # another structure, from its own cameras (ours would miss it)
            pics, err = _call((renderer, "ref", (other, target_rows_of(far))))
        else:
            pics, err = _call((renderer, "answer", (other, ref)))
        if err:
            rejected[f"{kind}: did not render"] += 1
            continue
        # The pictures must bear the known answer out, whole and zoomed.
        shares = [differing_share(ref[v], pics[v]) for v in ("whole", "target") if ref.get(v) and pics.get(v)]
        # (a calibrated change may be too small to see in the whole view; the zoom must show it)
        seen = {"check-same": max(shares) <= 0.0005, "check-different": min(shares) >= 0.002,
                "check-calibrated": max(shares) >= 0.002}[kind]
        if not seen:
            rejected[f"{kind}: pictures do not show the known answer"] += 1
            continue
        info["differing_pixels"] = [round(x, 5) for x in shares]
        add(item_id(secret, set_id, kind, *ident), task, ref, pics, info)
        made[kind] += 1
    short = {k: made[k] for k in CHECK_KINDS if made[k] < n_checks}
    if short:
        log(f"  checks: fewer than {n_checks} of some kind: {short}")

    counts = collections.Counter((key[i]["grader_class"], key[i]["tier"]) for i in order)
    full_key = {
        "set": set_id, "design": DESIGN_V2, "secret": secret, "items": key, "order": order,
        "per_rater": PER_RATER, "population": population_v2(kept),
        "sample": {"pairs": len(order), "per_task": per_task, "model_share": model_share,
                   "mix": mix, "cells": [[c, t, n] for (c, t), n in sorted(counts.items())],
                   "candidates": len(cands), "left_out": left_out,
                   "answers_not_drawn": failures, "checks_rejected": dict(rejected)},
    }
    items.sort(key=lambda it: it["id"])   # public order says nothing about kind or stratum
    return items, full_key


def seed_sql(key: dict) -> str:
    """The rating site's serving plan for this set: which id is a pair or a check and the
    order pairs open in. Private (it tells checks from pairs)."""
    rows = [(i, "pair", n) for n, i in enumerate(key["order"])]
    rows += [(i, v["kind"], n) for n, (i, v) in enumerate(sorted(key["items"].items()))
             if v["kind"] in CHECK_KINDS]
    values = ",\n".join(f"  ('{key['set']}', '{i}', '{kind}', {n})" for i, kind, n in rows)
    return (f"-- Serving plan of rating set {key['set']} ({len(rows)} items). PRIVATE: it tells checks from pairs.\n"
            "-- Run once in the rating site's SQL editor, after the a4-v2 migration in supabase/schema.sql.\n"
            "insert into rating_items (set_id, item, kind, ord) values\n" + values + "\n"
            "on conflict (set_id, item) do update set kind = excluded.kind, ord = excluded.ord;\n")


def private_place(path: pathlib.Path) -> bool:
    """True if a file at ``path`` could not be committed by accident: it lies outside
    any git work tree, or git ignores it."""
    d = path.resolve().parent
    while not d.exists():
        d = d.parent
    inside = subprocess.run(["git", "-C", str(d), "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True)
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return True
    return subprocess.run(["git", "-C", str(d), "check-ignore", "-q", str(path.resolve())]).returncode == 0


def common_box(paths: list[str], margin: float = 0.06, least: float = 0.5) -> tuple[int, int, int, int] | None:
    """One crop box for pictures taken from the same camera: the smallest box of the
    pictures' own shape that holds everything drawn in ANY of them, plus a margin, and
    never less than ``least`` of each side (so nothing is blown up more than twice).
    The same box on both sides keeps the comparison honest. None = keep the full frame."""
    from PIL import Image, ImageChops
    box, size = None, None
    for path in paths:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
        size = size or rgb.size
        if rgb.size != size:
            return None
        drawn = ImageChops.difference(rgb, Image.new("RGB", rgb.size, (255, 255, 255))).getbbox()
        if drawn:
            box = drawn if box is None else (min(box[0], drawn[0]), min(box[1], drawn[1]),
                                             max(box[2], drawn[2]), max(box[3], drawn[3]))
    if box is None:
        return None
    w, h = size
    bw = max((box[2] - box[0]) * (1 + 2 * margin), least * w)
    bh = max((box[3] - box[1]) * (1 + 2 * margin), least * h)
    bw = max(bw, bh * w / h)
    bh = bw * h / w
    if bw >= w or bh >= h:
        return None
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    x0 = min(max(cx - bw / 2, 0), w - bw)
    y0 = min(max(cy - bh / 2, 0), h - bh)
    return round(x0), round(y0), round(x0 + bw), round(y0 + bh)


def _jpeg(src: str, dst: pathlib.Path, quality: int, box: tuple[int, int, int, int] | None = None) -> None:
    from PIL import Image
    with Image.open(src) as im:  # flatten any transparency onto white, not black
        rgba = im.convert("RGBA")
        flat = Image.new("RGB", rgba.size, (255, 255, 255))
        flat.paste(rgba, mask=rgba.getchannel("A"))
        if box:
            flat = flat.crop(box).resize(rgba.size, Image.LANCZOS)
        flat.save(dst, "JPEG", quality=quality)


def write_v2(items: list[dict], key: dict, out: pathlib.Path, key_path: pathlib.Path,
             quality: int = 85, review: bool = True) -> None:
    """Public: ``out``/items.json and img/. Private, beside the key: the key, the serving
    plan (seed_rating_items.sql) and review/ (one sheet per item + index.tsv)."""
    from PIL import Image
    if not private_place(key_path):
        raise SystemExit(f"{key_path} is inside a git work tree and not ignored: the answer key "
                         "would be one `git add` from public. Put it outside git or under an ignored path.")
    (out / "img").mkdir(parents=True, exist_ok=True)
    for old in (out / "img").glob("*.jpg"):
        old.unlink()
    public = []
    for it in items:
        rec = {k: v for k, v in it.items() if not k.startswith("_")}
        img = it["_img"]
        # One crop per view, shared by every picture taken from that camera.
        boxes = {"whole": common_box([img[n] for n in ("ref", "out", "start") if n in img]),
                 "target": common_box([img[n] for n in ("ref_target", "out_target") if n in img])}
        for side, src in img.items():
            rec[side] = f"img/{it['id']}-{side}.jpg"
            _jpeg(src, out / rec[side], quality, boxes["target" if side.endswith("_target") else "whole"])
        public.append(rec)
    (out / "items.json").write_text(json.dumps(
        {"set": key["set"], "design": DESIGN_V2, "questions": QUESTIONS_V2,
         "goal": PER_RATER["goal"], "items": public}, indent=1) + "\n")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, indent=1, sort_keys=True) + "\n")
    key_path.chmod(0o600)
    seed = key_path.parent / "seed_rating_items.sql"
    seed.write_text(seed_sql(key))
    seed.chmod(0o600)
    if not review:
        return
    sheets = key_path.parent / "review"
    sheets.mkdir(exist_ok=True)
    for old in sheets.glob("*.jpg"):
        old.unlink()
    lines = ["item\tkind\tclass\ttier\ttask\tmodel\tsuccess\ttarget_f1\texpected"]
    for it in items:
        v = key["items"][it["id"]]
        names = [n for n in ("ref", "out", "ref_target", "out_target") if n in it["_img"]]
        tiles = [Image.open(out / f"img/{it['id']}-{n}.jpg").convert("RGB") for n in names]
        w, h = tiles[0].size
        sheet = Image.new("RGB", (2 * w + 6, (len(tiles) // 2) * (h + 6)), "white")
        for n, tile in enumerate(tiles):   # columns: reference | answer; rows: whole, target
            sheet.paste(tile, ((n % 2) * (w + 6), (n // 2) * (h + 6)))
        sheet.save(sheets / f"{it['id']}.jpg", "JPEG", quality=80)
        lines.append("\t".join(str(x) for x in (
            it["id"], v["kind"], v.get("grader_class", ""), v.get("tier", ""), v["task"], v.get("model", ""),
            v.get("success", ""), v.get("target_f1", ""), v.get("expected", ""))))
    (sheets / "index.tsv").write_text("\n".join(lines) + "\n")


def read_judge(path: pathlib.Path | None) -> dict | None:
    """Image-judge verdicts, one JSON object per line: model, task_id, sample, label
    ("same" / "different"), optionally score and judge."""
    if path is None:
        return None
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r["label"] not in ("same", "different"):
                raise SystemExit(f"{path}: judge label must be same or different, got {r['label']!r}")
            out[r["model"], r["task_id"], r["sample"]] = r
    return out


def plan_table(key_or_cells, population: dict) -> str:
    """The sample by grader class and tier, beside what the run holds."""
    have = collections.Counter({(c, t): n for c, t, n in key_or_cells})
    run = collections.Counter({(c, t): n for t, c, n in population["cells"]})
    tiers = sorted({t for _, t in run})
    lines = ["tier".ljust(14) + "".join(f"{c + ' (run)':>20}" for c in CLASSES)]
    for t in tiers:
        lines.append(t.ljust(14) + "".join(f"{have[c, t]:>10} ({run[c, t]:>6})" for c in CLASSES))
    lines.append("total".ljust(14) + "".join(
        f"{sum(have[c, t] for t in tiers):>10} ({sum(run[c, t] for t in tiers):>6})" for c in CLASSES))
    return "\n".join(lines)


def main_v2(a, ap) -> None:
    from molbench import tasks as tasks_mod
    set_id = a.set_id or "a4-v2"
    if set_id == "a4-v1":
        ap.error("a4-v1 is the pilot set (design v1); give a v2 set its own id")
    corpus = {t["id"]: t for t in tasks_mod.load_corpus()}
    samples = read_run(a.results, a.condition)
    mix = dict(zip(CLASSES, (float(x) for x in a.mix.split(":"))))
    if len(mix) != 3 or min(mix.values()) < 0 or not sum(mix.values()):
        ap.error("--mix is right:close:wrong, e.g. 1:1:1")
    if a.plan_only:
        kept, left_out = frame(samples, corpus)
        cands = one_per_task_and_model(kept, "00" * 32, set_id)
        chosen = select_pairs(cands, a.pairs, mix, a.per_task, a.model_share)
        cells = collections.Counter((s["cls"], s["tier"]) for s in chosen)
        print(f"{len(samples)} samples; {len(kept)} valid MVS scenes; left out: {left_out}")
        print(f"{len(cands)} (task, model) candidates; {len(chosen)} pairs with a throwaway key "
              f"(the real build keys the choice):")
        print(plan_table([[c, t, n] for (c, t), n in cells.items()], population_v2(kept)))
        print(f"models: {len({s['model'] for s in chosen})}; tasks: {len({s['base'] for s in chosen})}")
        return
    if not (a.out and a.key):
        ap.error("--out and --key are required to build a set")
    if not private_place(a.key):
        ap.error(f"{a.key} is inside a git work tree and not ignored; the key must stay private")
    secret = json.loads(a.key.read_text())["secret"] if a.key.exists() else secrets.token_hex(32)
    cache = a.cache or a.key.parent / "render_cache"
    renderer = MolstarRenderer(cache, a.width, a.height, network=not a.offline)
    items, key = build_v2(samples, corpus, set_id, secret, renderer, n_pairs=a.pairs, mix=mix,
                          per_task=a.per_task, model_share=a.model_share, n_checks=a.checks,
                          workers=a.jobs, judge=read_judge(a.judge))
    key["run"] = {"dir": str(a.results), "condition": a.condition}
    write_v2(items, key, a.out, a.key)
    kinds = collections.Counter(v["kind"] for v in key["items"].values())
    print(f"{len(items)} items -> {a.out} ({dict(kinds)})")
    print(plan_table(key["sample"]["cells"], key["population"]))
    s = key["sample"]
    print(f"answers that could not be drawn (replaced): {len(s['answers_not_drawn'])}; "
          f"checks rejected: {s['checks_rejected'] or 'none'}")
    print(f"private: key, seed_rating_items.sql and review/ -> {a.key.parent}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", type=pathlib.Path, help="directory of scorecards with escalation")
    ap.add_argument("--set", dest="set_id", help="set id (default: a4-v1, or a4-v2 for a manifest run)")
    ap.add_argument("--out", type=pathlib.Path, help="public item dir")
    ap.add_argument("--key", type=pathlib.Path, help="private answer key (json)")
    ap.add_argument("--population-only", type=pathlib.Path, metavar="PATH",
                    help="write only the run's judged-pair counts per task and label, then stop")
    ap.add_argument("--controls", type=int, default=12, help="checks of each kind")
    ap.add_argument("--seed", type=int, default=4)
    ap.add_argument("--max-per-task", type=int, default=3, help="judged pairs kept per task")
    ap.add_argument("--keep", type=pathlib.Path,
                    help="JSON list of item ids already rated; kept first under the cap")
    ap.add_argument("--public", type=pathlib.Path, default=REPO / "docs" / "gallery_data.json",
                    help="published gallery; its pairs are left out so raters can't copy a verdict")
    v2 = ap.add_argument_group("design v2 (a manifest run: a directory with samples/<condition>/)")
    v2.add_argument("--condition", default="spec", help="the run's condition to sample (default: spec)")
    v2.add_argument("--pairs", type=int, default=300, help="pairs in the set (default 300; paper/a4/FINAL_CALL.md)")
    v2.add_argument("--mix", default="1:1:1", help="shares of the grader's classes right:close:wrong")
    v2.add_argument("--per-task", type=int, default=2, help="most pairs of one task (a paraphrase counts as its original)")
    v2.add_argument("--model-share", type=float, default=0.12, help="largest share of the set from one model")
    v2.add_argument("--checks", type=int, default=10, help="pool of attention checks of each of the three kinds")
    v2.add_argument("--judge", type=pathlib.Path, help="image-judge verdicts (JSON lines: model, task_id, sample, label)")
    v2.add_argument("--jobs", type=int, default=4, help="renders at a time")
    v2.add_argument("--offline", action="store_true",
                    help="refuse every download while drawing (an answer that loads a structure "
                         "outside the frozen panel then cannot be drawn and is replaced)")
    v2.add_argument("--cache", type=pathlib.Path, help="render cache (default: render_cache/ beside the key)")
    v2.add_argument("--width", type=int, default=800)
    v2.add_argument("--height", type=int, default=600)
    v2.add_argument("--plan-only", action="store_true", help="print the sample by class and tier; draw nothing")
    a = ap.parse_args(argv)
    if (a.results / "samples").is_dir():
        return main_v2(a, ap)
    a.set_id = a.set_id or "a4-v1"
    pop = population(a.results, public_pairs(a.public))
    if a.population_only:
        a.population_only.write_text(json.dumps(pop, indent=1) + "\n")
        print(f"{sum(n for _, _, n in pop['cells'])} judged pairs -> {a.population_only}")
        return
    if not (a.out and a.key):
        ap.error("--out and --key are required to build a set")
    secret = (json.loads(a.key.read_text())["secret"] if a.key.exists()
              else secrets.token_hex(32))
    keep = set(json.loads(a.keep.read_text())) if a.keep else set()
    items, key = build(a.results, a.set_id, a.controls, a.seed, secret, public_pairs(a.public),
                       a.max_per_task, keep)
    write(items, key, a.set_id, secret, a.out, a.key, population=pop)
    kinds = {}
    for v in key.values():
        kinds[v["kind"]] = kinds.get(v["kind"], 0) + 1
    print(f"{len(items)} items -> {a.out} ({kinds}); key -> {a.key}")


if __name__ == "__main__":
    main()
