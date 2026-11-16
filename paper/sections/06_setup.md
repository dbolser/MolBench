## 5. Experimental setup

One run fills every result in Section 6. Its plan is fixed in a single manifest file before any
model is called: the corpus version and its hash, the models and their prices, the prompting
conditions, the number of samples and the limits. SI Section S6 reproduces it.

### 5.1 Models

The panel is set by a written rule, not by results. It has {{plan.n_core_models}} language
models ({{plan.n_core_open}} with openly available weights, {{plan.n_core_closed}} without):
every model on the project's public leaderboard of October 2026, so that old and new numbers
can be compared. Up to {{plan.n_optional_models}} further models, the largest current model of
each major provider on the price date, are optional entries marked † in the tables. No model is
added or dropped after results are seen. A *keyword script* that uses no model is run on both
tracks as a floor: it maps words in the request to fixed output by rule.

### 5.2 Prompting conditions

Every model receives a system prompt and the request, and returns one answer. Models cannot
look anything up, ask a question back, or see a rendered result.

**Table 4. Prompting conditions.** *Format reference*: a frozen text that documents the answer
format. *JSON mode*: a provider option that forces syntactically valid JSON. *Grounding pack*:
facts about the structure that an offline lookup could produce.

| Condition | What the model is given | Run on |
|:---|:---|:---|
| **Format reference** (headline) | A short instruction, the output rule ("answer with one JSON value and nothing else") and a frozen reference text for the answer format | all models, all tasks, both tracks |
| Format reference + JSON mode | The same, with the provider's option that forces syntactically valid JSON | models that offer it; 1 sample |
| Format reference + grounding pack (answer supplied) | The same, with a *grounding pack* appended to the request: facts about the structure that an offline lookup could produce (chains, residue ranges in both numberings, the UniProt mapping, and the residue each named variant maps to) | name-resolution and clinical tiers, scene track |
| No format reference | The instruction and the output rule only | {{plan.n_bare_models}} models, scene track |

A grounding pack never contains a scene, a colour or a representation, but for a clinical task
it does contain the mapped residue, and for a name-resolution task a list of entries. This
condition is therefore an upper bound, the lookup already done and its result handed over, and
not a test of whether a model can use raw lookup tables. For the running example
it states that UniProt {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
{{ex.map_auth_first}}–{{ex.map_auth_last}} of chain {{ex.auth_chain}} (SI Section S1). No prompt was tuned on benchmark tasks, and the worked example in each prompt
uses a structure that no task uses. SI Section S7 gives both system prompts.

### 5.3 Sampling

Each model answers each task {{plan.samples}} times in the headline condition, at the
provider's default temperature. The output limit is {{plan.max_tokens:,}} tokens. A malformed
answer is scored as it stands and is not retried; only transport errors are retried. Every raw
answer is archived with its token counts, finish reason and cost.

### 5.4 Statistics

- **Per-model scores** are means over tasks of the mean over samples. Task success is also
  reported as the share of tasks on which all {{plan.samples}} samples are right.
- **Intervals** are 95% bootstrap intervals [@efron1979] with {{run.bootstrap_replicates:,}}
  resamples. Whole structures are resampled, not single tasks, because tasks on one structure
  share its difficulties.
- **Paired comparison of formats.** For each model and pair, a side counts as right when at
  least two of its three samples are right. "Right" is taken two ways: by the target score
  (the requested atoms drawn exactly as asked), which is the same test in both formats and is
  the primary comparison, and by task success, which is not the same test (Section 3.4) and is
  shown beside it. Pairs right on one side only are compared
  with McNemar's exact test [@mcnemar1947]. We report the four counts for every model, and
  repeat the analysis without the {{corpus.twins.need_hide_toggle}} pairs that need an unstated
  hide step and without the clinical pairs, where the call-list viewer can do the mapping
  itself (Section 3.4).
- **Planned comparisons**, each as a difference in task success with an interval: public
  against held-back split; full against terse and indirect wording; with and without JSON
  mode; with and without grounding pack; clinical tasks in which the number in the variant name
  is, or is not, the author residue number. Totals of the two tracks are not compared with
  each other: the tracks differ in their mix of tiers and in the length of the answer, so the
  formats are compared on the pairs only.
- **What the graded score is read against.** F1 has a floor that needs no skill: a scene with
  nothing but a protein cartoon, or a follow-up's start state returned unchanged, shares most
  of its drawing with the reference. Task success and the target score are the headline
  numbers; F1 is shown with the keyword baseline beside it, which marks that floor.

We do not correct for multiple comparisons; the comparisons are few, stated here in advance,
and reported in full.

### 5.5 Human check of the grader

The grader's verdict is also checked against people. After the run, volunteers will see pairs
of pictures, a reference and a model answer rendered from the same camera and framed on the
target atoms, and say whether the two show the same thing. The design calls for
{{study.n_pairs}} pairs with {{study.raters_per_pair}} raters each. People's answers are compared
with the grader's task success. A further {{study.n_grader_check_pairs}} pairs are answers that the
grader counts as exactly right although their pictures are not identical pixel for pixel;
people should call these the same. The study also tests an *image judge*: a vision-language
model that is shown the same two pictures and asked the same question. The image judge
contributes to no score in this paper. A smaller pilot of the study has been run (Section 6.6).

### 5.6 Reproducibility

One command performs the run from the manifest and stops if the projected cost passes a stated
cap. One command rebuilds every table, figure and number in this paper from the archived
answers. A rehearsal with a mock model exercises the whole path at no cost. Grading needs no
network access and no paid service.
