#!/usr/bin/env python3
"""
A4: how well does the VLM judge agree with human raters?

Joins the ratings collected on the rating site with the private answer key written
by scripts/build_rating_set.py, and reports:

  * per rater: items rated and attention-check accuracy (raters below --min-checks
    are dropped from everything after)
  * human vs human: Fleiss' kappa over the judged items with 2+ ratings
  * human vs VLM: the human majority per item against the judge's label — Cohen's
    kappa, raw agreement, and the number that matters under the rescue-only
    policy: of the pairs the judge called "same", how many humans call same too

"Can't tell" answers count as rated but carry no label.

    python scripts/agreement.py results/a4/a4-v1/key.json --from-supabase
    python scripts/agreement.py results/a4/a4-v1/key.json ratings.json

`--from-supabase` reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from the
environment (the molstar-chat-driver evaluator project).
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import urllib.request

LABELS = ("same", "different")


def fetch_ratings(set_id: str) -> list[dict]:
    url = f"{os.environ['SUPABASE_URL']}/rest/v1/ratings?set_id=eq.{set_id}&select=*"
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    req = urllib.request.Request(url, headers={"apikey": key, "authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fleiss_kappa(counts: list[collections.Counter]) -> float | None:
    """Fleiss' kappa with a varying number of raters per item (each item needs >= 2)."""
    counts = [c for c in counts if sum(c.values()) >= 2]
    if not counts:
        return None
    p_items = [sum(v * (v - 1) for v in c.values()) / (sum(c.values()) * (sum(c.values()) - 1))
               for c in counts]
    total = sum(sum(c.values()) for c in counts)
    p_cat = [sum(c[lab] for c in counts) / total for lab in LABELS]
    p_bar, p_e = sum(p_items) / len(p_items), sum(p * p for p in p_cat)
    return None if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    n = len(pairs)
    p_o = sum(a == b for a, b in pairs) / n
    p_e = sum((sum(a == lab for a, _ in pairs) / n) * (sum(b == lab for _, b in pairs) / n)
              for lab in LABELS)
    return None if p_e == 1 else (p_o - p_e) / (1 - p_e)


def majority(c: collections.Counter) -> str | None:
    if c["same"] == c["different"]:
        return None
    return "same" if c["same"] > c["different"] else "different"


def analyse(key: dict, ratings: list[dict], min_checks: float) -> dict:
    items = key["items"]
    by_rater = collections.defaultdict(list)
    for r in ratings:
        if r["item"] in items:
            by_rater[r["evaluator_token"]].append(r)

    raters, kept = {}, set()
    for tok, rs in by_rater.items():
        checks = [r for r in rs if items[r["item"]]["kind"].startswith("control")
                  and r["label"] in LABELS]
        right = sum(r["label"] == items[r["item"]]["expected"] for r in checks)
        acc = right / len(checks) if checks else None
        raters[tok[:8]] = {"rated": len(rs), "checks": len(checks), "check_accuracy": acc}
        if acc is None or acc >= min_checks:
            kept.add(tok)

    votes = collections.defaultdict(collections.Counter)
    for r in ratings:
        if r["evaluator_token"] in kept and r["label"] in LABELS and items.get(r["item"], {}).get("kind") == "vlm":
            votes[r["item"]][r["label"]] += 1

    vs_vlm = [(m, items[i]["vlm_label"]) for i, c in votes.items() if (m := majority(c))]
    judged_same = [m for m, v in vs_vlm if v == "same"]
    confusion = collections.Counter(f"human {m} / vlm {v}" for m, v in vs_vlm)
    return {
        "set": key["set"],
        "raters": raters,
        "raters_kept": len(kept),
        "items_rated": len(votes),
        "items_with_2plus": sum(sum(c.values()) >= 2 for c in votes.values()),
        "human_fleiss_kappa": fleiss_kappa(list(votes.values())),
        "vlm_items_with_majority": len(vs_vlm),
        "human_vs_vlm_cohen_kappa": cohen_kappa(vs_vlm),
        "human_vs_vlm_agreement": sum(m == v for m, v in vs_vlm) / len(vs_vlm) if vs_vlm else None,
        "rescue_precision": judged_same.count("same") / len(judged_same) if judged_same else None,
        "confusion": dict(confusion),
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("key", type=pathlib.Path)
    ap.add_argument("ratings", type=pathlib.Path, nargs="?", help="ratings JSON (a list of rows)")
    ap.add_argument("--from-supabase", action="store_true")
    ap.add_argument("--min-checks", type=float, default=0.8,
                    help="drop raters whose attention-check accuracy is below this")
    a = ap.parse_args(argv)
    key = json.loads(a.key.read_text())
    if a.from_supabase:
        ratings = fetch_ratings(key["set"])
    elif a.ratings:
        ratings = json.loads(a.ratings.read_text())
    else:
        ap.error("give a ratings file or --from-supabase")
    print(json.dumps(analyse(key, ratings, a.min_checks), indent=2))


if __name__ == "__main__":
    main()
