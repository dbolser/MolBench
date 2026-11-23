# Rating set a4-v2: the plan for the "final call"

Built **after** the final run, from its archives. Nothing here needs a paid call. The tooling is
in place and rehearsed (see "What has been rehearsed"); the exact commands are in
[`RATING_V2_RUNBOOK.md`](RATING_V2_RUNBOOK.md). Evidence for the choices: the a4-v1 readout
([`REPORT.md`](REPORT.md)) and the simulated interval widths ([`tables/power_v2.md`](tables/power_v2.md)).

## What changed since the first version of this plan

The first plan was built around the image-pair judge. Decision 23 of `FINAL_PLAN.md` moved the
study's purpose: **people now check the benchmark's own grader** (the headline numbers), and the
image-pair judge is a secondary column, reported only if it is run on the same pictures.

## What a4-v1 taught us

1. **Pairs, not ratings, set the precision.** 113 pairs cannot give ±0.10 on kappa however many
   people rate them.
2. **The serving order spread ratings one-deep.** Only 5 pairs got two labelled answers. No
   human-vs-human number came out.
3. **One person never saw an attention check; another fell under the pass rule on one "can't
   tell".**
4. **Small targets cannot be seen.** One highlighted residue on a whole complex is a few pixels.
5. **Open requests make "same picture?" ill-posed** ("Show me lysozyme": any sensible view is right).
6. **Raters differ**, so few raters give a fragile result.

Each has an answer below: 300 pairs; second raters first; three checks in the first 8 items; a
zoomed view of the target beside the whole view; name-resolution requests left out; 20 raters asked.

## What a rater sees

One request and **four pictures**: the reference and the model's scene, each shown **whole** and
**zoomed on the atoms the request is about**. Left and right are always taken from the same
camera (the reference's), so any difference is a difference in the scene. A follow-up request
also shows the scene as it was before the request.

Two answers per item (same / different / can't tell):

| answer | question | compared with |
|---|---|---|
| whole scene | Judged against the request, does the model's scene show the same thing as the reference? Extra drawing that was not asked for counts as different; a colour the request leaves open does not. | the grader's **task success** |
| zoomed view | Is the part the request is about picked out the same way (same atoms, same style, same colour where one is named)? | the grader's **target score = 1** |

A task whose target cannot be framed (no target atoms) gets the whole view and one answer.

## What the study must answer (fixed before any v2 rating exists)

Primary, on independent raters who pass the attention checks, each with a 95% interval that
resamples tasks:

1. **Of the answers the grader passes (task success), what share do people call the same?**
   This bounds the grader's false passes.
2. **Of the answers the grader fails, what share do people call different?** This bounds its
   false fails. Reported apart for "close" (task failed, target score 1) and "wrong".
3. **Target score against the zoomed view:** the same two shares, plus kappa and Gwet's AC1.
4. **People against people** on pairs with two labelled answers (Fleiss' kappa, Krippendorff's
   alpha), as the yardstick the grader is read against.

Secondary: by tier; with the author; test-retest; the image-pair judge against people if it was
run; a second interval that resamples raters as well as tasks.

Suggested reading rule for the paper (**Dan to confirm before launch**): the paper says "people
confirmed the grader" if people call at least 90% of its passes the same and at least 90% of its
"wrong" answers different, each with a lower interval bound of at least 0.80, and
grader-vs-people kappa is not more than 0.10 below people-vs-people. Otherwise it reports the
numbers and names the kind of answer where people and grader part.

## What is sampled from the final run

**Frame.** Scene track (MVS), `spec` condition, every answer that parsed to a valid scene. One
sample per (task, model), picked by keyed id, so the three samples of a cell do not fill the set.

**Scene track only, and why.** The pictures, the shared camera and the framing on the target are
built for MVS scenes (`molbench/render.py`). An API answer is a list of calls with no picture.
It *can* be pictured: `paper/a4/api_render_probe.py` replays a reference and an answer in
headless pdbe-molstar 3.3.2 and photographs both from the reference's camera (done for two
pilot answers). But that path has no target framing, a different look (the viewer's own
background and defaults), and has not been tried on every call kind. So API answers are not in
a4-v2. The API grader is covered by its control set (910 controls, 0 false passes, 0 false
fails), not by people; the paper should say so.

**Left out:** name-resolution requests (any view is accepted, so "same picture?" is not the
question), API answers, answers that did not parse to a scene (nothing to draw).

**Strata (300 pairs).**

| stratum | rule | why |
|---|---|---|
| grader's verdict | 100 **right** (task success) + 100 **close** (task failed, target score 1) + 100 **wrong** | "Close" is where the two scores disagree with each other, so it is where people tell us most |
| tier, inside each verdict | equal share per tier that has answers | a4-v1 could say nothing by tier |
| model, inside each tier | models in turn; no model above 12% of the set | no model dominates |
| task | at most 2 pairs per task (a paraphrase counts as its original) | spread over structures and templates |
| passes that look different | among the "right" pairs, up to twice as many are drawn, and those whose pictures differ from the reference's are kept first (up to 75% of the "right" pairs) | a pass whose picture is identical to the reference's tests nothing: anyone calls it the same |

The key records how many answers the run has per tier and verdict, and what share of the passes
drawn look different from the reference, so `scripts/agreement.py` weights the sample back to
the run with no extra input.

**Image-pair judge (secondary).** If the judge is run on the same four pictures, its verdicts go
into the build (`--judge`), and the analysis adds a judge-against-people table. No runner for the
judge on v2 pictures exists yet, and running it is a paid call; see the runbook.

## Per rater: 35 items, about 15 minutes

| | items |
|---|---|
| pairs | 27 |
| attention checks | 6 |
| repeats of two of the rater's own earlier pairs, in the last 10 items | 2 |

The 15 minutes is an estimate: a4-v1 took volunteers 12 to 15 seconds per item with two
pictures and one answer; a4-v2 has four pictures and two answers. Nobody has timed it yet.

**Attention checks, 6 per rater, one of each kind within the first 8 items** (never the first):

- **Known-same** (3): the reference against itself.
- **Known-different, easy** (2): the reference against another structure's reference.
- **Known-different, calibrated** (1): the reference against a copy changed by script in one
  way a careful person sees (a colour swapped for a far one, or a drawing style swapped), and
  which the grader fails. This tells "awake" from "looking closely".
- Each rater draws their six from a pool of 10 per kind, in their own order.
- **Pass rule, fixed now:** at least 4 checks answered, at most one miss over them, and no miss
  on an easy known-different. "Can't tell" on a check is a miss. A rater who does not pass is
  reported and left out of the primary analysis.
- Caveat from the rehearsal: with simulated raters who are wrong 8% of the time on each view,
  3 of 21 failed the rule. Expect to lose about one honest rater in seven.

## Serving order

One fixed order of the 300 pairs in which every prefix is balanced over verdict and tier. Each
rater gets, for a pair slot: first a pair with **exactly one** labelled answer from someone
else; then an unopened pair in the fixed order. A third answer is given only when no pair has
fewer than two. The author's and testing tokens do not count towards a pair's two raters.

So whenever the study stops, almost every opened pair has two raters and the opened pairs are a
balanced sample. Rehearsed with the real serving code on a 300-pair mock set: 22 raters gave
273 to 280 pairs two labelled answers, none a third; 10 raters gave 126 to 130.

## How many people

Simulated, not measured (`tables/power_v2.md`). Half-widths of 95% intervals; ranges cover two
raters splitting on 10% and on 20% of pairs.

| raters finishing 35 | pairs with 2 raters | grader's passes confirmed, if people nearly always agree | same, if the grader is off one time in ten | people vs people |
|---|---|---|---|---|
| 22 | 297 | ±0.05 to ±0.06 | ±0.07 to ±0.08 | ±0.09 to ±0.12 |
| 15 | 202 | ±0.06 to ±0.08 | ±0.09 | ±0.10 to ±0.14 |
| 10 | 135 | ±0.08 to ±0.09 | ±0.11 | ±0.13 to ±0.17 |
| 5 | 67 | ±0.11 to ±0.13 | ±0.16 | ±0.18 to ±0.24 |

**Aim for 20 people; 10 is the least that gives a result worth a paragraph.**

Honest caveats, all of which make the real intervals wider:

- Nobody knows yet how people will answer; the two cases are guesses that bracket "the grader is
  nearly always right" and "off one time in ten".
- The widths are for the set as built, raters taken as alike. Weighted back to the run they are
  wider (in a4-v1: ±0.21 against ±0.19), and raters differed a lot in a4-v1.
- The table assumes a third of the pairs are passes **that a person can test**. On the pilot run
  (two models) **all 14 passes drawn were pixel-identical to the reference**. If the final run
  is like that, the study cannot say much about false passes (identical pictures are always
  "the same"); what it then measures well is false fails and the "close" class. The build prints
  the count; the runbook says what to do with it.
- If no pass is contradicted, n passes rule out a false-pass rate above 1 − 0.05^(1/n): 3% for
  99 passes, 6% for 45, 13% for 22. That counts only passes whose pictures differ.

## Known before launch (found while rehearsing on the pilot run)

1. **A doubled drawing scores the target but may not show it.** Both "close" answers in the
   pilot draw the whole chain as a grey cartoon and then the target again as a coloured cartoon
   in the same place. The grader counts the target as coloured (target score 1). The rendered
   picture shows **no colour at all** (0 green or purple pixels against thousands in the
   reference): the first cartoon hides the second in this renderer. People will call these
   "different" in the zoomed view. Either the pictures or the target score need a decision
   before launch; see the open issues in the runbook.
2. **Most passes look identical to the reference** (above).
3. **A target spread over the structure does not zoom.** For "every disulfide" or a residue in
   every chain, the zoomed view is another whole view. It is still shown.
4. **Zoomed views can cut through atoms.** A camera placed near a buried target clips whatever
   is in front of it; cut surfaces show as dark caps. The same on both sides.
5. **Measured distances are thin** in the zoomed view (a dashed line a pixel or two wide).

## What would make it publication-grade

1. This plan and `scripts/agreement.py` at a named commit **before the first v2 rating**.
   Deviations are listed in the paper.
2. At least 10 independent raters; primary analysis without the author.
3. Every pair rated by two people, so people-vs-people is the yardstick.
4. Raters as a source of uncertainty: the second interval resamples raters and tasks.
5. A look at every review sheet of the "close" class and of 20 clinical pairs before launch.
6. Blind and balanced: no model name, verdict or task id shown; item ids keyed; the key outside git.
7. Test-retest from the 2 repeats per rater.
8. Release: pseudonymised ratings and the answer key with the paper, once the study closes.
   Names only in the acknowledgements, with each person's consent.

## What has been rehearsed

- The builder on the dry-run archive (300 pairs + 30 checks, every picture drawn) and on the
  real pilot run (18 pairs + 6 checks from two models' real answers).
- The rating page in a browser against the real serving code, with a4-v1 still readable.
- 5 to 30 simulated raters through the real serving code, exported and analysed end to end.
- Not rehearsed: real people, the hosted database (the migration is written, not applied), the
  image-pair judge on v2 pictures.

## Draft message to volunteer raters

Subject: MolBench: what your ratings showed, and one more 15-minute favour

Hi ⟦name⟧,

Thank you for rating scenes for MolBench. Here is what came of it, and one more request.

**What your ratings showed**

Last time you compared a reference picture with a model's picture, and we compared your answers
with a computational intelligence (CI) model that we use as a second opinion on the same
pictures. It was a pilot: 3 raters, one of them me, 114 answers on 109 picture pairs.

- People agreed with the second opinion on 79% of answers (Cohen's kappa 0.54, 95% interval
  0.34 to 0.71).
- When it said "these are the same", people agreed 74% of the time (57% to 89%); 62% (40% to
  85%) without my own ratings.
- The second opinion changes no model's average score by more than 0.028, so the main results
  do not depend on it.

That is not enough to call the second opinion validated, and the paper says so. Your notes also
showed a real flaw: when a request is about one residue in a large complex, the highlight was too
small to see. That is fixed: every pair now comes with a zoomed view of the part the request is
about.

**What the benchmark is now**

MolBench measures whether a language model can turn a plain-language request into correct control
of a molecular viewer: the right atoms, drawn and coloured as asked. It now has ⟦PENDING: n⟧
requests on ⟦PENDING: n⟧ structures, from simple display requests to clinical variants that need
a UniProt-to-structure residue mapping, and every answer is scored automatically.

The draft paper is here: ⟦PENDING: link to the draft paper⟧

**What I am asking**

This round checks the automatic scoring itself against people. Every pair is seen by two people,
so we can also measure how well people agree with each other.

- **About 35 pairs, about 15 minutes**, in one sitting, on a laptop or desktop.
- Each pair shows the request, then the reference and a model's scene, whole and zoomed in.
  Left and right are taken from the same viewpoint.
- Two answers per pair: is the whole scene the same, and is the zoomed part the same? Same,
  different, or can't tell.
- "Can't tell" is a fine answer. So is a note when something looks off; the notes were the most
  useful thing last time.
- A few pairs have a known answer. They calibrate the study; they are not a test of you.

Your personal link: ⟦link⟧
Please finish by ⟦PENDING: date, two weeks after sending⟧.

If you know someone who looks at protein structures and has 15 minutes, I would gladly send them
a link. We need about 20 people for a result we can stand behind.

You will be thanked by name in the paper unless you would rather not be; just tell me.

Thanks again,
Dan
