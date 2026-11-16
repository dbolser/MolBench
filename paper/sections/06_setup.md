## 5. Experimental setup

One run fills every result in Section 6. Its plan is fixed in a single manifest file before any
model is called: the corpus version and its hash, the models and their prices, the prompting
conditions, the number of samples and the limits. SI Section S6 reproduces it.

### 5.1 Models

The panel is set by a written rule, not by results. The core panel is every model on the
project's public results table of October 2026: {{plan.n_core_models}} language models,
{{plan.n_core_open}} with openly available weights and {{plan.n_core_closed}} without, so that
old and new numbers can be compared. {{plan.n_core_in_pilot}} of them ran in the October pilot
of the scene track (Section 6.6); the other, {{plan.core_not_in_pilot}}, could not be reached
on that day and had earlier call-list results only. Up to {{plan.n_optional_models}} further
models are *optional*: the current flagship model of each major provider, and the largest
model with public weights, as listed on the day the prices were recorded in the manifest
({{plan.price_date}}). They are run only if the budget allows (Section 5.6), which is decided
before any result exists, and they are marked † in the tables. No model is added or dropped after results are seen. A
*keyword script* that uses no model is run on both tracks as a floor: it maps words in the
request to fixed answers by rule. SI Table S6 lists every model.

### 5.2 Prompting conditions

Every model receives a system prompt and the request, and returns one answer. Models cannot
look anything up, ask a question back, or see a rendered result.

**Table 4. Prompting conditions.** The first is the *main condition*, from which all main
results come. *Format reference*: a frozen text that documents the answer format. *JSON mode*:
a provider option that forces syntactically valid JSON. *Grounding pack*: the result of an
offline lookup, appended to the request: the chains of the structure, its residue ranges in
both numberings, the UniProt mapping and, for a clinical task, the residue that each named
variant maps to. *Samples*: answers per model and task.

| Condition | What the model is given | Run on | Samples |
|:---|:---|:---|---:|
| **Format reference** (main condition) | A short instruction, the rule for the answer ("answer with one JSON value and nothing else") and the format reference | all models, all tasks, both tracks | {{plan.samples}} |
| Format reference + JSON mode | The same, with JSON mode switched on | the {{plan.n_json_mode_models}} core models whose provider offers it, all tasks, both tracks | 1 |
| Format reference + grounding pack | The same, with the task's grounding pack appended to the request | all models; the lookup tiers (name resolution, clinical variant), scene track | {{plan.samples}} |
| No format reference | The instruction and the rule for the answer only | {{plan.n_bare_models}} models ({{plan.bare_models}}), the same as in the pilot run; scene track | {{plan.samples}} |

A grounding pack never contains a scene, a colour or a representation. But for a clinical
task it contains the mapped residue, and for a name-resolution task a list of entries. The
grounding-pack condition is therefore an upper bound: the lookup has been done and its result
handed over. It is not a test of whether a model can use raw lookup tables. For the running
example the pack states that UniProt {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are
author residues {{ex.map_auth_first}}–{{ex.map_auth_last}} of chain {{ex.auth_chain}} (SI
Section S1). No prompt was tuned on benchmark tasks, and the worked example in each prompt
uses a structure that no task uses. SI Section S7 gives both system prompts.

### 5.3 Sampling

Each model answers each task {{plan.samples}} times in the main condition, at the provider's
default temperature. The limit on the length of an answer is {{plan.max_tokens:,}} tokens. A
malformed answer is scored as it stands and is not retried; only transport errors are retried.
Every raw answer is archived with its token counts, finish reason and cost.

### 5.4 Statistics

- **Per-model scores** are means over tasks of the mean over the task's {{plan.samples}}
  answers. For task success this is the task success rate; the all-{{plan.samples}} summary
  (the share of tasks on which every answer succeeds) is reported beside it (Section 4.2).
  Means over models leave the keyword script out.
- **Intervals** are 95% bootstrap intervals [@efron1979] with {{run.bootstrap_replicates:,}}
  resamples. Whole structures are resampled, not single tasks, because tasks on one structure
  share its difficulties.
- **Paired comparison of formats.** For each model and pair, a side counts as right when at
  least two of its three answers are right (the majority summary of Section 4.2). "Right" is
  taken two ways. The primary comparison uses the target score: an answer is right when it is
  target-right, that is, when its target score is exactly 1. This is the same test in both
  formats. The secondary comparison uses task success, which is not the same test in the two
  formats (Section 3.4), and is shown beside the first. Pairs right on one side only are
  compared with McNemar's exact test [@mcnemar1947]. We report the four counts for every
  model. We repeat the analysis without the {{corpus.twins.need_hide_toggle}} pairs in which
  the call list must switch off part of the default drawing (Section 3.4), and without the
  clinical pairs, in which the call-list viewer can do the mapping itself (Section 3.4).
- **Planned comparisons**, each as a difference in task success rate with an interval: public
  against held-back split; full against terse and indirect wording; with and without JSON
  mode; with and without grounding pack; clinical tasks in which the number in the variant name
  is, or is not, the author residue number. Totals of the two tracks are not compared with
  each other: the tracks differ in their mix of tiers and in the length of the answer, so the
  formats are compared on the pairs only.
- **What F1 is read against.** F1 has a floor that needs no skill: a scene with nothing but a
  protein cartoon, or a follow-up's start state returned unchanged, shares most of its drawing
  with the reference. The task success rate is therefore the primary score and the target
  score is reported beside it; F1 is shown with the keyword script beside it, which marks
  that floor.

The planned comparisons are the differences with intervals of Tables 9 and 11. The McNemar tests
are one per model; we read each as a description of that model and not as a family of tests.
We do not correct for multiple comparisons, and we report every count.

### 5.5 Human check of the grader

The grader's verdict is also checked against people. After the run, volunteers will see
*picture comparisons*: two pictures side by side, a reference and a model answer, rendered
from the same camera and framed on the target atoms. They say whether the two show the same
thing. The design calls for {{study.n_pairs}} picture comparisons with
{{study.raters_per_pair}} raters each. People's verdicts are compared with the grader's task
success. A further {{study.n_grader_check_pairs}} picture comparisons are of answers that the
grader counts as exactly right although their pictures are not identical pixel for pixel;
people should call these the same. The study also tests an *image judge*: a vision-language
model that is shown the same two pictures and asked the same question. The image judge
contributes to no score in this paper. A smaller pilot of the study has been run (Section 6.6).

### 5.6 Reproducibility

One command performs the run from the manifest. It does not start if the projected cost is
above a cap in US dollars that the manifest states, and it stops if spending would pass it.
One command rebuilds every table, figure and number in this paper from the archived answers. A rehearsal with a mock model exercises the whole path at no cost. Grading needs no
network access and no paid service.
