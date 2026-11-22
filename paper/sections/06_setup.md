## 5. Experimental setup

One run fills every result in Sections 6.1 to 6.5. Its plan is fixed in a single manifest file
before any model is called: the corpus version and its hash, the models and their prices, the
prompting conditions, the number of answers per task and the limits. SI Section S6 reproduces
it.

### 5.1 Models

The models are chosen by a written rule, not by results. The *core models* are the
{{plan.n_core_models}} language models of our public results table of October 2026, kept
unchanged so that old and new numbers can be compared. They are lower-priced models, with list
prices from {{plan.core_price_output_min}} to {{plan.core_price_output_max:.0f}} US dollars per
million output tokens. {{plan.n_core_open}} have openly available weights and
{{plan.n_core_closed}} do not. They are: {{plan.core_models}}. All but one of them ran in the
October pilot of the scene track (Section 6.6); the exception, {{plan.core_not_in_pilot}},
could not be reached on that day and had earlier call-list results only.

Up to {{plan.n_optional_models}} *optional models* are larger (list prices from
{{plan.optional_price_output_min}} to {{plan.optional_price_output_max:.0f}} US dollars per
million output tokens): the largest current model of several providers of closed models, and
the largest model with public weights, as listed on the day the prices were recorded in the
manifest ({{plan.price_date}}). The manifest names them (SI Table S6). Which of them are run
is decided before any result exists, from the projected cost alone, and they are marked † in
the tables. No model is added or dropped after results are seen.
⟦PENDING: Dan — which of the optional models are run⟧

A *keyword script* that uses no model is run on both tracks as a floor: it maps words in the
request to fixed answers by rule. SI Table S6 lists every model.

### 5.2 Prompting conditions

Every model receives a system prompt and the request, and returns one answer. A model cannot
look anything up, cannot ask a question back, and does not see a rendered result. It is not
given the structure file. Both system prompts tell the model that its answer is judged by what
the viewer ends up showing; the scene prompt adds that anything drawn that was not asked for
counts against the answer.

**Table 5. Prompting conditions.** *Main* is the condition from which all main results come.
*Format guide*: a frozen text in the system prompt that documents the answer format. *JSON
mode*: a provider option that forces syntactically valid JSON. *Grounding pack*: the result of
an offline lookup, appended to the request: the chains of the structure, its residue ranges in
both numberings, the UniProt mapping and, for a clinical task, the residue that each named
variant maps to. *Answers*: answers per model and task.

| Condition | What the model is given | Run on | Answers |
|:---|:---|:---|---:|
| **Main** | A short instruction, the rule for the answer ("answer with one JSON value and nothing else") and the format guide | all models, all tasks, both tracks | {{plan.samples}} |
| Main + JSON mode | The same, with JSON mode switched on | the {{plan.n_json_mode_models}} core models that offer JSON mode (all but {{plan.core_without_json_mode}}), all tasks, both tracks | 1 |
| Main + grounding pack | The same, with the task's grounding pack appended to the request | all models; the lookup categories (name resolution, clinical variant), scene track | {{plan.samples}} |
| No format guide | The instruction and the rule for the answer only | {{plan.n_bare_models}} models ({{plan.bare_models}}), the same as in the pilot run; scene track | {{plan.samples}} |

A grounding pack never contains a scene, a colour or a representation. But for a clinical
task it contains the mapped residue, and for a name-resolution task a list of entries. The
condition with a grounding pack therefore shows the most that a perfect lookup tool could add:
the lookup has been done and its result handed over. It is not a test of whether a model can
use raw lookup tables. For the running example the pack states that UniProt
{{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
{{ex.map_auth_first}}–{{ex.map_auth_last}} of chain {{ex.auth_chain}}, and that
{{ex.name_in_prompt}} is author residue {{ex.auth_number}} of that chain (SI Section S1).

No prompt was tuned on benchmark tasks. The worked example in each prompt uses an entry that
no task uses. The format guide of the scene track also contains one short illustration of a
distance line on an entry that tasks do use; no task asks for that distance. SI Section S7
gives both system prompts.

### 5.3 Sampling

Each model answers each task {{plan.samples}} times in the main condition, at the provider's
default temperature. The limit on the length of an answer is {{plan.max_tokens:,}} tokens.
{{plan.n_core_reasoning}} of the core models first write reasoning text that the user does not
see; the provider bills it and counts it against the limit. For these models the limit is
{{plan.reasoning_max_tokens:,}} tokens for reasoning and answer together (SI Table S6). An
invalid answer is scored as it stands and is not retried; only transport errors are retried.
Every raw answer is archived with its token counts, the reason the provider gives for the end
of the answer, and its cost.

### 5.4 Statistics

- **Per-model scores** are means over tasks of the mean over the task's {{plan.samples}}
  answers. For task success this is the task success rate; the all-{{plan.samples}} rate (the
  share of tasks on which all {{plan.samples}} answers succeed) is reported beside it (Section
  4.2). Means over models are means over the core models and the optional models that were
  run; they leave the keyword script out.
- **Intervals** are 95% bootstrap intervals [@efron1979] with {{run.bootstrap_replicates:,}}
  resamples. Whole structures are resampled with replacement, not single tasks, because tasks
  on one structure share its difficulties. Each task goes with the structure of its reference.
  Models are treated as fixed: an interval on a mean over models describes these models, not
  models in general. In the clinical category, several structures can belong to one protein;
  they are resampled as separate structures, which we name as a limit in Section 9.4. Table 8
  gives the number of structures beside the number of tasks.
- **Paired comparison of formats.** For each model and pair, a side counts as right when at
  least two of its three answers are right (the majority summary of Section 4.2). "Right" is
  taken two ways. The primary comparison uses the target score: an answer is right when it is
  target-right, that is, when its target score is exactly 1. This is the same test in both
  formats. The secondary comparison uses task success, which is not the same test in the two
  formats (Section 4.2), and is shown beside the first. An unshowable answer counts as not
  right. A pair that is right on one side only can therefore reflect an answer that could not
  be shown as well as one that was shown and selected the wrong atoms; the outcome tables of
  the SI give the share of unshowable answers per model and track, against which the
  one-sided counts must be read. Pairs right on one side only are compared with McNemar's
  exact test [@mcnemar1947]. We report the four counts for every model.
  {{corpus.twins.n_without_target}} follow-up pairs ask for something to be removed and have
  no target score (Section 4.2); they cannot be target-right on either side, so the primary
  comparison is read on the other {{corpus.twins.n_with_target}} pairs. We repeat the analysis
  without the {{corpus.twins.need_hide_toggle}} pairs in which the call list must switch off
  part of the default view (Section 3.4), and without the clinical pairs, in which the
  call-list viewer can do the mapping itself (Section 3.4).
- **Planned comparisons**, each as a difference in task success rate with an interval: public
  against held-back split; full against terse and indirect wording; with and without JSON
  mode; with and without grounding pack; and clinical tasks in which copying the number in the
  variant name is right against those in which it is wrong (the primary clinical grouping; the
  grouping by offset is descriptive). The first four are rows of Table 12; the last is the
  difference row of Table 10, which is also given on the target score. Totals of the two
  tracks are not compared with each other: the tracks differ in their mix of categories and in
  the length of the answer, so the formats are compared on the pairs only.
- **What F1 is read against.** F1 has a floor that needs no skill: a scene with nothing but a
  protein cartoon, or a follow-up's start state returned unchanged, shares most of its drawing
  with the reference. The task success rate is therefore the primary score and the target
  score is reported beside it; F1 is shown with the keyword script beside it, which marks
  that floor.

The McNemar tests are one per model; we read each as a description of that model and not as a
family of tests. We do not correct for multiple comparisons, and we report every count.

### 5.5 Human check of the grader

The grader's verdict is also checked against people. After the run, volunteers will see
*picture comparisons*: two pictures side by side, a reference and a model answer, rendered
from the same camera and framed on the target atoms. They say whether the two show the same
thing. The study has two parts.

*Possible false fails.* {{study.n_pairs}} picture comparisons are of valid scene-track answers
of the main condition that the grader does not count as a task success. They are sampled as
follows: at most {{study.max_per_task_model}} answer per task and model and {{study.max_per_task}} per task; half are answers that an
*image judge* calls the same as the reference and half are answers that it calls different;
within each half, equal numbers per category; and no model supplies more than {{study.max_model_share:.0%}} of the set.
The image judge is a vision-language model that is shown the same two pictures and asked the
same question; it is used here to find the answers most likely to look right, and it
contributes to no score in this paper. Each comparison is rated by {{study.raters_per_pair}}
people. We will report, with intervals, how often people call an answer that the grader failed
the same as the reference, the agreement between the raters, and the agreement between people
and the image judge. An answer that both raters call the same as the reference although the
grader failed it is either a false fail of the grader or a difference that the picture does
not show; each such case will be listed.

*Possible false passes.* A further {{study.n_grader_check_pairs}} picture comparisons are of
answers that the grader counts as a task success although their pictures are not identical
pixel for pixel. People should call these the same; each one that they call different is a
possible false pass.

A smaller trial of the study has been run on the pilot answers (Section 6.6, Finding 6).

### 5.6 Reproducibility

One command performs the run from the manifest. It does not start if the projected cost is
above a cap in US dollars that the manifest states, and it stops if spending would pass it.
One command rebuilds every table, figure and number in this paper from the archived answers.
A rehearsal with a mock model exercises the whole path at no cost. Grading needs no network
access and no paid service.
