# Human rating study (A4): readout of set a4-v1

Snapshot: ratings exported 2026-11-12. All numbers come from
[`tables/agreement.md`](tables/agreement.md) (full detail in `tables/agreement.json`) and
[`tables/power.md`](tables/power.md). Both are generated; see "How to rebuild" at the end.

## The answer

**The study is a pilot. It does not yet validate the image-pair judge, and the paper must not say
it does.**

- When the judge says a model's scene is the "same" as the reference (a *rescue*), people agreed
  **74% of the time (95% interval 57% to 89%)**. Without the benchmark author's own ratings:
  **62% (40% to 85%)**.
- There is **no usable human-vs-human number**: only 5 pairs have two labelled answers, and the
  two people split on 3 of them.
- The good news for the paper: the judge is a side column and its rescues move a model's mean F1
  by at most 0.028 (October run). Even if 4 in 10 rescues were wrong, no headline number changes
  by more than about 0.01.

## What was collected

| | |
|---|---|
| Rating set | 137 items: 113 judged pairs (judge says same: 38, different: 75; 44 tasks, 15 models) + 12 known-same and 12 known-different attention checks |
| Ratings in the database | 158, from 3 people |
| Dropped | 12 early ratings by R1 on items later removed from the set. 0 from testing-only tokens (the test token never rated). |
| Analysed | 146 ratings: 121 on judged pairs (114 with a label, 7 "can't tell"), 25 on checks |
| Pairs rated | 109 of 113 have at least one labelled answer; 104 have exactly one; **5 have two** |

Raters are pseudonyms. R1 is the benchmark author (his genuine trial ratings). R2 and R3 are
independent volunteers.

| rater | role | judged pairs rated | "can't tell" | known-same checks right | known-different checks right | median seconds per item |
|---|---|---|---|---|---|---|
| R1 | author | 50 | 1 | none shown | none shown | 6.4 |
| R2 | rater | 38 | 0 | 8 of 8 | 9 of 9 | 11.7 |
| R3 | rater | 33 | 6 | 5 of 5 | 2 of 3 (1 "can't tell") | 14.9 |

**Attention checks.** Nobody gave a wrong answer on a check: 24 of 25 right, and the one miss was a
"can't tell". But the rule written into the analysis before the data (at least 80% right on *each*
kind of check, "can't tell" counts as a miss) passes **only R2**:

- R1 was never shown a check (he has no rating on any check item).
- R3 has 2 of 3 on one kind, which is 67%.

So every result below is given three ways: all raters, without the author, and R2 alone (the only
rater who passes the rule as written). Using all three raters is a deviation from the rule, and
the paper should say so if it quotes an all-rater number.

## Human vs judge

All intervals are 95% bootstrap intervals that resample whole tasks, because pairs from the same
task share a prompt and a reference.

Plain meaning of each measure:

- **Raw agreement**: share of human answers that match the judge's label.
- **Cohen's kappa**: agreement beyond what chance would give; 0 = chance, 1 = perfect.
- **Gwet's AC1**: like kappa, but not dragged down when one answer is much more common.
- **Rescue precision**: of the pairs the judge calls "same", the share people also call same.
- **Sensitivity**: of the pairs people call same, the share the judge calls same.
- **Specificity**: of the pairs people call different, the share the judge calls different.
- **Balanced accuracy**: the mean of sensitivity and specificity.

### On the rating set as built (unweighted)

| measure | all raters (R1–R3) | without the author (R2, R3) | passes the check rule (R2) |
|---|---|---|---|
| labelled ratings / pairs / tasks | 114 / 109 / 44 | 65 / 63 / 35 | 38 / 38 / 27 |
| raw agreement | 0.79 (0.70 to 0.87) | 0.75 (0.64 to 0.85) | 0.74 (0.59 to 0.88) |
| Cohen's kappa | 0.54 (0.34 to 0.71) | 0.44 (0.19 to 0.65) | 0.42 (0.13 to 0.72) |
| Gwet's AC1 | 0.61 (0.44 to 0.77) | 0.56 (0.33 to 0.74) | 0.52 (0.22 to 0.79) |
| rescue precision (per rating) | 0.74 (0.57 to 0.89) | 0.62 (0.40 to 0.85) | 0.53 (0.29 to 0.82) |
| judge "different" confirmed (per pair) | 0.83 (0.72 to 0.93) | 0.81 (0.71 to 0.91) | 0.87 (0.72 to 1.00) |
| sensitivity | 0.68 (0.49 to 0.86) | 0.60 (0.39 to 0.81) | 0.73 (0.45 to 1.00) |
| specificity | 0.87 (0.77 to 0.95) | 0.81 (0.66 to 0.93) | 0.74 (0.55 to 0.91) |
| balanced accuracy | 0.78 (0.67 to 0.88) | 0.71 (0.58 to 0.82) | 0.73 (0.58 to 0.89) |

The counts behind the all-rater column: human same / judge same 28; human same / judge
different 14; human different / judge same 10; human different / judge different 62.

### Weighted back to the whole run

The set was stratified: it holds 38 of the run's 55 eligible judge-"same" pairs (69%) but only 75
of the 206 judge-"different" pairs (36%), and at most 3 pairs per task. Each rated pair is weighted
by how many pairs of its task and judge label it stands for, then scaled so each label adds up to
its total in the run (261 pairs; pairs shown on the public gallery were never eligible).

| measure | all raters | without the author | R2 only |
|---|---|---|---|
| raw agreement | 0.80 (0.71 to 0.88) | 0.66 (0.50 to 0.82) | 0.71 (0.49 to 0.92) |
| Cohen's kappa | 0.50 (0.28 to 0.69) | 0.22 (−0.02 to 0.54) | 0.28 (−0.05 to 0.75) |
| Gwet's AC1 | 0.68 (0.50 to 0.82) | 0.42 (0.06 to 0.71) | 0.53 (0.04 to 0.89) |
| rescue precision (per pair) | 0.78 (0.59 to 0.92) | 0.61 (0.36 to 0.85) | 0.58 (0.27 to 0.87) |
| sensitivity | 0.54 (0.32 to 0.77) | 0.33 (0.15 to 0.65) | 0.38 (0.12 to 1.00) |
| specificity | 0.93 (0.87 to 0.97) | 0.87 (0.73 to 0.96) | 0.87 (0.70 to 0.96) |
| balanced accuracy | 0.74 (0.63 to 0.85) | 0.60 (0.49 to 0.77) | 0.63 (0.47 to 0.94) |

Reading: over the whole run the judge is cautious. It rarely calls "same" what people call
different (specificity 0.93), and it misses about half of what people would accept (sensitivity
0.54). Under the rescue-only policy a miss costs nothing (the tree score stands), so the number
that matters is rescue precision. The without-author columns rest on 63 pairs with weights up to
about 5; treat them as rough. Without the author the weighted kappa interval includes zero: on
independent raters alone, agreement beyond chance over the whole run is not yet shown.

### The raters differ more than the intervals show

| rater | labelled ratings | on judge-"same" pairs | raw agreement | Cohen's kappa | rescue precision |
|---|---|---|---|---|---|
| R1 (author) | 49 | 17 | 0.84 (0.69 to 0.95) | 0.66 (0.36 to 0.88) | 0.88 = 15 of 17 |
| R2 | 38 | 15 | 0.74 (0.59 to 0.88) | 0.42 (0.13 to 0.72) | 0.53 = 8 of 15 |
| R3 | 27 | 6 | 0.78 (0.61 to 0.93) | 0.48 (0.17 to 0.79) | 0.83 = 5 of 6 |

The three people rated almost entirely different pairs, so this is not a clean rater comparison.
But a spread from 0.53 to 0.88 with 3 raters means the true uncertainty is wider than any interval
above: the bootstrap resamples tasks, not people, and 3 people are too few to resample.

### Human vs human

| | all raters | without the author |
|---|---|---|
| pairs with two labelled answers | 5 | 2 |
| pairs where the two split | 3 | 0 |
| raw agreement | 0.40 (0.00 to 0.80) | not meaningful (2 pairs) |
| Fleiss' kappa | −0.20 (−1.00 to 0.60) | not meaningful |
| Krippendorff's alpha | −0.08 (−0.80 to 0.64) | not meaningful |

Unusable. All 3 splits are R1 "different" against R3 "same". The cause is the serving order on the
rating site: it hands out the least-rated item first, so 146 ratings were spread one-deep over 137
items before any item got a second rating.

### By difficulty tier and by model

Too thin to claim anything (full tables in `tables/agreement.md`).

| tier (all raters) | labelled ratings | raw agreement | Cohen's kappa |
|---|---|---|---|
| Translation | 37 | 0.86 (0.76 to 0.97) | 0.68 (0.44 to 0.93) |
| Grounded (ligand / disulfide) | 16 | 0.75 (0.47 to 0.94) | 0.38 (0.00 to 0.85) |
| Clinical (SIFTS / ClinVar) | 27 | 0.78 (0.62 to 0.93) | 0.27 (−0.17 to 0.71) |
| Resolution (by name) | 19 | 0.79 (0.58 to 0.95) | 0.52 (−0.02 to 0.88) |
| Interactions (atoms) | 15 | 0.67 (0.33 to 0.94) | 0.35 (−0.26 to 0.88) |

Agreement looks best on the simplest tier, but every interval overlaps every other. By model there
are 1 to 17 ratings each; no model-level statement is possible. Where the generated tables say
"no interval", the group is too small for the bootstrap to give one.

## The two flags and the notes

Raters ticked "reference looks wrong" on **3** ratings and "model looks better" on **22**.

### References raters called wrong or unreadable

Each reference image and scene was inspected. **No reference selects the wrong atoms. The shared
problem is that the thing the prompt asks about is too small to see**: the reference shows the
whole structure with no camera focus, at 600 × 450 pixels.

| task | who | what they said | what the reference shows | verdict |
|---|---|---|---|---|
| `named-1tup-248` | R1 flagged wrong | – | Whole p53–DNA complex (3 protein chains + DNA) in grey; one residue in blue ball-and-stick, a few pixels wide | Atoms right, picture unreadable |
| `named-1tup-143` | R1 note | "Reference is bad!" | Same scene, residue 143 | Same problem |
| `int-001` | R3 flagged wrong | – | Whole myoglobin; His64 and O2 as small uncoloured ball-and-stick; the 3 Å dashed line and its label cannot be seen | Atoms right, picture unreadable |
| `gen-ions-1hho` | R3 flagged wrong | "4 x OXY in 1hho - too small to see?" | The only non-polymer in 1HHO that the viewer's "ion" rule matches is one phosphate (5 atoms); the bound O2 (2 molecules in the deposited entry) is not an ion | Reference matches the viewer's rule, but "the ions" is a poor question for this structure |
| `hotspots-1tup` | R3 note, "can't tell" | "difficult to see how many residues are found in the reference" | 6 residues as red spheres on the whole complex; some hide behind others | Readability |
| `int-005` | R3 note, "can't tell" | "If the inhibitor is the point of interest in the reference, it should be visible. … which interactions is it showing?" | Benzamidine with Mol\*'s automatic interaction display, no focus | Readability; prompt is open about which interactions |

This matters beyond the rating study: **the image-pair judge sees the same pictures.** For
single-residue tasks (the whole clinical tier) neither a person nor the judge can tell a right
residue from a wrong one at this zoom.

### Where the model's scene looked better

22 ratings, by 2 raters (R1: 15, R2: 7). They pile up on two task families:

- **Resolution by name** (`res-*`, 10 flags): the prompt is open ("Show me hen egg white
  lysozyme") and the reference is a bare default cartoon. Models add colour or ligands.
- **Interactions** (`int-*`, 9 flags): models zoom in on the site; the reference does not.

14 of the 22 came with the answer "same", 7 with "different" and 1 with "can't tell". So "model
looks better" mostly marks a plain reference, not a wrong one. For the open prompts, "is it the
same picture?" is not a well-posed question: R3 wrote "Its logically correct, but I want to see
the rest of the protein" and "Its the same as the request - but clearly visually cleaner in the
reference, which is purely an aesthetic choice?".

## What this supports in the paper today

Strictly:

1. **Can say:** "In a pilot (3 raters, one of them the author; 114 labelled answers on 109
   image pairs), people agreed with the judge on 79% of answers (Cohen's kappa 0.54, 95% interval
   0.34 to 0.71), and confirmed 74% (57% to 89%) of its 'same' calls; 62% (40% to 85%) without the
   author."
2. **Can say:** the judge's rescues change no model's mean F1 by more than 0.028, so the headline
   results do not depend on it.
3. **Cannot say:** that the judge is validated, that people agree with each other, that agreement
   differs by tier or by model, or anything about the final run (new tasks, new renders).
4. **Should say:** only one of the three raters passes the attention-check rule as written, and
   why.

Is the sample enough? No. The kappa interval is ±0.19 (±0.23 without the author) against a target
of ±0.10; the rescue-precision interval spans "the judge is wrong a tenth of the time" to "wrong
four times in ten"; and there is no human-vs-human baseline to read any of it against.

## Power analysis: what it takes

Simulated from the measured rates (`power.py`; the simulation reproduces today's interval: ±0.20
simulated vs ±0.19 measured). The unknown is how often two people split on a pair; three cases are
carried through (10%, 20%, 30% of pairs).

**Half-width of the 95% interval on human-vs-judge kappa:**

| judged pairs | raters per pair | ratings | split 10% | split 20% | split 30% |
|---|---|---|---|---|---|
| 113 (a4-v1 finished) | 2 | 226 | ±0.18 | ±0.16 | ±0.14 |
| 113 | 3 | 339 | ±0.17 | ±0.15 | ±0.12 |
| 200 | 2 | 400 | ±0.14 | ±0.12 | ±0.11 |
| 250 | 2 | 500 | ±0.12 | ±0.11 | ±0.10 |
| **300** | **2** | **600** | **±0.11** | **±0.10** | **±0.09** |
| 300 | 3 | 900 | ±0.11 | ±0.09 | ±0.08 |
| 400 | 2 | 800 | ±0.09 | ±0.08 | ±0.08 |

Three things follow:

1. **More raters on the same 113 pairs cannot reach ±0.10.** The judge is right or wrong per
   *pair*, so the number of pairs sets the floor. a4-v1 tops out near ±0.12 to ±0.17.
2. **±0.10 needs about 300 judged pairs with 2 raters each: about 600 judged ratings.** With a
   50:50 mix of judge "same" and "different" (instead of today's 34:66) the same 600 ratings also
   give rescue precision to ±0.07–0.08 and human-vs-human kappa to ±0.08–0.12.
3. **At 35 items per person (27 judged pairs + checks and repeats) that is about 22 raters.** With
   10 raters (about 135 pairs, 2 each) expect about ±0.12–0.16 on kappa and ±0.10–0.12 on rescue
   precision.

What the simulation leaves out, all of which make the real intervals wider, not narrower:

- It is for the **unweighted, per-rating** kappa. Weighting back to the run widens the interval
  (today: ±0.21 weighted against ±0.19 unweighted, all raters).
- It uses the all-rater rates. The independent raters agree with the judge less (kappa 0.44).
- Raters are treated as alike; today they are not (rescue precision 0.53 to 0.88).
- The narrower intervals in the "split 30%" column come from holding the measured rates fixed
  while assuming noisier raters. Plan on the 10% and 20% columns.

So 300 pairs × 2 raters is the smallest design that can plausibly reach ±0.10, not a guarantee.

**Finishing a4-v1 (optional):**

- 128 more ratings give every item 2 ratings: 4 new raters at 35 each. The site already serves the
  least-rated items first, so this needs no code change.
- 178 more ratings give every item 2 ratings *that are not the author's*: 6 new raters.
- That buys the first real human-vs-human number (±0.14 to ±0.21) and kappa to about ±0.14–0.18.
  It does not reach ±0.10, and its tasks are the October corpus, not the final one.

Recommendation: do not spend volunteers on finishing a4-v1 unless they are available *before*
the final run. Put the effort into a4-v2 (see [`FINAL_CALL.md`](FINAL_CALL.md)), built so that
pairs are completed to two raters before new pairs open.

## Limits of this readout

- 3 raters, one the author; R1 has 12 ratings on items that are no longer in the set, and rated
  at about half the time per item of the others.
- Intervals resample tasks only. Rater-to-rater spread is not in them.
- Weights assume the capped per-task sample is as good as random within a task and judge label.
  It was drawn in keyed order, which is arbitrary but not random. Five task-and-label cells of the
  run (8 pairs) have no pair in the set; the scaling covers them.
- 4 judged pairs have only "can't tell" answers and are outside every agreement number.
- The 12 pairs on the public gallery were excluded by design; the weighted numbers describe the
  other 261.
- The tier of a task is taken from today's task files (`scripts/build_leaderboard.py` regimes).
- The 0.028 figure counts every rescue (judge "same" and pixel-equivalent renders) as lifting the
  task from its tree score to 1.0, so it is an upper bound.

## How to rebuild

    # 1. export (read-only; writes git-ignored files next to the private key)
    uv run python scripts/export_ratings.py --author "<author's token name>" --test "<test token name>" \
        --out /path/to/MolBench/results/a4/a4-v1
    # 2. judged-pair counts of the run, for the weights
    uv run python scripts/build_rating_set.py /path/to/MolBench/results/r2x2/spec \
        --population-only /path/to/MolBench/results/a4/a4-v1/population.json
    # 3. analysis (offline)
    A=/path/to/MolBench/results/a4/a4-v1
    uv run python scripts/agreement.py $A/key.json $A/ratings.json --population $A/population.json \
        --json paper/a4/tables/agreement.json --markdown paper/a4/tables/agreement.md
    # 4. power tables (about two minutes)
    uv run python paper/a4/power.py

Nothing committed here holds a rater's name, an invite token, an item id or the answer key.
