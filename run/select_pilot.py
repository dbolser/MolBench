#!/usr/bin/env python3
"""
Choose the tasks of the provider-path pilot and write them into ``run/pilot.toml``.

    python run/select_pilot.py            # rewrite the task list in run/pilot.toml
    python run/select_pilot.py --check    # exit 1 if the list in the file is out of date
    python run/select_pilot.py --show     # print what was chosen and why

The pilot proves the real provider path (request, archive, parse, grade, scorecards)
on a handful of tasks before the paid run. Its tasks are picked by rule from the corpus
on disk, so that every tier of each track and every special kind of task passes through
a real model once:

* every tier x track: one public task and one held-back task; a second public task from
  another template in the tiers that exist on both tracks with more than one twin kind
  (translation, grounded, clinical, follow-up);
* twins: in every tier that has them, the public MVS pick and its API twin;
* follow-ups: per track, one edit that must leave part of the start state alone and one
  "no change" task;
* accept-set: the accept-set tier itself;
* paraphrases: one request with all three phrasings on each track (a clinical twin
  pair, so the phrasings also pass through the grounding condition);
* the grounding condition takes the resolve and clinical MVS picks; the
  structured-output condition takes the translation, follow-up and accept-set picks.

"Picked" always means: the candidate with the smallest SHA-256 of ``pilot|<task id>``,
so the choice depends on nothing but the task ids. No network, no model.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import manifest as manifest_mod  # noqa: E402
from molbench import runner  # noqa: E402
from molbench import tasks as tasks_mod  # noqa: E402

PILOT = REPO / "run" / "pilot.toml"
BEGIN = "# BEGIN TASKS (written by run/select_pilot.py; do not edit by hand)"
END = "# END TASKS"
SECOND_PUBLIC_TIERS = ("translation", "grounded", "clinical", "followup")


def _rank(task: dict) -> str:
    return hashlib.sha256(f"pilot|{task['id']}".encode()).hexdigest()


def _first(tasks: list[dict]) -> dict | None:
    return min(tasks, key=_rank) if tasks else None


def select(corpus: list[dict]) -> list[tuple[dict, str]]:
    """[(task, why it is in the pilot), ...] in the order they are run."""
    by_id = {t["id"]: t for t in corpus}
    originals = [t for t in corpus if not t.get("paraphrase_of")]
    paraphrased = {t["paraphrase_of"] for t in corpus if t.get("paraphrase_of")}
    chosen: dict[str, tuple[dict, str]] = {}

    def take(task: dict | None, why: str) -> None:
        if task is not None and task["id"] not in chosen:
            chosen[task["id"]] = (task, why)

    def cell(track: str, tier: str, **want) -> list[dict]:
        return [t for t in originals if t["category"] == track and t["tier"] == tier
                and all(t.get(k) == v for k, v in want.items())]

    for tier in tasks_mod.TIERS:
        # Public MVS pick: a task with an API twin where the tier has twins; in the
        # clinical tier, a twin pair that also has paraphrases.
        mvs_pub = cell("mvs", tier, split="public")
        twinned = [t for t in mvs_pub if t.get("twin_of") in by_id]
        if tier == "clinical":
            both = [t for t in twinned if t["id"] in paraphrased and t["twin_of"] in paraphrased]
            twinned = both or twinned
        pick = _first(twinned) or _first(mvs_pub)
        take(pick, f"{tier}, MVS, public" + (", twin" if pick and pick.get("twin_of") else ""))
        twin = by_id.get(pick.get("twin_of")) if pick else None
        if twin is not None:
            take(twin, f"{tier}, API, public, twin of {pick['id']}")
        else:
            take(_first(cell("api_calling", tier, split="public")), f"{tier}, API, public")
        for track, name in (("mvs", "MVS"), ("api_calling", "API")):
            take(_first(cell(track, tier, split="heldback")), f"{tier}, {name}, held back")
        if tier in SECOND_PUBLIC_TIERS:
            for track, name in (("mvs", "MVS"), ("api_calling", "API")):
                families = {t["family"] for t, _ in chosen.values()
                            if t["category"] == track and t["tier"] == tier}
                rest = [t for t in cell(track, tier, split="public")
                        if t["family"] not in families and t["id"] not in chosen]
                if tier == "followup":  # an edit that has something to leave alone
                    rest = [t for t in rest if runner.preserved_parts(t)] or rest
                take(_first(rest), f"{tier}, {name}, public, second template")
    for track, name in (("mvs", "MVS"), ("api_calling", "API")):
        noop = [t for t in originals if t["category"] == track and t.get("context")
                and t["context"].get("noop") and t["split"] == "public"]
        take(_first(noop), f"follow-up with no change, {name}")
    # Every phrasing of the paraphrased originals already chosen in the clinical tier.
    for tid in [i for i, (t, _) in chosen.items() if t["tier"] == "clinical" and i in paraphrased]:
        for t in sorted((t for t in corpus if t.get("paraphrase_of") == tid), key=lambda t: t["id"]):
            take(t, f"paraphrase ({t['style']}) of {tid}")
    return list(chosen.values())


def block(picks: list[tuple[dict, str]]) -> str:
    width = max(len(t["id"]) for t, _ in picks) + 3
    lines = [BEGIN, "tasks = ["]
    lines += [f"    {(chr(34) + t['id'] + chr(34) + ','):<{width}}  # {why}" for t, why in picks]
    return "\n".join(lines + ["]", END])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args(argv)
    picks = select(runner.load_tasks(list(manifest_mod.TRACKS)))
    if args.show:
        for t, why in picks:
            print(f"{t['id']:<52} {why}")
        print(f"{len(picks)} tasks")
        return 0
    text = PILOT.read_text(encoding="utf-8")
    a, b = text.index(BEGIN), text.index(END) + len(END)
    new = text[:a] + block(picks) + text[b:]
    if args.check:
        if new != text:
            print(f"{PILOT} is out of date: run python run/select_pilot.py", file=sys.stderr)
            return 1
        print(f"{PILOT}: task list is up to date ({len(picks)} tasks)")
        return 0
    PILOT.write_text(new, encoding="utf-8")
    print(f"wrote {len(picks)} tasks to {PILOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
