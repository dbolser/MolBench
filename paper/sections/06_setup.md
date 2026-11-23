## 5. Experimental setup

One run fills every result in Sections 6.1 to 6.5. Its plan is fixed in a single manifest file
before any model is called: the corpus version and its hash, the models and their prices, the
prompting conditions, the number of answers per task and the limits. SI Section S6 reproduces
it.

### 5.1 Models

The models are chosen by a written rule, not by results. The *core models* are the
{{plan.n_core_models}} language models in the results that we published online in October 2026
(the results browser of Section 12). They are kept unchanged, so that the choice of models
depends on no result of the present benchmark. They are lower-priced models, with list prices from {{plan.core_price_output_min}}
to {{plan.core_price_output_max:.0f}} US dollars per million output tokens. Of the
{{plan.n_core_models}}, {{plan.n_core_open}} have *open weights* (the weights of the model can
be downloaded) and {{plan.n_core_closed}} have *closed weights* (the model can be used only
through a provider's service).

- Closed weights ({{plan.n_core_closed}}): {{plan.core_models_closed}}.
- Open weights ({{plan.n_core_open}}): {{plan.core_models_open}}.

SI Table S7 lists every model with its full identifier and price. All but one of the core
models ran in the October pilot of the
scene track (Section 6.6); the exception, {{plan.core_not_in_pilot}}, could not be reached on
that day and had earlier call-list results only.

Up to {{plan.n_optional_models}} *optional models* are larger (list prices from
{{plan.optional_price_output_min}} to {{plan.optional_price_output_max:.0f}} US dollars per
million output tokens): the largest current model of several providers of closed-weight
models, and the largest model with open weights, as listed on the day the prices were recorded
in the manifest ({{plan.price_date:date}}). The manifest names them. Which of them
are run is decided before any result exists, from the projected cost alone, and they are
marked † in the tables. No model is added or dropped after results are seen.
⟦PENDING: Dan — which of the optional models are run⟧

A *keyword script* that uses no model is run on both tracks as a floor: it maps words in the
request to fixed answers by rule.

### 5.2 Prompting conditions

Table 5 lists the four prompting conditions. In each of them a model receives a system prompt
and the request, and returns one answer. A model cannot
look anything up, cannot ask a question back, and does not see a rendered result. It is not
given the structure file. Both system prompts tell the model that its answer is judged by what
the viewer ends up showing; the scene prompt adds that anything drawn that was not asked for
counts against the answer.

**Table 5. Prompting conditions.** *Main* is the condition from which all main results come.
*Format guide*: a frozen text in the system prompt that documents the answer format. *JSON
mode*: a provider option that forces syntactically valid JSON. *Grounding pack*: the result of
an offline lookup, appended to the request: the chains of the structure, its residue ranges in
both numberings, the UniProt mapping and, for a clinical task, the residue that each named
variant maps to. *Answers per task*: answers of each model to each task.

| Condition | What the model is given | Run on | Answers per task |
|:-----|:----------|:----------|--:|
| **Main** | A short instruction, the rule for the answer ("answer with one JSON value and nothing else") and the format guide | all models, all tasks, both tracks | {{plan.samples}} |
| Main + JSON mode | The same, with JSON mode switched on | every model that offers JSON mode: {{plan.n_json_mode_models}} of the {{plan.n_core_models}} core models (all but {{plan.core_without_json_mode}}) and each optional model that is run; all tasks, both tracks | 1 |
| Main + grounding pack | The same, with the task's grounding pack appended to the request | all models; the lookup categories (name resolution, clinical variant), scene track | {{plan.samples}} |
| No format guide | The instruction and the rule for the answer only | {{plan.n_bare_models}} models ({{plan.bare_models}}), the same as in the pilot run; all tasks of the scene track | {{plan.samples}} |

A grounding pack never contains a scene, a colour or a representation. But for a clinical
task it contains the mapped residue, and for a name-resolution task a list of entries. The
condition with a grounding pack therefore shows the most that a perfect lookup tool could add:
the lookup has been done and its result handed over. It is not a test of whether a model can
use raw lookup tables. For the running example the pack states that UniProt
{{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
{{ex.map_auth_first}}–{{ex.map_auth_last}} of chain {{ex.auth_chain}}, and that
{{ex.name_in_prompt}} is author residue {{ex.auth_number}} of that chain (SI Section S1).

The grounding-pack condition is run on the scene track only. Name resolution exists only
there, and on the call-list track a clinical request can be answered with the UniProt
selector, without the residue number that the pack supplies (Section 3.4).

**What the format guide contains.** The format guide is all that the model is told about the
answer format, so its content matters. The guide of the scene track ({{prompt.mvs.guide_words:,}}
words) lists the kinds of node of a scene and the fields of a selection, among them the chain
and residue number in author numbering and in label numbering. The guide of the call-list
track ({{prompt.api.guide_words:,}} words) lists the calls and their fields, among them
selection by author numbering, by label numbering and by UniProt accession and position.
Neither guide says which numbering a given entry uses, and the scene guide does not mention
UniProt. With the instruction and the rule for the answer, the system prompt has
{{prompt.mvs.words:,}} words on the scene track and {{prompt.api.words:,}} on the call-list
track. SI Section S7 prints both system prompts and both guides in full.

No prompt was tuned on benchmark tasks. Each of the two system prompts has one worked example,
and both examples use entry {{prompt.worked_example_entry}}, which no task uses. The format guide of the scene track also contains one short illustration of a
distance line on an entry that tasks do use; no task asks for that distance.

### 5.3 Sampling

Each model answers each task {{plan.samples:word}} times in the main condition, at the provider's
default temperature. The limit on the length of an answer is {{plan.max_tokens:,}} tokens.
Of the core models, {{plan.n_core_reasoning:word}} first write reasoning text that the user does not
see; the provider bills it and counts it against the limit. For these models the limit is
{{plan.reasoning_max_tokens:,}} tokens for reasoning and answer together (SI Table S7). An
invalid answer is scored as it stands and is not retried; only transport errors are retried.
Every raw answer is archived with its token counts, the reason the provider gives for the end
of the answer, and its cost.

### 5.4 Statistics

- **Per-model scores** are means over tasks of the mean over the task's {{plan.samples}}
  answers. For task success this is the task success rate; the all-{{plan.samples}} rate (the
  share of tasks on which all {{plan.samples}} answers succeed) is reported beside it (Section
  4.2). Valid-only scores are the exception: they pool a model's valid answers (Section 4.4).
  Means over models are means over the core models and the optional models that were run;
  they leave the keyword script out.
- **Intervals** are 95% bootstrap intervals [@efron1979] with {{run.bootstrap_replicates:,}}
  resamples.
    - *What is resampled.* Whole structures, with replacement, not single tasks, because
      tasks on one structure share its difficulties. Each task goes with the structure of its
      reference. The table of results by category (Section 6.2) gives the number of structures
      beside the number of tasks.
    - *What is not.* The {{plan.samples}} answers to a task are averaged before resampling and
      are not themselves resampled, so an interval reflects the choice of structures and
      tasks, not the variation between a model's answers to one task. Models are treated as
      fixed: an interval on a mean over models describes these models, not models in general.
    - *Valid-only scores.* Structures are resampled with all the valid answers to their
      tasks, and the pooled mean is recomputed in each resample.
    - *Differences.* Where the same tasks are compared under two conditions or two wordings
      (planned comparisons 2 to 6 below), the difference is taken task by task, and
      structures are resampled with the differences of their tasks. In comparison 1 the two
      splits share no structure, and each split is resampled on its own. In comparison 7 the
      two groups of clinical tasks can share a structure; each resample draws the structures
      once, and both groups are recomputed on that draw.
    - *A limit.* In the clinical category, several structures can belong to one protein. They
      are resampled as separate structures (Section 9.4).
- **Paired comparison of formats**, in six parts.
    - *Unit.* For each model and pair, a side is right when at least 2 of its
      {{plan.samples}} answers are right (the majority summary of Section 4.2). The test
      below needs one yes-or-no verdict per side, and the majority depends less on a single
      unlucky answer than the first answer alone would.
    - *Primary comparison.* An answer is right when it is target-right, that is, when its
      target score is exactly 1. This is the same test in both formats. It uses the
      {{corpus.twins.n_with_target}} pairs that have a target score. The other
      {{corpus.twins.n_without_target}} pairs have none (Section 4.2) and are left out: they
      are follow-up turns whose edit hides the water ({{corpus.twins.no_target.hide_water}}),
      sets the background colour ({{corpus.twins.no_target.background}}) or needs no change
      ({{corpus.twins.no_target.noop}}).
    - *Secondary comparison.* An answer is right when it is a task success. This is not the
      same test in the two formats (Section 4.2). It uses all {{corpus.n_twin_pairs}} pairs
      and is shown beside the first.
    - *Unshowable answers* count as not right. A pair that is right on one side only can
      therefore reflect an answer that could not be shown as well as one that was shown and
      selected the wrong atoms. The outcome tables of the SI give the share of unshowable
      answers per model and track, against which the one-sided counts must be read.
    - *Test.* The two counts of pairs that are right on one side only are compared with
      McNemar's exact test [@mcnemar1947]. We report the four counts for every model. The
      test treats pairs as independent, although several pairs sit on one structure, so its p
      values are somewhat too small. We read them as descriptions, and we give beside them
      the difference between the two one-sided counts as a share of the pairs, with a 95%
      interval for which structures are resampled.
    - *Repeats.* The analysis is repeated without the {{corpus.twins.need_hide_toggle}}
      pairs whose reference call list switches off part of the default view (Section 3.4),
      and without the clinical pairs, in which the call-list viewer can do the mapping
      itself. Those {{corpus.twins.need_hide_toggle}} pairs are first requests and the
      {{corpus.twins.n_without_target}} pairs without a target score are follow-up turns, so
      the two sets do not overlap.
- **Planned comparisons**, seven in all, each as a difference with an interval.
  Comparisons 1 to 6 are differences in task success rate and are reported together in
  Section 6.5: (1) public against held-back split; (2) full against terse wording and
  (3) full against indirect wording; (4) with and without JSON mode, where the single
  JSON-mode answer to a task is set against the mean of its {{plan.samples}} answers in the
  main condition; (5) with and without grounding pack; (6) with and without format guide.
  Comparisons 1 to 4 use both tracks, and 5 and 6 the scene track. Comparison 7 carries the
  question of the Introduction: clinical tasks of the scene track in which copying the number
  in the variant name is right against those in which it is wrong (the primary clinical
  grouping; the grouping by offset is descriptive). For this comparison alone the primary
  score is the target score, because task success also falls when an answer adds unrequested
  context; the difference in task success rate is given beside it. It is the difference row
  of the clinical table in Section 6.4. Totals of the two tracks are not compared with each
  other: the tracks differ in their mix of categories and in the length of the answer, so the
  formats are compared on the pairs only.
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

*Possible false fails.* The first part has {{study.n_pairs}} picture comparisons. Each is of
a valid scene-track answer of the main condition that the grader does not count as a task
success. They are sampled under four limits: (i) no task supplies more than
{{study.max_per_task}} answers, and never more than {{study.max_per_task_model}} from the same
model; (ii) half are answers that an *image judge* calls the same as the reference, and half
are answers that it calls different; (iii) within each half, the categories contribute as
nearly equal numbers of answers as the available answers allow; (iv) no model supplies more than {{study.max_model_share:.0%}} of the set.
The image judge is a vision-language model that is shown the same two pictures and asked the
same question; it is used here to find the answers most likely to look right, and it
contributes to no score in this paper. Each comparison is rated by {{study.raters_per_pair:word}}
raters. We will report three things, with intervals: the share of these answers that people
judge to show the same as the reference; the agreement between raters; and the agreement
between people and the image judge. Because the sample is balanced on the image judge's
verdict and on category, the first of these describes the sample. It is not the grader's
rate of false fails among all valid answers that it does not count as a success, and we make
no estimate of that rate from this study: the study looks for cases. An answer that all its raters judge to show the same as
the reference, although the grader did not count it as a success, is either a false fail of
the grader or a difference that the picture does not show; each such case will be listed.

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
