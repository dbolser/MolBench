#!/usr/bin/env python3
"""
A4 power analysis: how many pairs and raters give a 95% interval of about +/- 0.10 on kappa?

Simulates rating studies from the numbers measured so far (paper/a4/tables/agreement.json,
"all raters", unweighted) and reports the expected half-width of the 95% interval for

  * human-vs-judge Cohen's kappa (every rating against the judge's label),
  * rescue precision (of the answers on pairs the judge calls "same", the share saying same),
  * human-vs-human Fleiss' kappa (needs 2+ raters per pair),

for a grid of designs: number of judged pairs x raters per pair, and for two mixes of the
set: the judge-"same" share of the current set, and an even 50:50 split (the v2 proposal).

The model. A pair has a "true" human answer. It is "same" with probability A if the judge
said same and B if the judge said different. Each rater reports the true answer, except
with probability E they report the other one. A and B are fitted so the simulated share
of "same" answers matches the measured one. E is NOT known yet: only 5 pairs have two
labelled answers. So it is varied: the share of pairs on which two raters split is set to
10%, 20% and 30% (E = 5%, 11%, 18%).

Pairs from one task are not independent. The measured cost of that (the ratio of the
task-level to the pair-level bootstrap SE of kappa) widens every simulated interval.

    python paper/a4/power.py            # writes paper/a4/tables/power.json and power.md

Stdlib only; fixed seed; about two minutes.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics

HERE = pathlib.Path(__file__).resolve().parent
SPLITS = (0.10, 0.20, 0.30)         # share of pairs on which two raters disagree
PAIRS = (113, 150, 200, 250, 300, 400)
RATERS = (1, 2, 3)
MIXES = (None, 0.5)                 # judge-"same" share of the set: None = as in the current set
TARGET = 0.10


def flip_rate(split: float) -> float:
    """Per-rater error E such that two raters split on `split` of pairs: 2E(1-E) = split."""
    return (1 - math.sqrt(1 - 2 * split)) / 2


def latent(p_observed: float, e: float) -> float:
    """Share of pairs truly "same", given the share of answers that say same and the error E."""
    return min(1.0, max(0.0, (p_observed - e) / (1 - 2 * e)))


def cohen(a: int, b: int, c: int, d: int) -> float | None:
    """Kappa of a 2x2 table: a = both same, b = human same/judge different, c = the reverse, d."""
    n = a + b + c + d
    p_o, h, j = (a + d) / n, (a + b) / n, (a + c) / n
    p_e = h * j + (1 - h) * (1 - j)
    return None if p_e == 1 else (p_o - p_e) / (1 - p_e)


def simulate(rng: random.Random, n: int, k: int, judge_same: float, a: float, b: float, e: float):
    """One study: (human-vs-judge kappa, human-vs-human Fleiss kappa or None, rescue precision)."""
    t = [0, 0, 0, 0]
    agree_pairs = same_votes = 0
    for i in range(n):
        j_same = i < round(n * judge_same)
        truth = rng.random() < (a if j_same else b)
        votes = sum((rng.random() >= e) == truth for _ in range(k))  # answers saying "same"
        t[0 if j_same else 1] += votes
        t[2 if j_same else 3] += k - votes
        agree_pairs += votes * (votes - 1) + (k - votes) * (k - votes - 1)
        same_votes += votes
    kappa = cohen(*t)
    fleiss = None
    if k >= 2:
        p_bar = agree_pairs / (n * k * (k - 1))
        p = same_votes / (n * k)
        p_e = p * p + (1 - p) * (1 - p)
        fleiss = None if p_e == 1 else (p_bar - p_e) / (1 - p_e)
    return kappa, fleiss, t[0] / (t[0] + t[2]) if t[0] + t[2] else None


def half_width(xs: list[float]) -> float:
    return 1.96 * statistics.stdev(xs)


def run(agreement: dict, sims: int, seed: int) -> dict:
    c = agreement["cohorts"]["all"]
    t = c["unweighted"]["table"]
    ss, sd = t["human same / judge same"], t["human same / judge different"]
    ds, dd = t["human different / judge same"], t["human different / judge different"]
    p_same_given_same, p_same_given_diff = ss / (ss + ds), sd / (sd + dd)
    judge_same = agreement["rating_set"]["judge_same"] / agreement["rating_set"]["judged_pairs"]
    cluster = max(1.0, c["kappa_se_by_task_over_by_pair"] or 1.0)
    rng = random.Random(seed)
    grid = []
    for mix, split, n, k in ((m, s, n, k) for m in MIXES for s in SPLITS for n in PAIRS for k in RATERS):
                e = flip_rate(split)
                a, b = latent(p_same_given_same, e), latent(p_same_given_diff, e)
                share = judge_same if mix is None else mix
                res = [simulate(rng, n, k, share, a, b, e) for _ in range(sims)]
                kj = [x[0] for x in res if x[0] is not None]
                kh = [x[1] for x in res if x[1] is not None]
                pr = [x[2] for x in res if x[2] is not None]
                grid.append({"judge_same_share": round(share, 3), "split": split, "pairs": n,
                             "raters_per_pair": k, "ratings": n * k,
                             "kappa_human_judge": round(statistics.fmean(kj), 3),
                             "halfwidth_human_judge": round(half_width(kj) * cluster, 3),
                             "rescue_precision": round(statistics.fmean(pr), 3),
                             "halfwidth_rescue_precision": round(half_width(pr) * cluster, 3),
                             "kappa_human_human": round(statistics.fmean(kh), 3) if kh else None,
                             "halfwidth_human_human": round(half_width(kh) * cluster, 3) if kh else None})
    return {"inputs": {"source": f"{agreement['set']} export of {agreement['exported_at']}, all raters, unweighted",
                       "p_human_same_given_judge_same": round(p_same_given_same, 3),
                       "p_human_same_given_judge_different": round(p_same_given_diff, 3),
                       "judge_same_share_of_set": round(judge_same, 3),
                       "task_clustering_factor": cluster, "sims": sims, "seed": seed,
                       "measured_kappa": round(c["unweighted"]["per_rating"]["cohen_kappa"]["est"], 3),
                       "measured_halfwidth": round((c["unweighted"]["per_rating"]["cohen_kappa"]["hi"]
                                                    - c["unweighted"]["per_rating"]["cohen_kappa"]["lo"]) / 2, 3)},
            "grid": grid}


def markdown(res: dict) -> str:
    i = res["inputs"]
    L = ["<!-- generated by paper/a4/power.py; do not edit -->", "",
         "# Rating study: expected interval half-widths", "",
         f"Simulated from the {i['source']}: humans say \"same\" on "
         f"{i['p_human_same_given_judge_same']:.0%} of the judge's \"same\" pairs and "
         f"{i['p_human_same_given_judge_different']:.0%} of its \"different\" pairs; "
         f"{i['judge_same_share_of_set']:.0%} of the current set is judge-\"same\". Every half-width is multiplied by "
         f"{i['task_clustering_factor']} for pairs sharing a task. {i['sims']} simulated studies per cell.", "",
         f"Check against the real data: measured kappa {i['measured_kappa']}, measured half-width "
         f"{i['measured_halfwidth']} (114 labelled ratings on 109 pairs).", "",
         "Half-width of the 95% interval. \"Split\" is the share of pairs on which two raters disagree - "
         "not yet measurable, so three cases are shown.", ""]
    shares = sorted({g["judge_same_share"] for g in res["grid"]})
    for share in shares:
        for name, hw, kk in (("Human vs judge (Cohen's kappa)", "halfwidth_human_judge", "kappa_human_judge"),
                             ("Rescue precision", "halfwidth_rescue_precision", "rescue_precision"),
                             ("Human vs human (Fleiss' kappa)", "halfwidth_human_human", "kappa_human_human")):
            L += [f"## {name}, {share:.0%} of the set judge-\"same\"", "",
                  "| judged pairs | raters per pair | ratings | " + " | ".join(f"split {s:.0%}" for s in SPLITS) + " |",
                  "|---|---|---|" + "---|" * len(SPLITS)]
            for n in PAIRS:
                for k in RATERS:
                    cells = [g for g in res["grid"] if (g["pairs"], g["raters_per_pair"], g["judge_same_share"]) == (n, k, share)]
                    if cells[0][hw] is None:
                        continue
                    vals = " | ".join(f"±{g[hw]:.2f}{' ✓' if g[hw] <= TARGET + 0.005 else ''} (≈{g[kk]:.2f})" for g in cells)
                    L.append(f"| {n} | {k} | {n * k} | {vals} |")
            L.append("")
    L.append(f"✓ = at or under the ±{TARGET:.2f} target. In brackets: the expected value of the measure itself.")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agreement", type=pathlib.Path, default=HERE / "tables" / "agreement.json")
    ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=4)
    a = ap.parse_args(argv)
    res = run(json.loads(a.agreement.read_text()), a.sims, a.seed)
    (HERE / "tables" / "power.json").write_text(json.dumps(res, indent=1) + "\n")
    (HERE / "tables" / "power.md").write_text(markdown(res))
    print(markdown(res))


if __name__ == "__main__":
    main()
