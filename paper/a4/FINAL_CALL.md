# Rating set a4-v2: design for the "final call"

To be built **after** the final run, from its archives. Nothing here needs a paid call. No images
are built yet. Evidence for every choice is in the a4-v1 readout and in
[`tables/power.md`](tables/power.md).

## What a4-v1 taught us

1. **Pairs, not ratings, set the precision.** 113 judged pairs cannot give ±0.10 on kappa however
   many people rate them.
2. **The serving order spread ratings one-deep.** 146 ratings covered 137 items once; only 5
   judged pairs got two labelled answers. No human-vs-human number came out.
3. **One person never saw an attention check, another fell under the pass rule on a single
   "can't tell".** Three checks per kind is too few for an 80% rule.
4. **Small targets cannot be seen.** A single highlighted residue on a whole complex is a few
   pixels. People answered "can't tell" or flagged the reference; the judge sees the same pixels.
5. **Open prompts make "same picture?" ill-posed** ("Show me lysozyme": any sensible view is right).
6. **Raters differ**: rescue precision 0.53 to 0.88 across three people. Few raters = fragile.

## What the study must answer (declared before any v2 rating exists)

Primary, all on raters other than the author, each with a 95% interval:

1. **Rescue precision** – of the pairs the judge calls "same", the share the human majority calls
   same. Weighted to the run.
2. **Human vs judge**: Cohen's kappa and Gwet's AC1 per rating; sensitivity, specificity and
   balanced accuracy of the judge against the human majority.
3. **Human vs human**: Krippendorff's alpha on pairs with two or more labelled answers.

Secondary: the same by tier and by model family; with the author included; what the flags say.

Suggested reading rule for the paper (Dan to confirm): the judge column is called "validated for
rescue-only use" if rescue precision is at least 0.85 with a lower interval bound of at least
0.75, and human-vs-judge kappa is not below human-vs-human alpha by more than 0.10. Otherwise the
column is reported as "not validated" and kept out of every headline table.

## What to sample from the final run

**Frame.** MVS track, `spec` condition, every scene that reached the judge. The final run has 3
samples per task per model: take **at most one sample per (task, model)**, chosen by the keyed id
order the builder already uses, so near-identical triplets do not fill the set.

**Size: 300 judged pairs.** That is what ±0.10 on kappa needs with 2 raters per pair.

**Strata.**

| stratum | pairs | why |
|---|---|---|
| judge verdict | 150 "same" + 150 "different" | An even split gives the tightest interval on rescue precision (±0.07–0.08) for the same effort; weights undo it afterwards |
| tier, within each verdict | equal share per tier present (translation, structure-grounded, clinical, interactions, follow-up turns, accept-set), with a floor of 20 pairs per tier where the run has them | A4-v1 had 15–37 ratings per tier and could say nothing by tier |
| model, within each tier | round-robin over models; no model above 12% of the set | 15 models at 1–17 ratings each said nothing by model |
| task | at most 2 pairs per task (v1: 3) | The corpus is larger now; spread over structures and templates |

The builder records, for every (task, verdict) cell, how many pairs the run has
(`population` in the private key; added in this branch), so `scripts/agreement.py` weights the
sample back to the run with no extra input.

**Leave out of the main set, and analyse apart if included at all:**

- **Name-resolution prompts** ("show me X" with any view acceptable). Put at most 20 pairs in a
  labelled side stratum. They are graded on the structure chosen, not the picture.
- **Pairs on the public gallery** (their verdict is public), as in v1.

**Add a small grader check (40 pairs, needs 40 extra free renders):** scenes the atom-set grader
scores as exactly right (task success) but that are not pixel-identical to the reference. People
should call these "same". This is the only human check of the *headline* metric, and it is cheap.
If the renders are not available, drop this stratum; do not delay the call for it.

### API-track state comparisons: recommendation is no

Do not put API-track comparisons in a4-v2.

- The judge is not used on the API track. It is graded by replaying calls to a final viewer state.
  There is nothing for humans to validate there with this instrument.
- No renders exist for API answers. Producing them means driving pdbe-molstar 3.3.2 headlessly for
  both reference and answer: new machinery, new failure modes, right before the final call.
- Raters are the scarce resource. 600 judged ratings is already about 21 people.

If renders of API final states come for free from the final run, a separate block of at most 30
*paired-task* comparisons (API answer render vs the MVS twin's reference render) would support
the claim that twins target the same atoms. Analyse it on its own; never pool it into kappa.

## Before the images are built (blocking)

**Make the target visible in both renders.** For any task whose target is under about 5% of the
structure's atoms (single residues, a ligand, a measured distance), render reference and answer
with the *same* camera, framed on the reference's target atoms plus a margin, or show a second
zoomed panel next to the whole view. Without this the clinical tier is unratable by people and by
the judge alike. The judge must be run on these same images, so this has to be in place before
the final run's escalation step, not after.

## Per rater

**35 items, about 10–15 minutes** (v1 median: 12–15 seconds per item for the volunteers).

| | items |
|---|---|
| judged pairs | 27 |
| repeats of two of the rater's own earlier pairs (new ids, same images), in the last 10 | 2 |
| attention checks | 6 |

**Attention checks: 3 known-same + 3 known-different per rater, one of each within the first 8
items.**

- Known-same: a re-render or a scene whose render differs by at most 2 pixels (as in v1).
- Known-different, easy (2): the reference against another structure's reference (as in v1).
- Known-different, calibrated (1): the reference against a copy of itself changed by script in one
  way a careful person sees — a different chain coloured, a different representation, or the
  highlight moved to a far-away residue. This tells apart "awake" from "looking closely".
- **Pass rule, fixed now:** at most one miss over the six checks, and no miss on an easy
  known-different. "Can't tell" on a check is a miss. A rater with fewer than 4 checks answered is
  reported but left out of the primary analysis.
- Checks are built per rater from a pool of 30 so no two people share all six.

## Serving order (the change that matters most)

Fix a single random order of the 300 pairs in which every prefix is balanced across strata.
Serve each rater: first, pairs that have **exactly one** rating by someone else; then unopened
pairs in the fixed order. Never a third rating while any opened pair has one.

Result: whenever the study stops, almost every opened pair has two raters, and the opened pairs
are a balanced sample. With 10 raters the study yields about 135 double-rated pairs instead of 270
single-rated ones.

## How many people

| raters finishing 35 | judged pairs with 2 raters | kappa (human vs judge) | rescue precision | human vs human |
|---|---|---|---|---|
| 22 | 300 | ±0.09 to ±0.10 | ±0.07 to ±0.08 | ±0.08 to ±0.12 |
| 15 | about 200 | ±0.10 to ±0.13 | ±0.08 to ±0.10 | ±0.10 to ±0.15 |
| 10 | about 135 | ±0.12 to ±0.16 | ±0.10 to ±0.12 | ±0.12 to ±0.19 |
| 5 | about 65 | about ±0.20 | about ±0.16 | about ±0.17 to ±0.28 |

(Half-widths of 95% intervals from `tables/power.md`, 50:50 mix; ranges cover 10% to 30% of pairs
being split between two raters. The 135-pair row is read between the simulated 113 and 150 rows;
the 65-pair row is scaled from the 113 row and is the least certain.) 18 invite tokens already exist; 3 have been used. **Aim for 20 people; 10 is the
minimum for a result worth a paragraph.**

## What would make it publication-grade

1. **The plan above is committed before the first v2 rating**, with `scripts/agreement.py` at a
   named commit as the analysis. Deviations are listed in the paper.
2. **At least 10 independent raters, primary analysis without the author.** The author may rate;
   his answers appear only in a "with author" column.
3. **Every pair rated by two or more people**, so human-vs-human agreement is the yardstick the
   judge is read against. A judge that agrees with people as well as people agree with each other
   is the claim; kappa alone is not.
4. **Raters as a source of uncertainty**: with 10 or more raters, bootstrap raters as well as
   tasks (not yet in `agreement.py`; a small addition once there is data to run it on).
5. **Readable images** (the camera rule above), checked on 20 clinical-tier pairs before launch.
6. **Blind and balanced**: no model name, no verdict, no task id shown; public-gallery pairs
   excluded; item ids keyed (all as in v1).
7. **Rater background** recorded in one optional question (works with protein structures: daily /
   sometimes / never), reported in aggregate.
8. **Test-retest**: the 2 repeats per rater give within-person consistency.
9. **Release**: pseudonymised ratings and the answer key published with the paper once the study
   closes. Names appear only in the acknowledgements, with each person's consent.
10. **One fixed pass rule for attention checks, enough checks to apply it, shown early.**

## Draft message to volunteer raters

Subject: MolBench – the paper draft, and one last 15-minute favour

Hi ⟦name⟧,

Thank you for rating scenes for MolBench last month. The paper draft is attached, and your work
is in it.

**What you helped us find**

- We use a computational intelligence (CI) model as a second opinion: it looks at two pictures of
  a molecular scene and says whether they show the same thing. Your answers were the first test
  of that second opinion against people.
- You and it agreed on about 4 pairs in 5.
- When it said "these are the same", people agreed about 3 times in 4. That is promising, but not
  yet solid enough to rely on, and we say so in the draft.
- Your notes showed us a real flaw: when a task highlights one residue on a large complex, the
  highlight was too small to see. ⟦PENDING: one line on the fix – both pictures now zoom to the
  part the request is about⟧.

**What we are asking now**

We have rerun the whole benchmark: ⟦PENDING: n tasks⟧ requests on ⟦PENDING: n structures⟧
structures, ⟦PENDING: n models⟧ models. We need one more round of ratings on the new scenes, and
this time every pair is seen by two people, so we can also measure how well people agree with
each other.

- **35 pairs, about 10 to 15 minutes**, in one sitting, on a laptop or desktop.
- Same task as before: reference picture on the left, a model's picture on the right. Same,
  different, or can't tell. Ignore camera angle and zoom.
- "Can't tell" is a fine answer. So is a note when something looks off; those were the most
  useful thing last time.
- A few pairs have a known answer. They are there to calibrate the study, not to test you.

Your personal link: ⟦link⟧
Please finish by ⟦date, two weeks out⟧.

If you know a colleague who looks at protein structures and has 15 minutes, I would gladly send
them a link too. We need about 20 people for a result we can stand behind.

You will be thanked by name in the paper unless you would rather not be; just tell me.

Thanks again,
Dan
